#!/bin/bash
# **************************************************************************
# This updates your TLE file needed to find the segments that depict areas.
# It should be updated at least once a month in a scheduled 24/7 TC system.
# Call this as the GNU/Linux user that has Miniconda3 in the home directory!
#
# CH-3123 Belp, 2022/12/10           License GPL3         (c) Ernst Lobsiger
# **************************************************************************

# Top tools directory
TOODIR="$HOME/SPStools"

# Activate your Miniconda3 environment pytroll
source $HOME/miniconda3/bin/activate pytroll

#  Call the Python update script (absolute path)
nice python $TOODIR/cmdfiles/Update_TLE_file.py
