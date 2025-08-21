# Configuration

SocData reads configuration at runtime.

## Defaults

- Cache directory: `~/.socdata`
- Timeout: 60 seconds
- Retries: 3
- User-Agent: `socdata/0.1`

## Environment variables

- `SOCDATA_CONFIG`: Path to a future YAML/JSON config file (planned)

## Showing config

```bash
socdata show-config
```