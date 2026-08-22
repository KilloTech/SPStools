#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# USAGE: HIMA8-hima_f_2km.py YYYYmmddHHMM
# Satellite HIMA8 - Full disk | Europe (eurol) - INGV/SPS adapted
# Reader: ahi_hsd | Segdir: /home/sps/received/hvs-1/E1H-TPG-2
# License GPL3 (c) Ernst Lobsiger / INGV adaptation

import os, sys, platform
from GEOstuff import test_argv, geo_images, get_magick

OS = platform.system()
sat, Dat, Yea, Mon, Day, Hou, Min = test_argv()

# ----------------------------------------------------------------
segdir  = '/home/sps/received/hvs-1/E1H-TPG-2'
isbulk  = True    # Files flat in channel dir (no YYYY/mm/DD subdirs)
decomp  = False

composites = ['colorized_ir_clouds', 'natural_color', 'overview']  # true_color rimosso (rayleigh_corrected non funziona con HRIT)

areas = ['hima_f_2km']    # full disk + European detail

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

sensor   = 'ahi'
service  = 'HVS-1'
channel  = 'E1H-TPG-2'
logo1    = 'JMA_947x969.gif'
logo2    = 'PyTROLL_400x400.jpg'
receiver = 'TBS-6909X'

for area in areas:
    height = geo_images(Yea, Mon, Day, Hou, Min, sat, segdir, decomp, isbulk,
                        'ahi_hrit', composites,
                        area, area_cities, ADDcoasts, ADDborders, ADDrivers, ADDlakes,
                        ADDgrid, ADDcities, ADDpoints, ADDstation, GEOcache, OVRcache, testrun)

    for composite in composites:
        magick = get_magick(Yea, Mon, Day, Hou, Min, height, logo1, logo2, service, channel,
                            receiver, sat, sensor, composite, area, testrun, ADDlegend,
                            subdir='frames')
        os.system(magick)

