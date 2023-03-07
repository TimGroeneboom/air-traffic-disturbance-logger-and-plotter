# Import the python libraries
import argparse
import base64
from datetime import datetime, timedelta
import logging
from ovm import environment
from ovm.disturbancefinder import DisturbanceFinder

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

    # Load environment
    environment = environment.load_environment('environment.json')

    # Find all disturbances
    user = 'John Doe'
    now = datetime.now()
    disturbance_finder: DisturbanceFinder = DisturbanceFinder(environment)
    disturbances = disturbance_finder.find_disturbances(begin=now - timedelta(hours=24),
                                                        end=now,
                                                        zoomlevel=args.zoomlevel,
                                                        plot=args.plot,
                                                        title=user,
                                                        origin=(52.311502, 4.827680),  # Amsterdamse Bos
                                                        radius=1000,
                                                        altitude=1000,
                                                        occurrences=4,
                                                        timeframe=60)
    elapsed = datetime.now() - now
    logging.info('Operation took %f seconds' % elapsed.seconds)

    # Write plots to disk
    if args.plot:
        for found_disturbance in disturbances:
            with open('%s_%s.jpg' % (user, found_disturbance.begin), 'wb') as fh:
                fh.write(base64.decodebytes(bytes(found_disturbance.img, "utf-8")))
                fh.close()

    # Exit gracefully
    exit(0)
