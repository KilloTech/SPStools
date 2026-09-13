#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# USAGE: ElectroL-eurol.py YYYYmmddHHMM
# Satellite Electro-L N3 (MSU-GS) - Europe detail | Area: eurol
# Reader: electrol_hrit | Segdir: TBD (canale non ancora visibile su /mnt/eumetcast)
#
# NOTA IMPORTANTE: il canale EUMETCast per Electro-L non è ancora presente sul
# ricevitore al momento in cui questo script è stato scritto (richiesta di
# sottoscrizione appena inviata). Il percorso 'segdir' qui sotto è un
# PLACEHOLDER: va aggiornato con il canale reale (probabile bas/E1B-TPG-N,
# come FY-2 su E1B-TPG-1) non appena compare in /home/sps/received/bas/.
#
# Il reader SatPy 'electrol_hrit' non definisce compositi con nome (niente
# true_color/natural_color): fornisce solo canali radiometrici grezzi:
#   00_6, 00_7, 00_9  (visibile/NIR, calibrazione: radiance o counts, NON reflectance)
#   03_8, 06_4, 08_0, 08_7, 09_7, 10_7, 11_9  (IR, calibrazione: brightness_temperature)
# Questo script produce quindi due immagini singolo-canale (non compositi RGB):
#   - VIS (00_6, counts)      -> immagine diurna in scala di grigi
#   - IR finestra (10_7, Tb)  -> immagine giorno/notte, nuvole in toni freddi
#
# License GPL3 (c) INGV adaptation 2026

import os, sys, platform
from GEOstuff import test_argv, geo_images, get_magick

OS = platform.system()
sat, Dat, Yea, Mon, Day, Hou, Min = test_argv()

# ----------------------------------------------------------------
segdir  = '/home/sps/received/bas/E1B-TPG-X'  # PLACEHOLDER: aggiornare con il canale reale
isbulk  = True
decomp  = False

composites = ['00_6', '10_7']  # canali grezzi, non compositi con nome

areas = ['eurol']

area_cities = []
ADDcoasts  = True
ADDborders = True
ADDrivers  = False
ADDlakes   = False
ADDgrid    = False
ADDcities  = False
ADDpoints  = False
ADDstation = False
ADDlegend  = True

GEOcache = True
OVRcache = True
testrun  = False
# ----------------------------------------------------------------

sensor   = 'msu-gs'
service  = 'Third Party Data Services - GEO'
channel  = 'E1B-TPG-X'  # PLACEHOLDER
logo1    = 'eumetsat_200x199.png'
logo2    = 'PyTROLL_400x400.jpg'
receiver = 'TBS-6909X'

if not os.path.isdir(segdir):
    sys.exit(f'SORRY: segdir {segdir} non esiste ancora — aggiorna il placeholder '
             f'in ElectroL-eurol.py con il canale reale una volta che EUMETSAT '
             f'attiva la sottoscrizione Electro-L N3 (controllare /home/sps/received/bas/)')

for area in areas:
    height = geo_images(Yea, Mon, Day, Hou, Min, sat, segdir, decomp, isbulk,
                        'electrol_hrit', composites,
                        area, area_cities, ADDcoasts, ADDborders, ADDrivers, ADDlakes,
                        ADDgrid, ADDcities, ADDpoints, ADDstation, GEOcache, OVRcache, testrun)

    for composite in composites:
        magick = get_magick(Yea, Mon, Day, Hou, Min, height, logo1, logo2, service, channel,
                            receiver, sat, sensor, composite, area, testrun, ADDlegend,
                            subdir='frames')
        os.system(magick)
