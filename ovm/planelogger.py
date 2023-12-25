import base64
import logging
from datetime import datetime
import geopy
import geopy.distance
import pytz

from ovm.environment import Environment
from ovm.plotter import plot_states
from pymongo import MongoClient
from dataclasses import dataclass
from ovm.utils import *
from FlightRadar24 import FlightRadar24API

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

        # Set timezone
        self.timezone = pytz.timezone(self.environment.timezone.timezone)

        # Create MongoDB client
        self.mongo_client = MongoClient(environment.mongodb_config.host,
                                        environment.mongodb_config.port)

        # Create with flightradar24api
        flightradar24_user: str = environment.flightradar24_creds.username
        flightradar24_pass: str = environment.flightradar24_creds.password
        if flightradar24_user != "" and flightradar24_pass != "":
            self.fr_api = FlightRadar24API(user=flightradar24_user, password=flightradar24_pass)
        else:
            self.fr_api = FlightRadar24API()

    def prepare_log(self, message: str):
        return self.__class__.__name__ + ': ' + message

    def log(self, center: tuple, radius: int, plot_options: PlotOptions = None):
        """
        Queries states from open sky given the specified geographic bounding box and logs states into MongoDB.
        Creates state plot if required
        @param center in lat lon
        @param radius in meters
        @param plot_options: plot options
        """

        try:
            # Obtain current states
            logging.info(self.prepare_log('Obtaining states from flightradar24'))
            bounds = self.fr_api.get_bounds_by_point(latitude=center[0], longitude=center[1], radius=radius)
            flights = self.fr_api.get_flights(bounds=bounds)

            if flights is None:
                logging.error(self.prepare_log('Failed to obtain states from flightradar24'))
                return

            # Create states list with interesting data and store list in mongo db with timestamp as key value
            timestamp = datetime.datetime.now(self.timezone)
            logging.info(self.prepare_log('Timestamp of obtained flights : %s' % timestamp.__str__()))
            key = convert_datetime_to_int(timestamp)

            logging.info(self.prepare_log('Storing %i flights in database' % len(flights)))
            db_states = self.mongo_client[self.environment.mongodb_config.database][
                self.environment.mongodb_config.collection]
            states = []
            for flight in flights:
                state_object = {
                    "longitude": flight.longitude,
                    "latitude": flight.latitude,
                    "callsign": flight.callsign,
                    "geo_altitude": flight.altitude * 0.3048, # feet to meters
                    "icao24": flight.airline_icao
                }
                states.append(state_object)
            result = db_states.update_one({'Time': key}, {"$set": {'States': states}}, upsert=True)

            # Plot if necessary
            if plot_options is not None and plot_options.plot:
                # Compute bbox from center and radius
                center = geopy.Point(center[0], center[1])
                d = geopy.distance.geodesic(meters=radius)

                # get upper bound (north)
                north = d.destination(point=center, bearing=0)
                # get right bound (east)
                east = d.destination(point=center, bearing=90)
                # get lower bound (south)
                south = d.destination(point=center, bearing=180)
                # get left bound (west)
                west = d.destination(point=center, bearing=270)

                # Create plot
                logging.info(self.prepare_log('Creating plot'))
                img = plot_states(states,
                                  bbox=(south.latitude, north.latitude, west.longitude, east.longitude),
                                  tile_zoom=plot_options.tilezoom)

                # Write image to disk
                with open(plot_options.filename, 'wb') as fh:
                    fh.write(img)
                    fh.close()

        except Exception as ex:
            logging.exception(ex)
