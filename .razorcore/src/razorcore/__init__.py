"""razorcore - Shared foundation library for RazorBackRoar's macOS Python applications.

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
    updates     - Update checking via GitHub Releases API
    appinfo     - Standardized app metadata, license display, About dialog
"""

__version__ = "1.0.1"
__author__ = "RazorBackRoar"
__license__ = "2025 RazorBackRoar"

from razorcore.appinfo import (
    LICENSE_TEXT,
    AboutDialog,
    AppInfo,
    AppInfoStatusWidget,
    AppMetadata,
    SpaceBarAboutMixin,
    print_startup_info,
)
from razorcore.config import ProjectConfig, get_version
from razorcore.filesystem import (
    check_disk_space,
    compute_file_hash,
    format_file_size,
    generate_unique_filename,
    sanitize_filename,
)
from razorcore.logging import get_logger, setup_logging
from razorcore.threading import AsyncTaskWorker, BaseWorker
from razorcore.updates import (
    UpdateChecker,
    UpdateResult,
    check_for_updates,
    compare_versions,
    is_newer_version,
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
    # Updates
    "UpdateChecker",
    "UpdateResult",
    "check_for_updates",
    "compare_versions",
    "is_newer_version",
    # App Info
    "AppInfo",
    "AppMetadata",
    "AboutDialog",
    "SpaceBarAboutMixin",
    "AppInfoStatusWidget",
    "print_startup_info",
    "LICENSE_TEXT",
]
