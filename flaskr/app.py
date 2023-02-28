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
    app.run()
