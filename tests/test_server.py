"""Tests for socdata.server module."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest
from fastapi.testclient import TestClient

from socdata.core.exceptions import AdapterNotFoundError, DatasetNotFoundError, ParserError
from socdata.server import app

client = TestClient(app)


def test_root():
    """Test root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "SocData API"
    assert data["version"] == "0.1.0"
    assert "endpoints" in data


def test_get_datasets_all(tmp_path, monkeypatch):
    """Test GET /datasets endpoint without source filter."""
    monkeypatch.setenv("SOCDATA_CACHE_DIR", str(tmp_path))
    
    response = client.get("/datasets")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    if data:
        assert "id" in data[0]
        assert "source" in data[0]
        assert "title" in data[0]


def test_get_datasets_with_source(tmp_path, monkeypatch):
    """Test GET /datasets endpoint with source filter."""
    monkeypatch.setenv("SOCDATA_CACHE_DIR", str(tmp_path))
    
    response = client.get("/datasets?source=eurostat")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    if data:
        assert all(ds["source"] == "eurostat" for ds in data)


def test_search_basic(tmp_path, monkeypatch):
    """Test GET /search endpoint."""
    monkeypatch.setenv("SOCDATA_CACHE_DIR", str(tmp_path))
    
    response = client.get("/search?q=test")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_search_with_source(tmp_path, monkeypatch):
    """Test GET /search endpoint with source filter."""
    monkeypatch.setenv("SOCDATA_CACHE_DIR", str(tmp_path))
    
    response = client.get("/search?q=test&source=eurostat")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_search_with_variable(tmp_path, monkeypatch):
    """Test GET /search endpoint with variable filter."""
    monkeypatch.setenv("SOCDATA_CACHE_DIR", str(tmp_path))
    
    response = client.get("/search?q=test&variable=age")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_search_with_limit(tmp_path, monkeypatch):
    """Test GET /search endpoint with limit."""
    monkeypatch.setenv("SOCDATA_CACHE_DIR", str(tmp_path))
    
    response = client.get("/search?q=test&limit=5")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) <= 5


def test_get_dataset_info_found(tmp_path, monkeypatch):
    """Test GET /datasets/{dataset_id}/info endpoint with existing dataset."""
    monkeypatch.setenv("SOCDATA_CACHE_DIR", str(tmp_path))
    
    # Mock index
    mock_info = {
        "id": "test:dataset1",
        "source": "test",
        "title": "Test Dataset",
        "description": "A test dataset",
        "license": "MIT",
        "access_mode": "direct",
        "variable_labels": {"var1": "Variable 1"},
        "created_at": "2024-01-01",
        "updated_at": "2024-01-01",
    }
    
    with patch("socdata.server.get_index") as mock_index:
        mock_index.return_value.get_dataset_info.return_value = mock_info
        
        response = client.get("/datasets/test:dataset1/info")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "test:dataset1"
        assert data["title"] == "Test Dataset"


def test_get_dataset_info_not_found(tmp_path, monkeypatch):
    """Test GET /datasets/{dataset_id}/info endpoint with non-existent dataset."""
    monkeypatch.setenv("SOCDATA_CACHE_DIR", str(tmp_path))
    
    with patch("socdata.server.get_index") as mock_index:
        mock_index.return_value.get_dataset_info.return_value = None
        
        response = client.get("/datasets/nonexistent:dataset/info")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


def test_get_dataset_info_error(tmp_path, monkeypatch):
    """Test GET /datasets/{dataset_id}/info endpoint with error."""
    monkeypatch.setenv("SOCDATA_CACHE_DIR", str(tmp_path))
    
    with patch("socdata.server.get_index", side_effect=Exception("Index error")):
        response = client.get("/datasets/test:dataset1/info")
        assert response.status_code == 500


def test_load_dataset_json(tmp_path, monkeypatch):
    """Test POST /datasets/{dataset_id}/load endpoint with JSON format."""
    monkeypatch.setenv("SOCDATA_CACHE_DIR", str(tmp_path))
    
    mock_df = pd.DataFrame({"col1": [1, 2, 3], "col2": [4, 5, 6]})
    
    with patch("socdata.server.load", return_value=mock_df):
        response = client.post("/datasets/test:dataset1/load?format=json")
        assert response.status_code == 200
        data = response.json()
        assert data["dataset_id"] == "test:dataset1"
        assert "rows" in data
        assert "columns" in data
        assert "data" in data


def test_load_dataset_with_filters_json(tmp_path, monkeypatch):
    """Test POST /datasets/{dataset_id}/load endpoint with filters."""
    monkeypatch.setenv("SOCDATA_CACHE_DIR", str(tmp_path))
    
    mock_df = pd.DataFrame({"col1": [1, 2]})
    
    with patch("socdata.server.load", return_value=mock_df):
        filters = '{"key": "value"}'
        response = client.post(f"/datasets/test:dataset1/load?filters={filters}&format=json")
        assert response.status_code == 200
        data = response.json()
        assert data["dataset_id"] == "test:dataset1"


def test_load_dataset_csv(tmp_path, monkeypatch):
    """Test POST /datasets/{dataset_id}/load endpoint with CSV format."""
    monkeypatch.setenv("SOCDATA_CACHE_DIR", str(tmp_path))
    
    mock_df = pd.DataFrame({"col1": [1, 2], "col2": [3, 4]})
    
    with patch("socdata.server.load", return_value=mock_df):
        response = client.post("/datasets/test:dataset1/load?format=csv")
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/csv; charset=utf-8"
        assert "col1" in response.text


