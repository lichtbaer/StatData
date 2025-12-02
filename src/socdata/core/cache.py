from __future__ import annotations

import hashlib
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Optional

from .config import get_config


class CacheManager:
    """
    Cache manager with TTL support and metadata tracking.
    """

    def __init__(self):
        self.config = get_config()
        self.metadata_file = self.config.cache_dir / "cache_metadata.json"
        self.metadata: Dict[str, Dict[str, Any]] = self._load_metadata()

    def _load_metadata(self) -> Dict[str, Dict[str, Any]]:
        """Load cache metadata."""
        if self.metadata_file.exists():
            try:
                with self.metadata_file.open(encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def _save_metadata(self) -> None:
        """Save cache metadata."""
        self.metadata_file.parent.mkdir(parents=True, exist_ok=True)
        with self.metadata_file.open("w", encoding="utf-8") as f:
            json.dump(self.metadata, f, indent=2)

    def _get_cache_key(self, source: str, dataset: str, version: str) -> str:
        """Generate cache key."""
        return f"{source}:{dataset}:{version}"

    def is_valid(self, source: str, dataset: str, version: str = "latest") -> bool:
        """
        Check if cached data is still valid based on TTL.
        
        Args:
            source: Source name
            dataset: Dataset name
            version: Dataset version
        
        Returns:
            True if cache is valid, False otherwise
        """
        cache_key = self._get_cache_key(source, dataset, version)
        
        if cache_key not in self.metadata:
            return False
        
        metadata = self.metadata[cache_key]
        cached_at = datetime.fromisoformat(metadata.get("cached_at", ""))
        ttl_hours = self.config.cache_ttl_hours
        
        age = datetime.now() - cached_at
        return age < timedelta(hours=ttl_hours)

    def mark_cached(
        self,
        source: str,
        dataset: str,
        version: str = "latest",
        size_bytes: Optional[int] = None,
    ) -> None:
        """
        Mark a dataset as cached.
        
        Args:
            source: Source name
            dataset: Dataset name
            version: Dataset version
            size_bytes: Optional file size in bytes
        """
        cache_key = self._get_cache_key(source, dataset, version)
        
        self.metadata[cache_key] = {
            "cached_at": datetime.now().isoformat(),
            "size_bytes": size_bytes,
        }
        
        self._save_metadata()

    def invalidate(self, source: str, dataset: str, version: str = "latest") -> None:
        """
        Invalidate cache for a dataset.
        
        Args:
            source: Source name
            dataset: Dataset name
            version: Dataset version
        """
        cache_key = self._get_cache_key(source, dataset, version)
        
        if cache_key in self.metadata:
            del self.metadata[cache_key]
            self._save_metadata()

    def cleanup_expired(self) -> int:
        """
        Remove expired cache entries.
        
        Returns:
            Number of entries removed
        """
        removed = 0
        ttl_hours = self.config.cache_ttl_hours
        cutoff = datetime.now() - timedelta(hours=ttl_hours)
        
        keys_to_remove = []
        for cache_key, metadata in self.metadata.items():
            cached_at = datetime.fromisoformat(metadata.get("cached_at", ""))
            if cached_at < cutoff:
                keys_to_remove.append(cache_key)
        
        for key in keys_to_remove:
            del self.metadata[key]
            removed += 1
        
        if removed > 0:
            self._save_metadata()
        
        return removed


# Global cache manager instance
_cache_manager: Optional[CacheManager] = None


def get_cache_manager() -> CacheManager:
    """Get or create the global cache manager instance."""
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = CacheManager()
    return _cache_manager
