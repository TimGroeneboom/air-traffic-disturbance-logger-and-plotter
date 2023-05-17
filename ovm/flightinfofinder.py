import base64
import collections
import logging
import operator
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import geopy.distance
import pymongo
from pymongo import MongoClient
from ovm import utils
from ovm.disturbanceperiod import DisturbancePeriod, Disturbances, Disturbance, CallsignInfo
from ovm.environment import Environment
from ovm.plotter import plot_trajectories
from ovm.trajectory import Trajectory
from ovm.utils import convert_datetime_to_int


class FlightInfoFinder:
    """
    FlightInfoFinder exposes some methods to query and find flight information from the stored states in the database
    """

    # parameterized constructor
    def __init__(self, environment: Environment):
        # Set environment
        self.environment = environment

        # Create MongoDB client
        self.mongo_client = MongoClient(environment.mongodb_config.host,
                                        environment.mongodb_config.port)

    def get_trajectory(self,
                       callsign: str,
                       timestamp: datetime,
                       duration: int):
        """
        Returns a list of coordinates of the flight path of given callsign around timestamp. Period is determined by
        duration around timestamp. Meaning a duration of 60 means beginning of period of trajectory = timestamp - duration / 2
        and end of period of trajectory = timestamp + duration / 2
        """

        # Get the collection of states from the mongo db
        # A state holds all plane information (callsign, location, altitude, etc..) on a specific timestamp
        # The time is the key value of a state and is ordered accordingly in the mongo database
        # Time is an int64 holding the timestamp in the following format %Y%m%d%H%M%S
        states_collection = self.mongo_client[self.environment.mongodb_config.database][
                self.environment.mongodb_config.collection]

        # Sanity check callsign
        callsign = utils.remove_whitespace(callsign)

        # Compute begin and end timestamp
        begin = timestamp - timedelta(minutes=duration / 2)
        end = timestamp + timedelta(minutes=duration / 2)

        # Find the first entry near begin timestamp
        cursor = states_collection.find({'Time': {'$gte': convert_datetime_to_int(begin)}})

        # Holds all coordinates
        coords = []

        # Iterate through states
        for document in cursor:
            # Get timestamp as integer value and as datetime object
            timestamp_int = document['Time']
            new_timestamp = utils.convert_int_to_datetime(timestamp_int)

            # bail if timestamp exceeded end
            if new_timestamp > end:
                break

            # Get all states
            states = document['States']

            # Iterate through states
            for state in states:
                # Get callsign
                found_callsign = utils.remove_whitespace(state['callsign'])

                if callsign == found_callsign:
                    # Obtain altitude
                    geo_altitude = state['geo_altitude']

                    # Ignore grounded planes
                    if geo_altitude is None:
                        continue

                    # obtain flight coordinate
                    flight_coord = (state['latitude'], state['longitude'])
                    coords.append(flight_coord)

        return coords

    def find_flights(self,
                     origin: tuple,
                     begin: datetime,
                     end: datetime,
                     radius: int,
                     altitude: int,
                     plot: bool = False,
                     zoomlevel: int = 14):
        """
        Finds all flights that flew within a given radius and time period and below a given altitude
        Returns a single disturbance object containing all flights found
        """

        # Create disturbances
        disturbances: Disturbances = Disturbances()
        disturbance: Disturbance = Disturbance()
        disturbances.disturbances.append(disturbance)
        disturbance.begin = begin.strftime("%Y-%m-%d %H:%M:%S")
        disturbance.end = end.strftime("%Y-%m-%d %H:%M:%S")

        # Create dictionary of all trajectories
        trajectories: dict = {}

        # Get the collection of states from the mongo db
        # A state holds all plane information (callsign, location, altitude, etc..) on a specific timestamp
        # The time is the key value of a state and is ordered accordingly in the mongo database
        # Time is an int64 holding the timestamp in the following format %Y%m%d%H%M%S
        states_collection = self.mongo_client[self.environment.mongodb_config.database][
            self.environment.mongodb_config.collection]
        cursor = states_collection.find({'Time': {'$gte': convert_datetime_to_int(begin)}})

        # Iterate through states
        for document in cursor:
            # Get timestamp as integer value and as datetime object
            timestamp_int = document['Time']
            timestamp = utils.convert_int_to_datetime(timestamp_int)

            # bail if timestamp exceeded end
            if timestamp > end:
                break

            # Get all states
            states = document['States']

            # Iterate through states
            for state in states:
                # Get callsign
                callsign = utils.remove_whitespace(state['callsign'])

                # Ignore if callsign already present
                callsign_already_registered = False
                for existing_callsign in disturbance.callsigns:
                    if existing_callsign.callsign == callsign:
                        callsign_already_registered = True
                        continue
                if callsign_already_registered:
                    continue

                # Obtain icao24
                icao24 = utils.xstr(state['icao24'])

                # Obtain altitude
                geo_altitude = state['geo_altitude']

                # Ignore grounded planes
                if geo_altitude is None:
                    continue

                # obtain flight coordinate
                flight_coord = (state['latitude'], state['longitude'])

                # Check if altitude is lower than altitude and if distance is within specified radius
                if geo_altitude < altitude:
                    # Obtain lat lon from location to compute distance from complainant origin
                    distance = geopy.distance.great_circle(origin, flight_coord).meters
                    if distance < radius:
                        disturbance.callsigns.append(CallsignInfo(callsign=callsign,
                                                                  datetime=timestamp_int,
                                                                  altitude=geo_altitude,
                                                                  icao24=icao24))

                        # obtain trajectory if plot is needed
                        if plot:
                            # Create trajectory and append coordinate
                            trajectories[callsign] = Trajectory()
                            trajectories[callsign].callsign = callsign
                            trajectories[callsign].average_altitude += geo_altitude

                            # Get timestamp
                            timestamp_int = document['Time']

                            # Limit results to cap trajectory, if interval is set to 22 seconds,
                            # a limit of 15 will be +- 5 minutes, which should be more than enough
                            items_after = states_collection.find({'Time': {'$gte': timestamp_int}}).limit(15)
                            items_before = states_collection.find({'Time': {'$lte': timestamp_int}}).sort(
                                [('Time', pymongo.DESCENDING)]).limit(15)

                            # coordinates will be stored here
                            coords: list = []

                            # First iterate over the past, insert coordinates
                            for doc in items_before:
                                timestamp_int = doc['Time']
                                older_states = doc['States']
                                trajectory_complete = False
                                callsign_found_in_states = False
                                for older_state in older_states:
                                    if utils.remove_whitespace(older_state['callsign']) == callsign:
                                        new_altitude = older_state['geo_altitude']
                                        if new_altitude is not None:
                                            # Obtain lat lon from location to compute distance from complainant origin
                                            old_coord = (older_state['latitude'], older_state['longitude'])
                                            distance = geopy.distance.great_circle(origin, old_coord).meters
                                            coords.insert(0, (old_coord[1], old_coord[0]))
                                            trajectories[callsign].average_altitude += new_altitude
                                            if distance > radius * 2:
                                                trajectory_complete = True
                                        callsign_found_in_states = True

                                # Callsign not preset or distance is outside radius, finish
                                if trajectory_complete or callsign_found_in_states is False:
                                    break

                            # Iterate over the future, append coordinates
                            for doc in items_after:
                                timestamp_int = doc['Time']
                                newer_states = doc['States']
                                trajectory_complete = False
                                callsign_found_in_states = False
                                for newer_state in newer_states:
                                    if utils.remove_whitespace(newer_state['callsign']) == callsign:
                                        new_altitude = newer_state['geo_altitude']
                                        if new_altitude is not None:
                                            # Obtain lat lon from location to compute distance from complainant origin
                                            new_coord = (newer_state['latitude'], newer_state['longitude'])
                                            distance = geopy.distance.great_circle(origin, new_coord).meters
                                            coords.append((new_coord[1], new_coord[0]))
                                            trajectories[callsign].average_altitude += new_altitude
                                            if distance > radius * 2:
                                                trajectory_complete = True
                                        callsign_found_in_states = True

                                # Callsign not preset or distance is outside radius, finish
                                if trajectory_complete or callsign_found_in_states is False:
                                    break

                            # Calculate
                            coord_num = len(coords)
                            trajectories[callsign].coords = coords
                            if coord_num > 0:
                                trajectories[callsign].average_altitude /= len(trajectories[callsign].coords)

        if plot:
            # Set the bounding box for our area of interest, add an extra meters/padding for a better view of
            # trajectories
            bbox = utils.get_geo_bbox_around_coord(origin, (radius) / 1000.0)

            # Make plot of all callsign trajectories
            logging.info('Generating trajectory plot')
            image = plot_trajectories(bbox=bbox,
                                      origin=origin,
                                      begin=begin,
                                      end=end,
                                      trajectories=trajectories,
                                      tile_zoom=zoomlevel)
            disturbance.img = str(base64.b64encode(image), 'UTF-8')
        else:
            disturbance.img = None

        # sort disturbances by timestamp
        return disturbances

    def find_disturbances(self,
                          origin: tuple,
                          begin: datetime,
                          end: datetime,
                          radius: int,
                          altitude: int,
                          occurrences: int,
                          timeframe: int,
                          plot: bool = False,
                          title: str = '',
                          zoomlevel: int = 14):
        """
        Finds disturbances within given parameters
        Returns a list holding all disturbances found
        """

        # Get the collection of states from the mongo db
        # A state holds all plane information (callsign, location, altitude, etc..) on a specific timestamp
        # The time is the key value of a state and is ordered accordingly in the mongo database
        # Time is an int64 holding the timestamp in the following format %Y%m%d%H%M%S
        states_collection = self.mongo_client[self.environment.mongodb_config.database][
            self.environment.mongodb_config.collection]
        cursor = states_collection.find({'Time': {'$gte': convert_datetime_to_int(begin)}})

        #
        all_found_disturbances = []

        # Disturbances is a dictionary with plane callsign as key value and the integer timestamp as value
        disturbances: dict = {}

        # Array of DisturbancePeriod data classes holding information about all disturbance periods found in database
        disturbance_periods: list = []

        # Amount of disturbances recorded
        disturbance_hits: int = 0

        # If the disturbance threshold is reached, and we're currently iterating through a disturbance period
        in_disturbance: bool = False

        # Callsigns in current disturbance period
        callsigns_in_disturbance: list = []

        # Total altitude, this is used to compute the average altitude measured in a disturbance period
        total_altitude: int = 0

        # Signifies if during this timestamp, a disturbance is detected
        disturbance_in_this_timestamp: bool = False

        # The last timestamp found
        last_timestamp: datetime = None

        # The timestamp of the beginning of a disturbance period
        disturbance_begin: datetime = None

        # The timestamp of the last disturbance occurrence found
        last_disturbance: datetime = None

        # Iterate through states
        for document in cursor:
            # Get timestamp as integer value and as datetime object
            timestamp_int = document['Time']
            timestamp = utils.convert_int_to_datetime(timestamp_int)

            # bail if timestamp exceeded end
            if timestamp > end:
                break

            # Get all states
            states = document['States']

            # Signifies if during this timestamp, a disturbance is detected
            disturbance_in_this_timestamp = False

            # Iterate through states
            for state in states:
                # Get callsign
                callsign = state['callsign']

                # Obtain altitude
                geo_altitude = state['geo_altitude']

                # Obtain icao24
                icao24 = utils.xstr(state['icao24'])

                # Ignore grounded planes
                if geo_altitude is None:
                    continue

                # Check if altitude is lower than altitude and if distance is within specified radius
                if geo_altitude < altitude:
                    # Obtain lat lon from location to compute distance from complainant origin
                    coord = (state['latitude'], state['longitude'])
                    distance = geopy.distance.great_circle(origin, coord).meters

                    if distance < radius:
                        # A disturbance is detected, check if it is a new plane in this disturbance period
                        if not utils.list_contains_value(callsigns_in_disturbance, callsign):
                            disturbance_hits += 1
                            callsigns_in_disturbance.append(callsign)

                        total_altitude += geo_altitude

                        # Check if there already is a disturbance in this timeframe, otherwise create a new
                        # disturbance
                        disturbance_in_this_timestamp = True
                        if not in_disturbance:
                            in_disturbance = True
                            disturbance_begin = timestamp
                            last_disturbance = timestamp
                        else:
                            last_disturbance = timestamp

                        # if callsign is not already logged for this disturbance, do it now
                        if callsign not in disturbances.keys():
                            disturbances[callsign] = {'timestamp': timestamp_int,
                                                      'altitude': geo_altitude,
                                                      'icao24': icao24}

            # Check if disturbance has ended and if we need to generate a complaint within set parameters
            if not disturbance_in_this_timestamp:
                # There is no disturbance in this timestamp, if we're currently in a disturbance period
                # check if this needs to end, and we can log store this period as a disturbance period
                if in_disturbance:
                    diff_since_last = last_timestamp - last_disturbance
                    if (diff_since_last.seconds / 60) >= timeframe:
                        if disturbance_hits >= occurrences:
                            disturbance_period = DisturbancePeriod(user=title,
                                                                   disturbances=disturbances.copy(),
                                                                   begin=disturbance_begin,
                                                                   end=last_disturbance,
                                                                   flights=disturbance_hits,
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

        if in_disturbance:
            disturbance_duration = last_disturbance - disturbance_begin
            if disturbance_hits >= occurrences:
                if (disturbance_duration.seconds / 60) > timeframe:
                    disturbance_period = DisturbancePeriod(user=title,
                                                           disturbances=disturbances.copy(),
                                                           begin=disturbance_begin,
                                                           end=last_disturbance,
                                                           flights=disturbance_hits,
                                                           average_altitude=total_altitude / disturbance_hits)
                    disturbance_periods.append(disturbance_period)

        # Calc trajectories for callsigns
        for disturbance_period in disturbance_periods:
            # Holds all callsigns for this period
            callsigns: list = []

            # Calc disturbance duration
            disturbance_duration = disturbance_period.end - disturbance_period.begin
            logging.info('User %s : Disturbance detected. %i flights and a total duration of %i minutes. '
                         'Disturbance began at %s and ended at %s' %
                         (title, len(disturbance_period.disturbances.items()),
                          (disturbance_duration.seconds / 60),
                          disturbance_period.begin.__str__(), disturbance_period.end.__str__()))

            # Create plot if necessary
            if plot:
                # Create trajectories for complaint
                logging.info(
                    'Collecting trajectories for %i flights' % (len(disturbance_period.disturbances.items())))
                for callsign, entry in disturbance_period.disturbances.items():
                    trajectory: Trajectory = Trajectory()
                    trajectory.callsign = callsign
                    trajectory.average_altitude = 0

                    # Get timestamp
                    timestamp_int = entry['timestamp']

                    # Limit results to cap trajectory, if interval is set to 22 seconds,
                    # a limit of 15 will be +- 5 minutes, which should be more than enough
                    items_after = states_collection.find({'Time': {'$gte': timestamp_int}}).limit(15)
                    items_before = states_collection.find({'Time': {'$lte': timestamp_int}}).sort(
                        [('Time', pymongo.DESCENDING)]).limit(15)

                    # coordinates will be stored here
                    coords: list = []

                    # First iterate over the past, insert coordinates
                    for doc in items_before:
                        timestamp_int = doc['Time']
                        older_states = doc['States']
                        trajectory_complete = False
                        callsign_found_in_states = False
                        for older_state in older_states:
                            if older_state['callsign'] == callsign:
                                new_altitude = older_state['geo_altitude']
                                if new_altitude is not None:
                                    # Obtain lat lon from location to compute distance from complainant origin
                                    old_coord = (older_state['latitude'], older_state['longitude'])
                                    distance = geopy.distance.great_circle(origin, old_coord).meters
                                    coords.insert(0, (old_coord[1], old_coord[0]))
                                    trajectory.average_altitude += new_altitude
                                    if distance > radius * 2:
                                        trajectory_complete = True
                                callsign_found_in_states = True

                        # Callsign not preset or distance is outside radius, finish
                        if trajectory_complete or callsign_found_in_states is False:
                            break

                    # Iterate over the future, append coordinates
                    for doc in items_after:
                        timestamp_int = doc['Time']
                        newer_states = doc['States']
                        trajectory_complete = False
                        callsign_found_in_states = False
                        for newer_state in newer_states:
                            if newer_state['callsign'] == callsign:
                                new_altitude = newer_state['geo_altitude']
                                if new_altitude is not None:
                                    # Obtain lat lon from location to compute distance from complainant origin
                                    new_coord = (newer_state['latitude'], newer_state['longitude'])
                                    distance = geopy.distance.great_circle(origin, new_coord).meters
                                    coords.append((new_coord[1], new_coord[0]))
                                    trajectory.average_altitude += new_altitude
                                    if distance > radius * 2:
                                        trajectory_complete = True
                                callsign_found_in_states = True

                        # Callsign not preset or distance is outside radius, finish
                        if trajectory_complete or callsign_found_in_states is False:
                            break

                    # Calculate
                    coord_num = len(coords)
                    trajectory.coords = coords
                    if coord_num > 0:
                        trajectory.average_altitude /= coord_num

                    # Add it to the trajectories of this complaint and store callsign
                    disturbance_period.trajectories[callsign] = trajectory
                    callsigns.append(CallsignInfo(callsign=callsign,
                                                  datetime=timestamp_int,
                                                  altitude=trajectory.average_altitude,
                                                  icao24=entry['icao24']))
            else:
                for callsign, entry in disturbance_period.disturbances.items():
                    callsigns.append(CallsignInfo(callsign=callsign,
                                                  datetime=entry['timestamp'],
                                                  altitude=entry['altitude'],
                                                  icao24=entry['icao24']))

            if plot:
                # Set the bounding box for our area of interest
                bbox = utils.get_geo_bbox_around_coord(origin=origin, radius=radius / 1000.0)

                # Make plot of all callsign trajectories
                logging.info('Generating disturbance period plot with title %s', title)
                disturbance_period.plot = plot_trajectories(bbox=bbox,
                                                            trajectories=disturbance_period.trajectories,
                                                            origin=origin,
                                                            begin=disturbance_period.begin,
                                                            end=disturbance_period.end,
                                                            tile_zoom=zoomlevel)

            # Create disturbance
            disturbance: Disturbance = Disturbance()
            disturbance.begin = disturbance_period.begin.__str__()
            disturbance.end = disturbance_period.end.__str__()
            disturbance.callsigns = callsigns
            if plot:
                disturbance.img = str(base64.b64encode(disturbance_period.plot), 'UTF-8')
            else:
                disturbance.img = {}
            all_found_disturbances.append(disturbance)

        # Finally return all found disturbances
        return all_found_disturbances
