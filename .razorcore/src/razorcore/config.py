"""
Project configuration and version management.

Provides utilities for reading project metadata from pyproject.toml
and managing application configuration.
"""

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional

try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib  # type: ignore


@dataclass
class ProjectConfig:
    """
    Holds project configuration loaded from pyproject.toml.
    
    Usage:
        config = ProjectConfig.from_pyproject()
        print(config.name, config.version)
    """
    
    name: str = ""
    version: str = "0.0.0"
    description: str = ""
    authors: list = field(default_factory=list)
    requires_python: str = ">=3.10"
    
    # App-specific settings
    app_name: str = ""
    organization: str = ""
    domain: str = ""
    
    @classmethod
    def from_pyproject(
        cls,
        pyproject_path: Optional[Path] = None,
        search_depth: int = 4
    ) -> "ProjectConfig":
        """
        Load configuration from pyproject.toml.
        
        Args:
            pyproject_path: Direct path to pyproject.toml. If None, searches upward.
            search_depth: How many parent directories to search.
            
        Returns:
            ProjectConfig instance with loaded values.
        """
        if pyproject_path is None:
            pyproject_path = cls._find_pyproject(search_depth)
        
        if pyproject_path is None or not pyproject_path.exists():
            return cls()
        
        try:
            with open(pyproject_path, "rb") as f:
                data = tomllib.load(f)
            
            project = data.get("project", {})
            
            return cls(
                name=project.get("name", ""),
                version=project.get("version", "0.0.0"),
                description=project.get("description", ""),
                authors=project.get("authors", []),
                requires_python=project.get("requires-python", ">=3.10"),
                app_name=project.get("name", ""),
                organization=project.get("name", ""),
                domain=f"{project.get('name', 'app').lower()}.com",
            )
        except Exception:
            return cls()
    
    @staticmethod
    def _find_pyproject(search_depth: int = 4) -> Optional[Path]:
        """Search for pyproject.toml in parent directories."""
        current = Path(__file__).resolve()
        
        for _ in range(search_depth):
            current = current.parent
            candidate = current / "pyproject.toml"
            if candidate.exists():
                return candidate
        
        return None


def get_version(
    default: str = "0.0.0",
    pyproject_path: Optional[Path] = None,
    search_depth: int = 5
) -> str:
    """
    Get project version from pyproject.toml.
    
    This is the primary function used by applications to get their version
    at runtime, supporting both development and bundled (py2app) scenarios.
    
    Args:
        default: Fallback version if pyproject.toml cannot be read.
        pyproject_path: Direct path to pyproject.toml. If None, searches upward.
        search_depth: How many parent directories to search.
        
    Returns:
        Version string (e.g., "1.2.3").
        
    Example:
        # In your main.py:
        from razorcore import get_version
        VERSION = get_version(default="1.0.0")
    """
    # First, try importlib.metadata (works for installed packages)
    try:
        from importlib.metadata import version as pkg_version, PackageNotFoundError
        # Try common package names
        for pkg_name in ("razorcore",):
            try:
                return pkg_version(pkg_name)
            except PackageNotFoundError:
                continue
    except ImportError:
        pass
    
    # Fallback: read from pyproject.toml
    if pyproject_path is None:
        # Search from the calling module's location
        import inspect
        frame = inspect.currentframe()
        if frame and frame.f_back:
            caller_file = frame.f_back.f_globals.get("__file__")
            if caller_file:
                start_path = Path(caller_file).resolve().parent
                for _ in range(search_depth):
                    candidate = start_path / "pyproject.toml"
                    if candidate.exists():
                        pyproject_path = candidate
                        break
                    start_path = start_path.parent
    
    if pyproject_path and pyproject_path.exists():
        try:
            with open(pyproject_path, "rb") as f:
                data = tomllib.load(f)
            return data.get("project", {}).get("version", default)
        except Exception:
            pass
    
    # Last resort: try regex on pyproject.toml content
    try:
        # Search in common locations relative to cwd
        for candidate in [
            Path.cwd() / "pyproject.toml",
            Path.cwd().parent / "pyproject.toml",
        ]:
            if candidate.exists():
                content = candidate.read_text(encoding="utf-8")
                match = re.search(r'version\s*=\s*"([^"]+)"', content)
                if match:
                    return match.group(1)
    except Exception:
        pass
    
    return default


def get_pyproject_value(key: str, default: Any = None, section: str = "project") -> Any:
    """
    Get a specific value from pyproject.toml.
    
    Args:
        key: The key to look up (e.g., "name", "version").
        default: Default value if key not found.
        section: The TOML section (default: "project").
        
    Returns:
        The value from pyproject.toml or the default.
    """
    config = ProjectConfig.from_pyproject()
    return getattr(config, key, default)
