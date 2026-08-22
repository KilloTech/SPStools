#!/usr/bin/env python3
# Wrapper cron per MSG3 NWC-SAF (CT, CMA, CTTH) - eurol area
# Cron: 10,25,40,55 * * * *  (offset +10 min da MSG3 slots 0,15,30,45 UTC)
import subprocess, logging
from datetime import datetime, timezone

logging.basicConfig(filename="/home/sps/SPSdata/cron.log", level=logging.INFO,
                    format="%(asctime)s %(message)s")

now_utc  = datetime.now(timezone.utc)
# Round down to previous 15-min slot
mins = (now_utc.minute - 10) // 15 * 15   # slot 10 min ago
slot = now_utc.replace(minute=mins, second=0, microsecond=0)
dat_str  = slot.strftime("%Y%m%d%H%M")

logging.info(f"MSG3 NWCSAF start slot={dat_str}")
r = subprocess.run(
    ["/home/sps/miniconda3/envs/pytroll/bin/python3",
     "/home/sps/SPStools/GEOscripts/MSG3-NWCSAF-eurol.py",
     dat_str],
    capture_output=True, text=True
)
logging.info(f"MSG3 NWCSAF done slot={dat_str} rc={r.returncode}")
if r.returncode != 0:
    logging.error(f"MSG3 NWCSAF stderr: {r.stderr[-300:]}")
