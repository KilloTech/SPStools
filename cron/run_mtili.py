#!/usr/bin/env python3
# Wrapper cron per MTG-I1 Lightning Imager AF (eurol) - ciclo ogni 10 minuti UTC
# Cron: 3,13,23,33,43,53 * * * * (TRAIL arriva ~25-30s dopo fine ciclo, lookback minimo)
import subprocess, logging
from datetime import datetime, timezone, timedelta

logging.basicConfig(filename="/home/sps/SPSdata/cron.log", level=logging.INFO,
                    format="%(asctime)s %(message)s")

LOOKBACK = 3
INTERVAL = 10

now_utc = datetime.now(timezone.utc) - timedelta(minutes=LOOKBACK)
slot_min = (now_utc.minute // INTERVAL) * INTERVAL
slot_time = now_utc.replace(minute=slot_min, second=0, microsecond=0)
slot_str = slot_time.strftime("%Y%m%d%H%M")

logging.info(f"MTILI start slot={slot_str}")
r = subprocess.run(
    ["/home/sps/miniconda3/envs/pytroll/bin/python3",
     "/home/sps/SPStools/GEOscripts/MTILI-eurol.py",
     slot_str],
    capture_output=True, text=True
)
logging.info(f"MTILI done slot={slot_str} rc={r.returncode}")
if r.returncode != 0:
    logging.error(f"MTILI stderr: {r.stderr[-500:]}")
