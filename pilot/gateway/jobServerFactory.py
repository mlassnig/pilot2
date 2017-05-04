#!/usr/bin/env python
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# http://www.apache.org/licenses/LICENSE-2.0
#
# Authors:
# - Wen Guan, wen.guan@cern.ch, 2017

"""
A factory to generate instance to talk with different job server,
such as Panda, aCT, harverter
"""

import traceback

from pilot.exceptions import exception

import logging
logger = logging.getLogger(__name__)


class JobServerFactory(object):
    def __init__(self):
        pass

    def create_job_server(self, options={'jobserver': 'pandaJobServer.PandaJobServer'}):
        if 'jobserver' in options:
            jobserver = options['jobserver']
        jobserver = 'pilot.gateway.%s' % jobserver

        logger.info("Importing job server %s" % jobserver)
        try:
            components = jobserver.split('.')
            mod = __import__('.'.join(components[:-1]))
            for comp in components[1:]:
                mod = getattr(mod, comp)
            server = mod(options)
            return server
        except Exception:
            raise exception.NotImplemented(traceback.format_exc())
