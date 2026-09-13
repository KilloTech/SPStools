#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# USAGE: MTI1-fci_0deg_2km.py YYYYmmddHHMM
# Satellite MTI-1 (MTG-I1) - Full disk FCI | Europe (eurol1)
# Reader: fci_l1c_nc | Segdir: /home/sps/received/hvs-2/E2H-MTG-1
# License GPL3 (c) Ernst Lobsiger / INGV adaptation

import os, sys, platform
from GEOstuff import test_argv, geo_images, get_magick

OS = platform.system()
sat, Dat, Yea, Mon, Day, Hou, Min = test_argv()

# ----------------------------------------------------------------
segdir  = '/home/sps/received/hvs-2/E2H-MTG-1'
isbulk  = True    # Files flat in channel dir (no YYYY/mm/DD subdirs)
decomp  = False

composites = ['colorized_ir_clouds', 'airmass', 'dust']

areas = ['fci_0deg_2km', 'eurol1']    # full disk + European detail (eurol1: ~0.77km/px vs eurol 3km/px)

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

GEOcache = True
OVRcache = True
testrun  = False
# ----------------------------------------------------------------

sensor   = 'fci'
service  = 'HVS-2'
channel  = 'E2H-MTG-1'
logo1    = 'eumetsat_200x199.png'
logo2    = 'PyTROLL_400x400.jpg'
receiver = 'TBS-6909X'

for area in areas:
    height = geo_images(Yea, Mon, Day, Hou, Min, sat, segdir, decomp, isbulk,
                        'fci_l1c_nc', composites,
                        area, area_cities, ADDcoasts, ADDborders, ADDrivers, ADDlakes,
                        ADDgrid, ADDcities, ADDpoints, ADDstation, GEOcache, OVRcache, testrun)

    for composite in composites:
        magick = get_magick(Yea, Mon, Day, Hou, Min, height, logo1, logo2, service, channel,
                            receiver, sat, sensor, composite, area, testrun, ADDlegend,
                            subdir='frames')
        os.system(magick)
