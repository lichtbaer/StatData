from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Optional

import backoff
import requests

from .config import get_config


def _hash_file(path: Path, algo: str = "sha256") -> str:
    hasher = hashlib.new(algo)
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


@backoff.on_exception(backoff.expo, (requests.RequestException,), max_tries=4)
def download_file(url: str, dest: Path, *, expected_checksum: Optional[str] = None) -> Path:
    cfg = get_config()
    dest.parent.mkdir(parents=True, exist_ok=True)
    headers = {"User-Agent": cfg.user_agent}
    with requests.get(url, headers=headers, timeout=cfg.timeout_seconds, stream=True) as r:
        r.raise_for_status()
        with dest.open("wb") as f:
            for chunk in r.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    f.write(chunk)

    if expected_checksum:
        actual = _hash_file(dest)
        if actual.lower() != expected_checksum.lower():
            raise ValueError(f"Checksum mismatch for {dest}: {actual} != {expected_checksum}")
    return dest

