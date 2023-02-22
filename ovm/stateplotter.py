import json
import math

import pandas as pd
import geopandas as gpd
from shapely import LineString
from shapely.geometry import Polygon
from pyproj import CRS, Proj, transform, Transformer
import contextily as ctx
import matplotlib.pyplot as plt


class StatePlotter:
    #   Converting lat, lon (epsg:4326) into EPSG:3857
    # Ref: https://stackoverflow.com/questions/37523872/converting-coordinates-from-epsg-3857-to-4326-dotspatial/40403522#40403522

    def ConvertCoordinate(self, lon, lat):
        lonInEPSG4326 = lon
        latInEPSG4326 = lat

        lonInEPSG3857 = (lonInEPSG4326 * 20037508.34 / 180)
        latInEPSG3857 = (math.log(math.tan((90 + latInEPSG4326) * math.pi / 360)) / (math.pi / 180)) * (
                    20037508.34 / 180)
        return lonInEPSG3857, latInEPSG3857

    def plot_states(self,
                    states: list,
                    bbox: tuple,
                    figsize: tuple = (15, 15),
                    tile_zoom: int = 8,
                    filename: str = "traffic.png"):
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
        f, ax = plt.subplots(figsize=figsize)
        bounds_3857.plot(ax=ax, alpha=0.0, edgecolor="k")
        gdf_3857.plot_states(ax=ax, alpha=0.8, edgecolor="k")
        ctx.add_basemap(ax, zoom=tile_zoom)
        ax.set_axis_off()
        ax.get_xaxis().set_visible(False)
        ax.get_yaxis().set_visible(False)
        plt.savefig(filename, bbox_inches="tight", pad_inches=-0.1)
        plt.close()

    def plot_trajectories(self,
                    trajectories: dict,
                    bbox: tuple,
                    figsize: tuple = (15, 15),
                    tile_zoom: int = 8,
                    filename: str = "traffic.png"):
            # define lat lon bounding box
            lat_min = bbox[0]
            lat_max = bbox[1]
            lon_min = bbox[2]
            lon_max = bbox[3]

            linestrings = {}
            for key, value in trajectories.items():
                if len(value) >= 2:
                    linestring: LineString = LineString(value)
                    linestrings[key] = linestring

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
            # perform spatial join
            gdf = gpd.sjoin(gdf, bounds)

            # plot data on map
            bounds_3857 = bounds.to_crs(epsg=3857)  # web mercator
            gdf_3857 = gdf.to_crs(epsg=3857)  # web mercator
            f, ax = plt.subplots(figsize=figsize)
            bounds_3857.plot(ax=ax, alpha=0.0, edgecolor="k")
            gdf_3857.plot(ax=ax, alpha=0.8, edgecolor="k", column='callsign')
            min_3857 = self.ConvertCoordinate(lon_min, lat_min)
            max_3857 = self.ConvertCoordinate(lon_max, lat_max)
            ax.set_xlim(min_3857[0], max_3857[0])
            ax.set_ylim(min_3857[1], max_3857[1])
            ctx.add_basemap(ax, zoom=tile_zoom)
            ax.set_axis_off()
            ax.get_xaxis().set_visible(False)
            ax.get_yaxis().set_visible(False)
            plt.savefig(filename, bbox_inches="tight", pad_inches=-0.1)
            plt.close()








