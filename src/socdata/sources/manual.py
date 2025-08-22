from __future__ import annotations

from pathlib import Path
import zipfile
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

	def ingest(self, dataset_id: str | None, *, file_path: str) -> pd.DataFrame:
		path = Path(file_path)
		if not path.exists():
			raise FileNotFoundError(path)
		# Determine recipe from dataset_id (expects 'manual:wvs' or 'wvs')
		recipe = None
		if dataset_id:
			ds = dataset_id.split(":", 1)[1] if ":" in dataset_id else dataset_id
			recipe = ds.lower()

		if path.suffix.lower() == ".zip":
			# Extract zip to a sibling directory next to the zip
			extract_dir = path.with_suffix("")
			extract_dir.mkdir(parents=True, exist_ok=True)
			with zipfile.ZipFile(path, "r") as zf:
				zf.extractall(extract_dir)
			# Pick a candidate data file
			candidates = []
			for p in extract_dir.rglob("*"):
				if p.is_file() and p.suffix.lower() in {".dta", ".sav", ".zsav", ".csv", ".tsv"}:
					candidates.append((p.stat().st_size, p))
			if not candidates:
				raise ValueError("No supported data files (.dta/.sav/.zsav/.csv/.tsv) found in extracted zip")
			# Prefer Stata/SPSS formats, then largest
			def rank(p: Path) -> int:
				if p.suffix.lower() in {".dta", ".sav", ".zsav"}:
					return 0
				return 1
			candidates.sort(key=lambda t: (rank(t[1]), -t[0]))
			target = candidates[0][1]
			df = read_table(target)
			return df

		# Single file path provided
		df = read_table(path)
		return df

