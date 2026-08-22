#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# USAGE: MetopC-eurol.py YYYYmmddNoD  (NoD = DAY or NIG)
# Satellite MetOp-C (M03) - AVHRR | Area: eurol
# Reader: avhrr_l1b_eps | Segdir: /home/sps/received/bas/E1B-EPS-10
# License GPL3 (c) Ernst Lobsiger / INGV adaptation

import os, sys, platform
from LEOstuff import test_argv, leo_images, get_magick

OS = platform.system()
sat, Dat, Yea, Mon, Day, NoD = test_argv()

# ----------------------------------------------------------------
segdir  = '/home/sps/received/bas/E1B-EPS-10'
isbulk  = True    # Files flat in channel dir (no YYYY/mm/DD subdirs)
decomp  = False
multi   = True    # Multiple passes per day for eurol

if NoD == 'DAY':
    composites = ['natural_color', 'overview', 'cloudtop']
else:   # NIG
    composites = ['night_fog', 'cloudtop']

area        = 'eurol'
area_cities = []
kwargs      = {}

ADDcoasts  = True
ADDborders = True
ADDrivers  = False
ADDlakes   = False
ADDgrid    = False
ADDcities  = False
ADDpoints  = False
ADDstation = False
ADDlegend  = True
OVRcache   = True
testrun    = False
# ----------------------------------------------------------------

sensor   = 'avhrr'
service  = 'Basic'
channel  = 'E1B-EPS-10'
logo1    = 'eumetsat_200x199.png'
logo2    = 'PyTROLL_400x400.jpg'
receiver = 'TBS-6909X'

Yea, Mon, Day, Hou, Min, height = leo_images(
    Yea, Mon, Day, sat, NoD, multi, segdir, decomp, isbulk,
    'avhrr_l1b_eps', composites, area, area_cities,
    ADDcoasts, ADDborders, ADDrivers, ADDlakes,
    ADDgrid, ADDcities, ADDpoints, ADDstation,
    OVRcache, testrun, **kwargs)

for composite in composites:
    magick = get_magick(Yea, Mon, Day, Hou, Min, height, logo1, logo2, service, channel,
                        receiver, sat, sensor, composite, area, testrun, NoD, multi, ADDlegend,
                        subdir=NoD)
    os.system(magick)
