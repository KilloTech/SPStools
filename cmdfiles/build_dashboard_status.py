#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------------
# Genera /home/sps/SPSdata/dashboard/status.json leggendo cron.log e poche
# altre fonti (df, s3_archive.log, mtime prodotti). Pensato per girare ogni
# minuto via cron e alimentare la dashboard statica (index.html + fetch()).
#
# Non serve toccare i ~30 wrapper cron esistenti: tutti loggano gia' con la
# convenzione "<label> start" / "<label> done ... rc=<n>" su cron.log, quindi
# basta parsare quello. I pochi job senza questa convenzione (movie, tidy,
# TLE) sono dedotti da mtime dei loro output.
# ---------------------------------------------------------------------------
import json
import os
import re
import subprocess
import tempfile
from datetime import datetime, timedelta, timezone

CRON_LOG = "/home/sps/SPSdata/cron.log"
S3_LOG = "/home/sps/SPSdata/s3_archive.log"
ALERTS_STORE = "/home/sps/SPSdata/eumetsat_alerts.json"
PRODUCTS_DIR = "/home/sps/SPSdata/products"
OUT_DIR = "/home/sps/SPSdata/dashboard"
OUT_FILE = OUT_DIR + "/status.json"

LOOKBACK_HOURS = 48      # finestra di parsing del log (copre anche i job giornalieri)
STATS_HOURS = 24         # finestra per il tasso di successo/falliti mostrato in alto
HISTORY_POINTS = 12      # quanti run recenti mostrare nello sparkline
STALE_RUNNING_MINUTES = 180  # oltre questa soglia uno 'start' senza 'done' e' considerato
                              # pianta/crashato, non piu' "in corso" (il piu' lento job
                              # osservato, S3 archive, impiega di norma <1h)

