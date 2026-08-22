#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# USAGE: MSG3-NWCSAF-eurol.py YYYYmmddHHMM
# NWC-SAF products (CT, CMA, CTTH) from MSG3 | Area: eurol
# Reader: nwcsaf-geo | Segdir: /home/sps/received/bas/E1B-GEO-4
# Products: cloudtype, cloudmask, cloud_top_height
# License GPL3 (c) Ernst Lobsiger / INGV adaptation

import os, sys, platform
from GEOstuff import test_argv, geo_images, get_magick

OS = platform.system()
sat, Dat, Yea, Mon, Day, Hou, Min = test_argv()
sat = 'MSG3'  # E1B-GEO-4 contains MSG3 NWC-SAF files (S_NWC_*_MSG3_*)

# ----------------------------------------------------------------
segdir  = '/home/sps/received/bas/E1B-GEO-4'
isbulk  = True
decomp  = False

composites  = ['cloudtype', 'cloudmask', 'cloud_top_height']
area        = 'eurol'
area_cities = []

ADDcoasts  = True
ADDborders = True
ADDrivers  = False
ADDlakes   = False
ADDgrid    = False
ADDcities  = False
ADDpoints  = False
ADDstation = False
ADDlegend  = True
GEOcache   = True
OVRcache   = True
testrun    = False
# ----------------------------------------------------------------

sensor   = 'seviri'
service  = 'Basic'
channel  = 'E1B-GEO-4'
logo1    = 'eumetsat_200x199.png'
logo2    = 'PyTROLL_400x400.jpg'
receiver = 'TBS-6909X'

height = geo_images(Yea, Mon, Day, Hou, Min, sat, segdir, decomp, isbulk,
                    'nwcsaf-geo', composites, area, area_cities,
                    ADDcoasts, ADDborders, ADDrivers, ADDlakes,
                    ADDgrid, ADDcities, ADDpoints, ADDstation,
                    GEOcache, OVRcache, testrun)

for composite in composites:
    magick = get_magick(Yea, Mon, Day, Hou, Min, height, logo1, logo2, service, channel,
                        receiver, sat, sensor, composite, area, testrun, ADDlegend)
    os.system(magick)
