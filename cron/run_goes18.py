#!/usr/bin/env python3
# Wrapper cron per GOES-18 full disk - slot ogni 10 minuti UTC
# Cron: 5-55/10 * * * *  (offset 5 min per non sovrapporre con GOES19)
import subprocess, logging
from datetime import datetime, timezone, timedelta

logging.basicConfig(filename="/home/sps/SPSdata/cron.log", level=logging.INFO,
                    format="%(asctime)s %(message)s")

LOOKBACK = 7
INTERVAL = 10

now_utc = datetime.now(timezone.utc) - timedelta(minutes=LOOKBACK)
slot_min = (now_utc.minute // INTERVAL) * INTERVAL
slot_time = now_utc.replace(minute=slot_min, second=0, microsecond=0)
slot_str = slot_time.strftime("%Y%m%d%H%M")

logging.info(f"GOES18 start slot={slot_str}")
r = subprocess.run(
    ["/home/sps/miniconda3/envs/pytroll/bin/python3",
     "/home/sps/SPStools/GEOscripts/GOES18-goes_wf_2km.py",
     slot_str],
    capture_output=True, text=True
)
logging.info(f"GOES18 done slot={slot_str} rc={r.returncode}")
if r.returncode != 0:
    logging.error(f"GOES18 stderr: {r.stderr[-500:]}")
