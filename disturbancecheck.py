# Import the python libraries
import argparse
import base64
from datetime import datetime, timedelta
import logging
from io import StringIO, BytesIO
from PIL import Image
from ovm import environment
from ovm.complainant import Complainant
from ovm.disturbancefinder import DisturbanceFinder
from ovm.utils import convert_datetime_to_int

if __name__ == '__main__':
    # parse cli arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('-l', '--loglevel',
                        type=str.upper,
                        default='INFO',
                        help='LOG Level (DEBUG, INFO, WARNING, ERROR, CRITICAL)')
    parser.add_argument('-p', '--plot',
                        action=argparse.BooleanOptionalAction,
                        help='Creates a plot for each run')
    parser.add_argument('-z', '--zoomlevel',
                        type=int,
                        default=14,
                        help='Zoom level of contextly maps')
    args = parser.parse_args()

    # Set log level
    logging.basicConfig(level=args.loglevel)

    # TODO: fetch complainants from database
    complainants = [Complainant(user='Jan',
                                origin=(52.311502, 4.827680),  # Amsterdamse Bos
                                radius=1000,
                                altitude=1000,
                                occurrences=4,
                                timeframe=60)]
    """
    Complainant(user='Henk',
                origin=(52.469640, 4.721354),  # Assendelft
                # Warmond
                # origin=(52.187571, 4.504961),
                radius=1000,
                altitude=1000,
                occurrences=4,
                timeframe=60),
    Complainant(user='Pieter',
                origin=(52.187571, 4.504961),  # Warmond
                radius=1000,
                altitude=1000,
                occurrences=4,
                timeframe=60),
    Complainant(user='Tim',
                origin=(52.402321, 4.916406),  # Christoffelkruidstraat
                radius=1000,
                altitude=1000,
                occurrences=4,
                timeframe=60)
    """

    # Load environment
    environment = environment.load_environment('environment.json')

    # Find all disturbances
    now = datetime.now()
    disturbance_finder: DisturbanceFinder = DisturbanceFinder(environment)
    disturbances = disturbance_finder.find_disturbances(begin=now - timedelta(hours=24),
                                                        end=now,
                                                        complainants=complainants,
                                                        zoomlevel=args.zoomlevel,
                                                        plot=args.plot)
    elapsed = datetime.now() - now
    logging.info('Operation took %f seconds' % elapsed.seconds)

    # Write plots to disk
    if args.plot:
        for user, found_disturbances in disturbances.items():
            index: int = 0
            for disturbance in found_disturbances.disturbances:
                with open('%s_%i.jpg' % (user, index), 'wb') as fh:
                    fh.write(base64.decodebytes(bytes(disturbance.img, "utf-8")))
                    fh.close()

    # Exit gracefully
    exit(0)
