from __future__ import annotations

from typing import Dict, List

from ..sources.base import BaseAdapter
from ..sources.eurostat import EurostatAdapter
from ..sources.manual import ManualAdapter
from ..sources.soep import SOEPAdapter
from ..sources.gss import GSSAdapter
from .types import DatasetSummary


_ADAPTERS: Dict[str, BaseAdapter] = {
    "eurostat": EurostatAdapter(),
    "manual": ManualAdapter(),
    "soep": SOEPAdapter(),
    "gss": GSSAdapter(),
}


def resolve_adapter(dataset_or_adapter_id: str) -> BaseAdapter:
    # dataset id format examples: eurostat:une_rt_m, manual:wvs
    if ":" in dataset_or_adapter_id:
        source, _ = dataset_or_adapter_id.split(":", 1)
        if source in _ADAPTERS:
            return _ADAPTERS[source]
    # allow passing adapter explicitly e.g. manual
    if dataset_or_adapter_id in _ADAPTERS:
        return _ADAPTERS[dataset_or_adapter_id]
    raise KeyError(f"Unknown adapter for '{dataset_or_adapter_id}'")


def list_datasets(source: str | None = None) -> List[DatasetSummary]:
    summaries: List[DatasetSummary] = []
    for key, adapter in _ADAPTERS.items():
        if source and source != key:
            continue
        summaries.extend(adapter.list_datasets())
    return summaries


def search_datasets(query: str) -> List[DatasetSummary]:
    query_lower = query.lower()
    all_ds = list_datasets()
    return [ds for ds in all_ds if query_lower in ds.title.lower() or query_lower in ds.id.lower()]

