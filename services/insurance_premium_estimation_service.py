from math import isnan

from repository import ParkingLocation
from repository.insurance_premium_estimation_repository import UserRiskTendency
from services.parking_locations_service import TheftProbabilityPrediction


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
