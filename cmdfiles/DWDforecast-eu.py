#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------------------
# Converte le carte previsionali DWD ("ps401", Bodenwetterkarte prognostiziert per
# l'Europa) ricevute via EUMETCast sul canale E1B-DWDSAT. A differenza delle carte
# dwda/dwdn/ukmox (solo isobare, pensate come overlay su un composito satellitare),
# queste sono grafici previsionali gia' completi - temperatura a colori, isobare,
# fronti, simboli meteo per citta' - e vengono quindi salvate come prodotto a se'
# stante, non composite con immagini satellitari.
#
# Formato sorgente: PostScript (Ghostscript via ImageMagick 'convert' lo rasterizza).
# Scadenze disponibili: +012h, +036h, +060h, +084h. Disseminazione due volte al
# giorno dopo i run 00Z/12Z del modello, con le 4 scadenze che arrivano scaglionate
# nell'arco di 15-45 minuti circa.
#
# CH-3123 Belp, 2022/12/10 (pattern originale)     License GPL3     (c) Ernst Lobsiger
# ---------------------------------------------------------------------------------

import os, re, subprocess, sys
from glob import glob
from datetime import datetime

segdir = '/home/sps/received/bas/E1B-DWDSAT'
outdir = '/home/sps/SPSdata/products/MSLP/dwdfc'
convert = 'convert'

leadtimes = ['012', '036', '060', '084']

os.makedirs(outdir, exist_ok=True)

PATTERN = re.compile(r'ps401-pro_zwk_eu_p_(\d{3})_000-(\d{10})-triv---ps$')

produced = []
skipped = []
failed = []

for lt in leadtimes:
    files = glob(segdir + '/ps401-pro_zwk_eu_p_' + lt + '_000-*-triv---ps')
    if not files:
        continue

    # Keep the newest dissemination (files can arrive as near-duplicate pairs a
    # minute apart); sort by the embedded YYMMDDHHMM timestamp, not mtime, so a
    # late filesystem touch doesn't reorder things.
    def _ts(f):
        m = PATTERN.search(os.path.basename(f))
        return m.group(2) if m else ''

    files.sort(key=_ts)
    newest = files[-1]
    m = PATTERN.search(os.path.basename(newest))
    if not m:
        continue
    ts = m.group(2)  # YYMMDDHHMM
    run_dt = datetime.strptime('20' + ts, '%Y%m%d%H%M')
    run_str = run_dt.strftime('%Y%m%d%H%M')

    out_name = f'DWDFC-EU-{run_str}-P{lt}.jpg'
    out_path = os.path.join(outdir, out_name)

    if os.path.exists(out_path):
        skipped.append(out_name)
        continue

    tmp_path = out_path + '.tmp.jpg'
    r = subprocess.run([convert, newest, tmp_path], capture_output=True, text=True)
    if r.returncode == 0 and os.path.exists(tmp_path):
        os.replace(tmp_path, out_path)
        produced.append(out_name)
    else:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        failed.append((out_name, r.stderr.strip()[-300:]))

print(f'prodotte={len(produced)} {produced}')
print(f'gia_presenti={len(skipped)} {skipped}')
if failed:
    print(f'fallite={len(failed)} {failed}')
    sys.exit(1)
