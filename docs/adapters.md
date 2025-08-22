# Adapters

## Eurostat (direct)

- Source: official Eurostat API via the `eurostat` Python package
- Status: implemented (search + load)

Example:

```python
import socdata as sd

# Minimal filter
df = sd.load("eurostat:une_rt_m", filters={"geo": "DE"})
```

CLI:

```bash
socdata load-cmd eurostat:une_rt_m --filters 'geo=DE'
```

Notes:
- Certain dimension combinations are invalid. Start with a minimal filter (e.g., `geo`).

## Manual (recipes)

- Purpose: ingest from locally downloaded files when no API/package exists
- Example target: WVS (World Values Survey)

Usage:

```bash
# Either pass the downloaded ZIP directly (auto-extracts and picks the main file)
socdata ingest-cmd manual:wvs ~/Downloads/WVS_Cross-National_Wave7.zip --export wvs.parquet

# Or pass an extracted data file directly
socdata ingest-cmd manual:wvs ~/path/to/WVS_Extract.dta --export wvs.parquet
```

Artifacts written to cache:
- Normalized Parquet with Arrow metadata (variable/value labels, provenance): `~/.socdata/manual/manual_wvs/latest/processed/data.parquet`
- Manifest JSON: `~/.socdata/manual/manual_wvs/latest/meta/ingestion_manifest.json`

Planned adapters/recipes:
- SOEP (ODF) – direct loading from ODF zip via dedicated package
- GSS – scripted automation
- ESS, ICPSR, ISSP, CSES, EVS – manual ingest with per-study recipes