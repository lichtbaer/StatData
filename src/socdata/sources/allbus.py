"""
Adapter for ALLBUS (German General Social Survey).

ALLBUS is the German equivalent of the GSS, conducted by GESIS.
Data is available from https://www.gesis.org/allbus/
"""

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


class ALLBUSAdapter(BaseAdapter):
    """
    Adapter for ALLBUS (Allgemeine Bevölkerungsumfrage der Sozialwissenschaften).
    
    ALLBUS is the German General Social Survey, conducted by GESIS.
    Data is available from https://www.gesis.org/allbus/
    This adapter supports ingestion from ALLBUS data files (SPSS, Stata, or CSV formats).
    """

    ALLBUS_BASE_URL = "https://www.gesis.org/allbus/"

    def list_datasets(self) -> List[DatasetSummary]:
        """List available ALLBUS datasets."""
        return [
            DatasetSummary(
                id="allbus:allbus-1980",
                source="allbus",
                title="ALLBUS 1980 - First Wave"
            ),
            DatasetSummary(
                id="allbus:allbus-1982",
                source="allbus",
                title="ALLBUS 1982"
            ),
            DatasetSummary(
                id="allbus:allbus-1984",
                source="allbus",
                title="ALLBUS 1984"
            ),
            DatasetSummary(
                id="allbus:allbus-1986",
                source="allbus",
                title="ALLBUS 1986"
            ),
            DatasetSummary(
                id="allbus:allbus-1988",
                source="allbus",
                title="ALLBUS 1988"
            ),
            DatasetSummary(
                id="allbus:allbus-1990",
                source="allbus",
                title="ALLBUS 1990"
            ),
            DatasetSummary(
                id="allbus:allbus-1991",
                source="allbus",
                title="ALLBUS 1991"
            ),
            DatasetSummary(
                id="allbus:allbus-1992",
                source="allbus",
                title="ALLBUS 1992"
            ),
            DatasetSummary(
                id="allbus:allbus-1994",
                source="allbus",
                title="ALLBUS 1994"
            ),
            DatasetSummary(
                id="allbus:allbus-1996",
                source="allbus",
                title="ALLBUS 1996"
            ),
            DatasetSummary(
                id="allbus:allbus-1998",
                source="allbus",
                title="ALLBUS 1998"
            ),
            DatasetSummary(
                id="allbus:allbus-2000",
                source="allbus",
                title="ALLBUS 2000"
            ),
            DatasetSummary(
                id="allbus:allbus-2002",
                source="allbus",
                title="ALLBUS 2002"
            ),
            DatasetSummary(
                id="allbus:allbus-2004",
                source="allbus",
                title="ALLBUS 2004"
            ),
            DatasetSummary(
                id="allbus:allbus-2006",
                source="allbus",
                title="ALLBUS 2006"
            ),
            DatasetSummary(
                id="allbus:allbus-2008",
                source="allbus",
                title="ALLBUS 2008"
            ),
            DatasetSummary(
                id="allbus:allbus-2010",
                source="allbus",
                title="ALLBUS 2010"
            ),
            DatasetSummary(
                id="allbus:allbus-2012",
                source="allbus",
                title="ALLBUS 2012"
            ),
            DatasetSummary(
                id="allbus:allbus-2014",
                source="allbus",
                title="ALLBUS 2014"
            ),
            DatasetSummary(
                id="allbus:allbus-2016",
                source="allbus",
                title="ALLBUS 2016"
            ),
            DatasetSummary(
                id="allbus:allbus-2018",
                source="allbus",
                title="ALLBUS 2018"
            ),
            DatasetSummary(
                id="allbus:allbus-2021",
                source="allbus",
                title="ALLBUS 2021"
            ),
            DatasetSummary(
                id="allbus:allbus-cumulative",
                source="allbus",
                title="ALLBUS Cumulative (1980-present)"
            ),
        ]

    def load(self, dataset_id: str, *, filters: Dict[str, Any]) -> pd.DataFrame:
        """
        Load ALLBUS dataset from cache.
        
        Args:
            dataset_id: Format 'allbus:allbus-YYYY' or 'allbus:allbus-cumulative'
            filters: Optional filters
        
        Returns:
            DataFrame with ALLBUS data
        """
        parts = dataset_id.split(":")
        if len(parts) < 2:
            raise ValueError(f"Invalid ALLBUS dataset ID: {dataset_id}. Expected format: allbus:allbus-YYYY")
        
        dataset_name = parts[1]
        version = parts[2] if len(parts) > 2 else "latest"
        
        # Check cache first
        cache_dir = get_dataset_dir("allbus", dataset_name, version)
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
            f"ALLBUS dataset '{dataset_id}' not found in cache. "
            "Please use ingest() with a local ALLBUS data file first. "
            "ALLBUS data requires registration and download from https://www.gesis.org/allbus/"
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

    def _detect_allbus_year(self, file_path: Path) -> str:
        """Try to detect ALLBUS year from filename."""
        name = file_path.stem.upper()
        
        # Check for cumulative
        if "CUMULATIVE" in name or "CUM" in name:
            return "allbus-cumulative"
        
        # Check for year pattern (4 digits)
        year_match = re.search(r"(\d{4})", name)
        if year_match:
            year = year_match.group(1)
            # Validate year range (1980-2024)
            if 1980 <= int(year) <= 2024:
                return f"allbus-{year}"
        
        return "allbus-unknown"

    def ingest(self, dataset_id: str | None, *, file_path: str) -> pd.DataFrame:
        """
        Ingest ALLBUS dataset from local file.
        
        Args:
            dataset_id: Format 'allbus:allbus-YYYY' or None (auto-detected)
            file_path: Path to ALLBUS data file (.sav, .dta, .csv) or ZIP archive
        
        Returns:
            Normalized DataFrame
        """
        path = Path(file_path)
        
        # Handle URL downloads
        if file_path.startswith(("http://", "https://")):
            cache_dir = get_dataset_dir("allbus", "downloads", "temp")
            path = cache_dir / Path(file_path).name
            if not path.exists():
                download_file(file_path, path)
        
        if not path.exists():
            raise FileNotFoundError(f"ALLBUS data file not found: {path}")
        
        # Determine dataset name and version
        if dataset_id:
            parts = dataset_id.split(":")
            dataset_name = parts[1] if len(parts) > 1 else "allbus-unknown"
            version = parts[2] if len(parts) > 2 else "latest"
        else:
            # Auto-detect from filename
            if path.suffix.lower() == ".zip":
                dataset_name = "allbus-unknown"
            else:
                dataset_name = self._detect_allbus_year(path)
            version = "latest"
        
        # Handle ZIP files
        if path.suffix.lower() == ".zip":
            extract_dir = path.parent / f"{path.stem}_extracted"
            extract_dir.mkdir(parents=True, exist_ok=True)
            
            with zipfile.ZipFile(path, "r") as zf:
                zf.extractall(extract_dir)
            
            # Find data files
            candidates: List[tuple[int, Path]] = []
            for p in extract_dir.rglob("*"):
                if p.is_file() and p.suffix.lower() in {".dta", ".sav", ".zsav", ".csv", ".tsv"}:
                    if p.stat().st_size < 1024:
                        continue
                    candidates.append((p.stat().st_size, p))
            
            if not candidates:
                raise ValueError(f"No supported data files found in ALLBUS ZIP: {path}")
            
            def rank(p: Path) -> int:
                if p.suffix.lower() in {".dta", ".sav", ".zsav"}:
                    return 0
                return 1
            
            candidates.sort(key=lambda t: (rank(t[1]), -t[0]))
            target_file = candidates[0][1]
            
            if not dataset_id or dataset_name == "allbus-unknown":
                dataset_name = self._detect_allbus_year(target_file)
        else:
            target_file = path
            if not dataset_id or dataset_name == "allbus-unknown":
                dataset_name = self._detect_allbus_year(target_file)
        
        # Read with metadata when possible
        df, meta = self._read_table_with_meta_fallback(target_file)
        
        # Normalize
        df = self._normalize(df)
        
        # Write to cache
        cache_dir = get_dataset_dir("allbus", dataset_name, version)
        manifest = IngestionManifest(
            timestamp=pd.Timestamp.utcnow().to_pydatetime(),
            adapter="allbus",
            parameters={
                "file_path": str(path),
                "target": str(target_file),
                "dataset_name": dataset_name,
                "version": version,
            },
            source_hashes={},
            transforms=["lowercase_columns", "strip_object_columns"],
            dataset_id=f"allbus:{dataset_name}",
            source="allbus",
            license="ALLBUS data use agreement required - see https://www.gesis.org/allbus/",
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
            dataset_id=f"allbus:{dataset_name}",
            source="allbus",
            adapter="allbus",
            manifest_path=manifest_path,
            variable_labels=manifest.variable_labels,
            value_labels=manifest.value_labels,
        )
        
        # Index the dataset
        self._index_dataset_safe(f"allbus:{dataset_name}", manifest_path)
        
        return df
