#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#************************************************************************
#
# This module provides functions necessary for generating *GEO* satellite
# products with 'Satpy Processing System' (SPS) advanced Kit Version 4.1.
# One copy of the file must reside in the same direcory with GEO scripts.
# There are only 2-4 lines that a user (may) have to adapt after install.
#
# CH-3123 Belp, 2022/12/10        License GPL3        (c) Ernst Lobsiger
#
#************************************************************************

# I need
import os, sys, platform
from datetime import datetime
from glob import glob

# Pytroll/SatPy needs
import hdf5plugin
from satpy import Scene, config
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
    xRITDecompress = toodir + '/exefiles/xRITDecompress'
    bz2Decompress = 'bzip2 -dc '
    escape = '\\'
    convert = 'convert'
elif OS == 'Windows':
    xRITDecompress = toodir + '/exefiles/xRITDecompress.exe'
    bz2Decompress = toodir + '/exefiles/7za x -so '
    escape = ''
    convert = toodir + '/exefiles/convert.exe'
else:
    print('OS not supported (yet) ...')

# Replace environment variable 'SATPY_CONFIG_PATH'
config.set(config_path = [toodir + '/userconfig'])

# The main data directory layout is defined here
# These are global variables (accessible below)
cachdir = datdir + '/cache'
logodir = datdir + '/logos'
geodata = datdir + '/geodata'
mslpdir = datdir + '/overlays'
tmpdirs = datdir + '/tmpdirs'
fontdir = datdir + '/fonts'
prodirs = datdir + '/products'


# This the fastest resampler. A cache_dir=geocache brings it down from 63 seconds to 18 seconds
# Resampler 'nearest' (default) gives more contrast (better results when resampling MSLP charts)
resampler_kwargs = {'resampler': 'nearest', 'radius_of_influence': 20000, 'reduce_data': False}

# This the slowest resampler. But cache_dir=geocache brings it down from 163 seconds to 25 seconds
# Resampler 'bilinear', once the cache files have been made, is even faster than 'gradient_search'
# resampler_kwargs = {'resampler': 'bilinear', 'reduce_data': True}  # True (default) is faster !

# Resampler 'gradient_search' gives finer resolution than 'nearest' (*shapely* must be installed).
# It does not value a cache_dir=geocache keyword argument and runs with and without in 31 seconds
# resampler_kwargs = {'resampler': 'gradient_search', 'method': 'bilinear', 'reduce_data': False}

# Short satellite names. These cannot contain a hyphen '-'. Only GEO sats are used in this module.
sat_list = ['GOES16', 'GOES17', 'GOES18', 'GOES19', 'HIMA8', 'MSG2', 'MSG3', 'MSG4', 'MTI1', 'MetopB', 'MetopC',
            'MetopX', 'Aqua', 'Terra', 'Sen3A', 'Sen3B', 'Sen3X', 'SNPP', 'NOAA20']

# Long satellite names. These are the ones in platforms.txt. Only GEO sats are used in this module.
sat_dict = {'GOES16': 'GOES-16',
            'GOES17': 'GOES-17',
            'GOES18': 'GOES-18',
            'GOES19': 'GOES-19',
            'HIMA8': 'Himawari-8',
            'MSG2': 'Meteosat-9',
            'MSG3': 'Meteosat-10',
            'MSG4': 'Meteosat-11',
            'MTI1': 'MTI-1',
            'MetopB': 'Metop-B',
            'MetopC': 'Metop-C',
            'MetopX': 'Metop-X',
            'Aqua': 'EOS-Aqua',
            'Terra': 'EOS-Terra',
            'Sen3A': 'Sentinel-3A',
            'Sen3B': 'Sentinel-3B',
            'Sen3X': 'Sentinel-3X',
            'SNPP': 'Suomi-NPP',
            'NOAA20': 'NOAA-20'}

# *******************************************************
# Geostationary satellites GOES16, GOES17, instrument abi
# *******************************************************

GOESsats = ['GOES16', 'GOES17', 'GOES18', 'GOES19']

abi_list = ['C01', 'C02', 'C03', 'C04', 'C05', 'C06', 'C07', 'C08',
            'C09', 'C10', 'C11', 'C12', 'C13', 'C14', 'C15', 'C16']
