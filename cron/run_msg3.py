#!/usr/bin/env python3
# Wrapper cron per MSG3 FES 3km - slot ogni 15 minuti UTC
# Cron: */15 * * * * (lookback 5 min per attesa file)
import subprocess, logging
from datetime import datetime, timezone, timedelta

logging.basicConfig(filename="/home/sps/SPSdata/cron.log", level=logging.INFO,
                    format="%(asctime)s %(message)s")

LOOKBACK = 20   # minuti da aspettare dopo slot per file completo
INTERVAL = 15  # intervallo slot in minuti

now_utc = datetime.now(timezone.utc) - timedelta(minutes=LOOKBACK)
slot_min = (now_utc.minute // INTERVAL) * INTERVAL
slot_time = now_utc.replace(minute=slot_min, second=0, microsecond=0)
slot_str = slot_time.strftime("%Y%m%d%H%M")

logging.info(f"MSG3 start slot={slot_str}")
r = subprocess.run(
    ["/home/sps/miniconda3/envs/pytroll/bin/python3",
     "/home/sps/SPStools/GEOscripts/MSG3-msg_fes_3km.py",
     slot_str],
    capture_output=True, text=True
)
logging.info(f"MSG3 done slot={slot_str} rc={r.returncode}")
if r.returncode != 0:
    logging.error(f"MSG3 stderr: {r.stderr[-500:]}")
