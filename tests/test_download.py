"""Tests for socdata.core.download module."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import requests

from socdata.core.download import download_file, _hash_file
from socdata.core.exceptions import DownloadError


def test_hash_file(tmp_path):
    """Test file hashing."""
    test_file = tmp_path / "test.txt"
    test_file.write_text("test content", encoding="utf-8")
    
    hash_value = _hash_file(test_file)
    assert isinstance(hash_value, str)
    assert len(hash_value) == 64  # SHA256 produces 64 hex characters


def test_hash_file_different_content(tmp_path):
    """Test that different content produces different hashes."""
    file1 = tmp_path / "test1.txt"
    file1.write_text("content 1", encoding="utf-8")
    
    file2 = tmp_path / "test2.txt"
    file2.write_text("content 2", encoding="utf-8")
    
    hash1 = _hash_file(file1)
    hash2 = _hash_file(file2)
    
    assert hash1 != hash2


def test_hash_file_same_content(tmp_path):
    """Test that same content produces same hash."""
    file1 = tmp_path / "test1.txt"
    file1.write_text("same content", encoding="utf-8")
    
    file2 = tmp_path / "test2.txt"
    file2.write_text("same content", encoding="utf-8")
    
    hash1 = _hash_file(file1)
    hash2 = _hash_file(file2)
    
    assert hash1 == hash2


def test_download_file_success(tmp_path, monkeypatch):
    """Test successful file download."""
    monkeypatch.setenv("SOCDATA_CACHE_DIR", str(tmp_path))
    
    dest = tmp_path / "downloaded.txt"
    test_content = b"test content"
    
    # Mock requests.get
    mock_response = MagicMock()
    mock_response.__enter__ = MagicMock(return_value=mock_response)
    mock_response.__exit__ = MagicMock(return_value=None)
    mock_response.raise_for_status = MagicMock()
    mock_response.iter_content = MagicMock(return_value=[test_content])
    
    with patch("socdata.core.download.requests.get", return_value=mock_response):
        result = download_file("http://example.com/test.txt", dest)
        assert result == dest
        assert dest.exists()
        assert dest.read_bytes() == test_content


def test_download_file_with_checksum(tmp_path, monkeypatch):
    """Test file download with checksum verification."""
    monkeypatch.setenv("SOCDATA_CACHE_DIR", str(tmp_path))
    
    dest = tmp_path / "downloaded.txt"
    test_content = b"test content"
    
    # Calculate expected checksum
    expected_checksum = _hash_file(Path("/dev/null"))  # We'll mock this
    # Actually calculate it properly
    import hashlib
    hasher = hashlib.sha256()
    hasher.update(test_content)
    expected_checksum = hasher.hexdigest()
    
    mock_response = MagicMock()
    mock_response.__enter__ = MagicMock(return_value=mock_response)
    mock_response.__exit__ = MagicMock(return_value=None)
    mock_response.raise_for_status = MagicMock()
    mock_response.iter_content = MagicMock(return_value=[test_content])
    
    with patch("socdata.core.download.requests.get", return_value=mock_response):
        result = download_file("http://example.com/test.txt", dest, expected_checksum=expected_checksum)
        assert result == dest
        assert dest.exists()


def test_download_file_checksum_mismatch(tmp_path, monkeypatch):
    """Test file download with checksum mismatch."""
    monkeypatch.setenv("SOCDATA_CACHE_DIR", str(tmp_path))
    
    dest = tmp_path / "downloaded.txt"
    test_content = b"test content"
    wrong_checksum = "wrong_checksum_value"
    
    mock_response = MagicMock()
    mock_response.__enter__ = MagicMock(return_value=mock_response)
    mock_response.__exit__ = MagicMock(return_value=None)
    mock_response.raise_for_status = MagicMock()
    mock_response.iter_content = MagicMock(return_value=[test_content])
    
    with patch("socdata.core.download.requests.get", return_value=mock_response):
        with pytest.raises(ValueError, match="Checksum mismatch"):
            download_file("http://example.com/test.txt", dest, expected_checksum=wrong_checksum)


def test_download_file_http_error(tmp_path, monkeypatch):
    """Test file download with HTTP error."""
    monkeypatch.setenv("SOCDATA_CACHE_DIR", str(tmp_path))
    
    dest = tmp_path / "downloaded.txt"
    
    mock_response = MagicMock()
    mock_response.__enter__ = MagicMock(return_value=mock_response)
    mock_response.__exit__ = MagicMock(return_value=None)
    mock_response.raise_for_status = MagicMock(side_effect=requests.HTTPError("404 Not Found"))
    mock_response.iter_content = MagicMock(return_value=[])
    
    with patch("socdata.core.download.requests.get", return_value=mock_response):
        # backoff will retry, but eventually raise
        with pytest.raises(requests.RequestException):
            download_file("http://example.com/notfound.txt", dest)


def test_download_file_creates_parent_dirs(tmp_path, monkeypatch):
    """Test that download creates parent directories."""
    monkeypatch.setenv("SOCDATA_CACHE_DIR", str(tmp_path))
    
    dest = tmp_path / "subdir" / "nested" / "downloaded.txt"
    test_content = b"test content"
    
    mock_response = MagicMock()
    mock_response.__enter__ = MagicMock(return_value=mock_response)
    mock_response.__exit__ = MagicMock(return_value=None)
    mock_response.raise_for_status = MagicMock()
    mock_response.iter_content = MagicMock(return_value=[test_content])
    
    with patch("socdata.core.download.requests.get", return_value=mock_response):
        result = download_file("http://example.com/test.txt", dest)
        assert result == dest
        assert dest.exists()
        assert dest.parent.exists()


def test_download_file_uses_user_agent(tmp_path, monkeypatch):
    """Test that download uses configured user agent."""
    monkeypatch.setenv("SOCDATA_CACHE_DIR", str(tmp_path))
    
    dest = tmp_path / "downloaded.txt"
    test_content = b"test content"
    
    mock_response = MagicMock()
    mock_response.__enter__ = MagicMock(return_value=mock_response)
    mock_response.__exit__ = MagicMock(return_value=None)
    mock_response.raise_for_status = MagicMock()
    mock_response.iter_content = MagicMock(return_value=[test_content])
    
    with patch("socdata.core.download.requests.get", return_value=mock_response) as mock_get:
        download_file("http://example.com/test.txt", dest)
        
        # Verify that requests.get was called with headers containing user agent
        call_args = mock_get.call_args
        assert "headers" in call_args.kwargs
        assert "User-Agent" in call_args.kwargs["headers"]


def test_download_file_uses_timeout(tmp_path, monkeypatch):
    """Test that download uses configured timeout."""
    monkeypatch.setenv("SOCDATA_CACHE_DIR", str(tmp_path))
    
    dest = tmp_path / "downloaded.txt"
    test_content = b"test content"
    
    mock_response = MagicMock()
    mock_response.__enter__ = MagicMock(return_value=mock_response)
    mock_response.__exit__ = MagicMock(return_value=None)
    mock_response.raise_for_status = MagicMock()
    mock_response.iter_content = MagicMock(return_value=[test_content])
    
    with patch("socdata.core.download.requests.get", return_value=mock_response) as mock_get:
        download_file("http://example.com/test.txt", dest)
        
        # Verify that requests.get was called with timeout
        call_args = mock_get.call_args
        assert "timeout" in call_args.kwargs
        assert call_args.kwargs["timeout"] > 0


def test_download_file_streaming(tmp_path, monkeypatch):
    """Test that download uses streaming."""
    monkeypatch.setenv("SOCDATA_CACHE_DIR", str(tmp_path))
    
    dest = tmp_path / "downloaded.txt"
    test_content = b"test content"
    
    mock_response = MagicMock()
    mock_response.__enter__ = MagicMock(return_value=mock_response)
    mock_response.__exit__ = MagicMock(return_value=None)
    mock_response.raise_for_status = MagicMock()
    mock_response.iter_content = MagicMock(return_value=[test_content])
    
    with patch("socdata.core.download.requests.get", return_value=mock_response) as mock_get:
        download_file("http://example.com/test.txt", dest)
        
        # Verify that requests.get was called with stream=True
        call_args = mock_get.call_args
        assert "stream" in call_args.kwargs
        assert call_args.kwargs["stream"] is True
