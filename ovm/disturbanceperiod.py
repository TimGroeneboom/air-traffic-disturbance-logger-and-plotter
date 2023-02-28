import datetime
from dataclasses import dataclass, field
from ovm.complainant import Complainant

@dataclass
class Disturbance:
    """
    This is a description of a disturbance
    Holds begin & end time of found disturbance, callsigns and a plotted jpg image encoded as string
    """

    callsigns: list = field(default_factory=list)

    begin: str = field(default_factory=str)

    end: str = field(default_factory=str)

    img: str = field(default_factory=str)


@dataclass
class Disturbances:
    """
    Holds all found Disturbances in a dictionary
    """
    disturbances: list = field(default_factory=list)


class DisturbancePeriod:
    """
    DisturbancePeriod holds information about a period of disturbance
    Meaning amount of flights, complainant interested in the disturbance and trajectories of callsigns
    Trajectories dictionary and plot are optional and can be added later outside the contructor
    """
    def __init__(self,
                 complainant: Complainant,
                 disturbances: dict,
                 begin: datetime,
                 end: datetime,
                 flights: int,
                 average_altitude: float):
        """
        Contructor
        @param complainant: Complainant interested in the disturbance period
        @param disturbances: dictionary holding all disturbances
        @param begin: begin datetime of disturbance period
        @param end: end datetime of disturbance period
        @param flights: amount of flights
        @param average_altitude: average altitude in meters
        """
        self.complainant = complainant
        self.disturbances = disturbances
        self.begin = begin
        self.end = end
        self.flights = flights
        self.average_altitude = average_altitude
        self.trajectories = {}
        self.plot = None

