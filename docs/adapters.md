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

## SOEP (ODF)

- Source: SOEP (Socio-Economic Panel) Open Data Format
- Status: implemented (ingest from ODF ZIP files)

SOEP ODF files are ZIP archives containing data files and documentation. The adapter automatically extracts and processes the main data file.

Usage:

```bash
# Ingest from local ODF ZIP file
socdata ingest-cmd soep:soep-core ~/Downloads/soep_core.zip --export soep.parquet
```

Python:

```python
import socdata as sd

# Ingest from local file
df = sd.ingest("soep:soep-core", file_path="~/Downloads/soep_core.zip")

# Load from cache (after ingestion)
df = sd.load("soep:soep-core")
```

Notes:
- SOEP data requires registration and data use agreement
- ODF ZIP files are automatically extracted
- The adapter prefers Stata/SPSS formats over CSV when multiple files are present
- Original ZIP is cached in `raw/` directory

## GSS (scripted)

- Source: General Social Survey (NORC at University of Chicago)
- Status: implemented (ingest from local files)

GSS data is available after registration. This adapter supports ingestion from downloaded GSS data files.

Usage:

```bash
# Ingest from local GSS data file
socdata ingest-cmd gss:gss-2022 ~/Downloads/GSS2022.dta --export gss.parquet
```

Python:

```python
import socdata as sd

# Ingest from local file
df = sd.ingest("gss:gss-2022", file_path="~/Downloads/GSS2022.dta")

# Load from cache with filters
df = sd.load("gss:gss-cumulative", filters={"year": 2022})
```

Notes:
- GSS data requires registration at https://gss.norc.org
- Supports Stata (.dta), SPSS (.sav), and CSV formats
- Version detection from filename (e.g., GSS2022.dta → gss-2022)
- Filters can be applied when loading from cache

Planned adapters/recipes:
- ESS, ICPSR, ISSP, CSES, EVS – manual ingest with per-study recipes