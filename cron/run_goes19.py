#!/usr/bin/env python3
# Wrapper cron per GOES-19 full disk - slot ogni 10 minuti UTC
# Cron: 6,16,26,36,46,56 * * * *
# I 16 canali ABI full-disk completano l'arrivo via EUMETCast ~12-12.5 min dopo
# l'inizio slot (verificato 2026-09-12). LOOKBACK=16 da margine di sicurezza.
import subprocess, logging
from datetime import datetime, timezone, timedelta

logging.basicConfig(filename="/home/sps/SPSdata/cron.log", level=logging.INFO,
                    format="%(asctime)s %(message)s")

LOOKBACK = 16
INTERVAL = 10

now_utc = datetime.now(timezone.utc) - timedelta(minutes=LOOKBACK)
slot_min = (now_utc.minute // INTERVAL) * INTERVAL
slot_time = now_utc.replace(minute=slot_min, second=0, microsecond=0)
slot_str = slot_time.strftime("%Y%m%d%H%M")

logging.info(f"GOES19 start slot={slot_str}")
r = subprocess.run(
    ["/home/sps/miniconda3/envs/pytroll/bin/python3",
     "/home/sps/SPStools/GEOscripts/GOES19-goes_ef_2km.py",
     slot_str],
    capture_output=True, text=True
)
logging.info(f"GOES19 done slot={slot_str} rc={r.returncode}")
if r.returncode != 0:
    logging.error(f"GOES19 stderr: {r.stderr[-500:]}")
