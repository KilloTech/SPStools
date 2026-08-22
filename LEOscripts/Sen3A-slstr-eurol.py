#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#*************************************************************************
#
# Sentinel-3A  SLSTR L2 WST  Sea Surface Temperature  eurol area
# Channel : E2H-S3A-04  (SL_2_WST  GHRSST L2P tiles)
# Reader  : ghrsst_l2
# Works both DAY and NIGHT (thermal infrared)
#
# Usage: Sen3A-slstr-eurol.py YYYYmmdd
#
# CH-3123 Belp  License GPL3  (c) Ernst Lobsiger / INGV adaptation
#
#*************************************************************************

import os, sys, glob, tarfile, shutil, warnings, subprocess
import netCDF4
warnings.filterwarnings('ignore', category=FutureWarning)

if len(sys.argv) < 2:
    sys.exit(f'Usage: {sys.argv[0]} YYYYmmdd')

from datetime import datetime, timedelta

Dat = sys.argv[1][:8]
Yea, Mon, Day = Dat[:4], Dat[4:6], Dat[6:8]

# vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv
# ********** ADAPT THESE PARAMETERS TO YOUR PERSONAL NEEDS ***********

segdir   = '/home/sps/received/hvs-2/E2H-S3A-04'
toodir   = '/home/sps/SPStools'
outbase  = '/home/sps/SPSdata/Sen3A/eurol/SST'
tmpdir   = f'/home/sps/SPSdata/tmp/slstr_S3A_{Dat}'
area     = 'eurol'
receiver = 'TBS-6909X'
service  = 'HVS-2'
channel  = 'E2H-S3A-04'

# ******** TOUCH THE CODE BELOW ONLY IF YOU KNOW WHAT YOU DO *********
# ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

# eurol bounding box for pre-filtering tiles
EUROL_LAT_MIN, EUROL_LAT_MAX =  25.0,  75.0
EUROL_LON_MIN, EUROL_LON_MAX = -25.0,  45.0

def nc_overlaps_eurol(nc_path):
    """Return True if the NC tile's lat/lon data overlaps with eurol area."""
    import numpy as np
    try:
        with netCDF4.Dataset(nc_path) as ds:
            if 'lat' not in ds.variables or 'lon' not in ds.variables:
                return True  # no coordinates — include as safe fallback
            # Sample every 50th row/col to get approximate bbox cheaply
            lat = ds.variables['lat'][::50, ::50]
            lon = ds.variables['lon'][::50, ::50]
        lat_min, lat_max = float(np.nanmin(lat)), float(np.nanmax(lat))
        lon_min, lon_max = float(np.nanmin(lon)), float(np.nanmax(lon))
        return (lat_max >= EUROL_LAT_MIN and lat_min <= EUROL_LAT_MAX and
                lon_max >= EUROL_LON_MIN and lon_min <= EUROL_LON_MAX)
    except Exception:
        return True  # include on read error (safe fallback)

shutil.rmtree(tmpdir, ignore_errors=True)   # clean up any stale tmpdir from previous run
os.makedirs(tmpdir, exist_ok=True)
os.makedirs(outbase, exist_ok=True)

# Find all SL_2_WST tar files for this date
# Also pick up previous night pass (files starting with prev date T2x UTC)
prev = (datetime(int(Yea), int(Mon), int(Day)) - timedelta(days=1)).strftime('%Y%m%d')
patterns = [
    f'{segdir}/S3A_SL_2_WST____{Dat}*.SEN3.tar',
    f'{segdir}/S3A_SL_2_WST____{prev}T2[0-9]*.SEN3.tar',
]
tarfiles = []
for pat in patterns:
    tarfiles += sorted(glob.glob(pat))

if not tarfiles:
    shutil.rmtree(tmpdir, ignore_errors=True)
    sys.exit(f'No SL_2_WST files for {Dat} in {segdir}')

print(f'[Sen3A-slstr] Found {len(tarfiles)} tile(s) for {Dat}')

