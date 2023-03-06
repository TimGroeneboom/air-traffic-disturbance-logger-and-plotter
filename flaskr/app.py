import argparse
import logging
from flask import Flask
from flaskr.swagger import swagger_template, swagger_config
from flaskr.testapi import test_api_page
from flaskr.api import api_page
from flasgger import Swagger, LazyJSONEncoder


# Create app
app = Flask(__name__)

# Setup json encoder
app.json_encoder = LazyJSONEncoder

# Register blueprints
app.register_blueprint(test_api_page)
app.register_blueprint(api_page)

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

    # Run app
    app.run()
