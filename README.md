# Air Traffic Disturbance Logger & Plotter

This project aims to automatically log air traffic disturbance in your area. It uses the [flightradar24](https://https://www.flightradar24.com/52.40,4.71/11/) to track air traffic around certain geographic bounds. 

Air traffic data is stored using MongoDB. See the [planelogger script](ovm/planelogger.py). See the [planelogger section](#loggerpy) for CLI instructions. 
Disturbance checking and plotting is done using the [disturbance finder script](ovm/disturbancefinder.py). See [Disturbance Check](#disturbancecheckpy) for CLI instructions.

Also, this project contains a Flask app that combines logging and plotting and serves the air traffic data using a REST API. See [Setup Flask App](#setup-flask-app) for instructions.

The project contains a [Dockerfile](Dockerfile) that serves the app using Ubuntu 22.04, python 3.10, gunicorn and nginx using a reverse proxy. See [Deployment & Docker](#deployment--docker)

This project was developed, deployed and tested on Ubuntu 22.04 and Python 3.10

The following README assumes you're somewhat comfortable setting up Python virtual environments and that MongoDB is installed.
See [MongoDB Installation](https://www.mongodb.com/docs/manual/installation/)

## logger.py
Logs air traffic within certain geographic bounds and writes entries into a MongoDB database

Uses the flightradar24 rest API

Make sure to setup your environment correctly using MongoDB and flightradar credentials in the [environment.json](environment.json)

Example usage:

```
# Query from flightradar24 and store all air traffic within given radius of given center
python3 logger.py --center 52.118077847871724 5.648460603506286 --radius 150000 --interval 22.0
```

All CLI arguments:

```
usage: logger.py [-h] [-c latitude longitude] [-r radius] [-l LOGLEVEL] [-p | --plot | --no-plot] [-o OUTPUTFILENAME]
                 [-z ZOOMLEVEL] [-i INTERVAL] [-r RUNS]

options:
  -h, --help            show this help message and exit
  -c latitude longitude, --center latitude longitude
                        Center [lat, lon]
  -r radius, --radius meters
                        Radius in meters
  -l LOGLEVEL, --loglevel LOGLEVEL
                        LOG Level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
  -p, --plot, --no-plot
                        Creates a plot for each run
  -o OUTPUTFILENAME, --outputfilename OUTPUTFILENAME
                        Plot base output filename, run number and png extension gets appended
  -z ZOOMLEVEL, --zoomlevel ZOOMLEVEL
  -i INTERVAL, --interval INTERVAL
                        Time between runs
  -r RUNS, --runs RUNS  Amount of runs between intervals, default = 0 meaning infinite
```

## disturbancecheck.py

disturbancecheck is a script that runs once and checks if any periods of disturbance have happened within set timespan.

If a disturbance is registered, it tries to create a trajectory of all callsigns that have been found flying over given area. It then produces an output image like this

![This is an image](disturbance_example.jpg)

All CLI arguments:

```
usage: disturbancecheck.py [-h] [-l LOGLEVEL] [-p | --plot | --no-plot] [-z ZOOMLEVEL]

options:
  -h, --help            show this help message and exit
  -l LOGLEVEL, --loglevel LOGLEVEL
                        LOG Level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
  -p, --plot, --no-plot
                        Creates a plot for each run
  -z ZOOMLEVEL, --zoomlevel ZOOMLEVEL
                        Zoom level of contextly maps
```

## environment.json

The [environment.json](environment.json) in the repository root directory contains configuration needed for both logger and disturbancecheck to run. It contains the following:
* flightradar24 credentials
* MongoDB configuration

# Setup Flask App

All files necessary for Flask to run the server-side application are contained in the ```flaskr``` directory. The Flask app does the following.

* Serves a rest API call around ```find_flights``` in ```disturbancefinder.py```
* Serves a rest API call around ```find_disturbances``` in ```disturbancefinder.py```
* Documentation is done using swagger
* Optionally, serves a user-friendly test HTML page around ```find_flights``` and ```find_disturbances```

To run the flask app. 

* Clone this repository
* CD to root directory of the cloned repository
* Setup a virtual environment ```virtualenv venv```
* Activate your virtual environment ```source venv/bin/activate```
* Install requirements ```pip install -r requirements.txt```
* You can now fire up the flask app from the CLI using the following command, replace ```<HOST-PORT>``` and ```<HOST-IP>``` with desired port and ip
  * ```flask --app flaskr/app:create_app run -p <HOST-PORT> --host=<HOST-IP>```

## App Configuration

All configuration and environment variables around the running Flask app reside in [flaskr/environment.py](flaskr/environment.py)

### Pro6pp
The following properties are necessary for looking up lat, lon coordinates using pro6pp. This means you can only lookup postal codes and streetnumbers from The Netherlands if you have a pro6pp account. If you tend to use the App outside of the Netherlands, you cannot use postal codes or streetnumbers in your query

For information about pro6pp see -> https://www.pro6pp.nl/

```
PRO6PP_AUTH_KEY = '<AUTH-KEY>'
PRO6PP_API_AUTO_COMPLETE_URL = 'https://api.pro6pp.nl/v2/autocomplete/nl'
PRO6PP_API_AUTO_LOCATOR_URL = 'https://api.pro6pp.nl/v2/locator/nl'
```

### latitude longitude address cache
To keep calls to pro6pp to a minimum, queried latitude and longitude will be stored in the MongoDB together with a timestamp. If timestamp is older than designated days, a new query will be made to update the latitude longitude coordinates
```
LATLON_CACHE_EXPIRATION_DAYS = 180
```

### States retention days
Once a day, a background job will check and delete states older than these amount of days in the database.
```
STATES_RETENTION_DAYS = 31
```

### Planelogger
The following properties determine how the planelogger will operate. These properties replace the CLI args as described in [logger.py](##logger.py)

```
LOG_INTERVAL_SECONDS = 22
PLANELOGGER_ENABLE = True
PLANELOGGER_BBOX = (49.44, 54.16, 2.82, 7.02)
```

### Test API
The following property determines if ```apitests/find_flights``` and ```apitests/find_disturbances``` will be deployed.

```
DEPLOY_TEST_API = True
```
### loglevel
Sets loglevel of app and background jobs

```
LOGLEVEL='INFO'
```

### Temp Files
Time of temporary files to stay alive 

```commandline
TEMP_DIR_FILE_ALIVE_TIME_SECONDS = 300
```

## Testing

With the running Flask application. Navigate to ```http://127.0.0.1/apidocs``` on your development machine to read the documentation generated by Swagger and test the API calls.
Optionally, if the ```DEPLOY_TEST_API = True``` navigate to ```http://127.0.0.1/apitests/find_flights``` or ```http://127.0.0.1/apitests/find_disturbances```

## Deployment & Docker

The repositoy contain a [Dockerfile](Dockerfile) that creates a container that runs the Flask app using [Gunicorn](https://gunicorn.org/) served via reverse proxy using [NGINX](https://www.nginx.com/).

To create the Docker container do the following

- Make sure all settings are correct in the [Environment.json](environment.json) and [environment.py](flaskr/environment.py).
- Run the [build_docker.sh](build_docker.sh) script
- Create a container and run the created Docker image using the following command, replace <CONTAINER_NAME> with a name of your liking
  - ```docker run --name <CONTAINER_NAME> air-traffic-logger-and-plotter:latest```
- Optionally, save the created container using the following command, replace <FILE_NAME> with a name of your choosing
  - ```docker save air-traffic-logger-and-plotter:latest > <FILE_NAME>.tar```
