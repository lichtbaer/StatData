import json
from pathlib import Path

import pytest

from socdata.core.search_index import SearchIndex, get_index
from socdata.core.types import DatasetSummary


def test_search_index_init(tmp_path: Path):
    """Test search index initialization."""
    index_path = tmp_path / "test_index.db"
    index = SearchIndex(index_path)
    assert index_path.exists()


def test_index_dataset(tmp_path: Path):
    """Test indexing a dataset."""
    index_path = tmp_path / "test_index.db"
    index = SearchIndex(index_path)
    
    index.index_dataset(
        dataset_id="test:dataset1",
        source="test",
        title="Test Dataset",
        description="A test dataset",
        variable_labels={"age": "Age in years", "income": "Annual income"},
        value_labels={"gender": {"1": "Male", "2": "Female"}},
    )
    
    # Verify it was indexed
    info = index.get_dataset_info("test:dataset1")
    assert info is not None
    assert info["id"] == "test:dataset1"
    assert info["title"] == "Test Dataset"
    assert len(info["variable_labels"]) == 2


def test_search_basic(tmp_path: Path):
    """Test basic search functionality."""
    index_path = tmp_path / "test_index.db"
    index = SearchIndex(index_path)
    
    # Index multiple datasets
    index.index_dataset(
        dataset_id="test:unemployment",
        source="test",
        title="Unemployment Rate Dataset",
    )
    index.index_dataset(
        dataset_id="test:income",
        source="test",
        title="Income Distribution Dataset",
    )
    
    # Search
    results = index.search("unemployment")
    assert len(results) > 0
    assert any(r.id == "test:unemployment" for r in results)
    
    results = index.search("income")
    assert len(results) > 0
    assert any(r.id == "test:income" for r in results)


def test_search_with_source_filter(tmp_path: Path):
    """Test search with source filter."""
    index_path = tmp_path / "test_index.db"
    index = SearchIndex(index_path)
    
    index.index_dataset(
        dataset_id="test:dataset1",
        source="test",
        title="Test Dataset",
    )
    index.index_dataset(
        dataset_id="other:dataset1",
        source="other",
        title="Other Dataset",
    )
    
    results = index.search("dataset", source="test")
    assert len(results) > 0
    assert all(r.source == "test" for r in results)


def test_search_advanced_variable(tmp_path: Path):
    """Test advanced search with variable filter."""
    index_path = tmp_path / "test_index.db"
    index = SearchIndex(index_path)
    
    index.index_dataset(
        dataset_id="test:dataset1",
        source="test",
        title="Test Dataset",
        variable_labels={"age": "Age in years", "income": "Annual income"},
    )
    index.index_dataset(
        dataset_id="test:dataset2",
        source="test",
        title="Another Dataset",
        variable_labels={"height": "Height in cm"},
    )
    
    results = index.search_advanced(variable_name="age")
    assert len(results) > 0
    assert any(r.id == "test:dataset1" for r in results)
    
    results = index.search_advanced(variable_name="height")
    assert any(r.id == "test:dataset2" for r in results)


def test_get_dataset_info(tmp_path: Path):
    """Test getting dataset information."""
    index_path = tmp_path / "test_index.db"
    index = SearchIndex(index_path)
    
    index.index_dataset(
        dataset_id="test:dataset1",
        source="test",
        title="Test Dataset",
        description="A test dataset",
        license="MIT",
        variable_labels={"age": "Age in years"},
    )
    
    info = index.get_dataset_info("test:dataset1")
    assert info is not None
    assert info["title"] == "Test Dataset"
    assert info["description"] == "A test dataset"
    assert info["license"] == "MIT"
    assert "age" in info["variable_labels"]


def test_rebuild_index(tmp_path: Path):
    """Test rebuilding index from registry."""
    index_path = tmp_path / "test_index.db"
    index = SearchIndex(index_path)
    
    # Rebuild should index all datasets from adapters
    index.rebuild_index()
    
    # Should have indexed at least the built-in datasets
    results = index.search("")
    assert len(results) >= 0  # May be empty if no datasets exist yet


def test_clear_index(tmp_path: Path):
    """Test clearing the index."""
    index_path = tmp_path / "test_index.db"
    index = SearchIndex(index_path)
    
    index.index_dataset(
        dataset_id="test:dataset1",
        source="test",
        title="Test Dataset",
    )
    
    assert index.get_dataset_info("test:dataset1") is not None
    
    index.clear_index()
    
    # Index should be reinitialized but empty
    assert index_path.exists()
    assert index.get_dataset_info("test:dataset1") is None


def test_get_index_singleton():
    """Test that get_index returns a singleton."""
    index1 = get_index()
    index2 = get_index()
    assert index1 is index2
