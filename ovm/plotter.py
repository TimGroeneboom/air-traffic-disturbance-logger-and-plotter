import io
import threading
from datetime import datetime
import matplotlib
import pandas as pd
import geopandas as gpd
from shapely import LineString, Point
from shapely.geometry import Polygon
from pyproj import CRS
import contextily as ctx
import matplotlib.pyplot as plt
from ovm.utils import convert_epsg4326_to_epsg3857

"""
Use the agg backend because we only want to plot to files
See : https://matplotlib.org/stable/users/explain/backends.html
"""
matplotlib.use('agg')

def plot_trajectories(title: str,
                      origin: tuple,
                      begin: datetime,
                      end: datetime,
                      trajectories: dict,
                      bbox: tuple,
                      figsize: tuple = (15, 15),
                      tile_zoom: int = 8):
    """
    Plots trajectories into a plot with trajectories and a geographic bounding box plus some meta-information
    about the disturbance period.
    Returns image as bytes
    @param title: title of the plot
    @param origin: origin in lat, lon
    @param begin: beginning of the plot in time
    @param end: end of the plot in time
    @param trajectories: all the trajectories to plot
    @param bbox: the geographic bounding box
    @param figsize: the figure size
    @param tile_zoom: the zoomlevel
    @return: image in bytes
    """

    # define lat lon bounding box
    lat_min = bbox[0]
    lat_max = bbox[1]
    lon_min = bbox[2]
    lon_max = bbox[3]

    # calc average altitude
    average_altitude = 0
    idx = 0
    linestrings = {}
    for key, value in trajectories.items():
        if len(value.coords) >= 2:
            linestring: LineString = LineString(value.coords)
            linestrings[key] = linestring
            average_altitude += value.average_altitude
            idx += 1
    average_altitude /= idx

    data = []
    for key, value in linestrings.items():
        data.append([key, value])

    # create data frame
    df = pd.DataFrame(data, columns=['callsign', 'LineString_obj'])
    gdf = gpd.GeoDataFrame(
        df,
        geometry='LineString_obj',
        crs=CRS("EPSG:4326"),  # WGS84
    )
    bounds = gpd.GeoDataFrame(geometry=[Polygon([[lon_min, lat_min],
                                                 [lon_min, lat_max],
                                                 [lon_max, lat_max],
                                                 [lon_max, lat_min]])],
                              crs="EPSG:4326")
    center = gpd.GeoDataFrame(geometry=[Point([origin[1], origin[0]])],
                              crs="EPSG:4326")
    # perform spatial join
    gdf = gpd.sjoin(gdf, bounds)

    # plot data on map
    bounds_3857 = bounds.to_crs(epsg=3857)  # web mercator
    gdf_3857 = gdf.to_crs(epsg=3857)  # web mercator
    center_3857 = center.to_crs(epsg=3857)  # web mercator

    # Because matplotlib is not multi threaded, lock
    f, ax = plt.subplots(figsize=figsize)
    center_3857.plot(ax=ax, alpha=0.7, edgecolor="blue")
    bounds_3857.plot(ax=ax, alpha=0.0, edgecolor="blue")
    gdf_3857.plot(ax=ax, alpha=0.4, edgecolor="red", column='callsign')
    min_3857 = convert_epsg4326_to_epsg3857(lon_min, lat_min)
    max_3857 = convert_epsg4326_to_epsg3857(lon_max, lat_max)
    ax.set_xlim(min_3857[0], max_3857[0])
    ax.set_ylim(min_3857[1], max_3857[1])
    ctx.add_basemap(ax, zoom=tile_zoom)
    ax.get_xaxis().set_visible(False)
    ax.get_yaxis().set_visible(False)
    ax.text(0.05, 0.10,
            '%s\nlocation: [%f, %f]\nperiod: [%s, %s]\nflights: %i\naverage altitude: %im' %
            (title, origin[0], origin[1], begin.strftime("%Y-%m-%d %H:%M:%S"), end.strftime("%Y-%m-%d %H:%M:%S"),
             len(trajectories.items()), average_altitude),
            verticalalignment='bottom', horizontalalignment='left',
            transform=ax.transAxes,
            color='black', fontsize=15,
            bbox={'facecolor': 'white', 'alpha': 1, 'pad': 10})
    ax.add_patch(plt.Circle((0.5, 0.5), 0.2, color='red', alpha=1.0))

    img: bytes
    with io.BytesIO() as buffer: # use buffer memory
        plt.savefig(buffer, format='jpg', bbox_inches="tight", pad_inches=-0.1)
        buffer.seek(0)
        img = buffer.getvalue()
    plt.close()

    return img


def plot_states(states: list,
                bbox: tuple,
                figsize: tuple = (15, 15),
                tile_zoom: int = 8):
    """
    Draws all states/plane locations onto a map
    @param states: all states/planes
    @param bbox: geographic bounding box
    @param figsize: figure size
    @param tile_zoom: zoomlevel
    @return: image in bytes
    """

    # define columns
    columns = [
        "icao24",
        "callsign",
        "origin_country",
        "time_position",
        "last_contact",
        "longitude",
        "latitude",
        "baro_altitude",
        "on_ground",
        "velocity",
        "true_track",
        "vertical_rate",
        "sensors",
        "geo_altitude",
        "squawk",
        "spi",
        "position_source",
    ]

    # define lat lon bounding box
    lat_min = bbox[0]
    lat_max = bbox[1]
    lon_min = bbox[2]
    lon_max = bbox[3]

    # create data frame
    df = pd.DataFrame(states, columns=columns)
    gdf = gpd.GeoDataFrame(
        df,
        geometry=gpd.points_from_xy(df.longitude, df.latitude),
        crs=CRS("EPSG:4326"),  # WGS84
    )
    bounds = gpd.GeoDataFrame(geometry=[Polygon([[lon_min, lat_min],
                                                 [lon_min, lat_max],
                                                 [lon_max, lat_max],
                                                 [lon_max, lat_min]])],
                              crs="EPSG:4326")
    # perform spatial join
    gdf = gpd.sjoin(gdf, bounds, predicate='within', how='inner')

    # plot data on map
    bounds_3857 = bounds.to_crs(epsg=3857)  # web mercator
    gdf_3857 = gdf.to_crs(epsg=3857)  # web mercator

    # Because matplotlib is not multi threaded lock
    f, ax = plt.subplots(figsize=figsize)
    bounds_3857.plot(ax=ax, alpha=0.0, edgecolor="k")
    gdf_3857.plot(ax=ax, alpha=0.8, edgecolor="k")
    ctx.add_basemap(ax, zoom=tile_zoom)
    ax.set_axis_off()
    ax.get_xaxis().set_visible(False)
    ax.get_yaxis().set_visible(False)
    img: bytes
    with io.BytesIO() as buffer:  # use buffer memory
        plt.savefig(buffer, format='jpg', bbox_inches="tight", pad_inches=-0.1)
        buffer.seek(0)
        img = buffer.getvalue()
    plt.close()

    return img


