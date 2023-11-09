from math import log2, ceil
from matplotlib import pyplot as plt
from mpl_toolkits.basemap import Basemap

from services.parking_locations_service import DotAndItsImportance, TheftProbabilityPrediction
from repository.parking_locations_repository import get_map_corners
from repository import Location, EPSILON


def _configure_locations_plt(use_high_resolution: bool = False, disable_axes: bool = False):
    plt.figure(
        'Current location and the "history" of this area',
        figsize=((20, 20) if use_high_resolution else (10, 10))
    )
    if disable_axes:
        ax = plt.axes([0, 0, 1, 1], frameon=False)
        ax.get_xaxis().set_visible(False)
        ax.get_yaxis().set_visible(False)
        plt.autoscale(tight=True)


def draw_prediction_function(start: int, prediction: TheftProbabilityPrediction, show: bool = False):
    if start <= 0:
        raise ValueError("The 'start' can't be less than 1")
    plt.figure("Linear regression of the theft probability, depending on time", (16, 4))
    if prediction.regression_params is not None:
        end = ceil((1.0 - prediction.regression_params.b) * 1.05 / prediction.regression_params.a)
        x = [*range(start, end + 1)]
        y = [prediction.probability_function(i) for i in x]
        plt.plot([i / 3600 for i in x], y)
    plt.xlabel("Time (in hours)")
    plt.ylabel("Risk of a theft (from 0 to 1)")
    plt.title("This is how a theft probability changes here depending on parking time" + (
        '' if prediction.regression_params is not None else
        "\n(Error: can not build the plot since the regression parameters don't exist)"
    ))
    if show:
        plt.show()


def draw_dots(
        central_location: Location, dots_with_importance: list[DotAndItsImportance],
        show: bool = False, use_high_resolution: bool = False, use_logarithm: bool = True
) -> None:
    radius = round(
        max(i.dot - central_location for i in dots_with_importance) * 1.2 + 1000
    ) if dots_with_importance else 20000
    lat_min, lat_max, lon_min, lon_max = get_map_corners(central_location, radius)
    _configure_locations_plt(use_high_resolution)
    basemap = Basemap(
        projection='merc', llcrnrlat=lat_min, urcrnrlat=lat_max,
        llcrnrlon=lon_min, urcrnrlon=lon_max, resolution=('h' if use_high_resolution else 'i')
    )
    basemap.drawcoastlines()
    basemap.fillcontinents(color='#999', lake_color='#8ae')
    basemap.drawmapboundary(fill_color='#8ae')
    basemap.drawcountries()
    basemap.drawrivers(color="#457")
    if dots_with_importance:
        if use_logarithm:
            importance_list = [log2(i.importance) for i in dots_with_importance]
        else:
            importance_list = [i.importance for i in dots_with_importance]
        max_importance = max(importance_list) + (EPSILON ** 2)
        min_importance = min(importance_list)
        importance_list = [
            min(1.0, ((i - min_importance) / (max_importance - min_importance)) * 0.85 + 0.15)
            for i in importance_list
        ]
        for dot, importance in zip((i.dot for i in dots_with_importance), importance_list):
            basemap.plot(
                *basemap(*reversed(dot.coordinates)), marker='o', alpha=importance,
                color=("#f00" if dot.stolen and not dot.recovered else ("#0f0" if not dot.stolen else "#fb1"))
            )
    basemap.plot(*basemap(*reversed(central_location.coordinates)), 'bP')
    if show:
        plt.show()
