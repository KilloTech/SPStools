#!/usr/bin/env python3
# Wrapper cron per Sentinel-3B SLSTR SST - eurol area
# Processes day pass tiles arriving around 10:10 UTC
# Cron: 45 10 * * *
import subprocess, logging
from datetime import datetime, timezone

logging.basicConfig(filename="/home/sps/SPSdata/cron.log", level=logging.INFO,
                    format="%(asctime)s %(message)s")

now_utc = datetime.now(timezone.utc)
dat_str = now_utc.strftime("%Y%m%d")

logging.info(f"Sen3B SLSTR start dat={dat_str}")
r = subprocess.run(
    ["/home/sps/miniconda3/envs/pytroll/bin/python3",
     "/home/sps/SPStools/LEOscripts/Sen3B-slstr-eurol.py",
     dat_str],
    capture_output=True, text=True,
    cwd="/home/sps/SPStools/LEOscripts"
)
logging.info(f"Sen3B SLSTR done dat={dat_str} rc={r.returncode}")
if r.returncode != 0:
    logging.error(f"Sen3B SLSTR stderr: {r.stderr[-500:]}")
