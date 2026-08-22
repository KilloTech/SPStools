#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#*************************************************************************
#
# NOAA-20  JPSS (Joint Polar Satellite System)    sensor viirs M+DNB-Bands
# https://directory.eoportal.org/web/eoportal/satellite-missions/n/noaa-20
# https://www.wmo-sat.info/oscar/satellites/view/noaa_20
#
# Orbit: Sun-synchronous app. LTAN=13:30    (Local Time on Ascending Node)
#
#         ***** This script takes an argument YYYYmmddNoD *****
#                  Where NoD must be either NIG or DAY
#
# During daylight passes only MXY bands are available. During night passes
# we have DNB (moonlight and artificial illumination) plus all MXY bands!!
#-------------------------------------------------------------------------
#
# CH-3123 Belp, 2022/12/10        License GPL3          (c) Ernst Lobsiger
# Adapted for eurol area - E1H-RDS-1 HVS-1 service
#
#*************************************************************************
#
# File Pattern : SVDNBC_{platform_shortname}_d{start_time:%Y%m%d_t%H%M%S%f}_e{end_time:%H%M%S%f}_b{orbit:5d}_c{creation_time:%Y%m%d%H%M%S%f}_eum_ops.h5
# Example name : SVDNBC_j01_d20190411_t0424054_e0425281_b07219_c20190411043053000049_eum_ops.h5
# EUMETCast    : These files arrive as above in channel E1H-RDS-1 (HVS-1)
# ANNOTATION   : This script uses ImageMagick (IM) convert for annotation
#

# I need
from LEOstuff import test_argv, leo_images, get_magick
import os, sys, platform

# What you should know
OS = platform.system()
# Minimal command line parameter test
sat, Dat, Yea, Mon, Day, NoD = test_argv()

# vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv
# ********** ADAPT THESE PARAMETERS TO YOUR PERSONAL NEEDS ***********

if OS == 'Linux':
    segdir = '/home/sps/received/hvs-1/E1H-RDS-1'
    isbulk = False
elif OS == 'Windows':
    segdir = 'Y:/received/hvs-1/E1H-RDS-1'
    isbulk = False
else:
    sys.exit('Sorry, OS ' + OS + ' seems unsupported yet ...')

# Your TC receiver type
receiver = 'TBS-6909X'

# Choose your composites for DAY and NIG passes.
if NoD == 'DAY':
    composites = ['cloudtop_daytime', 'natural_color', 'true_color']
else:   # 'NIG'
    composites = ['ir108_3d', 'night_fog', 'night_overview']

# eurol area - multi=True to composite all passes over the area
area = 'eurol'
multi = True

area_cities = []

# Configure your individual overlays
ADDgrid    = True
ADDcoasts  = True
ADDborders = True
ADDrivers  = True
ADDlakes   = True
ADDcities  = True
ADDpoints  = True
ADDstation = True
ADDlegend  = True

OVRcache   = True
testrun    = False

kwargs = {}

# ******** TOUCH THE CODE BELOW ONLY IF YOU KNOW WHAT YOU DO *********
# ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Yea, Mon, Day, Hou, Min, height = leo_images(Yea, Mon, Day, sat, NoD, multi, segdir, True, isbulk, 'viirs_compact',
                                             composites, area, area_cities, ADDcoasts, ADDborders, ADDrivers, ADDlakes,
                                             ADDgrid, ADDcities, ADDpoints, ADDstation, OVRcache, testrun, **kwargs)

# *******************************************************************
# POST PROCESSING LEGEND: WORKS WITH ALL SCRIPTS AND PROJECTION AREAS
# *******************************************************************

sensor  = 'viirs'
service = 'HVS-1'
channel = 'E1H-RDS-1'
logo1   = 'NOAA_1200x1200.png'
logo2   = 'PyTROLL_400x400.jpg'

for composite in composites:

    magick = get_magick(Yea, Mon, Day, Hou, Min, height, logo1, logo2, service, channel, receiver,
                        sat, sensor, composite, area, testrun, NoD, multi, ADDlegend,
                        subdir=NoD)

    # **ImageMagick**
    os.system(magick)
