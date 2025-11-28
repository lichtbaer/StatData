import json
from pathlib import Path

import pandas as pd
import pyarrow.parquet as pq

from socdata.api import ingest


def _make_gss_dta(tmp_path: Path) -> Path:
    """Create a mock GSS Stata file."""
    csv = "year,sex,age,income\n2022,M,35,50000\n2022,F,40,60000\n"
    dta_path = tmp_path / "GSS2022.dta"
    # In real scenario, this would be a proper Stata .dta file
    # For testing, we'll use CSV format and let the parser handle it
    dta_path.write_text(csv)
    return dta_path


def test_ingest_gss_file(tmp_path: Path):
    """Test GSS file ingestion."""
    dta_path = _make_gss_dta(tmp_path)
    # Use CSV instead since we can't easily create binary Stata files in tests
    csv_path = tmp_path / "GSS2022.csv"
    csv_path.write_text("year,sex,age,income\n2022,M,35,50000\n2022,F,40,60000\n")
    
    df = ingest("gss:gss-2022", file_path=str(csv_path))
    assert not df.empty
    # Check cache artifacts
    cache_root = Path.home() / ".socdata" / "gss" / "gss-2022" / "latest"
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
    assert manifest.get("adapter") == "gss"
    assert manifest.get("dataset_id") == "gss:gss-2022"


def test_gss_list_datasets():
    """Test GSS adapter list_datasets."""
    from socdata.core.registry import list_datasets
    
    datasets = list_datasets(source="gss")
    assert len(datasets) > 0
    assert any("gss" in ds.id for ds in datasets)


def test_gss_load_with_filters(tmp_path: Path):
    """Test GSS load with filters."""
    csv_path = tmp_path / "GSS2022.csv"
    csv_path.write_text("year,sex,age,income\n2022,M,35,50000\n2022,F,40,60000\n2021,M,30,45000\n")
    
    # First ingest
    ingest("gss:gss-2022", file_path=str(csv_path))
    
    # Then load with filters
    from socdata.api import load
    
    df = load("gss:gss-2022", filters={"year": 2022})
    assert not df.empty
    assert all(df["year"] == 2022)
