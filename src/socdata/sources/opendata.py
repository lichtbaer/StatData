"""
Generic adapter for Open Data Portals.

Supports various open data portals like data.gov, data.gouv.fr, etc.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

import pandas as pd
import requests

from .base import BaseAdapter
from ..core.config import get_config
from ..core.download import download_file
from ..core.logging import get_logger
from ..core.types import DatasetSummary

logger = get_logger(__name__)


class OpenDataAdapter(BaseAdapter):
    """
    Generic adapter for Open Data Portals.
    
    Supports various open data portals:
    - data.gov (US)
    - data.gouv.fr (France)
    - data.gov.uk (UK)
    - And others via CKAN API
    
    This adapter uses the CKAN API standard which is used by many open data portals.
    """

    CKAN_API_VERSION = "3"

    def __init__(self, portal_url: Optional[str] = None):
        """
        Initialize Open Data adapter.
        
        Args:
            portal_url: Base URL of the open data portal (e.g., 'https://data.gov')
        """
        self.portal_url = portal_url or "https://data.gov"
        # Normalize URL (remove trailing slash)
        self.portal_url = self.portal_url.rstrip("/")
        self.api_url = f"{self.portal_url}/api/{self.CKAN_API_VERSION}/action"

    def list_datasets(self) -> List[DatasetSummary]:
        """
        List available datasets from the open data portal.
        
        Note: This may return a limited set or require API key for full access.
        """
        try:
            cfg = get_config()
            headers = {"User-Agent": cfg.user_agent}
            
            # Try to get package list (datasets)
            response = requests.get(
                f"{self.api_url}/package_list",
                headers=headers,
                timeout=cfg.timeout_seconds,
            )
            response.raise_for_status()
            
            data = response.json()
            if data.get("success") and "result" in data:
                packages = data["result"][:100]  # Limit to first 100 for performance
                return [
                    DatasetSummary(
                        id=f"opendata:{package}",
                        source="opendata",
                        title=package.replace("_", " ").title(),
                    )
                    for package in packages
                ]
        except Exception as e:
            logger.warning(f"Failed to list datasets from {self.portal_url}: {e}")
        
        # Fallback: return empty list or curated examples
        return [
            DatasetSummary(
                id="opendata:example",
                source="opendata",
                title=f"Open Data Portal: {self.portal_url} (use ingest() with URL)",
            ),
        ]

    def load(self, dataset_id: str, *, filters: Dict[str, Any]) -> pd.DataFrame:
        """
        Load dataset from open data portal.
        
        Args:
            dataset_id: Format 'opendata:package-name' or URL
            filters: Optional filters (not typically supported by portals)
        
        Returns:
            DataFrame with the dataset
        """
        parts = dataset_id.split(":")
        if len(parts) < 2:
            raise ValueError(f"Invalid Open Data dataset ID: {dataset_id}")
        
        package_name = parts[1]
        
        # Try to get package metadata
        try:
            cfg = get_config()
            headers = {"User-Agent": cfg.user_agent}
            
            response = requests.get(
                f"{self.api_url}/package_show",
                params={"id": package_name},
                headers=headers,
                timeout=cfg.timeout_seconds,
            )
            response.raise_for_status()
            
            data = response.json()
            if not data.get("success") or "result" not in data:
                raise ValueError(f"Package '{package_name}' not found")
            
            package = data["result"]
            resources = package.get("resources", [])
            
            if not resources:
                raise ValueError(f"No resources found for package '{package_name}'")
            
            # Find CSV or compatible resource
            csv_resource = None
            for resource in resources:
                if resource.get("format", "").upper() in ["CSV", "TSV"]:
                    csv_resource = resource
                    break
            
            if not csv_resource:
                # Use first resource
                csv_resource = resources[0]
            
            # Download and load
            url = csv_resource.get("url")
            if not url:
                raise ValueError(f"No URL found for resource in package '{package_name}'")
            
            # Download to temp location
            from ..core.storage import get_dataset_dir
            
            cache_dir = get_dataset_dir("opendata", package_name, "latest")
            temp_file = cache_dir / "raw" / Path(url).name
            
            if not temp_file.exists():
                download_file(url, temp_file)
            
            # Read the file
            df = pd.read_csv(temp_file)
            
            # Apply filters if provided
            if filters:
                df = self._apply_filters(df, filters)
            
            return df
            
        except Exception as e:
            logger.error(f"Failed to load dataset {dataset_id} from open data portal: {e}", exc_info=True)
            raise

    def _apply_filters(self, df: pd.DataFrame, filters: Dict[str, Any]) -> pd.DataFrame:
        """Apply filters to DataFrame."""
        result = df.copy()
        for key, value in filters.items():
            if key in result.columns:
                if isinstance(value, list):
                    result = result[result[key].isin(value)]
                else:
                    result = result[result[key] == value]
        return result

    def ingest(self, dataset_id: str | None, *, file_path: str) -> pd.DataFrame:
        """
        Ingest dataset from URL or local file.
        
        Args:
            dataset_id: Optional dataset identifier
            file_path: URL or local file path
        
        Returns:
            DataFrame with the dataset
        """
        # If URL, download first
        if file_path.startswith(("http://", "https://")):
            from ..core.storage import get_dataset_dir
            
            dataset_name = dataset_id.split(":")[1] if dataset_id and ":" in dataset_id else "opendata-unknown"
            cache_dir = get_dataset_dir("opendata", dataset_name, "latest")
            temp_file = cache_dir / "raw" / Path(urlparse(file_path).path).name
            
            if not temp_file.exists():
                download_file(file_path, temp_file)
            
            file_path = str(temp_file)
        
        # Read the file
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Detect format and read
        if path.suffix.lower() in [".csv", ".tsv"]:
            df = pd.read_csv(path, sep="\t" if path.suffix.lower() == ".tsv" else ",")
        elif path.suffix.lower() == ".json":
            df = pd.read_json(path)
        elif path.suffix.lower() == ".xlsx":
            df = pd.read_excel(path)
        else:
            # Try CSV as fallback
            df = pd.read_csv(path)
        
        return df
