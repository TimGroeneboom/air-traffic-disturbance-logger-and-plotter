import logging
import os
import datetime
from flaskr.environment import TEMP_DIR_FILE_ALIVE_TIME_SECONDS

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


# Background scheduled job, deletes files older than TEMP_DIR_FILE_ALIVE_TIME_SECONDS
def remove_temp_files():
    # Remove previous temp files
    now = datetime.datetime.now()
    for filename in os.listdir(temp_dir):
        f = os.path.join(temp_dir, filename)
        t = datetime.datetime.fromtimestamp(os.path.getmtime(f))
        if (now - t).seconds > TEMP_DIR_FILE_ALIVE_TIME_SECONDS:
            logging.info('Removing old %s temp file' % filename)
            os.remove(f)
