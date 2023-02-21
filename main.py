#!/usr/bin/env python3

import logging
import argparse
from planelogger import PlaneLogger, PlotOptions

if __name__ == '__main__':
    # parse cli arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--creds',
                        type=str,
                        nargs=2,
                        required=True,
                        help="Username and password")
    parser.add_argument('-b', '--bbox',
                        type=float,
                        nargs=4,
                        default=[49.44, 54.16, 2.82, 7.02],
                        help="Bounding Box [lat_min, lat_max, lon_min, lon_max]")
    parser.add_argument('-l', '--loglevel',
                        type=str.upper,
                        default='INFO',
                        help="LOG Level (DEBUG, INFO, WARNING, ERROR, CRITICAL)")
    parser.add_argument('-p', '--plot', action=argparse.BooleanOptionalAction)
    parser.add_argument('-z', '--zoomlevel',
                        type=int,
                        default=10)
    parser.add_argument('-i', '--interval',
                        type=float,
                        default=10.5)
    args = parser.parse_args()

    # Set log level
    logging.basicConfig(level=args.loglevel)

    # Create and run plane logger
    plane_logger = PlaneLogger(args.creds[0], args.creds[1])
    exit(plane_logger.run(bbox=(args.bbox[0], args.bbox[1], args.bbox[2], args.bbox[3]),
                          plot_options=PlotOptions(args.plot, args.zoomlevel),
                          interval=args.interval))
