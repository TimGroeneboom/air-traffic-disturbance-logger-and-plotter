import base64
import logging
from datetime import datetime
from opensky_api import OpenSkyApi
from ovm.environment import Environment
from ovm.plotter import plot_states
from pymongo import MongoClient
from dataclasses import dataclass
from ovm.utils import *


@dataclass
class PlotOptions:
    """
    Dataclass holding plot info
    """
    plot: bool
    tilezoom: int
    filename: str


class PlaneLogger:
    """
    PlaneLogger queries states from open  and writes states into MongoDB
    """
    # parameterized constructor
    def __init__(self, environment: Environment):
        # Set environment
        self.environment = environment

        # Create MongoDB client
        self.mongo_client = MongoClient(environment.mongodb_config.host,
                                        environment.mongodb_config.port)

        # Connect with opensky network
        self.opensky_api = OpenSkyApi(environment.opensky_credentials.username,
                                      environment.opensky_credentials.password)

    def prepare_log(self, message: str):
        return self.__class__.__name__ + ': ' + message

    def log(self, bbox: tuple, plot_options: PlotOptions = None):
        """
        Queries states from open sky given the specified geographic bounding box and logs states into MongoDB.
        Creates state plot if required
        @param bbox: geographic bounding box (lat_min, lat_max, lon_min, lon_max)
        @param plot_options: plot options
        """

        try:
            # Obtain current states
            logging.info(self.prepare_log('Obtaining states from opensky network'))
            state_collection = self.opensky_api.get_states(bbox=bbox)
            if state_collection is None:
                logging.error(self.prepare_log('Failed to obtain states from opensky'))
                return

            # Create states list with interesting data and store list in mongo db with timestamp as key value
            time = state_collection.time
            timestamp = datetime.datetime.fromtimestamp(time)
            logging.info(self.prepare_log('Timestamp of obtained states : %s' % timestamp.__str__()))
            key = convert_datetime_to_int(timestamp)

            logging.info(self.prepare_log('Storing %i states in database' % len(state_collection.states)))
            db_states = self.mongo_client[self.environment.mongodb_config.database][
                self.environment.mongodb_config.collection]
            states = []
            for state in state_collection.states:
                state_object = {
                    "longitude": state.longitude,
                    "latitude": state.latitude,
                    "callsign": state.callsign,
                    "geo_altitude": state.geo_altitude,
                    "icao24": state.icao24
                }
                states.append(state_object)
            result = db_states.update_one({'Time': key}, {"$set": {'States': states}}, upsert=True)

            # Plot if necessary
            if plot_options is not None and plot_options.plot:
                logging.info(self.prepare_log('Creating plot'))
                img = plot_states(states,
                                  bbox=bbox,
                                  tile_zoom=plot_options.tilezoom)

                # Write image to disk
                with open(plot_options.filename, 'wb') as fh:
                    fh.write(img)
                    fh.close()
        except Exception as ex:
            logging.exception(ex)
