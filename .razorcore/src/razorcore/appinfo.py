"""
Standardized application information and metadata for RazorBackRoar apps.

This module provides:
- Centralized license information ("2025 RazorBackRoar")
- App bundle size and modification date detection
- Startup info display (version, license, size, date)
- About dialog with space bar trigger
- Standardized app metadata across all projects

Usage:
    from razorcore.appinfo import AppInfo, AboutDialog, print_startup_info

    # Print startup info to console
    print_startup_info("MyApp")

    # Create about dialog
    dialog = AboutDialog(parent_window, "MyApp")
    dialog.exec()

    # Get app info programmatically
    info = AppInfo.get_app_info("MyApp")
"""

import os
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QKeyEvent
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from razorcore.config import get_version

# =============================================================================
# Constants
# =============================================================================

LICENSE_TEXT = "2025 RazorBackRoar"
COPYRIGHT_FULL = f"© {LICENSE_TEXT}. All rights reserved."
ORGANIZATION = "RazorBackRoar"


# =============================================================================
# App Information
# =============================================================================

@dataclass
class AppMetadata:
    """Holds standardized application metadata."""

    name: str
    version: str
    license: str
    bundle_size: str
    last_modified: str
    architecture: str = "ARM64 (Apple Silicon)"

    def to_display_lines(self) -> list[str]:
        """Return the four standardized display lines."""
        return [
            f"Version {self.version}",
            self.license,
            f"Size: {self.bundle_size}",
            f"Modified: {self.last_modified}",
        ]

    def to_console_output(self) -> str:
        """Format for console output."""
        lines = [
            "",
            "━" * 40,
            f"  {self.name}",
            "━" * 40,
            f"  Version:  {self.version}",
            f"  License:  {self.license}",
            f"  Size:     {self.bundle_size}",
            f"  Modified: {self.last_modified}",
            f"  Arch:     {self.architecture}",
            "━" * 40,
            "",
        ]
        return "\n".join(lines)


class AppInfo:
    """
    Utility class for retrieving standardized application information.

    All RazorBackRoar apps use this for consistent metadata display.
    """

    @staticmethod
    def get_bundle_path(app_name: str) -> Optional[Path]:
        """
        Find the .app bundle path for a running application.

        Works both in development (returns project root) and
        when running as a bundled .app.
        """
        # Check if running as bundled app
        if getattr(sys, "frozen", False):
            # Running as py2app bundle
            # sys.executable is inside AppName.app/Contents/MacOS/
            exe_path = Path(sys.executable)
            # Go up to .app directory
            for parent in exe_path.parents:
                if parent.suffix == ".app":
                    return parent
        else:
            # Development mode - look for project directory
            # Try to find based on common patterns
            cwd = Path.cwd()
            for search_dir in [cwd, cwd.parent, Path(__file__).parent.parent.parent]:
                if (search_dir / "pyproject.toml").exists():
                    return search_dir

        return None

    @staticmethod
    def get_bundle_size(app_name: str) -> str:
        """
        Get the compressed/actual size of the app bundle.

        Returns human-readable size string (e.g., "45.2 MB").
        """
        bundle_path = AppInfo.get_bundle_path(app_name)

        if bundle_path is None:
            return "N/A"

        try:
            if bundle_path.suffix == ".app":
                # Sum all files in the .app bundle
                total_size = 0
                for f in bundle_path.rglob("*"):
                    if f.is_file():
                        total_size += f.stat().st_size
            else:
                # Development mode - sum src/ directory
                src_dir = bundle_path / "src"
                if src_dir.exists():
                    total_size = sum(
                        f.stat().st_size
                        for f in src_dir.rglob("*")
                        if f.is_file()
                    )
                else:
                    total_size = 0

            return AppInfo._format_size(total_size)
        except Exception:
            return "N/A"

    @staticmethod
    def get_last_modified(app_name: str) -> str:
        """
        Get the last modification date of the app bundle.

        Returns formatted date string (e.g., "Dec 12, 2025").
        """
        bundle_path = AppInfo.get_bundle_path(app_name)

        if bundle_path is None:
            return "N/A"

        try:
            if bundle_path.suffix == ".app":
                # Get newest modification time from bundle
                newest_time = 0.0
                for f in bundle_path.rglob("*"):
                    if f.is_file():
                        mtime = f.stat().st_mtime
                        if mtime > newest_time:
                            newest_time = mtime
                mod_time = datetime.fromtimestamp(newest_time)
            else:
                # Development mode - use pyproject.toml mtime
                pyproject = bundle_path / "pyproject.toml"
                if pyproject.exists():
                    mod_time = datetime.fromtimestamp(pyproject.stat().st_mtime)
                else:
                    mod_time = datetime.now()

            return mod_time.strftime("%b %d, %Y")
        except Exception:
            return "N/A"

    @staticmethod
    def _format_size(size_bytes: int) -> str:
        """Format bytes to human-readable size."""
        for unit in ["B", "KB", "MB", "GB"]:
            if size_bytes < 1024:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024
        return f"{size_bytes:.1f} TB"

    @classmethod
    def get_app_info(cls, app_name: str) -> AppMetadata:
        """
        Get complete standardized app information.

        Args:
            app_name: The application name (e.g., "4Charm", "iSort").

        Returns:
            AppMetadata instance with all standardized fields.
        """
        version = get_version(default="1.0.0")
        bundle_size = cls.get_bundle_size(app_name)
        last_modified = cls.get_last_modified(app_name)

        return AppMetadata(
            name=app_name,
            version=version,
            license=LICENSE_TEXT,
            bundle_size=bundle_size,
            last_modified=last_modified,
        )


