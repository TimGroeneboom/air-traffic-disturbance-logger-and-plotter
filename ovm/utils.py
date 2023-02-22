import datetime
import string


def convert_datetime_to_int(dt: datetime):
    return int(dt.strftime("%Y%m%d%H%M%S"))


def convert_int_to_datetime(value: int):
    return datetime.datetime.strptime(str(value), "%Y%m%d%H%M%S")


def callsign_compare(callsign1: str, callsign2: str):
    return callsign1.replace(' ', '') == callsign2.replace(' ', '')

