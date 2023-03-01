import json
from datetime import datetime, timedelta
from time import sleep
from flask import Blueprint
from flaskr.atomicinteger import AtomicInteger
from ovm.complainant import Complainant
from ovm.disturbancefinder import DisturbanceFinder
from ovm.environment import load_environment
from ovm.utils import DataclassJSONEncoder, convert_int_to_datetime

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
        response['value'] = function(*args)
        response['status'] = 'OK'
    except Exception as e:
        response['value'] = e.__str__()
        response['status'] = 'ERROR'

    # Decrement worker count
    worker_count.dec(1)

    # Return response object
    return response


def find_disturbance(user,
                     lat,
                     lon,
                     radius,
                     altitude,
                     occurrences,
                     timeframe,
                     plot,
                     zoomlevel):
    complainants = [Complainant(user=user,
                                origin=(lat, lon),
                                radius=radius,
                                altitude=altitude,
                                occurrences=occurrences,
                                timeframe=timeframe)]

    now = datetime.now()
    disturbance_finder: DisturbanceFinder = DisturbanceFinder(environment)
    disturbances = disturbance_finder.find_disturbances(begin=now - timedelta(hours=24),
                                                        end=now,
                                                        complainants=complainants,
                                                        zoomlevel=zoomlevel,
                                                        plot=plot)
    return json.dumps(disturbances, cls=DataclassJSONEncoder, indent=4)


@api_page.route('/api/find_disturbance/<string:user>/'
                '<float:lat>/<float:lon>/'
                '<int:radius>/<int:altitude>/'
                '<int:occurrences>/<int:timeframe>/'
                '<int:plot>/<int:zoomlevel>')
def find_disturbance_api(user,
                         lat,
                         lon,
                         radius,
                         altitude,
                         occurrences,
                         timeframe,
                         plot,
                         zoomlevel):
    return execute(function=find_disturbance,
                   args=(user, lat, lon, radius, altitude, occurrences, timeframe, plot, zoomlevel))


def find_flights(user,
                 lat,
                 lon,
                 radius,
                 altitude,
                 begin,
                 end,
                 plot,
                 zoomlevel):
    disturbance_finder: DisturbanceFinder = DisturbanceFinder(environment)
    flights = disturbance_finder.find_flights(origin=(lat, lon),
                                              begin=convert_int_to_datetime(begin),
                                              end=convert_int_to_datetime(end),
                                              radius=radius,
                                              altitude=altitude,
                                              title=user,
                                              plot=plot,
                                              zoomlevel=zoomlevel)
    return json.dumps(flights, cls=DataclassJSONEncoder, indent=4)


@api_page.route('/api/find_flights/<string:user>/'
                '<float:lat>/<float:lon>/'
                '<int:radius>/<int:altitude>/'
                '<int:begin>/<int:end>/'
                '<int:plot>/<int:zoomlevel>')
def find_flights_api(user,
                     lat,
                     lon,
                     radius,
                     altitude,
                     begin,
                     end,
                     plot,
                     zoomlevel):
    return execute(function=find_flights,
                   args=(user, lat, lon, radius, altitude, begin, end, plot, zoomlevel))
