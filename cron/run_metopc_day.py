#!/usr/bin/env python3
# Wrapper cron per MetOp-C DAY pass - eurol area
# Cron: 30 11 * * *  (pass ~10:07 UTC + 83 min delivery, staggered from MetopB 10:45)
import subprocess, logging
from datetime import datetime, timezone

logging.basicConfig(filename="/home/sps/SPSdata/cron.log", level=logging.INFO,
                    format="%(asctime)s %(message)s")

now_utc = datetime.now(timezone.utc)
dat_str = now_utc.strftime("%Y%m%d") + "DAY"

logging.info(f"MetopC DAY start dat={dat_str}")
r = subprocess.run(
    ["/home/sps/miniconda3/envs/pytroll/bin/python3",
     "/home/sps/SPStools/LEOscripts/MetopC-eurol.py",
     dat_str],
    capture_output=True, text=True
)
logging.info(f"MetopC DAY done dat={dat_str} rc={r.returncode}")
if r.returncode != 0:
    logging.error(f"MetopC DAY stderr: {r.stderr[-500:]}")
