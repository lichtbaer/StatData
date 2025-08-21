# CLI reference

The CLI entry point is `socdata`.

## Commands

- `version`: Print version
- `show-config`: Print current configuration
- `list [--source NAME]`: List known datasets per adapter
- `search QUERY`: Local search in known descriptors
- `load-cmd DATASET [--filters ...] [--export PATH]`: Load a dataset via adapter
- `ingest-cmd ADAPTER FILE [--export PATH]`: Ingest a local file using adapter recipe

## Examples

```bash
# Version and config
socdata version
socdata show-config

# Discovery
socdata list
socdata list --source eurostat
socdata search "population"

# Load Eurostat dataset
socdata load-cmd eurostat:demo_r_pjangroup --filters 'geo=DE' --export demo.parquet

# Manual ingest (e.g., WVS extracted file)
socdata ingest-cmd manual ~/Downloads/WVS_Extract.dta --export wvs.parquet
```

## Filters format

- JSON string: `'{"geo": "DE", "sex": "T"}'`
- Simple pairs: `'geo=DE,sex=T'`