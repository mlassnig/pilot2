#!/usr/bin/env python
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# http://www.apache.org/licenses/LICENSE-2.0
#
# Authors:
# - Mario Lassnig, mario.lassnig@cern.ch, 2016-2017
# - Daniel Drizhuk, d.drizhuk@gmail.com, 2017

import argparse
import logging
import sys
import threading

from pilot.util.constants import SUCCESS, FAILURE, ERRNO_NOJOBS
from pilot.util.https import https_setup
from pilot.util.information import set_location

VERSION = '2017-04-04.001'


def main():
    logger = logging.getLogger(__name__)
    logger.info('pilot startup - version %s' % VERSION)

    args.graceful_stop = threading.Event()

    https_setup(args, VERSION)

    if not set_location(args):
        return False

    logger.info('workflow: %s' % args.workflow)
    workflow = __import__('pilot.workflow.%s' % args.workflow, globals(), locals(), [args.workflow], -1)
    return workflow.run(args)


if __name__ == '__main__':
    arg_parser = argparse.ArgumentParser()

    arg_parser.add_argument('-d',
                            dest='debug',
                            action='store_true',
                            default=False,
                            help='enable debug logging messages')

    # the choices must match in name the python module in pilot/workflow/
    arg_parser.add_argument('-w',
                            dest='workflow',
                            default='generic',
                            choices=['generic', 'generic_hpc',
                                     'production', 'production_hpc',
                                     'analysis', 'analysis_hpc',
                                     'eventservice', 'eventservice_hpc'],
                            help='pilot workflow (default: generic)')

    # graciously stop pilot process after hard limit
    arg_parser.add_argument('-l',
                            dest='lifetime',
                            default=10,
                            type=int,
                            help='pilot lifetime seconds (default: 10)')

    # set the appropriate site and queue
    arg_parser.add_argument('-q',
                            dest='queue',
                            required=True,
                            help='MANDATORY: queue name (e.g., AGLT2_TEST-condor')

    # ask panda for jobs only with the given prod/source label
    arg_parser.add_argument('-j',
                            dest='job_label',
                            default='mtest',
                            help='job prod/source label (default: mtest)')

    # SSL certificates
    arg_parser.add_argument('--cacert',
                            dest='cacert',
                            default=None,
                            help='CA certificate to use with HTTPS calls to server, commonly X509 proxy',
                            metavar='path/to/your/certificate')
    arg_parser.add_argument('--capath',
                            dest='capath',
                            default=None,
                            help='CA certificates path',
                            metavar='path/to/certificates/')

    args = arg_parser.parse_args()

    console = logging.StreamHandler(sys.stdout)
    if args.debug:
        logging.basicConfig(filename='pilotlog.txt', level=logging.DEBUG,
                            format='%(asctime)s | %(levelname)-8s | %(threadName)-10s | %(name)-32s | %(funcName)-32s | %(message)s')
        console.setLevel(logging.DEBUG)
        console.setFormatter(logging.Formatter('%(asctime)s | %(levelname)-8s | %(threadName)-10s | %(name)-32s | %(funcName)-32s | %(message)s'))
    else:
        logging.basicConfig(filename='pilotlog.txt', level=logging.INFO,
                            format='%(asctime)s | %(levelname)-8s | %(message)s')
        console.setLevel(logging.INFO)
        console.setFormatter(logging.Formatter('%(asctime)s | %(levelname)-8s | %(message)s'))
    logging.getLogger('').addHandler(console)

    trace = main()
    logging.shutdown()

    if not trace:
        logging.getLogger(__name__).critical('pilot startup did not succeed -- aborting')
        sys.exit(FAILURE)
    elif trace.pilot['nr_jobs'] > 0:
        sys.exit(SUCCESS)
    else:
        sys.exit(ERRNO_NOJOBS)
