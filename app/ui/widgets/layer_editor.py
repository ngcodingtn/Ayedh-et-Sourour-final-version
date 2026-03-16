"""Éditeur de lits d'armatures – version tableau avec positions verticales."""
from __future__ import annotations

import math

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
)
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QColor

from app.constants import AVAILABLE_DIAMETERS_MM
from app.core.reinforcement_layers import (
    ReinforcementLayer, TypeLit,
    recompute_layer_levels, validate_layer_spacing,
    compute_auto_first_distance_cm,
)
from app.ui.theme import ThemeManager

# Colonnes du tableau
_HEADERS = [
    "Lit", "Nb barres", "Diamètre", "As unit.\n(cm²)", "As lit\n(cm²)",
    "Type", "Dist. précéd.\n(cm)", "Dist. fibre\ntendue (cm)",
    "d du lit\n(cm)", "Statut",
]


class LayerEditor(QWidget):
    """Éditeur de lits d'armatures avec tableau, dialogue d'ajout et
    gestion complète des positions verticales."""

    layers_changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._layers: list[ReinforcementLayer] = []
        self._c_nom_mm: float = 30.0
        self._diam_etrier_mm: float = 8.0
        self._h_mm: float = 600.0
        self._d_mm: float = 540.0

        self._build_ui()

    # ── Construction UI ──────────────────────────────────────────────
    def _build_ui(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(6)

        # Barre de boutons
        btn_bar = QHBoxLayout()
        btn_bar.setSpacing(6)

        btn_add = QPushButton("➕  Ajouter un lit")
        btn_add.clicked.connect(self._on_add)
        btn_bar.addWidget(btn_add)

        btn_edit = QPushButton("✏  Modifier")
        btn_edit.setProperty("class", "secondary")
        btn_edit.clicked.connect(self._on_edit)
        btn_bar.addWidget(btn_edit)

        btn_del = QPushButton("🗑  Supprimer")
        btn_del.setProperty("class", "danger")
        btn_del.clicked.connect(self._on_delete)
        btn_bar.addWidget(btn_del)

        btn_up = QPushButton("▲  Monter")
        btn_up.setProperty("class", "secondary")
        btn_up.clicked.connect(self._on_move_up)
        btn_bar.addWidget(btn_up)

        btn_down = QPushButton("▼  Descendre")
        btn_down.setProperty("class", "secondary")
        btn_down.clicked.connect(self._on_move_down)
        btn_bar.addWidget(btn_down)

        btn_bar.addStretch()
        lay.addLayout(btn_bar)

        # Tableau
        self._table = QTableWidget()
        self._table.setColumnCount(len(_HEADERS))
        self._table.setHorizontalHeaderLabels(_HEADERS)
        self._table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self._table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._table.setAlternatingRowColors(True)
        self._table.verticalHeader().setVisible(False)
        self._table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self._table.doubleClicked.connect(self._on_edit)
        lay.addWidget(self._table, 1)

        # Résumé bas
        summary = QHBoxLayout()
        self._lbl_total = QLabel("Total : —")
        self._lbl_total.setStyleSheet("font-weight:600; font-size:13px; background:transparent;")
        summary.addWidget(self._lbl_total)

        self._lbl_d_reel = QLabel("d réel : —")
        self._lbl_d_reel.setStyleSheet("font-weight:600; font-size:13px; background:transparent;")
        summary.addWidget(self._lbl_d_reel)

        self._lbl_validation = QLabel("")
        self._lbl_validation.setStyleSheet("font-size:12px; background:transparent;")
        summary.addWidget(self._lbl_validation)

        summary.addStretch()
        lay.addLayout(summary)

    # ── Paramètres géométriques ──────────────────────────────────────
    def set_geometry_params(
        self,
        h_mm: float,
        d_mm: float,
        c_nom_mm: float,
        diam_etrier_mm: float,
    ):
        """Met à jour les paramètres géométriques utilisés."""
        self._h_mm = h_mm
        self._d_mm = d_mm
        self._c_nom_mm = c_nom_mm
        self._diam_etrier_mm = diam_etrier_mm
        self._recompute()

    # ── Actions ──────────────────────────────────────────────────────
    def _on_add(self):
        from app.ui.widgets.layer_dialog import LayerDialog
        is_first = len(self._layers) == 0
        dlg = LayerDialog(
            self,
            is_first=is_first,
            c_nom_mm=self._c_nom_mm,
            diam_etrier_mm=self._diam_etrier_mm,
        )
        if dlg.exec():
            layer = dlg.get_layer_data()
            self._layers.append(layer)
            self._recompute()

    def _on_edit(self):
        row = self._selected_row()
        if row < 0:
            return
        from app.ui.widgets.layer_dialog import LayerDialog
        is_first = (row == 0)
        dlg = LayerDialog(
            self,
            is_first=is_first,
            edit_data=self._layers[row],
            c_nom_mm=self._c_nom_mm,
            diam_etrier_mm=self._diam_etrier_mm,
        )
        if dlg.exec():
            new_data = dlg.get_layer_data()
            old = self._layers[row]
            old.n_bars = new_data.n_bars
            old.diameter_mm = new_data.diameter_mm
            old.layer_type = new_data.layer_type
            old.spacing_from_previous_cm = new_data.spacing_from_previous_cm
            old.auto_first = new_data.auto_first
            old.label = new_data.label
            self._recompute()

    def _on_delete(self):
        row = self._selected_row()
        if row < 0:
            return
        if row == 0 and len(self._layers) > 1:
            self._layers[1].spacing_from_previous_cm = (
                self._layers[1].distance_from_tension_face_cm
            )
            self._layers[1].auto_first = False
        self._layers.pop(row)
        self._recompute()

    def _on_move_up(self):
        row = self._selected_row()
        if row <= 0:
            return
        self._layers[row], self._layers[row - 1] = (
            self._layers[row - 1], self._layers[row]
        )
        # recalc spacings
        if row - 1 == 0:
            self._layers[0].spacing_from_previous_cm = (
                self._layers[0].distance_from_tension_face_cm
            )
        if row < len(self._layers):
            self._layers[row].spacing_from_previous_cm = (
                self._layers[row].distance_from_tension_face_cm
                - self._layers[row - 1].distance_from_tension_face_cm
            )
        self._recompute()
        self._table.selectRow(row - 1)

    def _on_move_down(self):
        row = self._selected_row()
        if row < 0 or row >= len(self._layers) - 1:
            return
        self._layers[row], self._layers[row + 1] = (
            self._layers[row + 1], self._layers[row]
        )
        if row == 0:
            self._layers[0].spacing_from_previous_cm = (
                self._layers[0].distance_from_tension_face_cm
            )
        if row + 1 < len(self._layers):
            self._layers[row + 1].spacing_from_previous_cm = (
                self._layers[row + 1].distance_from_tension_face_cm
                - self._layers[row].distance_from_tension_face_cm
            )
        self._recompute()
        self._table.selectRow(row + 1)

    def _selected_row(self) -> int:
        sel = self._table.selectedItems()
        return sel[0].row() if sel else -1

    # ── Recalcul et rafraîchissement ─────────────────────────────────
    def _recompute(self):
        recompute_layer_levels(
            self._layers, self._c_nom_mm, self._diam_etrier_mm,
        )
        self._refresh_table()
        self.layers_changed.emit()

    def _refresh_table(self):
        p = ThemeManager.get().p
        self._table.setRowCount(len(self._layers))

        total_area_cm2 = 0.0
        sum_ai_di = 0.0
        sum_ai = 0.0

        validation = validate_layer_spacing(
            self._layers, self._h_mm, self._d_mm,
        )
        # Build per-layer status map
        status_map: dict[int, str] = {}
        for msg in validation.messages:
            for layer in self._layers:
                if f"lit {layer.id}" in msg["message"].lower():
                    if layer.id not in status_map or msg["type"] == "erreur":
                        status_map[layer.id] = msg["type"]

        for row_idx, layer in enumerate(self._layers):
            y_mm = layer.distance_from_tension_face_cm * 10.0
            d_i_mm = self._h_mm - y_mm
            d_i_cm = d_i_mm / 10.0

            total_area_cm2 += layer.area_cm2
            if layer.layer_type != TypeLit.COMPRIME:
                sum_ai_di += layer.area_mm2 * d_i_mm
                sum_ai += layer.area_mm2

            dist_label = f"{layer.spacing_from_previous_cm:.1f}"
            if row_idx == 0:
                dist_label += " *"

            items = [
                f"Lit {layer.id}",
                str(layer.n_bars),
                f"HA{layer.diameter_mm:.0f}",
                f"{layer.unit_area_cm2:.2f}",
                f"{layer.area_cm2:.2f}",
                layer.layer_type.value.capitalize(),
                dist_label,
                f"{layer.distance_from_tension_face_cm:.1f}",
                f"{d_i_cm:.1f}",
            ]

            # Statut
            st = status_map.get(layer.id, "ok")
            st_text = "✓" if st == "ok" else ("⚠" if st == "avertissement" else "✗")
            items.append(st_text)

            for col, txt in enumerate(items):
                it = QTableWidgetItem(txt)
                it.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                if col == 0:
                    f = it.font()
                    f.setBold(True)
                    it.setFont(f)
                    it.setForeground(QColor(p.ac))
                if col == len(items) - 1:
                    if st == "erreur":
                        it.setForeground(QColor(p.err))
                    elif st == "avertissement":
                        it.setForeground(QColor(p.warn))
                    else:
                        it.setForeground(QColor(p.ok))
                self._table.setItem(row_idx, col, it)

        d_reel = sum_ai_di / sum_ai if sum_ai > 0 else 0.0
        self._lbl_total.setText(f"Total : {total_area_cm2:.2f} cm²")
        self._lbl_d_reel.setText(f"d réel : {d_reel / 10:.2f} cm  ({d_reel:.1f} mm)")

        if validation.valid:
            self._lbl_validation.setText("✓ Disposition valide")
            self._lbl_validation.setStyleSheet(
                f"color:{p.ok}; font-weight:600; font-size:12px; background:transparent;"
            )
        else:
            errs = [m["message"] for m in validation.messages if m["type"] == "erreur"]
            self._lbl_validation.setText(f"✗ {errs[0]}" if errs else "✗ Erreur")
            self._lbl_validation.setStyleSheet(
                f"color:{p.err}; font-weight:600; font-size:12px; background:transparent;"
            )

    # ── API publique ─────────────────────────────────────────────────
    def get_layers(self) -> list[ReinforcementLayer]:
        """Retourne la liste des ReinforcementLayer."""
        return list(self._layers)

    def get_lits(self) -> list[dict]:
        """API de compatibilité — retourne [{diam_mm, nb, ...}, …]."""
        result = []
        for layer in self._layers:
            if layer.n_bars > 0:
                result.append({
                    "diam_idx": (AVAILABLE_DIAMETERS_MM.index(layer.diameter_mm)
                                 if layer.diameter_mm in AVAILABLE_DIAMETERS_MM else 5),
                    "diam_mm": layer.diameter_mm,
                    "nb": layer.n_bars,
                    "type": layer.layer_type.value,
                    "spacing_cm": layer.spacing_from_previous_cm,
                    "distance_cm": layer.distance_from_tension_face_cm,
                    "auto_first": layer.auto_first,
                    "label": layer.label,
                })
        return result

    def set_lits(self, lits: list[dict]):
        """Charge depuis [{diam_mm, nb, spacing_cm?, distance_cm?, ...}]."""
        self._layers.clear()
        for i, lit in enumerate(lits):
            layer = ReinforcementLayer(
                id=i + 1,
                n_bars=lit.get("nb", 0),
                diameter_mm=float(lit.get("diam_mm", 16)),
                layer_type=TypeLit(lit.get("type", "tendu")),
                spacing_from_previous_cm=lit.get(
                    "spacing_cm",
                    lit.get("espacement_precedent_cm", 5.0),
                ),
                auto_first=lit.get("auto_first", False),
                label=lit.get("label", ""),
            )
            self._layers.append(layer)
        self._recompute()

    def set_from_catalogue(self, diam: int, nb: int):
        """Appelé quand l'utilisateur clique sur le catalogue."""
        layer = ReinforcementLayer(
            n_bars=nb,
            diameter_mm=float(diam),
            spacing_from_previous_cm=(
                compute_auto_first_distance_cm(
                    self._c_nom_mm, self._diam_etrier_mm, diam,
                ) if not self._layers else 5.0
            ),
            auto_first=(not self._layers),
        )
        self._layers.append(layer)
        self._recompute()

    def clear(self):
        """Vide tous les lits."""
        self._layers.clear()
        self._recompute()