# ── Catalogo job: label esatta nel log -> metadati per la dashboard ────────
# schedule e' in sintassi crontab a 5 campi (minuto ora giorno mese gg-settimana)
JOBS = [
    # ---- GEO tempo reale ----
    ("MSG3",               "GEO", "Meteosat-10 IODC 3km",        "E1B-GEO-3",  "5,20,35,50 * * * *"),
    ("MSG2",               "GEO", "Meteosat-9 IODC 3km",         "E1B-GEO-2",  "0,15,30,45 * * * *"),
    ("MSG3 NWCSAF",        "GEO", "NWC-SAF cloud (CT/CMA/CTTH)", "E1B-GEO-3",  "10,25,40,55 * * * *"),
    ("MSG4",               "GEO", "Meteosat-11 FES RSS",         "E1B-GEO-5",  "3,8,13,18,23,28,33,38,43,48,53,58 * * * *"),
    ("GOES19",              "GEO", "GOES-19 East full disk",      "E1H-TPG-1",  "6,16,26,36,46,56 * * * *"),
    ("GOES18",              "GEO", "GOES-18 West full disk",      "E1H-TPG-4",  "7,17,27,37,47,57 * * * *"),
    ("HIMA8",               "GEO", "Himawari-8 full disk",        "E1H-TPG-2",  "2,12,22,32,42,52 * * * *"),
    ("MTI1",               "GEO", "MTG-I1 FCI full disk",        "E2H-MTG-1",  "5,15,25,35,45,55 * * * *"),
    ("MTILI",              "GEO", "MTG-I1 Lightning Imager",     "E2H-MTG-LI", "3,13,23,33,43,53 * * * *"),

    # ---- LEO passaggi giornalieri ----
    ("MetopB DAY",         "LEO", "MetOp-B AVHRR giorno",        "E1B-EPS-10", "45 10 * * *"),
    ("MetopB NIG",         "LEO", "MetOp-B AVHRR notte",         "E1B-EPS-10", "0 22 * * *"),
    ("MetopC DAY",         "LEO", "MetOp-C AVHRR giorno",        "E1B-EPS-11", "30 11 * * *"),
    ("MetopC NIG",         "LEO", "MetOp-C AVHRR notte",         "E1B-EPS-11", "45 21 * * *"),
    ("Sen3A DAY",          "LEO", "Sentinel-3A OLCI (full orbit)","E2H-S3A-02", "40 12 * * *"),
    ("Sen3A OLCI",         "LEO", "Sentinel-3A true/ocean color","E2H-S3A-02", "30 11 * * *"),
    ("Sen3A SLSTR",        "LEO", "Sentinel-3A SLSTR SST",       "E2H-S3A-04", "0 11 * * *"),
    ("Sen3B DAY",          "LEO", "Sentinel-3B OLCI (full orbit)","E2H-S3B-02", "5 12 * * *"),
    ("Sen3B OLCI",         "LEO", "Sentinel-3B true/ocean color","E2H-S3B-02", "0 12 * * *"),
    ("Sen3B SLSTR",        "LEO", "Sentinel-3B SLSTR SST",       "E2H-S3B-04", "40 10 * * *"),
    ("NOAA20 DAY",         "LEO", "NOAA-20 VIIRS giorno",        "E1B-VIIRS-1","15 13 * * *"),
    ("NOAA20 NIG",         "LEO", "NOAA-20 VIIRS notte",         "E1B-VIIRS-1","45 1 * * *"),
    ("SNPP DAY",           "LEO", "Suomi-NPP VIIRS giorno",      "E1B-VIIRS-2","10 13 * * *"),
    ("SNPP NIG",           "LEO", "Suomi-NPP VIIRS notte",       "E1B-VIIRS-2","30 1 * * *"),
    ("FY3D DAY",           "LEO", "FY-3D MERSI-2 giorno",        "E1B-FY3-1",  "30 13 * * *"),
    ("FY3D NIG",           "LEO", "FY-3D MERSI-2 notte",         "E1B-FY3-1",  "45 21 * * *"),
    ("MODISOC",            "LEO", "MODIS-Aqua Ocean Color",      "E1B-TPC-6",  "0 17 * * *"),

    # ---- MSLP: chart di pressione ----
    ("DWD download",                          "MSLP", "Download DWD OpenData",        "opendata.dwd.de", "30 */3 * * *"),
    ("DWD MSLP chart (dwda/dwdn/dwdc/dwdi)",  "MSLP", "Generazione chart DWD",         "MSG3",            "30 */3 * * *"),
    ("OPC download",                          "MSLP", "Download OPC (NOAA)",           "ocean.weather.gov","45 3,9,15,21 * * *"),
    ("OPC MSLP chart (opcae/MSG4)",           "MSLP", "Chart OPC Atlantic East",       "MSG3",            "45 3,9,15,21 * * *"),
    ("OPC MSLP chart (opcaw/GOES19)",         "MSLP", "Chart OPC Atlantic West",       "GOES19",          "45 3,9,15,21 * * *"),
    ("OPC MSLP chart (opcpe/GOES18)",         "MSLP", "Chart OPC Pacific East",        "GOES18",          "45 3,9,15,21 * * *"),
    ("OPC MSLP chart (opcpw/HIMA8)",          "MSLP", "Chart OPC Pacific West",        "HIMA8",           "45 3,9,15,21 * * *"),
    ("UKMO download",                         "MSLP", "Download UKMO",                 "weathercharts.net","5 2,8,14,20 * * *"),
    ("UKMO MSLP chart (ukmox/ukmos/ukmol)",   "MSLP", "Generazione chart UKMO",        "MSG3",            "5 2,8,14,20 * * *"),
    ("DWDSAT overlays",                       "MSLP", "Overlay DWD/UKMO da satellite", "E1B-DWDSAT",      "15 * * * *"),
    ("DWDSAT MSLP chart (dwda/dwdn/dwdc/dwdi)","MSLP", "Chart DWD da satellite",        "MSG3",            "15 * * * *"),
    ("DWDSAT MSLP chart (ukmox/ukmos/ukmol)", "MSLP", "Chart UKMO da satellite",       "MSG3",            "15 * * * *"),
    ("DWD forecast",                          "MSLP", "Carte previsionali DWD (ps401)", "E1B-DWDSAT",     "*/15 * * * *"),

    # ---- Manutenzione ----
    ("S3 archive",         "MAINT", "Archiviazione su Cubbit S3",  "s3.cubbit.eu", "45 0,6,12,18 * * *"),
    ("EUMETSAT alerts",    "MAINT", "Archivio service alert",      "E1B-Info-Channel-2", "*/10 * * * *"),
]

