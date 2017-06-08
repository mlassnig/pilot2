#!/usr/bin/env python
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# http://www.apache.org/licenses/LICENSE-2.0
#
# Authors:
# - Wen Guan, wen.guan@cern.ch, 2017

"""
A factory to generate instance to talk with tracer server
"""

import traceback

from pilot.exceptions import exception

import logging
logger = logging.getLogger(__name__)


class TracerFactory(object):
    def __init__(self):
        pass

    def create_tracer(self, options={'tracer': 'rucioTracer.RucioTracer'}):
        if 'tracer' in options:
            tracer = options['tracer']
        tracer = 'pilot.gateway.%s' % tracer

        logger.info("Importing tracer %s" % tracer)
        try:
            components = tracer.split('.')
            mod = __import__('.'.join(components[:-1]))
            for comp in components[1:]:
                mod = getattr(mod, comp)
            tracer = mod(options)
            return tracer
        except Exception:
            raise exception.NotImplemented(traceback.format_exc())
