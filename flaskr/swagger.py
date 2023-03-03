from flasgger import LazyString
from flask import request

# Setup swagger template
swagger_template = dict(
    info= {
        'title': LazyString(lambda: 'Flight & Disturbance finder'),
        'version': LazyString(lambda: '0.1'),
        'description': LazyString(lambda: 'This document describes the Flight & Disturbance finder rest API'),
    },
    host=LazyString(lambda: request.host)
)

# Setup swagger config
swagger_config = {
    "headers": [],
    "specs": [
        {
            "endpoint": 'find_disturbances',
            "route": '/swagger/find_disturbances.json',
            "rule_filter": lambda rule: True,
            "model_filter": lambda tag: True,
        },
        {
            "endpoint": 'find_flights',
            "route": '/swagger/find_flights.json',
            "rule_filter": lambda rule: True,
            "model_filter": lambda tag: True,
        },
        {
            "endpoint": 'find_disturbances_pro6pp',
            "route": '/swagger/find_disturbances_pro6pp.json',
            "rule_filter": lambda rule: True,
            "model_filter": lambda tag: True,
        },
        {
            "endpoint": 'find_flights_pro6pp',
            "route": '/swagger/find_disturbances_pro6pp.json',
            "rule_filter": lambda rule: True,
            "model_filter": lambda tag: True,
        }
    ],
    "static_url_path": "/flasgger_static",
    "swagger_ui": True,
    "specs_route": "/apidocs/"
}