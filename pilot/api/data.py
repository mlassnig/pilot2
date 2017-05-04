#!/usr/bin/env python
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# http://www.apache.org/licenses/LICENSE-2.0
#
# Authors:
# - Mario Lassnig, mario.lassnig@cern.ch, 2017
# - Wen Guan, wen.guan@cern.ch, 2017

import os

from pilot.control import data


class TransferRequest(object):
    """
    Transfer request to handle files stagein/stageout
    """

    _attrs = ['type']  # stagein, stageout, ...
    _attrs += ['scope', 'name', 'guid', 'filesize', 'checksum']  # file info
    _attrs += ['dataset', 'ddmendpoint', 'jobqueue']
    _attrs += ['objectstoreId']  # special for ES
    _attrs += ['allowRemoteInputs']  # control options
    _attrs += ['status', 'destPfn']  # transfer result

    def __init__(self, **kwargs):
        for k in self._attrs:
            setattr(self, k, kwargs.get(k, getattr(self, k, None)))


class StageInClient(object):

    def __init__(self, site=None):
        super(StageInClient, self).__init__()

        # Check validity of specified site
        self.site = os.environ.get('VO_ATLAS_AGIS_SITE', site)
        if self.site is None:
            raise Exception('VO_ATLAS_AGIS_SITE not available, must set StageInClient(site=...) parameter')

        # Retrieve location information
        # will need this later -- don't spam AGIS for now
        # from pilot.util import information
        # self.args = collections.namedtuple('args', ['location'])
        # information.set_location(self.args, site=self.site)

    def transfer(self, files):
        """
        Automatically stage in files using rucio.

        :param files: List of dictionaries containing the DID and destination directory [{scope, name, destination
        :return: Annotated files -- List of dictionaries with additional variables [{..., errno, errmsg, status
        """

        all_files_ok = False
        for file in files:
            if all(key in file for key in ('scope', 'name', 'destination')):
                all_files_ok = True

        if all_files_ok:
            return data.stage_in_auto(self.site, files)
        else:
            raise Exception('Files dictionary does not conform: scope, name, destination')


class StageInClientAsync(object):

    def __init__(self, site):
        raise NotImplementedError

    def queue(self, files):
        raise NotImplementedError

    def is_transferring(self):
        raise NotImplementedError

    def start(self):
        raise NotImplementedError

    def finish(self):
        raise NotImplementedError

    def status(self):
        raise NotImplementedError
