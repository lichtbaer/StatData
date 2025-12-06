from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Optional

import backoff
import requests

from .config import get_config
from .exceptions import DownloadError
from .logging import get_logger

logger = get_logger(__name__)


def _hash_file(path: Path, algo: str = "sha256") -> str:
    hasher = hashlib.new(algo)
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


@backoff.on_exception(backoff.expo, (requests.RequestException,), max_tries=4)
def download_file(url: str, dest: Path, *, expected_checksum: Optional[str] = None) -> Path:
    """
    Download a file from URL with retry logic and optional checksum verification.
    
    Args:
        url: URL to download from
        dest: Destination path for the file
        expected_checksum: Optional SHA256 checksum to verify
    
    Returns:
        Path to downloaded file
    
    Raises:
        DownloadError: If download fails after retries
        ValueError: If checksum verification fails
    """
    cfg = get_config()
    
    try:
        dest.parent.mkdir(parents=True, exist_ok=True)
    except (OSError, PermissionError) as e:
        raise DownloadError(f"Failed to create destination directory {dest.parent}: {e}") from e
    
    headers = {"User-Agent": cfg.user_agent}
    
    try:
        with requests.get(url, headers=headers, timeout=cfg.timeout_seconds, stream=True) as r:
            r.raise_for_status()
            try:
                with dest.open("wb") as f:
                    for chunk in r.iter_content(chunk_size=1024 * 1024):
                        if chunk:
                            f.write(chunk)
            except (OSError, IOError, PermissionError) as e:
                raise DownloadError(f"Failed to write downloaded file to {dest}: {e}") from e
    except requests.Timeout as e:
        raise DownloadError(f"Download timeout for {url}: {e}") from e
    except requests.HTTPError as e:
        raise DownloadError(f"HTTP error downloading {url}: {e}") from e
    except requests.RequestException as e:
        # This will be retried by backoff, but if all retries fail, we get here
        raise DownloadError(f"Failed to download {url} after retries: {e}") from e

    if expected_checksum:
        try:
            actual = _hash_file(dest)
            if actual.lower() != expected_checksum.lower():
                raise ValueError(f"Checksum mismatch for {dest}: {actual} != {expected_checksum}")
        except (OSError, IOError) as e:
            logger.warning(f"Failed to verify checksum for {dest}: {e}")
            # Don't fail download if checksum verification fails due to file system issues
    
    return dest

