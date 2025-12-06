from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
import requests

try:
    import eurostat  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    eurostat = None  # type: ignore

from .base import BaseAdapter
from ..core.config import get_config
from ..core.exceptions import CacheError, DownloadError, ParserError
from ..core.logging import get_logger
from ..core.types import DatasetSummary

logger = get_logger(__name__)


class EurostatAdapter(BaseAdapter):
    def _get_cached_dataset_list(self) -> Optional[List[Dict[str, str]]]:
        """Get cached dataset list from file."""
        cfg = get_config()
        cache_file = cfg.cache_dir / "eurostat_datasets.json"
        
        if cache_file.exists():
            try:
                with cache_file.open(encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, UnicodeDecodeError) as e:
                # Corrupted cache file - log and return None to regenerate
                logger.warning(f"Failed to parse cached Eurostat dataset list (corrupted): {e}")
                return None
            except (OSError, IOError, PermissionError) as e:
                # File system errors
                logger.warning(f"Failed to read cached Eurostat dataset list (filesystem error): {e}")
                return None
            except Exception as e:
                # Unexpected errors
                logger.error(f"Unexpected error reading cached Eurostat dataset list: {e}", exc_info=True)
                return None
        
        return None

    def _cache_dataset_list(self, datasets: List[Dict[str, str]]) -> None:
        """Cache dataset list to file."""
        cfg = get_config()
        cache_file = cfg.cache_dir / "eurostat_datasets.json"
        
        try:
            cache_file.parent.mkdir(parents=True, exist_ok=True)
            with cache_file.open("w", encoding="utf-8") as f:
                json.dump(datasets, f, indent=2, ensure_ascii=False)
        except (OSError, IOError, PermissionError) as e:
            # File system errors - log but don't fail
            logger.warning(f"Failed to cache Eurostat dataset list (filesystem error): {e}")
        except Exception as e:
            # Unexpected errors
            logger.error(f"Unexpected error caching Eurostat dataset list: {e}", exc_info=True)

    def _fetch_datasets_from_api(self) -> Optional[List[Dict[str, str]]]:
        """Fetch dataset list from Eurostat REST API."""
        try:
            # Eurostat REST API endpoint for dataset list
            url = "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data"
            
            # Get list of datasets - Eurostat API doesn't have a direct list endpoint,
            # but we can try to get metadata for known datasets or use a curated list
            # For now, we'll use a hybrid approach: try API for specific datasets,
            # fall back to curated list
            
            # Try to fetch dataset metadata from Eurostat SDMX API
            sdmx_url = "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/dataflow/ALL"
            
            cfg = get_config()
            headers = {"User-Agent": cfg.user_agent}
            
            try:
                response = requests.get(sdmx_url, headers=headers, timeout=cfg.timeout_seconds)
                response.raise_for_status()
                
                # Parse SDMX XML response
                # Eurostat SDMX API returns XML with dataflow definitions
                try:
                    root = ET.fromstring(response.content)
                    
                    # SDMX namespace
                    namespaces = {
                        'structure': 'http://www.sdmx.org/resources/sdmxml/schemas/v2_1/structure',
                        'common': 'http://www.sdmx.org/resources/sdmxml/schemas/v2_1/common',
                    }
                    
                    # Extract dataflows (datasets)
                    datasets = []
                    # Try to find dataflows in the XML
                    # The exact structure depends on Eurostat's SDMX implementation
                    for dataflow in root.findall('.//structure:Dataflow', namespaces):
                        # Extract ID and name
                        dataflow_id = dataflow.get('id', '')
                        if not dataflow_id:
                            continue
                        
                        # Try to get name from various possible locations
                        name_elem = dataflow.find('.//common:Name', namespaces)
                        if name_elem is None:
                            # Try alternative location
                            name_elem = dataflow.find('.//structure:Name', namespaces)
                        
                        name = name_elem.text if name_elem is not None and name_elem.text else dataflow_id
                        
                        datasets.append({
                            'code': dataflow_id,
                            'title': name.strip() if name else dataflow_id
                        })
                    
                    if datasets:
                        logger.info(f"Successfully fetched {len(datasets)} datasets from Eurostat API")
                        return datasets
                    else:
                        logger.debug("Eurostat SDMX API response received but no datasets found in expected format")
                        return None
                        
                except ET.ParseError as e:
                    # XML parsing error
                    logger.warning(f"Failed to parse Eurostat SDMX XML response: {e}")
                    return None
                except KeyError as e:
                    # Namespace or structure issue
                    logger.debug(f"SDMX XML structure not as expected: {e}, using curated list")
                    return None
                    
            except requests.RequestException as e:
                # Expected network/API errors - log and fallback
                logger.debug(f"Eurostat API request failed: {e}, using curated list")
                return None
            except requests.Timeout as e:
                # Timeout errors
                logger.warning(f"Eurostat API request timed out: {e}, using curated list")
                return None
        except Exception as e:
            # Unexpected errors
            logger.error(f"Unexpected error fetching datasets from Eurostat API: {e}", exc_info=True)
            return None

    def list_datasets(self) -> List[DatasetSummary]:
        """List available Eurostat datasets."""
        # Common Eurostat datasets - curated list
        # This serves as both fallback and primary source until full API integration
        common_datasets = [
            ("une_rt_m", "Unemployment rate - monthly"),
            ("demo_r_pjangroup", "Population on 1 January by age group, sex and NUTS 3 region"),
            ("nama_10_gdp", "GDP and main components"),
            ("nama_10_p3", "Final consumption expenditure of households"),
            ("lfsq_egan2", "Employment by sex, age and educational attainment level"),
            ("ilc_li02", "At-risk-of-poverty rate by poverty threshold, age and sex"),
            ("edat_lfse_03", "Early leavers from education and training by sex and age"),
            ("hlth_silc_10", "Self-perceived health by sex, age and educational attainment level"),
            ("crim_hom_soff", "Intentional homicide offences"),
            ("migr_imm1ctz", "Immigration by age group, sex and citizenship"),
            ("demo_gind", "Demographic balance and crude rates"),
            ("nama_10r_2gdp", "GDP at regional level"),
            ("educ_uoe_enrt01", "Pupils and students enrolled in education"),
            ("hlth_dh010", "Healthcare expenditure"),
            ("env_ac_ainah_r2", "Air emissions accounts by NACE Rev. 2 activity"),
        ]
        
        # Try to get cached list first
        cached = self._get_cached_dataset_list()
        if cached:
            try:
                return [
                    DatasetSummary(id=f"eurostat:{ds['code']}", source="eurostat", title=ds.get("title", ds["code"]))
                    for ds in cached
                ]
            except (KeyError, TypeError) as e:
                # Invalid data structure in cache
                logger.warning(f"Failed to parse cached dataset list (invalid structure): {e}")
            except Exception as e:
                # Unexpected errors
                logger.error(f"Unexpected error parsing cached dataset list: {e}", exc_info=True)
        
        # Try to fetch from API
        api_datasets = self._fetch_datasets_from_api()
        if api_datasets:
            # Cache the API results
            self._cache_dataset_list(api_datasets)
            try:
                return [
                    DatasetSummary(id=f"eurostat:{ds['code']}", source="eurostat", title=ds.get("title", ds["code"]))
                    for ds in api_datasets
                ]
            except (KeyError, TypeError) as e:
                # Invalid data structure from API
                logger.warning(f"Failed to parse API dataset list (invalid structure): {e}")
            except Exception as e:
                # Unexpected errors
                logger.error(f"Unexpected error parsing API dataset list: {e}", exc_info=True)
        
        # Fallback to curated list
        datasets = [
            DatasetSummary(id=f"eurostat:{code}", source="eurostat", title=title)
            for code, title in common_datasets
        ]
        
        # Cache the curated list for future use
        curated_for_cache = [{"code": code, "title": title} for code, title in common_datasets]
        self._cache_dataset_list(curated_for_cache)
        
        return datasets

    def load(self, dataset_id: str, *, filters: Dict[str, Any]) -> pd.DataFrame:
        if eurostat is None:
            raise RuntimeError("eurostat extra not installed. Install with: pip install socdata[eurostat]")
        _, code = dataset_id.split(":", 1)
        # eurostat.get_data_df handles filters via 'filter_pars'
        # eurostat.get_data_df requires dict for filter_pars; pass {} if none
        df = eurostat.get_data_df(code, filter_pars=filters or {})
        return df

    def ingest(self, *, file_path: str) -> pd.DataFrame:  # not applicable
        raise NotImplementedError("Eurostat adapter does not support ingest() from file")

