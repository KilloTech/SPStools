#!/home/sps/miniconda3/envs/pytroll/bin/python3
# -*- coding: utf-8 -*-
# One-shot script: imposta/aggiorna la lifecycle rule sul bucket Cubbit S3.
# Esegui ogni volta che vuoi cambiare la retention (es. 15 → 30 giorni).
#
# Usage:
#   ./set_s3_lifecycle.py          # imposta/aggiorna regola
#   ./set_s3_lifecycle.py --show   # mostra regola attuale
#   ./set_s3_lifecycle.py --delete # rimuove la regola

import sys
import boto3
from botocore.config import Config
from botocore.exceptions import ClientError

# ── Credenziali da s3_credentials.py (mai sovrascritto dai deploy) ───────────
import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
try:
    from s3_credentials import S3_ENDPOINT_URL, S3_ACCESS_KEY, S3_SECRET_KEY, S3_BUCKET, S3_REGION
except ImportError:
    raise SystemExit('ERROR: s3_credentials.py not found — create it in the same directory as this script.')

# ── Retention: giorni dopo i quali i file vengono cancellati da Cubbit ────────
EXPIRATION_DAYS = 15   # cambia in 30 quando hai verificato che lo spazio regge

# ─────────────────────────────────────────────────────────────────────────────

client = boto3.client(
    's3',
    endpoint_url=S3_ENDPOINT_URL,
    aws_access_key_id=S3_ACCESS_KEY,
    aws_secret_access_key=S3_SECRET_KEY,
    config=Config(region_name=S3_REGION, s3={'addressing_style': 'path'}),
)

def show_rule():
    try:
        r = client.get_bucket_lifecycle_configuration(Bucket=S3_BUCKET)
        for rule in r.get('Rules', []):
            status = rule.get('Status', '?')
            exp    = rule.get('Expiration', {})
            days   = exp.get('Days', '—')
            date   = exp.get('Date', '—')
            print(f"  ID     : {rule.get('ID', '?')}")
            print(f"  Status : {status}")
            print(f"  Expires: {days} giorni  (o data: {date})")
    except ClientError as e:
        if e.response['Error']['Code'] in ('NoSuchLifecycleConfiguration', '404'):
            print('  Nessuna lifecycle rule configurata.')
        else:
            print(f'  Errore: {e}')

def set_rule():
    lifecycle = {
        'Rules': [
            {
                'ID': 'sps-expire-all',
                'Status': 'Enabled',
                'Prefix': '',          # old-style format: applica a tutti gli oggetti
                'Expiration': {
                    'Days': EXPIRATION_DAYS
                },
            }
        ]
    }
    try:
        client.put_bucket_lifecycle_configuration(
            Bucket=S3_BUCKET,
            LifecycleConfiguration=lifecycle,
        )
        print(f'OK: lifecycle rule impostata — tutti gli oggetti scadono dopo {EXPIRATION_DAYS} giorni.')
    except ClientError as e:
        print(f'Errore PUT lifecycle: {e}')
        sys.exit(1)

def delete_rule():
    try:
        client.delete_bucket_lifecycle(Bucket=S3_BUCKET)
        print('OK: lifecycle rule rimossa — nessuna scadenza automatica.')
    except ClientError as e:
        print(f'Errore DELETE lifecycle: {e}')
        sys.exit(1)

# ── main ──────────────────────────────────────────────────────────────────────
if '--show' in sys.argv:
    print(f'=== Lifecycle rule attuale su s3://{S3_BUCKET} ===')
    show_rule()
elif '--delete' in sys.argv:
    print(f'=== Rimozione lifecycle rule da s3://{S3_BUCKET} ===')
    delete_rule()
else:
    print(f'=== Impostazione lifecycle rule su s3://{S3_BUCKET} ===')
    print(f'    Retention: {EXPIRATION_DAYS} giorni')
    set_rule()
    print()
    print('=== Verifica ===')
    show_rule()
