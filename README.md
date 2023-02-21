# PlaneLogger

Logs air traffic within certain geographic bounds and writes entries into a MongoDB database

Uses the OpenSky rest API (https://openskynetwork.github.io/opensky-api/rest.html)

Example usage:

```
# Query from opensky and store all air traffic within given certain geographic bounds every 22 seconds
# Replace username and password with your OpenSky credentials
python3 main.py -c <username> <password> -l INFO --bbox 49.44 54.16 2.82 7.02 -i 22.0
```