abi_dict = { \
    # Single abi channels
    'C01': ['C01'],
    'C02': ['C02'],
    'C03': ['C03'],
    'C04': ['C04'],
    'C05': ['C05'],
    'C06': ['C06'],
    'C07': ['C07'],
    'C08': ['C08'],
    'C09': ['C09'],
    'C10': ['C10'],
    'C11': ['C11'],
    'C12': ['C12'],
    'C13': ['C13'],
    'C14': ['C14'],
    'C15': ['C15'],
    'C16': ['C16'],
    # Defined visir/abi composites
    'airmass': ['C08', 'C10', 'C12', 'C13'],
    'ash': ['C11', 'C13', 'C14', 'C15'],
    'cimss_cloud_type': ['C02', 'C04', 'C05'],
    'cimss_cloud_type_raw': ['C02', 'C04', 'C05'],
    'cimss_green': ['C01', 'C02', 'C03'],
    'cimss_green_sunz': ['C01', 'C02', 'C03'],
    'cimss_green_sunz_rayleigh': ['C01', 'C02', 'C03'],
    'cimss_true_color': ['C01', 'C02', 'C03'],
    'cimss_true_color_sunz': ['C01', 'C02', 'C03'],
    'cimss_true_color_sunz_rayleigh': ['C01', 'C02', 'C03'],
    'cira_day_convection': ['C02', 'C05', 'C07', 'C08', 'C10', 'C13'],
    'cira_fire_temperature': ['C05', 'C06', 'C07'],
    'cloud_phase': ['C02', 'C05', 'C06'],
    'cloud_phase_distinction': ['C02', 'C05', 'C13'],
    'cloud_phase_distinction_raw': ['C02', 'C05', 'C13'],
    'cloud_phase_raw': ['C02', 'C05', 'C06'],
    'cloudtop': ['C07', 'C14', 'C15'],
    'color_infrared': ['C01', 'C02', 'C03'],
    'colorized_ir_clouds': ['C13'],
    'convection': ['C02', 'C05', 'C07', 'C08', 'C10', 'C13'],
    'day_microphysics': ['C03', 'C07', 'C14', 'C16'],
    'day_microphysics_abi': ['C03', 'C06', 'C13'],
    'day_microphysics_eum': ['C03', 'C07', 'C14', 'C16'],
    'dust': ['C11', 'C13', 'C14', 'C15'],
    'fire_temperature_awips': ['C05', 'C06', 'C07'],
    'fog': ['C11', 'C14', 'C15'],
    'green': ['C01', 'C02', 'C03'],
    'green_crefl': ['C01', 'C02', 'C03'],
    'green_nocorr': ['C01', 'C02', 'C03'],
    'green_raw': ['C01', 'C02', 'C03'],
    'green_snow': ['C02', 'C05', 'C14'],
    'highlight_C14': ['C14'],
    'ir108_3d': ['C14'],
    'ir_cloud_day': ['C14'],
    'land_cloud': ['C02', 'C03', 'C05'],
    'land_cloud_fire': ['C02', 'C03', 'C06'],
    'natural_color': ['C02', 'C03', 'C05'],
    'natural_color_nocorr': ['C02', 'C03', 'C05'],
    'natural_color_raw': ['C02', 'C03', 'C05'],
    'night_fog': ['C07', 'C14', 'C15'],
    'night_ir_alpha': ['C07', 'C13', 'C15'],
    'night_ir_with_background': ['C07', 'C13', 'C15'],
    'night_ir_with_background_hires': ['C07', 'C13', 'C15'],
    'night_microphysics': ['C07', 'C14', 'C15'],
    'night_microphysics_abi': ['C07', 'C13', 'C15'],
    'overview': ['C02', 'C03', 'C14'],
    'overview_raw': ['C02', 'C03', 'C14'],
    'snow': ['C03', 'C05', 'C07', 'C14', 'C16'],
    'snow_fog': ['C03', 'C05', 'C07', 'C13'],
    'so2': ['C09', 'C10', 'C11', 'C13'],
    'tropical_airmass': ['C08', 'C10', 'C12', 'C13'],
    'true_color': ['C01', 'C02', 'C03'],
    'true_color_crefl': ['C01', 'C02', 'C03'],
    'true_color_nocorr': ['C01', 'C02', 'C03'],
    'true_color_raw': ['C01', 'C02', 'C03'],
    'true_color_with_night_ir': ['C01', 'C02', 'C03', 'C07', 'C13', 'C15'],
    'true_color_with_night_ir_hires': ['C01', 'C02', 'C03', 'C07', 'C13', 'C15'],
    'water_vapors1': ['C08', 'C10', 'C13'],
    'water_vapors2': ['C08', 'C10']}

