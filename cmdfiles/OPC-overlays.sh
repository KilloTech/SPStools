#!/bin/bash
# -x
# --------------------------------------------------------------
# Script to download (colorized) OPC Ground Pressure Charts from
# https://www.ocean.weather.gov and make PNG32 bc + wc overlays.
#
# Overlays are 1776 pixels wide and 1562 pixels high (all areas)
#
# Pressure lines + text black, rest color, needs fill_value=255
# opcxy-bc-YYYYmmddHHMM.png, Mercator Projection,  6 hourly
# Pressure lines + text white, rest color, needs fill_value = 0
# opcxy-wc-YYYYmmddHHMM.png, Mercator Projection,  6 hourly
#
# This script has to be scheduled 03:45 and every 6 hours later.
# 45 3,9,15,21 * * * user script (45 3-21/6 * * *  also works !)
#
# CH-3123 Belp, 2022/12/10    License GPL3    (c) Ernst Lobsiger
#---------------------------------------------------------------

# These two files are used to make OPC overlays for MSG4, GOES16, GOES18, Himawari-8
# A_sfc_full_ocean_color.png, Atlantic, valid 1200, typically issued 14:39, 6 hourly
# P_sfc_full_ocean_color.png, Pacific,  valid 1200, typically issued 15:05, 6 hourly
# There is a 50° overlap of the resulting charts for both PacificW/E and AtlanticW/E

# opcpe:
#   description: NOAA/OPC Pacific East Mercator (Surface Pressure Overlay, lat_ts=0.0)
#   projection:
#     proj: merc
#     ellps: WGS84
#     lon_0: -155.0
#   shape:
#     height: 1562
#     width:  1776
#   area_extent:
#     lower_left_xy: [-4457000.0,  1795000.0]
#     upper_right_xy: [4457000.0,  9600000.0]
#
# Area definitions for opcpw, opcae and opcaw do only differ in center meridian lon_0

# Top data directory
DATDIR="$HOME/SPSdata"

# ****************************************************
# Touch this stuff below only if you know what you do!
# ****************************************************

# You must have write access to TMP_DIR (a working directory)
# Downloaded files are deleted after overlays have been made!
TMP_DIR="/tmp"
# Processed overlays go into this directory
OVR_DIR="$DATDIR/overlays"

# Devuan 3.0 Beowulf
WGET="/usr/bin/wget"
CONVERT="/usr/bin/convert"
FIND="/usr/bin/find"

# NOAA Ocean Prediction Center
BASE_URL="https://ocean.weather.gov"
WHAT_WE_WANT="A_sfc_full_ocean_color.png P_sfc_full_ocean_color.png"
TMP_BASE="OPC-overlays"
LOCK_FILE="$TMP_BASE.lock"

if [ -f $TMP_DIR/$LOCK_FILE ]
then
   echo "ERROR: OPC script already running!"
   exit 1
fi

