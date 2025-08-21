# Architecture

SocData is organized in layers:

- Core:
  - `config`: global configuration and cache directory
  - `storage`: cache path helpers per source/dataset/version
  - `download`: resilient HTTP downloads with retry and checksum
  - `parsers`: loaders for CSV/TSV, Stata (.dta), SPSS (.sav/.zsav)
  - `models` and `types`: typed descriptors and manifests
- Adapters:
  - `sources.eurostat`: API-backed loading
  - `sources.manual`: local file ingestion recipes (e.g., WVS)
- API/CLI:
  - `api.load(dataset_id, filters=...)`
  - `api.ingest(adapter_id, file_path=...)`
  - Typer-based CLI wrapping the same functionality

## Dataset identifiers

- Format: `source:code`, e.g. `eurostat:une_rt_m`
- Manual adapters accept adapter IDs, e.g. `manual` for ingestion

## Caching layout

`~/.socdata/{source}/{dataset}/{version}/(raw|processed|meta)`

## Extending with new adapters

- Implement `BaseAdapter` with `list_datasets`, `load`, and optional `ingest`
- Register it in `core.registry._ADAPTERS`