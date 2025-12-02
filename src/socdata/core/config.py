from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field


class SocDataConfig(BaseModel):
    cache_dir: Path = Field(default=Path.home() / ".socdata")
    timeout_seconds: int = 60
    max_retries: int = 3
    user_agent: str = "socdata/0.1"
    enable_lazy_loading: bool = Field(default=True, description="Enable lazy loading for large datasets")
    cache_ttl_hours: int = Field(default=24, description="Cache time-to-live in hours")
    use_cloud_storage: bool = Field(default=False, description="Use cloud storage for caching")


_CONFIG: Optional[SocDataConfig] = None


def get_config() -> SocDataConfig:
    global _CONFIG
    if _CONFIG is not None:
        return _CONFIG

    env_path = os.getenv("SOCDATA_CONFIG")
    if env_path and Path(env_path).exists():
        # Simple env-based override later can parse YAML/JSON
        pass

    config = SocDataConfig()
    config.cache_dir.mkdir(parents=True, exist_ok=True)
    _CONFIG = config
    return _CONFIG

