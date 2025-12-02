from datetime import datetime, timedelta

from socdata.core.cache import get_cache_manager


def test_cache_is_valid():
    """Test cache validity checking."""
    cache = get_cache_manager()
    
    # Mark as cached
    cache.mark_cached("test_source", "test_dataset", "latest")
    
    # Should be valid immediately
    assert cache.is_valid("test_source", "test_dataset", "latest")
    
    # Invalidate
    cache.invalidate("test_source", "test_dataset", "latest")
    
    # Should not be valid after invalidation
    assert not cache.is_valid("test_source", "test_dataset", "latest")


def test_cache_cleanup_expired(monkeypatch):
    """Test cleanup of expired cache entries."""
    cache = get_cache_manager()
    
    # Mark as cached
    cache.mark_cached("test_source", "test_dataset", "latest")
    
    # Manually set old timestamp in metadata
    cache_key = "test_source:test_dataset:latest"
    old_time = (datetime.now() - timedelta(days=2)).isoformat()
    cache.metadata[cache_key]["cached_at"] = old_time
    
    # Cleanup should remove expired entries
    removed = cache.cleanup_expired()
    assert removed >= 1
