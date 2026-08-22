#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#************************************************************************
#
# This module provides functions necessary for generating *LEO* satellite
# products with 'Satpy Processing System' (SPS) advanced Kit Version 4.1.
# One copy of the file must reside in the same direcory with LEO scripts.
# There are only 2-4 lines that a user (may) have to adapt after install.
# You can also play with resamplers here. Please note that the 'bilinear'
# resampler caching for full disk areas is broken at the time of writing.
#
# CH-3123 Belp, 2022/12/10       License GPL3         (c) Ernst Lobsiger
#
#************************************************************************

# I need
import os, sys, platform
from math import sin, cos, tan, asin, acos, pi
from pyorbital.orbital import Orbital
from datetime import datetime, timedelta
from pyproj import Proj
from glob import glob

# Pytroll/SatPy needs
from satpy import Scene, MultiScene, config
from satpy.resample import get_area_def
try:
    from satpy.writers.core.compute import compute_writer_results
except ImportError:
    from satpy.writers import compute_writer_results

OS = platform.system()


# vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv
# Maybe edit toodir and datdir to define your system layout
# If so, you must also change in a couple of helper scripts

if OS == 'Linux':
    toodir = '/home/sps/SPStools'
    datdir = '/home/sps/SPSdata'
elif OS == 'Windows':
    toodir = 'C:/SPStools'
    datdir = 'D:/SPSdata'
else:
    print('OS not supported (yet) ...')

# This point will be used as your station marker
my_coordinates = []  # no station marker

# DO NOT TOUCH THE STUFF BELOW UNLESS YOU KNOW WHAT YOU DO!
# ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^


if OS == 'Linux':
    bz2Decompress = 'bzip2 -dc '
    escape = '\\'
    convert = 'convert'
    remove = 'rm -f '
    rmolci = 'rm -rf S3*OL_1_ERR____*.SEN3'
elif OS == 'Windows':
    bz2Decompress = toodir + '/exefiles/7za x -so '
    escape = ''
    convert = toodir + '/exefiles/convert.exe'
    remove = 'del /Q '
    rmolci = 'for /F %G in (\'dir /b S3*OL_1_ERR____*.SEN3\') do (rd /s /q %G)'
else:
    print('OS not supported (yet) ...')

# If you set tlefil = '' it will be downloaded from Internet!
tlefil = toodir + '/userconfig/my_TLE_file.txt'

# The main data directory layout is defined here
# These are global variables (accessible below)
cachdir = datdir + '/cache'
logodir = datdir + '/logos'
geodata = datdir + '/geodata'
mslpdir = datdir + '/overlays'
tmpdirs = datdir + '/tmpdirs'
fontdir = datdir + '/fonts'
prodirs = datdir + '/products'

# Replace environment variable 'SATPY_CONFIG_PATH'
config.set(config_path = [toodir + '/userconfig'])

# ************************************************************************************************
# ** For the time being there are numerous LEO sat issues with 'bilinear' and 'gradient_search' **
# ************************************************************************************************

# This the fastest resampler. A cache_dir=geocache brings it down from 63 seconds to 18 seconds
# Resampler 'nearest' (default) gives more contrast (better results when resampling MSLP charts)
resampler_kwargs = {'resampler': 'nearest', 'radius_of_influence': 3000} #, 'reduce_data': False}

# This the slowest resampler. But cache_dir=geocache brings it down from 163 seconds to 25 seconds
# Resampler 'bilinear', once the cache files have been made, is even faster than 'gradient_search'
# resampler_kwargs = {'resampler': 'bilinear', 'reduce_data': True}  # True (default) is faster !

# Resampler 'gradient_search' gives finer resolution than 'nearest' (*shapely* must be installed).
# It does not value a cache_dir=geocache keyword argument and runs with and without in 31 seconds
# resampler_kwargs = {'resampler': 'gradient_search', 'method': 'bilinear', 'reduce_data': True}

# Short satellite names. These cannot contain a hyphen '-'. Only GEO sats are used in this module.
sat_list = ['GOES16', 'GOES17', 'GOES18', 'HIMA8', 'MSG2', 'MSG3', 'MSG4', 'MetopB', 'MetopC',
            'MetopX', 'Aqua', 'Terra', 'Sen3A', 'Sen3B', 'Sen3X', 'SNPP', 'NOAA20', 'NOAAX', 'FY3D']

# Long satellite names. These are the ones in platforms.txt. Only LEO sats are used in this module.
sat_dict = {'GOES16': 'GOES-16',
            'GOES17': 'GOES-17',
            'GOES18': 'GOES-18',
            'HIMA8': 'Himawari-8',
            'MSG2': 'Meteosat-9',
            'MSG3': 'Meteosat-10',
            'MSG4': 'Meteosat-11',
            'MetopB': 'Metop-B',
            'MetopC': 'Metop-C',
            'MetopX': 'Metop-X',
            'Aqua': 'EOS-Aqua',
            'Terra': 'EOS-Terra',
            'Sen3A': 'Sentinel-3A',
            'Sen3B': 'Sentinel-3B',
            'Sen3X': 'Sentinel-3X',
            'SNPP': 'Suomi-NPP',
            'NOAA20': 'NOAA-20',
            'NOAAX': 'NOAA-X',
            'FY3D': 'FY-3D'}


# ********************************************************
# Polar orbiting satellites NOAA20, SNPP, instrument viirs
# ********************************************************

JPSSsats = ['NOAA20', 'SNPP', 'NOAAX']

viirs_list = ['DNB', 'M01', 'M02', 'M03', 'M04', 'M05', 'M06', 'M07', 'M08',
              'M09', 'M10', 'M11', 'M12', 'M13', 'M14', 'M15', 'M16']

viirs_dict = { \
    # Single viirs channels
    'DNB': ['DNB'],
    'M01': ['M01'],
    'M02': ['M02'],
    'M03': ['M03'],
    'M04': ['M04'],
    'M05': ['M05'],
    'M06': ['M06'],
    'M07': ['M07'],
    'M08': ['M08'],
    'M09': ['M09'],
    'M10': ['M10'],
    'M11': ['M11'],
    'M12': ['M12'],
    'M13': ['M13'],
    'M14': ['M14'],
    'M15': ['M15'],
    'M16': ['M16'],
    # Defined viirs composites
    'adaptive_dnb': ['DNB'],
    'ash': ['M14', 'M15', 'M16'],
    'cloudtop_daytime': ['M12', 'M15', 'M16'],
    'dust': ['M14', 'M15', 'M16'],
    'dynamic_dnb': ['DNB'],
    'false_color': ['M05', 'M07', 'M11'],
    'fire_temperature': ['M10', 'M11', 'M12'],
    'fire_temperature_39refl': ['M10', 'M11', 'M12', 'M15'],
    'fire_temperature_awips': ['M10', 'M11', 'M12'],
    'fire_temperature_eumetsat': ['M10', 'M11', 'M12'],
    'fog': ['M14', 'M15', 'M16'],
    'green_snow': ['DNB', 'M10', 'M15'],
    'histogram_dnb': ['DNB'],
    'hncc_dnb': ['DNB'],
    'ir108_3d': ['M15'],
    'ir_cloud_day': ['M15'],
    'natural_color': ['M05', 'M07', 'M10'],
    'natural_color_raw': ['DNB', 'M07', 'M10'],         # Cannot work
    'natural_color_sun_lowres': ['M05', 'M07', 'M10'],
    'natural_enh': ['DNB', 'M10'],                      # Cannot work
    'natural_with_night_fog': ['M05', 'M07', 'M10', 'M12', 'M15', 'M16'],
    'night_fog': ['M12', 'M15', 'M16'],
    'night_microphysics': ['DNB', 'M12', 'M15'],
    'night_overview': ['DNB', 'M15'],
    'ocean_color': ['M03', 'M04', 'M05'],
    'overview': ['M05', 'M07', 'M15'],
    'overview_raw': ['DNB', 'M15'],
    'snow_age': ['M07', 'M08', 'M09', 'M10', 'M11'],
    'snow_lowres': ['M07', 'M10', 'M12', 'M15'],
    'true_color': ['M03', 'M04', 'M05'],
    'true_color_crefl': ['M03', 'M04', 'M05'],
    'true_color_lowres': ['M03', 'M04', 'M05'],
    'true_color_lowres_crefl': ['M03', 'M04', 'M05'],
    'true_color_lowres_land': ['M03', 'M04', 'M05'],
    'true_color_lowres_marine_tropical': ['M03', 'M04', 'M05'],
    'true_color_raw': ['M03', 'M04', 'M05']
    }

