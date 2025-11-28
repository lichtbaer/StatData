import io
import json
import zipfile
from pathlib import Path

import pandas as pd
import pyarrow.parquet as pq

from socdata.api import ingest


def _make_soep_odf_zip(tmp_path: Path) -> Path:
    """Create a mock SOEP ODF ZIP file with a Stata data file."""
    csv = "id,income,age\n1,50000,35\n2,60000,40\n"
    zip_path = tmp_path / "soep_core.zip"
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("soep_data.dta", csv)  # Simplified - real ODF would have .dta binary
        zf.writestr("README.txt", "SOEP Core Data")
    return zip_path


def test_ingest_soep_odf_zip(tmp_path: Path):
    """Test SOEP ODF ZIP ingestion."""
    zip_path = _make_soep_odf_zip(tmp_path)
    df = ingest("soep:soep-core", file_path=str(zip_path))
    assert not df.empty
    # Check cache artifacts
    cache_root = Path.home() / ".socdata" / "soep" / "soep-core" / "latest"
    manifest_path = cache_root / "meta" / "ingestion_manifest.json"
    parquet_path = cache_root / "processed" / "data.parquet"
    assert manifest_path.exists(), "Manifest should be written"
    assert parquet_path.exists(), "Parquet should be written"
    # Verify Parquet metadata includes socdata keys
    table = pq.read_table(parquet_path)
    meta = table.schema.metadata or {}
    assert b"socdata.variable_labels" in meta
    assert b"socdata.value_labels" in meta
    # Manifest JSON loads
    manifest = json.loads(manifest_path.read_text())
    assert manifest.get("adapter") == "soep"
    assert manifest.get("dataset_id") == "soep:soep-core"


def test_soep_list_datasets():
    """Test SOEP adapter list_datasets."""
    from socdata.core.registry import list_datasets
    
    datasets = list_datasets(source="soep")
    assert len(datasets) > 0
    assert any(ds.id == "soep:soep-core" for ds in datasets)
