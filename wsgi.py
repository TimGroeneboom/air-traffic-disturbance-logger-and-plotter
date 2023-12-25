from flaskr.app import create_app
from flaskr.scheduler import Scheduler
from flaskr import environment

application = create_app(enableScheduler=False)

import faulthandler
faulthandler.enable()

# setup scheduler
from apscheduler.schedulers.background import BackgroundScheduler
application.scheduler = Scheduler(loglevel=environment.LOGLEVEL)