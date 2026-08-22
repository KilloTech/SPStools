#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#*************************************************************************
#
# NOAA-20  JPSS (Joint Polar Satellite System)    sensor viirs M+DNB-Bands
# https://directory.eoportal.org/web/eoportal/satellite-missions/n/noaa-20
# https://www.wmo-sat.info/oscar/satellites/view/noaa_20
# Suomi-NPP  JPSS (Joint Polar Satellite System)  sensor viirs M+DNB-Bands
# https://directory.eoportal.org/web/eoportal/satellite-missions/s/suomi-npp
# https://www.wmo-sat.info/oscar/satellites/view/snpp
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
#
#*************************************************************************
#
# File Pattern : SVMC_{platform_shortname}_d{start_time:%Y%m%d_t%H%M%S%f}_e{end_time:%H%M%S%f}_b{orbit:5d}_c{creation_time:%Y%m%d%H%M%S%f}_eum_ops.h5
# Example name : SVMC_j01_d20190411_t0224358_e0226003_b07218_c20190411023355000121_eum_ops.h5
# Hugo's ruler : 012345678901234567890123456789012345678901234567890123456789012345678901234567890
# copied EMCV  : 0         1         2         3         4         5         6         7         8
# File Pattern : SVDNBC_{platform_shortname}_d{start_time:%Y%m%d_t%H%M%S%f}_e{end_time:%H%M%S%f}_b{orbit:5d}_c{creation_time:%Y%m%d%H%M%S%f}_eum_ops.h5
# Example name : SVDNBC_j01_d20190411_t0424054_e0425281_b07219_c20190411043053000049_eum_ops.h5
# Hugo's ruler : 012345678901234567890123456789012345678901234567890123456789012345678901234567890
# copied EMCV  : 0         1         2         3         4         5         6         7         8
# EUMETCast    : NOAA-20   files arrive in channel E1B-RDS-2 (Basic Service)
# EUMETCast    : Suomi-NPP files arrive in channel E1H-RDS-1 (HVS-1 Service)
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
    segdir = ['/srv/E1B-RDS-2', '/srv/E1H-RDS-1']
    isbulk = [False, False]
elif OS == 'Windows':
    segdir = ['Z:/E1B-RDS-2', 'Z:/E1H-RDS-1']
    isbulk = [False, False]
else:
    sys.exit('Sorry, OS ' + OS + ' seems unsupported yet ...')

# Your TC receiver type
receiver = 'TBS-6909X'


# Available DAY composites: See files ../satpy/etc/composites/visir.yaml and viirs.yaml
# *************************************************************************************
# ['ash', 'cloudtop_daytime', 'dust', 'false_color', 'fire_temperature',
#  'fire_temperature_39refl', 'fire_temperature_awips', 'fire_temperature_eumetsat',
#  'fog', 'ir108_3d', 'ir_cloud_day', 'natural_color', 'natural_color_sun_lowres',
#  'natural_with_night_fog', 'night_fog', 'ocean_color', 'overview', 'snow_age',
#  'snow_lowres', 'true_color', 'true_color_crefl', 'true_color_lowres',
#  'true_color_lowres_crefl', 'true_color_lowres_land',
#  'true_color_lowres_marine_tropical', 'true_color_raw']
# NIG composites for DAY passes will not work if they use DNB channels

# Available NIG composites: See files ../satpy/etc/composites/visir.yaml and viirs.yaml
# *************************************************************************************
# ['adaptive_dnb', 'ash', 'dust', 'dynamic_dnb', 'fog', 'histogram_dnb', 'hncc_dnb',
#  'ir108_3d', 'natural_with_night_fog', 'night_fog', 'night_overview']
# Most DAY composites for NIG passes will be black, use DNB for Auroras

# Choose your composites for DAY and NIG passes. These must be lists containing at least one entry.
if NoD == 'DAY':
    composites = ['cloudtop_daytime', 'natural_color', 'true_color']
else:   # 'NIG'
    composites = ['ir108_3d', 'night_fog', 'night_overview']

# Choose your 'area' name from file areas.yaml, there is no fake area 'swath' as in Starter Kit 3.0
# This script is 'multi' per default. Therefore you can't/shouldn't choose 'omerc_bb' or 'laea_bb'!
area = 'eurol'
# area = 'westminster'
# area = 'isleofman'
# area= 'switzerland'

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

# OVRCache speeds up static overlays. These are stored in your .../SPSdata/cache
# Never use this with homebrew or SatPy's dynamic areas like omec_bb and laea_bb
# With caching you will sometimes have to delete *.png OVRcache files manually !
OVRcache = False

# If you are testing interactively while PyTROLL/SatPy image generation croned
# This allows for one interactively started script that will use tmpdirs/xtest
testrun = True

# ******** TOUCH THE CODE BELOW ONLY IF YOU KNOW WHAT YOU DO *********
# ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^


Yea, Mon, Day, Hou, Min, height = leo_images(Yea, Mon, Day, sat, NoD, True, segdir, [True, True], isbulk, 'viirs_compact',
                                             composites, area, area_cities, ADDcoasts, ADDborders, ADDrivers, ADDlakes,
                                             ADDgrid, ADDcities, ADDpoints, ADDstation, OVRcache, testrun, **{})


# *******************************************************************
# POST PROCESSING LEGEND: WORKS WITH ALL SCRIPTS AND PROJECTION AREAS
# *******************************************************************

# Below is for legend only
sensor = 'viirs'
# EUMETCast Europe service
service = 'Basic+HVS-1'
# EUMETSAT channel naming
channel = 'E1X-RDS-X'
# Logos in logos directory
logo1 = 'NOAA_1200x1200.png'
logo2 = 'PyTROLL_400x400.jpg'

for composite in composites:

    magick = get_magick(Yea, Mon, Day, Hou, Min, height, logo1, logo2, service, channel, receiver,
                        sat, sensor, composite, area, testrun, NoD, True, ADDlegend)  # basedir=basedir, subdir=subdir

    # **ImageMagick**
    os.system(magick)

# If you get an image in the satellites tmp directory but no final image with
# legend at left then you have a problem with ImageMagick. THAT'S ALL FOLKS?!