DISPLAY_OVERRIDES = {
    "MSG3": "MSG3 IODC", "MSG2": "MSG2 IODC", "MSG4": "MSG4 RSS",
    "GOES19": "GOES-19 East", "GOES18": "GOES-18 West", "HIMA8": "Himawari-8",
    "MTI1": "MTG-I1 FCI", "MTILI": "MTG-I1 LI",
}

# ── Job "file-based" senza pattern start/done nel log ──────────────────────
FILE_JOBS = [
    {
        "name": "Movie giornaliero", "group": "MAINT", "chan": "ffmpeg",
        "schedule": "10 0 * * *",
        "check_glob": "/home/sps/SPSdata/products/*/movies/*.webm",
    },
    {
        "name": "Tidy cleanup", "group": "MAINT", "chan": "tidy.sh",
        "schedule": "0 1 * * *",
        "check_glob": None,  # nessun output diretto: solo schedule
    },
    {
        "name": "TLE update", "group": "MAINT", "chan": "celestrak",
        "schedule": "0 3 * * 0",
        "check_glob": "/home/sps/SPStools/userconfig/my_TLE_file.txt",
    },
]

GROUP_ORDER = ["GEO", "LEO", "MSLP", "MAINT"]
GROUP_LABEL = {
    "GEO": "GEO — tempo reale", "LEO": "LEO — passaggi giornalieri",
    "MSLP": "MSLP — chart di pressione", "MAINT": "Manutenzione",
}


# ── Mini cron-next-run (basta liste/step/asterisco, niente range a-b) ──────
def _parse_field(field, lo, hi):
    if field == "*":
        return set(range(lo, hi + 1))
    out = set()
    for part in field.split(","):
        if part.startswith("*/"):
            step = int(part[2:])
            out.update(range(lo, hi + 1, step))
        else:
            out.add(int(part))
    return out


def next_run(schedule, from_dt):
    minute_f, hour_f, dom_f, mon_f, dow_f = schedule.split()
    minutes = _parse_field(minute_f, 0, 59)
    hours = _parse_field(hour_f, 0, 23)
    doms = _parse_field(dom_f, 1, 31) if dom_f != "*" else None
    dows = _parse_field(dow_f, 0, 6) if dow_f != "*" else None

    t = from_dt.replace(second=0, microsecond=0) + timedelta(minutes=1)
    for _ in range(60 * 24 * 8):  # max 8 giorni avanti
        if t.minute in minutes and t.hour in hours:
            dom_ok = doms is None or t.day in doms
            dow_ok = dows is None or (t.weekday() + 1) % 7 in dows  # cron: 0=domenica
            if dom_ok and dow_ok:
                return t
        t += timedelta(minutes=1)
    return None


# ── Parsing cron.log ────────────────────────────────────────────────────
# NB: niente ancora ^ / uso search(), non match(): alcune righe hanno in testa
# output "sporco" di wget (barra di progresso con \r, niente newline) prima
# del vero timestamp di log, es. "    50K .......... ...2026-09-14 19:45:02
# FY3D NIG done ... rc=1" — con match()+^ questi "done" venivano persi,
# lasciando il job marcato per sempre come "in corso".
START_RE = re.compile(
    r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}),\d+ (.{1,60}?) start\b"
)
DONE_RE = re.compile(
    r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}),\d+ (.{1,60}?) done\b.*?rc=(-?\d+)"
)


