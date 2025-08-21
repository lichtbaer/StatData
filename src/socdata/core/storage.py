from __future__ import annotations

from pathlib import Path

from .config import get_config


def get_dataset_dir(source: str, dataset: str, version: str = "latest") -> Path:
    cfg = get_config()
    base = cfg.cache_dir / source / dataset / version
    (base / "raw").mkdir(parents=True, exist_ok=True)
    (base / "processed").mkdir(parents=True, exist_ok=True)
    (base / "meta").mkdir(parents=True, exist_ok=True)
    return base

