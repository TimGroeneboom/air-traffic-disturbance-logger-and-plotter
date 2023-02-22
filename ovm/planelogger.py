import logging
from datetime import datetime
from opensky_api import OpenSkyApi
from ovm.environment import Environment
from ovm.plotter import Plotter
from pymongo import MongoClient
from dataclasses import dataclass
from ovm.utils import *


@dataclass
class PlotOptions:
    plot: bool
    tilezoom: int
    filename: str


class PlaneLogger:
    # parameterized constructor
    def __init__(self, environment: Environment):
        # Set environment
        self.environment = environment

        # Create MongoDB client
        self.mongo_client = MongoClient(environment.mongodb_config.host,
                                        environment.mongodb_config.port)

        # Create plotter
        self.state_plotter = Plotter()

        # Connect with opensky network
        self.opensky_api = OpenSkyApi(environment.opensky_credentials.username,
                                      environment.opensky_credentials.password)

    def prepare_log(self, message: str):
        return self.__class__.__name__ + ': ' + message

    def log(self, bbox: tuple, plot_options: PlotOptions = None):
        # Obtain current states
        logging.info(self.prepare_log('Obtaining states from opensky network'))
        state_collection = self.opensky_api.get_states(bbox=bbox)

        # Create states list with interesting data and store list in mongo db with timestamp as key value
        logging.info(self.prepare_log('Storing %i states in database' % len(state_collection.states)))
        key = convert_datetime_to_int(datetime.datetime.now())
        db_states = self.mongo_client[self.environment.mongodb_config.database][self.environment.mongodb_config.collection]
        states = []
        for state in state_collection.states:
            state_object = ***REMOVED***
                "longitude": state.longitude,
                "latitude": state.latitude,
                "icao24": state.icao24,
                "callsign": state.callsign,
                "on_ground": state.on_ground,
                "baro_altitude": state.baro_altitude,
                "geo_altitude": state.geo_altitude,
                "origin_country": state.origin_country,
                "velocity": state.velocity
          ***REMOVED***
            states.append(state_object)
        result = db_states.insert_one(***REMOVED***
            'Time': key,
            'States': states
      ***REMOVED***)

        # Plot if necessary
        if plot_options is not None and plot_options.plot:
            logging.info(self.prepare_log('Creating plot'))
            self.state_plotter.plot_states(states,
                                           bbox=bbox,
                                           tile_zoom=plot_options.tilezoom,
                                           filename=plot_options.filename)
