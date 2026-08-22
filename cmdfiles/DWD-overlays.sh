#!/bin/bash
# -x
# -----------------------------------------------------------
# Script to download Ground Pressure Charts from DWD OpenData
# dwda   Western Europe, lcc    3 hourly   SW = black & white
# dwdna  North Atlantic, lcc    6 hourly   SW = black & white
# dwdc   Polar Stereographic   12 hourly   SW = black & white
# dwdi   Central Europe, lcc   12 hourly   only black & white
#
# Downloaded files named Z__C_EDZW*.png go into the directory
# TMP_DIR and are removed after having been overlay processed
# Tested to work under Devuan 3.0 Beowulf amd64    2022/09/27
#
# CH-3123 Belp, 2022/12/10  License GPL3   (c) Ernst Lobsiger
# -----------------------------------------------------------

# Top data directory
DATDIR="$HOME/SPSdata"

# ****************************************************
# Touch this stuff below only if you know what you do!
# ****************************************************

# You must have write access to TMP_DIR (a working directory)
# File $FILE_LIST_OLD of recent downloads will be kept there!
TMP_DIR="/tmp"
# Processed overlays go in this directory
OVR_DIR="$DATDIR/overlays"

# Devuan 3.0 Beowulf
WGET="/usr/bin/wget"
BUNZIP2="/bin/bunzip2"
CONVERT="/usr/bin/convert"
FIND="/usr/bin/find"

# DWD Open Data Server
BASE_URL="https://opendata.dwd.de/weather/charts/"
WHAT_WE_WANT="analysis/Z__C_EDZW.*(dwda|dwdna|dwdc|p00_na)"
CONTENT_LOG_BZ2="content.log.bz2"
FILE_LIST="file.list"
FILE_LIST_OLD="$FILE_LIST.old"
TMP_BASE="fetchOpenData"
TODO_LIST="$TMP_BASE.todo"
LOCK_FILE="$TMP_BASE.lock"

if [ -f $TMP_DIR/$LOCK_FILE ]
then
   echo "ERROR: DWD script already running!"
   exit 1
fi

# Handle signals
trap 'exithandler' 0 1 2 15
exithandler() {
   rm -f $TMP_DIR/$LOCK_FILE $TMP_DIR/$TODO_LIST $TMP/$FILE_LIST $TMP_DIR/Z__C_EDZW*.png
}

# Write PID into lock file
echo "$$" > $TMP_DIR/$LOCK_FILE
if [ $? != '0' ]
then
   echo "ERROR: No write access to $TMP_DIR ..."
   exit 1
fi

# Change directory
cd $TMP_DIR
if [ $? != '0' ]
then
   echo "ERROR: Cannot change to $TMP_DIR ..."
   exit 1
fi


$WGET -q -O - ${BASE_URL}${CONTENT_LOG_BZ2} | $BUNZIP2 | egrep -v $CONTENT_LOG_BZ2 | cut -f 1 -d "|" | egrep $WHAT_WE_WANT | sort > $FILE_LIST

if [ ! -f $FILE_LIST ]
then
   echo "ERROR: DWD download failed"
   exit 1
fi

if [ -f $FILE_LIST_OLD ]
then
   diff $FILE_LIST $FILE_LIST_OLD | egrep "<" | sed s/\<\ .// | sed "s,^\/,$BASE_URL," > $TODO_LIST
else
   cat $FILE_LIST | sed "s,^.\/,$BASE_URL," > $TODO_LIST
fi

if [ -s $TODO_LIST ]
then
   $WGET -nd -q -np -i $TODO_LIST
fi

mv $FILE_LIST $FILE_LIST_OLD


# ------------------------------------------------------------------
# Now we do produce DWD (mostly transparent, PNG32) surface pressure
# overlays of use for PyTROLL/Satpy. Naming of overlays is as below:
#
# Pressure lines and text annotation black, needs fill_value = 255
# dwda-bc-YYYYmmddHHMM.png  Western Europe, black + color,  3 hourly
# dwda-bb-YYYYmmddHHMM.png  Western Europe, black + black,  3 hourly
# dwdn-bc-YYYYmmddHHMM.png  North Atlantic, black + color,  6 hourly
# dwdn-bb-YYYYmmddHHMM.png  North Atlantic, black + black,  6 hourly
# dwdc-bc-YYYYmmddHHMM.png  Stereographic,  black + color, 12 hourly
# dwdc-bb-YYYYmmddHHMM.png  Stereographic,  black + black, 12 hourly
# dwdi-bb-YYYYmmddHHMM.png  Central Europe, black + black, 12 hourly

