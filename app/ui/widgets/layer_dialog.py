"""Boîte de dialogue pour ajouter / modifier un lit d'armatures."""
from __future__ import annotations

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLabel,
    QComboBox, QSpinBox, QDoubleSpinBox, QCheckBox,
    QPushButton, QLineEdit, QDialogButtonBox, QFrame,
)
from PySide6.QtCore import Qt

from app.constants import AVAILABLE_DIAMETERS_MM
from app.core.reinforcement_layers import (
    ReinforcementLayer, TypeLit, compute_auto_first_distance_cm,
)


class LayerDialog(QDialog):
    """Dialogue d'ajout / modification d'un lit d'armatures.

    Parameters
    ----------
    parent : QWidget
    is_first : bool
        True si c'est le premier lit (label adapté).
    edit_data : ReinforcementLayer | None
        Si fourni, pré-remplit le formulaire (mode édition).
    c_nom_mm, diam_etrier_mm : float
        Pour le calcul auto du premier lit.
    """

    def __init__(
        self,
        parent=None,
        *,
        is_first: bool = True,
        edit_data: ReinforcementLayer | None = None,
        c_nom_mm: float = 30.0,
        diam_etrier_mm: float = 8.0,
    ):
        super().__init__(parent)
        self._is_first = is_first
        self._c_nom_mm = c_nom_mm
        self._diam_etrier_mm = diam_etrier_mm

        self.setWindowTitle("Modifier le lit" if edit_data else "Ajouter un lit")
        self.setMinimumWidth(420)
        self._build_ui()
        if edit_data:
            self._load(edit_data)
        else:
            self._on_auto_toggled()

    # ── Construction ─────────────────────────────────────────────────
    def _build_ui(self):
        lay = QVBoxLayout(self)
        lay.setSpacing(12)

        form = QFormLayout()
        form.setSpacing(8)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        # Nom / label
        self.txt_label = QLineEdit()
        self.txt_label.setPlaceholderText("ex : Lit principal")
        form.addRow("Nom du lit :", self.txt_label)

        # Type
        self.cmb_type = QComboBox()
        self.cmb_type.addItems(["Tendu", "Comprimé", "Montage"])
        form.addRow("Type :", self.cmb_type)

        # Nombre de barres
        self.spn_nb = QSpinBox()
        self.spn_nb.setRange(1, 20)
        self.spn_nb.setValue(5)
        self.spn_nb.valueChanged.connect(self._update_section)
        form.addRow("Nombre de barres :", self.spn_nb)

        # Diamètre
        self.cmb_diam = QComboBox()
        for d in AVAILABLE_DIAMETERS_MM:
            self.cmb_diam.addItem(f"HA{d}", d)
        self.cmb_diam.setCurrentIndex(7)  # HA25
        self.cmb_diam.currentIndexChanged.connect(self._update_section)
        self.cmb_diam.currentIndexChanged.connect(self._on_auto_toggled)
        form.addRow("Diamètre :", self.cmb_diam)

        # Section affichée
        self.lbl_section = QLabel("—")
        self.lbl_section.setStyleSheet("font-weight:600;")
        form.addRow("Section du lit :", self.lbl_section)

        # ── Séparateur ──
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        form.addRow(sep)

        # Distance
        if self._is_first:
            dist_label = "Distance à la fibre tendue :"
        else:
            dist_label = "Distance au lit précédent :"

        # Auto checkbox (first lit only)
        self.chk_auto = QCheckBox("Calcul automatique (enrobage + étrier + Ø/2)")
        self.chk_auto.setVisible(self._is_first)
        self.chk_auto.toggled.connect(self._on_auto_toggled)
        form.addRow("", self.chk_auto)

        self.spn_distance = QDoubleSpinBox()
        self.spn_distance.setRange(0.1, 200.0)
        self.spn_distance.setDecimals(1)
        self.spn_distance.setSuffix(" cm")
        self.spn_distance.setValue(5.0)
        form.addRow(dist_label, self.spn_distance)

        lay.addLayout(form)

        # Boutons
        btns = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        lay.addWidget(btns)

        self._update_section()

    # ── Mise à jour section ──
    def _update_section(self):
        import math
        d = self.cmb_diam.currentData()
        n = self.spn_nb.value()
        if d and n:
            s_mm2 = n * math.pi * d ** 2 / 4.0
            self.lbl_section.setText(f"{s_mm2 / 100:.2f} cm²  ({s_mm2:.0f} mm²)")

    def _on_auto_toggled(self):
        if self.chk_auto.isChecked():
            d = self.cmb_diam.currentData() or 25
            auto_val = compute_auto_first_distance_cm(
                self._c_nom_mm, self._diam_etrier_mm, d,
            )
            self.spn_distance.setValue(round(auto_val, 1))
            self.spn_distance.setEnabled(False)
        else:
            self.spn_distance.setEnabled(True)

    # ── Chargement (édition) ──
    def _load(self, layer: ReinforcementLayer):
        self.txt_label.setText(layer.label)
        type_map = {TypeLit.TENDU: 0, TypeLit.COMPRIME: 1, TypeLit.MONTAGE: 2}
        self.cmb_type.setCurrentIndex(type_map.get(layer.layer_type, 0))
        self.spn_nb.setValue(layer.n_bars)
        # Find diam index
        for i in range(self.cmb_diam.count()):
            if self.cmb_diam.itemData(i) == layer.diameter_mm:
                self.cmb_diam.setCurrentIndex(i)
                break
        self.spn_distance.setValue(layer.spacing_from_previous_cm)
        self.chk_auto.setChecked(layer.auto_first)

    # ── Résultat ──
    def get_layer_data(self) -> ReinforcementLayer:
        """Retourne un ReinforcementLayer avec les valeurs saisies."""
        type_map = {0: TypeLit.TENDU, 1: TypeLit.COMPRIME, 2: TypeLit.MONTAGE}
        return ReinforcementLayer(
            n_bars=self.spn_nb.value(),
            diameter_mm=self.cmb_diam.currentData(),
            layer_type=type_map.get(self.cmb_type.currentIndex(), TypeLit.TENDU),
            spacing_from_previous_cm=self.spn_distance.value(),
            auto_first=self.chk_auto.isChecked() and self._is_first,
            label=self.txt_label.text().strip(),
        )
