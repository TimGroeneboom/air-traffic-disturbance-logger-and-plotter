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


def main():
    # Set log level
    logging.basicConfig(level=environment.LOGLEVEL)

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

    # Setup scheduler
    scheduler = Scheduler(loglevel=environment.LOGLEVEL)

    # Run app
    app.run()


# Fire up app
if __name__ == '__main__':
    main()
