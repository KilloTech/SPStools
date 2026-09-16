#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Pipeline event-driven: scarica gli overlay OPC (opcae/opcaw/opcpe/opcpw), poi genera
# subito i 4 chart MSLP satellite-specifici con lo slot appena scaricato per ciascuna
# area, invece di indovinare un orario fisso con margine spesso insufficiente.
# Sostituisce i vecchi run_msg4_mslp_opc.py / run_goes19_mslp_opc.py /
# run_goes18_mslp_opc.py / run_hima8_mslp_opc.py (basati su orario stimato).
# Cron: 45 3,9,15,21 * * * (stesso orario di OPC-overlays.sh, la generazione segue subito)
import sys
sys.path.insert(0, "/home/sps/SPStools/cron")
from mslp_common import run, latest_slot, run_chart_script

run(["/bin/bash", "/home/sps/SPStools/cmdfiles/OPC-overlays.sh"], "OPC download")

# Slot esatto dell'overlay (lo snap al minuto MSG3 reale avviene dentro lo script)
run_chart_script("MSG4-MSLP-opcae.py", latest_slot("opcae", kind="wc"), "OPC MSLP chart (opcae/MSG4)")
run_chart_script("GOES19-MSLP-opcaw.py", latest_slot("opcaw", kind="wc"), "OPC MSLP chart (opcaw/GOES19)")
run_chart_script("GOES18-MSLP-opcpe.py", latest_slot("opcpe", kind="wc"), "OPC MSLP chart (opcpe/GOES18)")
run_chart_script("HIMA8-MSLP-opcpw.py", latest_slot("opcpw", kind="wc"), "OPC MSLP chart (opcpw/HIMA8)")
