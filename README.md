# socdata

Einheitlicher Zugriff auf sozialwissenschaftliche Datensätze.

## Installation (Entwicklung)

```bash
pip install -e .
# Optional für Eurostat
pip install -e .[eurostat]
# Optional für REST API
pip install -e .[api]
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

## REST API

Start the API server:

```bash
socdata serve
# Or: python -m socdata.server
```

Access the interactive API documentation at http://localhost:8000/docs

```bash
# List datasets
curl http://localhost:8000/datasets

# Search
curl "http://localhost:8000/search?q=unemployment"

# Load dataset
curl -X POST "http://localhost:8000/datasets/eurostat:une_rt_m/load?filters=%7B%22geo%22%3A%22DE%22%7D"
```

## Lizenz

MIT