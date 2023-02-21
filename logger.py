#!/usr/bin/env python3
import json
import time
import logging
import argparse

from numpy import uint64

from ovm.planelogger import PlaneLogger, PlotOptions

if __name__ == '__main__':
    # parse cli arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('-b', '--bbox',
                        type=float,
                        nargs=4,
                        default=[49.44, 54.16, 2.82, 7.02],
                        help='Bounding Box [lat_min, lat_max, lon_min, lon_max]')
    parser.add_argument('-l', '--loglevel',
                        type=str.upper,
                        default='INFO',
                        help='LOG Level (DEBUG, INFO, WARNING, ERROR, CRITICAL)')
    parser.add_argument('-p', '--plot',
                        action=argparse.BooleanOptionalAction,
                        help='Creates a plot for each run')
    parser.add_argument('-o', '--outputfilename',
                        type=str,
                        default='traffic',
                        help='Plot base output filename, run number and png extension gets appended')
    parser.add_argument('-z', '--zoomlevel',
                        type=int,
                        default=10)
    parser.add_argument('-i', '--interval',
                        type=float,
                        default=22.5,
                        help='Time between runs')
    parser.add_argument('-r', '--runs',
                        type=int,
                        default=0,
                        help='Amount of runs between intervals, default = 0 meaning infinite')
    args = parser.parse_args()

    # Set log level
    logging.basicConfig(level=args.loglevel)

    # Read environment config from json
    environment = json.load(open('environment.json'))

    # Create and run plane logger
    plane_logger = PlaneLogger(environment)

    run = True
    runs: uint64 = uint64(0)
    while run:
        sleep_interval = args.interval
        try:
            logging.info('Starting run %i' % runs)

            # Get current time for performance and time measurement
            current_time = time.perf_counter()

            # Run plane logger
            plane_logger.log(bbox=(args.bbox[0], args.bbox[1], args.bbox[2], args.bbox[3]),
                             plot_options=PlotOptions(args.plot,
                                                      args.zoomlevel,
                                                      ('%s%i.png' % (args.outputfilename, runs))))

            time_elapsed = time.perf_counter() - current_time
            sleep_interval = sleep_interval - time_elapsed
            if sleep_interval < 0:
                sleep_interval = 0
            logging.info('PlaneLogger took %f seconds, sleep for %f seconds' % (time_elapsed, sleep_interval))
        except KeyboardInterrupt:
            exit(0)
        except Exception as ex:
            logging.exception(ex.__str__())

        runs += 1
        if args.runs > 0 and runs >= args.runs:
            run = False
            logging.info('%i runs finished, exiting.' % args.runs)
        else:
            time.sleep(sleep_interval)

    exit(0)
