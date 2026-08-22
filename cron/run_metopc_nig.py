#!/usr/bin/env python3
# Wrapper cron per MetOp-C NIG pass - eurol area
# Cron: 45 21 * * *  (pass ~20:49 UTC + 56 min delivery, before MetopB NIG 22:00)
import subprocess, logging
from datetime import datetime, timezone

logging.basicConfig(filename="/home/sps/SPSdata/cron.log", level=logging.INFO,
                    format="%(asctime)s %(message)s")

now_utc = datetime.now(timezone.utc)
dat_str = now_utc.strftime("%Y%m%d") + "NIG"

logging.info(f"MetopC NIG start dat={dat_str}")
r = subprocess.run(
    ["/home/sps/miniconda3/envs/pytroll/bin/python3",
     "/home/sps/SPStools/LEOscripts/MetopC-eurol.py",
     dat_str],
    capture_output=True, text=True
)
logging.info(f"MetopC NIG done dat={dat_str} rc={r.returncode}")
if r.returncode != 0:
    logging.error(f"MetopC NIG stderr: {r.stderr[-500:]}")
