"""
Custom exceptions for socdata.
"""

from __future__ import annotations


class SocDataError(Exception):
    """Base exception for all socdata errors."""
    pass


class AdapterNotFoundError(SocDataError):
    """Raised when an adapter cannot be found."""
    pass


class DatasetNotFoundError(SocDataError):
    """Raised when a dataset cannot be found."""
    pass


class ConfigError(SocDataError):
    """Raised when there is a configuration error."""
    pass


class CacheError(SocDataError):
    """Raised when there is a cache-related error."""
    pass


class SearchIndexError(SocDataError):
    """Raised when there is a search index error."""
    pass


class I18nError(SocDataError):
    """Raised when there is an i18n-related error."""
    pass


class ParserError(SocDataError):
    """Raised when there is a parsing error."""
    pass


class DownloadError(SocDataError):
    """Raised when there is a download error."""
    pass


class StorageError(SocDataError):
    """Raised when there is a storage-related error."""
    pass


class MetadataError(SocDataError):
    """Raised when there is a metadata-related error (reading/writing)."""
    pass
