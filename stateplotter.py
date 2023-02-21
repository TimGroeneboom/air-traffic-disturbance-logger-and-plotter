import json
import pandas as pd
import geopandas as gpd
from shapely.geometry import Polygon
from pyproj import CRS, Proj, transform, Transformer
import contextily as ctx
import matplotlib.pyplot as plt

class StatePlotter():
    #
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

    def plot(self,
             states: list,
             bbox: tuple,
             figsize: tuple = (15, 15),
             tile_zoom: int = 8):
        # define lat lon bounding box
        lat_min = bbox[0]
        lat_max = bbox[1]
        lon_min = bbox[2]
        lon_max = bbox[3]

        # create data frames from states
        json_dict = []
        for state in states:
            json_dict.append(state.__dict__)

        # create data frame
        df = pd.DataFrame(json_dict, columns=self.columns)
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
        f, ax = plt.subplots(figsize=figsize)
        bounds_3857.plot(ax=ax, alpha=0.0, edgecolor="k")
        gdf_3857.plot(ax=ax, alpha=0.8, edgecolor="k")
        ctx.add_basemap(ax, zoom=tile_zoom)
        ax.set_axis_off()
        ax.get_xaxis().set_visible(False)
        ax.get_yaxis().set_visible(False)
        plt.savefig("traffic.png", bbox_inches="tight", pad_inches=-0.1)
        plt.close()








