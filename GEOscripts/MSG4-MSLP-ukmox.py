#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# USAGE: MSG4.py YYYYmmddHHMM, where dd=01..31, HH=00..23, MM=00,15,30,45
#************************************************************************
#
# European geostationary satellite Meteosat-11 (MSG4) at 0.0 degrees East
#------------------------------------------------------------------------
# EUMETSAT is EUMETCast disseminating MSG4 data in Basic channel E1B-GEO-3
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
# Typical naming of MSG4 channel data files (channel WV_062 segment 5 below)
# File pattern : {rate:1s}-000-{hrit_format:_<6s}-{platform_shortname:4s}_{service:_<7s}-WV_062___-{segment:06d}___-{start_time:%Y%m%d%H%M}-__
# Example name : H-000-MSG4__-MSG4________-WV_062___-000005___-202204070215-C_
# Hugo's ruler : 0123456789012345678901234567890123456789012345678901234567890
# copied EMCV  : 0         1         2         3         4         5         6
# EUMETCast    : These files arrive as above in channel E1B-GEO-3 (Basic)
# ANNOTATION   : This script uses ImageMagick (IM) convert for annotation


# I need
import os, sys, platform
from GEOstuff import test_argv, get_lists, geo_images, get_magick

# Why to hell is it not working?
# from satpy.utils import debug_on
# debug_on()

# What you should know
OS = platform.system()
# Minimal command line parameter test
sat, Dat, Yea, Mon, Day, Hou, Min = test_argv()
sat = 'MSG3'  # E1B-GEO-3 contains MSG3 (Meteosat-10) files


# vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv
# ********** ADAPT THESE PARAMETERS TO YOUR PERSONAL NEEDS ***********

# Edit 0-6 parameter(s) below according to your file layout:
# My files are in a /MountPoint/Channel/YYYY/mm/DD structure
# My files are compressed as received Christian decompresses
# Your segdir may be named differently from EUMETSAT channel
# No trailing / because this will make timestamps unreadable

if OS == 'Linux':
    segdir = '/home/sps/received/bas/E1B-GEO-3'
    isbulk = True   # flat directory
    decomp = False
elif OS == 'Windows':
    segdir = 'Z:/E1B-GEO-3'
    isbulk = False
    decomp = False
else:
    sys.exit('Sorry, OS ' + OS + ' seems unsupported yet ...')

# Your TC receiver type
receiver = 'TBS-6909X'

# Output of global_scene.available_composite_names() when all Meteosat-X seviri channels are loaded:
# **************************************************************************************************
# allcomposites = ['airmass', 'ash', 'cloud_phase_distinction', 'cloud_phase_distinction_raw', 'cloudtop',
# 'cloudtop_daytime', 'colorized_ir_clouds', 'convection', 'day_microphysics', 'day_microphysics_winter',
# 'dust', 'fog', 'green_snow', 'hrv_clouds', 'hrv_fog', 'hrv_severe_storms', 'hrv_severe_storms_masked',
# 'ir108_3d', 'ir_cloud_day', 'ir_overview', 'ir_sandwich', 'natural_color', 'natural_color_nocorr',
# 'natural_color_raw', 'natural_color_with_night_ir', 'natural_color_with_night_ir_hires', 'natural_enh',
# 'natural_enh_with_night_ir', 'natural_enh_with_night_ir_hires', 'natural_with_night_fog', 'night_fog',
# 'night_ir_alpha', 'night_ir_with_background', 'night_ir_with_background_hires', 'night_microphysics',
# 'overview', 'overview_raw', 'realistic_colors', 'snow', 'vis_sharpened_ir']

# All composites above as included with SatPy 0.35 and are defined in seviri_dict{} + seviri_abbr{}.
# For not yet defined personal composites all channels are decompressed and an automatic abbreviation
# is generated. Therefore frequently used composites **should** be defined to minimize decompression
# times. This includes personal composites that you have in ../pppconfig/composites + /enhancements !
# Decompressed files are cached in the respective tmp directory for one current time slot. If you make
# successive images of the same time slot, this will minimize the CPU time for wavelet decompression.

