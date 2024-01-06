from typing import Final
from enum import Enum
from random import uniform, choice
from math import log10, fabs, inf

from numpy.random import normal

from utils import ReprMixin, EPSILON

MIN_PRICE: Final = 100.0
STD_PRICE: Final = 2000.0
MAX_PRICE: Final = 10000.0
AVG_PARKING_TIME: Final = 30000
WK_DEVICE_VERSIONS: Final = (2, 3)
MAX_SECONDS_IN_MONTH: Final = 31 * 24 * 3600


class LockType(Enum):  # values are important
    none = 0
    cable = 1
    chain = 2
    u_lock = 3  # U-lock/D-lock
    folding = 4


class BikeType(Enum):
    mtb = 1
    fat = 2
    road = 3
    city = 4
    tt = 5  # time trial or triathlon
    touring = 6
    bmx = 7
    cargo = 8
    tandem = 9
    gravel = 10
    other = 0


class FrameMaterial(Enum):
    aluminum = 1
    carbon = 2
    steel = 3
    titanium = 4
    other = 0


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


class InsuranceInputData(ReprMixin):
    def __init__(
            self, bike_price: float, lock_type: LockType, bike_type: BikeType, frame_material: FrameMaterial,
            parking_time_during_last_month: int, user_risk_tendency: UserRiskTendency, lock_price: float = 0.0,
            wk_device_revision_number: int = 3, bike_is_electric: bool = False, damage_insurance_included: bool = False
    ):
        if bike_price <= 0.0:
            raise ValueError("Bike price must be higher than zero")
        if lock_price < 0.0:
            raise ValueError("Lock price cannot be lower than zero")
        if parking_time_during_last_month < 0:
            raise ValueError("Parking time cannot be lower than zero")
        if wk_device_revision_number not in WK_DEVICE_VERSIONS:
            raise ValueError(f"Invalid WK device version. Correct ones are: {WK_DEVICE_VERSIONS}")
        self.bike_price, self.lock_type, self.bike_type = bike_price, lock_type, bike_type
        self.frame_material, self.parking_time_during_last_month = frame_material, parking_time_during_last_month
        self.user_risk_tendency, self.wk_device_revision_number = user_risk_tendency, wk_device_revision_number
        self.bike_is_electric, self.damage_insurance_included = bike_is_electric, damage_insurance_included
        self.lock_price = 0.0 if lock_type == LockType.none else lock_price


def _bounds(value, minimum=0.0, maximum=1.0):
    return max(minimum, min(value, maximum))


def generate_random_insurance_data() -> InsuranceInputData:
    price = round(choice((
        min(STD_PRICE + fabs(normal(scale=(MAX_PRICE - STD_PRICE) / 2)), MAX_PRICE),
        max(STD_PRICE - fabs(normal(scale=(STD_PRICE - MIN_PRICE) / 2)), MIN_PRICE)
    )), 2)
    if price > 1000:
        bike_type = choice(list(BikeType))
    elif price > 500:
        bike_type = choice([BikeType(i) for i in (0, 1, 2, 3, 4, 7, 8, 9, 10)])
    else:
        bike_type = choice([BikeType(i) for i in (0, 1, 2, 4, 7, 9)])
    lock_type = choice(list(LockType))
    lock_price = round(max(
        3.0 + fabs(normal()), fabs(normal(loc=lock_type.value * 10, scale=10))
    ), 2) if lock_type != LockType.none else 0
    if bike_type == BikeType.tt:
        frame = FrameMaterial.carbon
    else:
        frame = choice(list(FrameMaterial)) if price < 500 else choice([FrameMaterial(i) for i in (0, 1, 2, 4)])
    is_electric = choice((False,) + (True,) * (round(log10(price)) - 2)) if bike_type != BikeType.bmx else False
    parking_time = _bounds(round(normal(loc=AVG_PARKING_TIME, scale=AVG_PARKING_TIME / 3)), minimum=60, maximum=inf)
    usual_prediction = _bounds(normal(loc=0.1 - (lock_type.value / 20), scale=0.06))
    wk_version = choice(WK_DEVICE_VERSIONS)
    recovery_probability = _bounds(normal(loc=0.25 if wk_version == 2 else 0.4, scale=0.2))
    risk_tendency = UserRiskTendency(
        avg_theft_probability_prediction=usual_prediction,
        avg_theft_probability=_bounds(normal(loc=usual_prediction, scale=0.06)),
        avg_recovery_probability_prediction=_bounds(normal(loc=recovery_probability, scale=0.1)),
        avg_recovery_probability=recovery_probability,
        avg_parking_time_theft_probability_prediction=_bounds(normal(loc=usual_prediction, scale=0.02)),
        avg_parking_time=parking_time
    )
    return InsuranceInputData(
        bike_price=price,
        lock_type=lock_type,
        bike_type=bike_type,
        frame_material=frame,
        parking_time_during_last_month=round(risk_tendency.avg_parking_time * uniform(28, 31)),
        user_risk_tendency=risk_tendency,
        lock_price=lock_price,
        wk_device_revision_number=wk_version,
        bike_is_electric=is_electric,
        damage_insurance_included=choice((True, False))
    )


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
    insurance_cost /= 1 + (data.lock_type.value / 8 + data.lock_price / 100)  # todo sanity-check
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
