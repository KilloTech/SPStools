#!/usr/bin/env python3
# Wrapper cron per Suomi-NPP NIG pass - eurol area
# Night descending pass over EU ~01:15 UTC; cron: 30 1 * * *
import subprocess, logging
from datetime import datetime, timezone

logging.basicConfig(filename="/home/sps/SPSdata/cron.log", level=logging.INFO,
                    format="%(asctime)s %(message)s")

now_utc = datetime.now(timezone.utc)
dat_str = now_utc.strftime("%Y%m%d") + "NIG"

logging.info(f"SNPP NIG start dat={dat_str}")
r = subprocess.run(
    ["/home/sps/miniconda3/envs/pytroll/bin/python3",
     "/home/sps/SPStools/LEOscripts/SNPP-eurol.py",
     dat_str],
    capture_output=True, text=True,
    cwd="/home/sps/SPStools/LEOscripts"
)
logging.info(f"SNPP NIG done dat={dat_str} rc={r.returncode}")
if r.returncode != 0:
    logging.error(f"SNPP NIG stderr: {r.stderr[-500:]}")
