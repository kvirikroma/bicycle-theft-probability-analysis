from typing import Final, Callable

from repository import parking_locations_repository, Location


MAX_LOCATIONS_DISTANCE: Final = 4096  # meters


def estimate_theft_probability(
        location: Location, k_locations_to_test: int = 4, desired_close_samples: int = 4
) -> (float, float, float, Callable[[int], float]):
    """
    Parameter desired_close_samples is compared to 1/(distance^N) for all used dots
    and the result is used as a coefficient for the prediction accuracy.
    Returned value consists of 2 values:
        1st value: the probability of bike theft in the given location
        2nd value: the probability of bike recovery in case of theft
        3rd value: theoretical accuracy of the prediction, based on the independent test of K nearest locations
        4th value: a linear function that generates a theft probability  in the given location,
        depending on the parking time
    """
    sum_of_total = 0.0
    sum_of_stolen_forever = 0.0
    sum_of_stolen_and_recovered = 0.0
    for dot in parking_locations_repository.stream_parking_locations_nearby(
            location, MAX_LOCATIONS_DISTANCE, exclude_center=False
    ):
        pass
