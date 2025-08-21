from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List

import pandas as pd

from ..core.types import DatasetSummary


class BaseAdapter(ABC):
    @abstractmethod
    def list_datasets(self) -> List[DatasetSummary]:  # lightweight built-ins
        raise NotImplementedError

    @abstractmethod
    def load(self, dataset_id: str, *, filters: Dict[str, Any]) -> pd.DataFrame:
        raise NotImplementedError

    def ingest(self, *, file_path: str) -> pd.DataFrame:  # optional for manual adapters
        raise NotImplementedError

