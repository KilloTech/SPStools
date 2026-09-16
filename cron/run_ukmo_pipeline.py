#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Pipeline event-driven: scarica gli overlay UKMO (ukmos/ukmol), poi genera subito il
# chart MSLP con lo slot appena scaricato, invece di indovinare un orario fisso.
# Sostituisce il vecchio run_msg4_mslp_ukmo.py (basato su orario stimato).
# Cron: 5 2,8,14,20 * * * (stesso orario di UKMO-overlays.sh, la generazione segue subito)
import sys
sys.path.insert(0, "/home/sps/SPStools/cron")
from mslp_common import run, latest_slot, run_chart_script

run(["/bin/bash", "/home/sps/SPStools/cmdfiles/UKMO-overlays.sh"], "UKMO download")

# Slot esatto dell'overlay (lo snap al minuto MSG3 reale avviene dentro lo script)
run_chart_script("MSG4-MSLP-ukmox.py", latest_slot("ukmos"), "UKMO MSLP chart (ukmox/ukmos/ukmol)")
