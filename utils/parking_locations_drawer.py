from matplotlib import pyplot as plt
from mpl_toolkits.basemap import Basemap

from services.parking_locations_service import DotAndItsImportance
from repository.parking_locations_repository import get_map_corners
from repository import Location


def _configure_plt(use_high_resolution: bool = False):
    plt.figure(figsize=((20, 20) if use_high_resolution else (10, 10)))
    ax = plt.axes([0, 0, 1, 1], frameon=False)
    ax.get_xaxis().set_visible(False)
    ax.get_yaxis().set_visible(False)
    plt.autoscale(tight=True)


def draw_dots(
        central_location: Location, dots_with_importance: list[DotAndItsImportance],
        show: bool = False, use_high_resolution: bool = False
) -> None:
    radius = round(max(i.dot - central_location for i in dots_with_importance) * 1.1)
    lat_min, lat_max, lon_min, lon_max = get_map_corners(central_location, radius)
    _configure_plt(use_high_resolution)
    basemap = Basemap(
        projection='merc', llcrnrlat=lat_min, urcrnrlat=lat_max,
        llcrnrlon=lon_min, urcrnrlon=lon_max, resolution=('h' if use_high_resolution else 'i')
    )
    basemap.drawcoastlines()
    basemap.fillcontinents(color='#aaa', lake_color='#8ae')
    basemap.drawmapboundary(fill_color='#8ae')
    basemap.drawcountries()
    basemap.drawrivers(color="#457")
    max_importance = max(i.importance for i in dots_with_importance)
    min_importance = min(i.importance for i in dots_with_importance)
    importance_list = [
        min(1.0, ((i.importance - min_importance) / (max_importance - min_importance)) * 0.85 + 0.2)
        for i in dots_with_importance
    ]
    basemap.plot(*basemap(*reversed(central_location.coordinates)), 'bo')
    for dot, importance in zip((i.dot for i in dots_with_importance), importance_list):
        basemap.plot(
            *basemap(*reversed(dot.coordinates)), marker='o', alpha=importance,
            color=("#f00" if dot.stolen and not dot.recovered else ("#0f0" if not dot.stolen else "#ff0"))
        )
    if show:
        plt.show()
