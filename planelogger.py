import logging
import time
from datetime import datetime
from opensky_api import OpenSkyApi
from stateplotter import StatePlotter
from pymongo import MongoClient
from dataclasses import dataclass


@dataclass
class PlotOptions:
    plot: bool
    tilezoom: int


class PlaneLogger:
    # parameterized constructor
    def __init__(self, username: str, password: str):
        # MongoDB client
        self.mongo_client = MongoClient()

        # Create plotter
        self.state_plotter = StatePlotter()

        # Connect with opensky network
        self.username = username
        self.password = password
        self.opensky_api = OpenSkyApi(username=username, password=password)

    def prepare_log(self, message: str):
        return self.__class__.__name__ + ': ' + message

    def run(self,
            bbox: tuple,
            plot_options: PlotOptions = None,
            interval: int = 10):
        while True:
            try:
                # Get current time for performance and time measurment
                current_time = time.perf_counter()

                # Obtain current states
                logging.info(self.prepare_log('Obtaining states from opensky network'))
                state_collection = self.opensky_api.get_states(bbox=bbox)

                # Store states in mongo db
                logging.info(self.prepare_log('Storing %i states in database' % len(state_collection.states)))
                key = int(datetime.now().strftime("%Y%m%d%H%M%S"))
                db_states = self.mongo_client.planelogger.states
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
                    self.state_plotter.plot(state_collection.states,
                                            bbox=bbox,
                                            tile_zoom=plot_options.tilezoom)

                # Calculate sleep interval
                time_elapsed = time.perf_counter() - current_time;
                sleep_interval = interval - time_elapsed;
                if sleep_interval < 0:
                    sleep_interval = 0
                logging.info(self.prepare_log('Actions took %f seconds, sleep for %f seconds' %
                                              (time_elapsed, sleep_interval)))
                time.sleep(sleep_interval)
            except KeyboardInterrupt:
                return 0
            except Exception as ex:
                logging.exception(self.prepare_log('An error has occurred : %s' % ex.__str__()))
                time.sleep(interval)
