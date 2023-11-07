from typing import Generator
from random import uniform, choice, randint

from geopy import distance

from . import ParkingLocation, Location, EPSILON


def parking_locations_source(
        lat_min: float = -90.0, lat_max: float = 90.0,
        lon_min: float = -180.0, lon_max: float = 180.0
) -> Generator[ParkingLocation, None, None]:
    def get_random_locations(number: int) -> Generator[ParkingLocation, None, None]:
        for _ in range(number):
            theft_and_recovery = choice(((True, False), (True, True)) + ((False, None), ) * 5)
            yield ParkingLocation(
                round(uniform(lat_min, lat_max), 7),
                round(uniform(lon_min, lon_max), 7),
                round(randint(2, 86400) * (theft_and_recovery[0] + uniform(0.5, 1.5))),
                *theft_and_recovery
            )

    return get_random_locations(200)


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
    for location in parking_locations_source(*get_map_corners(center, radius)):
        if (center - location) <= radius:
            if not exclude_center or (center - location) > EPSILON:
                yield location
