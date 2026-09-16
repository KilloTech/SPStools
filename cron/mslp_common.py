#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Funzioni condivise dalle pipeline MSLP (download -> generazione chart immediata)
import glob
import logging
import os
import subprocess

LOG_FILE = "/home/sps/SPSdata/cron.log"

logging.basicConfig(filename=LOG_FILE, level=logging.INFO,
                    format="%(asctime)s %(message)s")
log = logging.getLogger("mslp")


def latest_slot(area, kind="ww"):
    """Ritorna lo slot YYYYmmddHHMM (str) dell'overlay piu' recente per un'area,
    oppure None se non esiste nessun overlay. kind e' il tipo di file da cercare
    (bb/bc/wc/ww) - basta uno qualsiasi perche' sono sempre generati in coppia."""
    pattern = f"/home/sps/SPSdata/overlays/{area}/{area}-{kind}-*.png"
    files = glob.glob(pattern)
    if not files:
        return None
    latest = max(files, key=os.path.getmtime)
    base = os.path.basename(latest)
    # <area>-<kind>-<slot>.png
    slot = base.rsplit("-", 1)[-1].replace(".png", "")
    return slot


def run(cmd, label, cwd=None, timeout=180):
    """Esegue un comando, logga risultato, ritorna CompletedProcess."""
    log.info(f"{label} start")
    r = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd, timeout=timeout)
    log.info(f"{label} done rc={r.returncode}")
    if r.stdout.strip():
        log.info(f"{label} stdout: {r.stdout.strip()[-500:]}")
    if r.returncode != 0:
        log.error(f"{label} stderr: {r.stderr[-500:]}")
    return r


def run_chart_script(script_name, slot, label):
    """Lancia uno script di generazione chart GEOscripts/<script_name> con lo slot dato."""
    if slot is None:
        log.warning(f"{label}: nessuno slot disponibile, skip generazione")
        return
    run(
        ["/home/sps/miniconda3/envs/pytroll/bin/python3",
         f"/home/sps/SPStools/GEOscripts/{script_name}", slot],
        label,
        cwd="/home/sps/SPStools/GEOscripts",
    )
