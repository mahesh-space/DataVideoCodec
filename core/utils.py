"""
Utility functions for the DataVideoCodec System.

Provides helper functions for hashing, directory management,
and cross-platform path handling.
"""

import hashlib
import logging
from pathlib import Path
from typing import Optional


def compute_hash(filepath: Path) -> str:
    """Compute SHA-256 hash of a file.

    Args:
        filepath: Path to the file to hash.

    Returns:
        Hex-encoded SHA-256 hash string.
    """
    filepath = Path(filepath)
    sha256 = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def compute_bytes_hash(data: bytes) -> str:
    """Compute SHA-256 hash of raw bytes.

    Args:
        data: Byte data to hash.

    Returns:
        Hex-encoded SHA-256 hash string.
    """
    return hashlib.sha256(data).hexdigest()


def ensure_dir(path: Path) -> Path:
    """Create directory (and parents) if it doesn't exist.

    Args:
        path: Directory path to ensure exists.

    Returns:
        The same path for chaining.
    """
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def setup_logging(level: str = "INFO") -> logging.Logger:
    """Set up and return the application logger.

    Args:
        level: Logging level string (DEBUG, INFO, WARNING, ERROR).

    Returns:
        Configured logger instance.
    """
    logger = logging.getLogger("DataVideoCodec")
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%H:%M:%S",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    return logger


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """Get a child logger for a specific module.

    Args:
        name: Module name for the child logger.

    Returns:
        Logger instance.
    """
    parent = logging.getLogger("DataVideoCodec")
    if name:
        return parent.getChild(name)
    return parent
