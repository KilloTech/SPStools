#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# USAGE: Sen3B-eurol.py YYYYmmddNoD  (NoD = DAY only, OLCI is daylight only)
# Satellite Sentinel-3B - OLCI L1b ERR | Area: eurol
# Reader: olci_l1b | Segdir: /home/sps/received/hvs-2/E2H-S3B-02
# License GPL3 (c) Ernst Lobsiger / INGV adaptation

import os, sys, platform
from LEOstuff import test_argv, leo_images, get_magick

OS = platform.system()
sat, Dat, Yea, Mon, Day, NoD = test_argv()

# ----------------------------------------------------------------
segdir  = '/home/sps/received/hvs-2/E2H-S3B-02'
isbulk  = True    # Files flat in channel dir (no YYYY/mm/DD subdirs)

if NoD != 'DAY':
    sys.exit('OLCI is a daylight instrument only, exiting.')

composites  = ['true_color', 'ocean_color']
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

sensor   = 'olci'
service  = 'HVS-2'
channel  = 'E2H-S3B-02'
logo1    = 'Copernicus_1050x1050.png'
logo2    = 'PyTROLL_400x400.jpg'
receiver = 'TBS-6909X'

Yea, Mon, Day, Hou, Min, height = leo_images(
    Yea, Mon, Day, sat, NoD, False, segdir, False, isbulk,
    'olci_l1b', composites, area, area_cities,
    ADDcoasts, ADDborders, ADDrivers, ADDlakes,
    ADDgrid, ADDcities, ADDpoints, ADDstation,
    OVRcache, testrun, **kwargs)

for composite in composites:
    magick = get_magick(Yea, Mon, Day, Hou, Min, height, logo1, logo2, service, channel,
                        receiver, sat, sensor, composite, area, testrun, NoD, False, ADDlegend,
                        subdir=NoD)
    os.system(magick)
