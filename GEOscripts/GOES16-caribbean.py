#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# USAGE: GOES16.py YYYYmmddHHMM, where dd=01..31, HH=00..23, MM=00,10,...
#************************************************************************
#
# American geostationary satellite GOES-16 at 75.2 degrees West (Florida)
# -----------------------------------------------------------------------
# EUMETSAT is EUMETCast disseminating 10 minutes GOES16 data in E1H-TPG-1
# GOES16 at 75.2 degrees West has noon at about 16:30 UTC, sensor 'abi'
#
# See Hugo's EUMETCastView or in .../satpy/etc/readers/abi_l1b.yaml
#
# Channel | C01  | C02  | C03  | C04  | C05  | C06  | C07  | C08  |
# WaveLen | 0.47 | 0.64 | 0.86 | 1.37 | 1.61 | 2.25 | 3.89 | 6.17 |
# --------+------+------+------+------+------+------+------+------+
# Channel | C09  | C10  | C11  | C12  | C13  | C14  | C15  | C16  |
# WaveLen | 6.93 | 7.34 | 8.50 | 9.61 | 10.35| 11.2 | 12.3 | 13.3 |
#
# CH-3123 Belp, 2022/12/10       License GPL3          (c) Ernst Lobsiger
#
#************************************************************************
#
# Typical naming of GOES16 channel data files (channel C15 is shown below)
# File Pattern : {system_environment:2s}_{mission_id:3s}-L1b-{observation_type:3s}{scene_abbr:s}-{scan_mode:2s}C15_{platform_shortname:3s}_s{start_time:%Y%j%H%M%S%f}_e{end_time:%Y%j%H%M%S%f}_c{creation_time:%Y%j%H%M%S%f}.nc{nc_version}
# Example name : OR_ABI-L1b-RadF-M6C15_G16_s20220970510205_e20220970519519_c20220970519587.nc
# Hugo's ruler : 012345678901234567890123456789012345678901234567890123456789012345678901234567890
# copied EMCV  : 0         1         2         3         4         5         6         7         8
# EUMETCast    : These files arrive as above in channel E1H-TPG-1 (HVS-1)
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
    segdir = '/srv/E1H-TPG-1'
    isbulk = False
elif OS == 'Windows':
    segdir = 'Z:/E1H-TPG-1'
    isbulk = False
else:
    sys.exit('Sorry, OS ' + OS + ' seems unsupported yet ...')

# Your TC receiver type
receiver = 'TBS-6909X'

# Output of global_scene.available_composite_names() when all 16 GOES16/17 abi channels are loaded:
# *************************************************************************************************
# allcomposites = ['airmass', 'ash', 'cimss_cloud_type', 'cimss_cloud_type_raw', 'cimss_green',
#    'cimss_green_sunz', 'cimss_green_sunz_rayleigh', 'cimss_true_color', 'cimss_true_color_sunz',
#    'cimss_true_color_sunz_rayleigh', 'cira_day_convection', 'cira_fire_temperature', 'cloud_phase',
#    'cloud_phase_distinction', 'cloud_phase_distinction_raw', 'cloud_phase_raw', 'cloudtop',
#    'color_infrared', 'colorized_ir_clouds', 'convection', 'day_microphysics', 'day_microphysics_abi',
#    'day_microphysics_eum', 'dust', 'fire_temperature_awips', 'fog', 'green', 'green_crefl', 'green_nocorr',
#    'green_raw', 'green_snow', 'highlight_C14', 'ir108_3d', 'ir_cloud_day', 'land_cloud', 'land_cloud_fire',
#    'natural_color', 'natural_color_nocorr', 'natural_color_raw', 'night_fog', 'night_ir_alpha',
#    'night_ir_with_background', 'night_ir_with_background_hires', 'night_microphysics', 'night_microphysics_abi',
#    'overview', 'overview_raw', 'snow', 'snow_fog', 'so2', 'tropical_airmass', 'true_color', 'true_color_crefl',
#    'true_color_nocorr', 'true_color_raw', 'true_color_with_night_ir', 'true_color_with_night_ir_hires',
#    'water_vapors1', 'water_vapors2']

# All composites above as included with SatPy 0.35 and are defined in abi_dict{} + abi_abbr{}.
# For not yet defined personal composites all channels are read from disk and an automatic abbreviation
# is generated. Therefore frequently used composites **should** be defined to minimize disk/network
# load. This includes personal composites that you have in ../pppconfig/composites + /enhancements !

# Choose one or more composites from the list above:
# (Your own personal composites should work as well)
# You can set composites = allcomposites if you dare

# This is now a list of composites and not a string (a single entry 'ash' must be written as ['ash'])
composites = ['true_color_with_night_ir_hires']

# Choose your area ('full_scan' was not pretty) GOES16 'full_scan' has been replaced by 'goes_ef_2km'
# area = 'goes_ef_2km'
area = 'caribbean'
# area = 'n_america'
# area = 's_america'

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

# OVRCache speeds up static overlays. These are stored in your .../SPSdata/cache
# With caching you will sometimes have to delete *.png OVRcache files manually !
OVRcache = True

# If you are testing interactively while PyTROLL/SatPy image generation croned
# This allows for one interactively started script that will use tmpdirs/xtest
testrun = False

# ******** TOUCH THE CODE BELOW ONLY IF YOU KNOW WHAT YOU DO *********
# ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^


height = geo_images(Yea, Mon, Day, Hou, Min, sat, segdir, True, isbulk, 'abi_l1b', composites, area, area_cities,
                    ADDcoasts, ADDborders, ADDrivers, ADDlakes, ADDgrid, ADDcities, ADDpoints, ADDstation,
                    GEOcache, OVRcache, testrun)


# *******************************************************************
# POST PROCESSING LEGEND: WORKS WITH ALL SCRIPTS AND PROJECTION AREAS
# *******************************************************************

# Below is for legend only
sensor = 'abi'
# EUMETCast Europe service
service = 'HVS-1'
# EUMETSAT channel naming
channel = 'E1H-TPG-1'
# Logos in logos directory
logo1 = 'NOAA_1200x1200.png'
logo2 = 'PyTROLL_400x400.jpg'

for composite in composites:

    magick = get_magick(Yea, Mon, Day, Hou, Min, height, logo1, logo2, service, channel,
                        receiver, sat, sensor, composite, area, testrun, ADDlegend,
                        subdir='images')  # basedir=basedir, subdir=subdir

    # **ImageMagick**
    os.system(magick)

# If you get an image in the satellites tmp directory but no final image with
# legend at left then you have a problem with ImageMagick. THAT'S ALL FOLKS?!
