#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Wrapper cron per eumetsat_alerts.py (archivio Service Alert da E1B-Info-Channel-2)
# Cron: */10 * * * *  (i file XML vengono ripuliti dalla retention del sistema dopo
# poco tempo, quindi vanno letti frequentemente prima che spariscano)
import subprocess, logging

logging.basicConfig(filename="/home/sps/SPSdata/cron.log", level=logging.INFO,
                    format="%(asctime)s %(message)s")

logging.info("EUMETSAT alerts start")
r = subprocess.run(
    ["/home/sps/miniconda3/envs/pytroll/bin/python3",
     "/home/sps/SPStools/cmdfiles/eumetsat_alerts.py"],
    capture_output=True, text=True
)
logging.info(f"EUMETSAT alerts done rc={r.returncode}")
if r.stdout.strip():
    logging.info(f"EUMETSAT alerts stdout: {r.stdout.strip()[-500:]}")
if r.returncode != 0:
    logging.error(f"EUMETSAT alerts stderr: {r.stderr[-500:]}")
