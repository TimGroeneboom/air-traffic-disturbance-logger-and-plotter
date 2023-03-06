import argparse
import logging
from flask import Flask

import flaskr.environment
from flaskr.scheduler import Scheduler
from flaskr.swagger import swagger_template, swagger_config
from flaskr.testapi import test_api_page
from flaskr.api import api_page
from flasgger import Swagger, LazyJSONEncoder
from flaskr import environment


# Create app
app = Flask(__name__)

# Setup json encoder
app.json_encoder = LazyJSONEncoder

# Register blueprints
app.register_blueprint(api_page)
if environment.DEPLOY_TEST_API:
    app.register_blueprint(test_api_page)

# Setup swagger
swagger = Swagger(app,
                  template=swagger_template,
                  config=swagger_config)

# Run
if __name__ == '__main__':
    # parse cli arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('-l', '--loglevel',
                        type=str.upper,
                        default='INFO',
                        help='LOG Level (DEBUG, INFO, WARNING, ERROR, CRITICAL)')
    args = parser.parse_args()

    # Set log level
    logging.basicConfig(level=args.loglevel)

    # Setup scheduler
    scheduler = Scheduler(loglevel=args.loglevel)

    # Run app
    app.run()
