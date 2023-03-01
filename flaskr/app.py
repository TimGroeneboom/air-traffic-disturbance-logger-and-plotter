import argparse
import logging
from flask import Flask
from flaskr.testapi import test_api_page
from flaskr.api import api_page

# Create app
app = Flask(__name__)

# Register blueprints
app.register_blueprint(test_api_page)
app.register_blueprint(api_page)

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
