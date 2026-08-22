#!/bin/bash
# -x
# -------------------------------------------------------------------------
# This script can be used by CRON or interactively by the USER at any time.
# A lock is used to prevent two scripts of the same GEO satellite to run at
# the same time as there is only *one* XSAT tmp directory per GEO satellite.
#
# Needs $1 basename of satpy script in $HOME/SPStools/GEOscripts/ to run
# Needs $2 time offset like -22min to start the right slot (/etc/crontab)
# Needs $2 as a valid time slot YYYYmmddHHMM if started by USER at prompt
# Needs $3 +time in seconds this script will wait if XSAT is being used!
#
# NOTE: In the case of more than one instances running/waiting concurrently
# the lock_file is removed at exit of the first instance. This doesn't mean
# that the locking is all over as flock() works with File Descriptors (FDs).
# There must be a *unique* lock_file name and FD per satellite (see case!).
#
# CH-3123 Belp, 2022/12/10         License GPL3          (c) Ernst Lobsiger
# -------------------------------------------------------------------------


# This is the recommended place for croned GEO scripts
SATPY_SCRIPT_PATH="$HOME/SPStools/GEOscripts"


# Check script parameters
if (( $# != 3 )) ; then
  echo USAGE: `basename $0`  GEOSAT-area.py TimeOffsetMin|YYYYmmddHHMM wait_time_seconds
  exit 1
fi

# Exit if the given script does not exist
if [ ! -f $SATPY_SCRIPT_PATH/$1 ]; then
  echo $SATPY_SCRIPT_PATH/$1 does not exist ...
  exit 1
fi

# Get the sat name from the script
sat=`echo $1 | cut -d '-' -f1`

# Test if $2 represents a valid slot YYYYmmddHHMM|-22min (as counted from now)
# This might still go wrong if we get a time slot like 202110151217 (17 != 15)
slot=`date -u -d "$2" +"%Y%m%d%H%M"`
if [ $? != 0 ] ; then
  slot=$2
  slot="${slot:0:8} ${slot:8:2}:${slot:10:2}"
  echo ------------------ $slot
  slot=`date -u -d "$slot" +"%Y%m%d%H%M"`
  if [ ! $? = 0 ] ; then
    echo $2 does not evaluate to a valid YYYYmmddHHMM GEO satellite slot ...
    exit 1
  fi
fi

# Check whether we have a valid maximum flock() wait time
if (( $3 < 1 )) || (( $3 > 3600 )) ; then
  echo $3 is not an acceptable maximum wait time for flock ...
  exit 1
fi


#*********************************************************************
# !! DO NOT TOUCH THE FILE DESCRIPTORS (FD) USED BY flock() BELOW !! *
#*********************************************************************

# You must have write access here!
lock_file="/var/run/lock/$sat.lck"
trap 'rm -f $lock_file' EXIT

case $sat in
MTI1)
  exec 101>$lock_file || exit 1
  FD=101
  ;;
MSG2)
  exec 102>$lock_file || exit 1
  FD=102
  ;;
MSG3)
  exec 103>$lock_file || exit 1
  FD=103
  ;;
MSG4)
  exec 104>$lock_file || exit 1
  FD=104
  ;;
GOES16)
  exec 105>$lock_file || exit 1
  FD=105
  ;;
GOES17)
  exec 106>$lock_file || exit 1
  FD=106
  ;;
GOES18)
  exec 107>$lock_file || exit 1
  FD=107
  ;;
HIMA8)
  exec 108>$lock_file || exit 1
  FD=108
  ;;
*)
  echo $sat is not a GEO satellite treated by this script ...
  exit 1
  ;;
esac

#*********************************************************************
# !! DO NOT TOUCH THE FILE DESCRIPTORS (FD) USED BY flock() ABOVE !! *
#*********************************************************************

echo Waiting up to $3 seconds to get a lock for GEO satellite $sat ...

# Exit if invalid wait seconds given
flock --verbose  -w $3 $FD ||  exit 1

source $HOME/miniconda3/bin/activate pytroll
# Latest date command sometimes adds "00" (seconds)
nice python $SATPY_SCRIPT_PATH/$1 ${slot:0:12}

exit 0
