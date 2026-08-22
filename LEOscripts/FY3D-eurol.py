#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#************************************************************************
#
# Satellite: Feng-Yun 3D                                  Sensor: MERSI-2
# https://directory.eoportal.org/web/eoportal/satellite-missions/f/fy-3
# https://www.wmo-sat.info/oscar/satellites/view/fy-3d
#
# Orbit: Sun-synchronous app. LTAN=13:29   (Local Time on Ascending Node)
#
#          ***** This script takes an argument YYYYmmddNoD *****
#                   Where NoD must be either NIG or DAY
#
#------------------------------------------------------------------------
#
# CH-3123 Belp, 2022/12/10       License GPL3          (c) Ernst Lobsiger
# Adapted for eurol area - E1H-RDS-2 HVS-1 service
#
#************************************************************************
#
# File Pattern : {platform_shortname}_{start_time:%Y%m%d_%H%M%S}_{end_time:%H%M%S}_{orbit}_MERSI_1000M_L1B.HDF
# Example name : FY3D_20200429_011200_011300_12719_MERSI_1000M_L1B.HDF
# EUMETCast    : These files arrive in channel E1H-RDS-2 (HVS-1)
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
    segdir = '/home/sps/received/hvs-1/E1H-RDS-2'
    isbulk = False
elif OS == 'Windows':
    segdir = 'Y:/received/hvs-1/E1H-RDS-2'
    isbulk = False
else:
    sys.exit('Sorry, OS ' + OS + ' seems unsupported yet ...')

# Your TC receiver type
receiver = 'TBS-6909X'

# Available composites: See files ../satpy/etc/composites/mersi-2.yaml and visir.yaml
# ***********************************************************************************
# ['ash', 'cloudtop', 'day_microphysics', 'dust', 'fog', 'green_snow',
# 'ir108_3d', 'ir_cloud_day', 'natural_color', 'natural_color_lowres',
# 'natural_color_raw', 'natural_with_night_fog', 'night_fog', 'overview',
# 'overview_raw', 'true_color', 'true_color_raw']

# Choose your composites for DAY and NIG passes.
if NoD == 'DAY':
    composites = ['true_color', 'natural_color', 'overview']
else:   # 'NIG'
    composites = ['ir108_3d', 'overview']

# eurol area - multi=True to composite all passes over the area
kwargs = {}
area = 'eurol'
multi = True

# area dependant cities-list (empty = sat default)
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

OVRcache = True
testrun  = False

# ******** TOUCH THE CODE BELOW ONLY IF YOU KNOW WHAT YOU DO *********
# ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Yea, Mon, Day, Hou, Min, height = leo_images(Yea, Mon, Day, sat, NoD, multi, segdir, True, isbulk, 'mersi2_l1b',
                                             composites, area, area_cities, ADDcoasts, ADDborders, ADDrivers, ADDlakes,
                                             ADDgrid, ADDcities, ADDpoints, ADDstation, OVRcache, testrun, **kwargs)

# *******************************************************************
# POST PROCESSING LEGEND
# *******************************************************************

sensor  = 'mersi2'
service = 'HVS-1'
channel = 'E1H-RDS-2'
logo1   = 'CMA_1000x1000.png'
logo2   = 'PyTROLL_400x400.jpg'

for composite in composites:
    magick = get_magick(Yea, Mon, Day, Hou, Min, height, logo1, logo2, service, channel, receiver,
                        sat, sensor, composite, area, testrun, NoD, multi, ADDlegend,
                        subdir=NoD)
    os.system(magick)
