"""
Update checker for razorcore-managed applications.

Provides utilities to check for new versions via GitHub Releases API
and compare semantic versions.

Usage:
    from razorcore.updates import UpdateChecker, compare_versions

    # Quick check
    checker = UpdateChecker("4Charm", "5.2.0")
    result = checker.check()
    if result.update_available:
        print(f"Update available: {result.latest_version}")

    # Or use the async worker for background checking
    from razorcore.updates import UpdateCheckerWorker
    worker = UpdateCheckerWorker("4Charm", "5.2.0")
    worker.update_available.connect(on_update_found)
    worker.start()
"""

import json
import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Tuple
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

# GitHub organization for all apps
GITHUB_ORG = "RazorBackRoar"

# Cache duration in seconds (1 hour)
CACHE_DURATION = 3600

# User agent for GitHub API requests
USER_AGENT = "razorcore-update-checker/1.0"


@dataclass
class UpdateResult:
    """Result of an update check."""

    current_version: str
    latest_version: str
    update_available: bool
    download_url: Optional[str] = None
    release_notes: Optional[str] = None
    release_date: Optional[str] = None
    error: Optional[str] = None

    @property
    def is_error(self) -> bool:
        """Check if the update check resulted in an error."""
        return self.error is not None


def parse_version(version: str) -> Tuple[int, int, int]:
    """
    Parse a semantic version string into a tuple of integers.

    Args:
        version: Version string like "1.2.3" or "v1.2.3"

    Returns:
        Tuple of (major, minor, patch)

    Raises:
        ValueError: If version format is invalid
    """
    # Remove leading 'v' if present
    version = version.lstrip('v').strip()

    # Match semver pattern (allowing for optional pre-release/build metadata)
    match = re.match(r'^(\d+)\.(\d+)\.(\d+)', version)
    if not match:
        raise ValueError(f"Invalid version format: {version}")

    return int(match.group(1)), int(match.group(2)), int(match.group(3))


def compare_versions(version1: str, version2: str) -> int:
    """
    Compare two semantic versions.

    Args:
        version1: First version string
        version2: Second version string

    Returns:
        -1 if version1 < version2
         0 if version1 == version2
         1 if version1 > version2

    Example:
        compare_versions("1.0.0", "1.1.0")  # Returns -1
        compare_versions("2.0.0", "1.9.9")  # Returns 1
        compare_versions("1.0.0", "1.0.0")  # Returns 0
    """
    try:
        v1 = parse_version(version1)
        v2 = parse_version(version2)
    except ValueError:
        return 0  # Can't compare invalid versions

    if v1 < v2:
        return -1
    elif v1 > v2:
        return 1
    return 0


def is_newer_version(current: str, latest: str) -> bool:
    """
    Check if latest version is newer than current version.

    Args:
        current: Current installed version
        latest: Latest available version

    Returns:
        True if latest > current
    """
    return compare_versions(current, latest) < 0


