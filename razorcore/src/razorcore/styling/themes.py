"""
Unified dark theme system for macOS applications.

Provides:
- Predefined color palettes
- Theme configuration and management
- Stylesheet generation
- Easy theme application to QApplication
"""

from dataclasses import dataclass, field
from typing import Dict, Optional

from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QApplication


@dataclass
class ColorPalette:
    """
    Color palette for application theming.
    
    Follows a consistent naming convention across all apps.
    """
    
    # Background colors
    bg_primary: str = "#1a1a1a"      # Main background
    bg_secondary: str = "#242424"    # Secondary panels
    bg_tertiary: str = "#2d2d2d"     # Input fields, cards
    bg_hover: str = "#353535"        # Hover states
    
    # Text colors
    text_primary: str = "#ffffff"    # Main text
    text_secondary: str = "#cccccc"  # Secondary text
    text_muted: str = "#888888"      # Muted/hint text
    text_disabled: str = "#666666"   # Disabled text
    
    # Accent colors
    accent_primary: str = "#76e648"  # Primary accent (green)
    accent_secondary: str = "#4a9eff"  # Secondary accent (blue)
    accent_warning: str = "#ffa502"  # Warning (orange)
    accent_error: str = "#ff4757"    # Error (red)
    accent_success: str = "#22c55e"  # Success (green)
    
    # Border colors
    border_default: str = "#404040"
    border_focus: str = "#76e648"
    border_error: str = "#ff4757"
    
    # Special
    shadow: str = "#000000"
    selection: str = "#76e648"


# Predefined palettes
DARK_PALETTE = ColorPalette()

NEON_BLUE_PALETTE = ColorPalette(
    accent_primary="#00f5ff",
    accent_secondary="#9933ff",
    border_focus="#00f5ff",
    selection="#00f5ff",
)

NEON_GREEN_PALETTE = ColorPalette(
    accent_primary="#39ff14",
    accent_secondary="#ffff00",
    border_focus="#39ff14",
    selection="#39ff14",
)

HOT_PINK_PALETTE = ColorPalette(
    accent_primary="#ff2d92",
    accent_secondary="#b200ff",
    border_focus="#ff2d92",
    selection="#ff2d92",
)


@dataclass
class Theme:
    """
    Complete theme definition with colors and styling options.
    """
    
    name: str
    palette: ColorPalette = field(default_factory=ColorPalette)
    border_radius: int = 8
    glow_radius: int = 25
    animation_duration: int = 200
    font_family: str = "-apple-system, BlinkMacSystemFont, 'SF Pro Display', 'Segoe UI', sans-serif"
    mono_font: str = "'SF Mono', 'Monaco', 'Menlo', 'Consolas', monospace"


