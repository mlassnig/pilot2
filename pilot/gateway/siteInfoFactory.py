#!/usr/bin/env python
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# http://www.apache.org/licenses/LICENSE-2.0
#
# Authors:
# - Wen Guan, wen.guan@cern.ch, 2017

"""
A factory to generate instance to get site info.
"""

import traceback

from pilot.exceptions import exception

import logging
logger = logging.getLogger(__name__)


class SiteInfoFactory(object):
    def __init__(self):
        pass

    def create_site_info(self, options={'siteinfo': 'agisSiteInfo.AGISSiteInfo'}):
        if 'siteinfo' in options:
            siteinfo = options['siteinfo']
        siteinfo = 'pilot.gateway.siteinfo.%s' % siteinfo

        logger.info("Importing siteinfo %s" % siteinfo)
        try:
            components = siteinfo.split('.')
            mod = __import__('.'.join(components[:-1]))
            for comp in components[1:]:
                mod = getattr(mod, comp)
            siteinfo = mod(options)
            return siteinfo
        except Exception:
            raise exception.NotImplemented(traceback.format_exc())
