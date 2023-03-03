import json
import multiprocessing
from datetime import datetime, timedelta
from time import sleep
import flaskr.environment
import requests
from flasgger import swag_from
from flask import Blueprint, request
from flaskr.atomicinteger import AtomicInteger
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
    Fires up a new process if worker is available
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

        # Join process
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


def sanity_check_input(args):
    """
    Sanity checks API call input, raises exception if input is not within specs
    TODO: define specs somewhere
    """
    # Sanity check input
    if args['user'] is None:
        raise Exception('User cannot be None')

    if args['lat'] is None:
        raise Exception('lat cannot be None')

    if args['lon'] is None:
        raise Exception('lon cannot be None')

    if args['radius'] is None:
        raise Exception('lon cannot be None')

    if args['altitude'] is None:
        raise Exception('altitude cannot be None')

    if args['begin'] is None:
        raise Exception('begin cannot be None')

    if args['end'] is None:
        raise Exception('end cannot be None')

    radius = int(args['radius'])
    altitude = int(args['altitude'])
    begin_dt = convert_int_to_datetime(int(args['begin']))
    end_dt = convert_int_to_datetime(int(args['end']))

    # Sanity check timespan
    if end_dt - begin_dt > timedelta(hours=24):
        raise Exception('Total timespan may not exceed %i hours' % 24)
    if begin_dt > end_dt:
        raise Exception('Begin cannot be later then end')

    # Sanity check radius
    if radius > 2000:
        raise Exception('Radius may not be larger than %i meters' % 2000)
    if radius < 100:
        raise Exception('Radius cannot be smaller than %i meters' % 100)

    # Sanity check altitude
    if altitude < 100:
        raise Exception('Altitude cannot be smaller than %i meters' % 100)


def get_lat_lon_from_pro6pp(args):
    """
    Queries lat and lon from given postalcode and streetnumber
    Uses pro6pp (https://www.pro6pp.nl/)
    Raises exception on error
    :param args: dict, except postalcode and streetnumber as keys
    :return: latitude and longitude
    """
    if args['postalcode'] is None:
        raise Exception('postalcode cannot be None')
    postalcode = args['postalcode']

    if args['streetnumber'] is None:
        raise Exception('streetnumber cannot be None')
    streetnumber = float(args['streetnumber'])

    url = '%s?' \
          'authKey=%s&' \
          'postalCode=%s&' \
          'streetNumberAndPremise=%i' % \
          (flaskr.environment.PRO6PP_API_URL,
           flaskr.environment.PRO6PP_AUTH_KEY,
           postalcode, streetnumber)

    data = requests.get(url).json()

    if 'lat' not in data or 'lng' not in data:
        err = 'Could not get latitude or longitude from pro6pp server'
        if 'error_id' in data:
            err += ' : ' + data['error_id']
        raise Exception(err)

    return data['lat'], data['lng']


def find_disturbances_process_pro6pp(shared_queue, args):
    """
    Process of finding disturbances using pro6pp query, exits on error or completion
    :param shared_queue: the shared_queue where data will be put
    :param args: arguments
    """
    try:
        lat, lon = get_lat_lon_from_pro6pp(args)
        modified_args = dict(args)
        modified_args['lat'] = lat
        modified_args['lon'] = lon
        find_disturbances_process(shared_queue, modified_args)
    except Exception as ex:
        shared_queue.put(ex.__str__())
        exit(1)


@swag_from('swagger/find_disturbances_pro6pp.yml', methods=['GET'])
@api_page.route('/api/find_disturbances_pro6pp')
def find_disturbances_pro6pp_api():
    """
    The find_disturbances_pro6pp API call
    :return: response data
    """
    return execute(function=find_disturbances_process_pro6pp,
                   args=request.args)


def find_disturbances_process(shared_queue, args):
    """
    Process of finding disturbances, exits on error or completion
    :param shared_queue: the shared_queue where data will be put
    :param args: arguments
    """
    try:
        # Sanity check input
        sanity_check_input(args)

        # Get input
        user = args['user']
        lat = float(args['lat'])
        lon = float(args['lon'])
        radius = int(args['radius'])
        altitude = int(args['altitude'])
        begin = int(args['begin'])
        end = int(args['end'])

        if args['occurrences'] is None:
            raise Exception('occurrences cannot be None')
        occurrences = int(args['occurrences'])

        if args['timeframe'] is None:
            raise Exception('timeframe cannot be None')
        timeframe = int(args['timeframe'])

        zoomlevel = 14
        if args['zoomlevel'] is not None:
            zoomlevel = int(args['zoomlevel'])
        plot = False
        if args['plot'] is not None:
            plot = bool(int(args['plot']))

        begin_dt = convert_int_to_datetime(begin)
        end_dt = convert_int_to_datetime(end)

        disturbance_finder: DisturbanceFinder = DisturbanceFinder(environment)
        disturbances = disturbance_finder.find_disturbances(begin=begin_dt,
                                                            end=end_dt,
                                                            zoomlevel=zoomlevel,
                                                            plot=plot,
                                                            title=user,
                                                            origin=(lat, lon),
                                                            radius=radius,
                                                            altitude=altitude,
                                                            occurrences=occurrences,
                                                            timeframe=timeframe
                                                            )
        shared_queue.put(disturbances)
        exit(0)
    except Exception as ex:
        shared_queue.put(ex.__str__())
        exit(1)


@swag_from('swagger/find_disturbances.yml', methods=['GET'])
@api_page.route('/api/find_disturbances')
def find_disturbances_api():
    """
    The find_disturbances API call
    :return: response data
    """
    return execute(function=find_disturbances_process,
                   args=request.args)


def find_flights_process(shared_queue, args):
    """
    Process of finding flights, exits on error or completion
    :param shared_queue: the shared_queue where data will be put
    :param args: arguments
    """
    try:
        # Sanity check input
        sanity_check_input(args)

        # Get input
        user = args['user']
        lat = float(args['lat'])
        lon = float(args['lon'])
        radius = int(args['radius'])
        altitude = int(args['altitude'])
        begin = int(args['begin'])
        end = int(args['end'])

        # Get optional args
        zoomlevel = 14
        if args['zoomlevel'] is not None:
            zoomlevel = int(args['zoomlevel'])
        plot = False
        if args['plot'] is not None:
            plot = bool(int(args['plot']))

        # Get begin & end datetime
        begin_dt = convert_int_to_datetime(begin)
        end_dt = convert_int_to_datetime(end)

        disturbance_finder: DisturbanceFinder = DisturbanceFinder(environment)
        flights = disturbance_finder.find_flights(origin=(lat, lon),
                                                  begin=begin_dt,
                                                  end=end_dt,
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
    """
    The find_flights API call
    :return: response data
    """
    return execute(function=find_flights_process,
                   args=request.args)


def find_flights_process_pro6pp(shared_queue, args):
    """
    Process of finding flights using pro6pp query, exits on error or completion
    :param shared_queue: the shared_queue where data will be put
    :param args: arguments
    """
    try:
        lat, lon = get_lat_lon_from_pro6pp(args)
        modified_args = dict(args)
        modified_args['lat'] = lat
        modified_args['lon'] = lon
        find_flights_process(shared_queue, modified_args)
    except Exception as ex:
        shared_queue.put(ex.__str__())
        exit(1)


@swag_from('swagger/find_flights_pro6pp.yml', methods=['GET'])
@api_page.route('/api/find_flights_pro6pp')
def find_flights_pro6pp_api():
    """
    The find_flights_pro6pp API call
    :return: response data
    """
    return execute(function=find_flights_process_pro6pp,
                   args=request.args)
