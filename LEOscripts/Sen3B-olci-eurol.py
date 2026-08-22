#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Sen3B-olci-eurol.py YYYYmmdd
# Sentinel-3B OLCI L1b ERR — true_color + ocean_color | Area: eurol
# Channel: E2H-S3B-02 | Reader: olci_l1b
# License GPL3 (c) Ernst Lobsiger / INGV adaptation

import os, sys, re, glob, tarfile, shutil, warnings
warnings.filterwarnings('ignore')

if len(sys.argv) < 2:
    sys.exit(f'Usage: {sys.argv[0]} YYYYmmdd')

Dat = sys.argv[1][:8]
Yea, Mon, Day = Dat[:4], Dat[4:6], Dat[6:8]

segdir     = '/home/sps/received/hvs-2/E2H-S3B-02'
toodir     = '/home/sps/SPStools'
outbase    = '/home/sps/SPSdata/products/Sen3B/OLCI'
tmpdir     = f'/home/sps/SPSdata/tmp/olci_S3B_{Dat}'
area       = 'eurol'
receiver   = 'TBS-6909X'
service    = 'HVS-2'
channel    = 'E2H-S3B-02'
composites = ['true_color', 'ocean_color']

# EU daytime window: search orbits with start_time in 08:30-13:00 UTC
EU_HOUR_MIN, EU_HOUR_MAX = 8.5, 13.0

import satpy
from satpy import Scene, config as satpy_config
# Include BOTH userconfig AND satpy built-in config (needed for olci composites)
satpy_etc = satpy.__file__.replace('__init__.py', 'etc')
satpy_config.set(config_path=[f'{toodir}/userconfig', satpy_etc])

os.makedirs(outbase, exist_ok=True)
shutil.rmtree(tmpdir, ignore_errors=True)
os.makedirs(tmpdir, exist_ok=True)

def start_hour(tf):
    m = re.search(r'\d{8}T(\d{2})(\d{2})', os.path.basename(tf))
    if m:
        return int(m.group(1)) + int(m.group(2)) / 60.0
    return 12.0

tarfiles = sorted(glob.glob(f'{segdir}/S3B_OL_1_ERR____{Dat}*.SEN3.tar'))
if not tarfiles:
    shutil.rmtree(tmpdir, ignore_errors=True)
    sys.exit(f'No OLCI ERR files for {Dat} in {segdir}')

eu_tars = [tf for tf in tarfiles if EU_HOUR_MIN <= start_hour(tf) <= EU_HOUR_MAX]
if not eu_tars:
    eu_tars = tarfiles[:1]
    print(f'[Sen3B-olci] WARNING: no orbit in EU window, using first available')

print(f'[Sen3B-olci] Found {len(eu_tars)} EU orbit(s) for {Dat}')

for tf in eu_tars[:1]:   # Process only the first EU orbit
    base    = os.path.basename(tf).replace('.SEN3.tar', '')
    sen3dir = f'{tmpdir}/{base}.SEN3'

    print(f'[Sen3B-olci] Extracting {os.path.basename(tf)} ...')
    try:
        with tarfile.open(tf) as tar:
            tar.extractall(path=tmpdir)
    except Exception as e:
        print(f'  ERROR extracting: {e}')
        continue

    if not os.path.isdir(sen3dir):
        dirs = glob.glob(f'{tmpdir}/*.SEN3')
        sen3dir = dirs[0] if dirs else None
    if not sen3dir:
        print(f'  ERROR: .SEN3 directory not found')
        continue

    # Include radiance + geo files; exclude uncertainty (_unc) and time files
    files = [f for f in glob.glob(f'{sen3dir}/*.nc')
             if '_unc' not in f and 'time_coord' not in f]
    print(f'[Sen3B-olci] Loading {len(files)} NC files ...')

    try:
        scene = Scene(filenames=files, reader='olci_l1b')
        scene.load(composites, generate=True)
    except Exception as e:
        print(f'  ERROR loading scene: {e}')
        shutil.rmtree(sen3dir, ignore_errors=True)
        continue

    # Get start time from filename
    m   = re.search(r'\d{8}T(\d{2})(\d{2})', os.path.basename(tf))
    Hou = m.group(1) if m else '10'
    Min = m.group(2) if m else '30'

    print(f'[Sen3B-olci] Resampling to {area} ...')
    try:
        lscene = scene.resample(area, resampler='nearest')
    except Exception as e:
        print(f'  ERROR resampling: {e}')
        shutil.rmtree(sen3dir, ignore_errors=True)
        continue

    for comp in composites:
        tmpimg  = f'{tmpdir}/S3B_olci_{comp}_{Dat}_{Hou}{Min}.png'
        outfile = f'{outbase}/S3B-{Dat}-{Hou}{Min}-{comp}-eurol.jpg'
        try:
            lscene.save_dataset(comp, filename=tmpimg, writer='simple_image')
            ann   = f'Sentinel-3B OLCI {comp}  {Yea}-{Mon}-{Day} {Hou}:{Min} UTC | {service}/{channel}'
            logo1 = f'{toodir}/logos/Copernicus_1050x1050.png'
            cmd   = (f'convert -quiet {tmpimg} '
                     f'-gravity NorthWest -fill yellow -font DejaVu-Sans-Bold -pointsize 28 '
                     f'-annotate +10+10 "{ann}" ')
            if os.path.exists(logo1):
                cmd += f'\\( {logo1} -resize 80x80 \\) -geometry +10+10 -composite '
            cmd += f'-quality 92 {outfile}'
            os.system(cmd)
            if os.path.exists(outfile):
                sz = os.path.getsize(outfile) / 1024 / 1024
                print(f'[Sen3B-olci] OK: {os.path.basename(outfile)} ({sz:.1f} MB)')
            else:
                print(f'  WARNING: {outfile} not created')
        except Exception as e:
            print(f'  ERROR saving {comp}: {e}')

    shutil.rmtree(sen3dir, ignore_errors=True)

shutil.rmtree(tmpdir, ignore_errors=True)
print('[Sen3B-olci] Done.')
