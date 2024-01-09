from math import isnan, log10
from typing import Iterable, Final

import numpy as np

from utils import tf, err, EPSILON
from repository import ParkingLocation
from repository.insurance_premium_estimation_repository import (UserRiskTendency, MIN_PRICE, MAX_PRICE, LockType,
                                                                BikeType, FrameMaterial, MAX_SECONDS_IN_MONTH,
                                                                MIN_LOCK_PRICE, MAX_LOCK_PRICE, WK_DEVICE_VERSIONS,
                                                                InsuranceInputData)
from services.parking_locations_service import TheftProbabilityPrediction


MODEL: Final = tf.keras.models.load_model('result-0.4537.keras', custom_objects={'err': err})


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


def prepare_insurance_data(x, y=None):
    x_prepared = []

    def normalize(val, minimum, maximum):
        return (val - minimum) / (maximum - minimum)

    for item in x:
        x_prepared.append([
            normalize(item[0], MIN_PRICE, MAX_PRICE),
            *[i.value == item[1] for i in LockType],
            *[i.value == item[2] for i in BikeType],
            *[i.value == item[3] for i in FrameMaterial],
            normalize(item[4], 0.0, MAX_SECONDS_IN_MONTH),
            *item[5:10],
            normalize(item[10], 0, MAX_SECONDS_IN_MONTH) if item[10] < MAX_SECONDS_IN_MONTH else 1.0,
            normalize(item[11], MIN_LOCK_PRICE, MAX_LOCK_PRICE),
            *[i == item[12] for i in WK_DEVICE_VERSIONS],
            *item[13:]
        ])

    x_prepared = np.array(x_prepared)
    y_prepared = None
    if y:
        y_prepared = np.array([0.0 if i is None else i for i in y])
    return (x_prepared, y_prepared) if y else x_prepared


def _simple_insurance_premium_prediction(data: InsuranceInputData) -> float | None:
    """The result is None if the insurance can't be provided for the given case"""
    if data.bike_price < 150 or data.lock_price < EPSILON or data.lock_type == LockType.none:
        return None
    init_insurance_cost = 30 + data.bike_price / 100 + 5 * log10(data.bike_price)
    insurance_cost = init_insurance_cost
    if data.damage_insurance_included:
        insurance_cost *= 1.18 if data.bike_price > 3000 else 1.15
    if data.bike_is_electric:
        coefficient = 1
        if data.bike_type in (BikeType.fat, BikeType.other):
            coefficient = 2
    else:
        coefficients = {
            BikeType.cargo: 1.35, BikeType.tandem: 1.35, BikeType.city: 1.35, BikeType.bmx: 1.35,
            BikeType.road: 1.85, BikeType.gravel: 1.85, BikeType.touring: 1.85, BikeType.tt: 1.85,
            BikeType.mtb: 2.3, BikeType.fat: 2.5, BikeType.other: 2.5
        }
        coefficient = coefficients[data.bike_type]
        if data.bike_price < 2500:
            coefficient *= 0.95
        elif data.bike_price < 2000:
            coefficient *= 0.9
    insurance_cost *= coefficient
    if data.frame_material == FrameMaterial.carbon or data.frame_material == FrameMaterial.titanium:
        insurance_cost **= 1.02
    insurance_cost /= 1 + (data.lock_type.value / 8 + data.lock_price / 100)
    theft_prediction_coefficient = (
        (data.user_risk_tendency.avg_theft_probability_prediction * 0.02) +
        (data.user_risk_tendency.avg_parking_time_theft_probability_prediction * 0.15) +
        ((1 - data.user_risk_tendency.avg_recovery_probability_prediction) * 0.03) +
        ((1 - data.user_risk_tendency.avg_recovery_probability) * 0.2) +
        (data.user_risk_tendency.avg_theft_probability * 0.6)
    ) * 2 + 1
    insurance_cost *= theft_prediction_coefficient ** 4
    insurance_cost *= 1 + ((data.parking_time_during_last_month / MAX_SECONDS_IN_MONTH) / 2)
    if data.wk_device_revision_number != max(WK_DEVICE_VERSIONS):
        insurance_cost *= 1.2
    insurance_cost = (init_insurance_cost * 0.5 + insurance_cost * 1.5) / 2
    insurance_cost /= 12  # per month
    return max(round(insurance_cost, 2), 5.0)


def insurance_premium_prediction(data: Iterable[InsuranceInputData]) -> list[float | None]:
    insurance_data = prepare_insurance_data(i.as_list_of_values() for i in data)
    return [max(0.0, round(float(i[0]), 2)) for i in MODEL.predict(insurance_data)]
