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
import json
import os
import subprocess
import tarfile
import threading
import time

from pilot.control.job import send_state

import logging
logger = logging.getLogger(__name__)


def control(queues, traces, args):

    threads = [threading.Thread(target=copytool_in,
                                kwargs={'queues': queues,
                                        'traces': traces,
                                        'args': args}),
               threading.Thread(target=copytool_out,
                                kwargs={'queues': queues,
                                        'traces': traces,
                                        'args': args})]

    [t.start() for t in threads]


def _call(args, executable, cwd=os.getcwd(), logger=logger):
    try:
        process = subprocess.Popen(executable,
                                   bufsize=-1,
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE,
                                   cwd=cwd)
    except Exception as e:
        logger.error('could not execute: %s' % str(e))
        return False

    logger.info('started -- pid=%s executable=%s' % (process.pid, executable))

    exit_code = None
    while exit_code is None and not args.graceful_stop.is_set():
        if args.graceful_stop.wait(timeout=1):
            logger.debug('breaking: sending SIGTERM pid=%s' % process.pid)
            process.terminate()
            logger.debug('breaking: sleep 3s before sending SIGKILL pid=%s' % process.pid)
            time.sleep(3)
            process.kill()
        else:
            exit_code = process.poll()

    logger.info('finished -- pid=%s exit_code=%s' % (process.pid, exit_code))
    stdout, stderr = process.communicate()
    logger.debug('stdout:\n%s' % stdout)
    logger.debug('stderr:\n%s' % stderr)

    if exit_code == 0:
        return True
    else:
        return False


def _stage_in(args, job):
    log = logger.getChild(str(job['PandaID']))

    os.environ['RUCIO_LOGGING_FORMAT'] = '{0}%(asctime)s %(levelname)s [%(message)s]'

    executable = ['/usr/bin/env',
                  'rucio', '-v', 'download',
                  '--no-subdir',
                  '--rse', job['ddmEndPointIn'],
                  '%s:%s' % (job['scopeIn'], job['inFiles'])]

    if not _call(args,
                 executable,
                 cwd=job['working_dir'],
                 logger=log):
        return False
    return True


def copytool_in(queues, traces, args):

    while not args.graceful_stop.is_set():
        try:
            job = queues.data_in.get(block=True, timeout=1)

            send_state(job, 'transferring')

            if _stage_in(args, job):
                queues.finished_data_in.put(job)
            else:
                queues.failed_data_in.put(job)

        except Queue.Empty:
            continue


def copytool_out(queues, traces, args):

    while not args.graceful_stop.is_set():
        try:
            job = queues.data_out.get(block=True, timeout=1)

            logger.info('dataset=%s rse=%s' % (job['destinationDblock'], job['ddmEndPointOut'].split(',')[0]))

            send_state(job, 'transferring')

            if _stage_out_all(job, args):
                queues.finished_data_out.put(job)
            else:
                queues.failed_data_out.put(job)

        except Queue.Empty:
            continue


def prepare_log(job, tarball_name):
    log = logger.getChild(str(job['PandaID']))
    log.info('preparing log file')

    input_files = job['inFiles'].split(',')
    output_files = job['outFiles'].split(',')
    force_exclude = ['geomDB', 'sqlite200']

    with tarfile.open(name=os.path.join(job['working_dir'], job['logFile']),
                      mode='w:gz',
                      dereference=True) as log_tar:
        for _file in list(set(os.listdir(job['working_dir'])) - set(input_files) - set(output_files) - set(force_exclude)):
            logging.debug('adding to log: %s' % _file)
            log_tar.add(os.path.join(job['working_dir'], _file),
                        arcname=os.path.join(tarball_name, _file))

    return {'scope': job['scopeLog'],
            'name': job['logFile'],
            'guid': job['logGUID'],
            'bytes': os.stat(os.path.join(job['working_dir'], job['logFile'])).st_size}


def _stage_out(args, outfile, job):
    log = logger.getChild(str(job['PandaID']))

    os.environ['RUCIO_LOGGING_FORMAT'] = '{0}%(asctime)s %(levelname)s [%(message)s]'
    executable = ['/usr/bin/env',
                  'rucio', '-v', 'upload',
                  '--summary', '--no-register',
                  '--guid', outfile['guid'],
                  '--rse', job['ddmEndPointOut'].split(',')[0],
                  '--scope', outfile['scope'],
                  outfile['name']]

    if not _call(args,
                 executable,
                 cwd=job['working_dir'],
                 logger=log):
        return None 

    summary = None
    with open(os.path.join(job['working_dir'], 'rucio_upload.json'), 'rb') as summary_file:
        summary = json.load(summary_file)

    return summary


def _stage_out_all(job, args):

    outputs = {}

    for f in job['job_report']['files']['output']:
        outputs[f['subFiles'][0]['name']] = {'scope': job['scopeOut'],
                                             'name': f['subFiles'][0]['name'],
                                             'guid': f['subFiles'][0]['file_guid'],
                                             'bytes': f['subFiles'][0]['file_size']}

    outputs['%s:%s' % (job['scopeLog'], job['logFile'])] = prepare_log(job, 'tarball_PandaJob_%s_%s' % (job['PandaID'], args.queue))

    pfc = '''<?xml version="1.0" encoding="UTF-8" standalone="no" ?>
<!DOCTYPE POOLFILECATALOG SYSTEM "InMemory">
<POOLFILECATALOG>'''

    pfc_file = '''
 <File ID="{guid}">
  <logical>
   <lfn name="{name}"/>
  </logical>
  <metadata att_name="surl" att_value="{pfn}"/>
  <metadata att_name="fsize" att_value="{bytes}"/>
  <metadata att_name="adler32" att_value="{adler32}"/>
 </File>
'''

    failed = False

    for outfile in outputs:
        summary = _stage_out(args, outputs[outfile], job)

        if summary is not None:
            outputs[outfile]['pfn'] = summary['%s:%s' % (outputs[outfile]['scope'], outputs[outfile]['name'])]['pfn']
            outputs[outfile]['adler32'] = summary['%s:%s' % (outputs[outfile]['scope'], outputs[outfile]['name'])]['adler32']

            pfc += pfc_file.format(**outputs[outfile])

        else:
            failed = True

    pfc += '</POOLFILECATALOG>'

    if failed:
        send_state(job, 'failed')
        return False
    else:
        send_state(job, 'finished', xml=pfc)
        return True
