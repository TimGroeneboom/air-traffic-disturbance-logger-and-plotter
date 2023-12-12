from flaskr.app import create_app
from flaskr.scheduler import Scheduler
from flaskr import environment

application = create_app()

import faulthandler
faulthandler.enable()

# setup scheduler
application.scheduler = Scheduler(loglevel=environment.LOGLEVEL)