"""Badge de statut visuel (vérifié, non vérifié, attention, info)."""
from __future__ import annotations

from PySide6.QtWidgets import QLabel
from PySide6.QtCore import Qt

from app.ui.theme import ThemeManager


class StatusBadge(QLabel):
    """Badge coloré avec texte – styles : ok, error, warning, info."""

    STYLES = {
        "ok":      lambda p: (p.ok, p.tx_on),
        "error":   lambda p: (p.err, p.tx_on),
        "warning": lambda p: (p.warn, p.tx_on),
        "info":    lambda p: (p.ac, p.tx_on),
    }

    def __init__(self, text: str = "", style: str = "info", parent=None):
        super().__init__(text, parent)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._style = style
        self._apply()

    def set_status(self, text: str, style: str = "info"):
        self.setText(text)
        self._style = style
        self._apply()

    def _apply(self):
        p = ThemeManager.get().p
        fn = self.STYLES.get(self._style, self.STYLES["info"])
        bg, fg = fn(p)
        self.setStyleSheet(
            f"background:{bg}; color:{fg}; padding:5px 16px; "
            f"border-radius:12px; font-weight:700; font-size:12px;"
        )
