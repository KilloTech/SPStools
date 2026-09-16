#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Pipeline event-driven: scarica gli overlay DWD OpenData (dwda/dwdn/dwdc), poi genera
# subito i chart MSLP con lo slot appena scaricato (invece di indovinare un orario fisso
# con margine di sicurezza, spesso insufficiente rispetto ai ritardi reali di DWD).
# Sostituisce il vecchio run_msg4_mslp_dwd.py (basato su orario stimato).
# Cron: 30 */3 * * * (stesso orario di DWD-overlays.sh, la generazione segue subito)
import sys
sys.path.insert(0, "/home/sps/SPStools/cron")
from mslp_common import run, latest_slot, run_chart_script

run(["/bin/bash", "/home/sps/SPStools/cmdfiles/DWD-overlays.sh"], "DWD download")

# Nota: lo slot passato deve restare quello ESATTO dell'overlay (es. minuto :00),
# perche' get_lists() in GEOstuff.py cerca il file overlay con questo nome esatto.
# Lo script MSG4-MSLP-dwdx.py fa internamente lo snap al minuto reale MSG3
# (:15/:45) solo per la ricerca dati satellite, non per l'overlay.
run_chart_script("MSG4-MSLP-dwdx.py", latest_slot("dwda"), "DWD MSLP chart (dwda/dwdn/dwdc/dwdi)")
