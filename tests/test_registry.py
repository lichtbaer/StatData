"""Tests for socdata.core.registry module."""

from unittest.mock import MagicMock, patch

import pytest

from socdata.core.exceptions import AdapterNotFoundError
from socdata.core.registry import (
    index_dataset_from_manifest,
    list_datasets,
    resolve_adapter,
    search_datasets,
    search_datasets_advanced,
)
from socdata.core.types import DatasetSummary


def test_resolve_adapter_with_dataset_id():
    """Test resolving adapter from dataset ID."""
    adapter = resolve_adapter("eurostat:une_rt_m")
    assert adapter is not None
    assert hasattr(adapter, "load")
    assert hasattr(adapter, "list_datasets")


def test_resolve_adapter_with_adapter_id():
    """Test resolving adapter from adapter ID."""
    adapter = resolve_adapter("manual")
    assert adapter is not None
    assert hasattr(adapter, "load")
    assert hasattr(adapter, "list_datasets")


def test_resolve_adapter_not_found():
    """Test resolving non-existent adapter."""
    with pytest.raises(AdapterNotFoundError, match="Unknown adapter"):
        resolve_adapter("nonexistent:dataset")


def test_list_datasets_all():
    """Test listing all datasets."""
    datasets = list_datasets()
    assert isinstance(datasets, list)
    assert len(datasets) > 0
    assert all(isinstance(ds, DatasetSummary) for ds in datasets)


def test_list_datasets_filtered():
    """Test listing datasets filtered by source."""
    datasets = list_datasets(source="eurostat")
    assert isinstance(datasets, list)
    assert all(ds.source == "eurostat" for ds in datasets)


def test_list_datasets_unknown_source():
    """Test listing datasets for unknown source."""
    datasets = list_datasets(source="nonexistent")
    assert datasets == []


def test_search_datasets_basic(tmp_path, monkeypatch):
    """Test basic search functionality."""
    monkeypatch.setenv("SOCDATA_CACHE_DIR", str(tmp_path))
    
    # Search should work even if index fails
    results = search_datasets("unemployment")
    assert isinstance(results, list)
    # Results might be empty if no datasets match, but should not raise


def test_search_datasets_with_source(tmp_path, monkeypatch):
    """Test search with source filter."""
    monkeypatch.setenv("SOCDATA_CACHE_DIR", str(tmp_path))
    
    results = search_datasets("test", source="eurostat")
    assert isinstance(results, list)
    # All results should be from eurostat if any
    if results:
        assert all(ds.source == "eurostat" for ds in results)


def test_search_datasets_no_index(tmp_path, monkeypatch):
    """Test search without using index."""
    monkeypatch.setenv("SOCDATA_CACHE_DIR", str(tmp_path))
    
    results = search_datasets("test", use_index=False)
    assert isinstance(results, list)


def test_search_datasets_index_fails(tmp_path, monkeypatch):
    """Test search when index fails and falls back."""
    monkeypatch.setenv("SOCDATA_CACHE_DIR", str(tmp_path))
    
    # Mock index to raise exception
    with patch("socdata.core.registry.get_index", side_effect=Exception("Index error")):
        results = search_datasets("test")
        # Should fall back to simple search
        assert isinstance(results, list)


def test_search_datasets_advanced(tmp_path, monkeypatch):
    """Test advanced search functionality."""
    monkeypatch.setenv("SOCDATA_CACHE_DIR", str(tmp_path))
    
    results = search_datasets_advanced(query="test", source="eurostat")
    assert isinstance(results, list)


def test_search_datasets_advanced_with_variable(tmp_path, monkeypatch):
    """Test advanced search with variable filter."""
    monkeypatch.setenv("SOCDATA_CACHE_DIR", str(tmp_path))
    
    results = search_datasets_advanced(variable_name="age")
    assert isinstance(results, list)


def test_search_datasets_advanced_index_fails(tmp_path, monkeypatch):
    """Test advanced search when index fails."""
    monkeypatch.setenv("SOCDATA_CACHE_DIR", str(tmp_path))
    
    with patch("socdata.core.registry.get_index", side_effect=Exception("Index error")):
        results = search_datasets_advanced(query="test")
        # Should fall back to simple search
        assert isinstance(results, list)


def test_index_dataset_from_manifest(tmp_path, monkeypatch):
    """Test indexing dataset from manifest."""
    monkeypatch.setenv("SOCDATA_CACHE_DIR", str(tmp_path))
    
    # Create a test manifest
    manifest_dir = tmp_path / "test" / "dataset1" / "latest" / "meta"
    manifest_dir.mkdir(parents=True)
    manifest_file = manifest_dir / "ingestion_manifest.json"
    
    import json
    manifest_data = {
        "dataset_id": "test:dataset1",
        "source": "test",
        "variable_labels": {"var1": "Variable 1"},
        "value_labels": {"var1": {"1": "Value 1"}},
        "license": "MIT",
        "adapter": "manual",
    }
    manifest_file.write_text(json.dumps(manifest_data))
    
    # Should not raise
    index_dataset_from_manifest("test:dataset1", str(manifest_file))


def test_index_dataset_from_manifest_missing_file(tmp_path, monkeypatch):
    """Test indexing with missing manifest file."""
    monkeypatch.setenv("SOCDATA_CACHE_DIR", str(tmp_path))
    
    # Should not raise, just log warning
    index_dataset_from_manifest("test:dataset1", "/nonexistent/manifest.json")


def test_index_dataset_from_manifest_invalid_json(tmp_path, monkeypatch):
    """Test indexing with invalid JSON manifest."""
    monkeypatch.setenv("SOCDATA_CACHE_DIR", str(tmp_path))
    
    # Create invalid JSON file
    manifest_file = tmp_path / "invalid.json"
    manifest_file.write_text("invalid json {")
    
    # Should not raise, just log warning
    index_dataset_from_manifest("test:dataset1", str(manifest_file))
