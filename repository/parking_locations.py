from typing import Generator
from random import uniform

from geopy import distance

from . import ParkingLocation


def parking_locations_source(
        lat_min: float = -90.0, lat_max: float = 90.0,
        lon_min: float = -180.0, lon_max: float = 180.0
) -> Generator[ParkingLocation, None, None]:
    def get_random_locations(number: int) -> Generator[ParkingLocation, None, None]:
        for _ in range(number):
            yield ParkingLocation(
                latitude=round(uniform(lat_min, lat_max), 7),
                longitude=round(uniform(lon_min, lon_max), 7)
            )

    return get_random_locations(20)


def stream_parking_locations_nearby(center: ParkingLocation, radius: int) -> Generator[ParkingLocation, None, None]:
    """Radius is in meters"""
    lat_top = distance.distance(meters=radius).destination(center.coordinates, bearing=0).latitude
    lat_bottom = distance.distance(meters=radius).destination(center.coordinates, bearing=180).latitude
    lon_left = distance.distance(meters=radius).destination(center.coordinates, bearing=270).longitude
    lon_right = distance.distance(meters=radius).destination(center.coordinates, bearing=90).longitude
    for location in parking_locations_source(
            lat_min=min(lat_bottom, lat_top),
            lat_max=max(lat_bottom, lat_top),
            lon_min=min(lon_right, lon_left),
            lon_max=max(lon_right, lon_left)
    ):
        if (center - location) <= radius:
            yield location