# Choose one or more composites from the list above:
# (Your own personal composites should work as well)
# You can set composites = allcomposites if you dare

# This is now a list of composites and not a string (a single entry 'ash' must be written as ['ash'])
composites = ['overview', 'airmass', 'colorized_ir_clouds']


# Choose your area (remember that HRV data has only limited coverage)
# ** THIS IS A SPECIAL SCRIPT VERSION FOR PRESSURE CHARTS OVERLAYS **
# You are only allowed to use these 8 special areas for these charts:

# 'dwda'       DWD, Western Europe, 3 hourly, allowed Types ['bb', 'ww', 'bc', 'wc]
# 'dwdn'       DWD, North Atlantic, 6 hourly, allowed Types ['bb', 'ww', 'bc', 'wc]
# 'dwdc'       DWD, Stereographic, 12 hourly, allowed Types ['bb', 'ww', 'bc', 'wc]
# 'dwdi'       DWD, ICON13 MSLP,   12 hourly, allowed Types ['bb', 'ww']
# 'ukmos'      UKMO, UK MetOffice,  6 hourly, allowed Types ['bb', 'ww']
# 'ukmol'      UKMO, UK MetOffice,  6 hourly, allowed Types ['bb', 'ww']
# 'ukmox'      UKMO, UK MetOffice,  6 hourly, allowed Types ['bb', 'ww']
# 'opcae'      OPC, Atlantic East,  6 hourly, allowed Types ['bc', 'wc']

# All these MSLP charts must be downloaded and prepared in seperate processing chains
for area in ['ukmox', 'ukmos', 'ukmol']:  # ukmox restored: available from E1B-DWDSAT

    # You have to define a list of chart types (one type per composite) that must fit to your composites
    Types = ['ww', 'ww', 'bb']

    # Optionally you can define an area dependant cities-list. If empty a sat default cities-list is used.
    # Be aware that adding one city name will change your OVRcache even if the city is outside your image.
    area_cities = []

    # Configure your individual overlay components, either True/False or 1/0 do work
    # The order below is how these components are drawn from the bottom to top layer
    ADDcoasts  = True
    ADDborders = False
    ADDrivers  = False
    ADDlakes   = False
    ADDgrid    = False
    ADDcities  = False
    ADDpoints  = False
    ADDstation = False
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


    ADDcharts, fill_values = get_lists(sat, composites, area, Types, Dat)

    height = geo_images(Yea, Mon, Day, Hou, Min, sat, segdir, decomp, isbulk, 'seviri_l1b_hrit', composites,
                        area, area_cities, ADDcoasts, ADDborders, ADDrivers, ADDlakes, ADDgrid, ADDcities,
                        ADDpoints, ADDstation, GEOcache, OVRcache, testrun, fill_values=fill_values)

    # *******************************************************************
    # POST PROCESSING LEGEND: WORKS WITH ALL SCRIPTS AND PROJECTION AREAS
    # *******************************************************************

    # Below is for legend only
    sensor = 'seviri'
    # EUMETCast Europe service
    service = 'Basic'
    # EUMETSAT channel naming
    channel = 'E1B-GEO-3'
    # Logos in logos directory
    logo1 = 'eumetsat_200x199.png'
    logo2 = 'PyTROLL_400x400.jpg'

    n = 0
    for composite in composites:

        magick = get_magick(Yea, Mon, Day, Hou, Min, height, logo1, logo2, service, channel,
                            receiver, sat, sensor, composite, area, testrun, ADDlegend,
                            ADDchart=ADDcharts[n], ADDtype=Types[n],
                            basedir='MSLP', subdir=area)
                            # basedir=basedir, subdir=subdir

        # **ImageMagick**
        os.system(magick)

        n += 1

    # If you get an image in the satellites tmp directory but no final image with
    # legend at left then you have a problem with ImageMagick. THAT'S ALL FOLKS?!
