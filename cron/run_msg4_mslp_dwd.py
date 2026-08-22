#!/usr/bin/env python3
# Wrapper cron per MSG4 MSLP DWD overlay - ogni 3h
# Cron: 45 */3 * * *
# Usa la 3h-boundary piu recente come slot MSG3
import subprocess, logging
from datetime import datetime, timezone

logging.basicConfig(filename="/home/sps/SPSdata/cron.log", level=logging.INFO,
                    format="%(asctime)s %(message)s")

now_utc = datetime.now(timezone.utc)
hour_3h = (now_utc.hour // 3) * 3          # es. 09:45 -> 09:00
slot_dt = now_utc.replace(hour=hour_3h, minute=0, second=0, microsecond=0)
dat_str = slot_dt.strftime("%Y%m%d%H%M")

logging.info(f"MSG4 MSLP DWD start slot={dat_str}")
r = subprocess.run(
    ["/home/sps/miniconda3/envs/pytroll/bin/python3",
     "/home/sps/SPStools/GEOscripts/MSG4-MSLP-dwdx.py",
     dat_str],
    capture_output=True, text=True,
    cwd="/home/sps/SPStools/GEOscripts"
)
logging.info(f"MSG4 MSLP DWD done slot={dat_str} rc={r.returncode}")
if r.returncode != 0:
    logging.error(f"MSG4 MSLP DWD stderr: {r.stderr[-500:]}")
