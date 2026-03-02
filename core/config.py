"""
Configuration management for the DataVideoCodec System.

Handles loading, saving, and providing defaults for user-configurable
settings persisted in a JSON config file.
"""

import json
from pathlib import Path
from typing import Any, Dict, Optional


# Default configuration values
DEFAULT_CONFIG = {
    "output_dir": "",
    "default_resolution": "720p",
    "default_block_size": 4,
    "default_ecc_overhead": 0.2,
    "default_fps": 30,
    "ffmpeg_path": "ffmpeg",
    "theme": "dark",
    "log_level": "INFO",
}

# Config file location (next to main.py)
_CONFIG_DIR = Path(__file__).parent.parent
CONFIG_FILE = _CONFIG_DIR / "config.json"


def load_config(config_path: Optional[Path] = None) -> Dict[str, Any]:
    """Load configuration from JSON file.

    If the config file does not exist, returns default configuration
    and creates the file with defaults.

    Args:
        config_path: Path to config file. Defaults to config.json in project root.

    Returns:
        Dictionary of configuration values.
    """
    path = Path(config_path) if config_path else CONFIG_FILE
    if path.exists():
        try:
            with open(path, "r", encoding="utf-8") as f:
                user_config = json.load(f)
            # Merge with defaults to fill any missing keys
            config = {**DEFAULT_CONFIG, **user_config}
            return config
        except (json.JSONDecodeError, IOError):
            return dict(DEFAULT_CONFIG)
    else:
        # Create default config file
        save_config(DEFAULT_CONFIG, path)
        return dict(DEFAULT_CONFIG)


def save_config(config: Dict[str, Any], config_path: Optional[Path] = None) -> None:
    """Save configuration to JSON file.

    Args:
        config: Dictionary of configuration values.
        config_path: Path to config file. Defaults to config.json in project root.
    """
    path = Path(config_path) if config_path else CONFIG_FILE
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)


def get_config_value(key: str, config_path: Optional[Path] = None) -> Any:
    """Get a single configuration value.

    Args:
        key: Configuration key to retrieve.
        config_path: Path to config file.

    Returns:
        The configuration value, or the default if not found.
    """
    config = load_config(config_path)
    return config.get(key, DEFAULT_CONFIG.get(key))
