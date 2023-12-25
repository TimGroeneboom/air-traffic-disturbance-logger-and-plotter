import json

class Timezone(object):
    """
    DataClass holding timezone
    """
    def __init__(self, timezone):
        self.timezone = timezone

        def __str__(self):
            return "{0}".format(self.timezone)

class FlightRadar24Credentials(object):
    """
    DataClass holding FlightRadar24 credentials
    """
    def __init__(self, username, password):
        self.username = username
        self.password = password

    def __str__(self):
        return "{0} {1}".format(self.username, self.password)


class MongoDBConfiguration(object):
    """
    DataClass holding mongodb configuration
    """
    def __init__(self, host, port, database, collection):
        self.host = host
        self.port = port
        self.database = database
        self.collection = collection

    def __str__(self):
        return "{0} {1} {2} {3}".format(self.host, self.port, self.database, self.collection)


class Environment(object):
    """
    DataClass containing MongoDBConfiguration and OpenSkyCredentials
    """
    def __init__(self, flightradar24_creds, mongodb_config, timezone):
        self.flightradar24_creds = FlightRadar24Credentials(**flightradar24_creds)
        self.mongodb_config = MongoDBConfiguration(**mongodb_config)
        self.timezone = Timezone(**timezone)

    def __str__(self):
        return "{0} ,{1} ,{2}".format(self.flightradar24_creds, self.mongodb_config, self.timezone)


def load_environment(filename: str):
    j = json.load(open(filename))
    return Environment(**j)
