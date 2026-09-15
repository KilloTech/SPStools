#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#*************************************************************************
#
# Sentinel-3B  SLSTR L2 WST  Sea Surface Temperature  eurol area
# Channel : E2H-S3B-04  (SL_2_WST  GHRSST L2P tiles)
# Reader  : ghrsst_l2
# Works both DAY and NIGHT (thermal infrared)
#
# Usage: Sen3B-slstr-eurol.py YYYYmmdd
#
# CH-3123 Belp  License GPL3  (c) Ernst Lobsiger / INGV adaptation
#
#*************************************************************************

import os, sys, glob, re, tarfile, shutil, warnings, subprocess
import netCDF4
warnings.filterwarnings('ignore', category=FutureWarning)

if len(sys.argv) < 2:
    sys.exit(f'Usage: {sys.argv[0]} YYYYmmdd')

from datetime import datetime, timedelta

Dat = sys.argv[1][:8]
Yea, Mon, Day = Dat[:4], Dat[4:6], Dat[6:8]

# vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv
# ********** ADAPT THESE PARAMETERS TO YOUR PERSONAL NEEDS ***********

segdir   = '/home/sps/received/hvs-2/E2H-S3B-04'
toodir   = '/home/sps/SPStools'
outbase  = '/home/sps/SPSdata/Sen3B/eurol/SST'
tmpdir   = f'/home/sps/SPSdata/tmp/slstr_S3B_{Dat}'
area     = 'eurol'
receiver = 'TBS-6909X'
service  = 'HVS-2'
channel  = 'E2H-S3B-04'

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
prev = (datetime(int(Yea), int(Mon), int(Day)) - timedelta(days=1)).strftime('%Y%m%d')
patterns = [
    f'{segdir}/S3B_SL_2_WST____{Dat}*.SEN3.tar',
    f'{segdir}/S3B_SL_2_WST____{prev}T2[0-9]*.SEN3.tar',
]
tarfiles = []
for pat in patterns:
    tarfiles += sorted(glob.glob(pat))

if not tarfiles:
    shutil.rmtree(tmpdir, ignore_errors=True)
    sys.exit(f'No SL_2_WST files for {Dat} in {segdir}')

print(f'[Sen3B-slstr] Found {len(tarfiles)} tile(s) for {Dat}')

# Extract tiles one by one; keep only those overlapping eurol to save disk/memory
ncfiles = []
for tf in tarfiles:
    base = os.path.basename(tf).replace('.tar', '')
    tiledir = f'{tmpdir}/{base}'
    try:
        with tarfile.open(tf) as tar:
            tar.extractall(path=tmpdir)
        # satpy/ghrsst_l2.yaml definisce sea_surface_temperature solo per la
        # vista 'nadir': i file *_DUAL_* non producono questo dataset e,
        # mischiati ai *_NADIR_* nella stessa Scene, mandano in confusione
        # l'assegnazione dei file dopo il resample (available_dataset_names
        # vuoto / dataset introvabile). Teniamo solo i NADIR.
        nc = glob.glob(f'{tiledir}/*NADIR*.nc')
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
print(f'[Sen3B-slstr] Kept {len(ncfiles)} NC file(s) overlapping eurol')

# I file "NRT" hanno un infisso '-NRT_NADIR_'/'-NRT_DUAL_' tra il tag vista
# (SLSTRB) e il secondo timestamp che il file_pattern di satpy/ghrsst_l2.yaml
# non prevede (si aspetta 'SLSTRB-{dt2}-{version}.nc' senza infisso), quindi
# il reader non riconosce questi file. Li rinominiamo (siamo in una tmpdir
# usa-e-getta) rimuovendo l'infisso per farli combaciare col pattern atteso.
renamed = []
for f in ncfiles:
    base = os.path.basename(f)
    new_base = re.sub(r'-NRT_(NADIR|DUAL)_', '-', base)
    if new_base != base:
        newpath = os.path.join(os.path.dirname(f), new_base)
        os.rename(f, newpath)
        renamed.append(newpath)
    else:
        renamed.append(f)
ncfiles = renamed

# Questa baseline di processing (GDS 2.1 / NRT) usa gli attributi globali
# ACDD 'time_coverage_start'/'time_coverage_end' (ISO), ma il reader
# satpy/ghrsst_l2 si aspetta 'start_time'/'stop_time' in formato compatto
# '%Y%m%dT%H%M%SZ' (baseline GDS 1 piu' vecchia): senza patch, FileHandler
# fallisce con AttributeError. Aggiungiamo gli attributi mancanti in-place.
for f in ncfiles:
    with netCDF4.Dataset(f, 'a') as ds:
        if 'start_time' not in ds.ncattrs():
            dt_s = datetime.strptime(ds.getncattr('time_coverage_start'), '%Y-%m-%dT%H:%M:%S')
            dt_e = datetime.strptime(ds.getncattr('time_coverage_end'), '%Y-%m-%dT%H:%M:%S')
            ds.setncattr('start_time', dt_s.strftime('%Y%m%dT%H%M%SZ'))
            ds.setncattr('stop_time', dt_e.strftime('%Y%m%dT%H%M%SZ'))

print(f'[Sen3B-slstr] Loading {len(ncfiles)} NC file(s) with ghrsst_l2')

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

print(f'[Sen3B-slstr] Resampling to {area}')
try:
    lscene = scene.resample(area, resampler='nearest')
except Exception as e:
    shutil.rmtree(tmpdir, ignore_errors=True)
    sys.exit(f'Resample error: {e}')

# Save as PNG via simple_image writer
tmpimg = f'{tmpdir}/sst_{Dat}_{Hou}{Min}.png'
try:
    lscene.save_dataset('sea_surface_temperature', filename=tmpimg, writer='simple_image')
    print(f'[Sen3B-slstr] Image saved: {tmpimg}')
except Exception as e:
    shutil.rmtree(tmpdir, ignore_errors=True)
    sys.exit(f'Save error: {e}')

# ImageMagick annotation
logo1   = f'{toodir}/logos/Copernicus_1050x1050.png'
logo2   = f'{toodir}/logos/PyTROLL_400x400.jpg'
outfile = f'{outbase}/S3B_sst_eurol_{Dat}_{Hou}{Min}.png'

ann = f'Sentinel-3B SLSTR SST  {Yea}-{Mon}-{Day} {Hou}:{Min} UTC | {service}/{channel} | {receiver}'
magick = (
    f'convert -quiet {tmpimg} '
    f'-gravity NorthWest -fill yellow -font DejaVu-Sans-Bold -pointsize 28 '
    f'-annotate +10+10 "{ann}" '
    f'-gravity SouthWest '
)
if os.path.exists(logo1):
    magick += f'\\( {logo1} -resize 80x80 \\) -geometry +10+10 -composite '
if os.path.exists(logo2):
    magick += f'\\( {logo2} -resize 80x80 \\) -geometry +100+10 -composite '
magick += outfile

os.system(magick)

if os.path.exists(outfile):
    print(f'[Sen3B-slstr] Output: {outfile}')
else:
    shutil.copy(tmpimg, outfile)
    print(f'[Sen3B-slstr] Output (no annotation): {outfile}')

# Cleanup
shutil.rmtree(tmpdir, ignore_errors=True)
print('[Sen3B-slstr] Done.')
