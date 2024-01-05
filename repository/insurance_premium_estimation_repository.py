from enum import Enum
from random import randint, uniform, choice
from math import log10, fabs, inf

from numpy.random import normal

from utils import ReprMixin


MIN_PRICE = 100.0
STD_PRICE = 2000.0
MAX_PRICE = 10000.0
AVG_PARKING_TIME = 30000


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
    is_electric = choice((False, ) + (True, ) * (round(log10(price)) - 2))
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
    parking_time = _bounds(round(normal(loc=AVG_PARKING_TIME, scale=AVG_PARKING_TIME / 3)), minimum=60, maximum=inf)
    usual_prediction = _bounds(normal(loc=0.3 - (lock_type.value / 20), scale=0.06))
    wk_version = randint(2, 3)
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


def _simple_insurance_premium_prediction(data: InsuranceInputData) -> float:
    pass
