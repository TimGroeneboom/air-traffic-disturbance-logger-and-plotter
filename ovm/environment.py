import json


class OpenSkyCredentials(object):
    """
    DataClass holding opensky credentials
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
    def __init__(self, opensky_credentials, mongodb_config):
        self.opensky_credentials = OpenSkyCredentials(**opensky_credentials)
        self.mongodb_config = MongoDBConfiguration(**mongodb_config)

    def __str__(self):
        return "{0} ,{1}".format(self.opensky_credentials, self.mongodb_config)


def load_environment(filename: str):
    j = json.load(open(filename))
    return Environment(**j)
