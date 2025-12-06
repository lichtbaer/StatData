# Configuration

SocData reads configuration at runtime.

## Defaults

- Cache directory: `~/.socdata`
- Timeout: 60 seconds
- Retries: 3
- User-Agent: `socdata/0.1`
- Lazy loading: Enabled (`enable_lazy_loading: true`)
- Cache TTL: 24 hours (`cache_ttl_hours: 24`)

## Configuration Options

### Lazy Loading

Lazy loading allows SocData to only load the columns you need from Parquet files, which can significantly improve performance and reduce memory usage for large datasets.

When enabled (default), SocData will:
- Only read specified columns when filters are provided
- Reduce memory footprint for large datasets
- Improve load times for filtered queries

To disable lazy loading, set `enable_lazy_loading: false` in your configuration.

### Cache Settings

- `cache_ttl_hours`: Time-to-live for cached datasets in hours (default: 24)
- `cache_dir`: Directory for storing cached datasets (default: `~/.socdata`)

## Environment variables

- `SOCDATA_CONFIG`: Path to a YAML/JSON config file
- `SOCDATA_CACHE_DIR`: Override cache directory

## Configuration File

You can create a configuration file in YAML or JSON format:

**YAML example (`config.yaml`):**
```yaml
cache_dir: "/path/to/cache"
timeout_seconds: 120
enable_lazy_loading: true
cache_ttl_hours: 48
log_level: "INFO"
```

**JSON example (`config.json`):**
```json
{
  "cache_dir": "/path/to/cache",
  "timeout_seconds": 120,
  "enable_lazy_loading": true,
  "cache_ttl_hours": 48,
  "log_level": "INFO"
}
```

Set the `SOCDATA_CONFIG` environment variable to point to your config file:
```bash
export SOCDATA_CONFIG=/path/to/config.yaml
```

## Showing config

```bash
socdata show-config
```