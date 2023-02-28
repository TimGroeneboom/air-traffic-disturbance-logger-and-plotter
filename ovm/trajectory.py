from dataclasses import dataclass, field


@dataclass
class Trajectory:
    """
    Trajectory holds a list of lat lon coordinates for a specific callsign together with the average altitude of the trajectory
    """
    callsign: str = field(default_factory=str)

    coords: list = field(default_factory=list)

    average_altitude: float = field(default_factory=float)