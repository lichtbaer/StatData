from __future__ import annotations

import zipfile
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd

from .base import BaseAdapter
from ..core.parsers import read_table, read_table_with_meta
from ..core.types import DatasetSummary
from ..core.models import IngestionManifest
from ..core.storage import get_dataset_dir
from ..core.download import download_file


class SOEPAdapter(BaseAdapter):
    """
    Adapter for SOEP (Socio-Economic Panel) Open Data Format (ODF).
    
    SOEP ODF files are ZIP archives containing data files and documentation.
    This adapter handles loading from ODF ZIP files, either from local paths
    or by downloading from SOEP's data portal.
    """

    def list_datasets(self) -> List[DatasetSummary]:
        return [
            DatasetSummary(
                id="soep:soep-core",
                source="soep",
                title="SOEP Core - Socio-Economic Panel Study"
            ),
            DatasetSummary(
                id="soep:soep-is",
                source="soep",
                title="SOEP Innovation Sample"
            ),
        ]

    def load(self, dataset_id: str, *, filters: Dict[str, Any]) -> pd.DataFrame:
        """
        Load SOEP dataset from ODF format.
        
        Args:
            dataset_id: Format 'soep:dataset_name' or 'soep:dataset_name:version'
            filters: Optional filters (e.g., {'year': 2020, 'wave': 'v38'})
        
        Returns:
            DataFrame with SOEP data
        """
        parts = dataset_id.split(":")
        if len(parts) < 2:
            raise ValueError(f"Invalid SOEP dataset ID: {dataset_id}. Expected format: soep:dataset_name")
        
        dataset_name = parts[1]
        version = parts[2] if len(parts) > 2 else "latest"
        
        # Check cache first
        cache_dir = get_dataset_dir("soep", dataset_name, version)
        parquet_path = cache_dir / "processed" / "data.parquet"
        
        if parquet_path.exists():
            return pd.read_parquet(parquet_path)
        
        # If not cached, require manual ingestion via ingest()
        raise NotImplementedError(
            f"SOEP dataset '{dataset_id}' not found in cache. "
            "Please use ingest() with a local ODF ZIP file first, or download it manually."
        )

    def _extract_odf_zip(self, zip_path: Path, extract_dir: Path) -> Path:
        """
        Extract ODF ZIP and find the main data file.
        
        ODF ZIPs typically contain:
        - Data files (.dta, .sav, .csv)
        - Documentation files (.pdf, .txt)
        - Metadata files
        
        Returns:
            Path to the main data file
        """
        extract_dir.mkdir(parents=True, exist_ok=True)
        
        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(extract_dir)
        
        # Find data files (prefer Stata/SPSS, then largest CSV)
        candidates: List[tuple[int, Path]] = []
        for p in extract_dir.rglob("*"):
            if p.is_file() and p.suffix.lower() in {".dta", ".sav", ".zsav", ".csv", ".tsv"}:
                # Skip documentation subdirectories
                if "doc" in p.parts or "readme" in p.name.lower():
                    continue
                candidates.append((p.stat().st_size, p))
        
        if not candidates:
            raise ValueError(
                f"No supported data files (.dta/.sav/.zsav/.csv/.tsv) found in ODF ZIP: {zip_path}"
            )
        
        # Prefer Stata/SPSS formats, then largest file
        def rank(p: Path) -> int:
            if p.suffix.lower() in {".dta", ".sav", ".zsav"}:
                return 0
            return 1
        
        candidates.sort(key=lambda t: (rank(t[1]), -t[0]))
        return candidates[0][1]

    def _normalize(self, df: pd.DataFrame) -> pd.DataFrame:
        """Normalize column names and string values."""
        df = df.copy()
        df.columns = [str(c).strip().lower() for c in df.columns]
        for col in df.select_dtypes(include=["object"]).columns:
            df[col] = df[col].astype(str).str.strip()
        return df

    def ingest(self, dataset_id: str | None, *, file_path: str) -> pd.DataFrame:
        """
        Ingest SOEP dataset from ODF ZIP file.
        
        Args:
            dataset_id: Format 'soep:dataset_name' or None (auto-detected from file)
            file_path: Path to ODF ZIP file or URL to download
        
        Returns:
            Normalized DataFrame
        """
        path = Path(file_path)
        
        # Handle URL downloads
        if file_path.startswith(("http://", "https://")):
            cache_dir = get_dataset_dir("soep", "downloads", "temp")
            path = cache_dir / Path(file_path).name
            if not path.exists():
                download_file(file_path, path)
        
        if not path.exists():
            raise FileNotFoundError(f"SOEP ODF file not found: {path}")
        
        if path.suffix.lower() != ".zip":
            raise ValueError(f"SOEP ODF files must be ZIP archives, got: {path.suffix}")
        
        # Determine dataset name
        if dataset_id:
            parts = dataset_id.split(":")
            dataset_name = parts[1] if len(parts) > 1 else "soep-unknown"
        else:
            # Try to infer from filename
            dataset_name = path.stem.replace("_", "-").lower()
            if "soep" not in dataset_name:
                dataset_name = f"soep-{dataset_name}"
        
        # Extract and find data file
        extract_dir = path.parent / f"{path.stem}_extracted"
        target_file = self._extract_odf_zip(path, extract_dir)
        
        # Read with metadata when possible
        try:
            df, meta = read_table_with_meta(target_file)
        except Exception:
            df = read_table(target_file)
            meta = {"variable_labels": {}, "value_labels": {}}
        
        # Normalize
        df = self._normalize(df)
        
        # Write to cache
        cache_dir = get_dataset_dir("soep", dataset_name, version="latest")
        manifest = IngestionManifest(
            timestamp=pd.Timestamp.utcnow().to_pydatetime(),
            adapter="soep",
            parameters={
                "file_path": str(path),
                "target": str(target_file),
                "extract_dir": str(extract_dir),
            },
            source_hashes={},
            transforms=["lowercase_columns", "strip_object_columns"],
            dataset_id=f"soep:{dataset_name}",
            source="soep",
            license="SOEP data use agreement required",
            variable_labels=meta.get("variable_labels", {}),
            value_labels=meta.get("value_labels", {}),
        )
        
        meta_dir = cache_dir / "meta"
        proc_dir = cache_dir / "processed"
        raw_dir = cache_dir / "raw"
        meta_dir.mkdir(parents=True, exist_ok=True)
        proc_dir.mkdir(parents=True, exist_ok=True)
        raw_dir.mkdir(parents=True, exist_ok=True)
        
        # Copy original ZIP to raw cache
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
                b"socdata.dataset_id": f"soep:{dataset_name}".encode("utf-8"),
                b"socdata.source": b"soep",
                b"socdata.adapter": b"soep",
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
        
        return df
