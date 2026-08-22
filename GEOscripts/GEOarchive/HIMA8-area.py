#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# USAGE: HIMA8.py YYYYmmddHHMM, where dd=01..31, HH=00..23, MM=00,10,20,30
#************************************************************************
#
# Japanese geostationary satellite Himawari-8 (HIMA8) at 144.7 degrees East
#
# See Hugo's EUMETCastView or in .../satpy/etc/readers/ahi_hrit.yaml
#------------------------------------------------------------------------
# EUMETSAT is EUMETCast disseminating 10 Minutes HIMA8 data in E1H-TPG-2
# Himawari-8 (HIMA8), at 144.7 noon is at about 03:00 UTC, sensor 'ahi'
#
# Channel | B01  | B02  | VIS  | B04  | B05  | B06  | IR4  | IR3  |
# Channel | B01  | B02  | B03  | B04  | B05  | B06  | B07  | B08  |
# WaveLen | 0.47 | 0.51 | 0.64 | 0.86 | 1.6  | 2.3  | 3.9  | 6.2  |
# --------+------+------+------+------+------+------+------+------+
# Channel | B09  | B10  | B11  | B12  | IR1  | B14  | IR2  | B16  |
# Channel | B09  | B10  | B11  | B12  | B13  | B14  | B15  | B16  |
# WaveLen | 6.9  | 7.3  | 8.6  | 9.6  | 10.4 | 11.2 | 12.4 | 13.3 |
#
# CH-3123 Belp, 2022/12/10        License GPL3         (c) Ernst Lobsiger
#
#************************************************************************
#
# Typical naming of Himawari-8 channel data files (channel B01, segment 4)
# File pattern : IMG_DK{area:02d}B01_{start_time:%Y%m%d%H%M}_{segment:03d}
# Example name : IMG_DK01B01_202204071252_004.bz2
# Hugo's ruler : 01234567890123456789012345678901234567890
# copied EMCV  : 0         1         2         3         4
# EUMETCast    : These files arrive as above in channel E1H-TPG-2 (HVS-1)
# ANNOTATION   : This script uses ImageMagick (IM) convert for annotation

# Hugos's EUMETCastView, mpop, Himawari files use the upper Channel names
# satpy uses lower Channel names B01 .. B16 (loading 'VIS' does not work)
# But 'VIS' makes part of the file names that I am looking to decompress.
# Good natural FES images around 03:00 UTC, we decompress only files used


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

# Edit 0-6 parameter(s) below according to your file layout:
# My files are in a /MountPoint/Channel/YYYY/mm/DD structure
# My files are compressed as received Christian decompresses
# Your segdir may be named differently from EUMETSAT channel
# No trailing / because this will make timestamps unreadable

if OS == 'Linux':
    segdir = '/srv/E1H-TPG-2'
    isbulk = False
    decomp = False
elif OS == 'Windows':
    segdir = 'Z:/E1H-TPG-2'
    isbulk = False
    decomp = False
else:
    sys.exit('Sorry, OS ' + OS + ' seems unsupported yet ...')

# Your TC receiver type
receiver = 'TBS-6909X'

# Output of global_scene.available_composite_names() when all Himawari-8 ahi channels are loaded:
# ***********************************************************************************************
# allcomposites = ['airmass', 'ash', 'cloud_phase_distinction', 'cloud_phase_distinction_raw',
#     'colorized_ir_clouds', 'convection', 'day_microphysics_ahi', 'day_microphysics_eum', 'dust',
#     'fire_temperature_39refl', 'fire_temperature_awips', 'fire_temperature_eumetsat', 'fog',
#     'green', 'green_nocorr', 'green_true_color_reproduction', 'ir_cloud_day', 'mid_vapor',
#     'natural_color', 'natural_color_nocorr', 'natural_color_raw', 'night_ir_alpha',
#     'night_ir_with_background', 'night_ir_with_background_hires', 'night_microphysics', 'overview',
#     'overview_raw', 'true_color', 'true_color_nocorr', 'true_color_raw', 'true_color_reproduction',
#     'true_color_with_night_ir', 'true_color_with_night_ir_hires', 'water_vapors1', 'water_vapors2']

# All composites above as included with SatPy 0.35 and are defined in ahi_dict{} + ahi_abbr{}.
# For not yet defined personal composites all channels are decompressed and an automatic abbreviation
# is generated. Therefore frequently used composites **should** be defined to minimize decompression
# times. This includes personal composites that you have in ../pppconfig/composites + /enhancements !
# Decompressed files are cached in the respective tmp directory for one current time slot. If you make
# successive images of the same time slot, this will minimize the CPU time for wavelet decompression.

# Choose one or more composites from the list above:
# (Your own personal composites should work as well)
# You can set composites = allcomposites if you dare

# This is now a list of composites and not a string (a single entry 'ash' must be written as ['ash'])
composites = ['overview', 'natural_color']

# Choose your area (what we get on EUMETCast seems all 2km), 'full_scan' has been renamed 'hima_f_2km'
# area = 'hima_f_2km'
# area = 'australia'
area = 'japan'

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
OVRcache = False

# If you are testing interactively while PyTROLL/SatPy image generation croned
# This allows for one interactively started script that will use tmpdirs/xtest
testrun = True

# ******** TOUCH THE CODE BELOW ONLY IF YOU KNOW WHAT YOU DO *********
# ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^


height = geo_images(Yea, Mon, Day, Hou, Min, sat, segdir, decomp, isbulk, 'ahi_hrit', composites, area, area_cities,
                    ADDcoasts, ADDborders, ADDrivers, ADDlakes, ADDgrid, ADDcities, ADDpoints, ADDstation,
                    GEOcache, OVRcache, testrun)


# *******************************************************************
# POST PROCESSING LEGEND: WORKS WITH ALL SCRIPTS AND PROJECTION AREAS
# *******************************************************************

# Below is for legend only
sensor = 'ahi'
# EUMETCast Europe service
service = 'HVS-1'
# EUMETSAT channel naming
channel = 'E1H-TPG-2'
# Logos in logos directory
logo1 = 'JMA_947x969.gif'
logo2 = 'PyTROLL_400x400.jpg'

for composite in composites:

    magick = get_magick(Yea, Mon, Day, Hou, Min, height, logo1, logo2, service, channel,
                        receiver, sat, sensor, composite, area, testrun, ADDlegend)  # basedir=basedir, subdir=subdir

    # **ImageMagick**
    os.system(magick)

# If you get an image in the satellites tmp directory but no final image with
# legend at left then you have a problem with ImageMagick. THAT'S ALL FOLKS?!
