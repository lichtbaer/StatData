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
# After downloading and extracting the archive, pass the main data file
socdata ingest-cmd manual ~/path/to/WVS_Extract.dta --export wvs.parquet
```

Planned adapters/recipes:
- SOEP (ODF) – direct loading from ODF zip via dedicated package
- GSS – scripted automation
- ESS, ICPSR, ISSP, CSES, EVS – manual ingest with per-study recipes