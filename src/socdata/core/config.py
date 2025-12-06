from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class SocDataConfig(BaseModel):
    cache_dir: Path = Field(default=Path.home() / ".socdata")
    timeout_seconds: int = 60
    max_retries: int = 3
    user_agent: str = "socdata/0.1"
    enable_lazy_loading: bool = Field(default=True, description="Enable lazy loading for large datasets")
    cache_ttl_hours: int = Field(default=24, description="Cache time-to-live in hours")
    use_cloud_storage: bool = Field(default=False, description="Use cloud storage for caching")
    log_level: str = Field(default="INFO", description="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)")
    log_file: Optional[Path] = Field(default=None, description="Optional path to log file")


_CONFIG: Optional[SocDataConfig] = None


def get_config() -> SocDataConfig:
    global _CONFIG
    if _CONFIG is not None:
        return _CONFIG

    # Try to load config from file
    env_path = os.getenv("SOCDATA_CONFIG")
    config_data: Dict[str, Any] = {}
    
    if env_path and Path(env_path).exists():
        config_path = Path(env_path)
        try:
            config_data = _load_config_file(config_path)
        except Exception as e:
            # Log error but continue with defaults
            import sys
            print(f"Warning: Failed to load config from {config_path}: {e}", file=sys.stderr)
    
    # Create config with file data and defaults
    config = SocDataConfig(**config_data)
    config.cache_dir.mkdir(parents=True, exist_ok=True)
    
    # Initialize logging with config
    from .logging import setup_logging
    setup_logging(level=config.log_level, log_file=config.log_file)
    
    _CONFIG = config
    return _CONFIG


def _load_config_file(config_path: Path) -> Dict[str, Any]:
    """
    Load configuration from YAML or JSON file.
    
    Args:
        config_path: Path to config file
    
    Returns:
        Dictionary with config values
    
    Raises:
        ValueError: If file format is not supported
        FileNotFoundError: If file does not exist
    """
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")
    
    suffix = config_path.suffix.lower()
    
    if suffix in {".json"}:
        with config_path.open(encoding="utf-8") as f:
            return json.load(f)
    elif suffix in {".yaml", ".yml"}:
        try:
            import yaml
        except ImportError:
            raise ValueError(
                "YAML config requires PyYAML. Install with: pip install pyyaml"
            )
        with config_path.open(encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    else:
        raise ValueError(f"Unsupported config file format: {suffix}. Use .json or .yaml")

