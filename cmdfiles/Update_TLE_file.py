#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#*************************************************************************
# This script updates the TLE file found in directory toodir + '/satpyetc'
# It should be updated at least once a month in scheduled 24/7 TC systems.
# If you use this manually be sure to activate your (pytroll) environment.
#
# CH-3123 Belp, 2022/11/10        License GPL3          (c) Ernst Lobsiger
#*************************************************************************

import shutil, platform
from pyorbital import tlefile

OS = platform.system()

if OS == 'Linux':
    toodir = '/home/sps/SPStools'
elif OS == 'Windows':
    toodir = 'C:/SPStools'
else:
    sys.exit('Sorry, OS ' + OS + ' seems unsupported yet ...')

# Use old path name ppp
ppp = toodir + '/userconfig'
# If something goes wrong we still have a copy of the current TLE file in backup!
shutil.copy(ppp + '/' + 'my_TLE_file.txt', ppp + '/backup/' + 'old_TLE_file.txt')
tlefile.fetch(ppp + '/' + 'my_TLE_file.txt')

