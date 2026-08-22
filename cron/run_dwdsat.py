#!/usr/bin/env python3
# Wrapper cron per DWDSAT-overlays.py — processa overlay DWD MSLP da E1B-DWDSAT
# Cron: 15 * * * *  (ogni ora, 15 minuti dopo l ora)
import subprocess, logging

logging.basicConfig(filename="/home/sps/SPSdata/cron.log", level=logging.INFO,
                    format="%(asctime)s %(message)s")

logging.info("DWDSAT overlays start")
r = subprocess.run(
    ["/home/sps/miniconda3/envs/pytroll/bin/python3",
     "/home/sps/SPStools/cmdfiles/DWDSAT-overlays.py"],
    capture_output=True, text=True,
    cwd="/home/sps/received/bas/E1B-DWDSAT"
)
logging.info(f"DWDSAT overlays done rc={r.returncode}")
if r.stdout.strip():
    logging.info(f"DWDSAT stdout: {r.stdout.strip()[-500:]}")
if r.returncode != 0:
    logging.error(f"DWDSAT stderr: {r.stderr[-500:]}")
