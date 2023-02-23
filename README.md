# Air Traffic Disturbance Logger & Plotter

This project aims to automatically log air traffic disturbance in your area. It uses the [opensky network](https://opensky-network.org/) to track air traffic around certain geographic bounds. 

Air traffic is stored in a MongoDB. See [logger.py](##logger.py). Disturbance checking and plotting is done using [disturbancecheck.py](##disturbancecheck.py)

## logger.py
Logs air traffic within certain geographic bounds and writes entries into a MongoDB database

Uses the OpenSky rest API (https://openskynetwork.github.io/opensky-api/rest.html)

Make sure to setup your environment correctly using MongoDB and OpenSky credentials in the ```environment.json``` 

Example usage:

```
# Query from opensky and store all air traffic within given certain geographic bounds every 22 seconds forever
python3 logger.py --bbox 49.44 54.16 2.82 7.02 --interval 22.0
```

All CLI arguments:

```
usage: logger.py [-h] [-b BBOX BBOX BBOX BBOX] [-l LOGLEVEL] [-p | --plot | --no-plot] [-o OUTPUTFILENAME]
                 [-z ZOOMLEVEL] [-i INTERVAL] [-r RUNS]

options:
  -h, --help            show this help message and exit
  -b BBOX BBOX BBOX BBOX, --bbox BBOX BBOX BBOX BBOX
                        Bounding Box [lat_min, lat_max, lon_min, lon_max]
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

disturbancecheck is a script that runs once, it gets all the registered complainers with their parameters and checks if any periods of disturbances have  occured within a certain timespan on their geographic location and disturbance parameters.

If a disturbance is registered, it tries to create a trajectory of all callsigns that have been found flying over complainants area. It then produces an output image like this

In the future, disturbance period information could automatically be sent to organizations responsible for collection aircraft noise complaints

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

