from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional

import pandas as pd

from .core.registry import resolve_adapter
from .core.i18n import get_i18n_manager
from .core.logging import get_logger
from .core.exceptions import AdapterNotFoundError, DatasetNotFoundError, I18nError
from .core.validation import get_validator, DatasetSchema

logger = get_logger(__name__)


def load(
    dataset_id: str,
    *,
    filters: Optional[Dict[str, Any]] = None,
    language: Optional[str] = None,
    validate: bool = False,
    schema: Optional[DatasetSchema] = None,
) -> pd.DataFrame:
    """
    Load a dataset with optional filters and language for labels.
    
    Args:
        dataset_id: Dataset identifier (e.g., 'eurostat:une_rt_m')
        filters: Optional filters to apply
        language: Optional language code for variable/value labels (e.g., 'de', 'fr')
    
    Returns:
        DataFrame with the dataset
    
    Raises:
        ValueError: If dataset_id format is invalid
        DatasetNotFoundError: If dataset cannot be found or loaded
    """
    # Validate dataset_id format
    if not dataset_id or not isinstance(dataset_id, str):
        raise ValueError("dataset_id must be a non-empty string")
    
    if ":" not in dataset_id and dataset_id not in ["manual", "eurostat", "soep", "gss", "ess", "icpsr", "issp", "cses", "evs"]:
        raise ValueError(f"Invalid dataset_id format: {dataset_id}. Expected format: 'source:dataset' or adapter name")
    
    # Validate language code if provided
    if language is not None:
        if not isinstance(language, str) or len(language) != 2:
            logger.warning(f"Invalid language code format: {language}. Expected 2-letter code (e.g., 'de', 'fr')")
            language = None  # Continue without i18n if language is invalid
    try:
        adapter = resolve_adapter(dataset_id)
    except AdapterNotFoundError:
        raise DatasetNotFoundError(f"Dataset not found: {dataset_id}")
    
    try:
        df = adapter.load(dataset_id, filters=filters or {})
    except Exception as e:
        logger.error(f"Failed to load dataset {dataset_id}: {e}", exc_info=True)
        raise DatasetNotFoundError(f"Failed to load dataset {dataset_id}: {e}") from e
    
    # Apply i18n if language is specified
    if language:
        try:
            df = _apply_i18n_labels(df, dataset_id, language)
        except Exception as e:
            logger.warning(f"Failed to apply i18n labels for {dataset_id}: {e}", exc_info=True)
            # Continue without i18n if it fails
    
    # Validate if requested
    if validate:
        try:
            validator = get_validator()
            report = validator.validate_and_check(df, schema=schema, dataset_id=dataset_id)
            
            if report.has_issues:
                logger.warning(f"Data quality issues found for {dataset_id}: {report.issues}")
            if report.has_warnings:
                logger.info(f"Data quality warnings for {dataset_id}: {report.warnings}")
            
            # Store report in DataFrame attributes for access
            df.attrs['quality_report'] = report.to_dict()
        except Exception as e:
            logger.warning(f"Failed to validate dataset {dataset_id}: {e}", exc_info=True)
            # Continue without validation if it fails
    
    return df


