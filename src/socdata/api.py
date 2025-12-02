from __future__ import annotations

from typing import Any, Dict, Optional

import pandas as pd

from .core.registry import resolve_adapter
from .core.i18n import get_i18n_manager


def load(
    dataset_id: str,
    *,
    filters: Optional[Dict[str, Any]] = None,
    language: Optional[str] = None,
) -> pd.DataFrame:
    """
    Load a dataset with optional filters and language for labels.
    
    Args:
        dataset_id: Dataset identifier (e.g., 'eurostat:une_rt_m')
        filters: Optional filters to apply
        language: Optional language code for variable/value labels (e.g., 'de', 'fr')
    
    Returns:
        DataFrame with the dataset
    """
    adapter = resolve_adapter(dataset_id)
    df = adapter.load(dataset_id, filters=filters or {})
    
    # Apply i18n if language is specified
    if language:
        # Note: Variable/value labels are stored in Parquet metadata,
        # not in the DataFrame itself. This would require reading metadata
        # and applying translations, which is a more complex operation.
        # For now, we return the DataFrame as-is.
        # Future enhancement: add method to apply translations to DataFrame columns
        pass
    
    return df


def ingest(dataset_or_adapter_id: str, *, file_path: str) -> pd.DataFrame:
    """
    Ingest a dataset from a local file.
    
    Args:
        dataset_or_adapter_id: Adapter or dataset identifier
        file_path: Path to the data file
    
    Returns:
        DataFrame with the ingested dataset
    """
    adapter = resolve_adapter(dataset_or_adapter_id)
    return adapter.ingest(dataset_or_adapter_id, file_path=file_path)

