#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# USAGE: MODISOC-eurol.py YYYYmmddHHMM (solo Anno/Mese/Giorno usati: prodotto giornaliero)
# MODIS-Aqua Ocean Color L3m (NASA OB.DAAC) - CHL/KD/PAR/SST | Europa (eurol)
# Segdir: /home/sps/received/bas/E1B-TPC-6
#
# Questi file sono gia' prodotti L3 "mappati" (griglia lat/lon regolare 4320x8640,
# ~4km), NON swath satellitari: non serve un reader SatPy ne' un resample verso
# un'area proiettata, basta un ritaglio per indice lat/lon sulla zona Europa/Med
# e poi si riusa l'overlay/branding standard di GEOstuff.py tramite una Scene
# sintetica con un'area 'longlat' (pycoast supporta le coordinate geografiche
# direttamente).
import os, sys, glob, platform
import numpy as np
import xarray as xr
import matplotlib
matplotlib.use('Agg')
import matplotlib.cm as cm
import matplotlib.colors as mcolors

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from satpy import Scene
from pyresample.geometry import AreaDefinition
from GEOstuff import test_argv, get_overlays, get_magick

OS = platform.system()
sat, Dat, Yea, Mon, Day, Hou, Min = test_argv()

# ----------------------------------------------------------------
segdir  = '/home/sps/received/bas/E1B-TPC-6'
area    = 'eurol'

LAT_MIN, LAT_MAX = 25.0, 75.0
LON_MIN, LON_MAX = -25.0, 45.0

tmpdir  = '/home/sps/SPSdata/tmpdirs/x' + sat.lower()

logo1    = 'eumetsat_200x199.png'
logo2    = 'PyTROLL_400x400.jpg'
service  = 'Third Party Data Services - LEO'
channel  = 'E1B-TPC-6'
sensor   = 'modis'
receiver = 'TBS-6909X'
ADDlegend = True

# composite: (file glob suffix, variabile, cmap, log-scale, vmin, vmax)
products = {
    'chl':   ('CHL.chlor_a', 'chlor_a', 'jet',     True,  0.03, 20.0),
    'kd490': ('KD.Kd_490',   'Kd_490',  'jet',     True,  0.02, 2.0),
    'par':   ('PAR.par',     'par',     'viridis', False, 0.0,  60.0),
    'sst':   ('SST.sst',     'sst',     'turbo',   False, 5.0,  30.0),
}
# ----------------------------------------------------------------

date_str = Yea + Mon + Day

try:
    os.chdir(tmpdir)
except FileNotFoundError:
    sys.exit('Cannot change to tmp directory ' + tmpdir + ' ...')

produced = 0
for composite, (suffix, varname, cmap_name, log_scale, vmin, vmax) in products.items():
    matches = glob.glob(f'{segdir}/AQUA_MODIS.{date_str}.L3m.DAY.{suffix}.4km.NRT.nc')
    if not matches:
        print(f'WARNING: nessun file trovato per {composite} (data {date_str}) ...')
        continue

    ds = xr.open_dataset(matches[0])
    da = ds[varname]
    crop = da.sel(lat=slice(LAT_MAX, LAT_MIN), lon=slice(LON_MIN, LON_MAX))
    vals = crop.values.astype(np.float64)

    if log_scale:
        norm = mcolors.LogNorm(vmin=vmin, vmax=vmax)
    else:
        norm = mcolors.Normalize(vmin=vmin, vmax=vmax)
    cmap = matplotlib.colormaps[cmap_name].copy()
    cmap.set_bad((0.85, 0.85, 0.85, 1.0))  # grigio per terra/dati mancanti

    rgba = cmap(norm(np.ma.masked_invalid(vals)))
    rgb = (rgba[:, :, :3] * 255).astype(np.uint8)

    nrows, ncols = crop.shape
    target_area = AreaDefinition('crop_' + composite, 'Crop', 'crop',
                                  {'proj': 'longlat', 'datum': 'WGS84'},
                                  ncols, nrows, (LON_MIN, LAT_MIN, LON_MAX, LAT_MAX))

    da_rgb = xr.DataArray(rgb.transpose(2, 0, 1), dims=('bands', 'y', 'x'),
                           coords={'bands': ['R', 'G', 'B']},
                           attrs={'name': composite, 'area': target_area, 'sensor': sensor})

    scn = Scene()
    scn[composite] = da_rgb

    overlays = get_overlays(sat, composite, area, [], nrows, ncols,
                             True, True, False, False, False, False, False, False,
                             True, False)
    scn.save_dataset(composite, filename=sat + '-' + composite + '-' + area + '.png',
                      overlay={'coast_dir': '/home/sps/SPSdata/geodata', 'overlays': overlays})

    magick = get_magick(Yea, Mon, Day, Hou, Min, nrows, logo1, logo2, service, channel,
                         receiver, sat, sensor, composite, area, False, ADDlegend,
                         subdir='frames')
    os.system(magick)
    produced += 1

if produced == 0:
    sys.exit(f'Sorry, no good files found for date {date_str} ...')
