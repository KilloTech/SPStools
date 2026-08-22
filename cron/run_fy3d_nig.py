#!/usr/bin/env python3
# Wrapper cron per FY-3D MERSI-2 NIG pass - eurol area
# Descending night pass over EU ~21:00-21:30 UTC; cron: 45 21 * * *
import subprocess, logging
from datetime import datetime, timezone

logging.basicConfig(filename="/home/sps/SPSdata/cron.log", level=logging.INFO,
                    format="%(asctime)s %(message)s")

now_utc = datetime.now(timezone.utc)
dat_str = now_utc.strftime("%Y%m%d") + "NIG"

logging.info(f"FY3D NIG start dat={dat_str}")
r = subprocess.run(
    ["/home/sps/miniconda3/envs/pytroll/bin/python3",
     "/home/sps/SPStools/LEOscripts/FY3D-eurol.py",
     dat_str],
    capture_output=True, text=True,
    cwd="/home/sps/SPStools/LEOscripts"
)
logging.info(f"FY3D NIG done dat={dat_str} rc={r.returncode}")
if r.returncode != 0:
    logging.error(f"FY3D NIG stderr: {r.stderr[-500:]}")
