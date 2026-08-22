#!/usr/bin/env python3
# Wrapper cron per Sentinel-3A DAY pass - eurol area (OLCI daylight only)
# Cron: 15 11 * * *  (pass ~10:35 UTC + 40 min delivery)
import subprocess, logging
from datetime import datetime, timezone

logging.basicConfig(filename="/home/sps/SPSdata/cron.log", level=logging.INFO,
                    format="%(asctime)s %(message)s")

now_utc = datetime.now(timezone.utc)
dat_str = now_utc.strftime("%Y%m%d") + "DAY"

logging.info(f"Sen3A DAY start dat={dat_str}")
r = subprocess.run(
    ["/home/sps/miniconda3/envs/pytroll/bin/python3",
     "/home/sps/SPStools/LEOscripts/Sen3A-eurol.py",
     dat_str],
    capture_output=True, text=True
)
logging.info(f"Sen3A DAY done dat={dat_str} rc={r.returncode}")
if r.returncode != 0:
    logging.error(f"Sen3A DAY stderr: {r.stderr[-500:]}")
