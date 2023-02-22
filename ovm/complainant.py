from attr import dataclass


@dataclass
class Complainant:
    user: str
    origin: tuple
    radius: int
    altitude: int
    occurrences: int
    timeframe: int