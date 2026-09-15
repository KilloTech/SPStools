#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# USAGE: LI-eurol.py YYYYmmddHHMM
# Satellite MTI-1 (MTG-I1) - Lightning Imager AF product | Europe (eurol)
# Reader: li_l2_nc | Segdir: /home/sps/received/hvs-2/E2H-MTG-LI
#
# Il prodotto AF (Accumulated Flash) e' distribuito come 20 chunk BODY + 1 TRAIL
# per ogni ciclo di accumulo di 10 minuti. Tutti e 20 i chunk BODY condividono la
# STESSA area geografica (StackedAreaDefinition), rappresentando 20 sotto-intervalli
# temporali di accumulo: vanno quindi sommati punto per punto, non mediati/scelti.
#
# Lo swath nativo e' enorme (111360x5568 = ~620M punti): un resample diretto
# (scn.resample) o anche solo area.get_lonlats() sull'intera StackedAreaDefinition
# causa OOM anche con 11GB RAM (verificato). La soluzione: processare le aree
# lon/lat/dati un chunk alla volta (ognuno ~31M punti, gestibile), applicare una
# maschera bounding-box sull'area target PRIMA di accumulare/concatenare, poi fare
# un unico resample_nearest sul sottoinsieme ridotto (tipicamente <5% dei punti).
import os, sys, glob, platform
import numpy as np
import xarray as xr

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hdf5plugin  # noqa: F401  side-effect import per filtri compressione HDF5/NetCDF
from satpy import Scene
from pyresample.geometry import SwathDefinition
from pyresample.kd_tree import resample_nearest
from satpy.area import get_area_def
from GEOstuff import test_argv, get_overlays, get_magick

OS = platform.system()
sat, Dat, Yea, Mon, Day, Hou, Min = test_argv()

# ----------------------------------------------------------------
segdir   = '/home/sps/received/hvs-2/E2H-MTG-LI'
area     = 'eurol'
composite = 'acc_flash'

# Bounding box approssimativo (lat/lon) usato per ridurre lo swath nativo
# PRIMA del resample: deve coprire abbondantemente l'estensione di 'eurol'.
LAT_MIN, LAT_MAX = 25.0, 75.0
LON_MIN, LON_MAX = -25.0, 45.0
RADIUS_M = 6000  # raggio di ricerca resample_nearest (~2x risoluzione nativa LI ~4.5km)

tmpdir = '/home/sps/SPSdata/tmpdirs/x' + sat.lower()

logo1    = 'eumetsat_200x199.png'
logo2    = 'PyTROLL_400x400.jpg'
service  = 'HVS-2'
channel  = 'E2H-MTG-LI'
sensor   = 'li'
receiver = 'TBS-6909X'
ADDlegend = True
# ----------------------------------------------------------------

slot_end = Yea + Mon + Day + Hou + Min + '00'

# Il file TRAIL copre l'intero ciclo di accumulo di 10 min (start=cycle_start,
# end=slot_end) e porta nel nome il numero di ciclo univoco '_O_<cycle>_0021.nc'.
# I 20 file BODY invece coprono ciascuno un solo sotto-intervallo di 30s (con
# start/end propri diversi tra loro) e vanno quindi selezionati per NUMERO DI
# CICLO (stesso di TRAIL), non per timestamp di fine.
all_files = glob.glob(segdir + '/*LI-2-AF-*.nc')
trail_candidates = [f for f in all_files if 'TRAIL' in f and f'_{slot_end}_N__O_' in f]

if len(trail_candidates) != 1:
    sys.exit(f'Sorry, no good files found (ciclo terminante in {slot_end}: '
             f'{len(trail_candidates)} file TRAIL trovati, ne serve 1) ...')

trail_file = trail_candidates[0]
cycle_id = trail_file.rsplit('_O_', 1)[1].split('_')[0]

# Il numero di ciclo si azzera ogni giorno a mezzanotte UTC e si ripete
# (es. ciclo 0061 esiste sia il giorno D che il giorno D+1): con file di
# piu' giorni presenti in segdir (retention), filtrare solo per cycle_id
# puo' raccogliere 40 chunk BODY invece di 20 (chunk di due giorni diversi
# con lo stesso numero di ciclo). Richiediamo anche la data del giorno target.
date_prefix = Yea + Mon + Day
body_files = [f for f in all_files
              if 'BODY' in f and f'_O_{cycle_id}_' in f and date_prefix in f]

if len(body_files) != 20:
    sys.exit(f'Sorry, no good files found (ciclo {cycle_id}: {len(body_files)}/20 chunk BODY presenti) ...')

body_files.sort()

scn = Scene(filenames=body_files, reader='li_l2_nc')
scn.load(['flash_accumulation'], generate=False)
data = scn['flash_accumulation']
native_area = data.attrs['area']

row_offsets = [0]
for chunk_h in data.data.chunks[0]:
    row_offsets.append(row_offsets[-1] + chunk_h)

# Tutti i 20 chunk condividono la stessa geolocazione: la calcoliamo una sola volta
lo0, la0 = native_area.defs[0].get_lonlats()
lo0 = np.asarray(lo0)
la0 = np.asarray(la0)
bbox_mask = (la0 >= LAT_MIN) & (la0 <= LAT_MAX) & (lo0 >= LON_MIN) & (lo0 <= LON_MAX)

lons_sub = lo0[bbox_mask]
lats_sub = la0[bbox_mask]
n_sel = int(bbox_mask.sum())
accumulated = np.zeros(n_sel, dtype=np.float64)

for i in range(len(native_area.defs)):
    r0, r1 = row_offsets[i], row_offsets[i + 1]
    chunk_data = np.asarray(data.data[r0:r1, :])
    accumulated += np.nan_to_num(chunk_data[bbox_mask])
    del chunk_data

swath_def = SwathDefinition(lons=lons_sub, lats=lats_sub)
target_area = get_area_def(area)

result = resample_nearest(swath_def, accumulated, target_area,
                           radius_of_influence=RADIUS_M, fill_value=0.0)

# Ricostruiamo una Scene "sintetica" con il dato gia' resampled, cosi' possiamo
# riusare l'enhancement (colormap) e l'overlay/branding standard di GEOstuff.py
result_da = xr.DataArray(result.astype(np.float32), dims=('y', 'x'), attrs={
    'name': 'flash_accumulation',
    'area': target_area,
    'sensor': sensor,
    'units': 'count',
    'start_time': scn.start_time,
    'end_time': scn.end_time,
})

out_scn = Scene()
out_scn['flash_accumulation'] = result_da
out_scn.load([composite], generate=True)

height, width = out_scn[composite].shape

try:
    os.chdir(tmpdir)
except FileNotFoundError:
    sys.exit('Cannot change to tmp directory ' + tmpdir + ' ...')

overlays = get_overlays(sat, composite, area, [], height, width,
                         True, True, False, False, False, False, False, False,
                         True, False)

out_scn.save_dataset(composite, filename=sat + '-' + composite + '-' + area + '.png',
                      overlay={'coast_dir': '/home/sps/SPSdata/geodata', 'overlays': overlays},
                      fill_value=0)

magick = get_magick(Yea, Mon, Day, Hou, Min, height, logo1, logo2, service, channel,
                     receiver, sat, sensor, composite, area, False, ADDlegend,
                     subdir='frames')
os.system(magick)
