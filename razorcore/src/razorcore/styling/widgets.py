"""
Shared styled widgets for consistent UI across applications.

Provides:
- NeonButton: Button with glow effect on hover
- GlassPanel: Semi-transparent panel with colored border
- StatCard: Statistic display card with animations
- StyledProgressBar: Enhanced progress bar
"""

from typing import Optional

from PySide6.QtCore import (
    QAbstractAnimation,
    QEasingCurve,
    QPropertyAnimation,
    Qt,
    QVariantAnimation,
    Signal,
)
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QFrame,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)


class NeonButton(QPushButton):
    """
    A custom button with a neon glow effect on hover.

    Features:
    - Animated glow on hover
    - Customizable color
    - Gradient background

    Example:
        button = NeonButton("Click Me", color="#00f5ff")
        button.clicked.connect(my_handler)
    """

    def __init__(
        self,
        text: str = "",
        color: str = "#76e648",
        parent: Optional[QWidget] = None
    ):
        super().__init__(text, parent)
        self.color = color
        self.glow_radius = 25
        self.animation_duration = 200

        self._setup_shadow_effect()
        self._update_style()
        self._setup_animations()

    def _setup_shadow_effect(self) -> None:
        """Initialize the glow shadow effect."""
        self.shadow = QGraphicsDropShadowEffect()
        self.shadow.setBlurRadius(0)
        self.shadow.setOffset(0, 0)
        self.shadow.setColor(QColor(self.color))
        self.setGraphicsEffect(self.shadow)

    def _update_style(self) -> None:
        """Update button stylesheet based on current color."""
        darker = QColor(self.color).darker(150).name()

        self.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(
                    x1:0, y1:0, x2:0, y2:1,
                    stop:0 {self.color}, stop:1 {darker}
                );
                color: #1a1a1a;
                border: none;
                border-radius: 8px;
                padding: 10px 20px;
                font-weight: bold;
                font-size: 14px;
            }}
            QPushButton:pressed {{
                background: {darker};
            }}
            QPushButton:disabled {{
                background: rgba(100,100,100,0.5);
                color: rgba(255,255,255,0.5);
            }}
        """)

    def _setup_animations(self) -> None:
        """Setup hover animations."""
        self.glow_in_anim = QPropertyAnimation(self.shadow, b"blurRadius")
        self.glow_in_anim.setDuration(self.animation_duration)
        self.glow_in_anim.setEndValue(self.glow_radius)
        self.glow_in_anim.setEasingCurve(QEasingCurve.Type.OutCubic)

        self.glow_out_anim = QPropertyAnimation(self.shadow, b"blurRadius")
        self.glow_out_anim.setDuration(self.animation_duration)
        self.glow_out_anim.setEndValue(0)
        self.glow_out_anim.setEasingCurve(QEasingCurve.Type.OutCubic)

    def set_color(self, color: str) -> None:
        """Change the button color."""
        self.color = color
        self.shadow.setColor(QColor(color))
        self._update_style()

    def enterEvent(self, event) -> None:
        """Start glow animation on mouse enter."""
        self.glow_out_anim.stop()
        self.glow_in_anim.setStartValue(self.shadow.blurRadius())
        self.glow_in_anim.start()
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:
        """Fade glow on mouse leave."""
        self.glow_in_anim.stop()
        self.glow_out_anim.setStartValue(self.shadow.blurRadius())
        self.glow_out_anim.start()
        super().leaveEvent(event)


class GlassPanel(QFrame):
    """
    A semi-transparent panel with a colored border.

    Used as a container for sections in the UI.

    Example:
        panel = GlassPanel(border_color="#76e648")
        layout = QVBoxLayout(panel)
        layout.addWidget(my_content)
    """

    def __init__(
        self,
        border_color: str = "#76e648",
        parent: Optional[QWidget] = None
    ):
        super().__init__(parent)
        self.border_color = border_color
        self.setObjectName("GlassPanel")
        self._update_style()

    def _update_style(self) -> None:
        """Update panel stylesheet."""
        self.setStyleSheet(f"""
            QFrame#GlassPanel {{
                background-color: rgba(30, 30, 30, 0.8);
                border: 2px solid {self.border_color};
                border-radius: 12px;
            }}
        """)

    def set_border_color(self, color: str) -> None:
        """Change the border color."""
        self.border_color = color
        self._update_style()


class StatCard(QFrame):
    """
    A statistic display card with interactive styling and animations.

    Features:
    - Animated value changes
    - Hover effects
    - Click signal
    - Icon support

    Example:
        card = StatCard(
            key="downloads",
            label="Downloads",
            icon="📥",
            accent_color="#4a9eff"
        )
        card.set_value(42)
        card.clicked.connect(handle_card_click)
    """

    clicked = Signal(str)  # Emits the card's key

    def __init__(
        self,
        key: str,
        label: str,
        icon: str = "📊",
        accent_color: str = "#4a9eff",
        tooltip: str = "",
        parent: Optional[QWidget] = None
    ):
        super().__init__(parent)
        self.key = key
        self.accent_color = accent_color
        self._current_value = 0
        self._value_anim: Optional[QVariantAnimation] = None

        self._setup_ui(label, icon)
        self._apply_shadow()

        if tooltip:
            self.setToolTip(tooltip)

        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def _setup_ui(self, label: str, icon: str) -> None:
        """Build the card UI."""
        self.setObjectName("StatCard")
        self.setStyleSheet(f"""
            QFrame#StatCard {{
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:1,
                    stop:0 #26262c, stop:1 #1f1f24
                );
                border-radius: 14px;
                border: 1px solid #32323a;
            }}
        """)
        self.setFixedHeight(110)
        self.setMinimumWidth(180)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(14)

        # Left side: value and label
        left_layout = QVBoxLayout()
        left_layout.setSpacing(6)

        self.value_label = QLabel("0")
        self.value_label.setStyleSheet("""
            QLabel {
                font-size: 34px;
                font-weight: 800;
                color: #f7f7f7;
            }
        """)

        self.text_label = QLabel(label)
        self.text_label.setStyleSheet("""
            QLabel {
                font-size: 13px;
                color: #b8b8c7;
                font-weight: 600;
            }
        """)

        left_layout.addWidget(self.value_label)
        left_layout.addWidget(self.text_label)

        # Right side: icon
        self.icon_label = QLabel(icon)
        self.icon_label.setStyleSheet(f"""
            QLabel {{
                font-size: 26px;
                color: {self.accent_color};
            }}
        """)
        self.icon_label.setAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        )

        layout.addLayout(left_layout, 1)
        layout.addWidget(self.icon_label)

    def _apply_shadow(self) -> None:
        """Add drop shadow effect."""
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(24)
        shadow.setColor(Qt.GlobalColor.black)
        shadow.setOffset(0, 6)
        self.setGraphicsEffect(shadow)

    def value(self) -> int:
        """Get current value."""
        return self._current_value

    def set_value(self, value: int, animate: bool = True) -> None:
        """
        Set the displayed value.

        Args:
            value: New value to display.
            animate: Whether to animate the transition.
        """
        old_value = self._current_value
        self._current_value = value

        # Update opacity based on value
        if value == 0:
            self.setWindowOpacity(0.8)
            self.icon_label.setStyleSheet(f"""
                QLabel {{
                    font-size: 26px;
                    color: {self.accent_color}AA;
                }}
            """)
        else:
            self.setWindowOpacity(1.0)
            self.icon_label.setStyleSheet(f"""
                QLabel {{
                    font-size: 26px;
                    color: {self.accent_color};
                }}
            """)

        if animate and old_value != value:
            self._animate_value(old_value, value)
        else:
            self.value_label.setText(str(value))

    def _animate_value(self, old: int, new: int) -> None:
        """Animate value change."""
        if self._value_anim and self._value_anim.state() == QAbstractAnimation.State.Running:
            self._value_anim.stop()

        self._value_anim = QVariantAnimation(self)
        self._value_anim.setStartValue(old)
        self._value_anim.setEndValue(new)
        self._value_anim.setDuration(200)
        self._value_anim.setEasingCurve(QEasingCurve.Type.OutQuad)
        self._value_anim.valueChanged.connect(
            lambda v: self.value_label.setText(str(int(v)))
        )
        self._value_anim.start()

    def mousePressEvent(self, event) -> None:
        """Handle click."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.key)
        super().mousePressEvent(event)

    def enterEvent(self, event) -> None:
        """Highlight on hover."""
        self.setStyleSheet(f"""
            QFrame#StatCard {{
                background-color: #323232;
                border-radius: 14px;
                border-left: 5px solid {self.accent_color};
            }}
        """)
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:
        """Remove highlight on leave."""
        self.setStyleSheet(f"""
            QFrame#StatCard {{
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:1,
                    stop:0 #26262c, stop:1 #1f1f24
                );
                border-radius: 14px;
                border: 1px solid #32323a;
            }}
        """)
        super().leaveEvent(event)


