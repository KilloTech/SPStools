#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# USAGE: MSG4.py YYYYmmddHHMM, where dd=01..31, HH=00..23, MM=00,15,30,45
#************************************************************************
#
# European geostationary satellite Meteosat-11 (MSG4) at 0.0 degrees East
#------------------------------------------------------------------------
# EUMETSAT is EUMETCast sending  NWC (SAF) data in Basic channel E1B-GEO-4
# Meteosat-11 (MSG4), at 0.0 noon is exactly 12:00 UTC, sensor 'seviri'
#
# Channel | VIS006 |   HRV  | VIS008 | IR_016 | IR_039 | WV_062 |
# WaveLen |  0.635 |   0.7  |   0.81 |   1.64 |   3.90 |   6.25 |
# --------+--------+--------+--------+--------+--------+--------+
# Channel | WV_073 | IR_087 | IR_097 | IR_108 | IR_120 | IR_134 |
# WaveLen |   7.35 |   8.70 |   9.66 |  10.80 |  12.00 |  13.40 |
#
# CH-3123 Belp, 2022/12/10       License GPL3          (c) Ernst Lobsiger
#
#************************************************************************
#
# Typical naming of MSG4 NWC-SAF files (CT, CMA, CTTH, see ../etc/nwcsaf-geo.yaml)
# File_patterns: S_NWC_CT_{platform_id}_{region_id}_{start_time:%Y%m%dT%H%M%S}Z.nc
# Example name : S_NWC_CT_MSG4_MSG-N-VISIR_20220513T181500Z.nc
# Hugo's ruler : 012345678901234567890123456789012345678901234
# copied EMCV  : 0         1         2         3         4
# EUMETCast    : These files arrive as above in channel E1B-GEO-4 (Basic)
# ANNOTATION   : This script uses ImageMagick (IM) convert for annotation


# I need
import os, sys, platform
from GEOstuff import test_argv, geo_images, get_magick

# Why to hell is it not working?
# from satpy.utils import debug_on
# debug_on()

# What you should know
OS = platform.system()
# Minimal command line parameter test
sat, Dat, Yea, Mon, Day, Hou, Min = test_argv()


# vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv
# ********** ADAPT THESE PARAMETERS TO YOUR PERSONAL NEEDS ***********

# Edit 0-4 parameter(s) below according to your file layout:
# My files are in a /MountPoint/Channel/YYYY/mm/DD structure
# Your segdir may be named differently from EUMETSAT channel
# No trailing / because this will make timestamps unreadable

if OS == 'Linux':
    segdir = '/srv/E1B-GEO-4'
    isbulk = False
elif OS == 'Windows':
    segdir = 'Z:/E1B-GEO-4'
    isbulk = False
else:
    sys.exit('Sorry, OS ' + OS + ' seems unsupported yet ...')

# Your TC receiver type
receiver = 'TBS-6909X'

# Output of global_scene.available_composite_names() when all MSG4 NWC-SAF datasets are loaded:
# *********************************************************************************************
# ['cloud_top_height', 'cloud_top_pressure', 'cloud_top_temperature', 'cloudmask', 'cloudtype']

# Choose one or more composites from the list above:
# (Your own personal composites should work as well)

# This is now a list of composites and not a string (a single entry 'ash' must be written as ['ash'])
composites = ['cloudtype', 'cloud_top_pressure', 'cloud_top_temperature', 'cloudmask']


# The global data only show the northern part of the disc down to Marocco, dataset Nx=2295 and Ny=928
# area = 'msg_fes_3km'
# area = 'eurol'
area = 'westminster'
# area = 'isleofman'
# area = 'switzerland'

# Optionally you can define an area dependant cities-list. If empty a sat default cities-list is used.
# Be aware that adding one city name will change your OVRcache even if the city is outside your image.
area_cities = []

# Configure your individual overlay components, either True/False or 1/0 do work
# The order below is how these components are drawn from the bottom to top layer
ADDcoasts  = True
ADDborders = True
ADDrivers  = True
ADDlakes   = True
ADDgrid    = True
ADDcities  = True
ADDpoints  = True
ADDstation = True
ADDlegend  = True

# GEOcache allows for a resample cache of GEO satellites (speedy massproduction)
# These caches are stored in subdirectories with unique names .../nn_lut-*.zarr
GEOcache = True

# OVRCache speeds up static overlays. These are stored in data directory cache.
# With caching you will sometimes have to delete *.png OVRcache files manually!
OVRcache = True

# If you are testing interactively while PyTROLL/SatPy image generation croned
# This allows for one interactively started script that will use tmpdirs/xtest
testrun = True

# ******** TOUCH THE CODE BELOW ONLY IF YOU KNOW WHAT YOU DO *********
# ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^


height = geo_images(Yea, Mon, Day, Hou, Min, sat, segdir, True, isbulk, 'nwcsaf-geo', composites, area, area_cities,
                    ADDcoasts, ADDborders, ADDrivers, ADDlakes, ADDgrid, ADDcities, ADDpoints, ADDstation,
                    GEOcache, OVRcache, testrun)

# *******************************************************************
# POST PROCESSING LEGEND: WORKS WITH ALL SCRIPTS AND PROJECTION AREAS
# *******************************************************************

# Below is for legend only
sensor = 'seviri'
# EUMETCast Europe service
service = 'Basic'
# EUMETSAT channel naming
channel = 'E1B-GEO-4'
# Logos in logos directory
logo1 = 'eumetsat_200x199.png'
logo2 = 'PyTROLL_400x400.jpg'

for composite in composites:

    magick = get_magick(Yea, Mon, Day, Hou, Min, height, logo1, logo2, service, channel,
                        receiver, sat, sensor, composite, area, testrun, ADDlegend)  # basedir=basedir, subdir=subdir

    # **ImageMagick**
    os.system(magick)

# If you get an image in the satellites tmp directory but no final image with
# legend at left then you have a problem with ImageMagick. THAT'S ALL FOLKS?!
