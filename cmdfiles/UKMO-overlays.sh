#!/bin/bash
# -x
# --------------------------------------------------------------
# Script to download (fullsize) UKMO Ground Pressure Charts from
# https://www.weathercharts.org and make PNG32 bb + ww overlays.
# Results are 2148 pixels wide and 1452 pixels high (area ukmol)
# Added smaller version for completeness 1040 x 727 (area ukmos)
#
# Pressure lines and text annotation black, needs fill_value=255
# ukmo-bb-YYYYmmddHHMM.png, Stereographic Projection,   6 hourly
# Pressure lines and text annotation white, needs fill_value = 0
# ukmo-ww-YYYYmmddHHMM.png, Stereographic Projection,   6 hourly
#
# This script has to be scheduled 02:05 and every 6 hours later.
# 05 2,8,14,20 * * * user script (05 2-20/6 * * *  also works !)
#
# CH-3123 Belp, 2022/12/10     License GPL3   (c) Ernst Lobsiger
#---------------------------------------------------------------

# Until further notice from UKMO we use this area for overlays:
# (this has been optimized under GNU/Linux, with minor changes)

#
# ukmos:
#   description: UK MetOffice (Small size Ground Pressure Overlay from www.weathercharts.net)
#   projection:
#     proj: stere
#     ellps: WGS84
#     lat_0:  90.0
#     lon_0: -35.0
#   shape:
#     height: 727
#     width: 1074
#   area_extent:
#     lower_left_xy:  [-2173000.0, -6325000.0]
#     upper_right_xy: [ 6328000.0,  -587500.0]
#
# ukmol:
#   description: UK MetOffice (Large size Ground Pressure Overlay from www.weathercharts.net)
#   projection:
#     proj: stere
#     ellps: WGS84
#     lat_0: 90.0
#     lon_0: -35.0
#   shape:
#     height: 1452
#     width:  2148
#   area_extent:
#     lower_left_xy: [-2180000.0, -6319000.0]
#     upper_right_xy: [6328000.0, -588000.0]
#

# Top data directory
DATDIR="$HOME/SPSdata"

# ****************************************************
# Touch this stuff below only if you know what you do!
# ****************************************************

# You must have write access to TMP_DIR (a working directory)
TMP_DIR="/tmp"
# Processed overlays go in this directory
OVR_DIR="$DATDIR/overlays"

# The only place I found that has the ukmo fullsize version
BASE_URL="https://www.weathercharts.net/ukmo_mslp_analysis"
UKMOS="ppva.gif"
UKMOL="ppva_fullsize.gif"
TMP_BASE="fetchMetOffice"
LOCK_FILE="$TMP_BASE.lock"

# Devuan 3.0 Beowulf
WGET="/usr/bin/wget"
CONVERT="/usr/bin/convert"
FIND="/usr/bin/find"


# Check lock file
if [ -f $TMP_DIR/$LOCK_FILE ]
then
   echo "Script already running!"
   exit 1
fi

# Handle signals
trap 'exithandler' 0 1 2 15
exithandler() {
   rm -f $TMP_DIR/$LOCK_FILE $TMP_DIR/$UKMOS $TMP_DIR/$UKMOL
}

# Setup lock file with PID
echo "$$" > $TMP_DIR/$LOCK_FILE

$WGET -P $TMP_DIR $BASE_URL/$UKMOS
if [ ! -f $TMP_DIR/$UKMOS ]
then
   echo "Download $UKMOS failed"
   exit 1
else
   UnixTime=`stat -c%Y $TMP_DIR/$UKMOS`
   UkmoTime=$((UnixTime/21600*21600))
   UkmoTime=`date -u -d @$UkmoTime +%Y%m%d%H00`
   $CONVERT $TMP_DIR/$UKMOS -crop 1070x723+2+33 -bordercolor black -border 2x2 -threshold 80% +antialias -transparent white PNG32:$OVR_DIR/ukmos/ukmos-bb-$UkmoTime.png
   $CONVERT $TMP_DIR/$UKMOS -crop 1070x723+2+33 -bordercolor black -border 2x2 -threshold 80% +antialias -negate -transparent black PNG32:$OVR_DIR/ukmos/ukmos-ww-$UkmoTime.png
fi

$WGET -P $TMP_DIR $BASE_URL/$UKMOL
if [ ! -f $TMP_DIR/$UKMOL ]
then
   echo "Download $UKMOL failed"
   exit 1
else
   UnixTime=`stat -c%Y $TMP_DIR/$UKMOL`
   UkmoTime=$((UnixTime/21600*21600))
   UkmoTime=`date -u -d @$UkmoTime +%Y%m%d%H00`
   $CONVERT $TMP_DIR/$UKMOL -crop 2142x1446+3+66 -bordercolor black -border 3x3 -threshold 80% -transparent white PNG32:$OVR_DIR/ukmol/ukmol-bb-$UkmoTime.png
   $CONVERT $TMP_DIR/$UKMOL -crop 2142x1446+3+66 -bordercolor black -border 3x3 -threshold 80% -negate -transparent black PNG32:$OVR_DIR/ukmol/ukmol-ww-$UkmoTime.png
fi

exit 0
