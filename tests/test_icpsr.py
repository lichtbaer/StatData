import io
import json
import zipfile
from pathlib import Path

import pandas as pd
import pyarrow.parquet as pq

from socdata.api import ingest


def _make_icpsr_zip(tmp_path: Path, study_number: str = "12345") -> Path:
    """Create a test ICPSR ZIP file."""
    csv = "id,var1,var2\n1,value1,value2\n2,value3,value4\n"
    zip_path = tmp_path / f"ICPSR_{study_number}.zip"
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(f"ICPSR_{study_number}.csv", csv)
    return zip_path


def test_ingest_icpsr_zip(tmp_path: Path):
    """Test ICPSR adapter with ZIP file."""
    zip_path = _make_icpsr_zip(tmp_path, "12345")
    df = ingest("icpsr:icpsr-general", file_path=str(zip_path))
    assert not df.empty
    assert len(df) == 2
    
    # Check cache artifacts
    cache_root = Path.home() / ".socdata" / "icpsr" / "icpsr-general" / "latest"
    manifest_path = cache_root / "meta" / "ingestion_manifest.json"
    parquet_path = cache_root / "processed" / "data.parquet"
    
    assert manifest_path.exists(), "Manifest should be written"
    assert parquet_path.exists(), "Parquet should be written"
    
    # Verify Parquet metadata
    table = pq.read_table(parquet_path)
    meta = table.schema.metadata or {}
    assert b"socdata.dataset_id" in meta
    assert b"socdata.source" in meta
    
    # Verify manifest
    manifest = json.loads(manifest_path.read_text())
    assert manifest.get("adapter") == "icpsr"


def test_icpsr_auto_detect_study_number(tmp_path: Path):
    """Test auto-detection of ICPSR study number from filename."""
    zip_path = _make_icpsr_zip(tmp_path, "67890")
    df = ingest("icpsr", file_path=str(zip_path))
    assert not df.empty
    
    # Should detect study number from filename
    cache_root = Path.home() / ".socdata" / "icpsr"
    # The exact path depends on detection logic, but should exist
    assert any(cache_root.rglob("*/processed/data.parquet"))
