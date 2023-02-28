from dataclasses import dataclass, field


@dataclass
class Trajectory:
    callsign: str = field(default_factory=str)

    coords: list = field(default_factory=list)

    average_altitude: float = field(default_factory=float)