def test_load_dataset_parquet(tmp_path, monkeypatch):
    """Test POST /datasets/{dataset_id}/load endpoint with Parquet format."""
    monkeypatch.setenv("SOCDATA_CACHE_DIR", str(tmp_path))
    
    mock_df = pd.DataFrame({"col1": [1, 2], "col2": [3, 4]})
    
    with patch("socdata.server.load", return_value=mock_df):
        response = client.post("/datasets/test:dataset1/load?format=parquet")
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/octet-stream"
        # Verify it's valid parquet by trying to read it
        import io
        import pyarrow.parquet as pq
        parquet_data = io.BytesIO(response.content)
        table = pq.read_table(parquet_data)
        assert len(table) == 2


def test_load_dataset_not_found(tmp_path, monkeypatch):
    """Test POST /datasets/{dataset_id}/load endpoint with non-existent dataset."""
    monkeypatch.setenv("SOCDATA_CACHE_DIR", str(tmp_path))
    
    with patch("socdata.server.load", side_effect=KeyError("Dataset not found")):
        response = client.post("/datasets/nonexistent:dataset/load")
        assert response.status_code == 404


def test_load_dataset_error(tmp_path, monkeypatch):
    """Test POST /datasets/{dataset_id}/load endpoint with error."""
    monkeypatch.setenv("SOCDATA_CACHE_DIR", str(tmp_path))
    
    with patch("socdata.server.load", side_effect=Exception("Load error")):
        response = client.post("/datasets/test:dataset1/load")
        assert response.status_code == 500


def test_ingest_json(tmp_path, monkeypatch):
    """Test POST /ingest endpoint with JSON format."""
    monkeypatch.setenv("SOCDATA_CACHE_DIR", str(tmp_path))
    
    # Create test file
    test_file = tmp_path / "test.csv"
    test_file.write_text("col1,col2\n1,2\n3,4")
    
    mock_df = pd.DataFrame({"col1": [1, 3], "col2": [2, 4]})
    
    with patch("socdata.server.ingest", return_value=mock_df):
        response = client.post(
            "/ingest",
            json={
                "dataset_id": "manual",
                "file_path": str(test_file),
                "format": "json",
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["dataset_id"] == "manual"
        assert "rows" in data
        assert "columns" in data


def test_ingest_csv(tmp_path, monkeypatch):
    """Test POST /ingest endpoint with CSV format."""
    monkeypatch.setenv("SOCDATA_CACHE_DIR", str(tmp_path))
    
    test_file = tmp_path / "test.csv"
    test_file.write_text("col1,col2\n1,2")
    mock_df = pd.DataFrame({"col1": [1], "col2": [2]})
    
    with patch("socdata.server.ingest", return_value=mock_df):
        response = client.post(
            "/ingest",
            json={
                "dataset_id": "manual",
                "file_path": str(test_file),
                "format": "csv",
            }
        )
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/csv; charset=utf-8"


def test_ingest_parquet(tmp_path, monkeypatch):
    """Test POST /ingest endpoint with Parquet format."""
    monkeypatch.setenv("SOCDATA_CACHE_DIR", str(tmp_path))
    
    test_file = tmp_path / "test.csv"
    test_file.write_text("col1,col2\n1,2")
    mock_df = pd.DataFrame({"col1": [1], "col2": [2]})
    
    with patch("socdata.server.ingest", return_value=mock_df):
        response = client.post(
            "/ingest",
            json={
                "dataset_id": "manual",
                "file_path": str(test_file),
                "format": "parquet",
            }
        )
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/octet-stream"


def test_ingest_file_not_found(tmp_path, monkeypatch):
    """Test POST /ingest endpoint with non-existent file."""
    monkeypatch.setenv("SOCDATA_CACHE_DIR", str(tmp_path))
    
    response = client.post(
        "/ingest",
        json={
            "dataset_id": "manual",
            "file_path": str(tmp_path / "nonexistent.csv"),
            "format": "json",
        }
    )
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_ingest_error(tmp_path, monkeypatch):
    """Test POST /ingest endpoint with error."""
    monkeypatch.setenv("SOCDATA_CACHE_DIR", str(tmp_path))
    
    test_file = tmp_path / "test.csv"
    test_file.write_text("col1,col2\n1,2")
    
    with patch("socdata.server.ingest", side_effect=Exception("Ingest error")):
        response = client.post(
            "/ingest",
            json={
                "dataset_id": "manual",
                "file_path": str(test_file),
                "format": "json",
            }
        )
        assert response.status_code == 500


def test_rebuild_index_success(tmp_path, monkeypatch):
    """Test POST /rebuild-index endpoint success."""
    monkeypatch.setenv("SOCDATA_CACHE_DIR", str(tmp_path))
    
    with patch("socdata.server.get_index") as mock_index:
        mock_index.return_value.rebuild_index.return_value = None
        
        response = client.post("/rebuild-index")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"


def test_rebuild_index_error(tmp_path, monkeypatch):
    """Test POST /rebuild-index endpoint with error."""
    monkeypatch.setenv("SOCDATA_CACHE_DIR", str(tmp_path))
    
    with patch("socdata.server.get_index", side_effect=Exception("Index error")):
        response = client.post("/rebuild-index")
        assert response.status_code == 500
