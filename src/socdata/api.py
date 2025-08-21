from __future__ import annotations

from typing import Any, Dict, Optional

import pandas as pd

from .core.registry import resolve_adapter


def load(dataset_id: str, *, filters: Optional[Dict[str, Any]] = None) -> pd.DataFrame:
    adapter = resolve_adapter(dataset_id)
    return adapter.load(dataset_id, filters=filters or {})


def ingest(adapter_id: str, *, file_path: str) -> pd.DataFrame:
    adapter = resolve_adapter(adapter_id)
    return adapter.ingest(file_path=file_path)

