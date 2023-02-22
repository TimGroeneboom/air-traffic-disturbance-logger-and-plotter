import datetime
import math
import string


def convert_datetime_to_int(dt: datetime):
    return int(dt.strftime("%Y%m%d%H%M%S"))


def convert_int_to_datetime(value: int):
    return datetime.datetime.strptime(str(value), "%Y%m%d%H%M%S")


def callsign_compare(callsign1: str, callsign2: str):
    return callsign1.replace(' ', '') == callsign2.replace(' ', '')


#   Converting lat, lon (epsg:4326) into EPSG:3857
# Ref: https://stackoverflow.com/questions/37523872/converting-coordinates-from-epsg-3857-to-4326-dotspatial/40403522#40403522

def convert_epsg4326_to_epsg3857(lon, lat):
    lonInEPSG4326 = lon
    latInEPSG4326 = lat

    lonInEPSG3857 = (lonInEPSG4326 * 20037508.34 / 180)
    latInEPSG3857 = (math.log(math.tan((90 + latInEPSG4326) * math.pi / 360)) / (math.pi / 180)) * (
                20037508.34 / 180)
    return lonInEPSG3857, latInEPSG3857

