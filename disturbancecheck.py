# Import the python libraries
import argparse
import collections
import logging
import datetime
import time
import pymongo as pymongo
from pymongo import MongoClient
import geopy.distance
from ovm import environment
from ovm.complainant import Complainant
from ovm.disturbanceperiod import DisturbancePeriod
from ovm.plotter import Plotter
from ovm.utils import *

if __name__ == '__main__':
    # parse cli arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('-l', '--loglevel',
                        type=str.upper,
                        default='INFO',
                        help='LOG Level (DEBUG, INFO, WARNING, ERROR, CRITICAL)')
    parser.add_argument('-p', '--plot',
                        action=argparse.BooleanOptionalAction,
                        help='Creates a plot for each run')
    parser.add_argument('-z', '--zoomlevel',
                        type=int,
                        default=14,
                        help='Zoom level of contextly maps')
    args = parser.parse_args()

    # Set log level
    logging.basicConfig(level=args.loglevel)

    # TODO: fetch complainants from database
    complainants = []
    complainants.append(Complainant(user='CodeFlow',
                                    # Amsterdamse Bos
                                    #origin=(52.311502, 4.827680),
                                    # Assendelft
                                    origin=(52.469640, 4.721354),
                                    # Christoffelkruidstraat
                                    #origin=(52.396172234741506, 4.905621078252285),
                                    radius=1250,
                                    altitude=1000,
                                    occurrences=4,
                                    timeframe=60))

    # Load environment
    environment = environment.load_environment('environment.json')

    # Choose the appropriate client
    client = MongoClient(environment.mongodb_config.host, environment.mongodb_config.port)

    # TODO: get callsigns to ignore from database
    # Ignore certain callsigns
    ignore_callsigns = [
        'LIFELN1'
    ]

    for complainant in complainants:
        # Get current time for performance and time measurement
        current_time = time.perf_counter()

        # Log user info
        logging.info('Checking disturbances for user %s' % complainant.user)

        # Disturbances is a dictionary with plane callsign as key value and the integer timestamp as value
        disturbances: dict = {}

        # Array of DisturbancePeriod data classes holding information about all disturbance periods found in database
        disturbance_periods = []

        # The last timestamp found
        last_timestamp: datetime

        # The timestamp of the beginning of a disturbance period
        disturbance_begin: datetime

        # The timestamp of the last disturbance occurrence found
        last_disturbance: datetime

        # Amount of disturbances recorded
        disturbance_hits = 0

        # If the disturbance threshold is reached, and we're currently iterating through a disturbance period
        in_disturbance = False

        # Callsigns in current disturbance period
        callsigns_in_disturbance = []

        # Get the collection of states from the mongo db
        # A state holds all plane information (callsign, location, altitude, etc..) on a specific timestamp
        # The time is the key value of a state and is ordered accordingly in the mongo database
        # Time is an int64 holding the timestamp in the following format %Y%m%d%H%M%S
        states_collection = client[environment.mongodb_config.database][environment.mongodb_config.collection]
        cursor = states_collection.find({})

        # Total altitude, this is used to compute the average altitude measured in a disturbance period
        total_altitude = 0

        # Iterate through states
        for document in cursor:
            # Get timestamp as integer value and as datetime object
            timestamp_int = document['Time']
            timestamp = convert_int_to_datetime(timestamp_int)

            # Get all states
            states = document['States']

            # Signifies if during this timestamp, a disturbance is detected
            disturbance_in_this_timestamp = False

            for state in states:
                # Get callsign
                callsign = remove_whitespace(state['callsign'])

                # Ignore grounded planes
                if state['baro_altitude'] is None:
                    continue

                # Ignore specified callsigns
                if list_contains_value(arr=ignore_callsigns,
                                       value=callsign):
                    continue

                # Check if altitude is lower than altitude and if distance is within specified radius
                if state['baro_altitude'] < complainant.altitude:
                    # Obtain lat lon from location to compute distance from complainent origin
                    coord = (state['latitude'], state['longitude'])
                    distance = geopy.distance.distance(complainant.origin, coord).meters

                    if distance < complainant.radius:
                        # A disturbance is detected, check if it is a new plane in this disturbance period
                        if not list_contains_value(callsigns_in_disturbance, callsign):
                            disturbance_hits += 1
                            callsigns_in_disturbance.append(callsign)

                        total_altitude += state['baro_altitude']

                        # Check if there already is a disturbance in this timeframe, otherwise create a new disturbance
                        disturbance_in_this_timestamp = True
                        if not in_disturbance:
                            in_disturbance = True
                            disturbance_begin = timestamp
                            last_disturbance = timestamp
                        else:
                            diff_since_begin = timestamp - disturbance_begin
                            diff_since_last = timestamp - last_disturbance
                            last_disturbance = timestamp

                        # if callsign is not already logged for this disturbance, do it now
                        if callsign not in disturbances.keys():
                            disturbances[callsign] = timestamp_int

            # Check if disturbance has ended and if we need to generate a complaint within set parameters
            if not disturbance_in_this_timestamp:
                # There is no disturbance in this timestamp, if we're currently in a disturbance period
                # check if this needs to end, and we can log store this period as a disturbance period
                if in_disturbance:
                    diff_since_last = timestamp - last_disturbance
                    disturbance_duration = last_disturbance - disturbance_begin
                    diff_since_begin = timestamp - disturbance_begin
                    if (diff_since_last.seconds / 60) >= complainant.timeframe:
                        if disturbance_hits >= complainant.occurrences:
                            disturbance_period = DisturbancePeriod(complainant=complainant,
                                                                   disturbances=disturbances.copy(),
                                                                   begin=disturbance_begin,
                                                                   end=last_disturbance,
                                                                   hits=disturbance_hits,
                                                                   average_altitude=total_altitude / disturbance_hits)
                            disturbance_periods.append(disturbance_period)

                        in_disturbance = False
                        disturbance_begin = None
                        last_disturbance = None
                        disturbance_hits = 0
                        total_altitude = 0
                        disturbances = {}
                        callsigns_in_disturbance = []

            last_timestamp = timestamp

        # Done iterating through al states in database
        # Handle disturbance if we finished in disturbance state
        if in_disturbance:
            diff_since_last = timestamp - last_disturbance
            disturbance_duration = last_disturbance - disturbance_begin
            diff_since_begin = timestamp - disturbance_begin
            if disturbance_hits >= complainant.occurrences:
                if (disturbance_duration.seconds / 60) > complainant.timeframe:
                    disturbance_period = DisturbancePeriod(complainant=complainant,
                                                           disturbances=disturbances.copy(),
                                                           begin=disturbance_begin,
                                                           end=last_disturbance,
                                                           hits=disturbance_hits,
                                                           average_altitude=total_altitude / disturbance_hits)
                    disturbance_periods.append(disturbance_period)

        # Calc trajectories for generate complaints for callsigns
        index = 0
        for disturbance_period in disturbance_periods:
            # Calc disturbance duration
            disturbance_duration = disturbance_period.end - disturbance_period.begin
            logging.info('Disturbance detected. %i flights and a total duration of %i minutes. '
                         'Disturbance began at %s and ended at %s' %
                         (len(disturbance_period.disturbances.items()), (disturbance_duration.seconds / 60),
                          disturbance_period.begin.__str__(), disturbance_period.end.__str__()))

            # Create trajectories for complaint
            logging.info('Collecting trajectories for %i flights' % (len(disturbance_period.disturbances.items())))
            for callsign, datetime_int in disturbance_period.disturbances.items():
                # Gather states before and after this entry to plot a trajectory for callsign
                dictionary = {}
                items_before = states_collection.find({'Time': {'$gte': datetime_int}}).limit(4)
                items_after = states_collection.find({'Time': {'$lte': datetime_int}}).sort(
                    [('Time', pymongo.DESCENDING)]).limit(4)
                for doc in items_before:
                    timestamp_int = doc['Time']
                    if timestamp_int not in dictionary.keys():
                        dictionary[timestamp_int] = doc['States']
                for doc in items_after:
                    timestamp_int = doc['Time']
                    if timestamp_int not in dictionary.keys():
                        dictionary[timestamp_int] = doc['States']

                # Order found states and create the trajectory of disturbance callsign
                trajectory = []
                ordered_dict = collections.OrderedDict(sorted(dictionary.items()))
                for key, value in ordered_dict.items():
                    for state in value:
                        if remove_whitespace(state['callsign']) == callsign:
                            coord = (state['longitude'], state['latitude'])
                            trajectory.append(coord)

                # Add it to the trajectories of this complaint
                disturbance_period.trajectories[callsign] = trajectory

            # Set the bounding box for our area of interest, add an extra meters/padding for a better view of
            # trajectories
            bbox = get_geo_bbox_around_coord(complainant.origin, (complainant.radius + 1000) / 1000.0)

            # Make plot of all callsign trajectories
            if args.plot:
                output_file = '%s%s.jpg' % (disturbance_period.complainant.user,
                                            disturbance_period.begin.strftime("%Y%m%d%H%M%S"))
                logging.info('Generating disturbance period plot %s', output_file)
                plotter = Plotter()
                plotter.plot_trajectories(bbox=bbox,
                                          disturbance_period=disturbance_period,
                                          tile_zoom=args.zoomlevel,
                                          figsize=(10, 10),
                                          filename=output_file)

        # Log performance
        time_elapsed = time.perf_counter() - current_time
        logging.info('Operation took %f seconds' % time_elapsed)

    # Exit gracefully
    exit(0)
