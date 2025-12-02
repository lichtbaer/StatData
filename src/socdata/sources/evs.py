from __future__ import annotations

import zipfile
from pathlib import Path
from typing import Any, Dict, List
import re

import pandas as pd

from .base import BaseAdapter
from ..core.parsers import read_table, read_table_with_meta
from ..core.types import DatasetSummary
from ..core.models import IngestionManifest
from ..core.storage import get_dataset_dir
from ..core.download import download_file


class EVSAdapter(BaseAdapter):
    """
    Adapter for EVS (European Values Study).
    
    EVS data is available from https://europeanvaluesstudy.eu/
    This adapter supports ingestion from EVS data files (SPSS, Stata, or CSV formats).
    """

    EVS_BASE_URL = "https://europeanvaluesstudy.eu/"

    def list_datasets(self) -> List[DatasetSummary]:
        """List available EVS datasets."""
        return [
            DatasetSummary(
                id="evs:evs-1981",
                source="evs",
                title="EVS 1981 - First Wave"
            ),
            DatasetSummary(
                id="evs:evs-1990",
                source="evs",
                title="EVS 1990 - Second Wave"
            ),
            DatasetSummary(
                id="evs:evs-1999",
                source="evs",
                title="EVS 1999 - Third Wave"
            ),
            DatasetSummary(
                id="evs:evs-2008",
                source="evs",
                title="EVS 2008 - Fourth Wave"
            ),
            DatasetSummary(
                id="evs:evs-2017",
                source="evs",
                title="EVS 2017 - Fifth Wave"
            ),
            DatasetSummary(
                id="evs:evs-integrated",
                source="evs",
                title="EVS Integrated Dataset (all waves)"
            ),
        ]

    def load(self, dataset_id: str, *, filters: Dict[str, Any]) -> pd.DataFrame:
        """
        Load EVS dataset from cache.
        
        Args:
            dataset_id: Format 'evs:evs-YYYY' or 'evs:evs-integrated'
            filters: Optional filters (e.g., {'country': 'DE', 'wave': 2017})
        
        Returns:
            DataFrame with EVS data
        """
        parts = dataset_id.split(":")
        if len(parts) < 2:
            raise ValueError(f"Invalid EVS dataset ID: {dataset_id}. Expected format: evs:evs-YYYY")
        
        dataset_name = parts[1]
        version = parts[2] if len(parts) > 2 else "latest"
        
        # Check cache first
        cache_dir = get_dataset_dir("evs", dataset_name, version)
        parquet_path = cache_dir / "processed" / "data.parquet"
        
        if parquet_path.exists():
            df = pd.read_parquet(parquet_path)
            # Apply filters if provided
            if filters:
                df = self._apply_filters(df, filters)
            return df
        
        # If not cached, require manual ingestion
        raise NotImplementedError(
            f"EVS dataset '{dataset_id}' not found in cache. "
            "Please use ingest() with a local EVS data file first. "
            "EVS data requires registration and download from https://europeanvaluesstudy.eu/"
        )

    def _apply_filters(self, df: pd.DataFrame, filters: Dict[str, Any]) -> pd.DataFrame:
        """Apply filters to DataFrame."""
        result = df.copy()
        for key, value in filters.items():
            if key in result.columns:
                if isinstance(value, list):
                    result = result[result[key].isin(value)]
                else:
                    result = result[result[key] == value]
        return result

    def _normalize(self, df: pd.DataFrame) -> pd.DataFrame:
        """Normalize column names and string values."""
        df = df.copy()
        df.columns = [str(c).strip().lower() for c in df.columns]
        for col in df.select_dtypes(include=["object"]).columns:
            df[col] = df[col].astype(str).str.strip()
        return df

    def _detect_evs_wave(self, file_path: Path) -> str:
        """
        Try to detect EVS wave from filename or content.
        
        Common patterns:
        - EVS_1981.sav
        - evs_1990.dta
        - EVS_Integrated.sav
        """
        name = file_path.stem.upper()
        
        # Check for integrated
        if "INTEGRATED" in name:
            return "evs-integrated"
        
        # Check for year pattern (4 digits)
        year_match = re.search(r"EVS[_\s]?(\d{4})", name)
        if year_match:
            year = year_match.group(1)
            return f"evs-{year}"
        
        return "evs-unknown"

    def _extract_evs_zip(self, zip_path: Path, extract_dir: Path) -> Path:
        """
        Extract EVS ZIP and find the main data file.
        
        EVS ZIPs typically contain:
        - Data files (.sav, .dta, .csv)
        - Documentation files (.pdf, .txt)
        - Codebooks
        """
        extract_dir.mkdir(parents=True, exist_ok=True)
        
        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(extract_dir)
        
        # Find data files (prefer SPSS/Stata, then largest CSV)
        candidates: List[tuple[int, Path]] = []
        for p in extract_dir.rglob("*"):
            if p.is_file() and p.suffix.lower() in {".dta", ".sav", ".zsav", ".csv", ".tsv"}:
                # Skip documentation subdirectories
                if "doc" in p.parts or "readme" in p.name.lower() or "codebook" in p.name.lower():
                    continue
                candidates.append((p.stat().st_size, p))
        
        if not candidates:
            raise ValueError(
                f"No supported data files (.dta/.sav/.zsav/.csv/.tsv) found in EVS ZIP: {zip_path}"
            )
        
        # Prefer SPSS/Stata formats, then largest file
        def rank(p: Path) -> int:
            if p.suffix.lower() in {".dta", ".sav", ".zsav"}:
                return 0
            return 1
        
        candidates.sort(key=lambda t: (rank(t[1]), -t[0]))
        return candidates[0][1]

    def ingest(self, dataset_id: str | None, *, file_path: str) -> pd.DataFrame:
        """
        Ingest EVS dataset from local file.
        
        Args:
            dataset_id: Format 'evs:evs-YYYY' or None (auto-detected)
            file_path: Path to EVS data file (.sav, .dta, .csv) or ZIP archive
        
        Returns:
            Normalized DataFrame
        """
        path = Path(file_path)
        
        # Handle URL downloads
        if file_path.startswith(("http://", "https://")):
            cache_dir = get_dataset_dir("evs", "downloads", "temp")
            path = cache_dir / Path(file_path).name
            if not path.exists():
                download_file(file_path, path)
        
        if not path.exists():
            raise FileNotFoundError(f"EVS data file not found: {path}")
        
        # Determine dataset name and version
        if dataset_id:
            parts = dataset_id.split(":")
            dataset_name = parts[1] if len(parts) > 1 else "evs-unknown"
            version = parts[2] if len(parts) > 2 else "latest"
        else:
            # Auto-detect from filename
            if path.suffix.lower() == ".zip":
                # Will detect after extraction
                dataset_name = "evs-unknown"
            else:
                dataset_name = self._detect_evs_wave(path)
            version = "latest"
        
        # Handle ZIP files
        if path.suffix.lower() == ".zip":
            extract_dir = path.parent / f"{path.stem}_extracted"
            target_file = self._extract_evs_zip(path, extract_dir)
            if not dataset_id or dataset_name == "evs-unknown":
                dataset_name = self._detect_evs_wave(target_file)
        else:
            target_file = path
            if not dataset_id or dataset_name == "evs-unknown":
                dataset_name = self._detect_evs_wave(target_file)
        
        # Read with metadata when possible
        try:
            df, meta = read_table_with_meta(target_file)
        except Exception:
            df = read_table(target_file)
            meta = {"variable_labels": {}, "value_labels": {}}
        
        # Normalize
        df = self._normalize(df)
        
        # Write to cache
        cache_dir = get_dataset_dir("evs", dataset_name, version)
        manifest = IngestionManifest(
            timestamp=pd.Timestamp.utcnow().to_pydatetime(),
            adapter="evs",
            parameters={
                "file_path": str(path),
                "target": str(target_file),
                "dataset_name": dataset_name,
                "version": version,
            },
            source_hashes={},
            transforms=["lowercase_columns", "strip_object_columns"],
            dataset_id=f"evs:{dataset_name}",
            source="evs",
            license="EVS data use agreement required - see https://europeanvaluesstudy.eu/",
            variable_labels=meta.get("variable_labels", {}),
            value_labels=meta.get("value_labels", {}),
        )
        
        meta_dir = cache_dir / "meta"
        proc_dir = cache_dir / "processed"
        raw_dir = cache_dir / "raw"
        meta_dir.mkdir(parents=True, exist_ok=True)
        proc_dir.mkdir(parents=True, exist_ok=True)
        raw_dir.mkdir(parents=True, exist_ok=True)
        
        # Copy original file to raw cache
        import shutil
        if path.suffix.lower() == ".zip":
            shutil.copy2(path, raw_dir / path.name)
        else:
            shutil.copy2(target_file, raw_dir / target_file.name)
        
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
                b"socdata.dataset_id": f"evs:{dataset_name}".encode("utf-8"),
                b"socdata.source": b"evs",
                b"socdata.adapter": b"evs",
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
            index_dataset_from_manifest(f"evs:{dataset_name}", str(manifest_path))
        except Exception:
            # Silently fail if indexing fails
            pass
        
        return df
