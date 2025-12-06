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


class ISSPAdapter(BaseAdapter):
    """
    Adapter for ISSP (International Social Survey Programme).
    
    ISSP data is available from https://www.issp.org/
    This adapter supports ingestion from ISSP data files (SPSS, Stata, or CSV formats).
    """

    ISSP_BASE_URL = "https://www.issp.org/"

    def list_datasets(self) -> List[DatasetSummary]:
        """List available ISSP datasets."""
        return [
            DatasetSummary(
                id="issp:issp-1985",
                source="issp",
                title="ISSP 1985 - Role of Government I"
            ),
            DatasetSummary(
                id="issp:issp-1986",
                source="issp",
                title="ISSP 1986 - Social Networks"
            ),
            DatasetSummary(
                id="issp:issp-1987",
                source="issp",
                title="ISSP 1987 - Social Inequality I"
            ),
            DatasetSummary(
                id="issp:issp-1989",
                source="issp",
                title="ISSP 1989 - Work Orientations I"
            ),
            DatasetSummary(
                id="issp:issp-1990",
                source="issp",
                title="ISSP 1990 - Role of Government II"
            ),
            DatasetSummary(
                id="issp:issp-1991",
                source="issp",
                title="ISSP 1991 - Religion I"
            ),
            DatasetSummary(
                id="issp:issp-1992",
                source="issp",
                title="ISSP 1992 - Social Inequality II"
            ),
            DatasetSummary(
                id="issp:issp-1993",
                source="issp",
                title="ISSP 1993 - Environment I"
            ),
            DatasetSummary(
                id="issp:issp-1994",
                source="issp",
                title="ISSP 1994 - Family and Changing Gender Roles I"
            ),
            DatasetSummary(
                id="issp:issp-1995",
                source="issp",
                title="ISSP 1995 - National Identity I"
            ),
            DatasetSummary(
                id="issp:issp-1996",
                source="issp",
                title="ISSP 1996 - Role of Government III"
            ),
            DatasetSummary(
                id="issp:issp-1997",
                source="issp",
                title="ISSP 1997 - Work Orientations II"
            ),
            DatasetSummary(
                id="issp:issp-1998",
                source="issp",
                title="ISSP 1998 - Religion II"
            ),
            DatasetSummary(
                id="issp:issp-1999",
                source="issp",
                title="ISSP 1999 - Social Inequality III"
            ),
            DatasetSummary(
                id="issp:issp-2000",
                source="issp",
                title="ISSP 2000 - Environment II"
            ),
            DatasetSummary(
                id="issp:issp-2001",
                source="issp",
                title="ISSP 2001 - Social Relations and Support Systems"
            ),
            DatasetSummary(
                id="issp:issp-2002",
                source="issp",
                title="ISSP 2002 - Family and Changing Gender Roles II"
            ),
            DatasetSummary(
                id="issp:issp-2003",
                source="issp",
                title="ISSP 2003 - National Identity II"
            ),
            DatasetSummary(
                id="issp:issp-2004",
                source="issp",
                title="ISSP 2004 - Citizenship"
            ),
            DatasetSummary(
                id="issp:issp-2005",
                source="issp",
                title="ISSP 2005 - Work Orientations III"
            ),
            DatasetSummary(
                id="issp:issp-2006",
                source="issp",
                title="ISSP 2006 - Role of Government IV"
            ),
            DatasetSummary(
                id="issp:issp-2007",
                source="issp",
                title="ISSP 2007 - Leisure Time and Sports"
            ),
            DatasetSummary(
                id="issp:issp-2008",
                source="issp",
                title="ISSP 2008 - Religion III"
            ),
            DatasetSummary(
                id="issp:issp-2009",
                source="issp",
                title="ISSP 2009 - Social Inequality IV"
            ),
            DatasetSummary(
                id="issp:issp-2010",
                source="issp",
                title="ISSP 2010 - Environment III"
            ),
            DatasetSummary(
                id="issp:issp-2011",
                source="issp",
                title="ISSP 2011 - Health and Health Care"
            ),
            DatasetSummary(
                id="issp:issp-2012",
                source="issp",
                title="ISSP 2012 - Family and Changing Gender Roles III"
            ),
            DatasetSummary(
                id="issp:issp-2013",
                source="issp",
                title="ISSP 2013 - National Identity III"
            ),
            DatasetSummary(
                id="issp:issp-2014",
                source="issp",
                title="ISSP 2014 - Citizenship II"
            ),
            DatasetSummary(
                id="issp:issp-2015",
                source="issp",
                title="ISSP 2015 - Work Orientations IV"
            ),
            DatasetSummary(
                id="issp:issp-2016",
                source="issp",
                title="ISSP 2016 - Role of Government V"
            ),
            DatasetSummary(
                id="issp:issp-2017",
                source="issp",
                title="ISSP 2017 - Social Networks and Social Resources"
            ),
            DatasetSummary(
                id="issp:issp-2018",
                source="issp",
                title="ISSP 2018 - Religion IV"
            ),
            DatasetSummary(
                id="issp:issp-2019",
                source="issp",
                title="ISSP 2019 - Social Inequality V"
            ),
            DatasetSummary(
                id="issp:issp-2020",
                source="issp",
                title="ISSP 2020 - Environment IV"
            ),
        ]

    def load(self, dataset_id: str, *, filters: Dict[str, Any]) -> pd.DataFrame:
        """
        Load ISSP dataset from cache.
        
        Args:
            dataset_id: Format 'issp:issp-YYYY'
            filters: Optional filters (e.g., {'country': 'DE'})
        
        Returns:
            DataFrame with ISSP data
        """
        parts = dataset_id.split(":")
        if len(parts) < 2:
            raise ValueError(f"Invalid ISSP dataset ID: {dataset_id}. Expected format: issp:issp-YYYY")
        
        dataset_name = parts[1]
        version = parts[2] if len(parts) > 2 else "latest"
        
        # Check cache first
        cache_dir = get_dataset_dir("issp", dataset_name, version)
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
            f"ISSP dataset '{dataset_id}' not found in cache. "
            "Please use ingest() with a local ISSP data file first. "
            "ISSP data requires registration and download from https://www.issp.org/"
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

    def _detect_issp_year(self, file_path: Path) -> str:
        """
        Try to detect ISSP year from filename or content.
        
        Common patterns:
        - ISSP1985.sav
        - ISSP_1990.dta
        - ZA1234_ISSP2000.sav
        """
        name = file_path.stem.upper()
        
        # Check for year pattern (4 digits)
        year_match = re.search(r"(?:ISSP|ZA\d+)[_\s]?(\d{4})", name)
        if year_match:
            year = year_match.group(1)
            return f"issp-{year}"
        
        return "issp-unknown"

    def _extract_issp_zip(self, zip_path: Path, extract_dir: Path) -> Path:
        """
        Extract ISSP ZIP and find the main data file.
        
        ISSP ZIPs typically contain:
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
                f"No supported data files (.dta/.sav/.zsav/.csv/.tsv) found in ISSP ZIP: {zip_path}"
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
        Ingest ISSP dataset from local file.
        
        Args:
            dataset_id: Format 'issp:issp-YYYY' or None (auto-detected)
            file_path: Path to ISSP data file (.sav, .dta, .csv) or ZIP archive
        
        Returns:
            Normalized DataFrame
        """
        path = Path(file_path)
        
        # Handle URL downloads
        if file_path.startswith(("http://", "https://")):
            cache_dir = get_dataset_dir("issp", "downloads", "temp")
            path = cache_dir / Path(file_path).name
            if not path.exists():
                download_file(file_path, path)
        
        if not path.exists():
            raise FileNotFoundError(f"ISSP data file not found: {path}")
        
        # Determine dataset name and version
        if dataset_id:
            parts = dataset_id.split(":")
            dataset_name = parts[1] if len(parts) > 1 else "issp-unknown"
            version = parts[2] if len(parts) > 2 else "latest"
        else:
            # Auto-detect from filename
            if path.suffix.lower() == ".zip":
                # Will detect after extraction
                dataset_name = "issp-unknown"
            else:
                dataset_name = self._detect_issp_year(path)
            version = "latest"
        
        # Handle ZIP files
        if path.suffix.lower() == ".zip":
            extract_dir = path.parent / f"{path.stem}_extracted"
            target_file = self._extract_issp_zip(path, extract_dir)
            if not dataset_id or dataset_name == "issp-unknown":
                dataset_name = self._detect_issp_year(target_file)
        else:
            target_file = path
            if not dataset_id or dataset_name == "issp-unknown":
                dataset_name = self._detect_issp_year(target_file)
        
        # Read with metadata when possible
        df, meta = self._read_table_with_meta_fallback(target_file)
        
        # Normalize
        df = self._normalize(df)
        
        # Write to cache
        cache_dir = get_dataset_dir("issp", dataset_name, version)
        manifest = IngestionManifest(
            timestamp=pd.Timestamp.utcnow().to_pydatetime(),
            adapter="issp",
            parameters={
                "file_path": str(path),
                "target": str(target_file),
                "dataset_name": dataset_name,
                "version": version,
            },
            source_hashes={},
            transforms=["lowercase_columns", "strip_object_columns"],
            dataset_id=f"issp:{dataset_name}",
            source="issp",
            license="ISSP data use agreement required - see https://www.issp.org/",
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
            dataset_id=f"issp:{dataset_name}",
            source="issp",
            adapter="issp",
            manifest_path=manifest_path,
            variable_labels=manifest.variable_labels,
            value_labels=manifest.value_labels,
        )
        
        # Index the dataset
        self._index_dataset_safe(f"issp:{dataset_name}", manifest_path)
        
        return df
