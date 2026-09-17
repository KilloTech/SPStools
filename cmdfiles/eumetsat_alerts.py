#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------------------
# Archivia i Service Alert EUMETSAT (E-UNS_Alert_Message_*.xml) ricevuti via
# EUMETCast sul canale E1B-Info-Channel-2 in uno storico persistente. I file XML
# nella directory ricevuta vengono ripuliti dalla retention del sistema dopo poco
# tempo; questo script li legge prima che spariscano e mantiene una copia con
# uno storico di 7 giorni, deduplicando per numero di annuncio (ogni revisione
# successiva - es. da "ongoing" a "recovered" - aggiorna lo stesso record).
#
# CH-3123 Belp (pattern originale)              License GPL3           (c) Ernst Lobsiger
# ---------------------------------------------------------------------------------

import json
import os
import tempfile
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from glob import glob

segdir = '/home/sps/received/bas/E1B-Info-Channel-2'
store_path = '/home/sps/SPSdata/eumetsat_alerts.json'
RETENTION_DAYS = 7


def load_store():
    if os.path.exists(store_path):
        try:
            with open(store_path) as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            pass
    return {}


def save_store(store):
    fd, tmp_path = tempfile.mkstemp(dir=os.path.dirname(store_path))
    try:
        with os.fdopen(fd, 'w') as f:
            json.dump(store, f, indent=1, sort_keys=True)
        os.replace(tmp_path, store_path)
    except Exception:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        raise


def parse_alert_file(path):
    tree = ET.parse(path)
    root = tree.getroot()
    issued_on = root.get('issued-on', '')
    records = []
    for ann in root.iter('announcement'):
        ann_number = ann.get('ann-number', '')
        if not ann_number:
            continue
        satellites = [s.text for s in ann.iter('satellite') if s.text]
        services = [pg.get('name', '') for pg in ann.iter('product-group')]
        detail_el = ann.find('detail')
        records.append({
            'ann_number': ann_number,
            'ann_revision': int(ann.get('ann-revision', 0)),
            'ann_type': ann.get('ann-type', ''),
            'subject': ann.get('ann-subject', ''),
            'impact': ann.get('impact', ''),
            'status': ann.get('status', ''),
            'start_time': ann.get('start-time', ''),
            'end_time': ann.get('end-time', ''),
            'satellites': satellites,
            'services': services,
            'detail': (detail_el.text or '').strip() if detail_el is not None else '',
            'last_update': issued_on,
        })
    return records


def main():
    store = load_store()

    files = sorted(glob(os.path.join(segdir, 'E-UNS_Alert_Message_*.xml')))
    new_count = 0
    updated_count = 0
    for path in files:
        try:
            records = parse_alert_file(path)
        except ET.ParseError:
            continue
        for rec in records:
            key = rec['ann_number']
            existing = store.get(key)
            if existing is None:
                store[key] = rec
                new_count += 1
            elif rec['ann_revision'] >= existing.get('ann_revision', -1):
                store[key] = rec
                updated_count += 1

    # 7-day rolling retention, based on start_time (fall back to last_update)
    cutoff = datetime.now(timezone.utc) - timedelta(days=RETENTION_DAYS)
    pruned = 0
    for key in list(store.keys()):
        rec = store[key]
        ts_str = rec.get('start_time') or rec.get('last_update')
        try:
            ts = datetime.fromisoformat(ts_str)
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=timezone.utc)
        except (ValueError, TypeError):
            continue
        if ts < cutoff:
            del store[key]
            pruned += 1

    save_store(store)
    print(f'file_letti={len(files)} nuovi={new_count} aggiornati={updated_count} '
          f'rimossi_scaduti={pruned} totale_storico={len(store)}')


if __name__ == '__main__':
    main()
