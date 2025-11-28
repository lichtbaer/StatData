# Search Index

SocData includes a local search index for fast full-text search over dataset metadata, variable labels, and value labels.

## Features

- **Full-text search** using SQLite FTS5 (with fallback to LIKE queries)
- **Variable-level search** - Find datasets by variable names
- **Source filtering** - Filter results by data source
- **Automatic indexing** - Datasets are automatically indexed after ingestion
- **Metadata storage** - Variable labels, value labels, and license information

## Usage

### CLI

```bash
# Basic search
socdata search "unemployment"

# Search with source filter
socdata search "income" --source gss

# Search by variable name
socdata search "age" --variable age

# Show dataset details
socdata info gss:gss-cumulative

# Rebuild index (if needed)
socdata rebuild-index
```

### Python API

```python
import socdata as sd
from socdata.core.registry import search_datasets, search_datasets_advanced
from socdata.core.search_index import get_index

# Basic search (uses index automatically)
results = search_datasets("unemployment", source="eurostat")

# Advanced search
results = search_datasets_advanced(
    query="income",
    source="gss",
    variable_name="income"
)

# Get detailed dataset information
index = get_index()
info = index.get_dataset_info("gss:gss-cumulative")
print(info["variable_labels"])
```

## Index Location

The search index is stored at:
```
~/.socdata/search_index.db
```

## How It Works

1. **Automatic Indexing**: When you ingest a dataset, its metadata (title, variable labels, value labels) is automatically added to the index.

2. **Full-Text Search**: The index uses SQLite FTS5 for fast full-text search. If FTS5 is not available, it falls back to simple LIKE queries.

3. **Variable Labels**: Variable labels from Stata/SPSS files are indexed, allowing you to search for datasets containing specific variables.

4. **Rebuilding**: Use `socdata rebuild-index` to rebuild the index from all cached datasets if needed.

## Search Syntax

The search supports SQLite FTS5 syntax when available:
- Simple terms: `unemployment`
- Phrases: `"unemployment rate"`
- Boolean operators: `unemployment AND rate`
- Prefix matching: `unemploy*`

When FTS5 is not available, simple substring matching is used.
