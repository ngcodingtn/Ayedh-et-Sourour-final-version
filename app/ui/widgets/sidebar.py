"""Barre latérale de navigation premium."""
from __future__ import annotations

from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QSpacerItem, QSizePolicy
from PySide6.QtCore import Signal


NAV_ITEMS = [
    ("📊", "Données"),
    ("📐", "Calcul ELU"),
    ("🔩", "Ferraillage"),
    ("🔍", "Fissuration"),
    ("📏", "Vue 2D"),
    ("🧊", "Vue 3D"),
    ("📄", "Rapport"),
]


class Sidebar(QWidget):
    page_changed = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("sidebar")
        self._btns: list[QPushButton] = []

        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        # Logo
        logo = QLabel("FlexiBeam")
        logo.setObjectName("sb_logo")
        lay.addWidget(logo)

        sub = QLabel("Dimensionnement EC2")
        sub.setObjectName("sb_sub")
        lay.addWidget(sub)

        # Section label
        sect = QLabel("NAVIGATION")
        sect.setObjectName("sb_sect")
        lay.addWidget(sect)

        for i, (icon, label) in enumerate(NAV_ITEMS):
            btn = QPushButton(f"  {icon}  {label}")
            btn.setProperty("nav", "true")
            btn.setCursor(self.cursor())
            btn.clicked.connect(lambda checked, idx=i: self._on_click(idx))
            lay.addWidget(btn)
            self._btns.append(btn)

        lay.addSpacerItem(QSpacerItem(0, 0, QSizePolicy.Policy.Minimum,
                                       QSizePolicy.Policy.Expanding))

        # Version
        ver = QLabel("v1.0.0")
        ver.setObjectName("sb_sub")
        lay.addWidget(ver)

        self._set_active(0)

    def _on_click(self, idx: int):
        self._set_active(idx)
        self.page_changed.emit(idx)

    def _set_active(self, idx: int):
        for i, btn in enumerate(self._btns):
            btn.setProperty("active", "true" if i == idx else "false")
            btn.style().unpolish(btn)
            btn.style().polish(btn)

    def set_page(self, idx: int):
        self._set_active(idx)
