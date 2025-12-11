"""
razorcore.styling - UI themes and styled widgets.
"""

from razorcore.styling.themes import (
    Theme,
    ThemeManager,
    DARK_PALETTE,
    get_dark_stylesheet,
    apply_dark_theme,
)
from razorcore.styling.widgets import (
    NeonButton,
    GlassPanel,
    StatCard,
    StyledProgressBar,
)

__all__ = [
    # Themes
    "Theme",
    "ThemeManager",
    "DARK_PALETTE",
    "get_dark_stylesheet",
    "apply_dark_theme",
    # Widgets
    "NeonButton",
    "GlassPanel",
    "StatCard",
    "StyledProgressBar",
]
