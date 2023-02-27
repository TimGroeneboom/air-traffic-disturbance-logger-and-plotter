from attr import dataclass


@dataclass
class Complainant:
    """
    Complainant data structure. Contains information about a user and the parameters which are set for this user that
    describe a disturbance period
    """
    user: str
    origin: tuple
    radius: int
    altitude: int
    occurrences: int
    timeframe: int

