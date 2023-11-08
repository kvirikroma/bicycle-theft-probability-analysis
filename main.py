from matplotlib import pyplot as plt

from utils.parking_locations_drawer import draw_dots, draw_prediction_function
from services.parking_locations_service import estimate_theft_probability
from repository.parking_locations_repository import Location, ParkingLocation, stream_parking_locations_nearby


def predict_theft(location: Location, power_of_distance: float = None):
    prediction, dots = estimate_theft_probability(
        location, get_probability_function=True, get_all_dots=True,
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


if __name__ == "__main__":
    # predict_theft(Location(48.435039, 35.020607))
    predict_theft(Location(48.538401, 35.069718))
