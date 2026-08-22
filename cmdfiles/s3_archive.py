#!/home/sps/miniconda3/envs/pytroll/bin/python3
# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------------------
# S3 Archive Script — upload old products to S3-compatible storage, then delete
# locally. Designed for the SPS satellite processing system on Debian 13.
#
# Compatible with: AWS S3, Cubbit, MinIO, Wasabi, Backblaze B2, Cloudflare R2.
#
# Recommended cron schedule: 45 0 * * *  (00:45 UTC)
#   Runs AFTER daily movie generation (00:10 UTC) and BEFORE tidy.sh (01:00 UTC).
#   This ensures yesterday's frames are archived only after movies are produced.
#
# Usage:
#   python3 s3_archive.py            # normal run
#   python3 s3_archive.py --dry-run  # simulate only, no uploads/deletes
#   python3 s3_archive.py --verbose  # extra per-file logging
#
# CH-3123 Belp / INGV adaptation, 2026     License GPL3     (c) Ernst Lobsiger
# ---------------------------------------------------------------------------------

import os
import sys
import glob
import time
import logging
import argparse
import hashlib
import boto3
from boto3.s3.transfer import TransferConfig
from botocore.config import Config
from botocore.exceptions import ClientError
from datetime import datetime, timezone

# ══════════════════════════════════════════════════════════════════════════════
# ★  CONFIGURE HERE — adapt to your personal needs  ★
# ══════════════════════════════════════════════════════════════════════════════

# ── S3 endpoint & credentials ─────────────────────────────────────────────────
# Loaded from s3_credentials.py (never overwritten by deployments)
import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
try:
    from s3_credentials import S3_ENDPOINT_URL, S3_ACCESS_KEY, S3_SECRET_KEY, S3_BUCKET, S3_REGION
except ImportError:
    raise SystemExit('ERROR: s3_credentials.py not found — create it in the same directory as this script.')

# ── Local paths ───────────────────────────────────────────────────────────────
PRODUCTS_DIR        = '/home/sps/SPSdata/products'
LOG_FILE            = '/home/sps/SPSdata/s3_archive.log'

# ── S3 key prefix (folder inside the bucket) ─────────────────────────────────
S3_PREFIX           = 'SPSdata/products'       # e.g. s3://bucket/SPSdata/products/HIMA8/frames/…

# ── Archive rules ─────────────────────────────────────────────────────────────
# Each rule: (subdir_glob, pattern, min_age_hours, description)
#   subdir_glob  : glob relative to PRODUCTS_DIR, e.g. '*/frames' or 'HIMA8/frames'
#   pattern      : filename pattern to match
#   min_age_hours: archive files older than this many hours
#   description  : label for logs
#
# Timing note for frames (GEO satellites):
#   Movies run at 00:10 UTC using previous day's frames.
#   This script runs at 00:45 UTC.
#   min_age_hours=25 ensures yesterday's frames are archived only after movies.

ARCHIVE_RULES = [
    # ── GEO satellite frames (HIMA8, MTI1, MSG3, MSG4, …) ──────────────────
    # Archive frames older than 25h — safely after daily movie generation.
    ('*/frames',  '*.jpg',  25,  'GEO frames'),

    # ── GOES-19 and GOES-18 frames — archive after 25h ────────────────────────
    ('GOES19/frames', '*.jpg', 25, 'GOES-19 frames'),
    ('GOES18/frames', '*.jpg', 25, 'GOES-18 frames'),

    # ── GEO movies (.webm) — archive after 7 days ───────────────────────────
    ('*/movies',  '*.webm',  7 * 24,  'GEO movies'),

    # ── LEO satellite images — archive after 14 days ────────────────────────
    ('NOAA20/*',  '*.jpg',  14 * 24, 'NOAA-20 images'),
    ('SNPP/*',    '*.jpg',  14 * 24, 'SNPP images'),
    ('MetopB/*',  '*.jpg',  14 * 24, 'MetopB images'),
    ('MetopC/*',  '*.jpg',  14 * 24, 'MetopC images'),
    ('FY3D/*',    '*.jpg',  14 * 24, 'FY-3D images'),
    ('Sen3A/*',   '*.png',  14 * 24, 'Sen3A SLSTR'),
    ('Sen3A/OLCI', '*.jpg',  14 * 24, 'Sen3A OLCI'),
    ('Sen3B/OLCI', '*.jpg',  14 * 24, 'Sen3B OLCI'),
    ('Sen3B/*',   '*.png',  14 * 24, 'Sen3B SLSTR'),

    # ── MSG3 NWC-SAF cloud products — archive after 14 days ────────────────────
    ('MSG3', '*cloud*.jpg',  14 * 24, 'MSG3 NWC-SAF'),

    # ── MSLP pressure charts — archive after 14 days ────────────────────────
    ('MSLP/*/*',  '*.jpg',  14 * 24, 'MSLP charts'),
]

