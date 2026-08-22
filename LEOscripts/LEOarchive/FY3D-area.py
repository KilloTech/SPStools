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
#
#************************************************************************
#
# File Pattern : {platform_shortname}_{start_time:%Y%m%d_%H%M%S}_{end_time:%H%M%S}_{orbit_number:s}_MERSI_1000M_L1B.{ext}
# File Pattern : {platform_shortname}_{start_time:%Y%m%d_%H%M%S}_{end_time:%H%M%S}_{orbit_number:s}_MERSI_GEO1K_L1B.{ext}
# Example name : FY3D_20200429_011200_011300_12719_MERSI_1000M_L1B.HDF
# Example name : FY3D_20200429_011200_011300_12719_MERSI_GEO1K_L1B.HDF
# Hugo's ruler : 0123456789012345678901234567890123456789012345678901234567890
# copied EMCV  : 0         1         2         3         4         5         6
# EUMETCast    : These files arrive as above in channel E1H-RDS-2 (HVS-1)
# ANNOTATION   : This script uses ImageMagick (IM) convert for annotation
#

# I need
from LEOstuff import test_argv, leo_images, get_magick
import os, sys, platform

# Why to hell is it not working?
# from satpy.utils import debug_on
# debug_on()

# What you should know
OS = platform.system()
# Minimal command line parameter test
sat, Dat, Yea, Mon, Day, NoD = test_argv()

# vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv
# ********** ADAPT THESE PARAMETERS TO YOUR PERSONAL NEEDS ***********

# Edit 0-4 parameter(s) below according to your file layout:
# My files are in a /MountPoint/Channel/YYYY/mm/dd structure
# Your segdir may be named differently from EUMETSAT channel
# No trailing / because this will make timestamps unreadable

if OS == 'Linux':
    segdir = '/srv/E1H-RDS-2'
    isbulk = False
elif OS == 'Windows':
    segdir = 'Z:/E1H-RDS-2'
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
# 'overview_raw', 'true_color', 'true_color_raw']  ('ash'+'dust' broken?).

# Choose your composites for DAY and NIG passes. These must be lists containing at least one entry.
if NoD == 'DAY':
    composites = ['overview', 'true_color', 'natural_color']
else:   # 'NIG'
    composites = ['night_fog', 'ir108_3d']

# Choose your 'area' name from file areas.yaml, there is no fake area 'swath' as in Starter Kit 3.0
# For dynamic areas 'omerc_bb', 'laea_bb' set your POI with kwargs, else POI defaults to your station
# kwargs = {'lon': 7.5, 'lat': 47.0, 'ran': 20.0}   <--- This is an example, kwargs is a dictionary
kwargs = {}
# area = 'omerc_bb'
area = 'eurol'
# area = 'westminster'
# area = 'isleofman'
# area = 'switzerland'

# Depending on the size of your area you may want to display multiple passes (e.g. for area = 'eurol')
# You cannot choose multi = True for areas 'omerc_bb' and 'laea_bb' that work for single passes only!!
multi = True

# Optionally you can define an area dependant cities-list. If empty a sat default cities-list is used.
# Be aware that adding one city name will change your OVRcache even if the city is outside your image.
area_cities = []

# Configure your individual overlays, either True/False or 1/0 do work
ADDgrid    = True
ADDcoasts  = True
ADDborders = True
ADDrivers  = True
ADDlakes   = True
ADDcities  = True
ADDpoints  = True
ADDstation = True
ADDlegend  = True

# OVRCache speeds up static overlays. These are stored in data directory cache.
# Never use this with homebrew or SatPy's dynamic areas like omec_bb and laea_bb
# With caching you will sometimes have to delete *.png OVRcache files manually!
OVRcache = False

# If you are testing interactively while PyTROLL/SatPy image generation croned
# This allows for one interactively started script that will use tmpdirs/xtest
testrun = True

# ******** TOUCH THE CODE BELOW ONLY IF YOU KNOW WHAT YOU DO *********
# ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^


Yea, Mon, Day, Hou, Min, height = leo_images(Yea, Mon, Day, sat, NoD, multi, segdir, True, isbulk, 'mersi2_l1b',
                                             composites, area, area_cities, ADDcoasts, ADDborders, ADDrivers, ADDlakes,
                                             ADDgrid, ADDcities, ADDpoints, ADDstation, OVRcache, testrun, **kwargs)


# *******************************************************************
# POST PROCESSING LEGEND: WORKS WITH ALL SCRIPTS AND PROJECTION AREAS
# *******************************************************************

# Below is for legend only
sensor = 'mersi2'
# EUMETCast Europe service
service = 'HVS-1'
# EUMETSAT channel naming
channel = 'E1H-RDS-2'
# Logos in logos directory
logo1 = 'CMA_1000x1000.png'
logo2 = 'PyTROLL_400x400.jpg'

for composite in composites:

    magick = get_magick(Yea, Mon, Day, Hou, Min, height, logo1, logo2, service, channel, receiver,
                        sat, sensor, composite, area, testrun, NoD, multi, ADDlegend)  # basedir=basedir, subdir=subdir

    # **ImageMagick**
    os.system(magick)

# If you get an image in the satellites tmp directory but no final image with
# legend at left then you have a problem with ImageMagick. THAT'S ALL FOLKS?!
