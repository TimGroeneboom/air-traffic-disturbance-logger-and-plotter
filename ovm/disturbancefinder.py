import base64
import collections
import logging
from dataclasses import dataclass, field
from datetime import datetime
import geopy.distance
import pymongo
from pymongo import MongoClient
from ovm import utils
from ovm.disturbanceperiod import DisturbancePeriod, Disturbances, Disturbance, Callsign
from ovm.environment import Environment
from ovm.plotter import plot_trajectories
from ovm.complainant import Complainant
from ovm.trajectory import Trajectory
from ovm.utils import convert_datetime_to_int


@dataclass
class StateIterator:
    """"
    The state iterator is used per complainant while iterating over MongoDB documents
    The reason to use this is that we want to iterate over the database one, collecting all disturbance periods
    for every given complainant
    """

    # Disturbances is a dictionary with plane callsign as key value and the integer timestamp as value
    disturbances: dict = field(default_factory=dict)

    # Array of DisturbancePeriod data classes holding information about all disturbance periods found in database
    disturbance_periods: list = field(default_factory=list)

    # Amount of disturbances recorded
    disturbance_hits: int = field(default=0)

    # If the disturbance threshold is reached, and we're currently iterating through a disturbance period
    in_disturbance: bool = field(default=False)

    # Callsigns in current disturbance period
    callsigns_in_disturbance: list = field(default_factory=list)

    # Total altitude, this is used to compute the average altitude measured in a disturbance period
    total_altitude: int = field(default=0)

    # Signifies if during this timestamp, a disturbance is detected
    disturbance_in_this_timestamp: bool = field(default=False)

    # The last timestamp found
    last_timestamp: datetime = None

    # The timestamp of the beginning of a disturbance period
    disturbance_begin: datetime = None

    # The timestamp of the last disturbance occurrence found
    last_disturbance: datetime = None

    # The complainant associated with this disturbance iterator
    complainant: Complainant = None


