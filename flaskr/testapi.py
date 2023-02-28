import base64
import os
from dataclasses import dataclass, field
import requests
from flask import Blueprint, request, render_template

# Create test api page
test_api_page = Blueprint('testapi', __name__, template_folder='templates')


class RenderDisturbance:
    file: str = field(default_factory=str)
    begin: str = field(default_factory=str)
    end: str = field(default_factory=str)
    callsigns: list = field(default_factory=list)
    plot: bool = field(default_factory=bool)


static_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'static')
if not os.path.exists(static_dir):
    os.mkdir(static_dir)


@test_api_page.route("/api", methods=["GET", "POST"])
def show():
    if request.method == "POST":
        try:
            d = request.form
            url = 'http://%s/api/find_disturbance/%s/%f/%f/%i/%i/%i/%i/%i/%i' % \
                  (request.host,
                   d['user'], float(d['lat']), float(d['lon']),
                   int(d['radius']), int(d['altitude']),
                   int(d['occurrences']),
                   int(d['timeframe']),
                   int('plot' in d),
                   int(d['zoomlevel']))
            disturbances = requests.get(url).json()

            render_disturbances = []
            for user, found_disturbances in disturbances.items():
                for disturbance in found_disturbances['disturbances']:
                    render_disturbance = RenderDisturbance()
                    render_disturbance.file = ""
                    render_disturbance.begin = disturbance['begin']
                    render_disturbance.end = disturbance['end']
                    render_disturbance.callsigns = disturbance['callsigns']
                    if len(disturbance['img']) > 0:
                        temp_dir = 'temp'
                        if not os.path.exists(os.path.join(static_dir, temp_dir)):
                            os.mkdir(os.path.join(static_dir, temp_dir))

                        filename = os.path.join(temp_dir, '%s_%s.jpg' % (user, disturbance['begin']))
                        with open(os.path.join(static_dir, filename), 'wb') as fh:
                            fh.write(base64.decodebytes(bytes(disturbance['img'], "utf-8")))
                            fh.close()
                        render_disturbance.file = filename
                        render_disturbance.plot = True
                    else:
                        render_disturbance.plot = False
                    render_disturbances.append(render_disturbance)

            return render_template("api/result.html",
                                   disturbances=render_disturbances)
        except Exception as ex:
            return ex.__str__()

    return render_template("api/input_test.html")