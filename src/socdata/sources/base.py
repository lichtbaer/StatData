from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

from ..core.config import get_config
from ..core.exceptions import MetadataError, ParserError, StorageError
from ..core.logging import get_logger
from ..core.parsers import read_table, read_table_with_meta
from ..core.types import DatasetSummary

logger = get_logger(__name__)


class BaseAdapter(ABC):
    @abstractmethod
    def list_datasets(self) -> List[DatasetSummary]:  # lightweight built-ins
        raise NotImplementedError

    @abstractmethod
    def load(self, dataset_id: str, *, filters: Dict[str, Any]) -> pd.DataFrame:
        raise NotImplementedError

    def ingest(self, dataset_id: str | None, *, file_path: str) -> pd.DataFrame:  # optional for manual adapters
        raise NotImplementedError

    def _read_table_with_meta_fallback(
        self, path: Path, *, encoding: str | None = None, sep: str | None = None
    ) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Read table with metadata, falling back to reading without metadata on error.
        
        Args:
            path: Path to the file
            encoding: Optional encoding
            sep: Optional separator
        
        Returns:
            Tuple of (DataFrame, metadata dict)
        """
        try:
            return read_table_with_meta(path, encoding=encoding, sep=sep)
        except (ParserError, MetadataError) as e:
            # Expected errors - log and fallback
            logger.warning(
                f"Failed to read metadata from {path}, falling back to basic read: {e}",
                exc_info=True
            )
            df = read_table(path, encoding=encoding, sep=sep)
            return df, {"variable_labels": {}, "value_labels": {}}
        except Exception as e:
            # Unexpected errors - log with full traceback
            logger.error(
                f"Unexpected error reading metadata from {path}: {e}",
                exc_info=True
            )
            # Still try to fallback to basic read
            try:
                df = read_table(path, encoding=encoding, sep=sep)
                return df, {"variable_labels": {}, "value_labels": {}}
            except Exception as e2:
                logger.error(f"Fallback read also failed for {path}: {e2}", exc_info=True)
                raise ParserError(f"Failed to read file {path}: {e2}") from e2

    def _write_parquet_with_metadata(
        self,
        df: pd.DataFrame,
        output_path: Path,
        *,
        dataset_id: str,
        source: str,
        adapter: str,
        manifest_path: Path,
        variable_labels: Dict[str, str],
        value_labels: Dict[str, Dict[str, str]],
    ) -> bool:
        """
        Write DataFrame to Parquet with metadata, best-effort.
        
        Args:
            df: DataFrame to write
            output_path: Output path for Parquet file
            dataset_id: Dataset identifier
            source: Source name
            adapter: Adapter name
            manifest_path: Path to manifest file
            variable_labels: Variable labels dict
            value_labels: Value labels dict
        
        Returns:
            True if successful, False otherwise
        """
        try:
            import json as _json
            import pyarrow as pa
            import pyarrow.parquet as pq

            table = pa.Table.from_pandas(df, preserve_index=False)
            meta_bytes = table.schema.metadata or {}
            aug = {
                b"socdata.dataset_id": dataset_id.encode("utf-8"),
                b"socdata.source": source.encode("utf-8"),
                b"socdata.adapter": adapter.encode("utf-8"),
                b"socdata.manifest_path": str(manifest_path).encode("utf-8"),
                b"socdata.variable_labels": _json.dumps(variable_labels).encode("utf-8"),
                b"socdata.value_labels": _json.dumps(value_labels).encode("utf-8"),
            }
            new_schema = table.schema.with_metadata({**meta_bytes, **aug})
            table = table.replace_schema_metadata(new_schema.metadata)
            pq.write_table(table, output_path)
            return True
        except (OSError, IOError, PermissionError) as e:
            # File system errors - log and try fallback
            logger.warning(
                f"Failed to write Parquet metadata for {dataset_id} (filesystem error): {e}",
                exc_info=True
            )
            # Fallback: write without metadata
            try:
                df.to_parquet(output_path, index=False)
                return True
            except Exception as e2:
                logger.error(
                    f"Failed to write Parquet file {output_path}: {e2}",
                    exc_info=True
                )
                raise StorageError(f"Failed to write Parquet file {output_path}: {e2}") from e2
        except Exception as e:
            # Other errors (e.g., pyarrow errors) - log and try fallback
            logger.warning(
                f"Failed to write Parquet metadata for {dataset_id}: {e}",
                exc_info=True
            )
            # Fallback: write without metadata
            try:
                df.to_parquet(output_path, index=False)
                return True
            except Exception as e2:
                logger.error(
                    f"Failed to write Parquet file {output_path}: {e2}",
                    exc_info=True
                )
                raise StorageError(f"Failed to write Parquet file {output_path}: {e2}") from e2

    def _index_dataset_safe(self, dataset_id: str, manifest_path: Path) -> bool:
        """
        Index dataset from manifest, best-effort.
        
        Args:
            dataset_id: Dataset identifier
            manifest_path: Path to manifest file
        
        Returns:
            True if successful, False otherwise
        """
        try:
            from ..core.registry import index_dataset_from_manifest
            from ..core.exceptions import SearchIndexError
            
            index_dataset_from_manifest(dataset_id, str(manifest_path))
            return True
        except SearchIndexError as e:
            # Expected index errors - log but don't fail ingestion
            logger.warning(
                f"Failed to index dataset {dataset_id} from manifest {manifest_path}: {e}",
                exc_info=True
            )
            return False
        except Exception as e:
            # Unexpected errors - log with full traceback
            logger.error(
                f"Unexpected error indexing dataset {dataset_id} from manifest {manifest_path}: {e}",
                exc_info=True
            )
            return False

