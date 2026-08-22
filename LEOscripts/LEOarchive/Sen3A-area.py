#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#************************************************************************
#
# Satellite: Sentinel-3A                                     Sensor: OLCI
#
# https://directory.eoportal.org/web/eoportal/satellite-missions/...
# https://www.wmo-sat.info/oscar/satellites/view/sentinel_3a/3b
#
# Orbit: Sun-synchronous app. LTDN=10:00   (Local Time on Descending Node)
#
#      **** This script takes one CLI parameter YYYYmmddNoD ****
#                       Where NoD must be DAY
#
# It only takes daylight passes       (OLCI does not gather any NIG data)
#------------------------------------------------------------------------
#
# Unfortunately OLCI EFR segments are not available on EUMETCast anymore.
# But we still get OLCI ERR passes. While this is no real replacement it
# is better than nothing. After all it's covering the whole planet like
# Metop GDS. There is no point in Sentinel-3A multipass as OLCI has very
# limited (west looking) swath. For more extended areas use Sentinel-3X
# that combines Sentinel-3A with Sentinel-3B passes in stacked images.
#
# CH-3123 Belp, 2022/12/10       License GPL3          (c) Ernst Lobsiger
#
#************************************************************************
#
# File Pattern : {mission_id:3s}_OL_1_{datatype_id:_<6s}_{start_time:%Y%m%dT%H%M%S}_{end_time:%Y%m%dT%H%M%S}_{creation_time:%Y%m%dT%H%M%S}_{duration:4d}_{cycle:3d}_{relative_orbit:3d}_{frame:4d}_{centre:3s}_{platform_mode:1s}_{timeliness:2s}_{collection:3s}.SEN3.tar
# Example name : S3A_OL_1_ERR____20220520T003318_20220520T011743_20220520T031351_2665_085_259______MAR_O_NR_002.SEN3.tar
# Hugo's ruler : 0123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012
# copied EMCV  : 0         1         2         3         4         5         6         7         8         9         10
# EUMETCast    : These files arrive as above in channel E2H-S3A-02 (HVS-2)
# ANNOTATION   : This script uses ImageMagick (IM) convert for annotation

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
    segdir = '/srv/E2H-S3A-02'
    isbulk = False
elif OS == 'Windows':
    segdir = 'Z:/E2H-S3A-02'
    isbulk = False
else:
    sys.exit('Sorry, OS ' + OS + ' seems unsupported yet ...')

# Your TC receiver type
receiver = 'TBS-6909X'

# ********************************************************************************
# Avaliable composites: See files ../satpy/etc/composites/olci.yaml and visir.yaml
# ********************************************************************************
# composites = ['ocean_color', 'true_color', 'true_color_desert', 'true_color_land',
#              'true_color_marine_clean', 'true_color_marine_tropical', 'true_color_raw',
#              # These moisture composites are taken in from visir.yaml
#              'day_essl_colorized_low_level_moisture', 'day_essl_low_level_moisture',
#              'essl_colorized_low_level_moisture', 'essl_low_level_moisture',
#              # These composites have been used by several power users
#              # See the thread https://groups.io/g/MSG-1/message/30626
#              'ernst100603n', 'ernst100603o', 'ernst100603t',
#              'simon080503n', 'simon080503o', 'simon080503t',
#              'david090604n', 'david090604o', 'david090604t',
#              'hugo211709n',  'hugo211709o',  'hugo211709t',
#              'satpy080603n', 'satpy080603o', 'satpy080603t']


# Choose your composites for DAY (only) passes. These must be lists containing at least one entry.
if NoD == 'DAY':
    composites = ['ernst100603n', 'ernst100603o', 'ernst100603t']
else:   # 'NIG'
    sys.exit('Sorry, OLCI is a daylight instrument only ...')


# Choose your 'area' name from file areas.yaml, there is no fake area 'swath' as in Starter Kit 3.0
# Due to the shape of OLCI ERR 45 minute segment files, 'omerc_bb' 'laea_bb' areas cannot be chosen

# area = 'barents_sea'
# area = 'eurol'
# area = 'westminster'
# area = 'isleofman'
area = 'switzerland'

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


Yea, Mon, Day, Hou, Min, height = leo_images(Yea, Mon, Day, sat, NoD, False, segdir, False, isbulk, 'olci_l1b',
                                             composites, area, area_cities, ADDcoasts, ADDborders, ADDrivers, ADDlakes,
                                             ADDgrid, ADDcities, ADDpoints, ADDstation, OVRcache, testrun, **{})


# *******************************************************************
# POST PROCESSING LEGEND: WORKS WITH ALL SCRIPTS AND PROJECTION AREAS
# *******************************************************************

# Below is for legend only
sensor = 'olci'
# EUMETCast Europe service
service = 'HVS-2'
# EUMETSAT channel naming
channel = 'E2H-S3A-02'
# Logos in logos directory
logo1 = 'Copernicus_1050x1050.png'
logo2 = 'PyTROLL_400x400.jpg'

for composite in composites:

    magick = get_magick(Yea, Mon, Day, Hou, Min, height, logo1, logo2, service, channel, receiver,
                        sat, sensor, composite, area, testrun, NoD, False, ADDlegend)  # basedir=basedir, subdir=subdir

    # **ImageMagick**
    os.system(magick)

# If you get an image in the satellites tmp directory but no final image with
# legend at left then you have a problem with ImageMagick. THAT'S ALL FOLKS?!