# ── Upload settings ───────────────────────────────────────────────────────────
UPLOAD_STORAGE_CLASS = ''           # leave empty for Cubbit (no STANDARD_IA/GLACIER support)
MAX_RETRIES          = 3            # retries on upload failure
RETRY_DELAY_S        = 5            # seconds between retries
MULTIPART_THRESHOLD  = 64 * 1024 * 1024   # 64 MB — use multipart above this
MULTIPART_CHUNKSIZE  = 16 * 1024 * 1024   # 16 MB chunks

# ── Verification ─────────────────────────────────────────────────────────────
VERIFY_UPLOAD = False  # HeadObject post-upload disabled: adds ~30s latency per file on Cubbit
                       # boto3 already guarantees integrity via TCP checksum + retry logic
LOG_PROGRESS_EVERY = 50  # log a progress line every N files (0 = disable)

# ══════════════════════════════════════════════════════════════════════════════
# ✱  Do not touch the code below unless you know what you do  ✱
# ══════════════════════════════════════════════════════════════════════════════

def setup_logging(verbose: bool) -> logging.Logger:
    log = logging.getLogger('s3_archive')
    log.setLevel(logging.DEBUG if verbose else logging.INFO)
    fmt = logging.Formatter('%(asctime)s %(levelname)-7s %(message)s',
                            datefmt='%Y-%m-%d %H:%M:%S')
    # Guard against duplicate handlers if module is somehow reloaded
    if not log.handlers:
        fh = logging.FileHandler(LOG_FILE)
        fh.setFormatter(fmt)
        ch = logging.StreamHandler(sys.stdout)
        ch.setFormatter(fmt)
        log.addHandler(fh)
        log.addHandler(ch)
    return log


def build_s3_client():
    """Build and return a boto3 S3 client for the configured endpoint."""
    botocore_cfg = Config(
        region_name=S3_REGION,
        retries={'max_attempts': MAX_RETRIES, 'mode': 'standard'},
        s3={'addressing_style': 'path'},   # path-style required by most S3-compatible providers
        read_timeout=300,    # 5 min — Cubbit can be slow on large files at low bandwidth
        connect_timeout=30,
    )
    return boto3.client(
        's3',
        endpoint_url=S3_ENDPOINT_URL,
        aws_access_key_id=S3_ACCESS_KEY,
        aws_secret_access_key=S3_SECRET_KEY,
        config=botocore_cfg,
    )


# TransferConfig for multipart uploads (module-level, reused for all uploads)
_transfer_cfg = TransferConfig(
    multipart_threshold=MULTIPART_THRESHOLD,
    multipart_chunksize=MULTIPART_CHUNKSIZE,
)


def verify_bucket(client, log):
    """Check credentials by uploading a tiny sentinel object, then deleting it.
    HeadBucket and ListObjects may be denied on some S3-compatible providers (e.g. Cubbit)."""
    sentinel_key = f'{S3_PREFIX}/.s3_archive_test'
    try:
        client.put_object(Bucket=S3_BUCKET, Key=sentinel_key, Body=b's3_archive_ok')
        client.delete_object(Bucket=S3_BUCKET, Key=sentinel_key)
        log.info(f'Bucket reachable: s3://{S3_BUCKET}  endpoint={S3_ENDPOINT_URL}')
        return True
    except ClientError as e:
        code = e.response['Error']['Code']
        log.error(f'Bucket check failed ({code}): {e}')
        return False
    except Exception as e:
        log.error(f'Bucket check error: {e}')
        return False


def s3_key_for(local_path: str) -> str:
    """Compute the S3 key for a local file path."""
    rel = os.path.relpath(local_path, PRODUCTS_DIR)
    return f'{S3_PREFIX.rstrip("/")}/{rel.replace(os.sep, "/")}'


def upload_file(client, local_path: str, s3_key: str, log,
                dry_run: bool, verbose: bool) -> bool:
    """
    Upload local_path to S3 at s3_key.
    Returns True on success (or simulated success in dry-run mode).
    No HeadObject calls — boto3 guarantees integrity via TCP/TLS + retry.
    If interrupted and re-run, S3 silently overwrites the existing object (idempotent).
    """
    local_size = os.path.getsize(local_path)

    if verbose:
        log.debug(f'  → s3://{S3_BUCKET}/{s3_key}  ({local_size/1024/1024:.1f} MB)')

    if dry_run:
        return True

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            extra = {'StorageClass': UPLOAD_STORAGE_CLASS} if UPLOAD_STORAGE_CLASS else {}
            client.upload_file(
                local_path,
                S3_BUCKET,
                s3_key,
                ExtraArgs=extra if extra else None,
                Config=_transfer_cfg,
            )
            return True
        except FileNotFoundError:
            raise   # let caller handle missing files — no point retrying
        except Exception as e:
            # Catches ClientError, ReadTimeoutError, EndpointConnectionError, etc.
            log.warning(f'  Upload attempt {attempt}/{MAX_RETRIES} failed: {e}')
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY_S)
    return False