class StyledProgressBar(QProgressBar):
    """
    Enhanced progress bar with gradient styling.

    Example:
        progress = StyledProgressBar(accent_color="#76e648")
        progress.setValue(50)
    """

    def __init__(
        self,
        accent_color: str = "#76e648",
        height: int = 20,
        parent: Optional[QWidget] = None
    ):
        super().__init__(parent)
        self.accent_color = accent_color
        self.setFixedHeight(height)
        self.setTextVisible(False)
        self._update_style()

    def _update_style(self) -> None:
        """Update progress bar stylesheet."""
        self.setStyleSheet(f"""
            QProgressBar {{
                border: none;
                border-radius: 10px;
                background-color: #2d2d2d;
            }}
            QProgressBar::chunk {{
                border-radius: 10px;
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 {self.accent_color},
                    stop:1 {QColor(self.accent_color).lighter(120).name()}
                );
            }}
        """)

    def set_accent_color(self, color: str) -> None:
        """Change the accent color."""
        self.accent_color = color
        self._update_style()


class UpdateBanner(QFrame):
    """
    A notification banner for displaying update availability.

    Features:
    - Animated slide-in
    - Download button
    - Dismiss button
    - Auto-check on startup

    Example:
        from razorcore.styling.widgets import UpdateBanner
        from razorcore.updates import UpdateCheckerWorker

        # In your MainWindow __init__:
        self.update_banner = UpdateBanner()
        self.update_banner.download_clicked.connect(self.open_download_url)
        self.layout().insertWidget(0, self.update_banner)

        # Start background check
        self.update_worker = UpdateCheckerWorker("4Charm", "5.2.0")
        self.update_worker.update_result.connect(self.update_banner.show_if_available)
        self.update_worker.start()
    """

    download_clicked = Signal(str)  # Emits download URL
    dismissed = Signal()

    def __init__(
        self,
        accent_color: str = "#4a9eff",
        parent: Optional[QWidget] = None
    ):
        super().__init__(parent)
        self.accent_color = accent_color
        self._download_url = ""
        self._setup_ui()
        self.hide()  # Hidden by default

    def _setup_ui(self) -> None:
        """Build the banner UI."""
        self.setObjectName("UpdateBanner")
        self.setStyleSheet(f"""
            QFrame#UpdateBanner {{
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #1a3a5c, stop:1 #0d2137
                );
                border: 1px solid {self.accent_color};
                border-radius: 8px;
                padding: 8px;
            }}
        """)
        self.setFixedHeight(50)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(12)

        # Icon
        icon_label = QLabel("🔄")
        icon_label.setStyleSheet("font-size: 18px;")
        layout.addWidget(icon_label)

        # Message
        self.message_label = QLabel("A new version is available!")
        self.message_label.setStyleSheet(f"""
            QLabel {{
                color: #ffffff;
                font-size: 13px;
                font-weight: 500;
            }}
        """)
        layout.addWidget(self.message_label, 1)

        # Download button
        self.download_btn = QPushButton("Download")
        self.download_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.download_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.accent_color};
                color: #ffffff;
                border: none;
                border-radius: 4px;
                padding: 6px 16px;
                font-weight: bold;
                font-size: 12px;
            }}
            QPushButton:hover {{
                background-color: {QColor(self.accent_color).lighter(120).name()};
            }}
        """)
        self.download_btn.clicked.connect(self._on_download_clicked)
        layout.addWidget(self.download_btn)

        # Dismiss button
        dismiss_btn = QPushButton("✕")
        dismiss_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        dismiss_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #888888;
                border: none;
                font-size: 14px;
                padding: 4px 8px;
            }
            QPushButton:hover {
                color: #ffffff;
            }
        """)
        dismiss_btn.clicked.connect(self._on_dismiss)
        layout.addWidget(dismiss_btn)

    def show_update(self, version: str, download_url: str = "") -> None:
        """
        Show the update banner with version info.

        Args:
            version: The new version string
            download_url: URL to download the update
        """
        self._download_url = download_url
        self.message_label.setText(f"Version {version} is available!")
        self.show()

    def show_if_available(self, result) -> None:
        """
        Show banner if update result indicates an update is available.

        Designed to connect directly to UpdateCheckerWorker.update_result signal.

        Args:
            result: UpdateResult from razorcore.updates
        """
        if hasattr(result, 'update_available') and result.update_available:
            self._download_url = getattr(result, 'download_url', '') or ''
            self.message_label.setText(
                f"Version {result.latest_version} is available!"
            )
            self.show()

    def _on_download_clicked(self) -> None:
        """Handle download button click."""
        if self._download_url:
            self.download_clicked.emit(self._download_url)
            # Also try to open in browser
            try:
                import webbrowser
                webbrowser.open(self._download_url)
            except Exception:
                pass

    def _on_dismiss(self) -> None:
        """Handle dismiss button click."""
        self.hide()
        self.dismissed.emit()
