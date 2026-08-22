#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# USAGE: MTI1.py YYYYmmddHHMM, where dd=01..31, HH=00..23, MM=00,10,...
#**********************************************************************************
# Meteosat Third Generation Imager, MTI-1                              sensor 'fci'
#
# Channel | vis_04 | vis_05 | vis_06 | vis_08 | vis_09 | nir_13 | nir_16 | nir_22 |
# WaveLen |  0.444 |  0.510 |  0.640 |  0.865 |  0.914 |  1.380 |  1.610 |  2.250 |
# --------+--------+--------+--------+--------+--------+--------+--------+--------+
# Channel |  ir_38 |  wv_63 |  wv_73 |  ir_87 |  ir_97 | ir_105 | ir_123 | ir_133 |
# WaveLen |  3.800 |  6.300 |  7.350 |  8.700 |  9.660 | 10.500 | 12.300 | 13.300 |
#
# CH-3123 Belp, 2022/12/10            License GPL3               (c) Ernst Lobsiger
#
#**********************************************************************************
#
# File_pattern : '{pflag}_{location_indicator},{data_designator},MTI{spacecraft_id:1d}+{data_source}-1C-RRAD-FDHSI-{coverage}-{subsetting}-{component1}-BODY-{component3}-{purpose}-{format}_{oflag}_{originator}_{processing_time:%Y%m%d%H%M%S}_{facility_or_tool}_{environment}_{start_time:%Y%m%d%H%M%S}_{end_time:%Y%m%d%H%M%S}_{processing_mode}_{special_compression}_{disposition_mode}_{repeat_cycle_in_day:>04d}_{count_in_repeat_cycle:>04d}.nc'
# Example name : W_XX-EUMETSAT-Darmstadt,IMG+SAT,MTI1+FCI-1C-RRAD-FDHSI-FD--CHK-BODY---NC4E_C_EUMT_20170920000515_GTT_DEV_20170920000008_20170920000015_N__T_0001_0001.nc
# Hugo's ruler : 01234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901
# copied EMCV  : 0         1         2         3         4         5         6         7         8         9        10        11        12        13        14        15
# EUMETCast(?) : These files are currently downloaded as test data assembled by EUMETSAT from MODIS and other sensors
# https://sftp.eumetsat.int/public/folder/UsCVknVOOkSyCdgpMimJNQ/User-Materials/Test-Data/MTG/MTG_FCI_L1C_SpectrallyRepresentative_TD-360_May2022/ <https://sftp.eumetsat.int/public/folder/UsCVknVOOkSyCdgpMimJNQ/User-Materials/Test-Data/MTG/MTG_FCI_L1C_SpectrallyRepresentative_TD-360_May2022/>
# ANNOTATION   : This script uses ImageMagick (IM) convert for annotation
#


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
    segdir = '/home/eumetcast/RC0073C'
    isbulk = True
elif OS == 'Windows':
    segdir = 'Z:/RCRC0073'
    isbulk = False
else:
    sys.exit('Sorry, OS ' + OS + ' seems unsupported yet ...')

# Your TC receiver type
receiver = 'TBS-6909X'

# Output of global_scene.available_composite_names() when all FCI channels are loaded:
# ***********************************************************************************
# ['airmass', 'ash', 'cimss_cloud_type', 'cimss_cloud_type_raw', 'cloud_phase', 'cloud_phase_distinction',
#  'cloud_phase_distinction_raw', 'cloud_phase_raw', 'cloudtop', 'convection', 'day_microphysics', 'dust',
#  'fog', 'green_snow', 'ir108_3d', 'ir_cloud_day', 'natural_color', 'natural_color_raw',
#  'natural_with_night_fog', 'night_fog', 'night_microphysics', 'true_color_raw']


# A list of possible composites is not yet available. Choose one or more composites from the list below:
# These composites currently work (enhancements often fail, due to missing solar angles in FCI test set).
composites = ['airmass', 'ash', 'cimss_cloud_type_raw', 'cloud_phase_distinction_raw', 'cloud_phase_raw',
              'cloudtop', 'convection', 'day_microphysics', 'dust', 'fog', 'green_snow',
              'ir108_3d', 'ir_cloud_day', 'natural_color', 'natural_color_raw',
              'night_fog', 'night_microphysics', 'true_color_raw']

# Choose your area ('full_scan' was not pretty) MTI1 'full_scan' has been replaced by 'fci_0deg_4km'
# area = 'eurol'
area = 'fci_0deg_4km'  # 2km = 5568x5568 pixels / 4km = 2784x2784 pixels
# area = 'eurol'

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


height = geo_images(Yea, Mon, Day, Hou, Min, sat, segdir, True, isbulk, 'fci_l1c_nc', composites, area, area_cities,
                    ADDcoasts, ADDborders, ADDrivers, ADDlakes, ADDgrid, ADDcities, ADDpoints, ADDstation,
                    GEOcache, OVRcache, testrun)


# *******************************************************************
# POST PROCESSING LEGEND: WORKS WITH ALL SCRIPTS AND PROJECTION AREAS
# *******************************************************************

# Below is for legend only
sensor = 'fci'
# EUMETCast Europe service
service = 'HVS-3'
# EUMETSAT channel naming
channel = 'E3H-GEO-1'
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
