# socdata

Einheitlicher Zugriff auf sozialwissenschaftliche Datensätze.

## Installation (Entwicklung)

```bash
pip install -e .
# Optional für Eurostat
pip install -e .[eurostat]
```

## CLI nutzen

```bash
socdata version
socdata show-config
socdata list --source eurostat
socdata search "unemployment"
# Laden eines Eurostat-Datensatzes
socdata load-cmd eurostat:une_rt_m --filters '{"geo": "DE", "sex": "T", "age": "Y15-74"}' --export out.parquet
# Manuelle Ingestion (z.B. WVS):
socdata ingest-cmd manual ~/Downloads/WVS_Extract.dta --export wvs.parquet
```

## Python API

```python
import socdata as sd

df = sd.load("eurostat:une_rt_m", filters={"geo": "DE"})
```

## Lizenz

MIT