"""
LibraLog - Library Manager
Entry point for the PySide6 GUI application.
"""

import sys
from pathlib import Path

# Ensure src/ is on sys.path for absolute imports
SRC_DIR = Path(__file__).resolve().parent.parent  # src/ directory
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QApplication


def setup_dark_theme(app: QApplication) -> None:
    """Configure dark theme palette for the application."""
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor(30, 30, 30))
    palette.setColor(QPalette.ColorRole.WindowText, QColor(220, 220, 220))
    palette.setColor(QPalette.ColorRole.Base, QColor(25, 25, 25))
    palette.setColor(QPalette.ColorRole.Text, QColor(220, 220, 220))
    palette.setColor(QPalette.ColorRole.Button, QColor(45, 45, 45))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor(220, 220, 220))
    palette.setColor(QPalette.ColorRole.Highlight, QColor(74, 158, 255))
    app.setPalette(palette)


def main() -> int:
    """Initialize and run the application."""
    QApplication.setApplicationName("LibraLog")
    QApplication.setOrganizationName("RazorBackRoar")
    QApplication.setOrganizationDomain("com.RazorBackRoar.LibraLog")
    QApplication.setApplicationDisplayName("LibraLog - Library Manager")
    
    if hasattr(Qt.ApplicationAttribute, "AA_DontShowIconsInMenus"):
        QApplication.setAttribute(
            Qt.ApplicationAttribute.AA_DontShowIconsInMenus, False
        )
    
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    setup_dark_theme(app)
    
    # TODO: Import and show main window
    # from libralog.gui.main_window import MainWindow
    # window = MainWindow()
    # window.show()
    
    print("LibraLog is not yet implemented.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
