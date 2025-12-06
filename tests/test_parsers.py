"""Tests for socdata.core.parsers module."""

from pathlib import Path

import pandas as pd
import pytest

from socdata.core.parsers import read_table, read_table_with_meta


def test_read_table_csv(tmp_path):
    """Test reading CSV file."""
    csv_file = tmp_path / "test.csv"
    csv_file.write_text("col1,col2\n1,2\n3,4")
    
    df = read_table(csv_file)
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 2
    assert "col1" in df.columns
    assert "col2" in df.columns
    assert df.iloc[0]["col1"] == 1
    assert df.iloc[0]["col2"] == 2


def test_read_table_csv_with_encoding(tmp_path):
    """Test reading CSV file with encoding."""
    csv_file = tmp_path / "test.csv"
    csv_file.write_text("col1,col2\n1,2\n3,4", encoding="utf-8")
    
    df = read_table(csv_file, encoding="utf-8")
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 2


def test_read_table_csv_with_sep(tmp_path):
    """Test reading CSV file with custom separator."""
    csv_file = tmp_path / "test.csv"
    csv_file.write_text("col1;col2\n1;2\n3;4")
    
    df = read_table(csv_file, sep=";")
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 2
    assert "col1" in df.columns


def test_read_table_tsv(tmp_path):
    """Test reading TSV file."""
    tsv_file = tmp_path / "test.tsv"
    tsv_file.write_text("col1\tcol2\n1\t2\n3\t4")
    
    df = read_table(tsv_file)
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 2
    assert "col1" in df.columns


def test_read_table_unsupported_format(tmp_path):
    """Test reading unsupported file format."""
    txt_file = tmp_path / "test.txt"
    txt_file.write_text("some text")
    
    with pytest.raises(ValueError, match="Unsupported file type"):
        read_table(txt_file)


def test_read_table_with_meta_csv(tmp_path):
    """Test reading CSV file with metadata."""
    csv_file = tmp_path / "test.csv"
    csv_file.write_text("col1,col2\n1,2\n3,4")
    
    df, meta = read_table_with_meta(csv_file)
    assert isinstance(df, pd.DataFrame)
    assert isinstance(meta, dict)
    assert "variable_labels" in meta
    assert "value_labels" in meta
    assert len(df) == 2


def test_read_table_with_meta_csv_empty_labels(tmp_path):
    """Test reading CSV file with metadata returns empty labels."""
    csv_file = tmp_path / "test.csv"
    csv_file.write_text("col1,col2\n1,2")
    
    df, meta = read_table_with_meta(csv_file)
    assert meta["variable_labels"] == {}
    assert meta["value_labels"] == {}


def test_read_table_with_meta_tsv(tmp_path):
    """Test reading TSV file with metadata."""
    tsv_file = tmp_path / "test.tsv"
    tsv_file.write_text("col1\tcol2\n1\t2")
    
    df, meta = read_table_with_meta(tsv_file)
    assert isinstance(df, pd.DataFrame)
    assert isinstance(meta, dict)


def test_read_table_with_meta_unsupported_format(tmp_path):
    """Test reading unsupported file format with metadata."""
    txt_file = tmp_path / "test.txt"
    txt_file.write_text("some text")
    
    with pytest.raises(ValueError, match="Unsupported file type"):
        read_table_with_meta(txt_file)


# Note: Tests for .dta and .sav files would require actual Stata/SPSS files
# or mocking pyreadstat/pandas.read_stata. For now, we test the error cases
# and CSV/TSV which don't require external dependencies.

def test_read_table_dta_not_found(tmp_path):
    """Test reading non-existent .dta file."""
    dta_file = tmp_path / "test.dta"
    
    # This will fail because file doesn't exist
    # The actual error depends on pandas/pyreadstat implementation
    with pytest.raises((FileNotFoundError, pd.errors.EmptyDataError, ValueError)):
        read_table(dta_file)


def test_read_table_sav_not_found(tmp_path):
    """Test reading non-existent .sav file."""
    sav_file = tmp_path / "test.sav"
    
    # This will fail because file doesn't exist
    with pytest.raises((FileNotFoundError, ValueError)):
        read_table(sav_file)


def test_read_table_with_meta_dta_not_found(tmp_path):
    """Test reading non-existent .dta file with metadata."""
    dta_file = tmp_path / "test.dta"
    
    # This will fail because file doesn't exist
    with pytest.raises((FileNotFoundError, pd.errors.EmptyDataError, ValueError)):
        read_table_with_meta(dta_file)


def test_read_table_with_meta_sav_not_found(tmp_path):
    """Test reading non-existent .sav file with metadata."""
    sav_file = tmp_path / "test.sav"
    
    # This will fail because file doesn't exist
    with pytest.raises((FileNotFoundError, ValueError)):
        read_table_with_meta(sav_file)
