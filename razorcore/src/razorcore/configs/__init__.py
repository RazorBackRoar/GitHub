"""
Razorcore Shared Configurations

This module provides shared configuration files for all RazorBackRoar projects.
Instead of symlinks, use `razorcore sync-configs` to copy these to your projects.
"""

import importlib.resources
from pathlib import Path
from typing import Optional


def get_config_path(config_name: str) -> Optional[Path]:
    """
    Get the path to a shared configuration file.
    
    Args:
        config_name: Name of the config file ('pylintrc' or 'pyrightconfig.json')
        
    Returns:
        Path to the config file, or None if not found
    """
    try:
        with importlib.resources.as_file(
            importlib.resources.files(__package__).joinpath(config_name)
        ) as path:
            if path.exists():
                return path
    except (TypeError, FileNotFoundError):
        pass
    
    # Fallback to package directory
    pkg_dir = Path(__file__).parent
    config_path = pkg_dir / config_name
    if config_path.exists():
        return config_path
    
    return None


def get_pylintrc() -> Optional[Path]:
    """Get path to shared .pylintrc configuration."""
    return get_config_path("pylintrc")


def get_pyrightconfig() -> Optional[Path]:
    """Get path to shared pyrightconfig.json."""
    return get_config_path("pyrightconfig.json")


def get_all_configs() -> dict[str, Optional[Path]]:
    """Get all available configuration file paths."""
    return {
        "pylintrc": get_pylintrc(),
        "pyrightconfig.json": get_pyrightconfig(),
    }
