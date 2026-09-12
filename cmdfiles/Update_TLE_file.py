#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#*************************************************************************
# This script updates the TLE file found in directory toodir + '/satpyetc'
# It should be updated at least once a month in scheduled 24/7 TC systems.
# If you use this manually be sure to activate your (pytroll) environment.
#
# CH-3123 Belp, 2022/11/10        License GPL3          (c) Ernst Lobsiger
# INGV adaptation 2026/09/12: fetch to a temp file first and validate before
# replacing the live TLE file -- a failed/empty fetch (e.g. HTTP 403 from
# the source, rate-limited on repeated calls) used to silently truncate
# my_TLE_file.txt to 0 bytes, breaking every LEO script until the next
# successful weekly run.
#*************************************************************************

import os, sys, shutil, platform, time
from pyorbital import tlefile

OS = platform.system()

if OS == 'Linux':
    toodir = '/home/sps/SPStools'
elif OS == 'Windows':
    toodir = 'C:/SPStools'
else:
    sys.exit('Sorry, OS ' + OS + ' seems unsupported yet ...')

# Use old path name ppp
ppp = toodir + '/userconfig'
live_file = ppp + '/my_TLE_file.txt'
tmp_file  = ppp + '/my_TLE_file.txt.new'
MIN_SATELLITES = 1000  # a healthy fetch has ~16000+; anything far below means a bad/partial download

def count_satellites(path):
    if not os.path.exists(path):
        return 0
    with open(path, 'r', errors='replace') as f:
        return sum(1 for line in f if line.startswith('1 '))

for attempt in range(1, 4):
    try:
        tlefile.fetch(tmp_file)
    except Exception as e:
        print(f'Attempt {attempt}/3: fetch failed: {e}')
        if attempt < 3:
            time.sleep(30)
        continue

    n = count_satellites(tmp_file)
    if n >= MIN_SATELLITES:
        # Good fetch: back up current live file, then replace it
        if os.path.exists(live_file):
            shutil.copy(live_file, ppp + '/backup/old_TLE_file.txt')
        shutil.move(tmp_file, live_file)
        print(f'TLE file updated OK: {n} satellites')
        sys.exit(0)
    else:
        print(f'Attempt {attempt}/3: fetch produced only {n} satellite(s), discarding (need >= {MIN_SATELLITES})')
        if os.path.exists(tmp_file):
            os.remove(tmp_file)
        if attempt < 3:
            time.sleep(30)

print('ERROR: could not obtain a valid TLE file after 3 attempts -- keeping existing my_TLE_file.txt untouched')
sys.exit(1)
