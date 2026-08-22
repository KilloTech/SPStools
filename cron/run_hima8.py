#!/usr/bin/env python3
# Wrapper cron per Himawari-8 full disk - slot ogni 10 minuti UTC
# Cron: 2-52/10 * * * *  (offset 2 min per staggering)
import subprocess, logging
from datetime import datetime, timezone, timedelta

logging.basicConfig(filename="/home/sps/SPSdata/cron.log", level=logging.INFO,
                    format="%(asctime)s %(message)s")

LOOKBACK = 22   # Himawari: dati arrivano con ~20 min ritardo, 22 min da slot start
INTERVAL = 10

now_utc = datetime.now(timezone.utc) - timedelta(minutes=LOOKBACK)
slot_min = (now_utc.minute // INTERVAL) * INTERVAL
slot_time = now_utc.replace(minute=slot_min, second=0, microsecond=0)
slot_str = slot_time.strftime("%Y%m%d%H%M")

logging.info(f"HIMA8 start slot={slot_str}")
r = subprocess.run(
    ["/home/sps/miniconda3/envs/pytroll/bin/python3",
     "/home/sps/SPStools/GEOscripts/HIMA8-hima_f_2km.py",
     slot_str],
    capture_output=True, text=True
)
logging.info(f"HIMA8 done slot={slot_str} rc={r.returncode}")
if r.returncode != 0:
    logging.error(f"HIMA8 stderr: {r.stderr[-500:]}")
