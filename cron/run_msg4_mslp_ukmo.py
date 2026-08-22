#!/usr/bin/env python3
# Wrapper cron per MSG4 MSLP UKMO overlay - ogni 6h
# Cron: 20 2,8,14,20 * * *  (15 min dopo UKMO-overlays.sh alle :05)
# Usa la 6h-boundary piu recente come slot MSG3
import subprocess, logging
from datetime import datetime, timezone

logging.basicConfig(filename="/home/sps/SPSdata/cron.log", level=logging.INFO,
                    format="%(asctime)s %(message)s")

now_utc = datetime.now(timezone.utc)
hour_6h = (now_utc.hour // 6) * 6          # 02:20 -> 00:00; 14:20 -> 12:00 etc.
slot_dt = now_utc.replace(hour=hour_6h, minute=0, second=0, microsecond=0)
dat_str = slot_dt.strftime("%Y%m%d%H%M")

logging.info(f"MSG4 MSLP UKMO start slot={dat_str}")
r = subprocess.run(
    ["/home/sps/miniconda3/envs/pytroll/bin/python3",
     "/home/sps/SPStools/GEOscripts/MSG4-MSLP-ukmox.py",
     dat_str],
    capture_output=True, text=True,
    cwd="/home/sps/SPStools/GEOscripts"
)
logging.info(f"MSG4 MSLP UKMO done slot={dat_str} rc={r.returncode}")
if r.returncode != 0:
    logging.error(f"MSG4 MSLP UKMO stderr: {r.stderr[-500:]}")
