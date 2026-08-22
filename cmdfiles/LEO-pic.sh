#!/bin/bash
# -x
# -------------------------------------------------------------------------
# This script can be used by CRON or interactively by the USER at any time.
# A lock is used to prevent two scripts of the same LEO satellite to run at
# the same time as there is only *one* XSAT tmp directory per LEO satellite.
#
# Needs $1 basename of satpy script in $HOME/SPStools/LEOscripts/ to run
# Needs $2 as a single word that date understands to form a YYYYmmdd pass
# This includes YYYmmdd|now|today|yesterday|-22min (as counted from now)
# Needs $3 either 'NIG' for pass on the dark side or 'DAY' on the lit side
# Needs $4 +time in seconds this script will wait if XSAT is being used!
#
# NOTE: In the case of more than one instances running/waiting concurrently
# the lock_file is removed at exit of the first instance. This doesn't mean
# that the locking is all over as flock() works with File Descriptors (FDs).
# There must be a *unique* lock_file name and FD per satellite (see case!).
#
# CH-3123 Belp, 2022/12/10         License GPL3          (c) Ernst Lobsiger
# -------------------------------------------------------------------------


# This is the recommended place for LEO scripts
SATPY_SCRIPT_PATH="$HOME/SPStools/LEOscripts"

# Check script parameters
if (( $# != 4 )) ; then
  echo USAGE: `basename $0`  LEOSAT-area.py TimeOffsetMin|YYYYmmdd DoN wait_time_seconds
  exit 1
fi

# Exit if the given script does not exist
if [ ! -f $SATPY_SCRIPT_PATH/$1 ]; then
  echo $SATPY_SCRIPT_PATH/$1 does not exist ...
  exit 1
fi

# Get the sat name from the script
sat=`echo $1 | cut -d '-' -f1`

# Test if $2 represents a valid pass date YYYYmmdd|now|today|yesterday|-22min
pass=`date -u -d "$2" +"%Y%m%d"`
if [ $? != 0 ] ; then
   echo $2 does not evaluate to a valid YYYYmmdd LEO satellite pass date ...
   exit 1
fi

# Test if $3 is either 'NIG' or 'DAY'
if  [ $3 != "NIG" ] && [ $3 != "DAY" ]; then
   echo $3 should either be NIG or DAY ...
   exit 1
fi

# Check whether we have a valid maximum flock() wait time
if (( $4 < 1 )) || (( $4 > 3600 )) ; then
  echo $4 is not an acceptable maximum wait time for flock ...
  exit 1
fi


#*********************************************************************
# !! DO NOT TOUCH THE FILE DESCRIPTORS (FD) USED BY flock() BELOW !! *
#*********************************************************************

# You must have write access here!
lock_file="/var/run/lock/$sat.lck"
trap 'rm -f $lock_file' EXIT

case $sat in
Aqua)
  exec 201>$lock_file || exit 1
  FD=201
  ;;
Terra)
  exec 202>$lock_file || exit 1
  FD=202
  ;;
MetopB)
  exec 203>$lock_file || exit 1
  FD=203
  ;;
MetopC)
  exec 204>$lock_file || exit 1
  FD=204
  ;;
MetopX)
  exec 205>$lock_file || exit 1
  FD=205
  ;;
Sen3A)
  exec 206>$lock_file || exit 1
  FD=206
  ;;
Sen3B)
  exec 207>$lock_file || exit 1
  FD=207
  ;;
Sen3X)
  exec 208>$lock_file || exit 1
  FD=208
  ;;
NOAA20)
  exec 209>$lock_file || exit 1
  FD=209
  ;;
SNPP)
  exec 210>$lock_file || exit 1
  FD=210
  ;;
NOAAX)
  exec 211>$lock_file || exit 1
  FD=211
  ;;
FY3D)
  exec 212>$lock_file || exit 1
  FD=212
  ;;
*)
  echo $sat is not a LEO satellite treated by this script ...
  exit 1
  ;;
esac

#*********************************************************************
# !! DO NOT TOUCH THE FILE DESCRIPTORS (FD) USED BY flock() ABOVE !! *
#*********************************************************************

echo Waiting up to $4 seconds to get a lock for LEO satellite $sat ...

# Exit if invalid wait seconds given
flock --verbose  -w $4 $FD ||  exit 1

source $HOME/miniconda3/bin/activate pytroll
nice python $SATPY_SCRIPT_PATH/$1 ${pass:0:8}$3

exit 0
