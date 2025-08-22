from __future__ import annotations

from typing import Any, Dict, List

import pandas as pd

try:
    import eurostat  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    eurostat = None  # type: ignore

from .base import BaseAdapter
from ..core.types import DatasetSummary


class EurostatAdapter(BaseAdapter):
    def list_datasets(self) -> List[DatasetSummary]:
        # Minimal curated examples for MVP
        return [
            DatasetSummary(id="eurostat:une_rt_m", source="eurostat", title="Unemployment rate - monthly"),
            DatasetSummary(id="eurostat:demo_r_pjangroup", source="eurostat", title="Population on 1 January by age group, sex and NUTS 3 region"),
        ]

    def load(self, dataset_id: str, *, filters: Dict[str, Any]) -> pd.DataFrame:
        if eurostat is None:
            raise RuntimeError("eurostat extra not installed. Install with: pip install socdata[eurostat]")
        _, code = dataset_id.split(":", 1)
        # eurostat.get_data_df handles filters via 'filter_pars'
        # eurostat.get_data_df requires dict for filter_pars; pass {} if none
        df = eurostat.get_data_df(code, filter_pars=filters or {})
        return df

    def ingest(self, *, file_path: str) -> pd.DataFrame:  # not applicable
        raise NotImplementedError("Eurostat adapter does not support ingest() from file")

