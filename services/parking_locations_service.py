from math import nan, isnan

from statsmodels.regression.linear_model import WLS
from statsmodels.api import add_constant

from repository import parking_locations_repository, Location, ParkingLocation, EPSILON
from utils import ReprMixin


class DotAndItsImportance(ReprMixin):
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

    def __str__(self):
        return f"{type(self).__name__}(dot={self.dot}, importance={self.importance})"


class LinearRegressionParams:
    """The function is meant to me a*x + b"""
    def __init__(self, a: int | float, b: int | float):
        self.a = a
        self.b = b

    def function(self, x):
        return self.a * x + self.b

    def __str__(self):
        return f"{type(self).__name__}(a={self.a}, b={self.b})"

    def __repr__(self):
        return str(self)


class TheftProbabilityPrediction(ReprMixin):
    def __init__(
            self, location: Location, theft_probability: float, recovery_probability: float,
            used_dots: int, regression_params: LinearRegressionParams | None
    ):
        """
        :param theft_probability: the probability of bike theft in the given location
        :param recovery_probability: the probability of bike recovery in case of theft
        :param used_dots: the number of dots used for this prediction
        :param regression_params: a linear function that generates a theft probability  in the given location,
            depending on the parking time. None if the get_probability_function is False
        """
        self.location = Location(*location.coordinates)
        self.theft_probability = theft_probability
        self.recovery_probability = recovery_probability
        self.used_dots = used_dots
        self.regression_params = regression_params

    def probability_function(self, time: int) -> float | None:
        if not self.regression_params or self.regression_params.a < 0:
            return None
        raw_prediction = self.regression_params.function(time)
        if raw_prediction < 0.0 or time <= 0:
            return 0.0
        if raw_prediction > 1.0:
            return 1.0
        return raw_prediction

    def __str__(self):
        return (f"{type(self).__name__}(location={self.location}, theft_probability={self.theft_probability}"
                f", used_dots={self.used_dots}, regression_params={self.regression_params})")


class UserRiskTendency(ReprMixin):
    def __init__(
            self, avg_theft_probability_prediction: float | None, avg_theft_probability: float | None,
            avg_recovery_probability_prediction: float | None, avg_recovery_probability: float | None,
            avg_parking_time_theft_probability_prediction: float | None, avg_parking_time: float | None
    ):
        self.avg_theft_probability_prediction = avg_theft_probability_prediction
        self.avg_theft_probability = avg_theft_probability
        self.avg_recovery_probability_prediction = avg_recovery_probability_prediction
        self.avg_recovery_probability = avg_recovery_probability
        self.avg_parking_time_theft_probability_prediction = avg_parking_time_theft_probability_prediction
        self.avg_parking_time = avg_parking_time

    def __str__(self):
        return (f"{type(self).__name__}(avg_theft_probability_prediction={self.avg_theft_probability_prediction}, "
                f"avg_theft_probability={self.avg_theft_probability}, "
                f"avg_recovery_probability_prediction={self.avg_recovery_probability_prediction}, "
                f"avg_recovery_probability={self.avg_recovery_probability}, "
                f"avg_parking_time_theft_probability_prediction={self.avg_parking_time_theft_probability_prediction}, "
                f"avg_parking_time={self.avg_parking_time})")


class PredictionAccuracy(ReprMixin):
    def __init__(
            self, theft_probability_prediction_accuracy: float | None,
            recovery_probability_prediction_accuracy: float | None,
            parking_time_theft_probability_prediction_accuracy: float | None
    ):
        self.theft_probability_prediction_accuracy = theft_probability_prediction_accuracy
        self.recovery_probability_prediction_accuracy = recovery_probability_prediction_accuracy
        self.parking_time_theft_probability_prediction_accuracy = parking_time_theft_probability_prediction_accuracy

    def __str__(self):
        return (f"{type(self).__name__}"
                f"(theft_probability_prediction_accuracy={self.theft_probability_prediction_accuracy}, "
                f"recovery_probability_prediction_accuracy={self.recovery_probability_prediction_accuracy}, "
                f"parking_time_theft_probability_prediction_accuracy="
                f"{self.parking_time_theft_probability_prediction_accuracy})")


def _get_max_distance(power_of_distance):
    """Calculate the distance at which the importance of the data is less than Epsilon"""
    return EPSILON ** (-1 / power_of_distance)


def _get_error(value: float, biased_value: float):
    return min(1.0, abs(biased_value - value) / value)


