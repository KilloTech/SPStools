#!/usr/bin/env python3
# Wrapper cron per MODIS-Aqua Ocean Color L3m (CHL/KD/PAR/SST) - prodotto giornaliero
# Cron: 0 17 * * * (i file del giorno D arrivano su EUMETCast verso le 15-16 UTC del
# giorno D+1: alle 17 UTC c'e' ampio margine per processare il file del giorno prima)
import subprocess, logging
from datetime import datetime, timezone, timedelta

logging.basicConfig(filename="/home/sps/SPSdata/cron.log", level=logging.INFO,
                    format="%(asctime)s %(message)s")

yesterday = datetime.now(timezone.utc) - timedelta(days=1)
date_str = yesterday.strftime("%Y%m%d") + "0000"

logging.info(f"MODISOC start date={date_str}")
r = subprocess.run(
    ["/home/sps/miniconda3/envs/pytroll/bin/python3",
     "/home/sps/SPStools/GEOscripts/MODISOC-eurol.py",
     date_str],
    capture_output=True, text=True
)
logging.info(f"MODISOC done date={date_str} rc={r.returncode}")
if r.returncode != 0:
    logging.error(f"MODISOC stderr: {r.stderr[-500:]}")