def collect_files(subdir_glob: str, pattern: str, min_age_hours: float) -> list:
    """Return a sorted list of files matching pattern, older than min_age_hours."""
    now = time.time()
    cutoff = now - min_age_hours * 3600
    results = []
    search = os.path.join(PRODUCTS_DIR, subdir_glob, pattern)
    for path in sorted(glob.glob(search)):
        if os.path.isfile(path) and os.path.getmtime(path) < cutoff:
            results.append(path)
    return results


def archive_rule(client, rule, log, dry_run: bool, verbose: bool,
                 stats: dict) -> None:
    subdir_glob, pattern, min_age_hours, description = rule
    files = collect_files(subdir_glob, pattern, min_age_hours)

    if not files:
        if verbose:
            log.debug(f'[{description}] no files older than {min_age_hours:.0f}h')
        return

    total = len(files)
    log.info(f'[{description}] {total} file(s) older than {min_age_hours:.0f}h')

    for i, local_path in enumerate(files, 1):
        s3_key = s3_key_for(local_path)
        fname  = os.path.basename(local_path)

        # File may have been deleted by tidy.sh between collect_files() and here
        try:
            fsize = os.path.getsize(local_path)
        except FileNotFoundError:
            if verbose:
                log.debug(f'  SKIP (deleted before upload): {fname}')
            stats['skipped'] = stats.get('skipped', 0) + 1
            continue

        # Upload — no pre-check HeadObject (too slow on Cubbit ~30s/call)
        # Re-runs are safe: S3 silently overwrites existing objects (idempotent)
        try:
            ok = upload_file(client, local_path, s3_key, log, dry_run, verbose)
        except FileNotFoundError:
            log.warning(f'  SKIP (deleted mid-upload): {fname}')
            stats['skipped'] = stats.get('skipped', 0) + 1
            continue

        if ok:
            if not dry_run:
                try:
                    os.remove(local_path)
                except FileNotFoundError:
                    pass  # already gone, not a problem
            stats['uploaded'] += 1
            stats['bytes_freed'] += fsize
            if verbose:
                log.debug(f'  OK: {fname}')
            # Progress log every N files
            if LOG_PROGRESS_EVERY and stats['uploaded'] % LOG_PROGRESS_EVERY == 0:
                gb = stats['bytes_freed'] / 1024 / 1024 / 1024
                log.info(f'[{description}] progress: {stats["uploaded"]}/{total}  freed={gb:.2f} GB')
        else:
            log.error(f'  FAILED: {fname} — keeping local copy')
            stats['errors'] += 1


def main():
    parser = argparse.ArgumentParser(
        description='Archive old SPS products to S3-compatible storage.')
    parser.add_argument('--dry-run', action='store_true',
                        help='Simulate only — no uploads or deletes')
    parser.add_argument('--verbose', action='store_true',
                        help='Log every file processed')
    args = parser.parse_args()

    log = setup_logging(args.verbose)

    # Lock file — prevent multiple simultaneous instances (atomic O_CREAT|O_EXCL)
    LOCK_FILE = '/tmp/s3_archive.lock'
    lock_fd = None
    if not args.dry_run:
        try:
            lock_fd = os.open(LOCK_FILE, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.write(lock_fd, str(os.getpid()).encode())
        except FileExistsError:
            pid = open(LOCK_FILE).read().strip()
            log.warning(f'Already running (lock={LOCK_FILE}, pid={pid}) — exiting.')
            sys.exit(0)
        import atexit
        atexit.register(lambda: (os.close(lock_fd), os.remove(LOCK_FILE))
                        if os.path.exists(LOCK_FILE) else None)

    run_label = '[DRY-RUN] ' if args.dry_run else ''
    log.info(f'=== s3_archive {run_label}start  endpoint={S3_ENDPOINT_URL} ===')

    # Build S3 client and verify connectivity
    try:
        client = build_s3_client()
    except Exception as e:
        log.error(f'Failed to build S3 client: {e}')
        sys.exit(1)

    if not args.dry_run:
        if not verify_bucket(client, log):
            sys.exit(1)
    else:
        log.info('[DRY-RUN] skipping bucket verification')

    stats = {
        'uploaded':    0,
        'skipped':     0,
        'errors':      0,
        'bytes_freed': 0,
    }

    t0 = time.time()
    for rule in ARCHIVE_RULES:
        try:
            archive_rule(client, rule, log, args.dry_run, args.verbose, stats)
        except Exception as e:
            log.error(f'Unexpected error in rule {rule[3]}: {e}')
            stats['errors'] += 1

    elapsed = time.time() - t0
    mb_freed = stats['bytes_freed'] / 1024 / 1024
    gb_freed = mb_freed / 1024

    log.info(
        f'=== s3_archive {run_label}done  '
        f"uploaded={stats['uploaded']}  "
        f"skipped={stats['skipped']}  "
        f"errors={stats['errors']}  "
        f"freed={gb_freed:.2f} GB  "
        f'elapsed={elapsed:.1f}s ==='
    )

    if stats['errors'] > 0:
        sys.exit(1)


if __name__ == '__main__':
    main()
