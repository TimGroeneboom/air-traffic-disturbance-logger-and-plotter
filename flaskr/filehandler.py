import dataclasses
import logging
import os
import queue
import time
import datetime
import atexit
from dataclasses import field
from apscheduler.schedulers.background import BackgroundScheduler
from attr import dataclass
from ovm.utils import convert_int_to_datetime, convert_datetime_to_int


class TempFile(object):
    def __init__(self, filename: str, datetime: int):
        self.filename = filename
        self.datetime = datetime


file_queue = queue.Queue()
files_to_delete = []
time_till_delete = 60

def register_temp_file(filename: str):
    file_queue.put(TempFile(filename, convert_datetime_to_int(datetime.datetime.now())))


def remove_temp_files():
    logging.info("Scanning for temporary files")
    while file_queue.empty() is False:
        files_to_delete.append(file_queue.get())

    files_deleted = []
    for temp_file in files_to_delete:
        if (datetime.datetime.now() - convert_int_to_datetime(temp_file.datetime)).seconds > time_till_delete:
            logging.info('Deleting %s' % temp_file.filename)
            try:
                os.remove(temp_file.filename)
            except Exception as ex:
                logging.exception(ex.__str__())
            files_deleted.append(temp_file)

    for file_deleted in files_deleted:
        files_to_delete.remove(file_deleted)


scheduler = BackgroundScheduler()
scheduler.add_job(func=remove_temp_files, trigger="interval", seconds=60)
scheduler.start()