def _apply_i18n_labels(df: pd.DataFrame, dataset_id: str, language: str) -> pd.DataFrame:
    """
    Apply internationalized labels to DataFrame columns and values.
    
    Args:
        df: DataFrame to apply labels to
        dataset_id: Dataset identifier
        language: Language code (e.g., 'de', 'fr')
    
    Returns:
        DataFrame with translated column names and values (if available)
    """
    try:
        i18n_manager = get_i18n_manager()
        
        # Try to get labels from Parquet metadata if DataFrame was loaded from cache
        variable_labels = {}
        value_labels = {}
        
        # Check if DataFrame has Parquet metadata (when loaded from cache)
        # This is a best-effort approach - not all DataFrames will have this metadata
        if hasattr(df, 'attrs') and df.attrs:
            # Try to get metadata from attrs (pandas 1.5+)
            variable_labels = df.attrs.get('variable_labels', {})
            value_labels = df.attrs.get('value_labels', {})
        
        # Alternative: Try to read from cache directory
        if not variable_labels:
            try:
                from .core.storage import get_dataset_dir
                from .core.config import get_config
                
                source = dataset_id.split(":")[0]
                dataset_name = dataset_id.split(":")[1] if ":" in dataset_id else dataset_id
                cache_dir = get_dataset_dir(source, dataset_name.replace(":", "_"), "latest")
                manifest_path = cache_dir / "meta" / "ingestion_manifest.json"
                
                if manifest_path.exists():
                    manifest_data = json.loads(manifest_path.read_text())
                    variable_labels = manifest_data.get("variable_labels", {})
                    value_labels = manifest_data.get("value_labels", {})
            except Exception as e:
                logger.debug(f"Could not load labels from manifest for {dataset_id}: {e}")
        
        # Translate variable labels
        if variable_labels:
            translated_var_labels = i18n_manager.translate_variable_labels(
                variable_labels, language=language, dataset_id=dataset_id
            )
            
            # Rename columns if translation exists
            column_mapping = {}
            for col in df.columns:
                if col in translated_var_labels:
                    # Use translated label as column name
                    column_mapping[col] = translated_var_labels[col]
            
            if column_mapping:
                df = df.rename(columns=column_mapping)
                logger.debug(f"Applied {len(column_mapping)} variable label translations for {dataset_id}")
        
        # Translate value labels
        if value_labels:
            translated_val_labels = i18n_manager.translate_value_labels(
                value_labels, language=language, dataset_id=dataset_id
            )
            
            # Apply value translations to categorical columns
            for var_name, val_dict in translated_val_labels.items():
                # Find column (might be renamed)
                col_name = None
                for col in df.columns:
                    if col == var_name or (var_name in variable_labels and col == variable_labels[var_name]):
                        col_name = col
                        break
                
                if col_name and col_name in df.columns:
                    # Create mapping for values
                    value_mapping = {}
                    for val, label in val_dict.items():
                        try:
                            # Try to convert value to appropriate type
                            if df[col_name].dtype in ['int64', 'Int64']:
                                val_key = int(val)
                            elif df[col_name].dtype in ['float64', 'Float64']:
                                val_key = float(val)
                            else:
                                val_key = val
                            
                            # Map value to translated label
                            if val_key in df[col_name].values:
                                value_mapping[val_key] = label
                        except (ValueError, TypeError):
                            # Skip if conversion fails
                            continue
                    
                    if value_mapping:
                        # Replace values with translated labels
                        df[col_name] = df[col_name].replace(value_mapping)
                        logger.debug(f"Applied value label translations for {col_name} in {dataset_id}")
        
    except Exception as e:
        logger.warning(f"Failed to apply i18n labels for {dataset_id} in language {language}: {e}", exc_info=True)
        # Return original DataFrame if translation fails
    
    return df


def ingest(dataset_or_adapter_id: str, *, file_path: str) -> pd.DataFrame:
    """
    Ingest a dataset from a local file.
    
    Args:
        dataset_or_adapter_id: Adapter or dataset identifier
        file_path: Path to the data file
    
    Returns:
        DataFrame with the ingested dataset
    
    Raises:
        AdapterNotFoundError: If adapter cannot be found
        FileNotFoundError: If file does not exist
        ParserError: If parsing fails
    """
    from pathlib import Path
    from .core.exceptions import ParserError
    
    if not Path(file_path).exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    try:
        adapter = resolve_adapter(dataset_or_adapter_id)
    except AdapterNotFoundError as e:
        logger.error(f"Adapter not found for {dataset_or_adapter_id}: {e}")
        raise
    
    try:
        return adapter.ingest(dataset_or_adapter_id, file_path=file_path)
    except NotImplementedError as e:
        logger.error(f"Ingest not supported for adapter {dataset_or_adapter_id}: {e}")
        raise ParserError(f"Ingest not supported for adapter {dataset_or_adapter_id}") from e
    except Exception as e:
        logger.error(f"Failed to ingest dataset from {file_path}: {e}", exc_info=True)
        raise ParserError(f"Failed to ingest dataset from {file_path}: {e}") from e