class ThemeManager:
    """
    Manages application theming.
    
    Usage:
        manager = ThemeManager(app)
        manager.apply_theme(Theme("Dark", DARK_PALETTE))
    """
    
    PREDEFINED_THEMES = {
        "dark": Theme("Dark", DARK_PALETTE),
        "neon_blue": Theme("Neon Blue", NEON_BLUE_PALETTE),
        "neon_green": Theme("Neon Green", NEON_GREEN_PALETTE),
        "hot_pink": Theme("Hot Pink", HOT_PINK_PALETTE),
    }
    
    def __init__(self, app: Optional[QApplication] = None):
        self.app = app or QApplication.instance()
        self.current_theme: Optional[Theme] = None
    
    def apply_theme(self, theme: Theme) -> None:
        """Apply a theme to the application."""
        if self.app is None:
            return
        
        self.current_theme = theme
        
        # Apply Qt palette
        palette = self._create_palette(theme.palette)
        self.app.setPalette(palette)
        
        # Apply stylesheet
        stylesheet = get_dark_stylesheet(theme)
        self.app.setStyleSheet(stylesheet)
    
    def apply_preset(self, name: str) -> None:
        """Apply a predefined theme by name."""
        theme = self.PREDEFINED_THEMES.get(name.lower())
        if theme:
            self.apply_theme(theme)
    
    def _create_palette(self, colors: ColorPalette) -> QPalette:
        """Create a QPalette from a ColorPalette."""
        palette = QPalette()
        
        palette.setColor(QPalette.ColorRole.Window, QColor(colors.bg_primary))
        palette.setColor(QPalette.ColorRole.WindowText, QColor(colors.text_primary))
        palette.setColor(QPalette.ColorRole.Base, QColor(colors.bg_tertiary))
        palette.setColor(QPalette.ColorRole.AlternateBase, QColor(colors.bg_secondary))
        palette.setColor(QPalette.ColorRole.Text, QColor(colors.text_primary))
        palette.setColor(QPalette.ColorRole.Button, QColor(colors.bg_secondary))
        palette.setColor(QPalette.ColorRole.ButtonText, QColor(colors.text_primary))
        palette.setColor(QPalette.ColorRole.Highlight, QColor(colors.accent_primary))
        palette.setColor(QPalette.ColorRole.HighlightedText, QColor(colors.bg_primary))
        palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(colors.bg_secondary))
        palette.setColor(QPalette.ColorRole.ToolTipText, QColor(colors.text_primary))
        palette.setColor(QPalette.ColorRole.PlaceholderText, QColor(colors.text_muted))
        
        return palette


