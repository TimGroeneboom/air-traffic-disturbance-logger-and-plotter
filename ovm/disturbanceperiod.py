import datetime
from ovm.complainant import Complainant


class DisturbancePeriod:
    def __init__(self,
                 complainant: Complainant,
                 disturbances: dict,
                 begin: datetime,
                 end: datetime,
                 hits: int,
                 average_altitude: float):
        self.complainant = complainant
        self.disturbances = disturbances
        self.begin = begin
        self.end = end
        self.hits = hits
        self.average_altitude = average_altitude
        self.trajectories = ***REMOVED******REMOVED***
        self.image = None

