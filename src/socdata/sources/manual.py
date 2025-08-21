from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

import pandas as pd

from .base import BaseAdapter
from ..core.parsers import read_table
from ..core.types import DatasetSummary


class ManualAdapter(BaseAdapter):
    def list_datasets(self) -> List[DatasetSummary]:
        return [
            DatasetSummary(id="manual:wvs", source="manual", title="World Values Survey (manual ingest)")
        ]

    def load(self, dataset_id: str, *, filters: Dict[str, Any]) -> pd.DataFrame:  # not applicable
        raise NotImplementedError(
            "Manual adapter requires ingest() with a local file path; use CLI ingest_cmd"
        )

    def ingest(self, *, file_path: str) -> pd.DataFrame:
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(path)
        # MVP: if a single table provided, parse it. If it's a zip, ask user to extract first.
        if path.suffix.lower() == ".zip":
            raise ValueError("For MVP, please extract the WVS zip and provide the main data file (CSV/DTA/SAV)")
        df = read_table(path)
        return df