# Pressure lines and text annotation white, needs fill_value =  0
# dwda-wc-YYYYmmddHHMM.png  Western Europe, white + color,  3 hourly
# dwda-ww-YYYYmmddHHMM.png  Western Europe, white + white,  3 hourly
# dwdn-wc-YYYYmmddHHMM.png  North Atlantic, white + color,  6 hourly
# dwdn-ww-YYYYmmddHHMM.png  North Atlantic, white + white,  6 hourly
# dwdc-wc-YYYYmmddHHMM.png  Stereographic,  white + color, 12 hourly
# dwdc-ww-YYYYmmddHHMM.png  Stereographic,  white + white, 12 hourly
# dwdi-ww-YYYYmmddHHMM.png  Central Europe, white + white, 12 hourly
#
# Overlay type 'bc' means 'black' pressure lines, color front lines
# Overlay type 'wc' means 'white' pressure lines, color front lines
# Overlay type 'bb' means 'black' pressure lines, black front lines
# Overlay type 'ww' means 'white' pressure lines, white front lines
#
# Input images from opendata.dwd.de, ImageMagick *must* be installed
# Used projections have been guessed and calculated (see areas.yaml)
# ------------------------------------------------------------------

# Main DWD colors
red="#ff0000"
blue="#0000ff"
black="#000000"
white="#ffffff"
violet="#ee82ee"
# Added for dwdi
gray20="#333333"


# Process all DWD colored overlays
for f in `ls Z__C_EDZW*WV12.png 2>/dev/null`
do
   area="${f:42:4}"
   case $area in
   dwda)
      echo "Processing Western Europe colored"
      tim="${f:63:12}"
   ;;
   dwdn)
      echo "Processing North Atlantic colored"
      tim="${f:64:12}"
   ;;
   dwdc)
      echo "Processing Stereographic  colored"
      tim="${f:63:12}"
   ;;
   esac
   $CONVERT $f +transparent $blue \( $f +transparent $red \) -composite \( $f +transparent $violet \) -composite \( $f +transparent $black \) -composite PNG32:$OVR_DIR/$area/$area-bc-$tim.png
   $CONVERT $f -negate +transparent $white \( $f +transparent $red \) -composite \( $f +transparent $violet \) -composite \( $f +transparent $blue \) -composite PNG32:$OVR_DIR/$area/$area-wc-$tim.png
done

# Process all DWD monochrome overlays
for f in `ls Z__C_EDZW*WV12SW.png 2>/dev/null`
do
   area="${f:42:4}"
   case $area in
   dwda)
      echo "Processing Western Europe monochrome"
      tim="${f:63:12}"
   ;;
   dwdn)
      echo "Processing North Atlantic monochrome"
      tim="${f:64:12}"
   ;;
   dwdc)
      echo "Processing Stereographic  monochrome"
      tim="${f:63:12}"
   ;;
   esac
   $CONVERT $f -threshold 80% -transparent $white PNG32:$OVR_DIR/$area/$area-bb-$tim.png
   $CONVERT $f -threshold 80% -negate -transparent $black PNG32:$OVR_DIR/$area/$area-ww-$tim.png
done

# Process DWD ICON13 MSLP overlays. These files have different colors from text antialiasing. Pressure lines are gray20.
for f in `ls Z__C_EDZW*WV11.png 2>/dev/null`
do
   area="dwdi"
   tim="${f:58:12}"
   echo "Processing Central Europe monochrome"
   $CONVERT $f -threshold 80% \( $f -fill $black -opaque $gray20 +transparent $black \) -composite -transparent $white PNG32:$OVR_DIR/$area/$area-bb-$tim.png
   $CONVERT $f -threshold 80% \( $f -fill $black -opaque $gray20 +transparent $black \) -composite -negate -transparent $black PNG32:$OVR_DIR/$area/$area-ww-$tim.png
done

exit 0