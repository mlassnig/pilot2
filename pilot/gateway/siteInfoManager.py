#!/usr/bin/env python
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# http://www.apache.org/licenses/LICENSE-2.0
#
# Authors:
# - Wen Guan, wen.guan@cern.ch, 2017

"""
A manager to manage site info.
"""

import traceback

from pilot.exceptions import exception

import logging
logger = logging.getLogger(__name__)


class QueueInfo(object):
    """
    An object about job queue info.
    """

    _attrs = ['queue', 'site', 'cvmfs', 'tmpdir', 'wntmpdir']
    _attrs += ['maxinputsize', 'maxmemory', 'maxrss', 'maxswap', 'maxtime', 'maxwdir', 'timefloor']

    def __init__(self, **kwargs):
        for k in self._attrs:
            setattr(self, k, kwargs.get(k, getattr(self, k, None)))


class StorageInfo(object):
    """
    An object about storage info.
    """

    _attrs = ['type']
    _attrs += ['ddmendpoints', 'objectstoreid', 'se', 'sepath']
    _attrs += ['isdirectio', 'allowRemoteInputs']

    def __init__(self, **kwargs):
        for k in self._attrs:
            setattr(self, k, kwargs.get(k, getattr(self, k, None)))


class SiteInfoManager(object):

    def __new__(cls, *args, **kwargs):
        """
        Override the __new__ method to make the class a singleton
        """

        if not cls.__instance:
            cls.__instance = super(SiteInfoManager, cls).__new__(cls, *args, **kwargs)
            cls.__instance.create_site_info(*args, **kwargs)

        return cls.__instance

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
            self._siteinfo = mod(options)
        except Exception:
            raise exception.NotImplemented(traceback.format_exc())

    def get_queue_info(self, queuename):
        """
        Get job queue info.

        :param queuename: queue name.
        :returns: QueueInfo object.
        """

        return QueueInfo()

    def get_storage_info(self, queuename, type='stagein'):
        """
        Get storage info for stagein and stageout, or eventservice.

        :param queuename: queue name.
        :param type: type of 'stagein', 'stageout', 'es_stagein', 'es_stageout'
        :returns: StorageInfo object.
        """

        return StorageInfo()
