"""
razorcore - Shared foundation library for RazorBackRoar's macOS Python applications.

This package provides common utilities, UI components, and build tools used across:
- 4Charm (4chan media downloader)
- Nexus (Safari URL automation)
- Papyrus (HTML converter)
- PyPixPro (Photo organization)
- iSort (Apple device file organizer)

Modules:
    config      - Project configuration and version management
    logging     - Unified logging setup
    threading   - Base QThread worker classes
    filesystem  - Safe file operations and hashing
    styling     - UI themes and styled widgets
    build       - DMG creation and build utilities
    configs     - Shared configuration files (pylintrc, pyrightconfig.json)
    cli         - Command-line tools (razorcore sync-configs, verify, commit-all)
"""

__version__ = "1.0.0"
__author__ = "RazorBackRoar"

from razorcore.config import ProjectConfig, get_version
from razorcore.logging import setup_logging, get_logger
from razorcore.threading import BaseWorker, AsyncTaskWorker
from razorcore.filesystem import (
    sanitize_filename,
    generate_unique_filename,
    compute_file_hash,
    check_disk_space,
    format_file_size,
)

__all__ = [
    # Config
    "ProjectConfig",
    "get_version",
    # Logging
    "setup_logging",
    "get_logger",
    # Threading
    "BaseWorker",
    "AsyncTaskWorker",
    # Filesystem
    "sanitize_filename",
    "generate_unique_filename",
    "compute_file_hash",
    "check_disk_space",
    "format_file_size",
]
