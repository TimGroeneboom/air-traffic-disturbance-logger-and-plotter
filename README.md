# Nuisance Check

## Logger.py
Logs air traffic within certain geographic bounds and writes entries into a MongoDB database

Uses the OpenSky rest API (https://openskynetwork.github.io/opensky-api/rest.html)

Make sure to setup your environment correctly using MongoDB and OpenSky credentials in the ```environment.json``` 

Example usage:

```
# Query from opensky and store all air traffic within given certain geographic bounds every 22 seconds forever
python3 python3 logger.py -l INFO --zoomlevel 9 --bbox 49.44 54.16 2.82 7.02 -i 22.0
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
