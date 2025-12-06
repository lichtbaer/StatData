"""Tests for data validation and quality checks."""

import pandas as pd
import pytest

from socdata.core.validation import (
    DataQualityReport,
    DataValidator,
    DatasetSchema,
    get_validator,
)


def test_data_validator_initialization():
    """Test validator initialization."""
    validator = DataValidator()
    assert validator is not None


def test_get_validator_singleton():
    """Test that get_validator returns singleton."""
    validator1 = get_validator()
    validator2 = get_validator()
    assert validator1 is validator2


def test_quality_check_basic():
    """Test basic quality checks."""
    df = pd.DataFrame({
        "col1": [1, 2, 3, 4, 5],
        "col2": ["a", "b", "c", "d", "e"],
        "col3": [1.1, 2.2, 3.3, 4.4, 5.5],
    })
    
    validator = DataValidator()
    report = validator.quality_check(df, dataset_id="test:dataset1")
    
    assert report.dataset_id == "test:dataset1"
    assert report.metrics["row_count"] == 5
    assert report.metrics["column_count"] == 3
    assert "memory_usage_mb" in report.metrics


def test_quality_check_missing_values():
    """Test quality check with missing values."""
    df = pd.DataFrame({
        "col1": [1, 2, None, 4, 5],
        "col2": ["a", None, "c", None, "e"],
        "col3": [1.1, 2.2, 3.3, 4.4, 5.5],
    })
    
    validator = DataValidator()
    report = validator.quality_check(df, dataset_id="test:dataset1")
    
    assert report.metrics["missing_values_count"] > 0
    assert report.metrics["missing_values_percentage"] > 0


def test_quality_check_empty_columns():
    """Test quality check with empty columns."""
    df = pd.DataFrame({
        "col1": [1, 2, 3],
        "col2": [None, None, None],
        "col3": [1.1, 2.2, 3.3],
    })
    
    validator = DataValidator()
    report = validator.quality_check(df, dataset_id="test:dataset1")
    
    assert len(report.issues) > 0
    assert any("empty columns" in issue.lower() for issue in report.issues)


def test_quality_check_duplicates():
    """Test quality check with duplicate rows."""
    df = pd.DataFrame({
        "col1": [1, 2, 3, 1, 2],
        "col2": ["a", "b", "c", "a", "b"],
    })
    
    validator = DataValidator()
    report = validator.quality_check(df, dataset_id="test:dataset1")
    
    assert report.metrics["duplicate_rows"] > 0
    assert len(report.warnings) > 0


def test_validate_schema_required_columns():
    """Test schema validation with required columns."""
    df = pd.DataFrame({
        "col1": [1, 2, 3],
        "col2": ["a", "b", "c"],
    })
    
    schema = DatasetSchema(required_columns=["col1", "col2", "col3"])
    validator = DataValidator()
    report = validator.validate_schema(df, schema, dataset_id="test:dataset1")
    
    assert len(report.issues) > 0
    assert any("missing required columns" in issue.lower() for issue in report.issues)


def test_validate_schema_column_types():
    """Test schema validation with column types."""
    df = pd.DataFrame({
        "col1": [1, 2, 3],
        "col2": ["a", "b", "c"],
    })
    
    schema = DatasetSchema(column_types={"col1": "int", "col2": "str"})
    validator = DataValidator()
    report = validator.validate_schema(df, schema, dataset_id="test:dataset1")
    
    # Should not have issues if types match
    assert len(report.issues) == 0 or all("type" not in issue.lower() for issue in report.issues)


def test_validate_schema_constraints():
    """Test schema validation with constraints."""
    df = pd.DataFrame({
        "col1": [1, 2, 3, 10, 20],
    })
    
    schema = DatasetSchema(constraints={"col1": {"min": 0, "max": 5}})
    validator = DataValidator()
    report = validator.validate_schema(df, schema, dataset_id="test:dataset1")
    
    # Should have issues for values above max
    assert len(report.issues) > 0


def test_validate_and_check():
    """Test combined validation and quality check."""
    df = pd.DataFrame({
        "col1": [1, 2, 3],
        "col2": ["a", "b", "c"],
    })
    
    schema = DatasetSchema(required_columns=["col1", "col2"])
    validator = DataValidator()
    report = validator.validate_and_check(df, schema=schema, dataset_id="test:dataset1")
    
    assert report.metrics["row_count"] == 3
    assert len(report.issues) == 0  # All required columns present


def test_quality_report_to_dict():
    """Test quality report serialization."""
    report = DataQualityReport("test:dataset1")
    report.add_metric("test_metric", 42)
    report.add_issue("Test issue")
    report.add_warning("Test warning")
    
    report_dict = report.to_dict()
    
    assert report_dict["dataset_id"] == "test:dataset1"
    assert report_dict["metrics"]["test_metric"] == 42
    assert len(report_dict["issues"]) == 1
    assert len(report_dict["warnings"]) == 1
    assert report_dict["has_issues"] is True
    assert report_dict["has_warnings"] is True
