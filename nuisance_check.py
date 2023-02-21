# Import the python libraries
import datetime

from pymongo import MongoClient
from pprint import pprint
import geopy.distance
import json

# Choose the appropriate client
client = MongoClient()

origin = (52.396172234741506, 4.905621078252285)
radius = 1000
altitude = 1000
occurrences = 4
timeframe = 1

# Connect to the test db
db = client.planelogger
states = db.states
cursor = states.find(***REMOVED******REMOVED***)
for document in cursor:
    time = document['Time']
    time_string = str(time)
    timestamp = datetime.datetime.strptime(time_string, "%Y%m%d%H%M%S")
    states = document['States']
    for state in states:
        if state['baro_altitude'] is None:
            continue

        if state['baro_altitude'] < altitude:
            coord = (state['latitude'], state['longitude'])
            distance = geopy.distance.distance(origin, coord).meters
            if distance < radius:
                print(('%s : %im [%s]' % (timestamp, distance, state['callsign'])))

