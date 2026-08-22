#!/bin/bash
# -------------------------------------------------------------------------
# Cron job to remove old EUMETCast products      (RSS frames most critical)
# NOTE: -mtime n is n*24 hours ago, -mmin n is n minutes ago (1day=1440min)
# If you change the layout of your system or add products change this too!!
#
# CH-3123 Belp, 2022/12/10          License GPL3         (c) Ernst Lobsiger
# -------------------------------------------------------------------------

# Top data directory
datdir=$HOME/SPSdata


# DEBUG is /dev/stdout or /dev/null
DEBUG=/dev/null
products=$datdir/products
overlays=$datdir/overlays
xtmpdirs=$datdir/tmpdirs

GEOtrim()
{
  find $products/$1/frames/ -maxdepth 1 -name "*.jpg" -type f -mmin +$2 -exec rm {} \; 2>$DEBUG
  find $products/$1/images/ -maxdepth 1 -name "*.jpg" -type f -mtime +$3 -exec rm {} \; 2>$DEBUG
  find $products/$1/movies/ -maxdepth 1 -name "*.webm" -type f -mtime +$4 -exec rm {} \; 2>$DEBUG
}
LEOtrim()
{
  find $products/$1/NIG/ -maxdepth 1 -name "*.jpg" -type f -mtime +$2 -exec rm {} \; 2>$DEBUG
  find $products/$1/DAY/ -maxdepth 1 -name "*.jpg" -type f -mtime +$3 -exec rm {} \; 2>$DEBUG
}

MSLPtrim()
{
  find $products/$1/dwda/ -maxdepth 1 -name "*.jpg" -type f -mtime +$2 -exec rm {} \; 2>$DEBUG
  find $products/$1/dwdn/ -maxdepth 1 -name "*.jpg" -type f -mtime +$2 -exec rm {} \; 2>$DEBUG
  find $products/$1/dwdc/ -maxdepth 1 -name "*.jpg" -type f -mtime +$2 -exec rm {} \; 2>$DEBUG
  find $products/$1/dwdi/ -maxdepth 1 -name "*.jpg" -type f -mtime +$2 -exec rm {} \; 2>$DEBUG
  find $products/$1/opcae/ -maxdepth 1 -name "*.jpg" -type f -mtime +$3 -exec rm {} \; 2>$DEBUG
  find $products/$1/opcaw/ -maxdepth 1 -name "*.jpg" -type f -mtime +$3 -exec rm {} \; 2>$DEBUG
  find $products/$1/opcpe/ -maxdepth 1 -name "*.jpg" -type f -mtime +$3 -exec rm {} \; 2>$DEBUG
  find $products/$1/opcpw/ -maxdepth 1 -name "*.jpg" -type f -mtime +$3 -exec rm {} \; 2>$DEBUG
  find $products/$1/ukmos/ -maxdepth 1 -name "*.jpg" -type f -mtime +$4 -exec rm {} \; 2>$DEBUG
  find $products/$1/ukmol/ -maxdepth 1 -name "*.jpg" -type f -mtime +$4 -exec rm {} \; 2>$DEBUG
  find $products/$1/ukmox/ -maxdepth 1 -name "*.jpg" -type f -mtime +$4 -exec rm {} \; 2>$DEBUG
}

OVERLAYtrim()
{
  find $overlays/dwda/ -maxdepth 1 -name "*.png" -type f -mtime +$1 -exec rm {} \; 2>$DEBUG
  find $overlays/dwdn/ -maxdepth 1 -name "*.png" -type f -mtime +$1 -exec rm {} \; 2>$DEBUG
  find $overlays/dwdc/ -maxdepth 1 -name "*.png" -type f -mtime +$1 -exec rm {} \; 2>$DEBUG
  find $overlays/dwdi/ -maxdepth 1 -name "*.png" -type f -mtime +$1 -exec rm {} \; 2>$DEBUG
  find $overlays/opcae/ -maxdepth 1 -name "*.png" -type f -mtime +$2 -exec rm {} \; 2>$DEBUG
  find $overlays/opcaw/ -maxdepth 1 -name "*.png" -type f -mtime +$2 -exec rm {} \; 2>$DEBUG
  find $overlays/opcpe/ -maxdepth 1 -name "*.png" -type f -mtime +$2 -exec rm {} \; 2>$DEBUG
  find $overlays/opcpw/ -maxdepth 1 -name "*.png" -type f -mtime +$2 -exec rm {} \; 2>$DEBUG
  find $overlays/ukmos/ -maxdepth 1 -name "*.png" -type f -mtime +$3 -exec rm {} \; 2>$DEBUG
  find $overlays/ukmol/ -maxdepth 1 -name "*.png" -type f -mtime +$3 -exec rm {} \; 2>$DEBUG
  find $overlays/ukmox/ -maxdepth 1 -name "*.png" -type f -mtime +$3 -exec rm {} \; 2>$DEBUG
}

TMPXtrim()
{
  for f in `ls -d $xtmpdirs/* 2>$DEBUG`
  do
    find $f/ -maxdepth 1 -name "*.png" -type f -mtime +$1 -exec rm {} \; 2>$DEBUG
    find $f/ -maxdepth 1 -type f -not -name "*.png" -mtime +1 -exec rm {} \; 2>$DEBUG
  done
}

CACHEtrim()
{
  find $datdir/cache -type f -mtime +$1 -delete 2>$DEBUG
}

# Delete GEO frames/images/movies
GEOtrim MSG2   1560 10 30
GEOtrim MSG3   1560 10 30
GEOtrim MSG4   1560 10 30
GEOtrim HIMA8  1560 10 30
GEOtrim GOES16 1560 10 30
GEOtrim GOES18 1560 10 30
GEOtrim GOES19 1560 10 30
GEOtrim MTI1   1560 10 30

# Delete LEO images NIG/DAY
LEOtrim Aqua   30 30
LEOtrim Terra  30 30
LEOtrim MetopB 30 30
LEOtrim MetopC 30 30
LEOtrim MetopX 30 30
LEOtrim SNPP   30 30
LEOtrim NOAA20 30 30
LEOtrim NOAAX  30 30
LEOtrim FY3D   30 30
LEOtrim Sen3A  30 30
LEOtrim Sen3B  30 30
LEOtrim Sen3X  30 30

# Delete GEO MSLP charts DWD/OPC/UKMO
MSLPtrim MSLP 30 30 30

# Delete png MSLP overlays DWD/OPC/UKMO
OVERLAYtrim 5 5 5

# Delete e.g. old remainders from different composite and area tests
TMPXtrim 10

# Clean SatPy reprojection cache (keep last 7 days)
CACHEtrim 7

# All done!

