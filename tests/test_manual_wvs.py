import io
import json
import zipfile
from pathlib import Path

import pandas as pd
import pyarrow.parquet as pq

from socdata.api import ingest


def _make_zip(tmp_path: Path) -> Path:
	csv = "a,b\n1,0\n2,1\n"
	zip_path = tmp_path / "wvs.zip"
	with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
		zf.writestr("WVS_Extract.csv", csv)
	return zip_path


def test_ingest_manual_wvs_zip(tmp_path: Path):
	zip_path = _make_zip(tmp_path)
	df = ingest("manual:wvs", file_path=str(zip_path))
	assert not df.empty
	# Check cache artifacts
	cache_root = Path.home() / ".socdata" / "manual" / "manual_wvs" / "latest"
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
	assert manifest.get("adapter") == "manual"