class UpdateChecker:
    """
    Check for updates via GitHub Releases API.

    This class provides synchronous update checking. For GUI applications,
    consider using UpdateCheckerWorker which runs in a background thread.

    Attributes:
        app_name: Name of the application (must match GitHub repo name)
        current_version: Currently installed version
        github_org: GitHub organization (default: RazorBackRoar)
        cache_dir: Directory for caching responses

    Example:
        checker = UpdateChecker("4Charm", "5.2.0")
        result = checker.check()

        if result.update_available:
            print(f"New version available: {result.latest_version}")
            print(f"Download: {result.download_url}")
    """

    def __init__(
        self,
        app_name: str,
        current_version: str,
        github_org: str = GITHUB_ORG,
        cache_dir: Optional[Path] = None
    ):
        self.app_name = app_name
        self.current_version = current_version
        self.github_org = github_org
        self.cache_dir = cache_dir or self._default_cache_dir()

    def _default_cache_dir(self) -> Path:
        """Get the default cache directory."""
        # Use ~/Library/Caches/AppName on macOS
        cache_base = Path.home() / "Library" / "Caches" / self.app_name
        cache_base.mkdir(parents=True, exist_ok=True)
        return cache_base

    def _cache_file(self) -> Path:
        """Get the cache file path."""
        return self.cache_dir / "update_check.json"

    def _read_cache(self) -> Optional[dict]:
        """Read cached update check result."""
        cache_file = self._cache_file()

        if not cache_file.exists():
            return None

        try:
            with open(cache_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Check if cache is expired
            if time.time() - data.get("timestamp", 0) > CACHE_DURATION:
                return None

            return data
        except Exception:
            return None

    def _write_cache(self, data: dict) -> None:
        """Write update check result to cache."""
        try:
            cache_data = {**data, "timestamp": time.time()}
            with open(self._cache_file(), "w", encoding="utf-8") as f:
                json.dump(cache_data, f)
        except Exception:
            pass  # Ignore cache write failures

    def _fetch_latest_release(self) -> dict:
        """
        Fetch the latest release from GitHub API.

        Returns:
            Dict containing release info from GitHub API

        Raises:
            URLError: If network request fails
        """
        url = f"https://api.github.com/repos/{self.github_org}/{self.app_name}/releases/latest"

        request = Request(
            url,
            headers={
                "User-Agent": USER_AGENT,
                "Accept": "application/vnd.github.v3+json"
            }
        )

        with urlopen(request, timeout=10) as response:
            return json.loads(response.read().decode("utf-8"))

    def check(self, force: bool = False) -> UpdateResult:
        """
        Check for updates.

        Args:
            force: If True, bypass cache and check directly

        Returns:
            UpdateResult with update information
        """
        # Check cache first (unless forced)
        if not force:
            cached = self._read_cache()
            if cached:
                latest = cached.get("latest_version", self.current_version)
                return UpdateResult(
                    current_version=self.current_version,
                    latest_version=latest,
                    update_available=is_newer_version(self.current_version, latest),
                    download_url=cached.get("download_url"),
                    release_notes=cached.get("release_notes"),
                    release_date=cached.get("release_date")
                )

        try:
            release = self._fetch_latest_release()

            # Parse release data
            latest_version = release.get("tag_name", "").lstrip("v")

            # Find DMG asset
            download_url = None
            for asset in release.get("assets", []):
                if asset.get("name", "").endswith(".dmg"):
                    download_url = asset.get("browser_download_url")
                    break

            # If no DMG, use the HTML URL for the release page
            if not download_url:
                download_url = release.get("html_url")

            result_data = {
                "latest_version": latest_version,
                "download_url": download_url,
                "release_notes": release.get("body"),
                "release_date": release.get("published_at")
            }

            # Cache the result
            self._write_cache(result_data)

            return UpdateResult(
                current_version=self.current_version,
                latest_version=latest_version,
                update_available=is_newer_version(self.current_version, latest_version),
                download_url=download_url,
                release_notes=release.get("body"),
                release_date=release.get("published_at")
            )

        except HTTPError as e:
            if e.code == 404:
                # No releases yet
                return UpdateResult(
                    current_version=self.current_version,
                    latest_version=self.current_version,
                    update_available=False,
                    error="No releases found"
                )
            return UpdateResult(
                current_version=self.current_version,
                latest_version=self.current_version,
                update_available=False,
                error=f"HTTP error: {e.code}"
            )
        except URLError as e:
            return UpdateResult(
                current_version=self.current_version,
                latest_version=self.current_version,
                update_available=False,
                error=f"Network error: {e.reason}"
            )
        except Exception as e:
            return UpdateResult(
                current_version=self.current_version,
                latest_version=self.current_version,
                update_available=False,
                error=str(e)
            )


# PySide6 worker for background update checking
try:
    from PySide6.QtCore import QThread, Signal

    class UpdateCheckerWorker(QThread):
        """
        Background worker for checking updates without blocking the UI.

        Signals:
            update_available(UpdateResult): Emitted when check completes
            error(str): Emitted if an error occurs

        Example:
            worker = UpdateCheckerWorker("4Charm", "5.2.0")
            worker.update_available.connect(self.on_update_result)
            worker.start()

            def on_update_result(self, result: UpdateResult):
                if result.update_available:
                    self.show_update_dialog(result)
        """

        # Signal emitted when update check completes
        update_result = Signal(object)  # UpdateResult

        def __init__(
            self,
            app_name: str,
            current_version: str,
            github_org: str = GITHUB_ORG,
            parent=None
        ):
            super().__init__(parent)
            self.app_name = app_name
            self.current_version = current_version
            self.github_org = github_org
            self._force = False

        def check_now(self, force: bool = False) -> None:
            """Start the update check. Use force=True to bypass cache."""
            self._force = force
            if not self.isRunning():
                self.start()

        def run(self) -> None:
            """Execute the update check in background thread."""
            checker = UpdateChecker(
                self.app_name,
                self.current_version,
                self.github_org
            )
            result = checker.check(force=self._force)
            self.update_result.emit(result)

except ImportError:
    # PySide6 not available - UpdateCheckerWorker won't be available
    pass


def check_for_updates(app_name: str, current_version: str) -> UpdateResult:
    """
    Convenience function to check for updates.

    Args:
        app_name: Name of the application (GitHub repo name)
        current_version: Currently installed version

    Returns:
        UpdateResult with update information

    Example:
        result = check_for_updates("4Charm", "5.2.0")
        if result.update_available:
            print(f"Update to {result.latest_version} available!")
    """
    checker = UpdateChecker(app_name, current_version)
    return checker.check()