# Extract tiles one by one; keep only those overlapping eurol to save disk/memory
ncfiles = []
for tf in tarfiles:
    base = os.path.basename(tf).replace('.tar', '')
    tiledir = f'{tmpdir}/{base}'
    try:
        with tarfile.open(tf) as tar:
            tar.extractall(path=tmpdir)
        nc = glob.glob(f'{tiledir}/*.nc')
        kept = [f for f in nc if nc_overlaps_eurol(f)]
        if kept:
            ncfiles.extend(kept)
            print(f'  keep: {os.path.basename(tf)} ({len(kept)}/{len(nc)} nc in eurol)')
        else:
            shutil.rmtree(tiledir, ignore_errors=True)
    except Exception as e:
        print(f'  WARNING: failed to extract {os.path.basename(tf)}: {e}')
        shutil.rmtree(tiledir, ignore_errors=True)

if not ncfiles:
    shutil.rmtree(tmpdir, ignore_errors=True)
    sys.exit('No NC files overlap eurol area')
print(f'[Sen3A-slstr] Kept {len(ncfiles)} NC file(s) overlapping eurol')

print(f'[Sen3A-slstr] Loading {len(ncfiles)} NC file(s) with ghrsst_l2')

# Set SatPy config path (same as LEOstuff.py)
from satpy import config as satpy_config
satpy_config.set(config_path=[f'{toodir}/userconfig'])

from satpy import Scene

try:
    scene = Scene(filenames=ncfiles, reader='ghrsst_l2')
    scene.load(['sea_surface_temperature'])
except Exception as e:
    shutil.rmtree(tmpdir, ignore_errors=True)
    sys.exit(f'Scene load error: {e}')

# Get start time from dataset attributes
try:
    sst = scene['sea_surface_temperature']
    start_dt = sst.attrs.get('start_time', datetime(int(Yea), int(Mon), int(Day), 9, 0))
    if isinstance(start_dt, str):
        start_dt = datetime.strptime(start_dt, '%Y-%m-%dT%H:%M:%S')
    Hou = start_dt.strftime('%H')
    Min = start_dt.strftime('%M')
except Exception:
    Hou, Min = '09', '00'

print(f'[Sen3A-slstr] Resampling to {area}')
try:
    lscene = scene.resample(area, resampler='nearest')
except Exception as e:
    shutil.rmtree(tmpdir, ignore_errors=True)
    sys.exit(f'Resample error: {e}')

# Save as PNG via simple_image writer
tmpimg = f'{tmpdir}/sst_{Dat}_{Hou}{Min}.png'
try:
    lscene.save_dataset('sea_surface_temperature', filename=tmpimg, writer='simple_image')
    print(f'[Sen3A-slstr] Image saved: {tmpimg}')
except Exception as e:
    shutil.rmtree(tmpdir, ignore_errors=True)
    sys.exit(f'Save error: {e}')

# ImageMagick annotation
logo1   = f'{toodir}/logos/Copernicus_1050x1050.png'
logo2   = f'{toodir}/logos/PyTROLL_400x400.jpg'
outfile = f'{outbase}/S3A_sst_eurol_{Dat}_{Hou}{Min}.png'

ann = f'Sentinel-3A SLSTR SST  {Yea}-{Mon}-{Day} {Hou}:{Min} UTC | {service}/{channel} | {receiver}'
magick = (
    f'convert -quiet {tmpimg} '
    f'-gravity NorthWest -fill yellow -font DejaVu-Sans-Bold -pointsize 28 '
    f'-annotate +10+10 "{ann}" '
    f'-gravity SouthWest '
)
# Add logos if present
if os.path.exists(logo1):
    magick += f'\\( {logo1} -resize 80x80 \\) -geometry +10+10 -composite '
if os.path.exists(logo2):
    magick += f'\\( {logo2} -resize 80x80 \\) -geometry +100+10 -composite '
magick += outfile

os.system(magick)

if os.path.exists(outfile):
    print(f'[Sen3A-slstr] Output: {outfile}')
else:
    # Fallback: copy without annotation
    shutil.copy(tmpimg, outfile)
    print(f'[Sen3A-slstr] Output (no annotation): {outfile}')

# Cleanup
shutil.rmtree(tmpdir, ignore_errors=True)
print('[Sen3A-slstr] Done.')
