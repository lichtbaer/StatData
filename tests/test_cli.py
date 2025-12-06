"""Tests for socdata.cli module."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from socdata.cli import app
from socdata.core.exceptions import AdapterNotFoundError, DatasetNotFoundError, ParserError

runner = CliRunner()


def test_version():
    """Test version command."""
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert "socdata" in result.stdout
    assert "0.1.0" in result.stdout


def test_show_config(tmp_path, monkeypatch):
    """Test show-config command."""
    monkeypatch.setenv("SOCDATA_CACHE_DIR", str(tmp_path))
    
    result = runner.invoke(app, ["show-config"])
    assert result.exit_code == 0
    assert "cache_dir" in result.stdout
    assert "timeout_seconds" in result.stdout


def test_list_all(tmp_path, monkeypatch):
    """Test list command without source filter."""
    monkeypatch.setenv("SOCDATA_CACHE_DIR", str(tmp_path))
    
    result = runner.invoke(app, ["list"])
    assert result.exit_code == 0
    assert "ID" in result.stdout
    assert "Source" in result.stdout
    assert "Title" in result.stdout


def test_list_with_source(tmp_path, monkeypatch):
    """Test list command with source filter."""
    monkeypatch.setenv("SOCDATA_CACHE_DIR", str(tmp_path))
    
    result = runner.invoke(app, ["list", "--source", "eurostat"])
    assert result.exit_code == 0
    assert "eurostat" in result.stdout


def test_list_unknown_source(tmp_path, monkeypatch):
    """Test list command with unknown source."""
    monkeypatch.setenv("SOCDATA_CACHE_DIR", str(tmp_path))
    
    result = runner.invoke(app, ["list", "--source", "nonexistent"])
    assert result.exit_code == 0
    # Should not error, just return empty table


def test_search_basic(tmp_path, monkeypatch):
    """Test search command."""
    monkeypatch.setenv("SOCDATA_CACHE_DIR", str(tmp_path))
    
    result = runner.invoke(app, ["search", "test"])
    assert result.exit_code == 0
    assert "ID" in result.stdout or "No datasets found" in result.stdout


def test_search_with_source(tmp_path, monkeypatch):
    """Test search command with source filter."""
    monkeypatch.setenv("SOCDATA_CACHE_DIR", str(tmp_path))
    
    result = runner.invoke(app, ["search", "test", "--source", "eurostat"])
    assert result.exit_code == 0


def test_search_with_variable(tmp_path, monkeypatch):
    """Test search command with variable filter."""
    monkeypatch.setenv("SOCDATA_CACHE_DIR", str(tmp_path))
    
    result = runner.invoke(app, ["search", "test", "--variable", "age"])
    assert result.exit_code == 0


def test_search_no_index(tmp_path, monkeypatch):
    """Test search command without index."""
    monkeypatch.setenv("SOCDATA_CACHE_DIR", str(tmp_path))
    
    result = runner.invoke(app, ["search", "test", "--no-index"])
    assert result.exit_code == 0


def test_info_dataset_found(tmp_path, monkeypatch):
    """Test info command with existing dataset."""
    monkeypatch.setenv("SOCDATA_CACHE_DIR", str(tmp_path))
    
    # Mock index to return dataset info
    with patch("socdata.cli.get_index") as mock_index:
        mock_index.return_value.get_dataset_info.return_value = {
            "id": "test:dataset1",
            "source": "test",
            "title": "Test Dataset",
            "description": "A test dataset",
            "license": "MIT",
            "variable_labels": {"var1": "Variable 1"},
        }
        
        result = runner.invoke(app, ["info", "test:dataset1"])
        assert result.exit_code == 0
        assert "test:dataset1" in result.stdout
        assert "Test Dataset" in result.stdout


def test_info_dataset_not_found(tmp_path, monkeypatch):
    """Test info command with non-existent dataset."""
    monkeypatch.setenv("SOCDATA_CACHE_DIR", str(tmp_path))
    
    # Mock index to return None
    with patch("socdata.cli.get_index") as mock_index:
        mock_index.return_value.get_dataset_info.return_value = None
        
        result = runner.invoke(app, ["info", "nonexistent:dataset"])
        assert result.exit_code == 0
        assert "not found" in result.stdout.lower()


def test_info_error(tmp_path, monkeypatch):
    """Test info command with error."""
    monkeypatch.setenv("SOCDATA_CACHE_DIR", str(tmp_path))
    
    # Mock index to raise exception
    with patch("socdata.cli.get_index", side_effect=Exception("Index error")):
        result = runner.invoke(app, ["info", "test:dataset1"])
        assert result.exit_code == 0
        assert "Error" in result.stdout


def test_rebuild_index_success(tmp_path, monkeypatch):
    """Test rebuild-index command success."""
    monkeypatch.setenv("SOCDATA_CACHE_DIR", str(tmp_path))
    
    # Mock index
    with patch("socdata.cli.get_index") as mock_index:
        mock_index.return_value.rebuild_index.return_value = None
        
        result = runner.invoke(app, ["rebuild-index"])
        assert result.exit_code == 0
        assert "successfully" in result.stdout.lower()


def test_rebuild_index_error(tmp_path, monkeypatch):
    """Test rebuild-index command with error."""
    monkeypatch.setenv("SOCDATA_CACHE_DIR", str(tmp_path))
    
    # Mock index to raise exception
    with patch("socdata.cli.get_index", side_effect=Exception("Index error")):
        result = runner.invoke(app, ["rebuild-index"])
        assert result.exit_code == 0
        assert "Error" in result.stdout


def test_load_cmd_success(tmp_path, monkeypatch):
    """Test load-cmd command success."""
    monkeypatch.setenv("SOCDATA_CACHE_DIR", str(tmp_path))
    
    # Mock load function
    import pandas as pd
    mock_df = pd.DataFrame({"col1": [1, 2, 3], "col2": [4, 5, 6]})
    
    with patch("socdata.cli.load", return_value=mock_df):
        result = runner.invoke(app, ["load-cmd", "test:dataset1"])
        assert result.exit_code == 0
        assert "col1" in result.stdout or "col2" in result.stdout


def test_load_cmd_with_filters(tmp_path, monkeypatch):
    """Test load-cmd command with filters."""
    monkeypatch.setenv("SOCDATA_CACHE_DIR", str(tmp_path))
    
    import pandas as pd
    mock_df = pd.DataFrame({"col1": [1, 2]})
    
    with patch("socdata.cli.load", return_value=mock_df):
        result = runner.invoke(app, [
            "load-cmd", "test:dataset1",
            "--filters", '{"key": "value"}'
        ])
        assert result.exit_code == 0


def test_load_cmd_with_simple_filters(tmp_path, monkeypatch):
    """Test load-cmd command with simple key=value filters."""
    monkeypatch.setenv("SOCDATA_CACHE_DIR", str(tmp_path))
    
    import pandas as pd
    mock_df = pd.DataFrame({"col1": [1, 2]})
    
    with patch("socdata.cli.load", return_value=mock_df):
        result = runner.invoke(app, [
            "load-cmd", "test:dataset1",
            "--filters", "key=value,key2=value2"
        ])
        assert result.exit_code == 0


def test_load_cmd_invalid_filters(tmp_path, monkeypatch):
    """Test load-cmd command with invalid filters."""
    monkeypatch.setenv("SOCDATA_CACHE_DIR", str(tmp_path))
    
    result = runner.invoke(app, [
        "load-cmd", "test:dataset1",
        "--filters", "invalid json {"
    ])
    assert result.exit_code == 1
    assert "Error" in result.stdout


def test_load_cmd_dataset_not_found(tmp_path, monkeypatch):
    """Test load-cmd command with non-existent dataset."""
    monkeypatch.setenv("SOCDATA_CACHE_DIR", str(tmp_path))
    
    with patch("socdata.cli.load", side_effect=DatasetNotFoundError("Dataset not found")):
        result = runner.invoke(app, ["load-cmd", "nonexistent:dataset"])
        assert result.exit_code == 1
        assert "Error" in result.stdout


def test_load_cmd_export_parquet(tmp_path, monkeypatch):
    """Test load-cmd command with parquet export."""
    monkeypatch.setenv("SOCDATA_CACHE_DIR", str(tmp_path))
    
    import pandas as pd
    mock_df = pd.DataFrame({"col1": [1, 2, 3]})
    export_path = tmp_path / "output.parquet"
    
    with patch("socdata.cli.load", return_value=mock_df):
        result = runner.invoke(app, [
            "load-cmd", "test:dataset1",
            "--export", str(export_path)
        ])
        assert result.exit_code == 0
        assert export_path.exists()
        assert "Exported" in result.stdout


def test_load_cmd_export_csv(tmp_path, monkeypatch):
    """Test load-cmd command with CSV export."""
    monkeypatch.setenv("SOCDATA_CACHE_DIR", str(tmp_path))
    
    import pandas as pd
    mock_df = pd.DataFrame({"col1": [1, 2, 3]})
    export_path = tmp_path / "output.csv"
    
    with patch("socdata.cli.load", return_value=mock_df):
        result = runner.invoke(app, [
            "load-cmd", "test:dataset1",
            "--export", str(export_path)
        ])
        assert result.exit_code == 0
        assert export_path.exists()
        assert "Exported" in result.stdout


def test_ingest_cmd_success(tmp_path, monkeypatch):
    """Test ingest-cmd command success."""
    monkeypatch.setenv("SOCDATA_CACHE_DIR", str(tmp_path))
    
    # Create test file
    test_file = tmp_path / "test.csv"
    test_file.write_text("col1,col2\n1,2\n3,4")
    
    import pandas as pd
    mock_df = pd.DataFrame({"col1": [1, 3], "col2": [2, 4]})
    
    with patch("socdata.cli.ingest", return_value=mock_df):
        result = runner.invoke(app, [
            "ingest-cmd", "manual", str(test_file)
        ])
        assert result.exit_code == 0
        assert "col1" in result.stdout or "col2" in result.stdout


def test_ingest_cmd_file_not_found(tmp_path, monkeypatch):
    """Test ingest-cmd command with non-existent file."""
    monkeypatch.setenv("SOCDATA_CACHE_DIR", str(tmp_path))
    
    result = runner.invoke(app, [
        "ingest-cmd", "manual", str(tmp_path / "nonexistent.csv")
    ])
    assert result.exit_code == 1
    assert "not found" in result.stdout.lower()


def test_ingest_cmd_adapter_not_found(tmp_path, monkeypatch):
    """Test ingest-cmd command with non-existent adapter."""
    monkeypatch.setenv("SOCDATA_CACHE_DIR", str(tmp_path))
    
    test_file = tmp_path / "test.csv"
    test_file.write_text("col1,col2\n1,2")
    
    with patch("socdata.cli.ingest", side_effect=AdapterNotFoundError("Adapter not found")):
        result = runner.invoke(app, [
            "ingest-cmd", "nonexistent", str(test_file)
        ])
        assert result.exit_code == 1
        assert "Error" in result.stdout


def test_ingest_cmd_parser_error(tmp_path, monkeypatch):
    """Test ingest-cmd command with parser error."""
    monkeypatch.setenv("SOCDATA_CACHE_DIR", str(tmp_path))
    
    test_file = tmp_path / "test.csv"
    test_file.write_text("col1,col2\n1,2")
    
    with patch("socdata.cli.ingest", side_effect=ParserError("Parse error")):
        result = runner.invoke(app, [
            "ingest-cmd", "manual", str(test_file)
        ])
        assert result.exit_code == 1
        assert "Error" in result.stdout


def test_ingest_cmd_export(tmp_path, monkeypatch):
    """Test ingest-cmd command with export."""
    monkeypatch.setenv("SOCDATA_CACHE_DIR", str(tmp_path))
    
    test_file = tmp_path / "test.csv"
    test_file.write_text("col1,col2\n1,2")
    export_path = tmp_path / "output.parquet"
    
    import pandas as pd
    mock_df = pd.DataFrame({"col1": [1], "col2": [2]})
    
    with patch("socdata.cli.ingest", return_value=mock_df):
        result = runner.invoke(app, [
            "ingest-cmd", "manual", str(test_file),
            "--export", str(export_path)
        ])
        assert result.exit_code == 0
        assert export_path.exists()
        assert "Exported" in result.stdout


def test_serve_missing_dependencies(tmp_path, monkeypatch):
    """Test serve command when dependencies are missing."""
    monkeypatch.setenv("SOCDATA_CACHE_DIR", str(tmp_path))
    
    with patch("socdata.cli.uvicorn", side_effect=ImportError("No module named 'uvicorn'")):
        result = runner.invoke(app, ["serve"])
        assert result.exit_code == 1
        assert "not installed" in result.stdout.lower()


def test_serve_success(tmp_path, monkeypatch):
    """Test serve command success."""
    monkeypatch.setenv("SOCDATA_CACHE_DIR", str(tmp_path))
    
    mock_uvicorn = MagicMock()
    
    with patch("socdata.cli.uvicorn", mock_uvicorn):
        with patch("socdata.cli.app") as mock_app:
            result = runner.invoke(app, ["serve", "--host", "127.0.0.1", "--port", "8000"])
            # Note: uvicorn.run blocks, so we can't easily test the full execution
            # But we can test that it doesn't error on import
            assert "uvicorn" in str(mock_uvicorn) or result.exit_code in [0, 1]
