"""Carte avec ombre portée pour regrouper visuellement du contenu."""
from __future__ import annotations

from PySide6.QtWidgets import QFrame, QVBoxLayout, QLabel, QGraphicsDropShadowEffect
from PySide6.QtGui import QColor
from PySide6.QtCore import Qt

from app.ui.theme import ThemeManager


class CardWidget(QFrame):
    """Carte visuelle réutilisable avec titre optionnel et ombre."""

    def __init__(self, title: str = "", parent=None):
        super().__init__(parent)
        self.setProperty("card", "true")
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(18, 14, 18, 14)
        self._layout.setSpacing(10)

        self._title_label = None
        if title:
            self._title_label = QLabel(title)
            p = ThemeManager.get().p
            self._title_label.setStyleSheet(
                f"font-size:15px; font-weight:700; color:{p.ac}; "
                "background:transparent; margin-bottom:4px;"
            )
            self._layout.addWidget(self._title_label)

        self._apply_shadow()

    def _apply_shadow(self):
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(16)
        shadow.setOffset(0, 2)
        shadow.setColor(QColor(0, 0, 0, 18))
        self.setGraphicsEffect(shadow)

    def content_layout(self) -> QVBoxLayout:
        return self._layout

    def refresh_theme(self):
        if self._title_label:
            p = ThemeManager.get().p
            self._title_label.setStyleSheet(
                f"font-size:15px; font-weight:700; color:{p.ac}; "
                "background:transparent; margin-bottom:4px;"
            )
        self._apply_shadow()