def estimate_theft_probability(
        location: Location, power_of_distance: float = 1.4,
        get_probability_function: bool = False, get_all_dots: bool = False, count_limit: int | None = None
) -> tuple[TheftProbabilityPrediction, list[DotAndItsImportance] | None]:
    """
    Calculate the approximate probability of the bicycle theft at the given location,
        basing on the data about bicycle thefts in this area.
    :param location: the location to perform the test on
    :param power_of_distance: The higher this value, the more significant becomes the distance to the compared dot.
        The allowed values for this parameter are between 1.0 and 32.0. Recommended values are between 1.0 and 2.0.
    :param get_probability_function: if set to True, the probability function parameters will be calculated.
    :param get_all_dots: Return list of all locations along with the TheftProbabilityPrediction() object.
    :param count_limit: if passed, the function will read not more than count_limit values from the database
    :return: a TheftProbabilityPrediction() object and, optionally, all the dots, used for the prediction,
        along with their weights. If there are no dots around the location,
        (TheftProbabilityPrediction(location, nan, nan, 0, None), None) will be returned.
    If the get_probability_function and the get_all_dots parameters are both False, the function will use O(1) memory.
    """
    if power_of_distance < 1.0 or power_of_distance > 32.0:
        raise ValueError("The allowed values for power_of_distance are between 1.0 and 32.0")
    if count_limit is not None and (count_limit < 0):
        raise ValueError("The count_limit parameter has to be greater or equal to zero")
    sum_of_importance = 0.0
    sum_of_stolen_forever = 0.0  # also about importance
    sum_of_stolen_and_recovered = 0.0  # also about importance
    dots_count = 0  # just a counter
    all_dots_with_importance = []
    max_locations_distance = _get_max_distance(power_of_distance)
    for dot in parking_locations_repository.stream_parking_locations_nearby(
            location, max_locations_distance, exclude_center=False, count_limit=count_limit
    ):
        dots_count += 1
        dot_importance = 1 / (max(dot - location, 3) ** power_of_distance)  # everything closer than 3m is the same
        sum_of_importance += dot_importance
        if dot.stolen and dot.recovered:
            sum_of_stolen_and_recovered += dot_importance
        elif dot.stolen:
            sum_of_stolen_forever += dot_importance
        dot_and_importance = DotAndItsImportance(dot, dot_importance)
        if get_probability_function or get_all_dots:
            all_dots_with_importance.append(dot_and_importance)
    if dots_count == 0:
        return TheftProbabilityPrediction(location, nan, nan, 0, None), None
    probability_of_theft = (sum_of_stolen_forever + sum_of_stolen_and_recovered) / sum_of_importance
    probability_of_recovery = sum_of_stolen_and_recovered / (sum_of_stolen_forever + sum_of_stolen_and_recovered) \
        if (sum_of_stolen_forever + sum_of_stolen_and_recovered) > 0.0 else nan
    regression_params = None
    if get_probability_function:
        weights = [i.importance for i in all_dots_with_importance]
        y_values = [int(i.dot.stolen) for i in all_dots_with_importance]
        x_values = [int(i.dot.parking_time) for i in all_dots_with_importance]
        probability_func_parameters = WLS(y_values, add_constant(x_values), weights=weights).fit().params
        if len(probability_func_parameters) > 1 and probability_func_parameters[1] >= 0.0:
            regression_params = LinearRegressionParams(probability_func_parameters[1], probability_func_parameters[0])
    return TheftProbabilityPrediction(
        location, probability_of_theft, probability_of_recovery, dots_count, regression_params
    ), (all_dots_with_importance if get_all_dots else None)


def get_user_risk_tendency(
        locations_with_predictions: list[tuple[ParkingLocation, TheftProbabilityPrediction]]
) -> UserRiskTendency:
    theft_probability_data = [
        prediction.theft_probability for location, prediction in locations_with_predictions
        if not isnan(prediction.theft_probability)
    ]
    recovery_probability_data = [
        prediction.recovery_probability for location, prediction in locations_with_predictions
        if not isnan(prediction.recovery_probability)
    ]
    recovery_data = [
        location.recovered for location, prediction in locations_with_predictions if location.recovered is not None
    ]
    parking_time_theft_data = [
        prediction.probability_function(location.parking_time)
        for location, prediction in locations_with_predictions
        if prediction.regression_params is not None
    ]
    return UserRiskTendency(
        avg_theft_probability_prediction=(
                sum(theft_probability_data) / len(theft_probability_data)
        ) if theft_probability_data else None,
        avg_theft_probability=(
                sum(i[0].stolen for i in locations_with_predictions) / len(locations_with_predictions)
        ) if locations_with_predictions else None,
        avg_recovery_probability_prediction=(
                sum(recovery_probability_data) / len(recovery_probability_data)
        ) if recovery_probability_data else None,
        avg_recovery_probability=(
                sum(recovery_data) / len(recovery_data)
        ) if recovery_data else None,
        avg_parking_time_theft_probability_prediction=(
                sum(parking_time_theft_data) / len(parking_time_theft_data)
        ) if parking_time_theft_data else None,
        avg_parking_time=(
                sum(i[0].parking_time for i in locations_with_predictions) / len(locations_with_predictions)
        ) if locations_with_predictions else None
    )


def get_prediction_accuracy(
        locations_with_predictions: list[tuple[ParkingLocation, TheftProbabilityPrediction]]
) -> PredictionAccuracy:
    theft_data = [
        (location.stolen, prediction.theft_probability)
        for location, prediction in locations_with_predictions
        if not isnan(prediction.theft_probability)
    ]
    recovery_data = [
        (location.recovered, prediction.recovery_probability)
        for location, prediction in locations_with_predictions
        if not isnan(prediction.recovery_probability) and location.recovered is not None
    ]
    parking_time_theft_data = [
        (location.stolen, prediction.probability_function(location.parking_time))
        for location, prediction in locations_with_predictions
        if prediction.regression_params is not None
    ]
    avg_theft_accuracy = None
    avg_recovery_accuracy = None
    avg_parking_time_theft_accuracy = None
    if theft_data:
        avg_theft_accuracy = 1.0 - sum(
            abs(stolen - probability) for stolen, probability in theft_data
        ) / len(theft_data)
    if recovery_data:
        avg_recovery_accuracy = 1.0 - sum(
            abs(recovered - probability) for recovered, probability in recovery_data
        ) / len(recovery_data)
    if parking_time_theft_data:
        avg_parking_time_theft_accuracy = 1.0 - sum(
            abs(stolen - probability) for stolen, probability in parking_time_theft_data
        ) / len(parking_time_theft_data)
    return PredictionAccuracy(
        theft_probability_prediction_accuracy=avg_theft_accuracy,
        recovery_probability_prediction_accuracy=avg_recovery_accuracy,
        parking_time_theft_probability_prediction_accuracy=avg_parking_time_theft_accuracy
    )
