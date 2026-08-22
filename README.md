# SPStools — SPS Satellite Processing System

Satellite imagery acquisition and processing system based on **PyTROLL/SatPy** (v0.60.0), adapted from Ernst Lobsiger's SPStools (GPL3) for an **INGV-style EUMETCast** setup on Debian 13.

## System overview

| Component | Description |
|-----------|-------------|
| **Server** | Debian 13, IP 192.168.1.204 |
| **Python env** | `/home/sps/miniconda3/envs/pytroll/` — SatPy 0.60.0 |
| **SPStools path** | `/home/sps/SPStools/` |
| **SPSdata path** | `/home/sps/SPSdata/` (products, overlays, tmpdirs) |
| **Live data** | `/home/sps/received/` (EUMETCast receiver mount) |

## EUMETCast channels active

| Channel | Path | Satellite / Product |
|---------|------|---------------------|
| `bas/E1B-GEO-3` | MSG3 + MSG4 (Meteosat FES) HRIT |
| `bas/E1B-GEO-4` | MSG3 + MSG4 NWC-SAF products |
| `bas/E1B-EPS-10` | Metop-B/C AVHRR L1b |
| `bas/E1B-DWDSAT` | DWD MSLP charts + SYNOP/TEMP BUFR |
| `hvs-1/E1H-RDS-1` | NOAA-20 + SNPP VIIRS Compact |
| `hvs-1/E1H-RDS-2` | FY-3D MERSI-2 |
| `hvs-1/E1H-TPG-1` | GOES-19 ABI L1b |
| `hvs-1/E1H-TPG-4` | GOES-18 ABI L1b |
| `hvs-1/E1H-TPG-2` | Himawari-8 AHI |
| `hvs-2/E2H-S3A-02` | Sentinel-3A OLCI L1b ERR |
| `hvs-2/E2H-S3A-04` | Sentinel-3A SLSTR L2 WST |
| `hvs-2/E2H-S3B-02` | Sentinel-3B OLCI L1b ERR |
| `hvs-2/E2H-S3B-04` | Sentinel-3B SLSTR L2 WST |
| `hvs-2/E2H-MTG-1` | MTG FCI (MTI1 / Meteosat Third Generation) |

## Directory structure

```
SPStools/
├── GEOscripts/        # Geostationary satellite processing scripts
│   ├── GEOstuff.py    # Core GEO module (readers, compositing, save)
│   ├── MSG3-*.py      # Meteosat-10 FES scripts
│   ├── MSG4-*.py      # Meteosat-11 FES + MSLP overlay scripts
│   ├── GOES18-*.py    # GOES-18 West scripts
│   ├── GOES19-*.py    # GOES-19 East scripts
│   ├── HIMA8-*.py     # Himawari-8 scripts
│   └── MTI1-*.py      # MTG FCI scripts
├── LEOscripts/        # Low Earth orbit satellite scripts
│   ├── LEOstuff.py    # Core LEO module
│   ├── NOAA20-*.py    # NOAA-20 VIIRS
│   ├── SNPP-*.py      # Suomi-NPP VIIRS
│   ├── MetopB-*.py    # Metop-B AVHRR
│   ├── MetopC-*.py    # Metop-C AVHRR
│   ├── FY3D-*.py      # FY-3D MERSI-2
│   ├── Sen3A-*.py     # Sentinel-3A OLCI + SLSTR
│   └── Sen3B-*.py     # Sentinel-3B OLCI + SLSTR
├── cron/              # Cron job wrappers (called from crontab)
│   ├── run_*.py       # Python wrappers for LEO/GEO scripts
│   └── run_geo_movies*.sh  # FFmpeg timelapse generation
├── cmdfiles/          # System-level utilities
│   ├── tidy.sh        # Local disk cleanup (GEOtrim + product pruning)
│   ├── GEO-mov.sh     # FFmpeg .webm timelapse builder
│   ├── s3_archive.py  # Upload old products to S3 (Cubbit), then delete locally
│   ├── DWDSAT-overlays.py  # DWD MSLP chart overlays from E1B-DWDSAT
│   ├── DWD-overlays.sh     # DWD OpenData MSLP overlays
│   ├── UKMO-overlays.sh    # UKMO MSLP overlays
│   ├── OPC-overlays.sh     # NOAA OPC MSLP overlays
│   └── Update_TLE_file.py  # Weekly TLE update
├── userconfig/        # SatPy configuration overrides
│   ├── areas.yaml     # Custom projection areas (eurol, opcaw, etc.)
│   ├── platforms.txt  # Platform aliases
│   └── composites/    # Custom composite recipes (OLCI, etc.)
├── DEVscripts/        # Development / experimental scripts
├── timeliness/        # EUMETCast timeliness histograms (GNUplot)
├── exefiles/          # Windows binaries (convert, ffmpeg, wget — Linux not needed)
└── documents/         # HOWTOs and documentation
```

## S3 archive

Products older than a configurable threshold are uploaded to **Cubbit S3** (`sps-satellite-archive` bucket) and deleted locally:

- GEO frames: after 25 h (archived after daily movie generation)
- GEO movies (.webm): after 7 days
- LEO imagery (all satellites): after 14 days
- MSLP charts: after 14 days

S3 lifecycle rule on the bucket expires all objects after **15 days**.

Credentials go in `cmdfiles/s3_credentials.py` (not tracked by git):
```python
S3_ENDPOINT_URL = 'https://s3.cubbit.eu'
S3_ACCESS_KEY   = '...'
S3_SECRET_KEY   = '...'
S3_BUCKET       = 'sps-satellite-archive'
S3_REGION       = 'auto'
```

## License

Original SPStools by Ernst Lobsiger, CH-3123 Belp — GPL3.  
INGV adaptation and extensions by KilloTech, 2026.
