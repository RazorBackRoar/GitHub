"""
razorcore.styling - UI themes and styled widgets.
"""

from razorcore.styling.themes import (
    DARK_PALETTE,
    Theme,
    ThemeManager,
    apply_dark_theme,
    get_dark_stylesheet,
)
from razorcore.styling.widgets import (
    GlassPanel,
    NeonButton,
    StatCard,
    StyledProgressBar,
    UpdateBanner,
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
    "UpdateBanner",
]
