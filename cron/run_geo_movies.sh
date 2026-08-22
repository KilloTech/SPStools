#!/bin/bash
# -----------------------------------------------------------------------
# run_geo_movies.sh — Generate daily GEO satellite movies (.webm)
# Calls GEO-mov.sh for each satellite/composite combination.
# Scheduled daily at 00:10 UTC to process "yesterday" full day frames.
#
# GEO-mov.sh syntax:
#   GEO-mov.sh <SAT> <composite-area> <date> <size_reduction>
#   date: yesterday | today | YYYYmmdd | last24h | last48h | last72h
#   size: 0=keep original size (frames/)  1=reduce to 1080p (images/)
# -----------------------------------------------------------------------

MOVCMD="/home/sps/SPStools/cmdfiles/GEO-mov.sh"
LOG="/home/sps/SPSdata/cron.log"

run_movie() {
    local sat="$1"
    local comp_area="$2"
    local date="$3"
    echo "[$(date -u '+%Y-%m-%d %H:%M:%S')] GEO-mov: $sat $comp_area $date" >> $LOG
    bash $MOVCMD "$sat" "$comp_area" "$date" 0 >> $LOG 2>&1
    echo "[$(date -u '+%Y-%m-%d %H:%M:%S')] GEO-mov: $sat $comp_area done rc=$?" >> $LOG
}

DATE="yesterday"

# MSG3 — SEVIRI Full Disk Europe (15-min, many composites)
run_movie MSG3  overview-eurol          $DATE
run_movie MSG3  natural_color-eurol     $DATE
run_movie MSG3  dust-eurol              $DATE
run_movie MSG3  colorized_ir_clouds-eurol $DATE

# MSG4 — SEVIRI RSS Europe (5-min)
run_movie MSG4  overview-eurol          $DATE
run_movie MSG4  dust-eurol              $DATE

# GOES-19 East Full Disk
run_movie GOES19 overview-goes_ef_2km   $DATE
run_movie GOES19 true_color-goes_ef_2km $DATE
run_movie GOES19 dust-goes_ef_2km       $DATE

# GOES-18 West Full Disk
run_movie GOES18 overview-goes_wf_2km   $DATE
run_movie GOES18 true_color-goes_wf_2km $DATE
run_movie GOES18 dust-goes_wf_2km       $DATE

# Himawari-9 Full Disk
run_movie HIMA8 overview-hima_f_2km     $DATE
run_movie HIMA8 true_color-hima_f_2km   $DATE
run_movie HIMA8 dust-hima_f_2km         $DATE

# MTG-I1 FCI
run_movie MTI1  overview-eurol          $DATE
run_movie MTI1  colorized_ir_clouds-eurol $DATE
run_movie MTI1  dust-eurol              $DATE

echo "[$(date -u '+%Y-%m-%d %H:%M:%S')] GEO-mov: all movies done" >> $LOG
