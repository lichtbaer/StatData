from __future__ import annotations

import zipfile
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd

from .base import BaseAdapter
from ..core.types import DatasetSummary
from ..core.models import IngestionManifest
from ..core.storage import get_dataset_dir
from ..core.download import download_file


class ESSAdapter(BaseAdapter):
    """
    Adapter for European Social Survey (ESS).
    
    ESS data is available from https://www.europeansocialsurvey.org/
    This adapter supports ingestion from ESS data files (SPSS, Stata, or CSV formats).
    """

    ESS_BASE_URL = "https://www.europeansocialsurvey.org/download.html"

    def list_datasets(self) -> List[DatasetSummary]:
        """List available ESS datasets."""
        return [
            DatasetSummary(
                id="ess:ess-round-1",
                source="ess",
                title="ESS Round 1 (2002-2003)"
            ),
            DatasetSummary(
                id="ess:ess-round-2",
                source="ess",
                title="ESS Round 2 (2004-2005)"
            ),
            DatasetSummary(
                id="ess:ess-round-3",
                source="ess",
                title="ESS Round 3 (2006-2007)"
            ),
            DatasetSummary(
                id="ess:ess-round-4",
                source="ess",
                title="ESS Round 4 (2008-2009)"
            ),
            DatasetSummary(
                id="ess:ess-round-5",
                source="ess",
                title="ESS Round 5 (2010-2011)"
            ),
            DatasetSummary(
                id="ess:ess-round-6",
                source="ess",
                title="ESS Round 6 (2012-2013)"
            ),
            DatasetSummary(
                id="ess:ess-round-7",
                source="ess",
                title="ESS Round 7 (2014-2015)"
            ),
            DatasetSummary(
                id="ess:ess-round-8",
                source="ess",
                title="ESS Round 8 (2016-2017)"
            ),
            DatasetSummary(
                id="ess:ess-round-9",
                source="ess",
                title="ESS Round 9 (2018-2019)"
            ),
            DatasetSummary(
                id="ess:ess-round-10",
                source="ess",
                title="ESS Round 10 (2020-2022)"
            ),
            DatasetSummary(
                id="ess:ess-cumulative",
                source="ess",
                title="ESS Cumulative File (all rounds)"
            ),
        ]

    def load(self, dataset_id: str, *, filters: Dict[str, Any]) -> pd.DataFrame:
        """
        Load ESS dataset from cache.
        
        Args:
            dataset_id: Format 'ess:ess-round-N' or 'ess:ess-cumulative'
            filters: Optional filters (e.g., {'cntry': 'DE', 'round': 10})
        
        Returns:
            DataFrame with ESS data
        """
        parts = dataset_id.split(":")
        if len(parts) < 2:
            raise ValueError(f"Invalid ESS dataset ID: {dataset_id}. Expected format: ess:ess-round-N")
        
        dataset_name = parts[1]
        version = parts[2] if len(parts) > 2 else "latest"
        
        # Check cache first
        cache_dir = get_dataset_dir("ess", dataset_name, version)
        parquet_path = cache_dir / "processed" / "data.parquet"
        
        if parquet_path.exists():
            df = pd.read_parquet(parquet_path)
            # Apply filters if provided
            if filters:
                df = self._apply_filters(df, filters)
            return df
        
        # If not cached, require manual ingestion
        raise NotImplementedError(
            f"ESS dataset '{dataset_id}' not found in cache. "
            "Please use ingest() with a local ESS data file first. "
            "ESS data requires registration and download from https://www.europeansocialsurvey.org/"
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

    def _detect_ess_round(self, file_path: Path) -> str:
        """
        Try to detect ESS round from filename or content.
        
        Common patterns:
        - ESS1e06_4.sav (Round 1, edition 6, version 4)
        - ESS10e01_1.sav (Round 10, edition 1, version 1)
        - ESS_cumulative_edition_1.sav
        """
        name = file_path.stem.upper()
        
        # Check for cumulative
        if "CUMULATIVE" in name:
            return "ess-cumulative"
        
        # Check for round pattern (ESS followed by digits)
        import re
        round_match = re.search(r"ESS(\d+)", name)
        if round_match:
            round_num = round_match.group(1)
            return f"ess-round-{round_num}"
        
        return "ess-unknown"

    def _extract_ess_zip(self, zip_path: Path, extract_dir: Path) -> Path:
        """
        Extract ESS ZIP and find the main data file.
        
        ESS ZIPs typically contain:
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
                f"No supported data files (.dta/.sav/.zsav/.csv/.tsv) found in ESS ZIP: {zip_path}"
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
        Ingest ESS dataset from local file.
        
        Args:
            dataset_id: Format 'ess:ess-round-N' or None (auto-detected)
            file_path: Path to ESS data file (.sav, .dta, .csv) or ZIP archive
        
        Returns:
            Normalized DataFrame
        """
        path = Path(file_path)
        
        # Handle URL downloads
        if file_path.startswith(("http://", "https://")):
            cache_dir = get_dataset_dir("ess", "downloads", "temp")
            path = cache_dir / Path(file_path).name
            if not path.exists():
                download_file(file_path, path)
        
        if not path.exists():
            raise FileNotFoundError(f"ESS data file not found: {path}")
        
        # Determine dataset name and version
        if dataset_id:
            parts = dataset_id.split(":")
            dataset_name = parts[1] if len(parts) > 1 else "ess-unknown"
            version = parts[2] if len(parts) > 2 else "latest"
        else:
            # Auto-detect from filename
            if path.suffix.lower() == ".zip":
                # Will detect after extraction
                dataset_name = "ess-unknown"
            else:
                dataset_name = self._detect_ess_round(path)
            version = "latest"
        
        # Handle ZIP files
        if path.suffix.lower() == ".zip":
            extract_dir = path.parent / f"{path.stem}_extracted"
            target_file = self._extract_ess_zip(path, extract_dir)
            if not dataset_id or dataset_name == "ess-unknown":
                dataset_name = self._detect_ess_round(target_file)
        else:
            target_file = path
            if not dataset_id or dataset_name == "ess-unknown":
                dataset_name = self._detect_ess_round(target_file)
        
        # Read with metadata when possible
        df, meta = self._read_table_with_meta_fallback(target_file)
        
        # Normalize
        df = self._normalize(df)
        
        # Write to cache
        cache_dir = get_dataset_dir("ess", dataset_name, version)
        manifest = IngestionManifest(
            timestamp=pd.Timestamp.utcnow().to_pydatetime(),
            adapter="ess",
            parameters={
                "file_path": str(path),
                "target": str(target_file),
                "dataset_name": dataset_name,
                "version": version,
            },
            source_hashes={},
            transforms=["lowercase_columns", "strip_object_columns"],
            dataset_id=f"ess:{dataset_name}",
            source="ess",
            license="ESS data use agreement required - see https://www.europeansocialsurvey.org/",
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
            dataset_id=f"ess:{dataset_name}",
            source="ess",
            adapter="ess",
            manifest_path=manifest_path,
            variable_labels=manifest.variable_labels,
            value_labels=manifest.value_labels,
        )
        
        # Index the dataset
        self._index_dataset_safe(f"ess:{dataset_name}", manifest_path)
        
        return df
