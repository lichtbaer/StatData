# Getting started

## Install

Development install (from repository root):

```bash
pip install -e .
# Optional: Eurostat support
pip install -e .[eurostat]
```

If your system is externally managed (PEP 668), use a virtualenv or:

```bash
python3 -m pip install --user -e .[eurostat] --break-system-packages
```

## Quickstart (CLI)

```bash
socdata version
socdata list --source eurostat
socdata search "unemployment"
# Load Eurostat dataset
socdata load-cmd eurostat:une_rt_m --filters 'geo=DE' --export out.parquet
```

## Quickstart (Python)

```python
import socdata as sd

df = sd.load("eurostat:une_rt_m", filters={"geo": "DE"})
print(df.head())
```

## Where data is stored

By default, cache is placed under `~/.socdata/{source}/{dataset}/{version}/(raw|processed|meta)`.