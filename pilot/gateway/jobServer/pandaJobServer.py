#!/usr/bin/env python
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# http://www.apache.org/licenses/LICENSE-2.0
#
# Authors:
# - Wen Guan, wen.guan@cern.ch, 2017

"""
A default interface to talk to panda server to get jobs, update status
"""


import traceback

from pilot.exceptions import exception
from pilot.gateway.jobServer.defaultJobServer import DefaultJobServer


class PandaJobServer(DefaultJobServer):
    def __init__(self):
        pass

    def get_jobs(self, data):
        """
        Get job from the job server.

        param data: Dictionary for retrieving jobs
        returns: List of jobs.
        exception: Fail to get a job or jobs
        """

        raise exception.NotImplemented(traceback.format_exc())

    def update_job(self, data):
        """
        Update job to the job server.

        param data: Dictionary for updating a job
        exception: Fail to update a job
        """

        raise exception.NotImplemented(traceback.format_exc())

    def get_event_ranges(self, data):
        """
        Get event ranges from the job server.

        param data: Dictionary for retrieving event ranges
        returns: List of event ranges
        exception: Fail to get event ranges
        """

        raise exception.NotImplemented(traceback.format_exc())

    def update_event_ranges(self, data):
        """
        Update event ranges to the job server.

        param data: Dictionary for updating event ranges
        exception: Fail to update event ranges
        """

        raise exception.NotImplemented(traceback.format_exc())
