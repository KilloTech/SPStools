#!/bin/bash
# -----------------------------------------------------------------------
# run_geo_movies_6h.sh — Generate rolling 6-hour GEO movies (.webm)
# Runs every 6 hours (06:10 / 12:10 / 18:10 UTC).
# The 00:10 UTC daily run (run_geo_movies.sh) covers the overnight window.
# Output files use 'last6h' as date — always overwritten with latest 6h.
# -----------------------------------------------------------------------

MOVCMD="/home/sps/SPStools/cmdfiles/GEO-mov.sh"
LOG="/home/sps/SPSdata/cron.log"

run_movie() {
    local sat="$1"
    local comp_area="$2"
    echo "[$(date -u '+%Y-%m-%d %H:%M:%S')] GEO-mov-6h: $sat $comp_area last6h" >> $LOG
    bash $MOVCMD "$sat" "$comp_area" last6h 0 >> $LOG 2>&1
    echo "[$(date -u '+%Y-%m-%d %H:%M:%S')] GEO-mov-6h: $sat $comp_area done rc=$?" >> $LOG
}

# MSG4 RSS Europe (5-min = 72 frame/6h ~ 12 secondi)
run_movie MSG4  natural_color-eurol
run_movie MSG4  overview-eurol
run_movie MSG4  dust-eurol

# MSG3 Full Disk Europe (15-min = 24 frame/6h ~ 4 secondi)
run_movie MSG3  natural_color-eurol
run_movie MSG3  overview-eurol

# MTI1 FCI Europe (10-min = 36 frame/6h ~ 6 secondi)
run_movie MTI1  natural_color-eurol
run_movie MTI1  overview-eurol

echo "[$(date -u '+%Y-%m-%d %H:%M:%S')] GEO-mov-6h: all 6h movies done" >> $LOG
