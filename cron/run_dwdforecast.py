#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Wrapper cron per DWDforecast-eu.py (carte previsionali DWD ps401, canale E1B-DWDSAT)
# Cron: */15 * * * *  (le 4 scadenze +012/+036/+060/+084h arrivano scaglionate nei
# ~45 min dopo ogni run 00Z/12Z; lo script salta i prodotti gia' presenti, quindi
# un controllo ogni 15 min li recupera senza rielaborare quelli gia' fatti)
import subprocess, logging

logging.basicConfig(filename="/home/sps/SPSdata/cron.log", level=logging.INFO,
                    format="%(asctime)s %(message)s")

logging.info("DWD forecast start")
r = subprocess.run(
    ["/home/sps/miniconda3/envs/pytroll/bin/python3",
     "/home/sps/SPStools/cmdfiles/DWDforecast-eu.py"],
    capture_output=True, text=True
)
logging.info(f"DWD forecast done rc={r.returncode}")
if r.stdout.strip():
    logging.info(f"DWD forecast stdout: {r.stdout.strip()[-500:]}")
if r.returncode != 0:
    logging.error(f"DWD forecast stderr: {r.stderr[-500:]}")
