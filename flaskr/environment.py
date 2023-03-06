# pro6pp configuration
import logging

PRO6PP_AUTH_KEY = '<AUTH-KEY>'
PRO6PP_API_AUTO_COMPLETE_URL = 'https://api.pro6pp.nl/v2/autocomplete/nl'
PRO6PP_API_AUTO_LOCATOR_URL = 'https://api.pro6pp.nl/v2/locator/nl'

# API configuration
MAX_WORKERS = 8
MAX_SIZE_JOB_QUEUE = 1000

# lat lon address cache
LATLON_CACHE_EXPIRATION_DAYS = 180

# old records retention in days
STATES_RETENTION_DAYS = 31

# log interval
LOG_INTERVAL_SECONDS = 22

# planelogger bbox
PLANELOGGER_ENABLE = True
PLANELOGGER_BBOX = (49.44, 54.16, 2.82, 7.02)

# deploy test API
DEPLOY_TEST_API = True

# loglevel
LOGLEVEL='INFO'
