"""
Data validation and quality checks for datasets.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import pandas as pd

from .exceptions import ValidationError
from .logging import get_logger

logger = get_logger(__name__)


class DatasetSchema:
    """Schema definition for a dataset."""

    def __init__(
        self,
        required_columns: Optional[List[str]] = None,
        column_types: Optional[Dict[str, str]] = None,
        constraints: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize dataset schema.
        
        Args:
            required_columns: List of required column names
            column_types: Dictionary mapping column names to expected types
            constraints: Dictionary with validation constraints
        """
        self.required_columns = required_columns or []
        self.column_types = column_types or {}
        self.constraints = constraints or {}


class DataQualityReport:
    """Report on data quality metrics."""

    def __init__(self, dataset_id: str):
        self.dataset_id = dataset_id
        self.metrics: Dict[str, Any] = {}
        self.issues: List[str] = []
        self.warnings: List[str] = []

    def add_metric(self, name: str, value: Any) -> None:
        """Add a quality metric."""
        self.metrics[name] = value

    def add_issue(self, issue: str) -> None:
        """Add a quality issue."""
        self.issues.append(issue)

    def add_warning(self, warning: str) -> None:
        """Add a quality warning."""
        self.warnings.append(warning)

    def to_dict(self) -> Dict[str, Any]:
        """Convert report to dictionary."""
        return {
            "dataset_id": self.dataset_id,
            "metrics": self.metrics,
            "issues": self.issues,
            "warnings": self.warnings,
            "has_issues": len(self.issues) > 0,
            "has_warnings": len(self.warnings) > 0,
        }


class DataValidator:
    """Validator for dataset quality and schema compliance."""

    def __init__(self):
        self.logger = get_logger(__name__)

    def validate_schema(
        self, df: pd.DataFrame, schema: DatasetSchema, dataset_id: str = "unknown"
    ) -> DataQualityReport:
        """
        Validate DataFrame against schema.
        
        Args:
            df: DataFrame to validate
            schema: Schema definition
            dataset_id: Dataset identifier
        
        Returns:
            DataQualityReport with validation results
        """
        report = DataQualityReport(dataset_id)

        # Check required columns
        missing_columns = [
            col for col in schema.required_columns if col not in df.columns
        ]
        if missing_columns:
            report.add_issue(f"Missing required columns: {missing_columns}")

        # Check column types
        for col, expected_type in schema.column_types.items():
            if col not in df.columns:
                continue

            actual_type = str(df[col].dtype)
            if not self._type_matches(actual_type, expected_type):
                report.add_warning(
                    f"Column '{col}' has type {actual_type}, expected {expected_type}"
                )

        # Check constraints
        for col, constraint in schema.constraints.items():
            if col not in df.columns:
                continue

            if "min" in constraint:
                if df[col].min() < constraint["min"]:
                    report.add_issue(
                        f"Column '{col}' has values below minimum {constraint['min']}"
                    )

            if "max" in constraint:
                if df[col].max() > constraint["max"]:
                    report.add_issue(
                        f"Column '{col}' has values above maximum {constraint['max']}"
                    )

            if "unique" in constraint and constraint["unique"]:
                if df[col].duplicated().any():
                    report.add_warning(f"Column '{col}' should be unique but has duplicates")

        return report

    def _type_matches(self, actual: str, expected: str) -> bool:
        """Check if actual type matches expected type."""
        type_mapping = {
            "int": ["int64", "int32", "Int64", "Int32"],
            "float": ["float64", "float32", "Float64", "Float32"],
            "str": ["object", "string"],
            "bool": ["bool", "boolean"],
        }

        if expected.lower() in type_mapping:
            return any(actual.startswith(t) for t in type_mapping[expected.lower()])

        return actual == expected

    def quality_check(self, df: pd.DataFrame, dataset_id: str = "unknown") -> DataQualityReport:
        """
        Perform quality checks on a dataset.
        
        Args:
            df: DataFrame to check
            dataset_id: Dataset identifier
        
        Returns:
            DataQualityReport with quality metrics
        """
        report = DataQualityReport(dataset_id)

        # Basic metrics
        report.add_metric("row_count", len(df))
        report.add_metric("column_count", len(df.columns))
        report.add_metric("memory_usage_mb", df.memory_usage(deep=True).sum() / 1024 / 1024)

        # Missing values
        missing_counts = df.isnull().sum()
        total_missing = missing_counts.sum()
        missing_percentage = (total_missing / (len(df) * len(df.columns))) * 100

        report.add_metric("missing_values_count", int(total_missing))
        report.add_metric("missing_values_percentage", round(missing_percentage, 2))

        if missing_percentage > 10:
            report.add_warning(f"High percentage of missing values: {missing_percentage:.2f}%")

        # Check for completely empty columns
        empty_columns = [col for col in df.columns if df[col].isnull().all()]
        if empty_columns:
            report.add_issue(f"Completely empty columns: {empty_columns}")

        # Check for duplicate rows
        duplicate_count = df.duplicated().sum()
        if duplicate_count > 0:
            duplicate_percentage = (duplicate_count / len(df)) * 100
            report.add_metric("duplicate_rows", int(duplicate_count))
            report.add_warning(
                f"Dataset contains {duplicate_count} duplicate rows ({duplicate_percentage:.2f}%)"
            )

        # Check for constant columns (no variation)
        constant_columns = []
        for col in df.columns:
            if df[col].nunique() <= 1:
                constant_columns.append(col)

        if constant_columns:
            report.add_warning(f"Constant columns (no variation): {constant_columns}")

        # Outlier detection (simple IQR method for numeric columns)
        numeric_columns = df.select_dtypes(include=["number"]).columns
        outlier_columns = []
        for col in numeric_columns:
            Q1 = df[col].quantile(0.25)
            Q3 = df[col].quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR

            outliers = df[(df[col] < lower_bound) | (df[col] > upper_bound)]
            if len(outliers) > len(df) * 0.05:  # More than 5% outliers
                outlier_columns.append(col)

        if outlier_columns:
            report.add_warning(f"Columns with many potential outliers: {outlier_columns}")

        return report

    def validate_and_check(
        self,
        df: pd.DataFrame,
        schema: Optional[DatasetSchema] = None,
        dataset_id: str = "unknown",
    ) -> DataQualityReport:
        """
        Perform both schema validation and quality checks.
        
        Args:
            df: DataFrame to validate
            schema: Optional schema definition
            dataset_id: Dataset identifier
        
        Returns:
            Combined DataQualityReport
        """
        # Quality check
        report = self.quality_check(df, dataset_id)

        # Schema validation if provided
        if schema:
            schema_report = self.validate_schema(df, schema, dataset_id)
            # Merge reports
            report.issues.extend(schema_report.issues)
            report.warnings.extend(schema_report.warnings)
            report.metrics.update(schema_report.metrics)

        return report


# Global validator instance
_validator: Optional[DataValidator] = None


def get_validator() -> DataValidator:
    """Get or create the global validator instance."""
    global _validator
    if _validator is None:
        _validator = DataValidator()
    return _validator
