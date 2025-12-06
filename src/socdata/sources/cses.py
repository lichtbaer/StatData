from __future__ import annotations

import zipfile
from pathlib import Path
from typing import Any, Dict, List
import re

import pandas as pd

from .base import BaseAdapter
from ..core.types import DatasetSummary
from ..core.models import IngestionManifest
from ..core.storage import get_dataset_dir
from ..core.download import download_file


class CSESAdapter(BaseAdapter):
    """
    Adapter for CSES (Comparative Study of Electoral Systems).
    
    CSES data is available from https://cses.org/
    This adapter supports ingestion from CSES data files (SPSS, Stata, or CSV formats).
    """

    CSES_BASE_URL = "https://cses.org/"

    def list_datasets(self) -> List[DatasetSummary]:
        """List available CSES datasets."""
        return [
            DatasetSummary(
                id="cses:cses-module-1",
                source="cses",
                title="CSES Module 1 (1996-2001)"
            ),
            DatasetSummary(
                id="cses:cses-module-2",
                source="cses",
                title="CSES Module 2 (2001-2006)"
            ),
            DatasetSummary(
                id="cses:cses-module-3",
                source="cses",
                title="CSES Module 3 (2006-2011)"
            ),
            DatasetSummary(
                id="cses:cses-module-4",
                source="cses",
                title="CSES Module 4 (2011-2016)"
            ),
            DatasetSummary(
                id="cses:cses-module-5",
                source="cses",
                title="CSES Module 5 (2016-2021)"
            ),
            DatasetSummary(
                id="cses:cses-integrated",
                source="cses",
                title="CSES Integrated Dataset (all modules)"
            ),
        ]

    def load(self, dataset_id: str, *, filters: Dict[str, Any]) -> pd.DataFrame:
        """
        Load CSES dataset from cache.
        
        Args:
            dataset_id: Format 'cses:cses-module-N' or 'cses:cses-integrated'
            filters: Optional filters (e.g., {'country': 'DE', 'module': 5})
        
        Returns:
            DataFrame with CSES data
        """
        parts = dataset_id.split(":")
        if len(parts) < 2:
            raise ValueError(f"Invalid CSES dataset ID: {dataset_id}. Expected format: cses:cses-module-N")
        
        dataset_name = parts[1]
        version = parts[2] if len(parts) > 2 else "latest"
        
        # Check cache first
        cache_dir = get_dataset_dir("cses", dataset_name, version)
        parquet_path = cache_dir / "processed" / "data.parquet"
        
        if parquet_path.exists():
            # Use optimized read with column selection if filters are provided
            columns = list(filters.keys()) if filters else None
            df = self._read_parquet_optimized(parquet_path, columns=columns)
            # Apply filters if provided
            if filters:
                df = self._apply_filters(df, filters)
            return df
        
        # If not cached, require manual ingestion
        raise NotImplementedError(
            f"CSES dataset '{dataset_id}' not found in cache. "
            "Please use ingest() with a local CSES data file first. "
            "CSES data requires registration and download from https://cses.org/"
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

    def _detect_cses_module(self, file_path: Path) -> str:
        """
        Try to detect CSES module from filename or content.
        
        Common patterns:
        - CSES_Module1.sav
        - cses_module2.dta
        - CSES_Integrated.sav
        """
        name = file_path.stem.upper()
        
        # Check for integrated
        if "INTEGRATED" in name:
            return "cses-integrated"
        
        # Check for module pattern
        module_match = re.search(r"MODULE[_\s]?(\d+)", name)
        if module_match:
            module_num = module_match.group(1)
            return f"cses-module-{module_num}"
        
        return "cses-unknown"

    def _extract_cses_zip(self, zip_path: Path, extract_dir: Path) -> Path:
        """
        Extract CSES ZIP and find the main data file.
        
        CSES ZIPs typically contain:
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
                f"No supported data files (.dta/.sav/.zsav/.csv/.tsv) found in CSES ZIP: {zip_path}"
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
        Ingest CSES dataset from local file.
        
        Args:
            dataset_id: Format 'cses:cses-module-N' or None (auto-detected)
            file_path: Path to CSES data file (.sav, .dta, .csv) or ZIP archive
        
        Returns:
            Normalized DataFrame
        """
        path = Path(file_path)
        
        # Handle URL downloads
        if file_path.startswith(("http://", "https://")):
            cache_dir = get_dataset_dir("cses", "downloads", "temp")
            path = cache_dir / Path(file_path).name
            if not path.exists():
                download_file(file_path, path)
        
        if not path.exists():
            raise FileNotFoundError(f"CSES data file not found: {path}")
        
        # Determine dataset name and version
        if dataset_id:
            parts = dataset_id.split(":")
            dataset_name = parts[1] if len(parts) > 1 else "cses-unknown"
            version = parts[2] if len(parts) > 2 else "latest"
        else:
            # Auto-detect from filename
            if path.suffix.lower() == ".zip":
                # Will detect after extraction
                dataset_name = "cses-unknown"
            else:
                dataset_name = self._detect_cses_module(path)
            version = "latest"
        
        # Handle ZIP files
        if path.suffix.lower() == ".zip":
            extract_dir = path.parent / f"{path.stem}_extracted"
            target_file = self._extract_cses_zip(path, extract_dir)
            if not dataset_id or dataset_name == "cses-unknown":
                dataset_name = self._detect_cses_module(target_file)
        else:
            target_file = path
            if not dataset_id or dataset_name == "cses-unknown":
                dataset_name = self._detect_cses_module(target_file)
        
        # Read with metadata when possible
        df, meta = self._read_table_with_meta_fallback(target_file)
        
        # Normalize
        df = self._normalize(df)
        
        # Write to cache
        cache_dir = get_dataset_dir("cses", dataset_name, version)
        manifest = IngestionManifest(
            timestamp=pd.Timestamp.utcnow().to_pydatetime(),
            adapter="cses",
            parameters={
                "file_path": str(path),
                "target": str(target_file),
                "dataset_name": dataset_name,
                "version": version,
            },
            source_hashes={},
            transforms=["lowercase_columns", "strip_object_columns"],
            dataset_id=f"cses:{dataset_name}",
            source="cses",
            license="CSES data use agreement required - see https://cses.org/",
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
        out_path = proc_dir / "data.parquet"
        self._write_parquet_with_metadata(
            df=df,
            output_path=out_path,
            dataset_id=f"cses:{dataset_name}",
            source="cses",
            adapter="cses",
            manifest_path=manifest_path,
            variable_labels=manifest.variable_labels,
            value_labels=manifest.value_labels,
        )
        
        # Index the dataset
        self._index_dataset_safe(f"cses:{dataset_name}", manifest_path)
        
        return df
