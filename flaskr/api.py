import multiprocessing
from datetime import timedelta
from multiprocessing import Process
import requests
from flasgger import swag_from
from flask import Blueprint, request
from flask_cors import cross_origin

import flaskr.environment
from flaskr.utils.latloncache import LatLonCache
from ovm.disturbancefinder import DisturbanceFinder
from ovm.environment import load_environment
from ovm.utils import convert_int_to_datetime

# Create api page
api_page = Blueprint('api', __name__, template_folder='templates')

# Load environment
environment = load_environment('environment.json')

# Get latlon cache
latlon_cache = LatLonCache(environment=environment,
                           expire_days=flaskr.environment.LATLON_CACHE_EXPIRATION_DAYS)


@swag_from('swagger/find_disturbances.yml', methods=['GET'])
@api_page.route('/api/find_disturbances')
@cross_origin()
def find_disturbances_api():
    """
    The find_disturbances API call
    :return: response data
    """
    return execute(function=find_disturbances_process,
                   args=request.args)


@swag_from('swagger/find_flights.yml', methods=['GET'])
@api_page.route('/api/find_flights')
@cross_origin()
def find_flights_api():
    """
    The find_flights API call
    :return: response data
    """
    return execute(function=find_flights_process,
                   args=request.args)


@swag_from('swagger/get_trajectory.yml', methods=['GET'])
@api_page.route('/api/get_trajectory')
@cross_origin()
def get_trajectory_api():
    """
    The get_trajectory API call
    :return: response data
    """
    return execute(function=get_trajectory_process,
                   args=request.args)


def find_disturbances_process(shared_queue, args):
    """
    Process of finding disturbances, exits on error or completion
    :param shared_queue: the shared_queue where data will be put
    :param args: arguments
    """
    try:
        # Sanity check input
        modified_args = process_input(args, extra_args=['occurrences', 'timeframe'])

        # Get input
        user = modified_args['user']
        lat = float(modified_args['lat'])
        lon = float(modified_args['lon'])
        radius = int(modified_args['radius'])
        altitude = int(modified_args['altitude'])
        begin = int(modified_args['begin'])
        end = int(modified_args['end'])
        occurrences = int(modified_args['occurrences'])
        timeframe = int(modified_args['timeframe'])

        zoomlevel = 14
        if modified_args['zoomlevel'] is not None:
            zoomlevel = int(modified_args['zoomlevel'])
        plot = False
        if args['plot'] is not None:
            plot = bool(int(modified_args['plot']))

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


def find_flights_process(shared_queue, args):
    """
    Process of finding flights, exits on error or completion
    :param shared_queue: the shared_queue where data will be put
    :param args: arguments
    """

    try:
        # Sanity check input
        modified_args = process_input(args)

        # Get input
        user = modified_args['user']
        lat = float(modified_args['lat'])
        lon = float(modified_args['lon'])
        radius = int(modified_args['radius'])
        altitude = int(modified_args['altitude'])
        begin = int(modified_args['begin'])
        end = int(modified_args['end'])

        # Get optional args
        zoomlevel = 14
        if modified_args['zoomlevel'] is not None:
            zoomlevel = int(modified_args['zoomlevel'])
        plot = False
        if args['plot'] is not None:
            plot = bool(int(modified_args['plot']))

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


def get_trajectory_process(shared_queue, args):
    """
    Process of finding trajectories of flights, exits on error or completion
    :param shared_queue: the shared_queue where data will be put
    :param args: arguments
    """
    try:
        # Get input
        callsign = str(args['callsign'])
        timestamp = int(args['timestamp'])
        duration = int(args['duration'])

        # Get timestamp datetime
        timestamp_dt = convert_int_to_datetime(timestamp)

        disturbance_finder: DisturbanceFinder = DisturbanceFinder(environment)
        coords = disturbance_finder.get_trajectory(callsign=callsign,
                                                   timestamp=timestamp_dt,
                                                   duration=duration)
        shared_queue.put(coords)
        exit(0)
    except Exception as ex:
        shared_queue.put(ex.__str__())
        exit(1)


