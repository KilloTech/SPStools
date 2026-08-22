#!/usr/bin/env python3
# Wrapper cron per Suomi-NPP DAY pass - eurol area
# LTAN=13:25 => pass EU ~12:55 UTC; cron: 10 13 * * *
import subprocess, logging
from datetime import datetime, timezone

logging.basicConfig(filename="/home/sps/SPSdata/cron.log", level=logging.INFO,
                    format="%(asctime)s %(message)s")

now_utc = datetime.now(timezone.utc)
dat_str = now_utc.strftime("%Y%m%d") + "DAY"

logging.info(f"SNPP DAY start dat={dat_str}")
r = subprocess.run(
    ["/home/sps/miniconda3/envs/pytroll/bin/python3",
     "/home/sps/SPStools/LEOscripts/SNPP-eurol.py",
     dat_str],
    capture_output=True, text=True,
    cwd="/home/sps/SPStools/LEOscripts"
)
logging.info(f"SNPP DAY done dat={dat_str} rc={r.returncode}")
if r.returncode != 0:
    logging.error(f"SNPP DAY stderr: {r.stderr[-500:]}")
