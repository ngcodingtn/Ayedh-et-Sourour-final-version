"""Carte de métrique pour afficher une valeur-clé avec label et unité."""
from __future__ import annotations

from PySide6.QtWidgets import QFrame, QVBoxLayout, QLabel, QGraphicsDropShadowEffect
from PySide6.QtGui import QColor
from PySide6.QtCore import Qt

from app.ui.theme import ThemeManager


class MetricCard(QFrame):
    """Affiche une valeur-clé style dashboard : label / valeur / unité."""

    def __init__(self, label: str = "", value: str = "—", unit: str = "",
                 accent: str = "", parent=None):
        super().__init__(parent)
        self.setProperty("metric", "true")

        lay = QVBoxLayout(self)
        lay.setContentsMargins(16, 12, 16, 12)
        lay.setSpacing(2)
        lay.setAlignment(Qt.AlignmentFlag.AlignCenter)

        p = ThemeManager.get().p
        c = accent or p.ac

        self._lbl = QLabel(label)
        self._lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._lbl.setStyleSheet(
            f"font-size:11px; font-weight:600; color:{p.tx2}; "
            "text-transform:uppercase; letter-spacing:0.5px; background:transparent;"
        )
        lay.addWidget(self._lbl)

        self._val = QLabel(value)
        self._val.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._val.setStyleSheet(
            f"font-size:22px; font-weight:700; color:{c}; background:transparent;"
        )
        lay.addWidget(self._val)

        self._unit = QLabel(unit)
        self._unit.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._unit.setStyleSheet(
            f"font-size:11px; color:{p.txm}; background:transparent;"
        )
        lay.addWidget(self._unit)

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(12)
        shadow.setOffset(0, 2)
        shadow.setColor(QColor(0, 0, 0, 14))
        self.setGraphicsEffect(shadow)

    def set_value(self, value: str, accent: str = ""):
        p = ThemeManager.get().p
        c = accent or p.ac
        self._val.setText(value)
        self._val.setStyleSheet(
            f"font-size:22px; font-weight:700; color:{c}; background:transparent;"
        )

    def set_label(self, label: str):
        self._lbl.setText(label)

    def set_unit(self, unit: str):
        self._unit.setText(unit)
