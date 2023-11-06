from typing import Callable
from math import nan, isnan
from heapq import heappush, heapreplace

from statsmodels.regression.linear_model import WLS
from statsmodels.api import add_constant

from repository import parking_locations_repository, Location, ParkingLocation, EPSILON


class DotAndItsImportance:
    def __init__(self, dot: ParkingLocation, importance: float):
        self.dot = dot
        self.importance = importance

    def __eq__(self, other: 'DotAndItsImportance'):
        return (self.importance / EPSILON - other.importance / EPSILON) < EPSILON

    def __gt__(self, other: 'DotAndItsImportance'):
        return self.importance > other.importance

    def __lt__(self, other: 'DotAndItsImportance'):
        return self.importance < other.importance

    def __ge__(self, other: 'DotAndItsImportance'):
        return self.importance >= other.importance

    def __le__(self, other: 'DotAndItsImportance'):
        return self.importance <= other.importance


def _get_max_distance(power_of_distance):
    """Calculate the distance at which the importance of the data is less than Epsilon"""
    return EPSILON ** (-1 / power_of_distance)


def _get_error(value: float, biased_value: float):
    return min(1.0, abs(biased_value - value) / value)


def estimate_theft_probability(
        location: Location, k_locations_to_test: int = 5,
        power_of_distance: float = 1.432, get_probability_function: bool = False
) -> tuple[float, float, int, float | None, Callable[[int | None], float | tuple[float, float]] | None]:
    """
    The allowed values for power_of_distance are between 1.0 and 32.0. Recommended values are between 1.0 and 2.0.
    The higher this value, the more significant becomes the distance to the compared dot.
    Parameter trusted_distance represents the size of interval (in meters), at least 1 point should be in.
    Returned value consists of these values:
        1st value: the probability of bike theft in the given location
        2nd value: the probability of bike recovery in case of theft
        3rd value: the number of dots used for this prediction
        4th value: theoretical accuracy (between 0 and 1) of the prediction,
            based on the independent test of K nearest locations. None if k_locations_to_test is zero
        5th value: a linear function that generates a theft probability  in the given location,
        depending on the parking time. None if the get_probability_function is False
    The function returns (nan, nan, None, None, None), if there are no dots around the location.
    """
    if power_of_distance < 1.0 or power_of_distance > 32.0:
        raise ValueError("The allowed values for power_of_distance are between 1.0 and 32.0")
    if k_locations_to_test < 0:
        raise ValueError("The k_locations_to_test parameter can't be negative")
    sum_of_importance = 0.0
    sum_of_stolen_forever = 0.0  # also about importance
    sum_of_stolen_and_recovered = 0.0  # also about importance
    dots_count = 0  # just a counter
    k_nearest_locations: list[DotAndItsImportance] = []
    all_dots_with_importance = []
    max_locations_distance = _get_max_distance(power_of_distance)
    for dot in parking_locations_repository.stream_parking_locations_nearby(
            location, max_locations_distance, exclude_center=False
    ):
        dots_count += 1
        dot_importance = 1 / ((dot - location) ** power_of_distance)
        sum_of_importance += dot_importance
        if dot.stolen and dot.recovered:
            sum_of_stolen_and_recovered += dot_importance
        elif dot.stolen:
            sum_of_stolen_forever += dot_importance
        dot_and_importance = DotAndItsImportance(dot, dot_importance)
        if len(k_nearest_locations) < k_locations_to_test:
            heappush(k_nearest_locations, dot_and_importance)
        elif (k_locations_to_test > 0) and (k_nearest_locations[0].importance < dot_importance):
            heapreplace(k_nearest_locations, dot_and_importance)
        all_dots_with_importance.append(dot_and_importance)
    if dots_count == 0:
        return nan, nan, 0, None, None
    probability_of_theft = (sum_of_stolen_forever + sum_of_stolen_and_recovered) / sum_of_importance
    probability_of_recovery = sum_of_stolen_and_recovered / (sum_of_stolen_forever + sum_of_stolen_and_recovered)
    test_results = [estimate_theft_probability(
        loc.dot, k_locations_to_test=0, power_of_distance=power_of_distance, get_probability_function=False
    ) for loc in k_nearest_locations]
    test_results = [i[0] for i in test_results if not isnan(i[0])]
    if len(test_results) > 0:
        k_nearest_avg_theft_probability = sum(test_results) / len(test_results)
        k_avg_thefts = sum(i.dot.stolen for i in k_nearest_locations) / len(k_nearest_locations)
        k_nearest_test_result = _get_error(k_nearest_avg_theft_probability, k_avg_thefts)
    else:
        k_nearest_test_result = None
    probability_function = None
    if get_probability_function:
        weights = [i.importance for i in all_dots_with_importance]
        y_values = [int(i.dot.stolen) for i in all_dots_with_importance]
        x_values = [int(i.dot.parking_time) for i in all_dots_with_importance]
        probability_func_parameters = WLS(y_values, add_constant(x_values), weights=weights).fit().params
        if probability_func_parameters[1] >= 0.0:
            def probability_function(time: int | None = None):
                if time is None:
                    return probability_func_parameters[1], probability_func_parameters[0]
                raw_prediction = probability_func_parameters[1] * time + probability_func_parameters[0]
                if raw_prediction < 0.0 or time <= 0 or probability_func_parameters[1] < 0:
                    return 0.0
                if raw_prediction > 1.0:
                    return 1.0
                return raw_prediction
    return probability_of_theft, probability_of_recovery, dots_count, k_nearest_test_result, probability_function
