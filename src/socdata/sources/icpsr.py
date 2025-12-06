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


class ICPSRAdapter(BaseAdapter):
    """
    Adapter for ICPSR (Inter-university Consortium for Political and Social Research).
    
    ICPSR data is available from https://www.icpsr.umich.edu/
    This adapter supports ingestion from ICPSR data files (SPSS, Stata, or CSV formats).
    """

    ICPSR_BASE_URL = "https://www.icpsr.umich.edu/"

    def list_datasets(self) -> List[DatasetSummary]:
        """List available ICPSR datasets."""
        return [
            DatasetSummary(
                id="icpsr:icpsr-general",
                source="icpsr",
                title="ICPSR General Archive (various studies)"
            ),
            DatasetSummary(
                id="icpsr:anes",
                source="icpsr",
                title="American National Election Studies (ANES)"
            ),
            DatasetSummary(
                id="icpsr:world-values-survey",
                source="icpsr",
                title="World Values Survey (via ICPSR)"
            ),
            DatasetSummary(
                id="icpsr:general-social-survey",
                source="icpsr",
                title="General Social Survey (GSS via ICPSR)"
            ),
            DatasetSummary(
                id="icpsr:panel-study-income-dynamics",
                source="icpsr",
                title="Panel Study of Income Dynamics (PSID)"
            ),
            DatasetSummary(
                id="icpsr:national-longitudinal-survey",
                source="icpsr",
                title="National Longitudinal Survey (NLS)"
            ),
            DatasetSummary(
                id="icpsr:health-retirement-study",
                source="icpsr",
                title="Health and Retirement Study (HRS)"
            ),
            DatasetSummary(
                id="icpsr:add-health",
                source="icpsr",
                title="National Longitudinal Study of Adolescent to Adult Health (Add Health)"
            ),
            DatasetSummary(
                id="icpsr:current-population-survey",
                source="icpsr",
                title="Current Population Survey (CPS)"
            ),
            DatasetSummary(
                id="icpsr:behavioral-risk-factor-surveillance",
                source="icpsr",
                title="Behavioral Risk Factor Surveillance System (BRFSS)"
            ),
        ]

    def load(self, dataset_id: str, *, filters: Dict[str, Any]) -> pd.DataFrame:
        """
        Load ICPSR dataset from cache.
        
        Args:
            dataset_id: Format 'icpsr:study-name' or 'icpsr:study-id'
            filters: Optional filters
        
        Returns:
            DataFrame with ICPSR data
        """
        parts = dataset_id.split(":")
        if len(parts) < 2:
            raise ValueError(f"Invalid ICPSR dataset ID: {dataset_id}. Expected format: icpsr:study-name")
        
        dataset_name = parts[1]
        version = parts[2] if len(parts) > 2 else "latest"
        
        # Check cache first
        cache_dir = get_dataset_dir("icpsr", dataset_name, version)
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
            f"ICPSR dataset '{dataset_id}' not found in cache. "
            "Please use ingest() with a local ICPSR data file first. "
            "ICPSR data requires registration and download from https://www.icpsr.umich.edu/"
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

    def _detect_icpsr_study(self, file_path: Path) -> str:
        """
        Try to detect ICPSR study from filename or content.
        
        Common patterns:
        - ICPSR_XXXXX.zip (study number)
        - anes_2020.dta (ANES study)
        - wvs_wave7.sav (World Values Survey)
        """
        name = file_path.stem.upper()
        
        # Check for ICPSR study number pattern (5 digits)
        study_match = re.search(r"ICPSR[_\s]?(\d{5})", name)
        if study_match:
            return f"icpsr-{study_match.group(1)}"
        
        # Check for ANES
        if "ANES" in name:
            year_match = re.search(r"(\d{4})", name)
            if year_match:
                return f"anes-{year_match.group(1)}"
            return "anes"
        
        # Check for WVS
        if "WVS" in name or "WORLD.VALUES" in name:
            wave_match = re.search(r"WAVE[_\s]?(\d+)", name)
            if wave_match:
                return f"wvs-wave{wave_match.group(1)}"
            return "world-values-survey"
        
        return "icpsr-general"

    def _extract_icpsr_zip(self, zip_path: Path, extract_dir: Path) -> Path:
        """
        Extract ICPSR ZIP and find the main data file.
        
        ICPSR ZIPs typically contain:
        - Data files (.sav, .dta, .csv)
        - Documentation files (.pdf, .txt, .doc)
        - Codebooks
        - Setup files
        """
        extract_dir.mkdir(parents=True, exist_ok=True)
        
        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(extract_dir)
        
        # Find data files (prefer SPSS/Stata, then largest CSV)
        candidates: List[tuple[int, Path]] = []
        for p in extract_dir.rglob("*"):
            if p.is_file() and p.suffix.lower() in {".dta", ".sav", ".zsav", ".csv", ".tsv"}:
                # Skip documentation subdirectories
                skip_dirs = ["doc", "documentation", "codebook", "readme", "setup"]
                if any(skip in p.parts for skip in skip_dirs):
                    continue
                # Skip very small files (likely not data)
                if p.stat().st_size < 1024:  # Less than 1KB
                    continue
                candidates.append((p.stat().st_size, p))
        
        if not candidates:
            raise ValueError(
                f"No supported data files (.dta/.sav/.zsav/.csv/.tsv) found in ICPSR ZIP: {zip_path}"
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
        Ingest ICPSR dataset from local file.
        
        Args:
            dataset_id: Format 'icpsr:study-name' or None (auto-detected)
            file_path: Path to ICPSR data file (.sav, .dta, .csv) or ZIP archive
        
        Returns:
            Normalized DataFrame
        """
        path = Path(file_path)
        
        # Handle URL downloads
        if file_path.startswith(("http://", "https://")):
            cache_dir = get_dataset_dir("icpsr", "downloads", "temp")
            path = cache_dir / Path(file_path).name
            if not path.exists():
                download_file(file_path, path)
        
        if not path.exists():
            raise FileNotFoundError(f"ICPSR data file not found: {path}")
        
        # Determine dataset name and version
        if dataset_id:
            parts = dataset_id.split(":")
            dataset_name = parts[1] if len(parts) > 1 else "icpsr-general"
            version = parts[2] if len(parts) > 2 else "latest"
        else:
            # Auto-detect from filename
            if path.suffix.lower() == ".zip":
                # Will detect after extraction
                dataset_name = "icpsr-general"
            else:
                dataset_name = self._detect_icpsr_study(path)
            version = "latest"
        
        # Handle ZIP files
        if path.suffix.lower() == ".zip":
            extract_dir = path.parent / f"{path.stem}_extracted"
            target_file = self._extract_icpsr_zip(path, extract_dir)
            if not dataset_id or dataset_name == "icpsr-general":
                dataset_name = self._detect_icpsr_study(target_file)
        else:
            target_file = path
            if not dataset_id or dataset_name == "icpsr-general":
                dataset_name = self._detect_icpsr_study(target_file)
        
        # Read with metadata when possible
        df, meta = self._read_table_with_meta_fallback(target_file)
        
        # Normalize
        df = self._normalize(df)
        
        # Write to cache
        cache_dir = get_dataset_dir("icpsr", dataset_name, version)
        manifest = IngestionManifest(
            timestamp=pd.Timestamp.utcnow().to_pydatetime(),
            adapter="icpsr",
            parameters={
                "file_path": str(path),
                "target": str(target_file),
                "dataset_name": dataset_name,
                "version": version,
            },
            source_hashes={},
            transforms=["lowercase_columns", "strip_object_columns"],
            dataset_id=f"icpsr:{dataset_name}",
            source="icpsr",
            license="ICPSR data use agreement required - see https://www.icpsr.umich.edu/",
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
            dataset_id=f"icpsr:{dataset_name}",
            source="icpsr",
            adapter="icpsr",
            manifest_path=manifest_path,
            variable_labels=manifest.variable_labels,
            value_labels=manifest.value_labels,
        )
        
        # Index the dataset
        self._index_dataset_safe(f"icpsr:{dataset_name}", manifest_path)
        
        return df