# =============================================================================
# Console Output
# =============================================================================

def print_startup_info(app_name: str) -> None:
    """
    Print standardized startup information to console.

    This should be called at application startup to display:
    - Version number
    - License (2025 RazorBackRoar)
    - Bundle size
    - Last modified date

    Args:
        app_name: The application name.

    Example:
        def main():
            print_startup_info("iSort")
            app = QApplication(sys.argv)
            ...
    """
    info = AppInfo.get_app_info(app_name)
    print(info.to_console_output())


# =============================================================================
# About Dialog
# =============================================================================

class AboutDialog(QDialog):
    """
    Standardized About dialog for all RazorBackRoar applications.

    Displays:
    - Application name and icon
    - Version number
    - License (2025 RazorBackRoar)
    - Bundle size
    - Last modified date

    Usage:
        dialog = AboutDialog(parent, "MyApp")
        dialog.exec()

    Or trigger via space bar in main window:
        class MainWindow(QMainWindow):
            def keyPressEvent(self, event):
                if event.key() == Qt.Key_Space:
                    AboutDialog(self, "MyApp").exec()
    """

    def __init__(self, parent: Optional[QWidget] = None, app_name: str = "App"):
        super().__init__(parent)
        self.app_name = app_name
        self.info = AppInfo.get_app_info(app_name)
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Set up the dialog UI."""
        self.setWindowTitle(f"About {self.app_name}")
        self.setFixedSize(400, 300)
        self.setWindowFlags(
            Qt.WindowType.Dialog
            | Qt.WindowType.WindowCloseButtonHint
        )

        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(32, 32, 32, 32)

        # App name (large)
        name_label = QLabel(self.app_name)
        name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        name_label.setStyleSheet("""
            font-size: 28px;
            font-weight: bold;
            color: #76e648;
        """)
        layout.addWidget(name_label)

        # Info lines
        for line in self.info.to_display_lines():
            label = QLabel(line)
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            label.setStyleSheet("""
                font-size: 14px;
                color: #cccccc;
            """)
            layout.addWidget(label)

        # Architecture
        arch_label = QLabel(f"Built for {self.info.architecture}")
        arch_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        arch_label.setStyleSheet("""
            font-size: 12px;
            color: #888888;
            margin-top: 8px;
        """)
        layout.addWidget(arch_label)

        layout.addStretch()

        # Copyright
        copyright_label = QLabel(COPYRIGHT_FULL)
        copyright_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        copyright_label.setStyleSheet("""
            font-size: 11px;
            color: #666666;
        """)
        layout.addWidget(copyright_label)

        # Close button
        close_btn = QPushButton("OK")
        close_btn.setFixedWidth(100)
        close_btn.clicked.connect(self.accept)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #76e648;
                color: #1a1a1a;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #8af050;
            }
        """)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(close_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        # Style the dialog
        self.setStyleSheet("""
            QDialog {
                background-color: #1a1a1a;
            }
        """)


# =============================================================================
# Space Bar Handler Mixin
# =============================================================================

class SpaceBarAboutMixin:
    """
    Mixin class that adds space bar -> About dialog functionality.

    Add this mixin to your MainWindow class to automatically show
    the About dialog when the user presses the space bar.

    Usage:
        from razorcore.appinfo import SpaceBarAboutMixin

        class MainWindow(SpaceBarAboutMixin, QMainWindow):
            APP_NAME = "MyApp"

            def __init__(self):
                super().__init__()
                ...

    The space bar will now trigger the About dialog.
    """

    APP_NAME: str = "App"  # Override in subclass

    def keyPressEvent(self, event: QKeyEvent) -> None:
        """Handle key press events - show About on space bar."""
        if event.key() == Qt.Key.Key_Space:
            self._show_about_dialog()
        else:
            # Call parent's keyPressEvent if it exists
            parent_handler = getattr(super(), "keyPressEvent", None)
            if parent_handler:
                parent_handler(event)

    def _show_about_dialog(self) -> None:
        """Show the About dialog."""
        app_name = getattr(self, "APP_NAME", "App")
        dialog = AboutDialog(self, app_name)  # type: ignore
        dialog.exec()


# =============================================================================
# Status Bar Widget
# =============================================================================

class AppInfoStatusWidget(QWidget):
    """
    A compact status bar widget showing app info.

    Displays version and license in a single line, suitable for
    embedding in a status bar.

    Usage:
        status_widget = AppInfoStatusWidget("MyApp")
        self.statusBar().addPermanentWidget(status_widget)
    """

    def __init__(self, app_name: str, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.info = AppInfo.get_app_info(app_name)
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Set up the widget UI."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 0, 8, 0)
        layout.setSpacing(12)

        version_label = QLabel(f"v{self.info.version}")
        version_label.setStyleSheet("color: #76e648; font-size: 11px;")

        separator = QLabel("|")
        separator.setStyleSheet("color: #666666; font-size: 11px;")

        license_label = QLabel(self.info.license)
        license_label.setStyleSheet("color: #888888; font-size: 11px;")

        layout.addWidget(version_label)
        layout.addWidget(separator)
        layout.addWidget(license_label)
