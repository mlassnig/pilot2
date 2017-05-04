#!/usr/bin/env python
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# http://www.apache.org/licenses/LICENSE-2.0
#
# Authors:
# - Wen Guan, wen.guan@cern.ch, 2017

"""
A default interface to send tracer info
"""


import traceback

from pilot.exceptions import exception


class DefaultTracer(object):
    def __init__(self):
        pass

    def send_trace(self, data):
        """
        send trace information.

        param data: Dictionary for updating a job.
        exception: Fail to send trace info.
        """

        raise exception.NotImplemented(traceback.format_exc())
