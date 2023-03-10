import logging
from datetime import datetime

import pymongo
from pymongo import MongoClient
from ovm.environment import Environment, load_environment
from ovm.utils import convert_datetime_to_int, convert_int_to_datetime


class DatabaseCollectionHandler:
    def __init__(self, environment: Environment):
        # Set environment
        self.environment = environment

        # Create MongoDB client
        self.mongo_client = MongoClient(environment.mongodb_config.host,
                                        environment.mongodb_config.port)

        # Acquire the collection
        self.collection = self.mongo_client[self.environment.mongodb_config.database][environment.mongodb_config.collection]

    def remove_entries_older_than(self, timestamp: datetime):
        logging.info('Deleting states from collection before %s' % timestamp.__str__())
        timestamp_int = convert_datetime_to_int(timestamp)
        self.collection.delete_many(***REMOVED***'Time': ***REMOVED***'$lte': timestamp_int***REMOVED******REMOVED***)

    def remove_entries_newer_than(self, timestamp: datetime):
        logging.info('Deleting states from collection after %s' % timestamp.__str__())
        timestamp_int = convert_datetime_to_int(timestamp)
        self.collection.delete_many(***REMOVED***'Time': ***REMOVED***'$gte': timestamp_int***REMOVED******REMOVED***)

    def add_property_to_all_states(self, property_name: str, default_value):
        cursor = self.collection.find(***REMOVED******REMOVED***).allow_disk_use(True)
        for doc in cursor:
            # Get all states
            states = doc['States']
            timestamp = doc['Time']
            update = False
            for state in states:
                if property_name not in state:
                    state[property_name] = default_value
                    update = True
            if update:
                self.collection.update_one(***REMOVED***'Time': timestamp***REMOVED***, ***REMOVED***"$set": ***REMOVED***'States': states***REMOVED******REMOVED***)