# Some composite names are too long for IM annotation left of pic
abi_abbr = { \
    'airmass': ('airmass', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'ash': ('ash', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'cimss_cloud_type': ('cimss_ct', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'cimss_cloud_type_raw': ('cimms_ctr', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'cimss_green': ('cimss_g', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'cimss_green_sunz': ('cimss_gs', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'cimss_green_sunz_rayleigh': ('cimss_gsr', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'cimss_true_color': ('cimss_tc', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'cimss_true_color_sunz': ('cimss_tcs', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'cimss_true_color_sunz_rayleigh': ('cimss_tcsr', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'cira_day_convection': ('cira_dc', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'cira_fire_temperature': ('cira_ft', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'cloud_phase': ('cloud_ph', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'cloud_phase_distinction': ('cloud_phd', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'cloud_phase_distinction_raw': ('cloud_phdr', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'cloud_phase_raw': ('cloud_phr', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'cloudtop': ('cloudtop', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'color_infrared': ('color_ir', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'colorized_ir_clouds': ('col_ir_clouds', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'convection': ('convection', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'day_microphysics': ('day_mp', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'day_microphysics_abi': ('day_mp_abi', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'day_microphysics_eum': ('day_mp_eum', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'dust': ('dust', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'fire_temperature_awips': ('fire_tem_awi', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'fog': ('fog', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'green': ('green', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'green_crefl': ('green_cre', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'green_nocorr': ('green_noc', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'green_raw': ('green_raw', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'green_snow': ('green_snow', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'highlight_C14': ('highlight_C14', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'ir108_3d': ('ir108_3d', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'ir_cloud_day': ('ir_cloud_day', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'land_cloud': ('land_cloud', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'land_cloud_fire': ('land_cloud_f', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'natural_color': ('natural_color', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'natural_color_nocorr': ('nat_col_noc', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'natural_color_raw': ('nat_col_raw', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'night_fog': ('night_fog', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'night_ir_alpha': ('night_ir_a', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'night_ir_with_background': ('night_ir_wb', 0, 0, 0, 0, 0, 0, 0, 0, 1),
    'night_ir_with_background_hires': ('night_ir_wbh', 0, 0, 0, 0, 0, 0, 0, 0, 1),
    'night_microphysics': ('night_mp', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'night_microphysics_abi': ('night_mp_abi', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'overview': ('overview', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'overview_raw': ('overview_raw', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'snow': ('snow', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'snow_fog': ('snow_fog', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'so2': ('so2', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'tropical_airmass': ('tropical_am', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'true_color': ('true_color', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'true_color_crefl': ('true_col_cre', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'true_color_nocorr': ('true_col_noc', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'true_color_raw': ('true_col_raw', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'true_color_with_night_ir': ('true_col_wni', 0, 0, 0, 0, 0, 0, 0, 0, 1),
    'true_color_with_night_ir_hires': ('true_col_wnih', 0, 0, 0, 0, 0, 0, 0, 0, 1),
    'water_vapors1': ('water_vap1', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'water_vapors2': ('water_vap2', 0, 0, 0, 0, 0, 0, 0, 0, 0)
    }


# *********************************************
# Geostationary satellite HIMA8, instrument ahi
# *********************************************

HIMAsats = ['HIMA8']

ahi_list =  ['B01', 'B02', 'VIS', 'B04', 'B05', 'B06', 'IR4', 'IR3',
             'B09', 'B10', 'B11', 'B12', 'IR1', 'B14', 'IR2', 'B16']
ahi_dict = { \
    # Single ahi channels
    'B01': ['B01'],
    'B02': ['B02'],
    'B03': ['VIS'],
    'B04': ['B04'],
    'B05': ['B05'],
    'B06': ['B06'],
    'B07': ['IR4'],
    'B08': ['IR3'],
    'B09': ['B09'],
    'B10': ['B10'],
    'B11': ['B11'],
    'B12': ['B12'],
    'B13': ['IR1'],
    'B14': ['B14'],
    'B15': ['IR2'],
    'B16': ['B16'],
    # Defined visir/ahi composites
    'airmass': ['IR3', 'B10', 'B12', 'B14'],
    'ash': ['B11', 'IR1', 'B14', 'IR2'],
    'cloud_phase_distinction': ['VIS', 'B05', 'IR1'],
    'cloud_phase_distinction_raw': ['VIS', 'B05', 'IR1'],
    'colorized_ir_clouds': ['IR1'],
    'convection': ['VIS', 'B05', 'IR4', 'B09', 'B10', 'IR1'],
    'day_microphysics_ahi': ['B04', 'B06', 'IR1'],
    'day_microphysics_eum': ['B04', 'IR4', 'IR1', 'B14', 'B16'],
    'dust': ['B11', 'IR1', 'B14', 'IR2'],
    'fire_temperature_39refl': ['B05', 'B06', 'IR4', 'B14', 'B16'],
    'fire_temperature_awips': ['B05', 'B06', 'IR4'],
    'fire_temperature_eumetsat': ['B05', 'B06', 'IR4'],
    'fog': ['B11', 'IR1', 'B14', 'IR2'],
    'green': ['B02', 'VIS', 'B04'],
    'green_nocorr': ['B02', 'B04'],
    'green_true_color_reproduction': ['B02', 'VIS', 'B04'],
    'ir_cloud_day': ['B14'],
    'mid_vapor': ['IR3', 'B10'],
    'natural_color': ['VIS', 'B04', 'B05'],
    'natural_color_nocorr': ['VIS', 'B04', 'B05'],
    'natural_color_raw': ['VIS', 'B04', 'B05'],
    'night_ir_alpha': ['IR4', 'IR1', 'IR2'],
    'night_ir_with_background': ['IR4', 'IR1', 'IR2'],
    'night_ir_with_background_hires': ['IR4', 'IR1', 'IR2'],
    'night_microphysics': ['IR4', 'IR1', 'B14', 'IR2'],
    'overview': ['VIS', 'B04', 'IR1'],
    'overview_raw': ['VIS', 'B04', 'IR1'],
    'true_color': ['B01', 'B02', 'VIS', 'B04'],
    'true_color_nocorr': ['B01', 'B02', 'VIS', 'B04'],
    'true_color_raw': ['B01', 'B02', 'VIS'],
    'true_color_reproduction': ['B01', 'B02', 'VIS', 'B04'],
    'true_color_with_night_ir': ['B01', 'B02', 'VIS', 'B04', 'IR4', 'IR1', 'IR2'],
    'true_color_with_night_ir_hires': ['B01', 'B02', 'VIS', 'B04', 'IR4', 'IR1', 'IR2'],
    'water_vapors1': ['IR3', 'B10', 'IR1'],
    'water_vapors2': ['IR3', 'B10']}

# Some composite names are too long for IM annotation left of pic
ahi_abbr = { \
    'airmass': ('airmass', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'ash': ('ash', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'cloud_phase_distinction': ('cloud_phd', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'cloud_phase_distinction_raw': ('cloud_phdr', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'colorized_ir_clouds': ('col_ir_clouds', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'convection': ('convection', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'day_microphysics_ahi': ('day_mp_ahi', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'day_microphysics_eum': ('day_mp_eum', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'dust': ('dust', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'fire_temperature_39refl': ('fire_tem_39r', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'fire_temperature_awips': ('fire_tem_awi', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'fire_temperature_eumetsat': ('fire_tem_eum', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'fog': ('fog', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'green': ('green', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'green_nocorr': ('green_noc', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'green_true_color_reproduction': ('green_tcr', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'ir_cloud_day': ('ir_cloud_day', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'mid_vapor': ('mid_vapor', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'natural_color': ('natural_color', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'natural_color_nocorr': ('nat_col_noc', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'natural_color_raw': ('nat_col_raw', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'night_ir_alpha': ('night_ir_a', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'night_ir_with_background': ('night_ir_wb', 0, 0, 0, 0, 0, 0, 0, 0, 1),
    'night_ir_with_background_hires': ('night_ir_wbh', 0, 0, 0, 0, 0, 0, 0, 0, 1),
    'night_microphysics': ('night_mp', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'overview': ('overview', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'overview_raw': ('overview_raw', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'true_color': ('true_color', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'true_color_nocorr': ('true_col_noc', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'true_color_raw': ('true_col_raw', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'true_color_reproduction': ('true_col_rep', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'true_color_with_night_ir': ('true_col_wni', 0, 0, 0, 0, 0, 0, 0, 0, 1),
    'true_color_with_night_ir_hires': ('true_col_wnih', 0, 0, 0, 0, 0, 0, 0, 0, 1),
    'water_vapors1': ('water_vap1', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'water_vapors2': ('water_vap2', 0, 0, 0, 0, 0, 0, 0, 0, 0)
    }


# ************************************************************
# Geostationary satellites MSG2, MSG3, MSG4, instrument seviri
# ************************************************************

MSGsats = ['MSG2', 'MSG3', 'MSG4']

seviri_list = ['VIS006', 'HRV', 'VIS008', 'IR_016', 'IR_039', 'WV_062',
               'WV_073', 'IR_087', 'IR_097', 'IR_108', 'IR_120', 'IR_134']
seviri_dict = { \
    # Single seviri channels
    'VIS006': ['VIS006'],
    'HRV': ['HRV'],
    'VIS008': ['VIS008'],
    'IR_016': ['IR_016'],
    'IR_039': ['IR_039'],
    'WV_062': ['WV_062'],
    'WV_073': ['WV_073'],
    'IR_087': ['IR_087'],
    'IR_097': ['IR_097'],
    'IR_108': ['IR_108'],
    'IR_120': ['IR_120'],
    'IR_134': ['IR_134'],
    # Defined visir/seviri composites
    'airmass': ['WV_062', 'WV_073', 'IR_097', 'IR_108'],
    'ash': ['IR_087', 'IR_108', 'IR_120'],
    'cloud_phase_distinction': ['VIS006', 'HRV', 'IR_016', 'IR_108'],
    'cloud_phase_distinction_raw': ['HRV', 'IR_016', 'IR_108'],
    'cloudtop': ['IR_039', 'IR_108', 'IR_120', 'IR_134'],
    'cloudtop_daytime': ['IR_039', 'IR_108', 'IR_120', 'IR_134'],
    'colorized_ir_clouds': ['IR_108'],
    'convection': ['VIS006', 'IR_016', 'IR_039', 'WV_062', 'WV_073', 'IR_108', 'IR_134'],
    'day_microphysics': ['VIS008', 'IR_039', 'IR_108', 'IR_134'],
    'day_microphysics_winter': ['VIS008', 'IR_039', 'IR_108', 'IR_134'],
    'dust': ['IR_087', 'IR_108', 'IR_120'],
    'fog': ['IR_087', 'IR_108', 'IR_120'],
    'green_snow': ['VIS006', 'IR_016', 'IR_108'],
    'hrv_clouds': ['HRV', 'IR_108'],
    'hrv_fog': ['HRV', 'IR_016'],
    'hrv_severe_storms': ['HRV', 'IR_039', 'IR_108'],
    'hrv_severe_storms_masked': ['HRV', 'IR_039', 'IR_108'],
    'ir108_3d': ['IR_108'],
    'ir_cloud_day': ['IR_108'],
    'ir_overview': ['IR_039', 'IR_108', 'IR_120', 'IR_134'],
    'ir_sandwich': ['HRV', 'IR_108'],
    'natural_color': ['VIS006', 'VIS008', 'IR_016'],
    'natural_color_nocorr': ['VIS006', 'VIS008', 'IR_016'],
    'natural_color_raw': ['VIS006', 'VIS008', 'IR_016'],
    'natural_color_with_night_ir': ['VIS006', 'VIS008', 'IR_016', 'IR_039', 'IR_108', 'IR_120'],
    'natural_color_with_night_ir_hires': ['VIS006', 'VIS008', 'IR_016', 'IR_039', 'IR_108', 'IR_120'],
    'natural_enh': ['VIS006', 'VIS008', 'IR_016'],
    'natural_enh_with_night_ir': ['VIS006', 'VIS008', 'IR_016', 'IR_039', 'IR_108', 'IR_120'],
    'natural_enh_with_night_ir_hires': ['VIS006', 'VIS008', 'IR_016', 'IR_039', 'IR_108', 'IR_120'],
    'natural_with_night_fog': ['VIS006', 'VIS008', 'IR_016', 'IR_039', 'IR_108', 'IR_120', 'IR_134'],
    'night_fog': ['IR_039', 'IR_108', 'IR_120', 'IR_134'],
    'night_ir_alpha': ['IR_039', 'IR_108', 'IR_120'],
    'night_ir_with_background': ['IR_039', 'IR_108', 'IR_120'],
    'night_ir_with_background_hires': ['IR_039', 'IR_108', 'IR_120'],
    'night_microphysics': ['IR_039', 'IR_108', 'IR_120'],
    'overview': ['VIS006', 'VIS008', 'IR_108'],
    'overview_raw': ['VIS006', 'VIS008', 'IR_108'],
    'realistic_colors': ['VIS006', 'HRV', 'VIS008'],
    'snow': ['VIS008', 'IR_016', 'IR_039', 'IR_108', 'IR_134'],
    'vis_sharpened_ir': ['HRV', 'IR_108'],
    'ir_clouds_hcp': ['IR_108']}

# Some composite names are too long for IM annotation left of pic
seviri_abbr = { \
    'airmass': ('airmass', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'ash': ('ash', 1, 0, 0, 0, 1, 0, 0, 0, 0),
    'cloud_phase_distinction': ('cloud_phd', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'cloud_phase_distinction_raw': ('cloud_phdr', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'cloudtop': ('cloudtop', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'cloudtop_daytime': ('cloudtop_day', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'colorized_ir_clouds': ('col_ir_clouds', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'convection': ('convection', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'day_microphysics': ('day_mp', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'day_microphysics_winter': ('day_mp_w', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'dust': ('dust', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'fog': ('fog', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'green_snow': ('green_snow', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'hrv_clouds': ('hrv_clouds', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'hrv_fog': ('hrv_fog', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'hrv_severe_storms': ('hrv_ss', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'hrv_severe_storms_masked': ('hrv_ssm', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'ir108_3d': ('ir108_3d', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'ir_cloud_day': ('ir_cloud_day', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'ir_overview': ('ir_overview', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'ir_sandwich': ('ir_sandwich', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'natural_color': ('natural_color', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'natural_color_nocorr': ('nat_col_noc', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'natural_color_raw': ('nat_col_raw', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'natural_color_with_night_ir': ('nat_col_wni', 0, 0, 0, 0, 0, 0, 0, 0, 1),
    'natural_color_with_night_ir_hires': ('nat_col_wnih', 0, 0, 0, 0, 0, 0, 0, 0, 1),
    'natural_enh': ('natural_enh', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'natural_enh_with_night_ir': ('nat_enh_wni', 0, 0, 0, 0, 0, 0, 0, 0, 1),
    'natural_enh_with_night_ir_hires': ('nat_enh_wnih', 0, 0, 0, 0, 0, 0, 0, 0, 1),
    'natural_with_night_fog': ('natural_wnf', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'night_fog': ('night_fog', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'night_ir_alpha': ('night_ir_a', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'night_ir_with_background': ('night_ir_wb', 0, 0, 0, 0, 0, 0, 0, 0, 1),
    'night_ir_with_background_hires': ('night_ir_wbh', 0, 0, 0, 0, 0, 0, 0, 0, 1),
    'night_microphysics': ('night_mp', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'overview': ('overview', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'overview_raw': ('overview_raw', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'realistic_colors': ('realist_color', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'snow': ('snow', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'vis_sharpened_ir': ('vis_sharp_ir', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    # Added for NWCSAF
    'cloudtype': ('cloudtype', 1, 0, 0, 0, 0, 0, 0, 0, 1),
    'cloud_top_pressure': ('cloud_top_p', 2, 0, 0, 0, 0, 0, 0, 0, 1),
    'cloud_top_temperature': ('cloud_top_t', 0, 0, 0, 0, 0, 0, 0, 0, 1),
    'cloudmask': ('cloudmask', 0, 0, 0, 0, 0, 0, 0, 0, 1),
    }

# ************************************************************
# Geostationary satellites MTIx, MTSx, instrument FCI, others?
# ************************************************************

MTGsats = ['MTI1']  # DEBUG: This is very preliminary based on EUMETSAT MTI1 FCI test data

fci_list = ['vis_04', 'vis_05', 'vis_06', 'vis_08', 'vis_09', 'nir_13', 'nir_16', 'nir_22',
            'ir_38', 'wv_63', 'wv_73', 'ir_87', 'ir_97', 'ir_105', 'ir_123', 'ir_133']
fci_dict = { \
    # Single fci channels
    'vis_04': ['vis_04'],
    'vis_05': ['vis_05'],
    'vis_06': ['vis_06'],
    'vis_08': ['vis_08'],
    'vis_09': ['vis_09'],
    'nir_13': ['nir_13'],
    'nir_16': ['nir_16'],
    'nir_22': ['nir_22'],
    'ir_38': ['ir_38'],
    'wv_63': ['wv_63'],
    'wv_73': ['wv_73'],
    'ir_87': ['ir_87'],
    'ir_97': ['ir_97'],
    'ir_105': ['ir_105'],
    'ir_123': ['ir_123'],
    'ir_133': ['ir_133'],
    # Defined fci composites
    'airmass': ['wv_63', 'wv_73', 'ir_97', 'ir_105'],
    'ash': ['ir_87', 'ir_105', 'ir_123'],
    'cimss_cloud_type_raw': ['vis_06', 'nir_13', 'nir_16'],
    'cloud_phase_distinction_raw': ['vis_06', 'nir_16', 'ir_105'],
    'cloud_phase_raw': ['vis_06', 'nir_16', 'nir_22'],
    'cloudtop': ['ir_38', 'ir_105', 'ir_123'],
    'convection': ['vis_06', 'nir_16', 'ir_38', 'wv_63', 'wv_73', 'ir_105'],
    'day_microphysics': ['vis_08', 'ir_38', 'ir_105', 'ir_133'],
    'dust': ['ir_87', 'ir_105', 'ir_123'],
    'fog': ['ir_87', 'ir_105', 'ir_123'],
    'green_snow': ['vis_06', 'nir_16', 'ir_105'],
    'ir108_3d': ['ir_105'],
    'ir_cloud_day': ['ir_105'],
    'natural_color': ['vis_06', 'vis_08', 'nir_16'],
    'natural_color_raw': ['vis_06', 'vis_08', 'nir_16'],
    'night_fog': ['ir_38', 'ir_105', 'ir_123'],
    'night_microphysics': ['ir_38', 'ir_105', 'ir_123'],
    'true_color_raw': ['vis_04', 'vis_05', 'vis_06']
    }

# Some composite names are too long for IM annotation left of pic
fci_abbr = { \
    'airmass': ('airmass', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'ash': ('ash', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'cimss_cloud_type_raw': ('cimss_ctr', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'cloud_phase_distinction_raw': ('cloud_phdr', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'cloud_phase_raw': ('cloud_phr', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'cloudtop': ('cloudtop', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'convection': ('convection', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'day_microphysics': ('day_mp', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'dust': ('dust', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'fog': ('fog', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'green_snow': ('green_snow', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'ir108_3d': ('ir108_3d', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'ir_cloud_day': ('ir_cloud_day', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'natural_color': ('natural_color', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'natural_color_raw': ('nat_col_raw', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'night_fog': ('night_fog', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'night_microphysics': ('night_mp', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'true_color_raw': ('true_col_raw', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'true_color': ('true_color', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'true_color_with_night_ir': ('tc_night_ir', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'colorized_ir_clouds': ('col_ir_cld', 0, 0, 0, 0, 0, 0, 0, 0, 0),
    'geo_color': ('geo_color', 0, 0, 0, 0, 0, 0, 0, 0, 0)
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

    # Minimal command line parameter test for all GEO satellites
    usage = sys.argv[0] + ' expects YYYYmmddHHMM as CLI parameter:\n' \
          + 'See comment concerning EUMETCast in the script header.'
    if len(sys.argv) != 2:
        sys.exit(usage)
    if len(sys.argv[1]) != 12:
        sys.exit(usage)

    # Time slot from CLI
    Dat=sys.argv[1]

    # Get substrings
    Yea=Dat[:4]
    Mon=Dat[4:6]
    Day=Dat[6:8]
    Hou=Dat[8:10]
    Min=Dat[10:]

    return  sat, Dat, Yea, Mon, Day, Hou, Min


def get_lists(sat, composites, area, Types, Dat):

    # Do a couple of tests for MSLP charts first
    if len(composites) != len(Types):
        sys.exit('SORRY: For every composite there must be exactly one Typ ...')
    okarea = {'MSG3': ['dwda', 'dwdn', 'dwdc', 'dwdi', 'ukmos', 'ukmol', 'ukmox', 'opcae'],
               'MSG4': ['dwda', 'dwdn', 'dwdc', 'dwdi', 'ukmos', 'ukmol', 'ukmox', 'opcae'],
              'GOES16': ['opcaw'], 'GOES17': ['opcpe'], 'GOES18': ['opcpe'], 'GOES19': ['opcaw'], 'HIMA8': ['opcpw']}
    okhour = {'dwda': 3, 'dwdn': 6, 'dwdc': 12, 'dwdi': 12, 'ukmos': 6, 'ukmol': 6, 'ukmox': 6,
              'opcae': 6, 'opcaw': 6, 'opcpe': 6, 'opcpw': 6}
    areas = okarea.get(sat, [])
    if not area in areas:
        sys.exit('SORRY: No MSLP charts exist for your satellite ' + sat + ' and area ' + area + ' ...')
    hourly = okhour[area]
    if int(Dat[-4:-2]) % hourly:
        sys.exit('SORRY: MSLP charts for area ' + area + ' are ' + str(hourly) + ' hourly ...')

    ADDcharts = []
    fill_values = []
    for Type in Types:
        chart = mslpdir + '/' + area + '/' + area + '-' + Type + '-' + Dat + '.png'
        if os.path.exists(chart):
            ADDcharts.append(chart + ' -composite ')
            fill_values.append(255 * int(Type[0]=='b'))  # Background negates outline color
        else:
            sys.exit('SORRY: MSLP chart ' + chart + ' not found ...')  # Wrong Type or Min?

    return ADDcharts, fill_values


def init_tmp(sat, testrun):
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

# ****************************************************************
# OS/SHELL specific stuff does run on GNU/Linux and Windows 10 PRO
# vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv

def hokus_pokus_png(sat, area):
# We must sit in sat tmp dir
    if OS == 'Linux':
        fidibus = 'rm -f ' + sat + '-*-' + area + '.png'
        os.system(fidibus)
    elif OS == 'Windows':
        fidibus = 'del ' + sat + '-*-' + area + '.png 2>nul'
        os.system(fidibus)
    else:
        print('OS_ERROR_png')

def hokus_pokus_ahi(sat, area, Dat):
# We must sit in HIMA8 tmp dir
    if OS == 'Linux':
        fidibus = 'rm -f ' + sat + '-*-' + area + '.png && rm -f `ls IMG_DK01* 2>/dev/null | grep -v ' + Dat[:-1] + '`'
        os.system(fidibus)
    elif OS == 'Windows':
        fidibus = '@echo off&del ' + sat + '-*-' + area +'.png 2>nul&for /F %G in (\'\"dir /B IMG_DK01* 2>nul | findstr /V '\
                  + Dat[:-1] + '\"\') do del %G'
        os.system(fidibus)
    else:
        print('OS_ERROR_ahi')

def hokus_pokus_seviri(sat, area, Dat):
# We must sit in MSG* tmp dir
    if OS == 'Linux':
        fidibus = 'rm -f ' + sat + '-*-' + area + '.png && rm -f `ls H-000-' + sat + '* 2>/dev/null | grep -v ' + Dat + '`'
        os.system(fidibus)
    elif OS == 'Windows':
        fidibus = '@echo off&del ' + sat + '-*-' + area + '.png 2>nul&for /F %G in (\'\"dir /B H-000-' \
                  + sat + '* 2>nul | findstr /V ' + Dat + '\"\') do del %G'
        os.system(fidibus)
    else:
        print('OS_ERROR_seviri')

# ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
# There should remain no OS/SHELL specific stuff below this line !
# ****************************************************************

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

# Find all needed files for a list of composites
def needed_files(inst_dict, inst_list, composites):
    needed = []
    for c in composites:
        if not c in inst_dict:
            return inst_list
        for f in inst_dict[c]:
            if not f in needed:
                needed.append(f)
    return needed

def get_files(Yea, Mon, Day, Hou, Min, sat, segdir, decomp, isbulk, reader, composites, area):
# You must sit in the GEO satellites tmp directory on entry of this function
    from datetime import datetime
    import re as _re

    if not sat in sat_list:
        sys.exit('Satellite short name must be in', sat_list)

    Dat = Yea + Mon + Day + Hou + Min

    if not isbulk: segdir += '/' + Yea + '/' + Mon + '/' + Day
    off0 = len(segdir) + 1

    if sat in ('MSG3', 'MSG4') and reader=='nwcsaf-geo':
        # Get NWC-SAF file types CT, CMA and CTTH
        hokus_pokus_png(sat, area)
        files = glob(segdir + '/' + 'S_NWC_C*_' + sat + '*' + Dat[:8] +'T'+Dat[8:] + '*.nc')
        return files

    # MTI1 FCI: select scan cycle closest to slot time (robust cycle-based selection)
    if sat=='MTI1':
        slot_dt = datetime(int(Yea), int(Mon), int(Day), int(Hou), int(Min))
        all_nc  = glob(segdir + '/' + 'W_XX-EUMETSAT*.nc')
        cycle_start = {}
        cycle_files = {}
        for _f in all_nc:
            mc = _re.search(r'_O_(\d{4})_\d{4}\.nc', _f)
            mt = _re.search(r'OPE_(\d{14})', _f)
            if mc and mt and 'BODY' in _f and '_0041.nc' not in _f:
                _cyc = int(mc.group(1))
                try: _ft = datetime.strptime(mt.group(1)[:12], '%Y%m%d%H%M')
                except: continue
                if _cyc not in cycle_start or _ft < cycle_start[_cyc]:
                    cycle_start[_cyc] = _ft
                cycle_files.setdefault(_cyc, []).append(_f)
        if cycle_start:
            best = min(cycle_start, key=lambda c: abs((cycle_start[c]-slot_dt).total_seconds()))
            files = cycle_files[best]
        else:
            files = [f for f in all_nc if 'BODY' in f and '_0041.nc' not in f]
        return files

    files = []

    if sat in GOESsats:
        hokus_pokus_png(sat, area)
        # GOES-16/17/18 use DayOfYear (DOY) instead of month and day in file names
        time_slot = datetime(int(Yea), int(Mon), int(Day), int(Hou), int(Min))
        Slo = time_slot.strftime('%Y%j%H%M')
        for b in needed_files(abi_dict, abi_list, composites):
            files += glob(segdir + '/' + 'OR_ABI-L1b-*' + str(b) + '*_G' + sat[4:]+'_s' + Slo + '*.nc')

    if sat in HIMAsats:
        hokus_pokus_ahi(sat, area, Dat)
        # Maybe we have decompressed files from our Dat[:-1]
        cached_files = glob('IMG_DK01*' + Dat[:-1] + '*')
        # If you have bz2Decompress(ed) all files beforehand with some data manager
        if decomp:
            for b in needed_files(ahi_dict, ahi_list, composites):
                files += glob(segdir + '/' + 'IMG_DK01' + str(b) + '_' + Dat[:-1] + '*')
        # I only decompress the files when I actually produce images and/or products
        else:
            for b in needed_files(ahi_dict, ahi_list, composites):
                compressed_files = glob(segdir + '/' + 'IMG_DK01' + str(b) + '_' + Dat[:-1] + '*')
                # Decompress all files needed if not already cached
                for f in compressed_files:
                    result = f[off0:-4]
                    if result in cached_files:
                        print('Found cached file: ' + result)
                    else:
                        cmdstr = bz2Decompress + f + ' > ' + result
                        os.system(cmdstr)
                        print('Decompressed file: ' + result)
                    files.append(result)

    if sat in MSGsats:
        hokus_pokus_seviri(sat, area, Dat)
        # Maybe we have decompressed files from our Dat
        cached_files = glob('H-000-' + sat + '*' + Dat + '*')

        # Meteosat-11 sends only 1 PROlogue and 1 EPIlogue file per 15 minute time slot
        # These files are not wavelet compressed, thus can be read directly from segdir

        files = glob(segdir + '/H-000-' + sat + '*PRO*' + Dat + '*') \
              + glob(segdir + '/H-000-' + sat + '*EPI*' + Dat + '*')

        # If you have xRITDecompress(ed) all files beforehand with some data manager
        if decomp:
            for b in needed_files(seviri_dict, seviri_list, composites):
                files += glob(segdir + '/H-000-' + sat + '*' + str(b) + '*' + Dat + '*-__')
        # I only decompress the files when I actually produce images and/or products
        else:
            for b in needed_files(seviri_dict, seviri_list, composites):
                compressed_files = glob(segdir + '/H-000-' + sat + '*' + str(b) + '*' + Dat + '*-C_')
                # Decompress all files needed if not already cached
                for f in compressed_files:
                    result = f[off0:-2] + '__'
                    if result in cached_files:
                        print('Found cached file: ' + result)
                    else:
                        os.system(xRITDecompress + ' ' + f)
                    files.append(result)

    # May still be []
    return files


# fcomposites work with scene.load(..., generate=False), which is faster
# tcomposites must have scene.load(..., generate=True) (default), slower
def get_ft_composites(sat, composites, fill_values):
    fcomposites=[]
    ffill_values=[]
    tcomposites=[]
    tfill_values=[]
    n = 0
    # If key composite does not exist default to tcomposites
    if sat in GOESsats:
        for composite in composites:
            if composite in abi_abbr:
                if abi_abbr[composite][9]:
                    tcomposites.append(composite)
                    tfill_values.append(fill_values[n])
                else:
                    fcomposites.append(composite)
                    ffill_values.append(fill_values[n])
            else:
                tcomposites.append(composite)
                tfill_values.append(fill_values[n])
            n += 1
    elif sat in HIMAsats:
        for composite in composites:
            if composite in ahi_abbr:
                if ahi_abbr[composite][9]:
                    tcomposites.append(composite)
                    tfill_values.append(fill_values[n])
                else:
                    fcomposites.append(composite)
                    ffill_values.append(fill_values[n])
            else:
                tcomposites.append(composite)
                tfill_values.append(fill_values[n])
            n += 1
    elif sat in MSGsats:
        for composite in composites:
            if composite in seviri_abbr:
                if seviri_abbr[composite][9]:
                    tcomposites.append(composite)
                    tfill_values.append(fill_values[n])
                else:
                    fcomposites.append(composite)
                    ffill_values.append(fill_values[n])
            else:
                tcomposites.append(composite)
                tfill_values.append(fill_values[n])
            n += 1
    elif sat in MTGsats:
        for composite in composites:
            if composite in fci_abbr:
                if fci_abbr[composite][9]:
                    tcomposites.append(composite)
                    tfill_values.append(fill_values[n])
                else:
                    fcomposites.append(composite)
                    ffill_values.append(fill_values[n])
            else:
                tcomposites.append(composite)
                tfill_values.append(fill_values[n])
            n += 1

    return fcomposites, ffill_values, tcomposites, tfill_values



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
    if sat in GOESsats and composite in abi_abbr:
        comp = abi_abbr[composite][0]
    elif sat in HIMAsats and composite in ahi_abbr:
        comp = ahi_abbr[composite][0]
    elif sat in MSGsats and  composite in seviri_abbr:
        comp = seviri_abbr[composite][0]
    elif sat in MTGsats and  composite in fci_abbr:
        comp = fci_abbr[composite][0]
    else:
        comp = abbreviated(composite)
    return comp

def get_index(sat, composite, i):
    # If key composite does not exist default to index = 0
    if sat in GOESsats and composite in abi_abbr:
        return  abi_abbr[composite][i]
    elif sat in HIMAsats and composite in ahi_abbr:
        return  ahi_abbr[composite][i]
    elif sat in MSGsats and  composite in seviri_abbr:
        return  seviri_abbr[composite][i]
    elif sat in MTGsats and  composite in fci_abbr:
        return  fci_abbr[composite][i]
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
    sat_cities_dict = { \
                'MTI1': ['Berlin', 'London', 'Paris', 'Madrid', 'Rome'],  # DEBUG for MTI1 test data
                'MSG4': ['Berlin', 'London', 'Paris', 'Madrid', 'Rome'],
                'MSG3': ['Berlin', 'London', 'Paris', 'Madrid', 'Rome'],
                'MSG2': ['Cairo', 'Cape Town', 'Herat', 'Kabul', 'New Delhi'],
                'GOES16': ['New York City', 'Chicago', 'Mexico City', 'Sao Paulo'],
                'GOES17': ['Los Angeles', 'Honolulu'],
                'GOES18': ['Los Angeles', 'Honolulu'],
                'GOES19': ['Los Angeles', 'Honolulu'],
                'HIMA8': ['Tokyo']}

    if area_cities:
        my_cities_list = area_cities
    else:
        my_cities_list = sat_cities_dict[sat]

    my_cities = {'font': fontdir + '/DejaVuSerif.ttf',
                 'font_size': 20*sf, 'cities_list': my_cities_list, 'symbol': 'circle',
                 'ptsize': 20*sf, 'outline': 'black', 'fill': 'red', 'width': 3.0*sf,
                 'outline_opacity': 255,'fill_opacity': 255, 'box_outline': 'black',
                 'box_linewidth': 3.0*sf, 'box_fill': 'gold', 'box_opacity': 255}


    # List of EARS Stations, Longitude E+ W- / Latitue N+ S- taken from url
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


def geo_images(Yea, Mon, Day, Hou, Min, sat, segdir, decomp, isbulk, reader, composites, area, area_cities,
               ADDcoasts, ADDborders, ADDrivers, ADDlakes, ADDgrid, ADDcities, ADDpoints, ADDstation,
               GEOcache, OVRcache, testrun, **kwargs):

    default_values = []
    for composite in composites:
        default_values.append(0)
    fill_values = kwargs.get('fill_values', default_values)
    if len(composites) != len(fill_values):
        sys.exit('SORRY: For every composite there must be exactly one fill_value ...')

    if GEOcache:
       if testrun:
           resampler_kwargs.update({'cache_dir': cachdir + '/ctest'})
       else:
           resampler_kwargs.update({'cache_dir': cachdir + '/c' + sat.lower()})

    init_tmp(sat, testrun)

    files = get_files(Yea, Mon, Day, Hou, Min, sat, segdir, decomp, isbulk, reader, composites, area)

    # We should have got at least some good files
    if files == []:
        sys.exit('Sorry, no good files found ...')

    global_scene = Scene(filenames = files, reader = reader)

    fcomposites, ffill_values, tcomposites, tfill_values = get_ft_composites(sat, composites, fill_values)

    if fcomposites:
        global_scene.load(fcomposites, generate = False)
        # Native seviri datasets are 3712x3712 pixels (3km), 'HRV' is 11136x11136 pixels (1km)!!
        new_scene = global_scene.resample(area, **resampler_kwargs)  # **defined @ top of module

        try: # This is for real (multichannel) composites
            layers, height, width = new_scene[fcomposites[0]].shape
        except: # In case of a single channel 'composite'
            height, width = new_scene[fcomposites[0]].shape

        # new_scene.save_datasets() does not allow for overlays that depend on composite colors!
        # This trick below has been proposed by core developer Panu Lahtinen on the google list:
        # Enhance images with composite dependant overlays and save *.png to temporary directory
        # Use new_scene 'name' (like composite name) and not 'standard_name' used in enhancement

        n = 0
        save_objects = []
        for composite in fcomposites:
            overlays = get_overlays(sat, composite, area, area_cities, height, width, ADDcoasts,
                                    ADDborders, ADDrivers, ADDlakes, ADDgrid, ADDcities, ADDpoints, ADDstation,
                                    OVRcache, testrun)
            overlay_config = {'coast_dir': geodata, 'overlays': overlays}
            save_objects.append(new_scene.save_dataset(composite, base_dir='.', filename=sat+'-{name}-'+area+'.png',
                                    overlay=overlay_config, compute=False, fill_value=ffill_values[n]))
            n += 1
        compute_writer_results(save_objects)

    if tcomposites:
        global_scene.load(tcomposites, generate = True)
        # Native seviri datasets are 3712x3712 pixels (3km), 'HRV' is 11136x11136 pixels (1km)!!
        new_scene = global_scene.resample(area, **resampler_kwargs)  # ** defined in geostuff.py

        try: # This is for real (multichannel) composites
            layers, height, width = new_scene[tcomposites[0]].shape
        except: # In case of a single channel 'composite'
            height, width = new_scene[tcomposites[0]].shape

        n = 0
        for composite in tcomposites:
            # That's what we did up to now, it is slower but should work for all composites with BlackMarble backgrounds
            overlays = get_overlays(sat, composite, area, area_cities, height, width, ADDcoasts,
                                    ADDborders, ADDrivers, ADDlakes, ADDgrid, ADDcities, ADDpoints, ADDstation,
                                    OVRcache, testrun)
            new_scene.save_dataset(composite, sat + '-' + composite + '-' + area +'.png', overlay={'coast_dir': geodata,
                                      'overlays': overlays}, fill_value=tfill_values[n])
            n += 1
    return height

def get_prodir_areal_areaf(sat, area, testrun, **kwargs):
    # Get storage path, allow for special treatment of MSLP overlays
    if testrun:
        prodir = prodirs + '/' + 'TEST'
    else:
        basedir = kwargs.get('basedir', sat)
        subdir = kwargs.get('subdir', '')
        if subdir:
            prodir = prodirs + '/'+ basedir + '/' + subdir
        else:
            prodir = prodirs + '/' + basedir
    ADDtype = kwargs.get('ADDtype', '')
    if ADDtype:
        areal = area + '   (' + ADDtype + ')'
        areaf = area + '-' + ADDtype
    else:
        areal = area
        areaf = area

    return prodir, areal, areaf


def get_magick(Yea, Mon, Day, Hou, Min, EffHeight, logo1, logo2, service, channel, receiver, sat, sensor,
                   composite, area, testrun, ADDlegend=True, **kwargs):  # kwargs for MSPL charts + basedir/subdir
                   # If a user selects basedir/subdir it's his responsability that these exist (defaut is just sat)
                   # ADDlegend should work for SPS V 4.0 (Beta) scripts as well, if not provided it defaults to True

        satellite = get_long_name(sat)
        comp = get_abbr(sat, composite)
        ADDchart = kwargs.get('ADDchart', '')

        prodir, areal, areaf = get_prodir_areal_areaf(sat, area, testrun, **kwargs)

        INfilenames = sat+'-'+composite+'-'+area+'.png '+ADDchart
        OUTfilename = prodir+'/'+sat+'-'+Yea+Mon+Day+'-SLO-'+Hou+Min+'-'+composite+'-'+areaf

        if not ADDlegend:
            magick = convert+' '+INfilenames+OUTfilename+'-bare.jpg'
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

        legend = [' \'DATE:\'\" '     , ' \''+Yea+'/'+Mon+'/'+Day+'\'\" ',
                  ' \'TIME:\'\" '     , ' \''+Hou+':'+Min+' UTC'+'\'\" ',
                  ' \'SOURCE:\'\" '   , ' \'EUMETCast\'\" ',
                  ' \'SERVICE:\'\" '  , ' \''+service+'\'\" ',
                  ' \'CHANNEL:\'\" '  , ' \''+channel+'\'\" ',
                  ' \'RECEIVER:\'\" ' , ' \''+receiver+'\'\" ',
                  ' \'SATELLITE:\'\" ', ' \''+satellite+'\'\" ',
                  ' \'SENSOR:\'\" '   , ' \''+sensor+'\'\" ',
                  ' \'COMPOSITE:\'\" ', ' \''+comp+'\'\" ',
                  ' \'AREA:\'\" '     , ' \''+areal+'\'\" ']

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

        magick = convert+' '+INfilenames\
        + '-gravity west -background rgb'+escape+'(245,245,245'+escape+') -splice '+EffSplice+'x0 '\
        + logo1+' -gravity northwest -geometry '+EffLogo1s+'x'\
        + EffLogo1s+'+'+EffLogo1x+'+'+EffLogo1y+' -composite '\
        + logo2+' -gravity southwest -geometry '+EffLogo2s+'x'\
        + EffLogo2s+'+'+EffLogo2x+'+'+EffLogo2y+' -composite '\
        + '-pointsize '+EffPoints+' -gravity northwest '+multidraw\
        + OUTfilename+'.jpg'

        return magick