# Some composite names are too long for IM annotation left of pic
viirs_abbr = { \
    'adaptive_dnb': ('adaptive_dnb', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'ash': ('ash', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'cloudtop_daytime': ('cloudtop_day', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'dust': ('dust', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'dynamic_dnb': ('dynamic_dnb', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'false_color': ('false_color', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'fire_temperature': ('fire_tem', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'fire_temperature_39refl': ('fire_tem_39r', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'fire_temperature_awips': ('fire_tem_awi', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'fire_temperature_eumetsat': ('fire_tem_eum', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'fog': ('fog', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'green_snow': ('green_snow', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'histogram_dnb': ('histo_dnb', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'hncc_dnb': ('hncc_dnb', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'ir108_3d': ('ir108_3d', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'ir_cloud_day': ('ir_cloud_day', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'natural_color': ('natural_color', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'natural_color_raw': ('nat_col_r', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'natural_color_sun_lowres': ('nat_col_sl', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'natural_enh': ('natural_enh', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'natural_with_night_fog': ('natural_wnf', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'night_fog': ('night_fog', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'night_microphysics': ('night_mp', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'night_overview': ('nig_overview', 3, 0, 0, 0, 0, 0, 0, 0, 0),
    'ocean_color': ('ocean_color', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'overview': ('overview', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'overview_raw': ('overview_raw', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'snow_age': ('snow_age', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'snow_lowres': ('snow_lowres', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'true_color': ('true_color', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'true_color_crefl': ('true_col_c', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'true_color_lowres': ('true_col_l', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'true_color_lowres_crefl': ('true_col_lc', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'true_color_lowres_land': ('true_col_ll', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'true_color_lowres_marine_tropical': ('true_col_lmt', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'true_color_raw': ('true_col_r', 0, 0, 0, 0, 0, 0, 0, 0, 0)
    }

# ***************************************************************
# Polar orbiting satellites EOP-Aqua, EOP-Terra, instrument modis
# ***************************************************************

# MODIS has 36 channels 1-20 reflection + 16 thermal:
# Below are the channels/datasets we get on EUMETCast

EOPsats = ['Aqua', 'Terra']

modis_list = ['1', '2', '5', '6', '8', '9', '10', '12', '15',
              '20', '23', '26', '27', '28', '29', '31', '32', '33']

modis_dict = { \
    # Single modis channels
    '1': ['1'],
    '2': ['2'],
    '5': ['5'],
    '6': ['6'],
    '8': ['8'],
    '9': ['9'],
    '10': ['10'],
    '12': ['12'],
    '15': ['15'],
    '20': ['20'],
    '23': ['23'],
    '26': ['26'],
    '27': ['27'],
    '28': ['28'],
    '29': ['29'],
    '31': ['31'],
    '32': ['32'],
    '33': ['33'],
    # Defined modis composites
    'ash': ['29', '31', '32'],
    'day_microphysics': ['1', '2', '20', '31', '33'],
    'dust': ['29', '31', '32'],
    'fog': ['29', '31', '32'],
    'green_snow': ['1', '6', '31'],
    'ir108_3d': ['31'],
    'ir_cloud_day': ['31'],
    'natural_color': ['1', '2', '6'],
    'natural_color_raw': ['1', '2', '6'],
    'natural_with_night_fog': ['1', '2', '6', '20', '31', '32'],
    'night_fog': ['20', '31', '32'],
    'overview': ['1', '2', '31'],
    'snow': ['1', '2', '6', '20', '31', '33'],
    'true_color_thin': ['1', '10', '12']
    }

# Some composite names are too long for IM annotation left of pic
modis_abbr = { \
    'ash': ('ash', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'day_microphysics': ('day_mp', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'dust': ('dust', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'fog': ('fog', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'green_snow': ('green_snow', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'ir108_3d': ('ir108_3d', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'ir_cloud_day': ('ir_cloud_day', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'natural_color': ('natural_color', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'natural_color_raw': ('nat_col_raw', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'natural_with_night_fog': ('natural_wnf', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'night_fog': ('night_fog', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'overview': ('overview', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'snow': ('snow', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'true_color_thin': ('true_col_thin', 0, 0, 0, 0, 0, 0, 0, 0, 1)
    # A huge effort to make this 'true_col_thin' run again ...
    }

# **********************************************************
# Polar orbiting (chinese) satellite FY3D, instrument mersi2
# **********************************************************
# All 25 FY3D mersi2 channels are available on EUMETCast !!!

FYsats = ['FY3D']

mersi2_list = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12', '13',
               '14', '15', '16', '17', '18', '19', '20', '21', '22', '23', '24', '25']
mersi2_dict = { \
    # Single mersi2 channels
    '1': ['1'],
    '2': ['2'],
    '3': ['3'],
    '4': ['4'],
    '5': ['5'],
    '6': ['6'],
    '7': ['7'],
    '8': ['8'],
    '9': ['9'],
    '10': ['10'],
    '11': ['11'],
    '12': ['12'],
    '13': ['13'],
    '14': ['14'],
    '15': ['15'],
    '16': ['16'],
    '17': ['17'],
    '18': ['18'],
    '19': ['19'],
    '20': ['20'],
    '21': ['21'],
    '22': ['22'],
    '23': ['23'],
    '24': ['24'],
    '25': ['25'],
    # Defined mersi2 composites
    'ash': ['23', '24', '25'],
    'cloudtop': ['20', '24', '25'],
    'day_microphysics': ['15', '20', '24'],
    'dust': ['23', '24', '25'],
    'fog': ['23', '24', '25'],
    'green_snow': ['3', '6', '24'],
    'ir108_3d': ['24'],
    'ir_cloud_day': ['24'],
    'natural_color': ['3', '4', '6', '15'],
    'natural_color_lowres': ['6', '12', '15'],
    'natural_color_raw': ['3', '4', '6'],
    'natural_with_night_fog': ['3', '4', '6', '15', '20', '24', '25'],
    'night_fog': ['20', '24', '25'],
    'overview': ['12', '15', '24'],
    'overview_raw': ['12', '15', '24'],
    'true_color': ['1', '2', '3'],
    'true_color_raw': ['1', '2', '3']
    }

# Some composite names are too long for IM annotation left of pic
mersi2_abbr = { \
    'ash': ('ash', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'cloudtop': ('cloudtop', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'day_microphysics': ('day_mp', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'dust': ('dust', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'fog': ('fog', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'green_snow': ('green_snow', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'ir108_3d': ('ir108_3d', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'ir_cloud_day': ('ir_cloud_day', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'natural_color': ('natural_color', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'natural_color_lowres': ('nat_col_l', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'natural_color_raw': ('nat_col_raw', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'natural_with_night_fog': ('natural_wnf', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'night_fog': ('night_fog', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'overview': ('overview', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'overview_raw': ('overview_raw', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'true_color': ('true_color', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'true_color_raw': ('true_col_raw', 0, 0, 0, 0, 0, 0, 0, 0, 0)
    }

# **********************************************************
# Polar orbiting satellites MetopB, MetopC, instrument avhrr
# **********************************************************
# Metop AVHRR will be deprecated soon, Metop 2nd gen comming
# Channel 3a is daylight only, channel 3b is at night only!!

EPSsats = ['MetopB', 'MetopC', 'MetopX']

avhrr_list = ['1', '2', '3a', '3b', '4', '5']

avhrr_dict = { \
    # Single avhrr channels
    '1': ['1'], '2': ['2'], '3a': ['3a'], '3b': ['3b'], '4': ['4'], '5': ['5'],
    # Defined avhrr composites
    'cloud_phase_distinction': ['1', '3a', '4'],
    'cloud_phase_distinction_raw': ['1', '3a', '4'],
    'cloudtop': ['3b', '4', '5'],
    'day_microphysics': ['2', '3b', '4'],     # Cannot work
    'green_snow': ['1', '3a', '4'],
    'ir108_3d': ['4'],
    'ir_cloud_day': ['4'],
    'natural_color': ['1', '2', '3a'],
    'natural_color_raw': ['1', '2', '3a'],
    'natural_enh': ['1', '2', '3a'],
    'natural_with_night_fog': ['1', '2', '3a', '3b', '4', '5'],
    'night_fog': ['3b', '4', '5'],
    'night_microphysics': ['3b', '4', '5'],
    'overview': ['1', '2', '4'],
    'overview_raw': ['1', '2', '4'],
    'snow': ['2', '3a', '3b', '4']            # Cannot work
    }

# Some composite names are too long for IM annotation left of pic
avhrr_abbr = { \
    'cloud_phase_distinction': ('cloud_phd', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'cloud_phase_distinction_raw': ('cloud_phdr', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'cloudtop': ('cloudtop', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'day_microphysics': ('day_mp', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'green_snow': ('green_snow', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'ir108_3d': ('ir108_3d', 0, 0, 0, 0, 0, 0, 0, 0, 1),
    'ir_cloud_day': ('ir_cloud_day', 0, 0, 0, 0, 0, 0, 0, 0, 1),
    'natural_color': ('natural_color', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'natural_color_raw': ('nat_col_raw', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'natural_enh': ('natural_enh', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'natural_with_night_fog': ('natural_wnf', 0, 0, 0, 0, 0, 0, 0, 0, 1),
    'night_fog': ('night_fog', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'night_microphysics': ('night_mp', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'overview': ('overview', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'overview_raw': ('overview_raw', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'snow': ('snow', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    # Added for Metop NWCSAF
    'cloudtype': ('cloudtype', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'cloud_top_pressure': ('cloud_top_p', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'cloud_top_temperature': ('cloud_top_t', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'cloudmask': ('cloudmask', 0, 0, 0, 0, 0, 0, 0, 0, 0)
    }


# ********************************************************
# Polar orbiting EU satellites Sentinel-3X instrument olci
# ********************************************************
# All 21 Sen3X olci channels are available on EUMETCast !!
# OLCI is a daylight instrument, no data on the dark side.

SENsats = ['Sen3A', 'Sen3B', 'Sen3X']

olci_list = ['Oa01', 'Oa02', 'Oa03', 'Oa04', 'Oa05', 'Oa06', 'Oa07',
             'Oa08', 'Oa09', 'Oa10', 'Oa11', 'Oa12', 'Oa13', 'Oa14',
             'Oa15', 'Oa16', 'Oa17', 'Oa18', 'Oa19', 'Oa20', 'Oa21' ]


# member_files = ['geo_coordinates.nc', 'instrument_data.nc', 'qualityFlags.nc', 'tie_geo_coordinates.nc',
#                 'tie_geometries.nc', 'tie_meteo.nc', 'time_coordinates.nc', xdumanifest.xml]

# Minimum needed *.nc datasets for the composites below. For OLCI defined composites 08 06 03!
member_files = ['tie_meteo.nc', 'tie_geometries.nc','geo_coordinates.nc', 'instrument_data.nc',
                'Oa01_radiance.nc', 'Oa02_radiance.nc', 'Oa03_radiance.nc',
                'Oa04_radiance.nc', 'Oa05_radiance.nc', 'Oa06_radiance.nc',
                'Oa07_radiance.nc', 'Oa08_radiance.nc', 'Oa09_radiance.nc',
                'Oa10_radiance.nc', 'Oa11_radiance.nc', 'Oa12_radiance.nc',
                'Oa13_radiance.nc', 'Oa14_radiance.nc', 'Oa15_radiance.nc',
                'Oa16_radiance.nc', 'Oa17_radiance.nc', 'Oa18_radiance.nc',
                'Oa19_radiance.nc', 'Oa20_radiance.nc', 'Oa21_radiance.nc']

olci_dict = { \
    # Single olci channels
    'Oa01': ['Oa01'],
    'Oa02': ['Oa02'],
    'Oa03': ['Oa03'],
    'Oa04': ['Oa04'],
    'Oa05': ['Oa05'],
    'Oa06': ['Oa06'],
    'Oa07': ['Oa07'],
    'Oa08': ['Oa08'],
    'Oa09': ['Oa09'],
    'Oa10': ['Oa10'],
    'Oa11': ['Oa11'],
    'Oa12': ['Oa12'],
    'Oa13': ['Oa13'],
    'Oa14': ['Oa14'],
    'Oa15': ['Oa15'],
    'Oa16': ['Oa16'],
    'Oa17': ['Oa17'],
    'Oa18': ['Oa18'],
    'Oa19': ['Oa19'],
    'Oa20': ['Oa20'],
    'Oa21': ['Oa21'],
    # Defined olci composites
    'ocean_color': ['Oa03', 'Oa06', 'Oa08'],
    'true_color': ['Oa03', 'Oa06', 'Oa08'],
    'true_color_desert': ['Oa03', 'Oa06', 'Oa08'],
    'true_color_land': ['Oa03', 'Oa06', 'Oa08'],
    'true_color_marine_clean': ['Oa03', 'Oa06', 'Oa08'],
    'true_color_marine_tropical': ['Oa03', 'Oa06', 'Oa08'],
    'true_color_raw': ['Oa03', 'Oa06', 'Oa08'],
     # These moisture composites are taken in from visir.yaml
     # They have been setup by looking at channel wavelengths
    'day_essl_colorized_low_level_moisture': ['Oa17', 'Oa19'],
    'day_essl_low_level_moisture': ['Oa17', 'Oa19'],
    'essl_colorized_low_level_moisture': ['Oa17', 'Oa19'],
    'essl_low_level_moisture': ['Oa17', 'Oa19'],
    # These composites have been used by several power users
    # They have been defined in a private user configuration
    # See the thread https://groups.io/g/MSG-1/message/30626
    # They all use (additional) '0a08' for Satpy enhancement
    'ernst100603n': ['Oa03', 'Oa06', 'Oa08', 'Oa10'],
    'ernst100603o': ['Oa03', 'Oa06', 'Oa08', 'Oa10'],
    'ernst100603t': ['Oa03', 'Oa06', 'Oa08', 'Oa10'],
    'simon080503n': ['Oa03', 'Oa05', 'Oa08'],
    'simon080503o': ['Oa03', 'Oa05', 'Oa08'],
    'simon080503t': ['Oa03', 'Oa05', 'Oa08'],
    'david090604n': ['Oa04', 'Oa06', 'Oa08', 'Oa09'],
    'david090604o': ['Oa04', 'Oa06', 'Oa08', 'Oa09'],
    'david090604t': ['Oa04', 'Oa06', 'Oa08', 'Oa09'],
    'hugo211709n': ['Oa08', 'Oa09', 'Oa17', 'Oa21'],
    'hugo211709o': ['Oa08', 'Oa09', 'Oa17', 'Oa21'],
    'hugo211709t': ['Oa08', 'Oa09', 'Oa17', 'Oa21'],
    'satpy080603n': ['Oa03', 'Oa06', 'Oa08'],
    'satpy080603o': ['Oa03', 'Oa06', 'Oa08'],
    'satpy080603t': ['Oa03', 'Oa06', 'Oa08']
    }

# Some composite names are too long for IM annotation left of pic
olci_abbr = { \
    'ocean_color': ('ocean_color', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'true_color': ('true_color', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'true_color_desert': ('true_col_de', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'true_color_land': ('true_col_la', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'true_color_marine_clean': ('true_col_mc', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'true_color_marine_tropical': ('true_col_mt', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'true_color_raw': ('true_col_raw', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'day_essl_colorized_low_level_moisture': ('decll_moist', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'day_essl_low_level_moisture': ('dell_moist', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'essl_colorized_low_level_moisture': ('ecll_moist', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'essl_low_level_moisture': ('ell_moist', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'ernst100603n': ('ernst100603n', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'ernst100603o': ('ernst100603o', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'ernst100603t': ('ernst100603t', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'simon080503n': ('simon080503n', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'simon080503o': ('simon080503o', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'simon080503t': ('simon080503t', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'david090604n': ('david090604n', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'david090604o': ('david090604o', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'david090604t': ('david090604t', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'hugo211709n': ('hugo211709n', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'hugo211709o': ('hugo211709o', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'hugo211709t': ('hugo211709t', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'satpy080603n': ('satpy080603n', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'satpy080603o': ('satpy080603o', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'satpy080603t': ('satpy080603t', 0, 0, 0, 0, 0, 0, 0, 0, 0)
    }



def get_long_name(sat):
    satellite = sat_dict.get(sat, 'Unkown')
    return satellite


def test_argv():

    # Get satellite short name
    sat = os.path.basename(sys.argv[0])
    sat = sat.split('-')[0]
    if not sat in sat_list:
       sat = sat.split('.')[0]
       if not sat in sat_list:
          sys.exit('Satellite \''+sat+'\' unknown, check naming convention ...')

    # Minimal command line parameter test
    usage = sys.argv[0] + ' expects YYYYmmddNoD as CLI parameter:\n' \
          + 'NoD must either be NIG (night pass) or DAY (daylight pass).\n' \
          + 'See comment concerning EUMETCast in the script header.'
    if len(sys.argv) != 2:
        sys.exit(usage)
    if len(sys.argv[1]) != 11:
        sys.exit(usage)

    # YYYYmmDD & NIG/DAY
    Dat = sys.argv[1][:8]
    NoD = sys.argv[1][8:]

    if NoD != 'NIG' and NoD != 'DAY':
        sys.exit(usage)

    # Get substrings
    Yea=Dat[:4]
    Mon=Dat[4:6]
    Day=Dat[6:]

    return  sat, Dat, Yea, Mon, Day, NoD


def init_tmp(sat, area, testrun):
    # Set tmp directory and change to it
    if not sat in sat_list:
        sys.exit('Satellite short name must be in', sat_list)
    if testrun:
        tmpdir = tmpdirs + '/xtest'
    else:
        tmpdir = tmpdirs + '/x' + sat.lower()
    # Directory must exist
    try:
       os.chdir(tmpdir)
    except:
       sys.exit('Cannot change to tmp directory ' + tmpdir + ' ...')
    os.system(remove + sat + '-*-' + area + '.png')


# ---------------------------------------------------------------------------------------------------

def arc_distance(lon, lat, clon, clat):
    # Degrees to radian
    dr = pi/180.0
    sinlat = sin(lat*dr)
    coslat = cos(lat*dr)
    # Use Nautical Triangle, return arc distance from center of map (POI) to corners in degrees
    cosarc = sinlat * sin(clat*dr) +  coslat * cos(clat*dr) * cos((lon-clon)*dr)
    return acos(cosarc)/dr

def get_lon_lat_ran(area):

    # area is str from areas.yaml
    area_def = get_area_def(area)
    prj = Proj(area_def.crs if hasattr(area_def, 'crs') else area_def.proj_str)
    # prj = Proj(area_def.proj_str)    # Is this all I need ... ?
    x_ll, y_ll = area_def.area_extent[0], area_def.area_extent[1]
    x_ur, y_ur = area_def.area_extent[2], area_def.area_extent[3]
    x, y = (x_ur + x_ll) / 2, (y_ur + y_ll) / 2

    # From lower left corner CW corners 1->2->3->4
    lon_c1, lat_c1 = prj(x_ll, y_ll, inverse=True)
    lon_c2, lat_c2 = prj(x_ll, y_ur, inverse=True)
    lon_c3, lat_c3 = prj(x_ur, y_ur, inverse=True)
    lon_c4, lat_c4 = prj(x_ur, y_ll, inverse=True)
    lon, lat = prj(x, y, inverse=True)  # Our POI

    # Inverse projection may give inf
    if lon_c1 > 1000: lon_c1 = -180.0
    if lat_c1 > 1000: lat_c1 =  -90.0
    if lon_c2 > 1000: lon_c2 = -180.0
    if lat_c2 > 1000: lat_c2 =   90.0
    if lon_c3 > 1000: lon_c3 =  180.0
    if lat_c3 > 1000: lat_c3 =   90.0
    if lon_c4 > 1000: lon_c4 =  180.0
    if lat_c4 > 1000: lat_c4 =  -90.0
    if lon > 1000: lon = 0.0
    if lat > 1000: lat = 0.0

    fac = 1.5
    d1 = fac * arc_distance(lon, lat, lon_c1, lat_c1)
    d2 = fac * arc_distance(lon, lat, lon_c2, lat_c2)
    d3 = fac * arc_distance(lon, lat, lon_c3, lat_c3)
    d4 = fac * arc_distance(lon, lat, lon_c4, lat_c4)

    ran = min(50.0, max(d1, d2, d3, d4, 10.0))

    return lon, lat, ran  # () not necessary?!

# ---------------------------------------------------------------------------------------------------


def abbreviated(name):  # This is a "botch" that might work :-\
    MAXLEN = 12
    if len(name) <= MAXLEN:
        return name
    if '_' in name:
        i = 0
        s =name[i]
        while i < len(name) - 1:
            if name[i] == '_' and name[i + 1] != '_':
                s += name[i + 1]
            i += 1
        return s
    return name[:MAXLEN-2] + '..'

# fcomposites work with scene.load(..., generate=False), which is faster
# tcomposites must have scene.load(..., generate=True) (default), slower
# For LEO satellites we generally set the fill values to black (for now)
def get_ft_composites(sat, composites):
    fcomposites=[]
    tcomposites=[]
    # If key composite does not exist default to tcomposites
    if sat in JPSSsats:
        for composite in composites:
            if composite in viirs_abbr:
                if viirs_abbr[composite][9]:
                    tcomposites.append(composite)
                else:
                    fcomposites.append(composite)
            else:
                tcomposites.append(composite)

    elif sat in EOPsats:
        for composite in composites:
            if composite in modis_abbr:
                if modis_abbr[composite][9]:
                    tcomposites.append(composite)
                else:
                    fcomposites.append(composite)
            else:
                tcomposites.append(composite)

    elif sat in FYsats:
        for composite in composites:
            if composite in mersi2_abbr:
                if mersi2_abbr[composite][9]:
                    tcomposites.append(composite)
                else:
                    fcomposites.append(composite)
            else:
                tcomposites.append(composite)

    elif sat in EPSsats:
        for composite in composites:
            if composite in avhrr_abbr:
                if avhrr_abbr[composite][9]:
                    tcomposites.append(composite)
                else:
                    fcomposites.append(composite)
            else:
                tcomposites.append(composite)

    elif sat in SENsats:
        for composite in composites:
            if composite in olci_abbr:
                if olci_abbr[composite][9]:
                    tcomposites.append(composite)
                else:
                    fcomposites.append(composite)
            else:
                tcomposites.append(composite)

    return fcomposites, tcomposites


# ***************************************************************************************
# BEGIN: That's where you can define your own special overlays per instrument + composite
# ***************************************************************************************

# 0) The number 0 of the tuple is a composite abbreviated

# 1) You can define 1 - 9 types of coastline update dicts
coasts1 = {'outline': (0, 0, 0), 'width': 2.5}
coasts2 = {'outline': (100, 100, 100), 'width': 2.5}
coasts3 = {'outline': 'green'}
coasts_upd = [coasts1, coasts2, coasts3]

# 2) You can define 1 - 9 types of borders update dicts
borders1 = {}
borders2 = {}
borders_upd =[]

# 3) You can define 1 - 9 types of rivers update dicts
rivers1 = {}
rivers2 = {}
rivers_upd=[]

# 4) You can define 1 - 9 types of lakes update dicts
lakes1 = {}
lakes2 = {}
lakes_upd=[]

# 5) You can define 1 - 9 types of grid update dicts
grid1 = {'outline': (0, 0, 0), 'minor_outline': (0, 0, 0), 'fill': (0, 0, 0)}
grid2 = {'outline': 'blue', 'minor_outline': 'red', 'fill': 'yellow'}
grid_upd = [grid1, grid2]

# 6) You can define 1 - 9 types of cities update dicts
cities1 = {}
cities2 = {}
cities_upd=[]

# 7) You can define 1 - 9 types of points update dicts
points1 = {}
points2 = {}
points_upd=[]

# 8) You can define 1 - 9 types of station update dicts
station1 = {}
station2 = {}
station_upd=[]

# ***************************************************************************************
# END: For special overlays per instrument + composite. Do also update instrument_abbr[]!
# ***************************************************************************************

def get_abbr(sat, composite):
    # If key composite does not exist default to abbreviated(composite)
    if sat in JPSSsats and composite in viirs_abbr:
        comp = viirs_abbr[composite][0]
    elif sat in EOPsats and composite in modis_abbr:
        comp = modis_abbr[composite][0]
    elif sat in EPSsats and composite in avhrr_abbr:
        comp = avhrr_abbr[composite][0]
    elif sat in SENsats and composite in olci_abbr:
        comp = olci_abbr[composite][0]
    elif sat in FYsats and composite in mersi2_abbr:
        comp = mersi2_abbr[composite][0]
    else:
        comp = abbreviated(composite)
    return comp

def get_index(sat, composite, i):
    # If key composite does not exist default to index = 0
    if sat in JPSSsats and composite in viirs_abbr:
        return  viirs_abbr[composite][i]
    elif sat in EOPsats and composite in modis_abbr:
        return  modis_abbr[composite][i]
    elif sat in EPSsats and composite in avhrr_abbr:
        return  avhrr_abbr[composite][i]
    elif sat in SENsats and  composite in olci_abbr:
        return  olci_abbr[composite][i]
    elif sat in FYsats and  composite in mersi2_abbr:
        return  mersi2_abbr[composite][i]
    else:
        return 0

# Use foo.update() method of dicts, j=1..8 (9 = generate)
def update_foo(sat, composite, foo, foo_upd, j):
    i = get_index(sat, composite, j)
    if i < 1 or i > len(foo_upd): return foo
    foo.update(foo_upd[i-1])
    return foo


def get_overlays(sat, composite, area, area_cities, height, width, ADDcoasts, ADDborders, ADDrivers, ADDlakes,
                     ADDgrid, ADDcities, ADDpoints, ADDstation, OVRcache, testrun):  # Maybe add **kwargs ??

    # The below sequence of overlay parts is how pycoast writes the different components on top of each other.
    # Cities, points and text are written last because we don't want to scratch their labels with other lines.

    # General floating point scale factor (sf) for adapting line width(s), fonts, labels, symbols, etc., ...
    sf = (height + width) / 3000

    # Colors are specified as strings (140 HTML color names) or as triple (R, G, B) 8Bit.
    # Best 'resolution' is automatically chosen according to area_def, no need to touch.
    # Coasts also has keys ..,'fill': 'green', 'fill_opacity': 50} for land mass filling.
    # 'level' defaults to 1 but should be chosen at least 2 for rivers (1 = 0 in GSHHG).
    # 'level': 3 will plot 3, 2, 1. But Pycoast accepts level lists like 'level': [1, 6].
    my_coasts  = {'outline': (255, 255,   0), 'outline_opacity': 255, 'width': 1.5*sf, 'level': 1} # level 1 .. 6
    my_borders = {'outline': (255,   0,   0), 'outline_opacity': 255, 'width': 1.0*sf, 'level': 1} # level 1 .. 3
    my_rivers  = {'outline': (  0,   0, 255), 'outline_opacity': 255, 'width': 1.0*sf, 'level': 3} # level 1 .. 11

    # For ShapeType polygon you can use 'fill', 'fill_opacity' like with coastlines
    # We misuse key 'shapefiles' to fill minor lakes / Christian might do otherwise
    # Maybe we could still automatically adapt resolution of GSHHS_?_L2.shp misused
    my_lakes = {'filename': geodata + '/GSHHS_shp/f/GSHHS_f_L2.shp',
                'outline': 'blue', 'outline_opacity': 255, 'width': 0.5*sf,
                'fill': 'blue', 'fill_opacity': 50}

    # This dict interface to pycoast was integrated 2020 and has been enhanced 2022
    # among other things with 'fill' and 'fill_opacity' that works for grid labels!
    my_grid  = {'major_lonlat': (10,10), 'minor_lonlat': (2, 2),
                # Opacity 0 will hide the line, values 0 ... 255  EL
                'outline': (255, 255, 255) , 'outline_opacity': 255,
                'minor_outline': (200, 200, 200),'minor_outline_opacity': 127,
                'width': 1.5*sf, 'minor_width': 1.0*sf, 'minor_is_tick': False,
                'write_text': True, 'lat_placement': 'lr', 'lon_placement': 'b',
                'font': fontdir + '/DejaVuSerif.ttf',
                'fill': 'white', 'fill_opacity': 255, 'font_size': 30*sf}
                # minor_is_tick: False draws a line not ticks, True does ticks
                # label placement l,r,lr for latitude and t,b,tb for longitude


    # Add your own cities or even make my_cities_dict/list area dependant
    default_cities = ['Berlin', 'London', 'Paris', 'Madrid', 'Rome',
                      'Cairo', 'Cape Town', 'Herat', 'Kabul', 'New Delhi',
                      'New York City', 'Chicago', 'Mexico City', 'Sao Paulo',
                      'Los Angeles', 'Honolulu', 'Tokyo']

    if area_cities:
        my_cities_list = area_cities
    else:
        my_cities_list = default_cities

    my_cities = {'font': fontdir + '/DejaVuSerif.ttf',
                 'font_size': 20*sf, 'cities_list': my_cities_list, 'symbol': 'circle',
                 'ptsize': 20*sf, 'outline': 'black', 'fill': 'red', 'width': 3.0*sf,
                 'outline_opacity': 255,'fill_opacity': 255, 'box_outline': 'black',
                 'box_linewidth': 3.0*sf, 'box_fill': 'gold', 'box_opacity': 255}


    # List of EARS Stations, Longitude E+ W-, Latitude N+ S- taken from url
    # https://directory.eoportal.org/web/eoportal/satellite-missions/e/ears
    my_poi_list = [((-113.50, 53.33), 'Edmonton'),
                   (( -54.57, 48.95), 'Gander'),
                   ((-147.40, 64.97), 'Gilmore Creek'),
                   ((-121.55, 36.35), 'Monterey'),
                   (( -80.16, 25.74), 'Miami'),
                   (( -75.30, 37.80), 'Wallops'),
                   (( -15.63, 27.78), 'Maspalomas'),
                   (( -50.67, 66.98), 'Kangerlussuaq'),
                   ((  15.23, 78.13), 'Svalbard'),
                   ((  23.77, 37.82), 'Athens'),
                   ((  -3.46, 48.75), 'Lannion'),
                   ((  55.50,-20.91), 'Saint-Denis (La Réunion)'),
                   ((  37.57, 55.76), 'Moscow'),
                   ((  58.29, 23.59), 'Muscat')]

    # You may find other True Type Fonts (*.ttf) in /usr/share/fonts/truetype/...
    # Windows 10 PRO users may find more True Type Fonts in C:\Windows\Fonts\ ...
    my_points = {'font': fontdir + '/DejaVuSerif.ttf',
                 'font_size': 20*sf, 'points_list': my_poi_list, 'symbol': 'star5',
                 'ptsize': 30*sf, 'outline': 'black', 'fill': 'cyan', 'width': 4.0*sf,
                 'outline_opacity': 255,'fill_opacity': 255, 'box_outline': 'black',
                 'box_linewidth': 3.0*sf, 'box_fill': 'white', 'box_opacity': 255}


    my_station = {'font': fontdir + '/DejaVuSerif.ttf',
                  'font_size': 20*sf, 'points_list': my_coordinates, 'symbol': 'triangle',
                  'ptsize': 35*sf, 'outline': 'white', 'fill': 'green', 'width': 2.0*sf,
                  'outline_opacity': 255,'fill_opacity': 255, 'box_outline': 'white',
                  'box_linewidth': 2.0*sf, 'box_fill': 'blue', 'box_opacity': 255}

    # OVR cache is useful for speedup. Overlays are stored as transparent *.png per sat!
    if testrun:
        my_cache = {'file': cachdir + '/ctest/' + area, 'regenerate': False}
    else:
        my_cache = {'file': cachdir + '/c' + sat.lower() + '/' + area, 'regenerate': False}

    # Setup individual overlays dictionary / default components can be composite adapted
    my_overlays = {}
    if ADDcoasts:  # Add key coasts
        my_overlays['coasts'] = update_foo(sat, composite, my_coasts, coasts_upd, 1)
    if ADDborders: # Add key borders
        my_overlays['borders'] = update_foo(sat, composite, my_borders, borders_upd, 2)
    if ADDrivers:  # Add key rivers
        my_overlays['rivers'] = update_foo(sat, composite, my_rivers, rivers_upd, 3)
    if ADDlakes:   # Add key lakes
        my_overlays['shapefiles'] = update_foo(sat, composite, my_lakes, lakes_upd, 4)
    if ADDgrid:    # Add key grid
        my_overlays['grid'] = update_foo(sat, composite, my_grid, grid_upd, 5)
    if ADDcities:  # Add key cities
        my_overlays['cities'] = update_foo(sat, composite, my_cities, cities_upd, 6)
    if ADDpoints:  # Add key points
        my_overlays['points'] = update_foo(sat, composite, my_points, points_upd, 7)
    if ADDstation: # Add key text
        my_overlays['text'] = update_foo(sat, composite, my_station, station_upd, 8)
    if OVRcache:   # Add key cache
        my_overlays['cache'] = my_cache

    return my_overlays

# ---------------------------------------------------------------------------------------------------

def get_hasdoy_pat_offs_dpat_hyp_suff_dsec(sat, decomp, reader):
# Use sat/reader for cases where one sat has different products

    # Swath image size is 3200 X (768) * NumberOfSegments (MX-Bands)
    # Swath image size is 4064 X (768) * NumberOfSegments (DNB-Band)
    # Segments are 85 - 86 seconds, advance to the center (+43 sec)
    if sat == 'NOAA20':
        return False, 'SV*C_j01_d', -66, -50, '%Y%m%d_t%H%M%S', '_t', '_ops.h5', 43
    if sat == 'SNPP':
        return False, 'SV*C_npp_d', -66, -50, '%Y%m%d_t%H%M%S', '_t', '_ops.h5', 43

    if sat == 'MetopB':
        if reader == 'nwcsaf-pps_nc':
            # Swath image size is 2040 X (360) * NumberOfSegments (nwcsaf)
            # Segments are 60 seconds, advance to the center (+30 sec)
            if decomp:
                return False, 'W_XX-EUMETSAT*METOPB+C*', -23,  -9, '%Y%m%d%H%M%S', '', '.nc', 30
            else:
                return False, 'W_XX-EUMETSAT*METOPB+C*', -27, -13, '%Y%m%d%H%M%S', '', '.nc.bz2', 30
        else:
            # Swath image size is 2040 X (1080) * NumberOfSegments (AVHRR)
            # Segments are 180 seconds, advance to the center (+90 sec)
            if decomp:
                return False, 'AVHR_xxx_1B_M01_', -51, -37, '%Y%m%d%H%M%S', '', 'Z', 90
                # return False, 'AVHR_xxx_1B_M01_', -59, -45, '%Y%m%d%H%M%S', '', 'Z.eps-glb', 90
            else:
                return False, 'AVHR_xxx_1B_M01_', -55, -41, '%Y%m%d%H%M%S', '', 'Z.bz2', 90
    if sat == 'MetopC':
        if reader == 'nwcsaf-pps_nc':
            # Swath image size is 2040 X (360) * NumberOfSegments (nwcsaf)
            # Segments are 60 seconds, advance to the center (+30 sec)
            if decomp:
                return False, 'W_XX-EUMETSAT*METOPC+C*', -23,  -9, '%Y%m%d%H%M%S', '', '.nc', 30
            else:
                return False, 'W_XX-EUMETSAT*METOPC+C*', -27, -13, '%Y%m%d%H%M%S', '', '.nc.bz2', 30
        else:
            # Swath image size is 2040 X (1080) * NumberOfSegments (AVHRR)
            # Segments are 180 seconds, advance to the center (+90 sec)
            if decomp:
                return False, 'AVHR_xxx_1B_M03_', -51, -37, '%Y%m%d%H%M%S', '', 'Z', 90
                # return False, 'AVHR_xxx_1B_M03_', -59, -45, '%Y%m%d%H%M%S', '', 'Z.eps-glb', 90
            else:
                return False, 'AVHR_xxx_1B_M03_', -55, -41, '%Y%m%d%H%M%S', '', 'Z.bz2', 90

    # Swath image size is 1354 X (2030) * NumberOfSegments (MODIS 1km)
    # Segments are 300 seconds, advance to the center (+150 sec)
    if sat == 'Aqua':
        return True, 'thin_MYD021KM.A', -38, -26, '%Y%j.%H%M', '.', '.NRT.hdf', 150
    if sat == 'Terra':
        return True, 'thin_MOD021KM.A', -38, -26, '%Y%j.%H%M', '.', '.NRT.hdf', 150

    # Swath image size is 2048 X (400) * NumberOfSegments (MERSI2)
    # Segments are 60 seconds, advance to the center (+30 sec)
    if sat == 'FY3D':
        return False, 'FY3D_', -48, -33, '%Y%m%d_%H%M%S', '_', '_L1B.HDF', 30

    # OLCI ERR is 4x4 pixels of OLCI EFR which makes a resolution of 1200m at SSP
    # OLCI ERR is almost 1/2 orbit, 45min, 15088 X 1217 pixels, for powerful PCs!
    if sat == 'Sen3A':
        return False, 'S3A_OL_1_ERR____', -87, -72, '%Y%m%dT%H%M%S', 'T', 'SEN3.tar', 90

    if sat == 'Sen3B':
        return False, 'S3B_OL_1_ERR____', -87, -72, '%Y%m%dT%H%M%S', 'T', 'SEN3.tar', 90

    sys.exit('Satellite ' + sat + ' not yet implemented ...')


# ********************************************************************************************************
# This function allows for single pass and multi pass an elvaluation with generate=True xor generate=False.
# It had to be introduced to solve a problem with modis 'true_color_thin' that is ugly when generate=False.
# Unknown composites (e.g. user defined and named in userconfig) will all be evaluated setting generate=True.

def multi_single_pass(scn, generate, multi, sat, composites, area, area_cities, ADDcoasts, ADDborders,
                      ADDrivers, ADDlakes, ADDgrid, ADDcities, ADDpoints, ADDstation, OVRcache, testrun):

    # In case of multi=True scn is passed as mscn. It could be mscn is passed by reference and given back
    # unusable. If I call this function twice with generate=True and generate=False I must remake mscn !!

    if sat in EOPsats:  # Not sure this is still necessary ?
        scn.load(composites, resolution=1000, generate=generate)
    else:
        scn.load(composites, generate=generate)

    # Choose resampler config with **resampler_kwargs
    if multi:
        new_mscn = scn.resample(area, **resampler_kwargs)
        new_scn = new_mscn.blend()
    else:
        new_scn = scn.resample(area, **resampler_kwargs)

    try: # This is for real (multichannel) composites
        layers, height, width = new_scn[composites[0]].shape
    except: # In case of a single channel 'composite'
        height, width = new_scn[composites[0]].shape

    if generate:

        for composite in composites:
            overlays = get_overlays(sat, composite, area, area_cities, height, width, ADDcoasts,
                                    ADDborders, ADDrivers, ADDlakes, ADDgrid, ADDcities, ADDpoints, ADDstation,
                                    OVRcache, testrun)
            new_scn.save_dataset(composite, sat+'-'+composite+'-'+area+'.png', overlay={'coast_dir': geodata,
                                    'overlays': overlays}, fill_value=0)
    else:

        save_objects = []
        for composite in composites:
            my_overlays =  get_overlays(sat, composite, area, area_cities, height, width, ADDcoasts, ADDborders,
                                    ADDrivers, ADDlakes, ADDgrid, ADDcities, ADDpoints, ADDstation, OVRcache, testrun)
            save_objects.append(new_scn.save_dataset(composite, base_dir='.', filename=sat+'-{name}-'+area+'.png',
                                overlay={'coast_dir': geodata, 'overlays' : my_overlays},
                                compute=False, fill_value=0))
        compute_writer_results(save_objects)

    return height

# ********************************************************************************************************

def get_off0_pp1_pp2(Yea, Mon, Day, dt, dt1, dt2, segdir, pat, hyp, hasdoy, isbulk):

    segdir1 = segdir
    segdir2 = segdir

    if dt1.day != dt.day:
        # We also need files from yesterday
        Yea1 = dt1.strftime('%Y')
        Mon1 = dt1.strftime('%m')
        Day1 = dt1.strftime('%d')
        Yea2 = Yea
        Mon2 = Mon
        Day2 = Day
        if isbulk == False:
           segdir1 += '/' + Yea1 + '/' + Mon1 + '/' + Day1
           segdir2 += '/' + Yea2 + '/' + Mon2 + '/' + Day2
        if hasdoy:
           yesterday = dt1.strftime('%Y%j')
           today = dt.strftime('%Y%j')
        else:
           yesterday = Yea1 + Mon1 + Day1
           today = Yea2 + Mon2 + Day2
        pathpat1 = segdir1 + '/' + pat + yesterday + hyp + '2*'
        pathpat2 = segdir2 + '/' + pat + today + hyp + '0*'
    elif dt2.day != dt.day:
        # We also need files from tomorrow
        Yea1 = Yea
        Mon1 = Mon
        Day1 = Day
        Yea2 = dt2.strftime('%Y')
        Mon2 = dt2.strftime('%m')
        Day2 = dt2.strftime('%d')
        if isbulk == False:
           segdir1 += '/' + Yea1 + '/' + Mon1 + '/' + Day1
           segdir2 += '/' + Yea2 + '/' + Mon2 + '/' + Day2
        if hasdoy:
           today = dt.strftime('%Y%j')
           tomorrow = dt2.strftime('%Y%j')
        else:
           today = Yea1 + Mon1 + Day1
           tomorrow = Yea2 + Mon2 + Day2
        pathpat1 = segdir1 + '/' + pat + today + hyp + '2*'
        pathpat2 = segdir2 + '/' + pat + tomorrow + hyp + '0*'
    else:
        # All needed files are from today
        if isbulk == False:
           segdir1 += '/' + Yea + '/' + Mon + '/' + Day
        if hasdoy:
           today = dt.strftime('%Y%j')
        else:
           today = Yea + Mon + Day
        pathpat1 = segdir1 + '/' + pat + today + '*'
        pathpat2 = ''

    off0 = len(segdir1) + 1

    return off0, pathpat1, pathpat2


def get_sat_lists(sat, satellite, segdir, decomp, isbulk):

    if not isinstance(segdir, list):
        segdir = [segdir]
    if not isinstance(decomp, list):
        decomp = [decomp]
    if not isinstance(isbulk, list):
        isbulk = [isbulk]

    if sat == 'MetopX':
        sats = ['MetopB', 'MetopC']
        satellites = ['Metop-B', 'Metop-C']
        if not len(segdir) == 2:
           sys.exit('Satellite \''+sat+'\' expects a list with 2 segdirs ...')
        if not len(decomp) == 2:
           sys.exit('Satellite \''+sat+'\' expects a list with 2 decomps ...')
        if not len(isbulk) == 2:
           sys.exit('Satellite \''+sat+'\' expects a list with 2 isbulks ...')
        ns0 = 2
    elif sat == 'NOAAX':
        sats = ['NOAA20', 'SNPP']
        satellites = ['NOAA-20', 'Suomi-NPP']
        if not len(segdir) == 2:
           sys.exit('Satellite \''+sat+'\' expects a list with 2 segdirs ...')
        if not len(decomp) == 2:
           sys.exit('Satellite \''+sat+'\' expects a list with 2 decomps ...')
        if not len(isbulk) == 2:
           sys.exit('Satellite \''+sat+'\' expects a list with 2 isbulks ...')
        ns0 = 2
    elif sat == 'Sen3X':
        sats = ['Sen3A', 'Sen3B']
        satellites = ['Sentinel-3A', 'Sentinel-3B']
        if not len(segdir) == 2:
           sys.exit('Satellite \''+sat+'\' expects a list with 2 segdirs ...')
        if not len(decomp) == 2:
           sys.exit('Satellite \''+sat+'\' expects a list with 2 decomps ...')
        if not len(isbulk) == 2:
           sys.exit('Satellite \''+sat+'\' expects a list with 2 isbulks ...')
        ns0 = 2
    else:
        sats = [sat]
        satellites = [satellite]
        ns0 = 1

    return  ns0, sats, satellites, segdir, decomp, isbulk


#  0 <= Hovr < 24
def limited(t):
    while t >= 24:
        t -= 24
    while t < 0:
        t += 24
    return t

# Some more Spherical Trigonometry in Memoriam Prof. Paul Wild
# NoD == 'DAY' searches for files on the sunny side of the globe

def leo_images(Yea, Mon, Day, sat, NoD, multi, segdir, decomp, isbulk, reader, composites, area, area_cities,
               ADDcoasts, ADDborders, ADDrivers, ADDlakes,  ADDgrid, ADDcities, ADDpoints, ADDstation,
               OVRcache, testrun, **kwargs):

    # Change to tmp directory
    init_tmp(sat, area, testrun)


    # SatPy's dynamic area definitions
    if area in ['omerc_bb', 'laea_bb']:
        multi = False
        OVRcache = False
        if kwargs:
            lon = kwargs.get('lon', my_coordinates[0][0][0])
            lat = kwargs.get('lat', my_coordinates[0][0][1])
            ran = kwargs.get('ran', 20)
        else:
            lon = my_coordinates[0][0][0]
            lat = my_coordinates[0][0][1]
            ran = 20
    else:
       # Automatically get file search parameters
       lon, lat, ran = get_lon_lat_ran(area)

    # Single passes would crash
    if sat in ['MetopX', 'NOAAX', 'Sen3X']:
        multi = True

    # Time search range 1.25 - 2.50 hours [seconds] from optimum pass
    if multi:
       tsr = 9000
    else:
       tsr = 4500

    # Degrees to radian
    dr = pi/180.0

    # These are the Inclination [°] and LTAN [hours] values taken/calculated from TLE (March 28th 2022)
    # Look at these as being constants for the lifetime of the satellite (only small changes expected).
    Const = {'EOS-Aqua'   : (98.24,  13.62),
             'EOS-Terra'  : (98.14,  22.36),
             'FY-3D'      : (98.81,  13.78),
             'Metop-B'    : (98.71,  21.50),
             'Metop-C'    : (98.69,  21.52),
             'Metop-X'    : (98.70,  21.51),
             'NOAA-20'    : (98.75,  13.42),
             'Suomi-NPP'  : (98.73,  13.42),
             'NOAA-X'     : (98.74,  13.42),
             'Sentinel-1A': (98.18,  18.02),
             'Sentinel-1B': (98.18,  18.01),
             'Sentinel-2A': (98.57,  22.50),
             'Sentinel-2B': (98.57,  22.50),
             'Sentinel-3A': (98.63,  22.00),
             'Sentinel-3B': (98.62,  22.00),
             'Sentinel-3X': (98.62,  22.00)}

    satellite = get_long_name(sat)
    i = Const[satellite][0] # Inclination [°]
    LTAN = Const[satellite][1] # LTAN [Hours]

    if lat >= 180 - i:
        lat = 179.999999 - i
    if lat <= i - 180:
        lat = i - 179.999999
    dLon1  = - asin(tan(lat*dr)/tan(i*dr))/dr
    dLon2  = 180 - dLon1
    pass1  = LTAN - (lon + dLon1) / 15
    pass2  = LTAN - (lon + dLon2) / 15
    # Sort out different cases
    if LTAN > 6 and LTAN < 18:
        if NoD == 'DAY':
            Hovr = limited(pass1)
        else:
            Hovr = limited(pass2)
    else:
        if NoD == 'DAY':
            Hovr = limited(pass2)
        else:
            Hovr = limited(pass1)

    print(f'Satellite {sat:s} is expected to make an ideal {NoD:s} overhead pass in the center of area "{area:s}" at {int(Hovr):02d}:{int((Hovr%1)*60):02d} UTC.')
    print ('Add worst case EUMETCast channel timeliness + 1 hour slack to above time for scheduling images from this area!')

    dt0 = datetime(int(Yea), int(Mon), int(Day)) + timedelta(hours = Hovr)
    dt1 = dt0 - timedelta(seconds = tsr)
    dt2 = dt0 + timedelta(seconds = tsr)
    ovr = int(dt0.timestamp())

    # Use Spherical Trigonometry:
    # In Memoriam Prof. Paul Wild
    sinlat = sin(lat*dr)
    coslat = cos(lat*dr)

    satnumber = []
    goodfiles = []
    goodtimes = []
    cosmax = 0

    if sat == 'FY3D':
        # FengYun-3D is special as we have pairs of files to treat

        # Get main characteristics of files
        hasdoy, pat, off1, off2, dpat, hyp, suff, dsec  =  get_hasdoy_pat_offs_dpat_hyp_suff_dsec(sat, decomp, reader)
        # Add half a data segment [°], needed ???
        ran_plus = ran + dsec * 0.06
        cosran = cos(ran_plus * dr)
        off0, pathpat1, pathpat2 = get_off0_pp1_pp2(Yea, Mon, Day, dt0, dt1, dt2, segdir, pat, hyp, hasdoy, isbulk)
        orb = Orbital(satellite, tlefil)

        files = glob(pathpat1 + '1000M' + suff)
        geo1k = glob(pathpat1 + 'GEO1K' + suff)
        if pathpat2:
            files += glob(pathpat2 + '1000M' + suff)
            geo1k += glob(pathpat2 + 'GEO1K' + suff)

        # Find satellite position from file name
        for fname in files:
            dt = datetime.strptime(fname[off1:off2], dpat) + timedelta(seconds = dsec)
            tim = int(dt.timestamp())
            # Time overhead +/- 1.5 - 3.0 hours [sec]
            if  abs(tim - ovr) < tsr:
                # Get longitide, latitude, altitude of sat
                (slon, slat, salt) = orb.get_lonlatalt(dt)
                # Use Nautical Triangle for arc distance
                cosarc = sinlat * sin(slat*dr) + \
                         coslat * cos(slat*dr) * cos((lon-slon)*dr)
                # Within search range, maybe more than 1 orbit
                gname = fname[:-13] + 'GEO1K' + suff
                if cosarc > cosran and gname in geo1k:
                    # The one and only
                    satnumber.append(0)
                    goodfiles.append(fname)
                    goodtimes.append(tim)
                    goodfiles.append(gname)
                    goodtimes.append(tim)
                    # We want to know telmax
                    if cosarc > cosmax:
                        cosmax = cosarc
                        timmax = tim

    elif sat in SENsats:

        # Clean old stuff
        os.system(rmolci)

        # Allow for combined satellites here (Sen3A, Sen3B, Sen3X, ...)
        # **************************************************************
        # We are working with lists that all must have 1 or 2 elements
        # EXAMPLE: sat = 'Sen3X' as combination of 'Sen3A' and 'Sen3B'
        # get_hasdoy..(.., ['Sen3A', 'Sen3B'], [decomp], ..)
        # get_off0..(.., [segdir], [isbulk], ..)
        # Orbital(['Sentinel-3A', 'Sentinel-3B'])
        # Satnumber is not used here as one segment is equal to one pass

        ns0, sats, satellites, segdirs, decomps, isbulks = get_sat_lists(sat, satellite, segdir, decomp, isbulk)

        # ns0 is either 1 or 2
        for ns in range(0, ns0):

            # Get main characteristics of files
            hasdoy, pat, off1, off2, dpat, hyp, suff, dsec  = \
                get_hasdoy_pat_offs_dpat_hyp_suff_dsec(sats[ns], decomps[ns], reader)
            # Add half a data segment [°], needed ???
            ran_plus = ran + dsec * 0.06
            cosran = cos(ran_plus * dr)
            off0, pathpat1, pathpat2 = \
                get_off0_pp1_pp2(Yea, Mon, Day, dt0, dt1, dt2, segdirs[ns], pat, hyp, hasdoy, isbulks[ns])

            orb = Orbital(satellites[ns], tlefil)

            files = glob(pathpat1 + suff)
            if pathpat2:
                files += glob(pathpat2 + suff)

            # Find satellite position from file name
            for fname in files:
                dt = datetime.strptime(fname[off1:off2], dpat) + timedelta(seconds = dsec)
                tim = int(dt.timestamp())
                if  abs(tim - ovr) < tsr:
                    # These are times at segment begin (one ERR segment = 1/2 orbit!)
                    # ERR passes are 45 minutes long, track the sat in 3 minute steps
                    dMin = 0
                    cosPass = 0
                    while dMin <= 45:
                        dt += timedelta(minutes = dMin)
                        # Get longitide, latitude, altitude of sat
                        (slon, slat, salt) = orb.get_lonlatalt(dt)
                        # Use Nautical Triangle for arc distance
                        cosarc = sinlat * sin(slat*dr) + coslat * cos(slat*dr) * cos((lon-slon)*dr)
                        if cosarc > cosPass:
                            cosPass = cosarc
                            timPass = int(dt.timestamp())
                        dMin += 3
                    # Within search range, should be more than 1 pass
                    # We keep this ERR pass tared as long as possible
                    if cosPass > cosran:
                        goodfiles.append(fname)
                        goodtimes.append(timPass)
                        # We remember the best pass
                        if cosPass > cosmax:
                            cosmax = cosPass
                            timmax = timPass


    else:

        # Allow for combined satellites here (MetopX, NOAAX, MoreX? ...)
        # **************************************************************
        # We are working with lists that all must have 1 or 2 elements
        # EXAMPLE: sat = 'NOAAX' as combination of 'NOAA-20' and 'SNPP'
        # get_hasdoy..(.., ['NOAA20', 'SNPP'], [decomp], ..)
        # get_off0..(.., [segdir], [isbulk], ..)
        # Orbital(['NOAA-20', 'Suomi-NPP'])

        ns0, sats, satellites, segdirs, decomps, isbulks = get_sat_lists(sat, satellite, segdir, decomp, isbulk)

        # ns0 is either 1 or 2
        for ns in range(0, ns0):

            # Get main characteristics of files
            hasdoy, pat, off1, off2, dpat, hyp, suff, dsec  = \
                get_hasdoy_pat_offs_dpat_hyp_suff_dsec(sats[ns], decomps[ns], reader)
            # Add half a data segment [°], needed ???
            ran_plus = ran + dsec * 0.06
            cosran = cos(ran_plus * dr)
            off0, pathpat1, pathpat2 = \
                get_off0_pp1_pp2(Yea, Mon, Day, dt0, dt1, dt2, segdirs[ns], pat, hyp, hasdoy, isbulks[ns])

            orb = Orbital(satellites[ns], tlefil)

            files = glob(pathpat1 + suff)
            if pathpat2:
                files += glob(pathpat2 + suff)

            # Find satellite position from file name
            for fname in files:
                dt = datetime.strptime(fname[off1:off2], dpat) + timedelta(seconds = dsec)
                tim = int(dt.timestamp())
                # Time overhead +/- 2 hours [sec]
                if  abs(tim - ovr) < tsr:
                    # Get longitide, latitude, altitude of sat
                    (slon, slat, salt) = orb.get_lonlatalt(dt)
                    # Use Nautical Triangle for arc distance
                    cosarc = sinlat * sin(slat*dr) + coslat * cos(slat*dr) * cos((lon-slon)*dr)
                    # Within search range, maybe more than 1 orbit
                    if cosarc > cosran:
                        satnumber.append(ns)
                        goodfiles.append(fname)
                        goodtimes.append(tim)
                        # We want to know telmax
                        if cosarc > cosmax:
                            cosmax = cosarc
                            timmax = tim


    # Now use goodfiles for images
    if goodfiles == []:
        sys.exit('Sorry, no good files found ...')

    # Get useful info back from timmax :
    # Date round midnight may change too
    dt = datetime.fromtimestamp(timmax)
    orbmax = orb.get_orbit_number(dt)
    Yea = dt.strftime('%Y')
    Mon = dt.strftime('%m')
    Day = dt.strftime('%d')
    Hou = dt.strftime('%H')
    Min = dt.strftime('%M')

    # Separate fcomposites and tcomposites
    fcomposites, tcomposites = get_ft_composites(sat, composites)


    if multi:
        # Multiple passes of either ONE satellite or TWO (twin) 180° out of phase satellites

        if sat in EPSsats:
            # Clean old stuff in tmp directory
            # Allow for both MetopB and MetopC
            os.system(remove + pat[:-3] + '*')
            # Decompress goodfiles if necessary
            # CMD needs "" for ',' in filenames
            # (off0 because of GDS and NWCSAF!)
            for n in range (0, len(goodfiles)):
                if goodfiles[n][-4:] == '.bz2':
                    filename = goodfiles[n][off0:-4]
                    cmdstr = bz2Decompress + '"' + goodfiles[n] + '" > "' + filename + '"'
                    goodfiles[n] = filename
                    os.system(cmdstr)

        scenes = []
        numpass = 0
        timfirst = min(goodtimes)
        timlast = max(goodtimes)

        # Find the satellite that comes first (in the east!)
        # Set ns=0 as Sentinel-3X has not touched satnumber
        ns = 0
        for n in range(0, len(satnumber)):
            if goodtimes[n] == timfirst:
                ns = satnumber[n]

        # Shingle passes from the east to west
        while timlast - timfirst >= 0:
            passfiles = []
            n = len(goodtimes) - 1
            while n >= 0:
                if sat == 'Sen3X':
                    # One extra long ERR granule.tar
                    if goodtimes[n] == timfirst:
                        f = goodfiles[n][-103:-4]
                        cmd = 'tar -xf ' + goodfiles[n]
                        for m in member_files:
                            cmd += ' ' + f + '/' + m
                            passfiles.append(f + '/' + m)
                        os.system(cmd)
                        goodfiles.pop(n)
                        goodtimes.pop(n)
                else:
                    # Many normal short granule files
                    if (goodtimes[n] - timfirst < 3000 and satnumber[n] == ns):
                        passfiles.append(goodfiles[n])
                        satnumber.pop(n)
                        goodfiles.pop(n)
                        goodtimes.pop(n)

                n -= 1
            if goodtimes:
               # If more than one sat, then alternate between sats!
               ns = (ns + 1) % ns0
               timfirst = min(goodtimes)
            else:
               # We are done, this is to exit the master while loop
               timfirst = timlast + 1

            numpass += 1
            passfiles = sorted(passfiles)
            print('Pass ', numpass)
            for n in range(0, len(passfiles)):
                print ('%2d --> ' % (n+1), passfiles[n])
            scenes.append(Scene(filenames=passfiles, reader=reader))

        print(f'Found {numpass:d} {sat:s} pass(es) in range of POI to stack (and possibly image depending on chosen area)')
        print(f'The closest pass (with maximum elevation) is orbit number={orbmax:d}, peaking at telmax={Hou:s}:{Min:s} UTC')

        # Does also work for just 1 pass (even if it consists of 1 segment)
        # For MultiScene (Experimental!) see the latest satpy documentation

        if fcomposites:
            mscn = MultiScene(scenes)
            height = multi_single_pass(mscn, False, multi, sat, fcomposites, area, area_cities, ADDcoasts, ADDborders,
                         ADDrivers, ADDlakes, ADDgrid, ADDcities, ADDpoints, ADDstation, OVRcache, testrun)

        if tcomposites:
            mscn = MultiScene(scenes)
            height = multi_single_pass(mscn, True, multi, sat, tcomposites, area, area_cities, ADDcoasts, ADDborders,
                         ADDrivers, ADDlakes, ADDgrid, ADDcities, ADDpoints, ADDstation, OVRcache, testrun)

    else:
        # Single pass of ONE satellite with maximum elevation seen from POI

        bestfiles = []
        # Only take segment files of the best orbit
        for n in range(0, len(goodfiles)):
            if sat in SENsats:
                # One extra long ERR granule.tar
                if  goodtimes[n] == timmax:
                    fname = goodfiles[n]
                    f = fname[-103:-4]
                    cmd = 'tar -xf ' + fname
                    for m in member_files:
                        cmd += ' ' + f + '/' + m
                        bestfiles.append(f + '/' + m)
                    os.system(cmd)
            else:
                # Many normal short granule files
                if  abs(goodtimes[n] - timmax) < 3000:
                    bestfiles.append(goodfiles[n])

        bestfiles.sort()
        for n in range(0, len(bestfiles)):
            print(f'{n+1:2d} --> {bestfiles[n]:s}')
        print(f'Script: {sys.argv[0]:s} {sys.argv[1]:s} POI: lat={lat:.1f} lon={lon:.1f} ran={ran:.1f}')
        print(f'Maximum elevation occurs on orbit number={orbmax:d} at telmax={Hou:s}:{Min:s} UTC')

        if sat in EPSsats:
            # Clean old stuff in tmp directory
            # This is either MetopB or MetopC!
            os.system(remove + pat + '*')
            # Decompress bestfiles if necessary
            # CMD needs "" for ',' in filenames
            # (off0 because of GDS and NWCSAF!)
            for n in range (0, len(bestfiles)):
                if bestfiles[n][-4:] == '.bz2':
                    filename = bestfiles[n][off0:-4]
                    cmdstr = bz2Decompress + '"' + bestfiles[n] + '" > "' + filename + '"'
                    bestfiles[n] = filename
                    os.system(cmdstr)

        scn = Scene(filenames=bestfiles, reader=reader)

        if fcomposites:
            height = multi_single_pass(scn, False, multi, sat, fcomposites, area, area_cities, ADDcoasts, ADDborders,
                         ADDrivers, ADDlakes, ADDgrid, ADDcities, ADDpoints, ADDstation, OVRcache, testrun)
        if tcomposites:
            height = multi_single_pass(scn, True, multi, sat, tcomposites, area, area_cities, ADDcoasts, ADDborders,
                         ADDrivers, ADDlakes, ADDgrid, ADDcities, ADDpoints, ADDstation, OVRcache, testrun)

    return Yea, Mon, Day, Hou, Min, height


def get_prodir_areaf(sat, area, multi, testrun, **kwargs):
    # Get storage path, allow for filename ending '-multi'

    # SatPy's dynamic area definitions
    if area in ['omerc_bb', 'laea_bb']:
        multi = False
    # prodirs comes as global variable
    if testrun:
        prodir = prodirs + '/' + 'TEST'
    else:
        basedir = kwargs.get('basedir', sat)
        subdir = kwargs.get('subdir', '')
        if subdir:
            prodir = prodirs + '/'+ basedir + '/' + subdir
        else:
            prodir = prodirs + '/' + basedir
    if multi:
        areaf = area + '-multi'
    else:
        areaf = area

    return prodir, areaf



def get_magick(Yea, Mon, Day, Hou, Min, EffHeight, logo1, logo2, service, channel, receiver, sat, sensor,
                   composite, area, testrun, NoD, multi, ADDlegend=True, **kwargs):
        # ADDlegend should work for SPS V 4.0 (Beta) scripts as well, **kwargs for basedir/subdir choice
        # If a user selects basedir/subdir it's his responsability that these exist (defaut is just sat)

        satellite = get_long_name(sat)
        comp = get_abbr(sat, composite)
        prodir, areaf = get_prodir_areaf(sat, area, multi, testrun, **kwargs)

        INfilename = sat+'-'+composite+'-'+ area
        OUTfilename = prodir+'/'+sat+'-'+Yea+Mon+Day+'-'+NoD+'-'+Hou+Min+'-'+composite+'-'+areaf

        # Enhanced for Douglas
        if not ADDlegend:
            magick = convert+' '+INfilename+'.png '+OUTfilename+'-bare.jpg'
            return magick


        logo1 = logodir + '/' + logo1
        logo2 = logodir + '/' + logo2


        """
        It seems ImageMagick under Windows cannot cope with multiline text
        that includes \n newlines. We have to draw every line separately.
        This scales all pixel values for IM according to the image height.
        Should make it easier to use annotation and logos at the left side.
        This has been optimized using MSG4 full scan with 3712x3712 pixels.
        """

        OptHeight = 3712
        OptSplice = 640
        OptLogo1s = 540
        OptLogo1x = 50   # 40 for 'GNU-Linux-Logo-Penguin-SVG.png'
        OptLogo1y = 40   # 60 for 'GNU-Linux-Logo-Penguin-SVG.png'
        OptLogo2s = 530
        OptLogo2x = 55
        OptLogo2y = 55
        OptPoints = 90

        fac = EffHeight/OptHeight
        EffSplice = str(int(fac*OptSplice+0.5))
        EffLogo1s = str(int(fac*OptLogo1s+0.5))
        EffLogo1x = str(int(fac*OptLogo1x+0.5))
        EffLogo1y = str(int(fac*OptLogo1y+0.5))
        EffLogo2s = str(int(fac*OptLogo2s+0.5))
        EffLogo2x = str(int(fac*OptLogo2x+0.5))
        EffLogo2y = str(int(fac*OptLogo2y+0.5))
        EffPoints = str(int(fac*OptPoints+0.5))

        DATE = 'DATE: ('+NoD+')'  # For LEOs add NIG or DAY pass to date
        legend = [' \''+DATE+'\'\" '  , ' \''+Yea+'/'+Mon+'/'+Day+'\'\" ',
                  ' \'TIME:\'\" '     , ' \''+Hou+':'+Min+' UTC'+'\'\" ',
                  ' \'SOURCE:\'\" '   , ' \'EUMETCast\'\" ',
                  ' \'SERVICE:\'\" '  , ' \''+service+'\'\" ',
                  ' \'CHANNEL:\'\" '  , ' \''+channel+'\'\" ',
                  ' \'RECEIVER:\'\" ' , ' \''+receiver+'\'\" ',
                  ' \'SATELLITE:\'\" ', ' \''+satellite+'\'\" ',
                  ' \'SENSOR:\'\" '   , ' \''+sensor+'\'\" ',
                  ' \'COMPOSITE:\'\" ', ' \''+comp+'\'\" ',
                  ' \'AREA:\'\" '     , ' \''+area+'\'\" ']
        multidraw = ''
        yoff = fac*470
        for n in range(0, len(legend)):
            if (n % 2) == 0:
                xoff = fac*40
                yoff += fac*150
            else:
                xoff = fac*60
                yoff += fac*100
            multidraw += '-draw \"text +'+str(int(xoff+0.5))+'+'+str(int(yoff+0.5))+legend[n]

        magick = convert+' '+INfilename+'.png '\
        + '-gravity west -background rgb'+escape+'(245,245,245'+escape+') -splice '+EffSplice+'x0 '\
        + logo1+' -gravity northwest -geometry '+EffLogo1s+'x'\
        + EffLogo1s+'+'+EffLogo1x+'+'+EffLogo1y+' -composite '\
        + logo2+' -gravity southwest -geometry '+EffLogo2s+'x'\
        + EffLogo2s+'+'+EffLogo2x+'+'+EffLogo2y+' -composite '\
        + '-pointsize '+EffPoints+' -gravity northwest '+multidraw\
        + OUTfilename+'.jpg'

        return magick
