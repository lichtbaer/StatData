# Advanced Features Tutorial

This tutorial covers advanced features of SocData.

## Internationalization (i18n)

SocData supports multiple languages for variable and value labels:

```python
from socdata.core.i18n import get_i18n_manager

i18n = get_i18n_manager(default_language="en")

# Save translations
i18n.save_translation("de", {
    "Unemployment rate": "Arbeitslosenquote",
    "GDP": "BIP",
}, dataset_id="eurostat:une_rt_m")

# Translate labels
translated = i18n.translate_variable_labels(
    {"var1": "Unemployment rate"},
    language="de",
    dataset_id="eurostat:une_rt_m"
)
```

## Cloud Storage

Use cloud storage (S3) for caching datasets:

```python
from socdata.core.cloud_storage import get_cloud_storage_manager

# Configure via environment variables:
# SOCDATA_S3_BUCKET=my-bucket
# AWS_ACCESS_KEY_ID=...
# AWS_SECRET_ACCESS_KEY=...

storage = get_cloud_storage_manager()

if storage.is_available():
    # Upload dataset to cloud
    storage.upload_dataset("eurostat", "une_rt_m", "latest")
    
    # Download from cloud
    storage.download_dataset("eurostat", "une_rt_m", "latest")
```

## Cache Management

Control cache behavior:

```python
from socdata.core.cache import get_cache_manager

cache = get_cache_manager()

# Check if cache is valid
if cache.is_valid("eurostat", "une_rt_m"):
    print("Cache is still valid")
else:
    print("Cache expired, reloading...")

# Invalidate cache
cache.invalidate("eurostat", "une_rt_m")

# Cleanup expired entries
removed = cache.cleanup_expired()
print(f"Removed {removed} expired cache entries")
```

## Performance Optimization

### Lazy Loading

Enable lazy loading for large datasets:

```python
from socdata.core.config import get_config

config = get_config()
config.enable_lazy_loading = True
```

### Cache TTL

Adjust cache time-to-live:

```python
config.cache_ttl_hours = 48  # Cache for 48 hours
```

## REST API

Start the REST API server:

```bash
socdata serve
# Or with custom settings
socdata serve --host 0.0.0.0 --port 8080
```

Access the interactive documentation at http://localhost:8000/docs

### Example API Usage

```python
import requests

# List datasets
response = requests.get("http://localhost:8000/datasets")
datasets = response.json()

# Search
response = requests.get("http://localhost:8000/search?q=unemployment")
results = response.json()

# Load dataset
response = requests.post(
    "http://localhost:8000/datasets/eurostat:une_rt_m/load",
    params={"filters": '{"geo": "DE"}'}
)
data = response.json()
```

## Custom Adapters

Create your own adapter:

```python
from socdata.sources.base import BaseAdapter
from socdata.core.types import DatasetSummary

class MyAdapter(BaseAdapter):
    def list_datasets(self):
        return [
            DatasetSummary(id="my:dataset1", source="my", title="My Dataset")
        ]
    
    def load(self, dataset_id, *, filters):
        # Your loading logic
        return pd.DataFrame()
```

Register it in `socdata.core.registry._ADAPTERS`.
