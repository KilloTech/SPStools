#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Wrapper cron per s3_archive.py
# Cron: 45 0 * * *  (00:45 UTC — dopo movie generation 00:10, prima di tidy.sh 01:00)

import subprocess, logging

logging.basicConfig(
    filename='/home/sps/SPSdata/cron.log',
    level=logging.INFO,
    format='%(asctime)s %(message)s'
)

logging.info('S3 archive start')
r = subprocess.run(
    ['/home/sps/miniconda3/envs/pytroll/bin/python3',
     '/home/sps/SPStools/cmdfiles/s3_archive.py'],
    capture_output=True, text=True,
)
logging.info(f'S3 archive done rc={r.returncode}')
if r.stdout.strip():
    logging.info(f'S3 stdout: {r.stdout.strip()[-800:]}')
if r.returncode != 0:
    logging.error(f'S3 stderr: {r.stderr[-500:]}')
