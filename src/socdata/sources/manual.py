from __future__ import annotations

from pathlib import Path
import zipfile
from typing import Any, Dict, List, Tuple

import pandas as pd

from .base import BaseAdapter
from ..core.parsers import read_table, read_table_with_meta
from ..core.types import DatasetSummary
from ..core.models import IngestionManifest
from ..core.storage import get_dataset_dir


class ManualAdapter(BaseAdapter):
	def list_datasets(self) -> List[DatasetSummary]:
		return [
			DatasetSummary(id="manual:wvs", source="manual", title="World Values Survey (manual ingest)")
		]

	def load(self, dataset_id: str, *, filters: Dict[str, Any]) -> pd.DataFrame:  # not applicable
		raise NotImplementedError(
			"Manual adapter requires ingest() with a local file path; use CLI ingest_cmd"
		)

	def _select_target_from_zip(self, zip_path: Path) -> Path:
		# Extract zip to a sibling directory next to the zip
		extract_dir = zip_path.with_suffix("")
		extract_dir.mkdir(parents=True, exist_ok=True)
		with zipfile.ZipFile(zip_path, "r") as zf:
			zf.extractall(extract_dir)
		# Pick a candidate data file
		candidates: List[Tuple[int, Path]] = []
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
		return candidates[0][1]

	def _normalize(self, df: pd.DataFrame) -> pd.DataFrame:
		# lowercase columns and strip whitespace in object columns
		df = df.copy()
		df.columns = [str(c).strip().lower() for c in df.columns]
		for col in df.select_dtypes(include=["object"]).columns:
			df[col] = df[col].astype(str).str.strip()
		return df

	def ingest(self, dataset_id: str | None, *, file_path: str) -> pd.DataFrame:
		path = Path(file_path)
		if not path.exists():
			raise FileNotFoundError(path)
		# Determine recipe from dataset_id (expects 'manual:wvs' or 'wvs')
		recipe = None
		if dataset_id:
			ds = dataset_id.split(":", 1)[1] if ":" in dataset_id else dataset_id
			recipe = ds.lower()

		# Choose target file
		if path.suffix.lower() == ".zip":
			target = self._select_target_from_zip(path)
		else:
			target = path

		# Read with metadata when possible
		try:
			df, meta = read_table_with_meta(target)
		except Exception:
			df = read_table(target)
			meta = {"variable_labels": {}, "value_labels": {}}

		# Normalize
		df = self._normalize(df)

		# Write manifest to cache
		source = "manual"
		dsid = dataset_id or "manual:wvs"
		cache_dir = get_dataset_dir(source, dsid.replace(":", "_"), version="latest")
		manifest = IngestionManifest(
			timestamp=pd.Timestamp.utcnow().to_pydatetime(),
			adapter="manual",
			parameters={"file_path": str(path), "target": str(target), "recipe": str(recipe)},
			source_hashes={},
			transforms=["lowercase_columns", "strip_object_columns"],
			dataset_id=dsid,
			source=source,
			license=None,
			variable_labels=meta.get("variable_labels", {}),
			value_labels=meta.get("value_labels", {}),
		)
		meta_dir = cache_dir / "meta"
		proc_dir = cache_dir / "processed"
		meta_dir.mkdir(parents=True, exist_ok=True)
		proc_dir.mkdir(parents=True, exist_ok=True)
		manifest_path = meta_dir / "ingestion_manifest.json"
		manifest_path.write_text(manifest.to_json(), encoding="utf-8")

		# Save normalized parquet with Arrow metadata
		try:
			import json as _json
			import pyarrow as pa
			import pyarrow.parquet as pq
			table = pa.Table.from_pandas(df, preserve_index=False)
			meta_bytes = table.schema.metadata or {}
			aug = {
				b"socdata.dataset_id": dsid.encode("utf-8"),
				b"socdata.source": source.encode("utf-8"),
				b"socdata.adapter": b"manual",
				b"socdata.manifest_path": str(manifest_path).encode("utf-8"),
				b"socdata.variable_labels": _json.dumps(manifest.variable_labels).encode("utf-8"),
				b"socdata.value_labels": _json.dumps(manifest.value_labels).encode("utf-8"),
			}
			new_schema = table.schema.with_metadata({**meta_bytes, **aug})
			table = table.replace_schema_metadata(new_schema.metadata)
			out_path = proc_dir / "data.parquet"
			pq.write_table(table, out_path)
		except Exception:
			# Best-effort; ignore metadata write failures
			pass

		# Index the dataset
		try:
			from ..core.registry import index_dataset_from_manifest
			index_dataset_from_manifest(dsid, str(manifest_path))
		except Exception:
			# Silently fail if indexing fails
			pass

		return df

