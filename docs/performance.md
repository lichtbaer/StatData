# Performance Optimization

SocData includes several features to optimize performance when working with large datasets.

## Lazy Loading

Lazy loading allows SocData to only load the columns you need from Parquet files. This can significantly improve performance and reduce memory usage.

### How It Works

When you load a dataset with filters, SocData can optimize the loading process by:

1. **Column Selection**: Only reading the columns specified in your filters
2. **Reduced Memory**: Loading less data into memory
3. **Faster Load Times**: Reading fewer columns means faster I/O

### Example

```python
import socdata as sd

# Load dataset with filters - only filter columns are loaded
df = sd.load("gss:gss-cumulative", filters={"year": 2022, "age": 30})
```

In this example, if lazy loading is enabled, SocData will only read the `year` and `age` columns from the Parquet file, plus any other columns needed for the result.

### Enabling/Disabling

Lazy loading is enabled by default. You can control it via configuration:

```yaml
# config.yaml
enable_lazy_loading: true  # or false to disable
```

Or via environment variable:
```bash
export SOCDATA_ENABLE_LAZY_LOADING=true
```

### When to Use

**Use lazy loading when:**
- Working with large datasets (>1GB)
- You only need specific columns
- Memory is limited
- You're applying filters

**Disable lazy loading when:**
- You need all columns anyway
- The dataset is small
- You want to ensure all data is loaded upfront

## Caching

SocData caches processed datasets in Parquet format for fast subsequent access.

### Cache Behavior

- Datasets are cached after first load/ingestion
- Cache is checked before downloading/processing
- Cache TTL can be configured (default: 24 hours)
- Cache location: `~/.socdata` by default

### Cache Management

```bash
# Show cache directory
socdata show-config

# Cache is automatically managed
# Old entries are cleaned up based on TTL
```

### Cache Configuration

```yaml
cache_dir: "/path/to/cache"
cache_ttl_hours: 48  # Keep cache for 48 hours
```

## Parquet Format

SocData uses Parquet format for efficient storage and retrieval:

- **Columnar Storage**: Efficient for analytical workloads
- **Compression**: Automatic compression reduces storage
- **Metadata**: Preserves variable and value labels
- **Fast Reads**: Optimized for reading specific columns

## Best Practices

1. **Use Filters**: When possible, use filters to reduce data size
2. **Enable Lazy Loading**: Keep it enabled for large datasets
3. **Cache Management**: Adjust TTL based on your needs
4. **Column Selection**: If you only need specific columns, use filters

## Performance Tips

- **Large Datasets**: Always use lazy loading and filters
- **Repeated Queries**: Cache will speed up repeated loads
- **Memory Constraints**: Reduce cache TTL or disable lazy loading if needed
- **Network**: Use local cache to avoid repeated downloads
