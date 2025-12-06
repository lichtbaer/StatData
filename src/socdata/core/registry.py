from __future__ import annotations

from typing import Dict, List, Optional

from ..sources.base import BaseAdapter
from ..sources.eurostat import EurostatAdapter
from ..sources.manual import ManualAdapter
from ..sources.soep import SOEPAdapter
from ..sources.gss import GSSAdapter
from ..sources.ess import ESSAdapter
from ..sources.icpsr import ICPSRAdapter
from ..sources.issp import ISSPAdapter
from ..sources.cses import CSESAdapter
from ..sources.evs import EVSAdapter
from .types import DatasetSummary
from .search_index import get_index
from .logging import get_logger
from .exceptions import AdapterNotFoundError, SearchIndexError

logger = get_logger(__name__)


_ADAPTERS: Dict[str, BaseAdapter] = {
    "eurostat": EurostatAdapter(),
    "manual": ManualAdapter(),
    "soep": SOEPAdapter(),
    "gss": GSSAdapter(),
    "ess": ESSAdapter(),
    "icpsr": ICPSRAdapter(),
    "issp": ISSPAdapter(),
    "cses": CSESAdapter(),
    "evs": EVSAdapter(),
}


def resolve_adapter(dataset_or_adapter_id: str) -> BaseAdapter:
    """
    Resolve an adapter from a dataset ID or adapter ID.
    
    Args:
        dataset_or_adapter_id: Dataset ID (e.g., 'eurostat:une_rt_m') or adapter ID (e.g., 'manual')
    
    Returns:
        BaseAdapter instance
    
    Raises:
        AdapterNotFoundError: If adapter cannot be found
    """
    # dataset id format examples: eurostat:une_rt_m, manual:wvs
    if ":" in dataset_or_adapter_id:
        source, _ = dataset_or_adapter_id.split(":", 1)
        if source in _ADAPTERS:
            return _ADAPTERS[source]
    # allow passing adapter explicitly e.g. manual
    if dataset_or_adapter_id in _ADAPTERS:
        return _ADAPTERS[dataset_or_adapter_id]
    raise AdapterNotFoundError(f"Unknown adapter for '{dataset_or_adapter_id}'")


def list_datasets(source: str | None = None) -> List[DatasetSummary]:
    summaries: List[DatasetSummary] = []
    for key, adapter in _ADAPTERS.items():
        if source and source != key:
            continue
        summaries.extend(adapter.list_datasets())
    return summaries


def search_datasets(
    query: str,
    source: Optional[str] = None,
    use_index: bool = True,
) -> List[DatasetSummary]:
    """
    Search datasets using full-text search index or fallback to simple search.
    
    Args:
        query: Search query
        source: Optional source filter
        use_index: Whether to use the search index (default: True)
    
    Returns:
        List of matching DatasetSummary objects
    """
    if use_index:
        try:
            index = get_index()
            # Try index search first
            results = index.search(query, source=source)
            if results:
                return results
        except (SearchIndexError, Exception) as e:
            # Fallback to simple search if index fails
            if isinstance(e, SearchIndexError):
                logger.warning(f"Search index error, falling back to simple search: {e}")
            else:
                logger.warning(f"Search index failed, falling back to simple search: {e}", exc_info=True)
    
    # Fallback: simple string matching
    query_lower = query.lower()
    all_ds = list_datasets(source)
    return [
        ds for ds in all_ds
        if query_lower in ds.title.lower() or query_lower in ds.id.lower()
    ]


def search_datasets_advanced(
    query: Optional[str] = None,
    source: Optional[str] = None,
    variable_name: Optional[str] = None,
) -> List[DatasetSummary]:
    """
    Advanced search with multiple filters.
    
    Args:
        query: Full-text search query
        source: Filter by source
        variable_name: Search for datasets containing this variable
    
    Returns:
        List of matching DatasetSummary objects
    """
    try:
        index = get_index()
        return index.search_advanced(query=query, source=source, variable_name=variable_name)
    except (SearchIndexError, Exception) as e:
        # Fallback to simple search
        if isinstance(e, SearchIndexError):
            logger.warning(f"Advanced search index error, falling back to simple search: {e}")
        else:
            logger.warning(f"Advanced search index failed, falling back to simple search: {e}", exc_info=True)
        if query:
            return search_datasets(query, source=source, use_index=False)
        return list_datasets(source)


def index_dataset_from_manifest(dataset_id: str, manifest_path: str) -> None:
    """
    Index a dataset from its ingestion manifest.
    
    This is called automatically after dataset ingestion.
    """
    try:
        import json
        from pathlib import Path
        from .search_index import get_index
        
        manifest = json.loads(Path(manifest_path).read_text())
        index = get_index()
        
        index.index_dataset(
            dataset_id=manifest.get("dataset_id") or dataset_id,
            source=manifest.get("source") or dataset_id.split(":")[0],
            title=f"{manifest.get('source', 'unknown')} dataset",
            variable_labels=manifest.get("variable_labels", {}),
            value_labels=manifest.get("value_labels", {}),
            license=manifest.get("license"),
            access_mode="manual" if manifest.get("adapter") == "manual" else "direct",
        )
        logger.debug(f"Indexed dataset {dataset_id} from manifest {manifest_path}")
    except Exception as e:
        # Log error but don't fail ingestion if indexing fails
        logger.warning(f"Failed to index dataset {dataset_id} from manifest {manifest_path}: {e}", exc_info=True)