# Handle signals
trap 'exithandler' 0 1 2 15
exithandler() {
   rm -f $TMP_DIR/$LOCK_FILE $TMP_DIR/*_sfc_full_ocean_color.png*
}

# Write PID into lock file
echo "$$" > $TMP_DIR/$LOCK_FILE
if [ $? != '0' ]
then
   echo "ERROR: No write access to $TMP_DIR ..."
   exit 1
fi

# If we cut the eastern Atlantic from the full_ocean image we have no lat labels!!
# So I decided to add these labels with IM and also polish the rest of the labels.

# Atlantic ocean western part        (overwrite OPC lat labels)
lat60N="rectangle 1, 237,42, 259" ; txt60N="text  +5+255 '60N'"
lat50N="rectangle 1, 627,42, 649" ; txt50N="text  +5+645 '50N'"
lat40N="rectangle 1, 941,42, 963" ; txt40N="text  +5+959 '40N'"
lat30N="rectangle 1,1213,42,1235" ; txt30N="text +5+1231 '30N'"
lat20N="rectangle 1,1458,42,1480" ; txt20N="text +5+1476 '20N'"

# Atlantic ocean eastern part (add missing lat labels in the middle)
lam60N="rectangle 667, 237,708, 259" ; txm60N="text  +671+255 '60N'"
lam50N="rectangle 667, 627,708, 649" ; txm50N="text  +671+645 '50N'"
lam40N="rectangle 667, 941,708, 963" ; txm40N="text  +671+959 '40N'"
lam30N="rectangle 667,1213,708,1235" ; txm30N="text +671+1231 '30N'"
lam20N="rectangle 667,1458,708,1480" ; txm20N="text +671+1476 '20N'"

# Atlantic ocean eastern and western part    (overwrite OPC lon labels)
lon90W="rectangle  196,1534, 240,1557" ; txt90W="text  +200+1553 '90W'"
lon80W="rectangle  418,1534, 462,1557" ; txt80W="text  +422+1553 '80W'"
lon70W="rectangle  640,1534, 684,1557" ; txt70W="text  +644+1553 '70W'"
lon60W="rectangle  862,1534, 906,1557" ; txt60W="text  +866+1553 '60W'"
lon50W="rectangle 1084,1534,1128,1557" ; txt50W="text +1088+1553 '50W'"
lon40W="rectangle 1305,1534,1349,1557" ; txt40W="text +1309+1553 '40W'"
lon30W="rectangle 1527,1534,1571,1557" ; txt30W="text +1531+1553 '30W'"
lon20W="rectangle 1749,1534,1793,1557" ; txt20W="text +1753+1553 '20W'"
lon10W="rectangle 1971,1538,2015,1557" ; txt10W="text +1975+1553 '10W'"
lon00W="rectangle 2198,1538,2242,1557" ; txt00W="text +2202+1553 '00W'"

# Pacific ocean eastern and western part        (overwrite OPC lon labels)
lon140E="rectangle   78,1534, 132,1557" ; txt140E="text   +83+1553 '140E'"
lon150E="rectangle  300,1534, 354,1557" ; txt150E="text  +305+1553 '150E'"
lon160E="rectangle  522,1534, 576,1557" ; txt160E="text  +527+1553 '160E'"
lon170E="rectangle  744,1534, 798,1557" ; txt170E="text  +749+1553 '170E'"
lon180E="rectangle  966,1534,1020,1557" ; txt180E="text  +979+1553 '180'"
lon170W="rectangle 1188,1534,1242,1557" ; txt170W="text +1192+1553 '170W'"
lon160W="rectangle 1409,1534,1463,1557" ; txt160W="text +1413+1553 '160W'"
lon150W="rectangle 1631,1534,1685,1557" ; txt150W="text +1635+1553 '150W'"
lon140W="rectangle 1853,1534,1907,1557" ; txt140W="text +1857+1553 '140W'"
lon130W="rectangle 2075,1534,2129,1557" ; txt130W="text +2079+1553 '130W'"
lon120W="rectangle 2297,1534,2351,1557" ; txt120W="text +2301+1553 '120W'"

# Pacific ocean eastern and western part  (overwrite OPC lat labels)
lpm60N="rectangle 954, 237,995, 259" ; tpm60N="text  +958+255 '60N'"
lpm50N="rectangle 954, 627,995, 649" ; tpm50N="text  +958+645 '50N'"
lpm40N="rectangle 954, 941,995, 963" ; tpm40N="text  +958+959 '40N'"
lpm30N="rectangle 954,1213,995,1235" ; tpm30N="text +958+1231 '30N'"
lpm20N="rectangle 954,1458,995,1480" ; tpm20N="text +958+1476 '20N'"


# We start with images 2441 x 1600 pixels that are kind of overly colored.
# Especially coast lines and text are not black and countours *ugly* brown.
# Unfortunately there are two different palettes used on both Atlantic and
# Pacific charts. Trying to use -fuzz 10% when changing colors didn't work.
# Very rare, only found twice, #00514A is a dark green || front break mark.

for f in $WHAT_WE_WANT
do
   $WGET  -P $TMP_DIR $BASE_URL/$f
   if [ ! -f $TMP_DIR/$f ]
   then
      echo "ERROR: OPC download failed"
      exit 1
   else
      UnixTime=`stat -c%Y $TMP_DIR/$f`
      OpcTime=$((UnixTime/21600*21600))
      OpcTime=`date -u -d "@$OpcTime" +%Y%m%d%H00`

      if [ ${f:0:1} == "A" ]
      then
         # Atlantic ocean western part (GOES16)
         area="opcaw"
         $CONVERT $TMP_DIR/$f -fill black -opaque '#001c21' -fill black -opaque '#001b23' \
            \( $TMP_DIR/$f -fill black -opaque '#00514a' +transparent black \) -composite \
            \( $TMP_DIR/$f -fill black -opaque '#de7100' +transparent black \) -composite \
            \( $TMP_DIR/$f -fill black -opaque '#e16f00' +transparent black \) -composite \
            \( $TMP_DIR/$f -fill black -opaque '#0059ad' +transparent black \) -composite \
            \( $TMP_DIR/$f -fill black -opaque '#005ab0' +transparent black \) -composite \
             -fill white -stroke black -pointsize 18 +antialias \
             -draw "$lat60N" -draw "$lat50N" -draw "$lat40N" -draw "$lat30N" \
             -draw "$lat20N" -draw "$lon90W" -draw "$lon80W" -draw "$lon70W" \
             -draw "$lon60W" -draw "$lon50W" -draw "$lon40W" -draw "$lon30W" \
             -draw "$lon20W" -fill black \
             -draw "$txt60N" -draw "$txt50N" -draw "$txt40N" -draw "$txt30N" \
             -draw "$txt20N" -draw "$txt90W" -draw "$txt80W" -draw "$txt70W" \
             -draw "$txt60W" -draw "$txt50W" -draw "$txt40W" -draw "$txt30W" \
             -draw "$txt20W" -transparent white -crop 1776x1562+0+0 \
             PNG32:$OVR_DIR/$area/$area-bc-$OpcTime.png
         $CONVERT $OVR_DIR/$area/$area-bc-$OpcTime.png -fill white -opaque black \
             PNG32:$OVR_DIR/$area/$area-wc-$OpcTime.png
         # Atlantic ocean eastern part (MSG4)
         area="opcae"
         $CONVERT $TMP_DIR/$f -fill black -opaque '#001c21' -fill black -opaque '#001b23' \
            \( $TMP_DIR/$f -fill black -opaque '#00514a' +transparent black \) -composite \
            \( $TMP_DIR/$f -fill black -opaque '#de7100' +transparent black \) -composite \
            \( $TMP_DIR/$f -fill black -opaque '#e16f00' +transparent black \) -composite \
            \( $TMP_DIR/$f -fill black -opaque '#0059ad' +transparent black \) -composite \
            \( $TMP_DIR/$f -fill black -opaque '#005ab0' +transparent black \) -composite \
             -fill white -stroke black -pointsize 18 +antialias \
             -draw "$lam60N" -draw "$lam50N" -draw "$lam40N" -draw "$lam30N" \
             -draw "$lam20N" -draw "$lon60W" -draw "$lon50W" -draw "$lon40W" \
             -draw "$lon30W" -draw "$lon20W" -draw "$lon10W" -draw "$lon00W" \
             -fill black \
             -draw "$txm60N" -draw "$txm50N" -draw "$txm40N" -draw "$txm30N" \
             -draw "$txm20N" -draw "$txt60W" -draw "$txt50W" -draw "$txt40W" \
             -draw "$txt30W" -draw "$txt20W" -draw "$txt10W" -draw "$txt00W" \
             -transparent white -crop 1776x1562+665+0 \
             PNG32:$OVR_DIR/$area/$area-bc-$OpcTime.png
         $CONVERT $OVR_DIR/$area/$area-bc-$OpcTime.png -fill white -opaque black PNG32:$OVR_DIR/$area/$area-wc-$OpcTime.png
      else
         # Pacific ocean western part (HIMA-8)
         area="opcpw"
         $CONVERT $TMP_DIR/$f -fill black -opaque '#001c21' -fill black -opaque '#001b23' \
            \( $TMP_DIR/$f -fill black -opaque '#00514a' +transparent black \) -composite \
            \( $TMP_DIR/$f -fill black -opaque '#de7100' +transparent black \) -composite \
            \( $TMP_DIR/$f -fill black -opaque '#e16f00' +transparent black \) -composite \
            \( $TMP_DIR/$f -fill black -opaque '#0059ad' +transparent black \) -composite \
            \( $TMP_DIR/$f -fill black -opaque '#005ab0' +transparent black \) -composite \
             -fill white -stroke black -pointsize 18 +antialias \
             -draw "$lpm60N"  -draw "$lpm50N"  -draw "$lpm40N"  -draw "$lpm30N"  \
             -draw "$lpm20N"  -draw "$lon140E" -draw "$lon150E" -draw "$lon160E" \
             -draw "$lon170E" -draw "$lon180E" -draw "$lon170W" -draw "$lon160W" \
             -draw "$lon150W" -fill black \
             -draw "$tpm60N"  -draw "$tpm50N"  -draw "$tpm40N"  -draw "$tpm30N"  \
             -draw "$tpm20N"  -draw "$txt140E" -draw "$txt150E" -draw "$txt160E" \
             -draw "$txt170E" -draw "$txt180E" -draw "$txt170W" -draw "$txt160W" \
             -draw "$txt150W" -transparent white -crop 1776x1562+0+0 \
             PNG32:$OVR_DIR/$area/$area-bc-$OpcTime.png
         $CONVERT $OVR_DIR/$area/$area-bc-$OpcTime.png -fill white -opaque black \
             PNG32:$OVR_DIR/$area/$area-wc-$OpcTime.png
         # Pacific ocean eastern part (GOES17)
         area="opcpe"
         $CONVERT $TMP_DIR/$f -fill black -opaque '#001c21' -fill black -opaque '#001b23' \
            \( $TMP_DIR/$f -fill black -opaque '#00514a' +transparent black \) -composite \
            \( $TMP_DIR/$f -fill black -opaque '#de7100' +transparent black \) -composite \
            \( $TMP_DIR/$f -fill black -opaque '#e16f00' +transparent black \) -composite \
            \( $TMP_DIR/$f -fill black -opaque '#0059ad' +transparent black \) -composite \
            \( $TMP_DIR/$f -fill black -opaque '#005ab0' +transparent black \) -composite \
             -fill white -stroke black -pointsize 18 +antialias \
             -draw "$lpm60N"  -draw "$lpm50N"  -draw "$lpm40N"  -draw "$lpm30N"  \
             -draw "$lpm20N"  -draw "$lon170E" -draw "$lon180E" -draw "$lon170W" \
             -draw "$lon160W" -draw "$lon150W" -draw "$lon140W" -draw "$lon130W" \
             -draw "$lon120W" -fill black \
             -draw "$tpm60N"  -draw "$tpm50N"  -draw "$tpm40N"  -draw "$tpm30N"  \
             -draw "$tpm20N"  -draw "$txt170E" -draw "$txt180E" -draw "$txt170W" \
             -draw "$txt160W" -draw "$txt150W" -draw "$txt140W" -draw "$txt130W" \
             -draw "$txt120W" -transparent white -crop 1776x1562+665+0 \
             PNG32:$OVR_DIR/$area/$area-bc-$OpcTime.png
         $CONVERT $OVR_DIR/$area/$area-bc-$OpcTime.png -fill white -opaque black \
             PNG32:$OVR_DIR/$area/$area-wc-$OpcTime.png
      fi
   fi
done

exit 0
