"""Panneau repliable (collapsible) avec animation."""
from __future__ import annotations

from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QFrame
from PySide6.QtCore import QPropertyAnimation, QEasingCurve, Qt


class CollapsiblePanel(QWidget):
    """GroupBox repliable avec animation de hauteur."""

    def __init__(self, title: str = "", expanded: bool = True, parent=None):
        super().__init__(parent)
        self._expanded = expanded

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._btn = QPushButton(f"{'▼' if expanded else '▶'}  {title}")
        self._btn.setProperty("class", "ghost")
        self._btn.setStyleSheet(
            "text-align:left; padding:10px 14px; font-size:14px; "
            "font-weight:700; border:none; border-radius:8px 8px 0 0;"
        )
        self._btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn.clicked.connect(self._toggle)
        layout.addWidget(self._btn)

        self._content = QFrame()
        self._content.setProperty("card", "true")
        self._content.setStyleSheet("border-top:none; border-radius:0 0 8px 8px;")
        self._content_layout = QVBoxLayout(self._content)
        self._content_layout.setContentsMargins(14, 10, 14, 14)
        self._content_layout.setSpacing(8)
        layout.addWidget(self._content)

        self._title = title
        if not expanded:
            self._content.setMaximumHeight(0)
            self._content.setVisible(False)

    def content_layout(self) -> QVBoxLayout:
        return self._content_layout

    def _toggle(self):
        self._expanded = not self._expanded
        arrow = "▼" if self._expanded else "▶"
        self._btn.setText(f"{arrow}  {self._title}")
        if self._expanded:
            self._content.setVisible(True)
            self._content.setMaximumHeight(16777215)
        else:
            self._content.setMaximumHeight(0)
            self._content.setVisible(False)

    def set_expanded(self, expanded: bool):
        if expanded != self._expanded:
            self._toggle()
