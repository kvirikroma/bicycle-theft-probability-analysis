import time

from matplotlib import pyplot as plt
from sys import maxsize
import json
from concurrent.futures import ProcessPoolExecutor

from utils.parking_locations_drawer import draw_dots, draw_prediction_function
from repository.parking_locations_repository import Location, ParkingLocationsSource, ParkingLocation, DATA_SOURCE_FILE
from services.insurance_premium_estimation_service import get_user_risk_tendency
from repository.insurance_premium_estimation_repository import UserRiskTendency
from services.parking_locations_service import (estimate_theft_probability, get_prediction_accuracy,
                                                TheftProbabilityPrediction)

# POWER_OF_DISTANCE = 1.432
POWER_OF_DISTANCE = 1.5


def predict_theft(location: Location, power_of_distance: float = None):
    prediction, dots = estimate_theft_probability(
        location, get_probability_function=True, get_all_dots=True, power_of_distance=POWER_OF_DISTANCE,
        **({"power_of_distance": power_of_distance} if power_of_distance else {})
    )
    draw_prediction_function(1, prediction)
    plt.show(block=False)
    draw_dots(location, dots, use_high_resolution=True)
    plt.xlabel("\n".join([
        f"Probability of theft: {prediction.theft_probability}",
        f"Probability of recovery in case of theft: {prediction.recovery_probability}"
    ]))
    plt.show()


def _add_info(u_id, loc, num):
    return u_id, loc, estimate_theft_probability(
        loc, get_probability_function=True, count_limit=num, power_of_distance=POWER_OF_DISTANCE
    )[0]


def calculate_risk_tendency_and_accuracy() -> dict[int: UserRiskTendency]:
    users: dict[int: list[tuple[ParkingLocation, TheftProbabilityPrediction]]] = {}
    locations_generator = ParkingLocationsSource().from_csv(DATA_SOURCE_FILE, add_user_id=True)
    executor = ProcessPoolExecutor()
    futures = []
    for number, location_with_user in zip(range(maxsize), locations_generator):
        location, user_id = location_with_user
        if not users.get(user_id):
            users[user_id] = []
        futures.append(executor.submit(_add_info, user_id, location, number))
    for i in futures:
        uid, location, estimation = i.result()
        users[uid].append((location, estimation))
    executor.shutdown()
    return {user_id: (
        get_user_risk_tendency(users[user_id]), get_prediction_accuracy(users[user_id])
    ) for user_id in users}


def theft_prediction_example():
    # predict_theft(Location(48.433039, 35.010607))  # good places
    # predict_theft(Location(48.530401, 35.069718))  # bad places (near to a dot)
    predict_theft(Location(48.525, 35.059))  # bad places (upper)
    # predict_theft(Location(48.437097, 35.0354721))  # near a green dot
    # predict_theft(Location(48.3661, 35.06612))  # right next to a green dot
    # predict_theft(Location(48.50305, 35.05875))  # right next to a red dot


if __name__ == "__main__":
    # theft_prediction_example()
    result = calculate_risk_tendency_and_accuracy()
    print(json.dumps({i: str(result[i][0]) for i in sorted(result)}, indent=2))
    print()
    print(json.dumps({i: str(result[i][1]) for i in sorted(result)}, indent=2))
