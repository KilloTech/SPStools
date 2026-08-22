#!/usr/bin/env python3
# Wrapper cron per HIMA8 MSLP OPC Pacific West overlay - ogni 6h
# Cron: 20 4,10,16,22 * * *
# Usa la 6h-boundary piu recente come slot HIMA8
import subprocess, logging
from datetime import datetime, timezone

logging.basicConfig(filename="/home/sps/SPSdata/cron.log", level=logging.INFO,
                    format="%(asctime)s %(message)s")

now_utc = datetime.now(timezone.utc)
hour_6h = (now_utc.hour // 6) * 6
slot_dt = now_utc.replace(hour=hour_6h, minute=0, second=0, microsecond=0)
dat_str = slot_dt.strftime("%Y%m%d%H%M")

logging.info(f"HIMA8 MSLP OPC start slot={dat_str}")
r = subprocess.run(
    ["/home/sps/miniconda3/envs/pytroll/bin/python3",
     "/home/sps/SPStools/GEOscripts/HIMA8-MSLP-opcpw.py",
     dat_str],
    capture_output=True, text=True,
    cwd="/home/sps/SPStools/GEOscripts"
)
logging.info(f"HIMA8 MSLP OPC done slot={dat_str} rc={r.returncode}")
if r.returncode != 0:
    logging.error(f"HIMA8 MSLP OPC stderr: {r.stderr[-500:]}")
