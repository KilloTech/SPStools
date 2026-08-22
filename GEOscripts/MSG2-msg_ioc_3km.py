#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# USAGE: MSG2-msg_ioc_3km.py YYYYmmddHHMM
# Satellite MSG2 - Full disk | Europe (eurol) - INGV/SPS adapted
# Reader: seviri_l1b_hrit | Segdir: /home/sps/received/bas/E1B-GEO-1
# License GPL3 (c) Ernst Lobsiger / INGV adaptation

import os, sys, platform
from GEOstuff import test_argv, geo_images, get_magick

OS = platform.system()
sat, Dat, Yea, Mon, Day, Hou, Min = test_argv()

# ----------------------------------------------------------------
segdir  = '/home/sps/received/bas/E1B-GEO-1'
isbulk  = True    # Files flat in channel dir (no YYYY/mm/DD subdirs)
decomp  = False

composites = ['airmass', 'colorized_ir_clouds', 'overview', 'dust']

areas = ['msg_ioc_3km']    # full disk + European detail

area_cities = []
ADDcoasts  = True
ADDborders = True
ADDrivers  = False   # rivers disabled
ADDlakes   = False   # lakes disabled
ADDgrid    = False
ADDcities  = False
ADDpoints  = False
ADDstation = False
ADDlegend  = True

GEOcache = True
OVRcache = True
testrun  = False
# ----------------------------------------------------------------

sensor   = 'seviri'
service  = 'Basic'
channel  = 'E1B-GEO-1'
logo1    = 'eumetsat_200x199.png'
logo2    = 'PyTROLL_400x400.jpg'
receiver = 'TBS-6909X'

for area in areas:
    height = geo_images(Yea, Mon, Day, Hou, Min, sat, segdir, decomp, isbulk,
                        'seviri_l1b_hrit', composites,
                        area, area_cities, ADDcoasts, ADDborders, ADDrivers, ADDlakes,
                        ADDgrid, ADDcities, ADDpoints, ADDstation, GEOcache, OVRcache, testrun)

    for composite in composites:
        magick = get_magick(Yea, Mon, Day, Hou, Min, height, logo1, logo2, service, channel,
                            receiver, sat, sensor, composite, area, testrun, ADDlegend,
                            subdir='frames')
        os.system(magick)
