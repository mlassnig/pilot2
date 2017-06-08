#!/usr/bin/env python
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# http://www.apache.org/licenses/LICENSE-2.0
#
# Authors:
# - Wen Guan, wen.guan@cern.ch, 2017

"""
A manager to manage comunications with different job server,
such as Panda, aCT, harverter
"""

import traceback

from pilot.exceptions import exception

import logging
logger = logging.getLogger(__name__)


class JobServerManager(object):

    def __new__(cls, *args, **kwargs):
        """
        Override the __new__ method to make the class a singleton
        """

        if not cls.__instance:
            cls.__instance = super(JobServerManager, cls).__new__(cls, *args, **kwargs)
            cls.__instance.create_job_server(*args, **kwargs)

        return cls.__instance

    def get_job_server(self, options={'jobserver': 'pandaJobServer.PandaJobServer'}):
        # default job server
        jobserver = 'pandaJobServer.PandaJobServer'

        if 'jobserver' in options:
            jobserver = options['jobserver']
        else:
            if 'type' in options:
                if options['type'] == 'panda':
                    jobserver = 'pandaJobServer.PandaJobServer'
                if options['type'] == 'act':
                    jobserver = 'aCTJobServer.ACTJobServer'
                if options['type'] == 'harvester':
                    jobserver = 'harverterJobServer.HarverterJobServer'

        jobserver = 'pilot.gateway.jobserver.%s' % jobserver
        return jobserver

    def create_job_server(self, options):
        jobserver = self.get_job_server(options)

        logger.info("Importing job server %s" % jobserver)
        try:
            components = jobserver.split('.')
            mod = __import__('.'.join(components[:-1]))
            for comp in components[1:]:
                mod = getattr(mod, comp)
            self._server = mod(options)
        except Exception:
            raise exception.NotImplemented(traceback.format_exc())

    def get_jobs(self, data):
        """
        Get job from the job server.

        param data: Dictionary for retrieving jobs
        returns: List of jobs.
        exception: Fail to get a job or jobs
        """
        return self._server.get_jobs(data)

    def update_jobs(self, data):
        """
        Update jobs to the job server.

        param data: List of dictionaries for updating a job
        exception: Fail to update jobs
        """
        self._server.update_jobs(data)

    def get_event_ranges(self, data):
        """
        Get event ranges from the job server.

        param data: Dictionary for retrieving event ranges
        returns: List of event ranges
        exception: Fail to get event ranges
        """
        self._server.get_event_ranges(data)

    def update_event_ranges(self, data):
        """
        Update event ranges to the job server.

        param data: Dictionary for updating event ranges
        exception: Fail to update event ranges
        """
        self._server.update_event_ranges(data)
