from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List
from urllib.parse import urlparse

import pandas as pd

from .base import BaseAdapter
from ..core.parsers import read_table, read_table_with_meta
from ..core.types import DatasetSummary
from ..core.models import IngestionManifest
from ..core.storage import get_dataset_dir
from ..core.download import download_file


class GSSAdapter(BaseAdapter):
    """
    Adapter for General Social Survey (GSS).
    
    GSS data is available from NORC at the University of Chicago.
    This adapter supports scripted ingestion from GSS data files.
    """

    # GSS data portal base URL (example - actual URL may vary)
    GSS_BASE_URL = "https://gss.norc.org/get-the-data/stata"

    def list_datasets(self) -> List[DatasetSummary]:
        return [
            DatasetSummary(
                id="gss:gss-cumulative",
                source="gss",
                title="GSS Cumulative Data (1972-present)"
            ),
            DatasetSummary(
                id="gss:gss-2022",
                source="gss",
                title="GSS 2022 Cross-Section"
            ),
        ]

    def load(self, dataset_id: str, *, filters: Dict[str, Any]) -> pd.DataFrame:
        """
        Load GSS dataset from cache or trigger download.
        
        Args:
            dataset_id: Format 'gss:dataset_name' or 'gss:dataset_name:version'
            filters: Optional filters (e.g., {'year': 2022})
        
        Returns:
            DataFrame with GSS data
        """
        parts = dataset_id.split(":")
        if len(parts) < 2:
            raise ValueError(f"Invalid GSS dataset ID: {dataset_id}. Expected format: gss:dataset_name")
        
        dataset_name = parts[1]
        version = parts[2] if len(parts) > 2 else "latest"
        
        # Check cache first
        cache_dir = get_dataset_dir("gss", dataset_name, version)
        parquet_path = cache_dir / "processed" / "data.parquet"
        
        if parquet_path.exists():
            df = pd.read_parquet(parquet_path)
            # Apply filters if provided
            if filters:
                df = self._apply_filters(df, filters)
            return df
        
        # If not cached, require manual ingestion
        raise NotImplementedError(
            f"GSS dataset '{dataset_id}' not found in cache. "
            "Please use ingest() with a local GSS data file first. "
            "GSS data requires registration and manual download from https://gss.norc.org"
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

    def _detect_gss_version(self, file_path: Path) -> str:
        """
        Try to detect GSS version/year from filename or content.
        
        Common patterns:
        - GSS7218_R3.dta (cumulative, release 3)
        - GSS2022.dta (single year)
        """
        name = file_path.stem.upper()
        
        # Check for year pattern (4 digits)
        year_match = re.search(r"(\d{4})", name)
        if year_match:
            year = year_match.group(1)
            if "CUMULATIVE" in name or "R" in name:
                return f"cumulative-{year}"
            return f"gss-{year}"
        
        # Check for cumulative pattern
        if "CUMULATIVE" in name or ("GSS" in name and "R" in name):
            release_match = re.search(r"R(\d+)", name)
            if release_match:
                return f"cumulative-r{release_match.group(1)}"
            return "cumulative"
        
        return "unknown"

    def ingest(self, dataset_id: str | None, *, file_path: str) -> pd.DataFrame:
        """
        Ingest GSS dataset from local file.
        
        Args:
            dataset_id: Format 'gss:dataset_name' or None (auto-detected)
            file_path: Path to GSS data file (.dta, .sav, .csv) or URL
        
        Returns:
            Normalized DataFrame
        """
        path = Path(file_path)
        
        # Handle URL downloads (if GSS provides direct download links)
        if file_path.startswith(("http://", "https://")):
            cache_dir = get_dataset_dir("gss", "downloads", "temp")
            path = cache_dir / Path(urlparse(file_path).path).name
            if not path.exists():
                download_file(file_path, path)
        
        if not path.exists():
            raise FileNotFoundError(f"GSS data file not found: {path}")
        
        # Determine dataset name and version
        if dataset_id:
            parts = dataset_id.split(":")
            dataset_name = parts[1] if len(parts) > 1 else "gss-unknown"
            version = parts[2] if len(parts) > 2 else "latest"
        else:
            # Auto-detect from filename
            version_info = self._detect_gss_version(path)
            if "cumulative" in version_info.lower():
                dataset_name = "gss-cumulative"
            else:
                dataset_name = version_info
            version = "latest"
        
        # Read with metadata when possible
        try:
            df, meta = read_table_with_meta(path)
        except Exception:
            df = read_table(path)
            meta = {"variable_labels": {}, "value_labels": {}}
        
        # Normalize
        df = self._normalize(df)
        
        # Write to cache
        cache_dir = get_dataset_dir("gss", dataset_name, version)
        manifest = IngestionManifest(
            timestamp=pd.Timestamp.utcnow().to_pydatetime(),
            adapter="gss",
            parameters={
                "file_path": str(path),
                "dataset_name": dataset_name,
                "version": version,
            },
            source_hashes={},
            transforms=["lowercase_columns", "strip_object_columns"],
            dataset_id=f"gss:{dataset_name}",
            source="gss",
            license="GSS data use agreement required - see https://gss.norc.org",
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
        shutil.copy2(path, raw_dir / path.name)
        
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
                b"socdata.dataset_id": f"gss:{dataset_name}".encode("utf-8"),
                b"socdata.source": b"gss",
                b"socdata.adapter": b"gss",
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
            index_dataset_from_manifest(f"gss:{dataset_name}", str(manifest_path))
        except Exception:
            # Silently fail if indexing fails
            pass
        
        return df
