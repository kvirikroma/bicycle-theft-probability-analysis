import csv
from typing import Generator
from random import uniform, choice, randint

from geopy import distance

from . import ParkingLocation, Location, EPSILON


DATA_SOURCE_FILE = "./data_with_8users.csv"


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

    def from_csv(
            self, path_to_file: str, user_id: int | None = None,
            add_user_id: bool = False, count_limit: int | None = None
    ) -> Generator[ParkingLocation, None, None]:
        """
        "count_limit" parameter is used only for testing purposes and should be removed or replaced in the production
        """
        count = 0
        with open(path_to_file, 'r') as file:
            reader = csv.reader(file)
            for _ in reader:
                break
            for line in reader:
                if count_limit is not None and count >= count_limit:
                    break
                count += 1
                if (user_id is not None) and (len(line) > 5) and (int(line[5]) != user_id):
                    continue
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
                item = ParkingLocation(
                    latitude=latitude, longitude=longitude, parking_time=int(line[2]),
                    stolen=(line[3].lower() == "true"), recovered=(None if not line[4] else (line[4].lower() == "true"))
                )
                yield (item, int(line[5])) if add_user_id and len(line) > 5 else item


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
        center: Location, radius: int, exclude_center: bool = False,
        user_id: int | None = None, count_limit: int | None = None
) -> Generator[ParkingLocation, None, None]:
    """
    Radius is in meters.
    "count_limit" parameter is used only for testing purposes and should be removed or replaced in the production
    """
    source = ParkingLocationsSource(*get_map_corners(center, radius))
    for location in source.from_csv(DATA_SOURCE_FILE, user_id, count_limit=count_limit):
        if (center - location) <= radius:
            if not exclude_center or (center - location) > EPSILON:
                yield location