def parse_events(path, since_dt):
    """Ritorna {label: [(ts, 'start'|'done', rc_or_None), ...]} ordinato per ts."""
    events = {}
    if not os.path.exists(path):
        return events
    with open(path, encoding="utf-8", errors="replace") as f:
        for line in f:
            if "stdout:" in line or "stderr:" in line:
                continue
            m = START_RE.search(line)
            if m:
                ts = datetime.strptime(m.group(1), "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
                if ts < since_dt:
                    continue
                events.setdefault(m.group(2), []).append((ts, "start", None))
                continue
            m = DONE_RE.search(line)
            if m:
                ts = datetime.strptime(m.group(1), "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
                if ts < since_dt:
                    continue
                events.setdefault(m.group(2), []).append((ts, "done", int(m.group(3))))
    for v in events.values():
        v.sort(key=lambda x: x[0])
    return events


def fmt_ago(ts, now):
    if ts is None:
        return "mai"
    delta = now - ts
    s = int(delta.total_seconds())
    if s < 0:
        s = 0
    if s < 60:
        return f"{s}s fa"
    if s < 3600:
        return f"{s // 60} min fa"
    if s < 86400:
        h = s // 3600
        m = (s % 3600) // 60
        return f"{h}h {m:02d}m fa"
    d = s // 86400
    h = (s % 86400) // 3600
    return f"{d}g {h}h fa"


def fmt_in(ts, now):
    if ts is None:
        return "—"
    delta = ts - now
    s = int(delta.total_seconds())
    if s < 0:
        return "ora"
    if s < 3600:
        return f"{s // 60} min"
    if s < 86400:
        h = s // 3600
        m = (s % 3600) // 60
        return f"{h}h {m:02d}m"
    d = s // 86400
    h = (s % 86400) // 3600
    return f"{d}g {h}h"


def fmt_dur(seconds):
    if seconds is None:
        return "—"
    if seconds < 60:
        return f"{seconds:.0f}s"
    m = int(seconds // 60)
    s = int(seconds % 60)
    return f"{m}m {s:02d}s"


def build_job_row(label, group, desc, chan, schedule, events, now):
    evs = events.get(label, [])
    # Pairing: scorriamo in ordine, ogni 'start' si accoppia col prossimo 'done'
    runs = []  # lista di dict {start, done, rc, dur}
    pending_start = None
    for ts, kind, rc in evs:
        if kind == "start":
            pending_start = ts
        else:  # done
            dur = (ts - pending_start).total_seconds() if pending_start else None
            runs.append({"start": pending_start, "done": ts, "rc": rc, "dur": dur})
            pending_start = None

    dangling = pending_start is not None and (not runs or pending_start > runs[-1]["done"])
    stale = dangling and (now - pending_start) > timedelta(minutes=STALE_RUNNING_MINUTES)
    running = dangling and not stale

    last_run = runs[-1] if runs else None
    if running:
        status = "running"
        last_ts = pending_start
        dur_txt = fmt_dur((now - pending_start).total_seconds())
    elif stale:
        # 'start' senza 'done' da troppo tempo: probabile crash/kill silenzioso
        status = "fail"
        last_ts = pending_start
        dur_txt = "bloccato"
    elif last_run:
        status = "ok" if last_run["rc"] == 0 else "fail"
        last_ts = last_run["done"]
        dur_txt = fmt_dur(last_run["dur"])
    else:
        status = "idle"
        last_ts = None
        dur_txt = "—"

    hist = [("ok" if r["rc"] == 0 else "fail") for r in runs[-HISTORY_POINTS:]]
    while len(hist) < HISTORY_POINTS:
        hist.insert(0, None)
    if running:
        hist = hist[1:] + ["running"]
    elif stale:
        hist = hist[1:] + ["fail"]

    nxt = next_run(schedule, now)

    stats_cutoff = now - timedelta(hours=STATS_HOURS)
    runs_24h = [r for r in runs if r["done"] >= stats_cutoff]

    return {
        "name": DISPLAY_OVERRIDES.get(label, label),
        "chan": chan,
        "desc": desc,
        "group": group,
        "status": status,
        "last": fmt_ago(last_ts, now),
        "dur": dur_txt,
        "next": fmt_in(nxt, now),
        "hist": hist,
        "runs_in_window": len(runs_24h),
        "fails_in_window": sum(1 for r in runs_24h if r["rc"] != 0),
    }


def build_file_job_row(job, now):
    import glob
    label = job["name"]
    schedule = job["schedule"]
    mtime = None
    if job["check_glob"]:
        matches = glob.glob(job["check_glob"])
        if matches:
            mtime = max(os.path.getmtime(p) for p in matches)
    nxt = next_run(schedule, now)
    if mtime:
        last_dt = datetime.fromtimestamp(mtime, tz=timezone.utc)
        status = "ok"
        last_txt = fmt_ago(last_dt, now)
    else:
        status = "idle"
        last_txt = "n/d"
    return {
        "name": label, "chan": job["chan"], "desc": "", "group": job["group"],
        "status": status, "last": last_txt, "dur": "—", "next": fmt_in(nxt, now),
        "hist": [None] * (HISTORY_POINTS - 1) + [status if status != "idle" else None],
        "runs_in_window": 0, "fails_in_window": 0,
    }


def disk_usage(path):
    try:
        st = os.statvfs(path)
        total = st.f_blocks * st.f_frsize
        free = st.f_bavail * st.f_frsize
        used = total - free
        return {"used_gb": round(used / 1e9, 1), "total_gb": round(total / 1e9, 1),
                "pct": round(100 * used / total, 1) if total else 0}
    except OSError:
        return None


def s3_freed_today(now):
    if not os.path.exists(S3_LOG):
        return 0.0, 0
    today = now.strftime("%Y-%m-%d")
    freed = 0.0
    runs = 0
    pat = re.compile(r"^(\d{4}-\d{2}-\d{2}) .*=== s3_archive done.*freed=([\d.]+) GB")
    with open(S3_LOG, encoding="utf-8", errors="replace") as f:
        for line in f:
            m = pat.match(line)
            if m and m.group(1) == today:
                freed += float(m.group(2))
                runs += 1
    return round(freed, 2), runs


def images_last_24h(now):
    # -L: PRODUCTS_DIR e' un symlink (-> /media/sps/SPS_archive/SPSdata-products),
    # senza seguirlo find non scende nell'albero e conta sempre 0.
    count = 0
    try:
        out = subprocess.run(
            ["find", "-L", PRODUCTS_DIR, "-type", "f",
             "(", "-name", "*.jpg", "-o", "-name", "*.png", ")",
             "-mtime", "-1"],
            capture_output=True, text=True, timeout=25,
        )
        count = len(out.stdout.splitlines())
    except Exception:
        count = -1
    return count


def eumetsat_alerts():
    # Storico gia' filtrato a 7 giorni da eumetsat_alerts.py; qui solo lettura e ordinamento.
    if not os.path.exists(ALERTS_STORE):
        return [], 0
    try:
        with open(ALERTS_STORE, encoding="utf-8") as f:
            store = json.load(f)
    except (json.JSONDecodeError, OSError):
        return [], 0

    items = []
    active_count = 0
    for rec in store.values():
        is_active = rec.get("status") not in ("recovered", "closed", "resolved")
        if is_active:
            active_count += 1
        items.append({
            "ann_number": rec.get("ann_number", ""),
            "status": rec.get("status", ""),
            "active": is_active,
            "impact": rec.get("impact", ""),
            "subject": rec.get("subject", ""),
            "satellites": rec.get("satellites", []),
            "services": rec.get("services", []),
            "detail": rec.get("detail", ""),
            "start_time": rec.get("start_time", ""),
            "end_time": rec.get("end_time", ""),
        })
    items.sort(key=lambda r: r["start_time"], reverse=True)
    return items, active_count


def main():
    now = datetime.now(timezone.utc)
    since = now - timedelta(hours=LOOKBACK_HOURS)
    events = parse_events(CRON_LOG, since)

    groups = {g: [] for g in GROUP_ORDER}
    all_rows = []
    next_candidates = []  # (next_dt, display_name)
    for label, group, desc, chan, schedule in JOBS:
        row = build_job_row(label, group, desc, chan, schedule, events, now)
        groups[group].append(row)
        all_rows.append(row)
        nd = next_run(schedule, now)
        if nd:
            next_candidates.append((nd, DISPLAY_OVERRIDES.get(label, label)))
    for job in FILE_JOBS:
        row = build_file_job_row(job, now)
        groups[job["group"]].append(row)
        all_rows.append(row)
        nd = next_run(job["schedule"], now)
        if nd:
            next_candidates.append((nd, job["name"]))

    next_candidates.sort(key=lambda x: x[0])
    next_job = None
    if next_candidates:
        nd, nn = next_candidates[0]
        next_job = {"name": nn, "in": fmt_in(nd, now), "at": nd.strftime("%H:%M UTC")}

    running_now = [r["name"] for r in all_rows if r["status"] == "running"]
    total_runs = sum(r["runs_in_window"] for r in all_rows)
    total_fails = sum(r["fails_in_window"] for r in all_rows)
    success_rate = round(100 * (total_runs - total_fails) / total_runs, 1) if total_runs else None

    freed_gb, s3_runs_today = s3_freed_today(now)
    alert_items, alert_active_count = eumetsat_alerts()

    # ultime righe di log "pulite" (solo eventi start/done riconosciuti) per il tail
    tail = []
    for label, evs in events.items():
        for ts, kind, rc in evs:
            tail.append((ts, label, kind, rc))
    tail.sort(key=lambda x: x[0], reverse=True)
    log_tail = []
    for ts, label, kind, rc in tail[:60]:
        if kind == "start":
            msg = "avviato"
            k = "info"
        else:
            ok = rc == 0
            msg = "completato" if ok else f"fallito (rc={rc})"
            k = "ok" if ok else "fail"
        log_tail.append({
            "t": ts.strftime("%H:%M:%S"), "job": DISPLAY_OVERRIDES.get(label, label),
            "kind": k, "msg": msg,
        })

    payload = {
        "generated_at": now.isoformat(),
        "summary": {
            "running_now": running_now,
            "running_count": len(running_now),
            "success_rate_24h": success_rate,
            "total_runs_24h": total_runs,
            "total_fails_24h": total_fails,
            "images_24h": images_last_24h(now),
            "s3_freed_today_gb": freed_gb,
            "s3_runs_today": s3_runs_today,
            "eumetsat_alerts_active": alert_active_count,
            "next_job": next_job,
        },
        "disk": {
            "root": disk_usage("/"),
            "sps_archive": disk_usage("/media/sps/SPS_archive"),
        },
        "groups": [
            {"key": g, "label": GROUP_LABEL[g], "jobs": groups[g]}
            for g in GROUP_ORDER
        ],
        "log_tail": log_tail,
        "eumetsat_alerts": {
            "active_count": alert_active_count,
            "items": alert_items,
        },
    }

    os.makedirs(OUT_DIR, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(dir=OUT_DIR, prefix=".status.", suffix=".json")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=1)
    os.replace(tmp_path, OUT_FILE)


if __name__ == "__main__":
    main()
