#!/usr/bin/env python3
# Wrapper cron per DWDSAT-overlays.py — processa overlay DWD/UKMO MSLP da E1B-DWDSAT,
# poi genera subito i chart con gli slot appena arrivati (event-driven, niente orario
# stimato: il canale satellitare arriva quando arriva, non secondo un nostro schema).
# Cron: 15 * * * *  (ogni ora, 15 minuti dopo l'ora)
import sys
sys.path.insert(0, "/home/sps/SPStools/cron")
from mslp_common import run, latest_slot, run_chart_script

run(
    ["/home/sps/miniconda3/envs/pytroll/bin/python3",
     "/home/sps/SPStools/cmdfiles/DWDSAT-overlays.py"],
    "DWDSAT overlays",
    cwd="/home/sps/received/bas/E1B-DWDSAT",
)

# Slot esatto dell'overlay (lo snap al minuto MSG3 reale avviene dentro gli script)
run_chart_script("MSG4-MSLP-dwdx.py", latest_slot("dwda"), "DWDSAT MSLP chart (dwda/dwdn/dwdc/dwdi)")
run_chart_script("MSG4-MSLP-ukmox.py", latest_slot("ukmox"), "DWDSAT MSLP chart (ukmox/ukmos/ukmol)")
