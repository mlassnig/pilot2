#!/usr/bin/env python
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# http://www.apache.org/licenses/LICENSE-2.0
#
# Authors:
# - Mario Lassnig, mario.lassnig@cern.ch, 2016-2017
# - Daniel Drizhuk, d.drizhuk@gmail.com, 2017

import Queue
import os
import threading
import urllib

from pilot.util import https

import logging
logger = logging.getLogger(__name__)


def control(queues, traces, args):

    threads = [threading.Thread(target=validate,
                                kwargs={'queues': queues,
                                        'traces': traces,
                                        'args': args}),
               threading.Thread(target=retrieve,
                                kwargs={'queues': queues,
                                        'traces': traces,
                                        'args': args}),
               threading.Thread(target=create_data_payload,
                                kwargs={'queues': queues,
                                        'traces': traces,
                                        'args': args})]

    [t.start() for t in threads]


def _validate_job(job):
    # valid = random.uniform(0, 100)
    # if valid > 99:
    #     logger.warning('%s: job did not validate correctly -- skipping' % job['PandaID'])
    #     job['errno'] = random.randint(0, 100)
    #     job['errmsg'] = 'job failed random validation'
    #     return False
    return True


def send_state(job, state, xml=None):
    log = logger.getChild(str(job['PandaID']))
    log.debug('set job state=%s' % state)

    data = {'jobId': job['PandaID'],
            'state': state}

    if xml is not None:
        data['xml'] = urllib.quote_plus(xml)

    try:
        if https.request('https://pandaserver.cern.ch:25443/server/panda/updateJob', data=data) is not None:
            log.info('confirmed job state=%s' % state)
            return True
    except Exception as e:
        log.warning('while setting job state, Exception caught: %s' % str(e.message))
        pass

    log.warning('set job state=%s failed' % state)
    return False


def validate(queues, traces, args):

    while not args.graceful_stop.is_set():
        try:
            job = queues.jobs.get(block=True, timeout=1)
        except Queue.Empty:
            continue
        log = logger.getChild(str(job['PandaID']))

        traces.pilot['nr_jobs'] += 1

        if _validate_job(job):

            log.debug('creating job working directory')
            job_dir = 'job-%s' % job['PandaID']
            try:
                os.mkdir(job_dir)
                job['working_dir'] = job_dir
            except Exception as e:
                log.debug('cannot create job working directory: %s' % str(e))
                queues.failed_jobs.put(job)
                break

            log.debug('symlinking pilot log')
            try:
                os.symlink('../pilotlog.txt', os.path.join(job_dir, 'pilotlog.txt'))
            except Exception as e:
                log.debug('cannot symlink pilot log: %s' % str(e))
                queues.failed_jobs.put(job)
                break

            queues.validated_jobs.put(job)
        else:
            queues.failed_jobs.put(job)


def create_data_payload(queues, traces, args):

    while not args.graceful_stop.is_set():
        try:
            job = queues.validated_jobs.get(block=True, timeout=1)
        except Queue.Empty:
            continue

        queues.data_in.put(job)
        queues.payloads.put(job)


def retrieve(queues, traces, args):

    while not args.graceful_stop.is_set():

        logger.debug('trying to fetch job')

        data = {'siteName': args.location.queue,
                'prodSourceLabel': args.job_label}

        res = https.request('https://pandaserver.cern.ch:25443/server/panda/getJob', data=data)

        if res is None:
            logger.warning('did not get a job -- sleep 1000s and repeat')
            args.graceful_stop.wait(timeout=1000)
        else:
            if res['StatusCode'] != 0:
                logger.warning('did not get a job -- sleep 1000s and repeat -- status: %s' % res['StatusCode'])
                args.graceful_stop.wait(timeout=1000)
            else:
                logger.info('got job: %s -- sleep 1000s before trying to get another job' % res['PandaID'])
                queues.jobs.put(res)
                args.graceful_stop.wait(timeout=1000)
