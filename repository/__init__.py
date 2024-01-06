from geopy.distance import distance

from utils import ReprMixin, EPSILON


class Location(ReprMixin):
    def __init__(self, latitude: float, longitude: float):
        self.latitude = latitude
        self.longitude = longitude

    @property
    def coordinates(self):
        return self.latitude, self.longitude

    def __sub__(self, other: 'Location'):
        """Distance in meters"""
        return distance(self.coordinates, other.coordinates).m


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
