# REST API

SocData provides a REST API for programmatic access to datasets. The API is built with FastAPI and provides OpenAPI documentation.

## Installation

Install the API dependencies:

```bash
pip install socdata[api]
```

## Starting the Server

### CLI

```bash
socdata serve
# Or with custom host/port
socdata serve --host 0.0.0.0 --port 8080
# Or with auto-reload for development
socdata serve --reload
```

### Python

```python
from socdata.server import app
import uvicorn

uvicorn.run(app, host="0.0.0.0", port=8000)
```

## API Endpoints

### Root

- `GET /` - API information and available endpoints

### Datasets

- `GET /datasets` - List all available datasets
  - Query params: `source` (optional) - filter by source
- `GET /datasets/{dataset_id}/info` - Get detailed information about a dataset
- `POST /datasets/{dataset_id}/load` - Load a dataset with optional filters
  - Body: `LoadRequest` with `filters` (optional) and `format` (json/csv/parquet)
  - Query params: `filters` (JSON string, optional), `format` (json/csv/parquet)

### Search

- `GET /search` - Search datasets
  - Query params:
    - `q` (required) - search query
    - `source` (optional) - filter by source
    - `variable` (optional) - search for datasets containing this variable
    - `limit` (optional, default: 100) - maximum results

### Ingestion

- `POST /ingest` - Ingest a dataset from a local file
  - Body: `IngestRequest` with `dataset_id`, `file_path`, and `format`

### Index

- `POST /rebuild-index` - Rebuild the search index

## Examples

### List datasets

```bash
curl http://localhost:8000/datasets
```

### Search datasets

```bash
curl "http://localhost:8000/search?q=unemployment"
```

### Get dataset info

```bash
curl http://localhost:8000/datasets/eurostat:une_rt_m/info
```

### Load dataset (JSON)

```bash
curl -X POST "http://localhost:8000/datasets/eurostat:une_rt_m/load?filters=%7B%22geo%22%3A%22DE%22%7D"
```

### Load dataset (CSV)

```bash
curl -X POST "http://localhost:8000/datasets/eurostat:une_rt_m/load?format=csv&filters=%7B%22geo%22%3A%22DE%22%7D" \
  -o output.csv
```

### Load dataset (Parquet)

```bash
curl -X POST "http://localhost:8000/datasets/eurostat:une_rt_m/load?format=parquet&filters=%7B%22geo%22%3A%22DE%22%7D" \
  -o output.parquet
```

### Ingest dataset

```bash
curl -X POST http://localhost:8000/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "dataset_id": "ess:ess-round-10",
    "file_path": "/path/to/ESS10e01_1.sav",
    "format": "json"
  }'
```

## OpenAPI Documentation

When the server is running, visit:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- OpenAPI JSON: http://localhost:8000/openapi.json

## Response Formats

### JSON (default)

Returns dataset metadata and first 100 rows:

```json
{
  "dataset_id": "eurostat:une_rt_m",
  "filters": {"geo": "DE"},
  "rows": 1234,
  "columns": ["geo", "time", "values"],
  "data": [...]
}
```

### CSV

Returns the full dataset as CSV with appropriate headers.

### Parquet

Returns the full dataset as Parquet binary format.
