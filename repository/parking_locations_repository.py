import csv
from typing import Generator
from random import uniform, choice, randint

from geopy import distance

from . import ParkingLocation, Location, EPSILON


class ParkingLocationsSource:
    def __init__(
            self,
            lat_min: float = -90.0, lat_max: float = 90.0,
            lon_min: float = -180.0, lon_max: float = 180.0,
    ):
        self.lat_min = lat_min
        self.lat_max = lat_max
        self.lon_min = lon_min
        self.lon_max = lon_max

    def random(self, number: int) -> Generator[ParkingLocation, None, None]:
        for _ in range(number):
            theft_and_recovery = choice(((True, False), (True, True)) + ((False, None), ) * 5)
            yield ParkingLocation(
                round(uniform(self.lat_min, self.lat_max), 7),
                round(uniform(self.lon_min, self.lon_max), 7),
                round(randint(2, 86400) * (theft_and_recovery[0] + uniform(0.5, 1.5))),
                *theft_and_recovery
            )

    def from_csv(self, path_to_file: str) -> Generator[ParkingLocation, None, None]:
        with open(path_to_file, 'r') as file:
            reader = csv.reader(file)
            for _ in reader:
                break
            for line in reader:
                latitude, longitude = float(line[0]), float(line[1])
                skip = False
                for coord, coord_min, coord_max in (
                        (latitude, self.lat_min, self.lat_max), (longitude, self.lon_min, self.lon_max)
                ):
                    if coord_min > coord_max and not (coord <= coord_min or coord >= coord_max):
                        skip = True
                    elif coord_max > coord_min and (coord < coord_min or coord > coord_max):
                        skip = True
                if skip:
                    continue
                yield ParkingLocation(
                    latitude=latitude, longitude=longitude, parking_time=int(line[2]),
                    stolen=(line[3].lower() == "true"), recovered=(None if not line[4] else (line[4].lower() == "true"))
                )


def get_map_corners(center: Location, radius: int) -> tuple[float, float, float, float]:
    """
    :param center: center of the map
    :param radius: this radius has to be displayed on the map
    :return: the borders of the map displaying the given radius: lat_min, lat_max, lon_min, lon_max
    """
    return (
        distance.distance(meters=radius).destination(center.coordinates, bearing=180).latitude,
        distance.distance(meters=radius).destination(center.coordinates, bearing=0).latitude,
        distance.distance(meters=radius).destination(center.coordinates, bearing=270).longitude,
        distance.distance(meters=radius).destination(center.coordinates, bearing=90).longitude
    )


def stream_parking_locations_nearby(
        center: Location, radius: int, exclude_center: bool = False
) -> Generator[ParkingLocation, None, None]:
    """Radius is in meters"""
    source = ParkingLocationsSource(*get_map_corners(center, radius))
    for location in source.from_csv("./data.csv"):
        if (center - location) <= radius:
            if not exclude_center or (center - location) > EPSILON:
                yield location
