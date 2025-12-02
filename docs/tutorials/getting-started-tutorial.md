# Getting Started Tutorial

This tutorial will guide you through your first steps with SocData.

## Installation

First, install SocData:

```bash
pip install socdata
# Or for development:
pip install -e .
```

For Eurostat support:

```bash
pip install socdata[eurostat]
```

## Your First Dataset

### Loading Eurostat Data

Eurostat provides direct API access, so you can load data immediately:

```python
import socdata as sd

# Load unemployment data for Germany
df = sd.load("eurostat:une_rt_m", filters={"geo": "DE"})
print(df.head())
```

### Searching for Datasets

Find datasets using the search functionality:

```python
# Search all sources
results = sd.search("unemployment")
for ds in results:
    print(f"{ds.id}: {ds.title}")

# Search specific source
results = sd.search("population", source="eurostat")
```

### Ingesting Local Files

For datasets that require manual download (like WVS, ESS, etc.):

```python
# Ingest a downloaded file
df = sd.ingest("ess:ess-round-10", file_path="~/Downloads/ESS10e01_1.sav")

# Now you can load it from cache
df = sd.load("ess:ess-round-10")
```

## Working with Multiple Sources

SocData provides a unified interface across different data sources:

```python
# Eurostat (direct API)
df1 = sd.load("eurostat:une_rt_m", filters={"geo": "DE"})

# ESS (after ingestion)
df2 = sd.load("ess:ess-round-10", filters={"cntry": "DE"})

# GSS (after ingestion)
df3 = sd.load("gss:gss-cumulative", filters={"year": 2022})
```

## Using the CLI

The CLI provides the same functionality:

```bash
# List available datasets
socdata list

# Search
socdata search "unemployment"

# Load and export
socdata load-cmd eurostat:une_rt_m --filters 'geo=DE' --export data.parquet

# Ingest local file
socdata ingest-cmd ess:ess-round-10 ~/Downloads/ESS10.sav --export ess.parquet
```

## Next Steps

- Explore the [Adapters documentation](../adapters.md) for source-specific details
- Check out the [REST API](../api.md) for programmatic access
- Read about [Configuration](../configuration.md) for advanced settings
