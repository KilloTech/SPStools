#!/usr/bin/env python3
# Wrapper cron per GOES19 MSLP OPC
# Cron: 10 4,10,16,22 * * *
# Passa il tempo della carta (6-hourly: 00,06,12,18 UTC)
import subprocess, logging
from datetime import datetime, timezone

logging.basicConfig(filename="/home/sps/SPSdata/cron.log", level=logging.INFO,
                    format="%(asctime)s %(message)s")

now_utc = datetime.now(timezone.utc)
chart_hour = (now_utc.hour // 6) * 6
chart_dt = now_utc.replace(hour=chart_hour, minute=0, second=0, microsecond=0)
dat_str = chart_dt.strftime("%Y%m%d%H%M")

logging.info(f"GOES19 MSLP OPC start slot={dat_str}")
r = subprocess.run(
    ["/home/sps/miniconda3/envs/pytroll/bin/python3",
     "/home/sps/SPStools/GEOscripts/GOES19-MSLP-opcaw.py",
     dat_str],
    capture_output=True, text=True,
    cwd="/home/sps/SPStools/GEOscripts"
)
logging.info(f"GOES19 MSLP OPC done slot={dat_str} rc={r.returncode}")
if r.returncode != 0:
    logging.error(f"GOES19 MSLP OPC stderr: {r.stderr[-500:]}")
