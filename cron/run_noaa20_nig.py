#!/usr/bin/env python3
# Wrapper cron per NOAA-20 NIG pass - eurol area
# Ideale (calcolato da leo_images) ~02:01 UTC; cron: 30 3 * * * (era 45 1,
# ESEGUITO PRIMA del passaggio stesso: falliva sempre, verificato 2026-09-17)
import subprocess, logging
from datetime import datetime, timezone

logging.basicConfig(filename="/home/sps/SPSdata/cron.log", level=logging.INFO,
                    format="%(asctime)s %(message)s")

now_utc = datetime.now(timezone.utc)
dat_str = now_utc.strftime("%Y%m%d") + "NIG"

logging.info(f"NOAA20 NIG start dat={dat_str}")
r = subprocess.run(
    ["/home/sps/miniconda3/envs/pytroll/bin/python3",
     "/home/sps/SPStools/LEOscripts/NOAA20-eurol.py",
     dat_str],
    capture_output=True, text=True,
    cwd="/home/sps/SPStools/LEOscripts"
)
logging.info(f"NOAA20 NIG done dat={dat_str} rc={r.returncode}")
if r.returncode != 0:
    logging.error(f"NOAA20 NIG stderr: {r.stderr[-500:]}")
