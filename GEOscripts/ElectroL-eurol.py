#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# USAGE: ElectroL-eurol.py YYYYmmddHHMM
# Satellite Electro-L N3 (MSU-GS) - Europe detail | Area: eurol
# Reader: electrol_hrit | Segdir: /home/sps/received/bas/E1B-TPG-1 (condiviso con FY-2)
#
# Confermato da EUMETSAT Product Navigator (MSU-GS level 1.5 Imager Data -
# Electro-L N3): canale E1B-TPG-1, platform_shortname 'GOMS3', file tipo
# H-000-GOMS3_-GOMS3_4_____-<banda>_076E-<segmento>-<data>-__
# Il canale è condiviso col multiplex FY-2 (Third Party GEO): al 2026-09-13
# arrivano solo file FY2G/FY2H, nessun file GOMS3 ancora — probabile
# attivazione EUMETSAT lato sorgente ancora in corso (Electro-L N3 richiesto
# via EO Portal, "attivazione entro 2 giorni lavorativi").
#
# Electro-L N3 trasmette solo 6 dei 10 canali MSU-GS ogni 30 minuti:
#   Canale EUMETSAT 3  (0.8-0.9 um)   -> satpy '00_9'
#   Canale EUMETSAT 4  (3.5-4.0 um)   -> satpy '03_8'
#   Canale EUMETSAT 6  (7.5-8.5 um)   -> satpy '08_0'
#   Canale EUMETSAT 8  (9.2-10.2 um)  -> satpy '09_7'
#   Canale EUMETSAT 9  (10.2-11.2 um) -> satpy '10_7'
#   Canale EUMETSAT 10 (11.2-12.5 um) -> satpy '11_9'
# NB: '00_6'/'00_7'/'06_4'/'08_7' NON sono trasmessi da Electro-L N3, solo
# definiti nel reader per compatibilita con altri satelliti Electro-L/GOMS.
#
# Il reader SatPy 'electrol_hrit' non definisce compositi con nome (niente
# true_color/natural_color), solo canali radiometrici grezzi. Questo script
# produce quindi due immagini singolo-canale:
#   - VIS/NIR (00_9, counts)   -> immagine diurna in scala di grigi
#   - IR finestra (10_7, Tb)   -> immagine giorno/notte, nuvole in toni freddi
#
# License GPL3 (c) INGV adaptation 2026

import os, sys, platform
from GEOstuff import test_argv, geo_images, get_magick

OS = platform.system()
sat, Dat, Yea, Mon, Day, Hou, Min = test_argv()

# ----------------------------------------------------------------
segdir  = '/home/sps/received/bas/E1B-TPG-1'
isbulk  = True
decomp  = False

composites = ['00_9', '10_7']  # canali grezzi, non compositi con nome

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
channel  = 'E1B-TPG-1'
logo1    = 'eumetsat_200x199.png'
logo2    = 'PyTROLL_400x400.jpg'
receiver = 'TBS-6909X'

if not os.path.isdir(segdir):
    sys.exit(f'SORRY: segdir {segdir} non esiste ...')

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
