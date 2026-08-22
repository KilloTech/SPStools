#!/bin/bash
# -x
#------------------------------------------------------
# Script that makes vp8 *.webm movies from *.jpg images
# **This is used for 24/7 movie production under cron**
# Uses a constant output frame rate of 6 for all movies
# Adds a common trailer scaled for all frame geometries
# Never run two instances with identical CLI parameters
# Two ffmpeg encodings cannot work with the same files!
# Uses local tmp to encode video, moves file when ready
#
# Needs $1 satellite name as used in product directory
# Needs $2 composite-area that is unique in frame names
# Needs $3 movie date as: today | yesterday | YYYYmmdd
# (YYYYmmDD must evaluate to a valid date!) | last24h |
# last48h | last72h (these are meant to be overwritten).
# Needs $4 for size reduction to H=1080 (1 | anything),
# if monitor with FullHD resolution 1080 x 1920 pixels.
#
# CH-3123 Belp, 2022/12/10   GPL3    (c) Ernst Lobsiger
#------------------------------------------------------

# Two top directories
TOODIR="$HOME/SPStools"
DATDIR="$HOME/SPSdata"

# ****************************************************
# Touch this stuff below only if you know what you do!
# ****************************************************

if [ "$4" == "1" ]
then # High resolution images that we reduce to FullHD
  frapath="$DATDIR/products/$1/images"
else # Special areas with FullHD or lower pixel numbers
  frapath="$DATDIR/products/$1/frames"
fi

introfra=9
trailfra=25
movpath="$DATDIR/products/$1/movies"
tmppath="$DATDIR/tmpdirs/ffmpeg"
font="$DATDIR/fonts/courbi.ttf"

case $3 in
today | yesterday)
  dat=`date -u -d $3 +%Y%m%d`
  files=`ls -tr $frapath/$1-$dat*-$2.jpg`
  ;;
????????)
  date -d $3 >/dev/null 2>&1
  if [ $? = 0 ]; then
    dat=`date -u -d $3 +%Y%m%d`
    files=`ls -tr $frapath/$1-$dat*-$2.jpg`
  else
    echo "Usage: $0 Satellite-name composite-area today|yesterday|YYYYmmDD|last24h|last48h|last72h"
    exit
  fi
  ;;
last24h)
  dat=$3
  files=`find $frapath/$1*-$2.jpg -maxdepth 1 -type f -mtime -1 -print0 | xargs -0 ls -tr`
  ;;
last48h)
  dat=$3
  files=`find $frapath/$1*-$2.jpg -maxdepth 1 -type f -mtime -2 -print0 | xargs -0 ls -tr`
  ;;
last72h)
  dat=$3
  files=`find $frapath/$1*-$2.jpg -maxdepth 1 -type f -mtime -3 -print0 | xargs -0 ls -tr`
  ;;
last4d)
  dat=$3
  files=`find $frapath/$1*-$2.jpg -maxdepth 1 -type f -daystart -mtime -5 -mmin +1441 -print0 | xargs -0 ls -tr`
  ;;
last6h)
  dat=$3
  files=`find $frapath/ -maxdepth 1 -name "$1*-$2.jpg" -type f -mmin -360 -print0 | xargs -0 ls -tr 2>/dev/null`
  ;;
*)
  echo "Usage: $0 Satellite-name composite-area today|yesterday|YYYYmmDD|last24h|last48h|last72h"
  exit
  ;;
esac

# Where does this script sit (absolute) ?
# This is needed because of AddTrailer.py
myHOME=`realpath $0`
myHOME=`dirname $myHOME`

# Frame prefix
fra=$1-$2

# Movie file name
mfn=$1-$dat-$2.webm

# Path must exist
cd $tmppath
if [ $? != 0 ] ; then
  echo $tmppath does not exist ...
  exit
fi

# Clean tmppath
rm -f $fra-*.jpg

# Counter
inum=0

for f in $files ; do
  # Integer comparison (( ))
  if (( $inum == 0 )) ; then
    ln -s $f $fra-0000.jpg
    inum=$((inum+1))
    # Wait a couple of frames (-r 6)
    for ((i=1; i<=$introfra; i++)) ; do
      num=$(printf "%04d" $inum)
      ln -s $f $fra-$num.jpg
      inum=$((inum+1))
    done
  else
    num=$(printf "%04d" $inum)
    ln -s $f $fra-$num.jpg
    inum=$((inum+1))
  fi
done

# Originally a 3712 x 3712 Meteosat image got 640 caption pixels added at left:
# This strip is 640/3712=0.1724 of the image height, Bash has no floating point
# We get the full image width 3712+640=4352 and have to find the original width
hokuspokus() {
  # We get (full) Width and Hight
  oriw=$(($1 - 1724 * $2 / 10000))
  offx=$(($1 - oriw))
  poin=$((oriw / 35))
  offx=$((offx + 2 * poin))
}
hokuspokus `identify -ping -format '%w %h' $f 2>/dev/null`

t0="Satpy Processing System (SPS) for EUMETCast V 4.1\n\n"
t1="HW       Fujitsu W520 Power, Xeon, 24GB RAM, 2013\n\n"
t2="OS       Devuan 3.0 Beowulf, amd64, GNU/Linux\n\n"
t3="Cron     All production chains are fully automated\n\n"
t4="Python   PyTROLL/SatPy, https://pytroll.github.io\n\n"
t5="Magick   https://imagemagick.org/script/index.php\n\n"
t6="FFmpeg   https://ffmpeg.org, https://trac.ffmpeg.org\n\n"
t7="Format   webp, webm, https://www.webmproject.org\n\n"
t8="ADMIN    Ernst Lobsiger, member \"Old Farts\", 1952"

# Now annotate this last frame, the text string *must* be on one script line !
lastnum=$(printf "%04d" $inum)
convert $f -modulate 60,60 -background transparent -fill white -gravity west \
 -pointsize $poin -font $font -annotate +$offx+0 "$t0$t1$t2$t3$t4$t5$t6$t7$t8" $fra-$lastnum.jpg

# If we do add 30 links (-r 6) to lastnum. This makes the trailer stay 5 seconds.
for ((i=1; i<=$trailfra; i++)) ; do
  inum=$((inum+1))
  num=$(printf "%04d" $inum)
  ln -s $fra-$lastnum.jpg $fra-$num.jpg
done

# Also Integer comparison (= equal ==)
if [ "$4" == "1" ]
then
  nice ffmpeg -y -r 6  -i $fra-%04d.jpg -filter:v "scale=w=-1:h=1080" -c:v libvpx -pix_fmt yuv420p -crf 20 -b:v 2M $mfn
else
  nice ffmpeg -y -r 6  -i $fra-%04d.jpg -c:v libvpx -pix_fmt yuv420p -crf 20 -b:v 2M $mfn
fi

# Move video when ready
mv -f $mfn $movpath
# If things go wrong ..
if [ $? != 0 ] ; then
  rm -f $mfn
fi

# Clean tmppath
rm -f $fra-*.jpg

exit 0
