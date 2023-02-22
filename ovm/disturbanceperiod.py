import datetime


class DisturbancePeriod:
    def __init__(self,
                 coord: tuple,
                 radius: int,
                 disturbance_callsigns: dict,
                 begin: datetime,
                 end: datetime,
                 hits: int):
        self.coord = coord
        self.radius = radius
        self.disturbance_callsigns = disturbance_callsigns
        self.begin = begin
        self.end = end
        self.hits = hits
        self.trajectories = {}

