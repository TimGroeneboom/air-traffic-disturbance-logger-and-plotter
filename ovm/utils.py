import dataclasses
import datetime
import json
import math
import string

import numpy
import pandas as pd


def convert_datetime_to_int(dt: datetime):
    """
    Converts a datetime object into an int64 in the following format %Y%m%d%H%M%S
    :param dt: the datetime object
    :return: an int64
    """
    return int(dt.strftime("%Y%m%d%H%M%S"))


def convert_int_to_datetime(value: int):
    """
    Converts an int64 into a datetime object in %Y%m%d%H%M%S format
    :param value: the int64
    :return: the datetime object
    """
    return datetime.datetime.strptime(str(value), "%Y%m%d%H%M%S")


def remove_whitespace(value: str):
    """
    Remove whitespaces from string
    :param value: the string
    :return: the string without whitespaces
    """
    return value.replace(' ', '')


def list_contains_value(arr: list, value):
    """
    Checks if given array contains value
    :param arr: The array
    :param value: The value
    :return: True if found
    """
    for other in arr:
        if other == value:
            return True
    return False


def get_geo_bbox_around_coord(origin: tuple, radius: float):
    """
    Returns a bbox around lat, lon origin (epsg:4326). Radius is in kilometers
    Returns bbox in following order (lat_min, lat_max, lon_min, lon_max)
    :param origin: origin in lat lon
    :param radius: radius in meters
    :return: geo bbox in following order (lat_min, lat_max, lon_min, lon_max)
    """
    r_earth = 6378
    r = radius / r_earth
    t_1 = 180.0 / math.pi
    t_2 = t_1 / math.cos(origin[0] * math.pi / 180.0)

    lat_min = origin[0] - r * t_1
    lon_min = origin[1] - r * t_2
    lat_max = origin[0] + r * t_1
    lon_max = origin[1] + r * t_2
    return lat_min, lat_max, lon_min, lon_max


def convert_epsg4326_to_epsg3857(lon, lat):
    """
    Converting lat, lon (epsg:4326) into EPSG:3857
    Ref: https://stackoverflow.com/questions/37523872/converting-coordinates-from-epsg-3857-to-4326-dotspatial/40403522#40403522
    :param lon: longitude
    :param lat: latitude
    :return: converted lon, lat
    """
    lonInEPSG4326 = lon
    latInEPSG4326 = lat

    lonInEPSG3857 = (lonInEPSG4326 * 20037508.34 / 180)
    latInEPSG3857 = (math.log(math.tan((90 + latInEPSG4326) * math.pi / 360)) / (math.pi / 180)) * (
            20037508.34 / 180)
    return lonInEPSG3857, latInEPSG3857


class DataclassJSONEncoder(json.JSONEncoder):
    """
    Use this encoder to serialize dataclasses
    """

    def default(self, o):
        if dataclasses.is_dataclass(o):
            return dataclasses.asdict(o)
        return super().default(o)


def xstr(s):
    if s is None:
        return ''
    return str(s)