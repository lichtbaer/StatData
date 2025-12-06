"""Tests for socdata.api module."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from socdata.api import load, ingest
from socdata.core.exceptions import AdapterNotFoundError, DatasetNotFoundError, ParserError


def test_load_success(tmp_path, monkeypatch):
    """Test successful dataset loading."""
    monkeypatch.setenv("SOCDATA_CACHE_DIR", str(tmp_path))
    
    # Mock adapter
    mock_adapter = MagicMock()
    mock_df = pd.DataFrame({"col1": [1, 2, 3], "col2": [4, 5, 6]})
    mock_adapter.load.return_value = mock_df
    
    with patch("socdata.api.resolve_adapter", return_value=mock_adapter):
        result = load("test:dataset1", filters={"key": "value"})
        
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 3
        mock_adapter.load.assert_called_once_with("test:dataset1", filters={"key": "value"})


def test_load_adapter_not_found():
    """Test load with non-existent adapter."""
    with patch("socdata.api.resolve_adapter", side_effect=AdapterNotFoundError("Adapter not found")):
        with pytest.raises(DatasetNotFoundError, match="Dataset not found"):
            load("unknown:dataset")


def test_load_dataset_load_fails():
    """Test load when adapter.load() fails."""
    mock_adapter = MagicMock()
    mock_adapter.load.side_effect = Exception("Load failed")
    
    with patch("socdata.api.resolve_adapter", return_value=mock_adapter):
        with pytest.raises(DatasetNotFoundError, match="Failed to load dataset"):
            load("test:dataset1")


def test_load_with_language(tmp_path, monkeypatch):
    """Test load with language parameter for i18n."""
    monkeypatch.setenv("SOCDATA_CACHE_DIR", str(tmp_path))
    
    # Create mock manifest with labels
    manifest_dir = tmp_path / "test" / "dataset1" / "latest" / "meta"
    manifest_dir.mkdir(parents=True)
    manifest_file = manifest_dir / "ingestion_manifest.json"
    manifest_data = {
        "variable_labels": {"col1": "Column 1", "col2": "Column 2"},
        "value_labels": {"col1": {"1": "Value 1", "2": "Value 2"}},
    }
    import json
    manifest_file.write_text(json.dumps(manifest_data))
    
    # Mock adapter
    mock_adapter = MagicMock()
    mock_df = pd.DataFrame({"col1": [1, 2], "col2": [3, 4]})
    mock_adapter.load.return_value = mock_df
    
    with patch("socdata.api.resolve_adapter", return_value=mock_adapter):
        # Should not raise even if i18n fails
        result = load("test:dataset1", language="de")
        assert isinstance(result, pd.DataFrame)


def test_load_invalid_dataset_id():
    """Test load with invalid dataset_id format."""
    with pytest.raises(ValueError, match="dataset_id must be a non-empty string"):
        load("")
    
    with pytest.raises(ValueError, match="Invalid dataset_id format"):
        load("invalid_format")


def test_load_invalid_language(tmp_path, monkeypatch):
    """Test load with invalid language code."""
    monkeypatch.setenv("SOCDATA_CACHE_DIR", str(tmp_path))
    
    mock_adapter = MagicMock()
    mock_df = pd.DataFrame({"col1": [1, 2]})
    mock_adapter.load.return_value = mock_df
    
    with patch("socdata.api.resolve_adapter", return_value=mock_adapter):
        # Should not raise, just log warning
        result = load("test:dataset1", language="invalid")
        assert isinstance(result, pd.DataFrame)


def test_ingest_success(tmp_path):
    """Test successful dataset ingestion."""
    # Create a test file
    test_file = tmp_path / "test.csv"
    test_file.write_text("col1,col2\n1,2\n3,4")
    
    # Mock adapter
    mock_adapter = MagicMock()
    mock_df = pd.DataFrame({"col1": [1, 3], "col2": [2, 4]})
    mock_adapter.ingest.return_value = mock_df
    
    with patch("socdata.api.resolve_adapter", return_value=mock_adapter):
        result = ingest("manual", file_path=str(test_file))
        
        assert isinstance(result, pd.DataFrame)
        mock_adapter.ingest.assert_called_once_with("manual", file_path=str(test_file))


def test_ingest_file_not_found():
    """Test ingest with non-existent file."""
    with pytest.raises(FileNotFoundError, match="File not found"):
        ingest("manual", file_path="/nonexistent/file.csv")


def test_ingest_adapter_not_found(tmp_path):
    """Test ingest with non-existent adapter."""
    test_file = tmp_path / "test.csv"
    test_file.write_text("col1,col2\n1,2")
    
    with patch("socdata.api.resolve_adapter", side_effect=AdapterNotFoundError("Adapter not found")):
        with pytest.raises(AdapterNotFoundError):
            ingest("unknown", file_path=str(test_file))


def test_ingest_not_implemented(tmp_path):
    """Test ingest when adapter doesn't support ingest."""
    test_file = tmp_path / "test.csv"
    test_file.write_text("col1,col2\n1,2")
    
    mock_adapter = MagicMock()
    mock_adapter.ingest.side_effect = NotImplementedError("Not supported")
    
    with patch("socdata.api.resolve_adapter", return_value=mock_adapter):
        with pytest.raises(ParserError, match="Ingest not supported"):
            ingest("test", file_path=str(test_file))


def test_ingest_parser_error(tmp_path):
    """Test ingest when parsing fails."""
    test_file = tmp_path / "test.csv"
    test_file.write_text("invalid,data")
    
    mock_adapter = MagicMock()
    mock_adapter.ingest.side_effect = Exception("Parse error")
    
    with patch("socdata.api.resolve_adapter", return_value=mock_adapter):
        with pytest.raises(ParserError, match="Failed to ingest"):
            ingest("test", file_path=str(test_file))
