#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------------------
# Script to produce MSLP Ground Pressure Overlays from EUMETCast channel E1B-DWDSAT
#
# Unfortunately E1B-DWDSAT has no colored DWD MSLP-charts as found on DWD OpenData:
# They disseminate dwda, dwdn 6 hourly, dwdc, dwdi 12 hourly, all black&white only!
# But they have an UKMO (XXL) 1728 x 2351 pixel MSLP analysis chart under the name:
# Z__C_EDZW_20220708193608_fax01,egrr_bwk_nt_p_000000_000000_202207081800_EGRR.tiff
# Users who want dwda 3 hourly and colored weather fronts must access DWD OpenData.
#
# This script should run in PyTROLL (base) environment under Windows and GNU/Linux.
# It expects a version of ImageMagick convert(.exe) to be installed on your system.
#
# CH-3123 Belp, 2022/12/10              License GPL3             (c) Ernst Lobsiger
# ---------------------------------------------------------------------------------

import os, sys, platform
from glob import glob
from datetime import datetime

OS = platform.system()

if OS == 'Linux':
    segdir = '/home/sps/received/bas/E1B-DWDSAT'
    isbulk = True
    toodir = '/home/sps/SPStools'
    datdir = '/home/sps/SPSdata'
    # Do not touch the GNU/Linux stuff below this line
    convert='convert'
    ob = ' \( '
    cbc = ' \) -composite'
elif OS == 'Windows':
    segdir = 'Z:/E1B-DWDSAT'
    isbulk = False
    toodir = 'C:/SPStools'
    datdir = 'D:/SPSdata'
    # Do not touch the Windows stuff below this line
    convert = toodir + '/exefiles/convert.exe'
    ob = ' ^( '
    cbc = ' ^) -composite'
else:
    sys.exit('Sorry, OS ' + OS + ' seems unsupported yet ...')

# Make dwda, dwdc, dwdna charts (da DWDSAT, in bianco/nero)
do_dwdx = True
# Make the eXtra large "Bracknell" chart
do_ukmox = True

# ****************************************************
# Touch this stuff below only if you know what you do!
# ****************************************************

# Processed MSLP overlays go into this directory (must exist)
# Sub directories dwda, dwdc, dwdna, ukmox are created automatically if missing
mslpdir = datdir + '/overlays'
# Threshold for B&W processing
threshold = ' -threshold 80%'


# isbulk=True: file piatti; isbulk=False: sottodirectory YYYY/MM/DD
if not isbulk:
    dt = datetime.now()
    Yea = dt.strftime('%Y')
    Mon = dt.strftime('%m')
    Day = dt.strftime('%d')
    segdir = segdir + '/' + Yea + '/' + Mon +'/' + Day

# Directory must exist
try:
   os.chdir(segdir)
except:
   sys.exit('Cannot change to segdir directory ' + segdir + ' ...')

# Used DWD colors ("" for GNU/Linux only?)
black='"#000000"'
white='"#ffffff"'
# Added for dwdi
gray20='"#333333"'

def make_overlay(area, Dat, fq):
    """Produce -bb- (black on transparent) e -ww- (white on transparent) overlay."""
    outdir = mslpdir + '/' + area
    os.makedirs(outdir, exist_ok=True)
    chart = outdir + '/' + area + '-bb-' + Dat + '.png'
    if not os.path.exists(chart):
        cmdstr = convert + ' ' + fq + threshold + ' -negate -transparent black -fill black -opaque white PNG32:' + chart
        os.system(cmdstr)
    chart = outdir + '/' + area + '-ww-' + Dat + '.png'
    if not os.path.exists(chart):
        cmdstr = convert + ' ' + fq + threshold + ' -negate -transparent ' + black + ' PNG32:' + chart
        os.system(cmdstr)


if do_dwdx:
    # dwda: Analisi superficie Europa Occidentale 3-hourly, file *_dwda_*_PB14.png
    # Nome: Z__C_EDZW_YYYYMMDDHHMMSS_tka01,ana_bwk_dwda_N_000000_999999_YYYYMMDDHHmm_PB14.png
    #       pos 39-42 = 'dwda';  pos 60-71 = YYYYMMDDHHmm (valid time)
    for f in glob('Z__C_EDZW*_dwda_*_PB14.png'):
        Dat = f[60:72]
        print(f'Processing dwda Western Europe {Dat}')
        make_overlay('dwda', Dat, '"' + f + '"')

    # dwdc / dwdn / dwdna: Analisi manuali Europa Centrale e Nord Atlantico 12-hourly
    # Nome: Z__C_EDZW_YYYYMMDDHHMMSS_tka01,ana_bwkman_dwdc_O_000000_000000_YYYYMMDDHHmm_WV12SW.png
    #       pos 42-45 = 'dwdc'/'dwdn';  pos 42-46 = 'dwdna';  pos 63-74 = YYYYMMDDHHmm
    for f in glob('Z__C_EDZW*dwd*WV12SW.png'):
        if f[42:47] == 'dwdna':
            # Il canale trasmette 'dwdna' (North Atlantic) ma i consumer (es.
            # MSG4-MSLP-dwdx.py) si aspettano l'area 'dwdn' (nome usato anche
            # dalla pipeline web DWD OpenData per la stessa area): normalizziamo
            # qui per evitare che i due nomi non si incontrino mai.
            area, Dat = 'dwdn', f[64:76]   # dwdna has 1 extra char → date shifts +1
        elif f[42:46] in ('dwdc', 'dwdn'):
            area, Dat = f[42:46], f[63:75]
        else:
            continue
        print(f'Processing {area} monochrome {Dat}')
        make_overlay(area, Dat, '"' + f + '"')


if do_ukmox:
    # Fax UKMO Bracknell T+0: Z__C_EDZW_*_fax01,egrr_bwk_nt_p_000000_*_YYYYMMDDHHmm_EGRR.tiff
    # pos 59-70 = YYYYMMDDHHmm (valid time); ruotato -90°, ritagliato
    for f in glob('Z__C_EDZW*bwk_nt_p_000000*.tiff'):
        Dat = f[59:71]
        fq  = '"' + f + '"'
        print(f'Processing DWD (XXL) Bracknell chart {Dat}')
        outdir = mslpdir + '/ukmox'
        os.makedirs(outdir, exist_ok=True)
        chart = outdir + '/ukmox-bb-' + Dat + '.png'
        if not os.path.exists(chart):
            cmdstr = convert + ' ' + fq + ' -rotate -90 -crop 2345x1583+3+72 -bordercolor ' + black + ' -border 3x3' + threshold + ' -transparent ' + white + ' PNG32:' + chart
            os.system(cmdstr)
        chart = outdir + '/ukmox-ww-' + Dat + '.png'
        if not os.path.exists(chart):
            cmdstr = convert + ' ' + fq + ' -rotate -90 -crop 2345x1583+3+72 -bordercolor ' + black + ' -border 3x3' + threshold + ' -negate -transparent ' + black + ' PNG32:' + chart
            os.system(cmdstr)