class DisturbanceFinder:
    """
    The DisturbanceFinder finds all disturbances that match the complainant parameters (see @Complainant) It connects
    with the mongo db and iterates through all records found within given begin and end time It generates a
    Disturbance object (see @Disturbance), containing a plotted graph of all flights encoded as a jpg image alongside
    some meta-information
    """

    # parameterized constructor
    def __init__(self, environment: Environment):
        # Set environment
        self.environment = environment

        # Create MongoDB client
        self.mongo_client = MongoClient(environment.mongodb_config.host,
                                        environment.mongodb_config.port)

        # TODO: get callsigns to ignore from database
        # Ignore certain callsigns
        self.ignore_callsigns = [
            'LIFELN1'
        ]

    def find_flights(self,
                     origin: tuple,
                     begin: datetime,
                     end: datetime,
                     radius: int,
                     altitude: int,
                     plot: bool = False,
                     title: str = '',
                     zoomlevel: int = 14):
        """

        """

        # Create disturbances
        disturbances: Disturbances = Disturbances()
        disturbance: Disturbance = Disturbance()
        disturbances.disturbances.append(disturbance)
        disturbance.begin = begin.strftime("%Y-%m-%d %H:%M:%S")
        disturbance.end = end.strftime("%Y-%m-%d %H:%M:%S")

        #
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

                # Ignore specified callsigns
                if utils.list_contains_value(arr=self.ignore_callsigns,
                                             value=callsign):
                    continue

                # Obtain altitude
                geo_altitude = state['geo_altitude']

                # Ignore grounded planes
                if geo_altitude is None:
                    continue

                # obtain flight coordinate
                flight_coord = (state['latitude'], state['longitude'])

                # Ignore if callsign already present
                if not utils.list_contains_value(disturbance.callsigns, callsign):
                    # Check if altitude is lower than altitude and if distance is within specified radius
                    if geo_altitude < altitude:
                        # Obtain lat lon from location to compute distance from complainant origin
                        distance = geopy.distance.distance(origin, flight_coord).meters
                        if distance < radius:
                            disturbance.callsigns.append(Callsign(callsign, timestamp_int))

                            # obtain trajectory if plot is needed
                            if plot:
                                trajectories[callsign] = Trajectory()
                                trajectories[callsign].callsign = callsign
                                trajectories[callsign].coords.append((flight_coord[1], flight_coord[0]))
                                trajectories[callsign].average_altitude += geo_altitude

                                timestamp_int = document['Time']
                                items_before = states_collection.find({'Time': {'$gte': timestamp_int}}).limit(4)
                                items_after = states_collection.find({'Time': {'$lte': timestamp_int}}).sort(
                                    [('Time', pymongo.DESCENDING)]).limit(4)
                                dictionary = {}
                                for doc in items_before:
                                    timestamp_int = doc['Time']
                                    if timestamp_int not in dictionary.keys():
                                        dictionary[timestamp_int] = doc['States']
                                for doc in items_after:
                                    timestamp_int = doc['Time']
                                    if timestamp_int not in dictionary.keys():
                                        dictionary[timestamp_int] = doc['States']

                                ordered_dict = collections.OrderedDict(sorted(dictionary.items()))
                                for key, value in ordered_dict.items():
                                    for other_state in value:
                                        if utils.remove_whitespace(other_state['callsign']) == callsign:
                                            new_altitude = other_state['geo_altitude']
                                            if new_altitude is not None:
                                                # Obtain lat lon from location to compute distance from complainant origin
                                                new_coord = (other_state['latitude'], other_state['longitude'])
                                                distance = geopy.distance.distance(origin, new_coord)
                                                if distance < radius * 2:
                                                    trajectories[callsign].average_altitude += new_altitude
                                                    trajectories[callsign].coords.append((new_coord[1], new_coord[0]))

                                coord_num = len(trajectories[callsign].coords)
                                if coord_num > 0:
                                    trajectories[callsign].average_altitude /= len(trajectories[callsign].coords)

        if plot:
            # Set the bounding box for our area of interest, add an extra meters/padding for a better view of
            # trajectories
            bbox = utils.get_geo_bbox_around_coord(origin, (radius + 1000) / 1000.0)

            # Make plot of all callsign trajectories
            logging.info('Generating trajectory plot')
            image = plot_trajectories(bbox=bbox,
                                      title=title,
                                      origin=origin,
                                      begin=begin,
                                      end=end,
                                      trajectories=trajectories,
                                      tile_zoom=zoomlevel)
            disturbance.img = str(base64.b64encode(image), 'UTF-8')
        else:
            disturbance.img = None

        return disturbances

    def find_disturbances(self,
                          begin: datetime,
                          end: datetime,
                          complainants: list,
                          plot: bool = True,
                          zoomlevel: int = 14):
        """
        Finds disturbances for all complainants given
        Returns a Disturbances object, holding all disturbances found
        :param begin: begin date & time of when to check for disturbances
        :param end: end date & time
        :param complainants: a list of complainants, als see @Complainant
        :param plot: boolean indicating to generate a plot or not
        :param zoomlevel: the zoomlevel of the plot
        :return: a Disturbances object, holding all disturbances found
        """

        # The return dictionary, will be dumped as json
        disturbances: dict = {}

        # Get the collection of states from the mongo db
        # A state holds all plane information (callsign, location, altitude, etc..) on a specific timestamp
        # The time is the key value of a state and is ordered accordingly in the mongo database
        # Time is an int64 holding the timestamp in the following format %Y%m%d%H%M%S
        states_collection = self.mongo_client[self.environment.mongodb_config.database][
            self.environment.mongodb_config.collection]
        cursor = states_collection.find({'Time': {'$gte': convert_datetime_to_int(begin)}})

        # Log user info
        logging.info('Checking disturbances for %i users' % len(complainants))

        # Create disturbance iterator for each complainent
        state_iterators: dict = {}
        for complainant in complainants:
            state_iterator = StateIterator()
            state_iterator.complainant = complainant
            state_iterators[complainant.user] = state_iterator

        last_timestamp: datetime = None

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

            # Iterate through disturbance iterator
            for user, state_iterator in state_iterators.items():
                # Signifies if during this timestamp, a disturbance is detected
                state_iterator.disturbance_in_this_timestamp = False

                # Iterate through states
                for state in states:
                    # Get callsign
                    callsign = utils.remove_whitespace(state['callsign'])

                    geo_altitude = state['geo_altitude']

                    # Ignore grounded planes
                    if geo_altitude is None:
                        continue

                    # Ignore specified callsigns
                    if utils.list_contains_value(arr=self.ignore_callsigns, value=callsign):
                        continue

                    # Check if altitude is lower than altitude and if distance is within specified radius
                    if geo_altitude < state_iterator.complainant.altitude:
                        # Obtain lat lon from location to compute distance from complainant origin
                        coord = (state['latitude'], state['longitude'])
                        distance = geopy.distance.distance(state_iterator.complainant.origin, coord).meters

                        if distance < state_iterator.complainant.radius:
                            # A disturbance is detected, check if it is a new plane in this disturbance period
                            if not utils.list_contains_value(state_iterator.callsigns_in_disturbance, callsign):
                                state_iterator.disturbance_hits += 1
                                state_iterator.callsigns_in_disturbance.append(callsign)

                            state_iterator.total_altitude += geo_altitude

                            # Check if there already is a disturbance in this timeframe, otherwise create a new
                            # disturbance
                            state_iterator.disturbance_in_this_timestamp = True
                            if not state_iterator.in_disturbance:
                                state_iterator.in_disturbance = True
                                state_iterator.disturbance_begin = timestamp
                                state_iterator.last_disturbance = timestamp
                            else:
                                state_iterator.last_disturbance = timestamp

                            # if callsign is not already logged for this disturbance, do it now
                            if callsign not in state_iterator.disturbances.keys():
                                state_iterator.disturbances[callsign] = timestamp_int

                # Check if disturbance has ended and if we need to generate a complaint within set parameters
                if not state_iterator.disturbance_in_this_timestamp:
                    # There is no disturbance in this timestamp, if we're currently in a disturbance period
                    # check if this needs to end, and we can log store this period as a disturbance period
                    if state_iterator.in_disturbance:
                        diff_since_last = last_timestamp - state_iterator.last_disturbance
                        if (diff_since_last.seconds / 60) >= complainant.timeframe:
                            if state_iterator.disturbance_hits >= complainant.occurrences:
                                disturbance_period = DisturbancePeriod(complainant=state_iterator.complainant,
                                                                       disturbances=state_iterator.disturbances.copy(),
                                                                       begin=state_iterator.disturbance_begin,
                                                                       end=state_iterator.last_disturbance,
                                                                       flights=state_iterator.disturbance_hits,
                                                                       average_altitude=state_iterator.total_altitude / state_iterator.disturbance_hits)
                                state_iterator.disturbance_periods.append(disturbance_period)

                            state_iterator.in_disturbance = False
                            state_iterator.disturbance_begin = None
                            state_iterator.last_disturbance = None
                            state_iterator.disturbance_hits = 0
                            state_iterator.total_altitude = 0
                            state_iterator.disturbances = {}
                            state_iterator.callsigns_in_disturbance = []

            last_timestamp = timestamp

        for user, state_iterator in state_iterators.items():
            if state_iterator.in_disturbance:
                disturbance_duration = state_iterator.last_disturbance - state_iterator.disturbance_begin
                if state_iterator.disturbance_hits >= complainant.occurrences:
                    if (disturbance_duration.seconds / 60) > complainant.timeframe:
                        disturbance_period = DisturbancePeriod(complainant=state_iterator.complainant,
                                                               disturbances=state_iterator.disturbances.copy(),
                                                               begin=state_iterator.disturbance_begin,
                                                               end=state_iterator.last_disturbance,
                                                               flights=state_iterator.disturbance_hits,
                                                               average_altitude=state_iterator.total_altitude / state_iterator.disturbance_hits)
                        state_iterator.disturbance_periods.append(disturbance_period)

            # Calc trajectories for callsigns
            for disturbance_period in state_iterator.disturbance_periods:
                # Holds all callsigns for this period
                callsigns: list = []

                # Calc disturbance duration
                disturbance_duration = disturbance_period.end - disturbance_period.begin
                logging.info('User %s : Disturbance detected. %i flights and a total duration of %i minutes. '
                             'Disturbance began at %s and ended at %s' %
                             (disturbance_period.complainant.user, len(disturbance_period.disturbances.items()),
                              (disturbance_duration.seconds / 60),
                              disturbance_period.begin.__str__(), disturbance_period.end.__str__()))

                # Create plot if necessary
                if plot:
                    # Create trajectories for complaint
                    logging.info(
                        'Collecting trajectories for %i flights' % (len(disturbance_period.disturbances.items())))
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
                        trajectory: Trajectory = Trajectory()
                        trajectory.callsign = callsign
                        trajectory.average_altitude = 0
                        ordered_dict = collections.OrderedDict(sorted(dictionary.items()))
                        for key, value in ordered_dict.items():
                            for state in value:
                                if utils.remove_whitespace(state['callsign']) == callsign:
                                    if state['geo_altitude'] is not None:
                                        trajectory.coords.append((state['longitude'], state['latitude']))
                                        trajectory.average_altitude += state['geo_altitude']

                        # Add it to the trajectories of this complaint and store callsign
                        trajectory.average_altitude /= len(trajectory.coords)
                        disturbance_period.trajectories[callsign] = trajectory
                        callsigns.append(Callsign(callsign, datetime_int))
                else:
                    for callsign, datetime_int in disturbance_period.disturbances.items():
                        callsigns.append(Callsign(callsign, datetime_int))

                if plot:
                    # Set the bounding box for our area of interest, add an extra meters/padding for a better view of
                    # trajectories
                    bbox = utils.get_geo_bbox_around_coord(disturbance_period.complainant.origin,
                                                           (complainant.radius + 1000) / 1000.0)

                    # Make plot of all callsign trajectories
                    logging.info('Generating disturbance period plot for user %s',
                                 disturbance_period.complainant.user)
                    disturbance_period.plot = plot_trajectories(bbox=bbox,
                                                                trajectories=disturbance_period.trajectories,
                                                                origin=disturbance_period.complainant.origin,
                                                                title=disturbance_period.complainant.user,
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

                if not disturbance_period.complainant.user in disturbances:
                    disturbances[disturbance_period.complainant.user] = Disturbances()
                disturbances[disturbance_period.complainant.user].disturbances.append(disturbance)

        # Finally return all found disturbances
        return disturbances
