"""Barre supérieure de l'application."""
from __future__ import annotations

from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QPushButton, QMenu,
)
from PySide6.QtCore import Signal


class TopBar(QWidget):
    theme_toggled = Signal()
    example_clicked = Signal(str)
    reinit_clicked = Signal()
    open_clicked = Signal()
    save_clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("topbar")

        lay = QHBoxLayout(self)
        lay.setContentsMargins(20, 0, 16, 0)
        lay.setSpacing(12)

        # Titre
        col_titre = QVBoxLayout()
        col_titre.setSpacing(0)
        col_titre.setContentsMargins(0, 8, 0, 8)
        t = QLabel("FlexiBeam")
        t.setObjectName("topbar_title")
        col_titre.addWidget(t)
        s = QLabel("Dimensionnement en flexion simple — Eurocode 2")
        s.setObjectName("topbar_sub")
        col_titre.addWidget(s)
        lay.addLayout(col_titre)

        lay.addStretch()

        # Boutons
        btn_theme = QPushButton("🌗 Thème")
        btn_theme.setToolTip("Basculer thème clair / sombre")
        btn_theme.clicked.connect(self.theme_toggled.emit)
        lay.addWidget(btn_theme)

        # Menu exemples
        btn_ex = QPushButton("📋 Exemples ▾")
        menu = QMenu(self)
        menu.addAction("Rectangulaire", lambda: self.example_clicked.emit("rect"))
        menu.addAction("Section T", lambda: self.example_clicked.emit("T"))
        menu.addAction("Aciers comprimés", lambda: self.example_clicked.emit("comp"))
        menu.addAction("Exemple de la figure", lambda: self.example_clicked.emit("figure"))
        btn_ex.setMenu(menu)
        lay.addWidget(btn_ex)

        btn_open = QPushButton("📂 Ouvrir")
        btn_open.clicked.connect(self.open_clicked.emit)
        lay.addWidget(btn_open)

        btn_save = QPushButton("💾 Sauver")
        btn_save.clicked.connect(self.save_clicked.emit)
        lay.addWidget(btn_save)

        btn_rst = QPushButton("🔄 Réinit.")
        btn_rst.clicked.connect(self.reinit_clicked.emit)
        lay.addWidget(btn_rst)
