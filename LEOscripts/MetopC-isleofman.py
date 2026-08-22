#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#***********************************************************************
#
# Satellite: Metop-C                                       Sensor: avhrr
# https://directory.eoportal.org/web/eoportal/satellite-missions/m/metop
#          (EPS M03 see EUMETSAT: EPS Product File Naming for EUMETCast)
#
# Orbit: Sun-synchronous app. LTDN=09:30 (Local Time on Descending Node)
#
#         ***** This script takes an argument YYYYmmddNoD *****
#                  Where NoD must be either NIG or DAY
#
#-----------------------------------------------------------------------
#
# CH-3123 Belp, 2022/12/10       License GPL3         (c) Ernst Lobsiger
#
#***********************************************************************
#
# File Pattern : AVHR_xxx_1B_{platform_short_name}_{start_time:%Y%m%d%H%M%SZ}_{end_time:%Y%m%d%H%M%SZ}_{processing_mode}_{disposition_mode}_{creation_time:%Y%m%d%H%M%SZ}
# Example name : AVHR_xxx_1B_M03_20190326085203Z_20190326085503Z_N_O_20190326103042Z
# Hugo's ruler : 01234567890123456789012345678901234567890123456789012345678901234567890
# copied EMCV  : 0         1         2         3         4         5         6         7
# EUMETCast    : These files arrive as *.bz2 in channel E1B-EPS-10 (Basic Service)
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
    segdir = '/srv/E1B-EPS-10'
    decomp = False
    isbulk = False
elif OS == 'Windows':
    segdir = 'Z:/E1B-EPS-10'
    decomp = False
    isbulk = False
else:
    sys.exit('Sorry, OS ' + OS + ' seems unsupported yet ...')

# Your TC receiver type
receiver = 'TBS-6909X'


# Available composites in this script   (see .../satpy/etc/composites/visir.yaml):
# ********************************************************************************
# ['cloud_phase_distinction', 'cloud_phase_distinction_raw', 'cloudtop', 'green_snow',
#  'ir108_3d', 'ir_cloud_day', 'natural_color', 'natural_color_raw', 'natural_enh',
#  'natural_with_night_fog', 'night_fog', 'night_microphysics', 'overview', 'overview_raw']

# Choose your composites for DAY and NIG passes. These must be lists containing at least one entry.
if NoD == 'DAY':
    composites = ['cloud_phase_distinction', 'natural_color']
else:   # 'NIG'
    composites = ['cloudtop', 'night_fog']

# Choose your 'area' name from file areas.yaml, there is no fake area 'swath' as in Starter Kit 3.0
# For dynamic areas 'omerc_bb', 'laea_bb' set your POI with kwargs, else POI defaults to your station
# kwargs = {'lon': 7.5, 'lat': 47.0, 'ran': 15.0}   <--- This is an example, kwargs is a dictionary
kwargs = {}
# area = 'omerc_bb'
# area = 'eurol'
# area = 'westminster'
area = 'isleofman'
# area = 'switzerland'

# Depending on the size of your area you may want to display multiple passes (e.g. for area = 'eurol')
# You cannot choose multi = True for areas 'omerc_bb' and 'laea_bb' that work for single passes only!!
multi = False

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


Yea, Mon, Day, Hou, Min, height = leo_images(Yea, Mon, Day, sat, NoD, multi, segdir, decomp, isbulk, 'avhrr_l1b_eps',
                                             composites, area, area_cities, ADDcoasts, ADDborders, ADDrivers, ADDlakes,
                                             ADDgrid, ADDcities, ADDpoints, ADDstation, OVRcache, testrun, **kwargs)


# *******************************************************************
# POST PROCESSING LEGEND: WORKS WITH ALL SCRIPTS AND PROJECTION AREAS
# *******************************************************************

# Below is for legend only
sensor = 'avhrr'
# EUMETCast Europe service
service = 'Basic'
# EUMETSAT channel naming
channel = 'E1B-EPS-10'
# Logos in logos directory
logo1 = 'eumetsat_200x199.png'
logo2 = 'PyTROLL_400x400.jpg'

for composite in composites:

    magick = get_magick(Yea, Mon, Day, Hou, Min, height, logo1, logo2, service, channel, receiver,
                        sat, sensor, composite, area, testrun, NoD, multi, ADDlegend,
                        subdir=NoD)  # basedir=basedir, subdir=subdir

    # **ImageMagick**
    os.system(magick)

# If you get an image in the satellites tmp directory but no final image with
# legend at left then you have a problem with ImageMagick. THAT'S ALL FOLKS?!
