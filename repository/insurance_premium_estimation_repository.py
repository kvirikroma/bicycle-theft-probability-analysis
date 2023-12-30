from enum import Enum
from typing import Generator

from utils import ReprMixin


class LockType(Enum):
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
    other = 0


class FrameMaterial(Enum):
    aluminum = 1
    carbon = 2
    steel = 3
    titanium = 4
    wood = 5
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
            self, bike_price: int, lock_type: LockType, bike_type: BikeType, frame_material: FrameMaterial,
            parking_time_during_last_month: int, user_risk_tendency: UserRiskTendency, lock_price: int = 0,
            wk_device_revision_number: int = 3, bike_is_electric: bool = False, damage_insurance_included: bool = False
    ):
        self.bike_price, self.lock_type, self.bike_type = bike_price, lock_type, bike_type
        self.frame_material, self.parking_time_during_last_month = frame_material, parking_time_during_last_month
        self.user_risk_tendency, self.wk_device_revision_number = user_risk_tendency, wk_device_revision_number
        self.bike_is_electric, self.damage_insurance_included = bike_is_electric, damage_insurance_included
        self.lock_type = 0 if lock_type == LockType.none else lock_price


def generate_random_insurance_data(number: int) -> Generator[InsuranceInputData, None, None]:
    pass
