#!/usr/bin/env python
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# http://www.apache.org/licenses/LICENSE-2.0
#
# Authors:
# - Paul Nilsson, paul.nilsson@cern.ch

import subprocess

import logging
logger = logging.getLogger(__name__)

def execute(executable):
    """

    :param executable: Command list to be executed.
    :return: exit code, stdout and stderr
    """

    process = subprocess.Popen(executable,
                               bufsize=-1,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()
    exit_code = process.poll()

    return exit_code, stdout, stderr
