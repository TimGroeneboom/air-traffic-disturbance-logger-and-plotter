import base64
import json
import os
from datetime import datetime, timedelta

import requests
from flask import request, render_template, redirect
from flask import Flask
from ovm.complainant import Complainant
from ovm.disturbancefinder import DisturbanceFinder, Disturbances
from ovm.environment import Environment
from ovm.environment import load_environment
from ovm.utils import DataclassJSONEncoder

# Load environment
environment = load_environment('../environment.json')

# Create app
app = Flask(__name__)

static_dir = 'static'
if not os.path.exists(static_dir):
    os.mkdir(static_dir)

@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        try:
            d = request.form
            url = 'http://localhost:5000/find_disturbance/%s/%f/%f/%i/%i/%i/%i' % \
                  (d['user'], float(d['lat']), float(d['lon']),
                   int(d['radius']), int(d['altitude']),
                   int(d['occurrences']),
                   int(d['timeframe']))
            disturbances = requests.get(url).json()

            files = []
            for user, found_disturbances in disturbances.items():
                for disturbance in found_disturbances['disturbances']:
                    temp_dir = 'temp'
                    if not os.path.exists(os.path.join(static_dir, temp_dir)):
                        os.mkdir(os.path.join(static_dir, temp_dir))

                    filename = os.path.join(temp_dir, '%s_%s.jpg' % (user, disturbance['begin']))
                    with open(os.path.join(static_dir, filename), 'wb') as fh:
                        fh.write(base64.decodebytes(bytes(disturbance['img'], "utf-8")))
                        fh.close()
                    files.append(filename)

            return render_template("result.html", imagelist=files)
        except Exception as ex:
            return ex.__str__()

    return render_template("input_test.html")


@app.route('/find_disturbance/<string:user>/'
           '<float:lat>/<float:lon>/'
           '<int:radius>/<int:altitude>/'
           '<int:occurrences>/<int:timeframe>/')
def find_disturbance(user, lat, lon, radius, altitude, occurrences, timeframe):
    complainants = [Complainant(user=user,
                                origin=(lat, lon),
                                radius=radius,
                                altitude=altitude,
                                occurrences=occurrences,
                                timeframe=timeframe)]

    now = datetime.now()
    disturbance_finder: DisturbanceFinder = DisturbanceFinder(environment)
    disturbances = disturbance_finder.find_disturbances(begin=now - timedelta(hours=24),
                                                        end=now,
                                                        complainants=complainants,
                                                        zoomlevel=14,
                                                        plot=True)
    return json.dumps(disturbances, cls=DataclassJSONEncoder, indent=4)


if __name__ == '__main__':
    app.run()
