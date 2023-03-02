import json
import multiprocessing
from datetime import datetime
from time import sleep
from flasgger import swag_from
from flask import Blueprint, request
from flaskr.atomicinteger import AtomicInteger
from ovm.complainant import Complainant
from ovm.disturbancefinder import DisturbanceFinder
from ovm.environment import load_environment
from ovm.utils import convert_int_to_datetime
from multiprocessing import Pool, Process
from multiprocessing import Value

# Create api page
api_page = Blueprint('api', __name__, template_folder='templates')

# Load environment
environment = load_environment('environment.json')

# Max active workers, requests will wait and hold
max_workers: int = 8

# Atomic integer, counting current active workers
worker_count: AtomicInteger = AtomicInteger(0)


def execute(function, args):
    """
    All api calls get executed by this function
    Waits if max worker threads has exceeded
    Returns response object in json on success
    ***REMOVED***
        status: 'OK',
        value: <string> <-- JSON string
  ***REMOVED***
    Returns response object in json on failure
    ***REMOVED***
        status: 'ERROR',
        value: <string> <-- failure description
  ***REMOVED***
    :param function: function to execute
    :param args: arguments that need to be passed into the function
    :return: response object with status and value
    """

    # Wait 100 millis for worker to finish
    while worker_count.value >= max_workers:
        sleep(0.1)

    # Increment worker count
    worker_count.inc(1)

    # Create response dict
    response = ***REMOVED******REMOVED***

    # Try and execute the API call and fill response object
    try:
        # We fire up a new thread, because matplotlib needs this in order to use it from
        # multiple threads

        # Create a queue to share data with between this and new process
        shared_queue = multiprocessing.Queue()

        # Create & start process
        process = Process(target=function, args=(shared_queue, args))
        process.start()

        # Get data from process
        data = shared_queue.get()

        # Join and close process
        process.join()

        # Some exception occurred if exit code is not 0
        # data will be exception message, pass it on
        if process.exitcode != 0:
            process.close()
            raise Exception(data)

        # Finally close the process
        process.close()

        # At this point we can assume the data is valid
        response['value'] = data
        response['status'] = 'OK'
    except Exception as e:
        response['value'] = e.__str__()
        response['status'] = 'ERROR'

    # Decrement worker count
    worker_count.dec(1)

    # Return response object
    return response


def find_disturbances_process(shared_queue, args):
    try:
        # Sanity check input
        if args['user'] is None:
            raise Exception('User cannot be None')
        user = args['user']

        if args['lat'] is None:
            raise Exception('lat cannot be None')
        lat = float(args['lat'])

        if args['lon'] is None:
            raise Exception('lon cannot be None')
        lon = float(args['lon'])

        if args['radius'] is None:
            raise Exception('lon cannot be None')
        radius = int(args['radius'])

        if args['altitude'] is None:
            raise Exception('altitude cannot be None')
        altitude = int(args['altitude'])

        if args['occurrences'] is None:
            raise Exception('occurrences cannot be None')
        occurrences = int(args['occurrences'])

        if args['timeframe'] is None:
            raise Exception('timeframe cannot be None')
        timeframe = int(args['timeframe'])

        if args['begin'] is None:
            raise Exception('begin cannot be None')
        begin = int(args['begin'])

        if args['end'] is None:
            raise Exception('end cannot be None')
        end = int(args['end'])

        zoomlevel = 14
        if args['zoomlevel'] is not None:
            zoomlevel = int(args['zoomlevel'])
        plot = False
        if args['plot'] is not None:
            plot = bool(int(args['plot']))

        complainants = [Complainant(user=user,
                                    origin=(lat, lon),
                                    radius=radius,
                                    altitude=altitude,
                                    occurrences=occurrences,
                                    timeframe=timeframe)]

        disturbance_finder: DisturbanceFinder = DisturbanceFinder(environment)
        disturbances = disturbance_finder.find_disturbances(begin=convert_int_to_datetime(begin),
                                                            end=convert_int_to_datetime(end),
                                                            complainants=complainants,
                                                            zoomlevel=zoomlevel,
                                                            plot=plot)
        shared_queue.put(disturbances)
        exit(0)
    except Exception as ex:
        shared_queue.put(ex.__str__())
        exit(1)


@swag_from('swagger/find_disturbances.yml', methods=['GET'])
@api_page.route('/api/find_disturbances')
def find_disturbances_api():
    return execute(function=find_disturbances_process,
                   args=request.args)


def find_flights_process(shared_queue, args):
    try:
        # Sanity check input
        if args['user'] is None:
            raise Exception('User cannot be None')
        user = args['user']

        if args['lat'] is None:
            raise Exception('lat cannot be None')
        lat = float(args['lat'])

        if args['lon'] is None:
            raise Exception('lon cannot be None')
        lon = float(args['lon'])

        if args['begin'] is None:
            raise Exception('begin cannot be None')
        begin = int(args['begin'])

        if args['end'] is None:
            raise Exception('end cannot be None')
        end = int(args['end'])

        if args['radius'] is None:
            raise Exception('radius cannot be None')
        radius = int(args['radius'])

        if args['altitude'] is None:
            raise Exception('altitude cannot be None')
        altitude = int(args['altitude'])

        zoomlevel = 14
        if args['zoomlevel'] is not None:
            zoomlevel = int(args['zoomlevel'])
        plot = False
        if args['plot'] is not None:
            plot = bool(int(args['plot']))

        disturbance_finder: DisturbanceFinder = DisturbanceFinder(environment)
        flights = disturbance_finder.find_flights(origin=(lat, lon),
                                                  begin=convert_int_to_datetime(begin),
                                                  end=convert_int_to_datetime(end),
                                                  radius=radius,
                                                  altitude=altitude,
                                                  title=user,
                                                  plot=plot,
                                                  zoomlevel=zoomlevel).disturbances
        shared_queue.put(flights)
        exit(0)
    except Exception as ex:
        shared_queue.put(ex.__str__())
        exit(1)


@swag_from('swagger/find_flights.yml', methods=['GET'])
@api_page.route('/api/find_flights')
def find_flights_api():
    return execute(function=find_flights_process,
                   args=request.args)
