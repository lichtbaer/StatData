"""
Logging infrastructure for socdata.

Provides structured logging with configurable log levels and module-specific loggers.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Optional

from .config import get_config


def setup_logging(
    level: Optional[str] = None,
    log_file: Optional[Path] = None,
    format_string: Optional[str] = None,
) -> None:
    """
    Set up logging configuration for the application.
    
    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL). 
               If None, reads from config or defaults to INFO.
        log_file: Optional path to log file. If None, logs only to stderr.
        format_string: Optional custom format string. If None, uses default.
    """
    if level is None:
        cfg = get_config()
        level_str = getattr(cfg, "log_level", "INFO")
    else:
        level_str = level
    
    log_level = getattr(logging, level_str.upper(), logging.INFO)
    
    if format_string is None:
        format_string = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    handlers: list[logging.Handler] = []
    
    # Console handler (stderr)
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(logging.Formatter(format_string))
    handlers.append(console_handler)
    
    # File handler (if specified)
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(log_level)
        file_handler.setFormatter(logging.Formatter(format_string))
        handlers.append(file_handler)
    
    # Configure root logger
    logging.basicConfig(
        level=log_level,
        handlers=handlers,
        force=True,  # Override any existing configuration
    )


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger for a specific module.
    
    Args:
        name: Logger name (typically __name__ of the module)
    
    Returns:
        Logger instance
    """
    # Ensure logging is set up
    if not logging.root.handlers:
        setup_logging()
    
    return logging.getLogger(name)
