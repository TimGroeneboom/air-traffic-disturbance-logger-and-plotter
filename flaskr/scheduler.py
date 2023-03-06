import logging
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from flaskr import environment
from flaskr.filehandler import remove_temp_files
from flaskr.utils.databasecollectionhandler import DatabaseCollectionHandler
from ovm.environment import load_environment
from ovm.planelogger import PlaneLogger


class Scheduler:
    def __init__(self, loglevel):
        # Create the background scheduler
        self.scheduler = BackgroundScheduler()
        logging.getLogger("apscheduler.scheduler").setLevel(loglevel)

        # Load environment
        self.environment = load_environment('environment.json')

        # Fire up temporary files remove job
        self.scheduler.add_job(func=remove_temp_files, trigger='interval', seconds=60)

        # Create database handler
        self.database_handler = DatabaseCollectionHandler(self.environment)
        self.scheduler.add_job(func=self.remove_entries_job, trigger='interval', days=1)
        self.remove_entries_job()

        # Create plane logger
        self.plane_logger = PlaneLogger(self.environment)
        if environment.PLANELOGGER_ENABLE:
            self.scheduler.add_job(func=self.log_planes, trigger='interval', seconds=environment.LOG_INTERVAL_SECONDS)

        # Start scheduler
        self.scheduler.start()

    def remove_entries_job(self):
        self.database_handler.remove_entries_older_than(datetime.now() - timedelta(days=environment.STATES_RETENTION_DAYS))

    def log_planes(self):
        self.plane_logger.log(environment.PLANELOGGER_BBOX)





