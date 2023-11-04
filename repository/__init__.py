from geopy.distance import distance


class ParkingLocation:
    def __init__(self, latitude: float, longitude: float):
        self.latitude = latitude
        self.longitude = longitude

    @property
    def coordinates(self):
        return self.latitude, self.longitude

    def __sub__(self, other: 'ParkingLocation'):
        """Distance in meters"""
        return distance(self.coordinates, other.coordinates).m

    def __str__(self):
        return f"{type(self).__name__}({','.join(str(i) for i in self.coordinates)})"

    def __repr__(self):
        return str(self)
