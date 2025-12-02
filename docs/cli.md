# CLI reference

The CLI entry point is `socdata`.

## Commands

- `version`: Print version
- `show-config`: Print current configuration
- `list [--source NAME]`: List known datasets per adapter
- `search QUERY [--source NAME] [--variable NAME] [--no-index]`: Full-text search with optional filters
- `info DATASET`: Show detailed information about a dataset
- `rebuild-index`: Rebuild the search index from all available datasets
- `load-cmd DATASET [--filters ...] [--export PATH]`: Load a dataset via adapter
- `ingest-cmd ADAPTER FILE [--export PATH]`: Ingest a local file using adapter recipe
- `serve [--host HOST] [--port PORT] [--reload]`: Start the REST API server

## Examples

```bash
# Version and config
socdata version
socdata show-config

# Discovery
socdata list
socdata list --source eurostat
socdata search "population"
socdata search "unemployment" --source eurostat
socdata search "income" --variable income
socdata info eurostat:une_rt_m
socdata rebuild-index

# Load Eurostat dataset
socdata load-cmd eurostat:demo_r_pjangroup --filters 'geo=DE' --export demo.parquet

# Manual ingest (e.g., WVS extracted file)
socdata ingest-cmd manual ~/Downloads/WVS_Extract.dta --export wvs.parquet

# Start REST API server
socdata serve
socdata serve --host 0.0.0.0 --port 8080
socdata serve --reload  # Auto-reload for development
```

## Filters format

- JSON string: `'{"geo": "DE", "sex": "T"}'`
- Simple pairs: `'geo=DE,sex=T'`