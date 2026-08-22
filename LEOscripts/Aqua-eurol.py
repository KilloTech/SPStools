#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#************************************************************************
#
# Satellite: EOS-Aqua                                       Sensor: MODIS
# https://directory.eoportal.org/web/eoportal/satellite-missions/a/aqua
# https://www.wmo-sat.info/oscar/satellites/view/aqua
#
# Orbit: Sun-synchronous app. LTAN=13:30   (Local Time on Ascending Node)
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
# File Pattern : thin_M{platform_indicator:1s}D021KM.A{start_time:%Y%j.%H%M}.{collection:03d}{suffix}.hdf
# Example name : thin_MYD021KM.A2022203.0450.061.2022203061813.NRT.hdf
# Hugo's ruler : 01234567890123456789012345678901234567890123456789012
# copied EMCV  : 0         1         2         3         4         5
# EUMETCast    : These files arrive as above in channel E1B-TPL-1 (Basic Service)
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
    segdir = '/srv/E1B-TPL-1'
    isbulk = False
elif OS == 'Windows':
    segdir = 'Z:/E1B-TPL-1'
    isbulk = False
else:
    sys.exit('Sorry, OS ' + OS + ' seems unsupported yet ...')

# Your TC receiver type
receiver = 'TBS-6909X'

# Available composites in this script   (see .../satpy/etc/composites/modis/visir.yaml):
# **************************************************************************************
# ['ash', 'day_microphysics', 'dust', 'fog', 'green_snow', 'ir108_3d', 'ir_cloud_day', 'natural_color',
#  'natural_color_raw', 'natural_with_night_fog', 'night_fog', 'overview', 'snow', 'true_color_thin']

# Choose your composites for DAY and NIG passes. These must be lists containing at least one entry.
if NoD == 'DAY':
    composites = ['natural_color', 'overview', 'true_color_thin']
else:   # 'NIG'
    composites = ['dust', 'ir108_3d', 'night_fog']

# Choose your 'area' name from file areas.yaml, there is no fake area 'swath' as in Starter Kit 3.0
# For dynamic areas 'omerc_bb', 'laea_bb' set your POI with kwargs, else POI defaults to your station
# kwargs = {'lon': 7.5, 'lat': 47.0, 'ran': 15.0}   <--- This is an example, kwargs is a dictionary
# area = 'omerc_bb'
kwargs = {}
# area = 'barents_sea'
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

# OVRCache speeds up static overlays. These are stored in your .../SPSdata/cache
# Never use this with homebrew or SatPy's dynamic areas like omec_bb and laea_bb
# With caching you will sometimes have to delete *.png OVRcache files manually !
OVRcache = True

# If you are testing interactively while PyTROLL/SatPy image generation croned
# This allows for one interactively started script that will use tmpdirs/xtest
testrun = False

# ******** TOUCH THE CODE BELOW ONLY IF YOU KNOW WHAT YOU DO *********
# ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^


Yea, Mon, Day, Hou, Min, height = leo_images(Yea, Mon, Day, sat, NoD, multi, segdir, True, isbulk, 'modis_l1b',
                                             composites, area, area_cities, ADDcoasts, ADDborders, ADDrivers, ADDlakes,
                                             ADDgrid, ADDcities, ADDpoints, ADDstation, OVRcache, testrun, **kwargs)


# *******************************************************************
# POST PROCESSING LEGEND: WORKS WITH ALL SCRIPTS AND PROJECTION AREAS
# *******************************************************************

# Below is for legend only
sensor = 'modis'
# EUMETCast Europe service
service = 'Basic'
# EUMETSAT channel naming
channel = 'E1B-TPL-1'
# Logos in logos directory
logo1 = 'NOAA_1200x1200.png'
logo2 = 'PyTROLL_400x400.jpg'

for composite in composites:

    magick = get_magick(Yea, Mon, Day, Hou, Min, height, logo1, logo2, service, channel, receiver,
                        sat, sensor, composite, area, testrun, NoD, multi, ADDlegend,
                        subdir = NoD)  # basedir=basedir, subdir=subdir

    # **ImageMagick**
    os.system(magick)

# If you get an image in the satellites tmp directory but no final image with
# legend at left then you have a problem with ImageMagick. THAT'S ALL FOLKS?!

