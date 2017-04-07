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
import commands
import json
import os
import shlex
import subprocess
import threading
import time

from pilot.control.job import send_state

import logging
logger = logging.getLogger(__name__)


def control(queues, traces, args):

    threads = [threading.Thread(target=validate_pre,
                                kwargs={'queues': queues,
                                        'traces': traces,
                                        'args': args}),
               threading.Thread(target=execute,
                                kwargs={'queues': queues,
                                        'traces': traces,
                                        'args': args}),
               threading.Thread(target=validate_post,
                                kwargs={'queues': queues,
                                        'traces': traces,
                                        'args': args})]

    [t.start() for t in threads]


def validate_pre(queues, traces, args):

    while not args.graceful_stop.is_set():
        try:
            job = queues.payloads.get(block=True, timeout=1)
        except Queue.Empty:
            continue

        if _validate_payload(job):
            queues.validated_payloads.put(job)
        else:
            queues.failed_payloads.put(job)


def _validate_payload(job):
    # valid = random.uniform(0, 100)
    # if valid > 99:
    #     logger.warning('payload did not validate correctly -- skipping')
    #     job['errno'] = random.randint(0, 100)
    #     job['errmsg'] = 'payload failed random validation'
    #     return False
    return True


def setup_payload(job, out, err):
    log = logger.getChild(str(job['PandaID']))

    executable = 'cd job-%s; '\
                 'ln -sf /cvmfs/atlas.cern.ch/repo/sw/database/DBRelease/current/sqlite200 sqlite200; '\
                 'ln -sf /cvmfs/atlas.cern.ch/repo/sw/database/DBRelease/current/geomDB geomDB; '\
                 'source $ATLAS_LOCAL_ROOT_BASE/user/atlasLocalSetup.sh --quiet; '\
                 'source $AtlasSetup/scripts/asetup.sh %s,here; cd ..' % (job['PandaID'],
                                                                          job['homepackage'].split('/')[1])

    log.debug('executable=%s' % executable)

    try:
        s, o = commands.getstatusoutput(executable)
    except Exception as e:
        log.error('could not setup environment: %s' % e)
        return False

    if s != 0:
        log.error('could not setup environment: %s' % o)
        return False

    return True


def run_payload(job, out, err):
    log = logger.getChild(str(job['PandaID']))

    executable = ['/usr/bin/env', job['transformation']] + shlex.split(job['jobPars'])
    log.debug('executable=%s' % executable)

    try:
        proc = subprocess.Popen(executable,
                                bufsize=-1,
                                stdout=out,
                                stderr=err,
                                cwd=job['working_dir'])
    except Exception as e:
        log.error('could not execute: %s' % str(e))
        return None

    log.info('started -- pid=%s executable=%s' % (proc.pid, executable))

    return proc


def wait_graceful(args, proc, job):
    log = logger.getChild(str(job['PandaID']))

    exit_code = None
    while exit_code is None and not args.graceful_stop.is_set():
        if args.graceful_stop.wait(timeout=10):
            log.debug('breaking -- sending SIGTERM pid=%s' % proc.pid)
            proc.terminate()
            log.debug('breaking -- sleep 3s before sending SIGKILL pid=%s' % proc.pid)
            time.sleep(3)
            proc.kill()
        else:
            exit_code = proc.poll()
            log.info('running: pid=%s exit_code=%s' % (proc.pid, exit_code))
            if exit_code is None:
                send_state(job, 'running')

    return exit_code


def execute(queues, traces, args):

    while not args.graceful_stop.is_set():
        try:
            job = queues.validated_payloads.get(block=True, timeout=1)
            log = logger.getChild(str(job['PandaID']))

            q_snapshot = list(queues.finished_data_in.queue)
            peek = [s_job for s_job in q_snapshot if job['PandaID'] == s_job['PandaID']]
            if len(peek) == 0:
                queues.validated_payloads.put(job)
                args.graceful_stop.wait(timeout=1)
                continue

            log.debug('opening payload stdout/err logs')
            out = open(os.path.join(job['working_dir'], 'payload.stdout'), 'wb')
            err = open(os.path.join(job['working_dir'], 'payload.stderr'), 'wb')

            log.debug('setting up payload environment')
            send_state(job, 'starting')

            exit_code = 1
            if setup_payload(job, out, err):
                log.debug('running payload')
                send_state(job, 'running')
                proc = run_payload(job, out, err)
                if proc is not None:
                    exit_code = wait_graceful(args, proc, job)
                    log.info('finished pid=%s exit_code=%s' % (proc.pid, exit_code))

            log.debug('closing payload stdout/err logs')
            out.close()
            err.close()

            if exit_code == 0:
                queues.finished_payloads.put(job)
            else:
                queues.failed_payloads.put(job)

        except Queue.Empty:
            continue


def validate_post(queues, traces, args):

    while not args.graceful_stop.is_set():
        try:
            job = queues.finished_payloads.get(block=True, timeout=1)
        except Queue.Empty:
            continue
        log = logger.getChild(str(job['PandaID']))

        log.debug('adding job report for stageout')
        with open(os.path.join(job['working_dir'], 'jobReport.json')) as data_file:
            job['job_report'] = json.load(data_file)

        queues.data_out.put(job)
