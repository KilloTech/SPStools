#!/usr/bin/env python3
# Wrapper cron per NOAA-20 DAY pass - eurol area
# Ideale (calcolato da leo_images) ~12:42 UTC; cron: 30 14 * * * (era 15 13,
# margine insufficiente: falliva quasi ogni giorno con "no good files found",
# verificato 2026-09-17)
import subprocess, logging
from datetime import datetime, timezone

logging.basicConfig(filename="/home/sps/SPSdata/cron.log", level=logging.INFO,
                    format="%(asctime)s %(message)s")

now_utc = datetime.now(timezone.utc)
dat_str = now_utc.strftime("%Y%m%d") + "DAY"

logging.info(f"NOAA20 DAY start dat={dat_str}")
r = subprocess.run(
    ["/home/sps/miniconda3/envs/pytroll/bin/python3",
     "/home/sps/SPStools/LEOscripts/NOAA20-eurol.py",
     dat_str],
    capture_output=True, text=True,
    cwd="/home/sps/SPStools/LEOscripts"
)
logging.info(f"NOAA20 DAY done dat={dat_str} rc={r.returncode}")
if r.returncode != 0:
    logging.error(f"NOAA20 DAY stderr: {r.stderr[-500:]}")