def get_dark_stylesheet(theme: Optional[Theme] = None) -> str:
    """
    Generate a comprehensive dark theme stylesheet.
    
    Args:
        theme: Theme to use (defaults to dark theme).
        
    Returns:
        CSS-like stylesheet string for Qt.
    """
    if theme is None:
        theme = Theme("Dark", DARK_PALETTE)
    
    p = theme.palette
    r = theme.border_radius
    
    return f"""
    /* === Global === */
    QWidget {{
        background-color: {p.bg_primary};
        color: {p.text_primary};
        font-family: {theme.font_family};
    }}
    
    /* === Main Window === */
    QMainWindow {{
        background-color: {p.bg_primary};
    }}
    
    /* === Group Boxes === */
    QGroupBox {{
        border: 2px solid {p.accent_primary};
        border-radius: {r}px;
        margin-top: 12px;
        padding-top: 8px;
        font-weight: bold;
    }}
    QGroupBox::title {{
        subcontrol-origin: padding;
        left: 12px;
        padding: 0 8px;
        color: {p.accent_primary};
    }}
    
    /* === Buttons === */
    QPushButton {{
        background-color: {p.bg_tertiary};
        color: {p.text_primary};
        border: none;
        border-radius: {r}px;
        padding: 10px 20px;
        font-weight: 600;
        min-height: 36px;
    }}
    QPushButton:hover {{
        background-color: {p.bg_hover};
    }}
    QPushButton:pressed {{
        background-color: {p.accent_primary};
        color: {p.bg_primary};
    }}
    QPushButton:disabled {{
        background-color: {p.bg_secondary};
        color: {p.text_disabled};
    }}
    
    /* === Primary Button === */
    QPushButton[primary="true"], QPushButton#primaryBtn {{
        background-color: {p.accent_primary};
        color: {p.bg_primary};
        font-weight: 700;
    }}
    QPushButton[primary="true"]:hover, QPushButton#primaryBtn:hover {{
        background-color: {p.accent_success};
    }}
    
    /* === Danger Button === */
    QPushButton[danger="true"], QPushButton#dangerBtn {{
        background-color: {p.accent_error};
        color: {p.text_primary};
    }}
    
    /* === Text Inputs === */
    QLineEdit, QTextEdit, QPlainTextEdit {{
        background-color: {p.bg_tertiary};
        color: {p.text_primary};
        border: 1px solid {p.border_default};
        border-radius: {r}px;
        padding: 8px 12px;
        selection-background-color: {p.selection};
    }}
    QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {{
        border: 2px solid {p.border_focus};
        background-color: {p.bg_hover};
    }}
    
    /* === Progress Bar === */
    QProgressBar {{
        border: none;
        border-radius: {r}px;
        background-color: {p.bg_tertiary};
        text-align: center;
        min-height: 20px;
        color: {p.text_primary};
    }}
    QProgressBar::chunk {{
        border-radius: {r}px;
        background-color: {p.accent_primary};
    }}
    
    /* === Labels === */
    QLabel {{
        color: {p.text_secondary};
    }}
    QLabel[heading="true"] {{
        color: {p.accent_primary};
        font-size: 24px;
        font-weight: bold;
    }}
    
    /* === Tabs === */
    QTabWidget::pane {{
        border: none;
        background-color: {p.bg_secondary};
        border-radius: {r}px;
    }}
    QTabBar::tab {{
        background-color: transparent;
        color: {p.text_muted};
        padding: 10px 20px;
        border: none;
    }}
    QTabBar::tab:selected {{
        background-color: {p.accent_secondary};
        color: {p.text_primary};
        border-radius: {r}px;
    }}
    QTabBar::tab:hover:!selected {{
        color: {p.text_primary};
    }}
    
    /* === Combo Box === */
    QComboBox {{
        background-color: {p.bg_tertiary};
        color: {p.text_primary};
        border: 1px solid {p.border_default};
        border-radius: {r}px;
        padding: 8px 12px;
        min-width: 120px;
    }}
    QComboBox::drop-down {{
        border: none;
        padding-right: 8px;
    }}
    QComboBox QAbstractItemView {{
        background-color: {p.bg_tertiary};
        color: {p.text_primary};
        selection-background-color: {p.accent_primary};
    }}
    
    /* === Check Box === */
    QCheckBox {{
        color: {p.text_primary};
        spacing: 8px;
    }}
    QCheckBox::indicator {{
        width: 18px;
        height: 18px;
        border-radius: 4px;
        border: 2px solid {p.border_default};
        background-color: {p.bg_tertiary};
    }}
    QCheckBox::indicator:checked {{
        background-color: {p.accent_primary};
        border-color: {p.accent_primary};
    }}
    
    /* === Scroll Bar === */
    QScrollBar:vertical {{
        background: {p.bg_secondary};
        width: 12px;
        margin: 0;
        border-radius: 6px;
    }}
    QScrollBar::handle:vertical {{
        background: {p.bg_hover};
        min-height: 20px;
        border-radius: 6px;
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0;
    }}
    QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
        background: none;
    }}
    
    /* === Status Bar === */
    QStatusBar {{
        background-color: {p.bg_secondary};
        color: {p.text_muted};
        border-top: 1px solid {p.border_default};
    }}
    
    /* === Menu === */
    QMenu {{
        background-color: {p.bg_secondary};
        color: {p.text_primary};
        border: 1px solid {p.border_default};
        border-radius: {r}px;
        padding: 4px;
    }}
    QMenu::item {{
        padding: 8px 24px;
        border-radius: 4px;
    }}
    QMenu::item:selected {{
        background-color: {p.accent_primary};
        color: {p.bg_primary};
    }}
    
    /* === Tooltips === */
    QToolTip {{
        background-color: {p.bg_secondary};
        color: {p.text_primary};
        border: 1px solid {p.border_default};
        border-radius: 4px;
        padding: 4px 8px;
    }}
    """


def apply_dark_theme(app: Optional[QApplication] = None) -> None:
    """
    Quick function to apply the default dark theme.
    
    Args:
        app: QApplication instance (uses current if None).
        
    Example:
        from razorcore.styling import apply_dark_theme
        app = QApplication(sys.argv)
        apply_dark_theme(app)
    """
    manager = ThemeManager(app)
    manager.apply_preset("dark")