def execute(function, args):
    """
    All api calls get executed by this function
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

    # Create response dict
    response = ***REMOVED******REMOVED***

    # Try and execute the API call and fill response object
    try:
        response['value'] = task(function, args)
        response['status'] = 'OK'
    except Exception as e:
        response['value'] = e.__str__()
        response['status'] = 'ERROR'

    # Return response object
    return response


def task(function, args):
    """
    A Task encapsulates an api call and expects a result to be put in a shared queue
    We create a new process because matplotlib cannot run from multiple threads within the same context
    :param function: the api function call
    :param args: the arguments
    :return: the data returned by the function, data has error string if exception is raised
    """

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

    return data


def get_lat_lon_from_pro6pp(args):
    """
    Queries lat and lon from given postalcode and streetnumber
    Uses pro6pp (https://www.pro6pp.nl/)
    Raises exception on error
    :param args: dict, except postalcode and streetnumber as keys
    :return: latitude and longitude
    """

    postalcode = args['postalcode']

    # remove whitespaces from postal code
    postalcode = postalcode.lstrip().rstrip()
    postalcode = postalcode.replace(' ', '')
    address_key = postalcode + args.get('streetnumber', type=str, default='')

    if latlon_cache.address_valid(address_key):
        return latlon_cache.get_latlon_from_address(address_key)
    else:
        if len(postalcode) == 6 and args.get('streetnumber', type=str) is not None:
            streetnumber = str(args['streetnumber'])

            # Remove characters from streetnumber
            numbers = [int(s) for s in streetnumber if s.isdigit()]
            if len(numbers) <= 0:
                raise Exception('No numbers found in streetnumber')

            number: str = ''
            for n in numbers:
                number += str(n)

            url = '%s?' \
                  'authKey=%s&' \
                  'postalCode=%s&' \
                  'streetNumberAndPremise=%s' % \
                  (flaskr.environment.PRO6PP_API_AUTO_COMPLETE_URL,
                   flaskr.environment.PRO6PP_AUTH_KEY,
                   postalcode, number)

            data = requests.get(url).json()

            if 'lat' not in data or 'lng' not in data:
                err = 'Could not get latitude or longitude from pro6pp server'
                if 'error_id' in data:
                    err += ' : ' + data['error_id']
                raise Exception(err)

            latlon_cache.add_or_update_address(address_key, (data['lat'], data['lng']))
            return data['lat'], data['lng']
        elif len(postalcode) == 4 or len(postalcode) == 6:
            postalcode = postalcode[0:4]
            url = '%s?' \
                  'authKey=%s&' \
                  'targetPostalCodes=%s&' \
                  'postalCode=%s' % \
                  (flaskr.environment.PRO6PP_API_AUTO_LOCATOR_URL,
                   flaskr.environment.PRO6PP_AUTH_KEY,
                   postalcode, postalcode)

            response = requests.get(url).json()

            if isinstance(response, list):
                if len(response) >= 1:
                    data = response[0]
                    if 'lat' not in data or 'lng' not in data:
                        err = 'Could not get latitude or longitude from pro6pp server'
                        if 'error_id' in data:
                            err += ' : ' + data['error_id']
                        raise Exception(err)

                    latlon_cache.add_or_update_address(address_key, (data['lat'], data['lng']))
                    return data['lat'], data['lng']
                else:
                    raise Exception('Returned list is empty')
            else:
                err = 'Invalid response from pro6pp'
                if 'error_id' in response:
                    err += ' : ' + response['error_id']
                raise Exception(err)

    raise Exception('No valid data supplied to get lat, lon from postalcode')


def process_input(args, extra_args: list = []):
    """
    Sanity checks API call input, raises exception if input is not within specs
    Gets lat, lon from pro6pp if postalcode is given
    TODO: define specs somewhere
    """
    args_mutable_dict = dict(args)

    # Sanity check input

    if args.get('postalcode', type=str) is None:
        if args.get('lat', type=float) is None:
            raise Exception('lat cannot be None if no postalcode and/or streetnumber is given')

        if args.get('lon', type=float) is None:
            raise Exception('lon cannot be None if no postalcode  and/or postal code is given')
    elif args.get('lat', type=float) is None or args.get('lon', type=float) is None:
        if args.get('postalcode') is None:
            raise Exception('postalcode cannot be None if no lat, lon is given')

    # postalcode and streetnumber override lat-lon
    if args.get('postalcode', type=str) is not None:
        data = get_lat_lon_from_pro6pp(args)
        args_mutable_dict['lat'] = data[0]
        args_mutable_dict['lon'] = data[1]

    if args.get('radius', type=int) is None:
        raise Exception('radius cannot be None')

    if args.get('altitude', type=int) is None:
        raise Exception('altitude cannot be None')

    if args.get('begin', type=int) is None:
        raise Exception('begin cannot be None')

    if args.get('begin', type=int) is None:
        raise Exception('end cannot be None')

    for extra_arg in extra_args:
        if args.get(extra_arg) is None:
            raise Exception('Expected %s argument but key is not present' % extra_arg)

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
    if radius > 5000:
        raise Exception('Radius may not be larger than %i meters' % 4000)
    if radius < 500:
        raise Exception('Radius cannot be smaller than %i meters' % 500)

    # Sanity check altitude
    if altitude < 100:
        raise Exception('Altitude cannot be smaller than %i meters' % 100)

    return args_mutable_dict
