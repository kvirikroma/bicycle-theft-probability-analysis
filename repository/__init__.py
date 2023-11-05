from typing import Final

from geopy.distance import distance


EPSILON: Final = 0.000001


class Location:
    def __init__(self, latitude: float, longitude: float):
        self.latitude = latitude
        self.longitude = longitude

    @property
    def coordinates(self):
        return self.latitude, self.longitude

    def __sub__(self, other: 'Location'):
        """Distance in meters"""
        return distance(self.coordinates, other.coordinates).m

    def __str__(self):
        return f"{type(self).__name__}({','.join(str(i) for i in self.coordinates)})"

    def __repr__(self):
        return str(self)


class ParkingLocation(Location):
    def __init__(
            self, latitude: float, longitude: float, parking_time: int,
            stolen: bool = False, recovered: bool | None = None
    ):
        """parking_time is in seconds"""
        super().__init__(latitude, longitude)
        if not stolen and (recovered is not None):
            raise ValueError("The 'recovered' value must be None if the 'stolen' value is False")
        self.stolen = stolen
        self.recovered = recovered
        self.parking_time = parking_time

    def __str__(self):
        return (f"{type(self).__name__}({', '.join(str(i) for i in self.coordinates)}"
                f", parking_time={self.parking_time}, stolen={self.stolen}"
                f"{f', recovered={self.recovered}' if self.recovered is not None else ''})")
