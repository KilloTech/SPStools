#!/usr/bin/env python3
# Wrapper cron per MetOp-B NIG pass - eurol area
# Cron: 0 22 * * *  (pass ~21:26 UTC + 34 min delivery)
import subprocess, logging
from datetime import datetime, timezone

logging.basicConfig(filename="/home/sps/SPSdata/cron.log", level=logging.INFO,
                    format="%(asctime)s %(message)s")

now_utc = datetime.now(timezone.utc)
dat_str = now_utc.strftime("%Y%m%d") + "NIG"

logging.info(f"MetopB NIG start dat={dat_str}")
r = subprocess.run(
    ["/home/sps/miniconda3/envs/pytroll/bin/python3",
     "/home/sps/SPStools/LEOscripts/MetopB-eurol.py",
     dat_str],
    capture_output=True, text=True
)
logging.info(f"MetopB NIG done dat={dat_str} rc={r.returncode}")
if r.returncode != 0:
    logging.error(f"MetopB NIG stderr: {r.stderr[-500:]}")
