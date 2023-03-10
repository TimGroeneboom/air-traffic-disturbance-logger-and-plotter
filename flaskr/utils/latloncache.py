import datetime
from pymongo import MongoClient
from ovm.environment import Environment
from ovm.utils import convert_datetime_to_int, convert_int_to_datetime


class LatLonCache:
    """
    The LatLonCache stores and gets lat, lon coordinates stored to addresses
    This is to reduce API calls to pro6pp or another service
    Addresses will get invalidated after expire days in which case they can be updated
    """
    def __init__(self, environment: Environment, expire_days: int):
        """
        Constructor, sets up the mongo client
        :param environment: the environment containing mongodb config
        :param expire_days: the amount of days after which addresses will be invalidated
        """
        # Set environment
        self.environment = environment

        # Create MongoDB client
        self.mongo_client = MongoClient(environment.mongodb_config.host,
                                        environment.mongodb_config.port)

        # Address entries will be considered invalid after this many days
        self.expire_days = expire_days

        # Acquire the collection
        self.collection = self.mongo_client[self.environment.mongodb_config.database]['latloncache']

    def address_valid(self, address: str):
        """
        Checks if address exists and is not expired, return True if valid
        :param address: the address key
        :return: True if address exists and is not expired
        """
        if self.collection.count_documents({'address': {"$in": [address]}}) > 0:
            entry = self.collection.find_one({'address': address})
            if 'lat' in entry and 'lon' in entry and 'timestamp' in entry:
                timestamp: datetime = convert_int_to_datetime(entry['timestamp'])
                if datetime.datetime.now() - timestamp > datetime.timedelta(days=self.expire_days):
                    return False
                return True
        return False

    def add_or_update_address(self, address: str, latlon: tuple):
        """
        Adds or updates an address, and it's corresponding latitude, longitude values
        :param address: the address to update
        :param latlon: the lat, lon value
        """
        self.collection.update_one({'address': address},
                                   {"$set": {
                                       'address': address,
                                       'lat': latlon[0],
                                       'lon': latlon[1],
                                       'timestamp': convert_datetime_to_int(datetime.datetime.now())
                                   }
                                   }, upsert=True)

    def get_latlon_from_address(self, address: str):
        """
        Gets latlon from address, can raise an exception, use after address_valid
        :param address: the address
        :return: lat, lon tuple
        """
        entry = self.collection.find_one({'address': address})
        return entry['lat'], entry['lon']

