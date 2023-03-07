import logging
from flask import Flask
from flaskr.scheduler import Scheduler
from flaskr.swagger import swagger_template, swagger_config
from flaskr.testapi import test_api_page
from flaskr.api import api_page
from flasgger import Swagger, LazyJSONEncoder
from flaskr import environment


def create_app():
    # Create app
    app = Flask(__name__)

    # Set log level
    logging.basicConfig(level=environment.LOGLEVEL)

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

    return app


# Fire up app from cli
if __name__ == '__main__':
    create_app().run()

