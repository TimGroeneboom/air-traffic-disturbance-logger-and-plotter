import datetime
import math
import string


# Converts a datetime object into an int64 in the following format %Y%m%d%H%M%S
def convert_datetime_to_int(dt: datetime):
    return int(dt.strftime("%Y%m%d%H%M%S"))


# Converts an int64 into a datetime object in %Y%m%d%H%M%S format
def convert_int_to_datetime(value: int):
    return datetime.datetime.strptime(str(value), "%Y%m%d%H%M%S")


# Remove whitespaces from string
def remove_whitespace(value: str):
    return value.replace(' ', '')


# Checks if given array contains value
def list_contains_value(arr: list, value):
    for other in arr:
        if other == value:
            return True
    return False


# Returns a bbox around lat, lon origin (epsg:4326). Radius is in kilometers
# Returns bbox in following order (lat_min, lat_max, lon_min, lon_max)
def get_geo_bbox_around_coord(origin: tuple, radius: float):
    r_earth = 6378
    r = radius / r_earth
    t_1 = 180.0 / math.pi
    t_2 = t_1 / math.cos(origin[0] * math.pi / 180.0)

    lat_min = origin[0] - r * t_1
    lon_min = origin[1] - r * t_2
    lat_max = origin[0] + r * t_1
    lon_max = origin[1] + r * t_2
    return lat_min, lat_max, lon_min, lon_max


#   Converting lat, lon (epsg:4326) into EPSG:3857
# Ref: https://stackoverflow.com/questions/37523872/converting-coordinates-from-epsg-3857-to-4326-dotspatial/40403522#40403522
def convert_epsg4326_to_epsg3857(lon, lat):
    lonInEPSG4326 = lon
    latInEPSG4326 = lat

    lonInEPSG3857 = (lonInEPSG4326 * 20037508.34 / 180)
    latInEPSG3857 = (math.log(math.tan((90 + latInEPSG4326) * math.pi / 360)) / (math.pi / 180)) * (
            20037508.34 / 180)
    return lonInEPSG3857, latInEPSG3857
