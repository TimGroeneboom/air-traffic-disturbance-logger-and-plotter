import logging
import os
import datetime
from apscheduler.schedulers.background import BackgroundScheduler

# Static directory
static_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'static')
if not os.path.exists(static_dir):
    os.mkdir(static_dir)

# Temp directory
temp_dir_name = 'temp'
temp_dir = os.path.join(static_dir, temp_dir_name)
if not os.path.exists(temp_dir):
    os.mkdir(temp_dir)

# Delete all old temporary files
for filename in os.listdir(temp_dir):
    f = os.path.join(temp_dir, filename)
    logging.info('Removing old %s temp file' % filename)
    os.remove(f)

# Delete files in temp directory older than this value
seconds_till_delete = 5 * 60


# Background sceduled task, deletes files older than seconds_till_delete
def remove_temp_files():
    # Remove previous temp files
    now = datetime.datetime.now()
    for filename in os.listdir(temp_dir):
        f = os.path.join(temp_dir, filename)
        t = datetime.datetime.fromtimestamp(os.path.getmtime(f))
        if (now - t).seconds > seconds_till_delete:
            logging.info('Removing old %s temp file' % filename)
            os.remove(f)


# Fire up the scheduler
scheduler = BackgroundScheduler()
scheduler.add_job(func=remove_temp_files, trigger="interval", seconds=60)
scheduler.start()
