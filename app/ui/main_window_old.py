"""Fenêtre principale de l'application FlexiBeam."""
from __future__ import annotations

import os
import sys
import traceback
from pathlib import Path
from typing import Optional

from PySide6.QtWidgets import (
    QMainWindow, QTabWidget, QWidget, QVBoxLayout, QHBoxLayout,
    QGroupBox, QLabel, QLineEdit, QComboBox, QPushButton,
    QFormLayout, QTextBrowser, QTableWidget, QTableWidgetItem,
    QSpinBox, QDoubleSpinBox, QCheckBox, QScrollArea,
    QFileDialog, QMessageBox, QStatusBar, QSplitter,
    QHeaderView, QGridLayout, QSizePolicy,
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QFont, QColor, QIcon

from app.config import APP_NAME, APP_VERSION
from app.constants import (
    AVAILABLE_DIAMETERS_MM, STEEL_TABLE_CM2, CLASSES_EXPOSITION,
)
from app.models.section_models import DonneesGeometrie, TypeSection
from app.models.material_models import (
    DonneesBeton, DonneesAcier, DonneesMateriaux,
    ClasseDuctilite, DiagrammeAcier,
)
from app.models.load_models import DonneesSollicitations
from app.models.reinforcement_models import (
    LitArmature, DonneesFerraillage, DonneesEnvironnement,
)
from app.models.result_models import ResultatsComplets
from app.core.units import (
    cm_to_mm, mm_to_cm, MNm_to_Nmm, Nmm_to_MNm, Nmm_to_kNm,
    mm2_to_cm2, m_to_mm, mm_to_m, kNm_to_Nmm,
)
from app.core.examples import (
    exemple_rectangulaire, exemple_section_T,
    exemple_aciers_comprimes, exemple_figure,
)
from app.core.section_decision import DecisionSection
from app.services.calculation_service import calcul_complet
from app.services.suggestion_service import proposer_solutions
from app.services.persistence_service import sauvegarder_projet, charger_projet
from app.services.report_service import generer_rapport
from app.ui.styles import (
    STYLESHEET, badge_ok, badge_ko, badge_attention, carte_html,
    COULEUR_PRIMAIRE, COULEUR_SUCCES, COULEUR_ERREUR, COULEUR_AVERTISSEMENT,
)


class FenetrePrincipale(QMainWindow):
    """Fenêtre principale de l'application FlexiBeam."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{APP_NAME} v{APP_VERSION}")
        self.setMinimumSize(1200, 800)
        self.resize(1400, 900)

        self.resultats: Optional[ResultatsComplets] = None
        self._lits_widgets: list[dict] = []

        self._creer_interface()
        self.statusBar().showMessage("Prêt. Chargez un exemple ou saisissez vos données.")

    # ──────────────────────────────────────────────
    # Création de l'interface
    # ──────────────────────────────────────────────
    def _creer_interface(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout_principal = QVBoxLayout(central)
        layout_principal.setContentsMargins(8, 8, 8, 8)

        # Barre de boutons supérieure
        barre_boutons = QHBoxLayout()
        btn_exemple_rect = QPushButton("📋 Exemple Rectangulaire")
        btn_exemple_rect.clicked.connect(lambda: self._charger_exemple("rect"))
        btn_exemple_T = QPushButton("📋 Exemple Section T")
        btn_exemple_T.clicked.connect(lambda: self._charger_exemple("T"))
        btn_exemple_comp = QPushButton("📋 Exemple Aciers Comprimés")
        btn_exemple_comp.clicked.connect(lambda: self._charger_exemple("comp"))
        btn_exemple_fig = QPushButton("📋 Exemple de la figure")
        btn_exemple_fig.clicked.connect(lambda: self._charger_exemple("figure"))
        btn_reinit = QPushButton("🔄 Réinitialiser")
        btn_reinit.setProperty("class", "secondary")
        btn_reinit.clicked.connect(self._reinitialiser)
        btn_ouvrir = QPushButton("📂 Ouvrir JSON")
        btn_ouvrir.clicked.connect(self._ouvrir_fichier)
        btn_sauver = QPushButton("💾 Sauvegarder JSON")
        btn_sauver.clicked.connect(self._sauvegarder_fichier)

        for btn in [btn_exemple_rect, btn_exemple_T, btn_exemple_comp,
                     btn_exemple_fig, btn_reinit, btn_ouvrir, btn_sauver]:
            barre_boutons.addWidget(btn)
        barre_boutons.addStretch()
        layout_principal.addLayout(barre_boutons)

        # Onglets principaux
        self.onglets = QTabWidget()
        self.onglets.setDocumentMode(True)
        layout_principal.addWidget(self.onglets)

        # Créer les onglets
        self._creer_onglet_donnees()
        self._creer_onglet_elu()
        self._creer_onglet_ferraillage()
        self._creer_onglet_fissuration()
        self._creer_onglet_vue2d()
        self._creer_onglet_vue3d()
        self._creer_onglet_rapport()

    # ──────────────────────────────────────────────
    # ONGLET 1 : DONNÉES
    # ──────────────────────────────────────────────
    def _creer_onglet_donnees(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        widget = QWidget()
        layout = QHBoxLayout(widget)

        # Colonne gauche : géométrie + sollicitations
        col_gauche = QVBoxLayout()

        # Géométrie — unités en cm
        grp_geo = QGroupBox("Géométrie de la section")
        form_geo = QFormLayout(grp_geo)
        form_geo.setSpacing(8)

        self.cmb_type = QComboBox()
        self.cmb_type.addItems(["Rectangulaire", "T", "Auto"])
        form_geo.addRow("Type de section :", self.cmb_type)

        self.txt_bw = QDoubleSpinBox(); self.txt_bw.setRange(0, 999); self.txt_bw.setSuffix(" cm"); self.txt_bw.setDecimals(1)
        form_geo.addRow("bw (largeur âme) :", self.txt_bw)

        self.txt_beff = QDoubleSpinBox(); self.txt_beff.setRange(0, 9999); self.txt_beff.setSuffix(" cm"); self.txt_beff.setDecimals(1)
        form_geo.addRow("beff (largeur table) :", self.txt_beff)

        self.txt_hf = QDoubleSpinBox(); self.txt_hf.setRange(0, 999); self.txt_hf.setSuffix(" cm"); self.txt_hf.setDecimals(1)
        form_geo.addRow("hf (hauteur table) :", self.txt_hf)

        self.txt_h = QDoubleSpinBox(); self.txt_h.setRange(0, 999); self.txt_h.setSuffix(" cm"); self.txt_h.setDecimals(1)
        form_geo.addRow("h (hauteur totale) :", self.txt_h)

        self.txt_d = QDoubleSpinBox(); self.txt_d.setRange(0, 999); self.txt_d.setSuffix(" cm"); self.txt_d.setDecimals(1)
        form_geo.addRow("d (hauteur utile) :", self.txt_d)

        self.chk_d_auto = QCheckBox("d automatique = 0.9·h si non saisi")
        self.chk_d_auto.setChecked(True)
        form_geo.addRow("", self.chk_d_auto)

        self.txt_dprime = QDoubleSpinBox(); self.txt_dprime.setRange(0, 99); self.txt_dprime.setSuffix(" cm"); self.txt_dprime.setDecimals(1)
        self.txt_dprime.setValue(5.0)
        form_geo.addRow("d' (aciers comprimés) :", self.txt_dprime)

        self.txt_cnom = QDoubleSpinBox(); self.txt_cnom.setRange(0, 20); self.txt_cnom.setSuffix(" cm"); self.txt_cnom.setDecimals(1)
        self.txt_cnom.setValue(3.0)
        form_geo.addRow("c_nom (enrobage) :", self.txt_cnom)

        self.txt_diam_etrier = QDoubleSpinBox(); self.txt_diam_etrier.setRange(0, 50); self.txt_diam_etrier.setSuffix(" mm"); self.txt_diam_etrier.setValue(8)
        form_geo.addRow("Ø étrier :", self.txt_diam_etrier)

        self.txt_esp_v = QDoubleSpinBox(); self.txt_esp_v.setRange(0, 20); self.txt_esp_v.setSuffix(" cm"); self.txt_esp_v.setDecimals(1)
        self.txt_esp_v.setValue(2.5)
        form_geo.addRow("Espacement vertical :", self.txt_esp_v)

        self.txt_esp_h = QDoubleSpinBox(); self.txt_esp_h.setRange(0, 20); self.txt_esp_h.setSuffix(" cm"); self.txt_esp_h.setDecimals(1)
        self.txt_esp_h.setValue(2.5)
        form_geo.addRow("Espacement horizontal :", self.txt_esp_h)

        self.txt_dg = QDoubleSpinBox(); self.txt_dg.setRange(0, 100); self.txt_dg.setSuffix(" mm"); self.txt_dg.setValue(20)
        form_geo.addRow("d_g (granulat max) :", self.txt_dg)

        self.spn_max_lits = QSpinBox(); self.spn_max_lits.setRange(1, 10); self.spn_max_lits.setValue(4)
        form_geo.addRow("Nb max lits :", self.spn_max_lits)

        self.txt_longueur_ext = QDoubleSpinBox(); self.txt_longueur_ext.setRange(100, 10000); self.txt_longueur_ext.setSuffix(" mm"); self.txt_longueur_ext.setValue(1000); self.txt_longueur_ext.setDecimals(0)
        form_geo.addRow("Longueur extrusion 3D :", self.txt_longueur_ext)

        col_gauche.addWidget(grp_geo)

        # Sollicitations — Mu,max en MN.m uniquement
        grp_sol = QGroupBox("Sollicitations")
        form_sol = QFormLayout(grp_sol)

        self.txt_mu_max = QDoubleSpinBox()
        self.txt_mu_max.setRange(0, 9999)
        self.txt_mu_max.setSuffix(" MN·m")
        self.txt_mu_max.setDecimals(4)
        form_sol.addRow("Mu,max (moment ultime) :", self.txt_mu_max)

        self.cmb_signe = QComboBox()
        self.cmb_signe.addItems(["Positif", "Négatif"])
        form_sol.addRow("Signe du moment :", self.cmb_signe)

        col_gauche.addWidget(grp_sol)
        col_gauche.addStretch()

        # Colonne droite : matériaux + environnement
        col_droite = QVBoxLayout()

        # Matériaux
        grp_mat = QGroupBox("Matériaux")
        form_mat = QFormLayout(grp_mat)

        self.txt_fck = QDoubleSpinBox(); self.txt_fck.setRange(12, 90); self.txt_fck.setSuffix(" MPa"); self.txt_fck.setValue(25)
        form_mat.addRow("fck :", self.txt_fck)

        self.txt_fyk = QDoubleSpinBox(); self.txt_fyk.setRange(200, 700); self.txt_fyk.setSuffix(" MPa"); self.txt_fyk.setValue(500)
        form_mat.addRow("fyk :", self.txt_fyk)

        self.txt_Es = QDoubleSpinBox(); self.txt_Es.setRange(100000, 250000); self.txt_Es.setSuffix(" MPa"); self.txt_Es.setValue(200000); self.txt_Es.setDecimals(0)
        form_mat.addRow("Es :", self.txt_Es)

        self.txt_alpha_cc = QDoubleSpinBox(); self.txt_alpha_cc.setRange(0.5, 1.5); self.txt_alpha_cc.setValue(1.0); self.txt_alpha_cc.setDecimals(2)
        form_mat.addRow("α_cc :", self.txt_alpha_cc)

        self.txt_gamma_c = QDoubleSpinBox(); self.txt_gamma_c.setRange(1.0, 2.0); self.txt_gamma_c.setValue(1.5); self.txt_gamma_c.setDecimals(2)
        form_mat.addRow("γ_c :", self.txt_gamma_c)

        self.txt_gamma_s = QDoubleSpinBox(); self.txt_gamma_s.setRange(1.0, 2.0); self.txt_gamma_s.setValue(1.15); self.txt_gamma_s.setDecimals(2)
        form_mat.addRow("γ_s :", self.txt_gamma_s)

        self.cmb_ductilite = QComboBox()
        self.cmb_ductilite.addItems(["A", "B", "C"])
        self.cmb_ductilite.setCurrentIndex(1)
        form_mat.addRow("Classe de ductilité :", self.cmb_ductilite)

        self.cmb_diagramme = QComboBox()
        self.cmb_diagramme.addItems(["Palier horizontal", "Palier incliné"])
        form_mat.addRow("Diagramme acier :", self.cmb_diagramme)

        btn_defaut = QPushButton("Paramètres EC2 par défaut")
        btn_defaut.setProperty("class", "secondary")
        btn_defaut.clicked.connect(self._parametres_defaut)
        form_mat.addRow("", btn_defaut)

        col_droite.addWidget(grp_mat)

        # Environnement
        grp_env = QGroupBox("Environnement / ELS")
        form_env = QFormLayout(grp_env)

        self.cmb_exposition = QComboBox()
        self.cmb_exposition.addItems(CLASSES_EXPOSITION)
        form_env.addRow("Classe d'exposition :", self.cmb_exposition)

        self.chk_fissuration = QCheckBox("Maîtrise de la fissuration")
        self.chk_fissuration.setChecked(True)
        form_env.addRow("", self.chk_fissuration)

        self.txt_wmax = QDoubleSpinBox(); self.txt_wmax.setRange(0, 1); self.txt_wmax.setDecimals(2); self.txt_wmax.setSuffix(" mm")
        self.txt_wmax.setSpecialValueText("Auto")
        form_env.addRow("w_max imposé :", self.txt_wmax)

        self.chk_calc_direct = QCheckBox("Calcul direct de fissuration")
        form_env.addRow("", self.chk_calc_direct)

        col_droite.addWidget(grp_env)

        # Bouton calculer
        grp_actions = QGroupBox("Actions")
        layout_actions = QVBoxLayout(grp_actions)

        btn_calculer = QPushButton("⚡ CALCULER")
        btn_calculer.setStyleSheet(
            f"background-color: {COULEUR_SUCCES}; font-size: 16px; "
            "padding: 12px; font-weight: bold;"
        )
        btn_calculer.clicked.connect(self._lancer_calcul)
        layout_actions.addWidget(btn_calculer)

        btn_proposer = QPushButton("💡 Proposer un ferraillage")
        btn_proposer.clicked.connect(self._proposer_ferraillage)
        layout_actions.addWidget(btn_proposer)

        col_droite.addWidget(grp_actions)
        col_droite.addStretch()

        layout.addLayout(col_gauche, 1)
        layout.addLayout(col_droite, 1)

        scroll.setWidget(widget)
        self.onglets.addTab(scroll, "1. Données")

    # ──────────────────────────────────────────────
    # ONGLET 2 : CALCUL ELU
    # ──────────────────────────────────────────────
    def _creer_onglet_elu(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        widget = QWidget()
        layout = QVBoxLayout(widget)

        self.txt_resultats_elu = QTextBrowser()
        self.txt_resultats_elu.setOpenExternalLinks(False)
        self.txt_resultats_elu.setMinimumHeight(500)
        layout.addWidget(self.txt_resultats_elu)

        scroll.setWidget(widget)
        self.onglets.addTab(scroll, "2. Calcul ELU")

    # ──────────────────────────────────────────────
    # ONGLET 3 : VÉRIFICATION DU FERRAILLAGE
    # ──────────────────────────────────────────────
    def _creer_onglet_ferraillage(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Zone de saisie des lits
        grp_saisie = QGroupBox("Ferraillage proposé – Lits d'armatures")
        layout_saisie = QVBoxLayout(grp_saisie)

        self.layout_lits = QVBoxLayout()
        layout_saisie.addLayout(self.layout_lits)

        btn_layout = QHBoxLayout()
        btn_ajouter_lit = QPushButton("➕ Ajouter un lit")
        btn_ajouter_lit.clicked.connect(self._ajouter_lit)
        btn_layout.addWidget(btn_ajouter_lit)

        btn_supprimer_lit = QPushButton("➖ Supprimer le dernier lit")
        btn_supprimer_lit.setProperty("class", "danger")
        btn_supprimer_lit.clicked.connect(self._supprimer_lit)
        btn_layout.addWidget(btn_supprimer_lit)

        btn_monter = QPushButton("🔼 Monter")
        btn_monter.clicked.connect(self._monter_lit)
        btn_layout.addWidget(btn_monter)

        btn_descendre = QPushButton("🔽 Descendre")
        btn_descendre.clicked.connect(self._descendre_lit)
        btn_layout.addWidget(btn_descendre)

        btn_verifier = QPushButton("✓ Vérifier le ferraillage")
        btn_verifier.setStyleSheet(f"background-color: {COULEUR_SUCCES}; font-weight:bold;")
        btn_verifier.clicked.connect(self._verifier_ferraillage_ui)
        btn_layout.addWidget(btn_verifier)

        btn_layout.addStretch()
        layout_saisie.addLayout(btn_layout)

        layout.addWidget(grp_saisie)

        # Catalogue des armatures
        grp_catalogue = QGroupBox("Catalogue des armatures (cm²)")
        layout_cat = QVBoxLayout(grp_catalogue)
        self.table_catalogue = QTableWidget()
        self._remplir_catalogue()
        self.table_catalogue.cellClicked.connect(self._clic_catalogue)
        layout_cat.addWidget(self.table_catalogue)
        layout.addWidget(grp_catalogue)

        # Résultats
        self.txt_resultats_ferraillage = QTextBrowser()
        self.txt_resultats_ferraillage.setMinimumHeight(300)
        layout.addWidget(self.txt_resultats_ferraillage)

        # Propositions
        grp_propositions = QGroupBox("Solutions proposées")
        layout_prop = QVBoxLayout(grp_propositions)
        self.txt_propositions = QTextBrowser()
        self.txt_propositions.setMinimumHeight(200)
        layout_prop.addWidget(self.txt_propositions)

        btn_comparer = QPushButton("📊 Comparer plusieurs solutions")
        btn_comparer.clicked.connect(self._proposer_ferraillage)
        layout_prop.addWidget(btn_comparer)

        layout.addWidget(grp_propositions)
        layout.addStretch()

        scroll.setWidget(widget)
        self.onglets.addTab(scroll, "3. Vérification ferraillage")

        # Ajouter un premier lit par défaut
        self._ajouter_lit()

    # ──────────────────────────────────────────────
    # ONGLET 4 : FISSURATION / ELS
    # ──────────────────────────────────────────────
    def _creer_onglet_fissuration(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        widget = QWidget()
        layout = QVBoxLayout(widget)

        self.txt_resultats_fissuration = QTextBrowser()
        self.txt_resultats_fissuration.setMinimumHeight(500)
        layout.addWidget(self.txt_resultats_fissuration)

        scroll.setWidget(widget)
        self.onglets.addTab(scroll, "4. Fissuration / ELS")

    # ──────────────────────────────────────────────
    # ONGLET 5 : VUE 2D
    # ──────────────────────────────────────────────
    def _creer_onglet_vue2d(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)

        btn_layout = QHBoxLayout()
        btn_generer_2d = QPushButton("🖼 Générer la vue 2D")
        btn_generer_2d.clicked.connect(self._generer_vue_2d)
        btn_layout.addWidget(btn_generer_2d)

        btn_export_2d = QPushButton("💾 Exporter PNG")
        btn_export_2d.clicked.connect(self._exporter_vue_2d)
        btn_layout.addWidget(btn_export_2d)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
        from matplotlib.figure import Figure
        self.figure_2d = Figure(figsize=(10, 8), dpi=100)
        self.canvas_2d = FigureCanvasQTAgg(self.figure_2d)
        layout.addWidget(self.canvas_2d)

        self.onglets.addTab(widget, "5. Vue 2D")

    # ──────────────────────────────────────────────
    # ONGLET 6 : VUE 3D
    # ──────────────────────────────────────────────
    def _creer_onglet_vue3d(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)

        btn_layout = QHBoxLayout()
        btn_generer_3d = QPushButton("🧊 Générer la vue 3D")
        btn_generer_3d.clicked.connect(self._generer_vue_3d)
        btn_layout.addWidget(btn_generer_3d)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        self.widget_3d_container = QVBoxLayout()
        layout.addLayout(self.widget_3d_container)

        self.lbl_3d_placeholder = QLabel(
            "Cliquez sur « Générer la vue 3D » après avoir lancé un calcul."
        )
        self.lbl_3d_placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_3d_placeholder.setStyleSheet("font-size: 14px; color: #757575; padding: 40px;")
        self.widget_3d_container.addWidget(self.lbl_3d_placeholder)

        self.onglets.addTab(widget, "6. Vue 3D")

    # ──────────────────────────────────────────────
    # ONGLET 7 : RAPPORT
    # ──────────────────────────────────────────────
    def _creer_onglet_rapport(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)

        btn_rapport = QPushButton("📄 Générer le rapport PDF")
        btn_rapport.setStyleSheet(
            f"background-color: {COULEUR_PRIMAIRE}; font-size: 16px; "
            "padding: 12px; font-weight: bold;"
        )
        btn_rapport.clicked.connect(self._generer_rapport)
        layout.addWidget(btn_rapport)

        self.txt_rapport_apercu = QTextBrowser()
        self.txt_rapport_apercu.setMinimumHeight(500)
        layout.addWidget(self.txt_rapport_apercu)

        self.onglets.addTab(widget, "7. Rapport")

    # ──────────────────────────────────────────────
    # Lecture des données depuis l'interface
    # (UI en cm → modèle en mm)
    # ──────────────────────────────────────────────
    def _lire_geometrie(self) -> DonneesGeometrie:
        type_map = {"Rectangulaire": TypeSection.RECTANGULAIRE, "T": TypeSection.T, "Auto": TypeSection.AUTO}
        return DonneesGeometrie(
            type_section=type_map[self.cmb_type.currentText()],
            b_eff=cm_to_mm(self.txt_beff.value()),
            b_w=cm_to_mm(self.txt_bw.value()),
            h_f=cm_to_mm(self.txt_hf.value()),
            h=cm_to_mm(self.txt_h.value()),
            d=cm_to_mm(self.txt_d.value()),
            d_prime=cm_to_mm(self.txt_dprime.value()),
            c_nom=cm_to_mm(self.txt_cnom.value()),
            diam_etrier=self.txt_diam_etrier.value(),
            espacement_vertical=cm_to_mm(self.txt_esp_v.value()),
            espacement_horizontal=cm_to_mm(self.txt_esp_h.value()),
            d_g=self.txt_dg.value(),
            nb_max_lits=self.spn_max_lits.value(),
            longueur_extrusion=self.txt_longueur_ext.value(),
            d_auto=self.chk_d_auto.isChecked(),
        )

    def _lire_materiaux(self) -> DonneesMateriaux:
        duct_map = {"A": ClasseDuctilite.A, "B": ClasseDuctilite.B, "C": ClasseDuctilite.C}
        diag_map = {"Palier horizontal": DiagrammeAcier.PALIER_HORIZONTAL, "Palier incliné": DiagrammeAcier.PALIER_INCLINE}
        return DonneesMateriaux(
            beton=DonneesBeton(
                fck=self.txt_fck.value(),
                alpha_cc=self.txt_alpha_cc.value(),
                gamma_c=self.txt_gamma_c.value(),
            ),
            acier=DonneesAcier(
                fyk=self.txt_fyk.value(),
                Es=self.txt_Es.value(),
                gamma_s=self.txt_gamma_s.value(),
                classe_ductilite=duct_map[self.cmb_ductilite.currentText()],
                diagramme=diag_map[self.cmb_diagramme.currentText()],
            ),
        )

    def _lire_sollicitations(self) -> DonneesSollicitations:
        return DonneesSollicitations(
            M_Ed=MNm_to_Nmm(self.txt_mu_max.value()),
            M_ser=0.0,
            moment_positif=(self.cmb_signe.currentText() == "Positif"),
        )

    def _lire_ferraillage(self) -> DonneesFerraillage:
        lits: list[LitArmature] = []
        for i, w in enumerate(self._lits_widgets):
            diam = AVAILABLE_DIAMETERS_MM[w["cmb_diam"].currentIndex()]
            nb = w["spn_nb"].value()
            if nb > 0:
                lits.append(LitArmature(numero=i+1, nombre_barres=nb, diametre_mm=float(diam)))
        return DonneesFerraillage(lits_tendus=lits)

    def _lire_environnement(self) -> DonneesEnvironnement:
        wmax_val = self.txt_wmax.value()
        return DonneesEnvironnement(
            classe_exposition=self.cmb_exposition.currentText(),
            maitrise_fissuration=self.chk_fissuration.isChecked(),
            wmax_impose=wmax_val if wmax_val > 0 else None,
            calcul_direct_fissuration=self.chk_calc_direct.isChecked(),
        )

    # ──────────────────────────────────────────────
    # Écriture des données dans l'interface
    # (modèle en mm → UI en cm)
    # ──────────────────────────────────────────────
    def _ecrire_geometrie(self, geo: DonneesGeometrie):
        type_map = {TypeSection.RECTANGULAIRE: 0, TypeSection.T: 1, TypeSection.AUTO: 2}
        self.cmb_type.setCurrentIndex(type_map.get(geo.type_section, 0))
        self.txt_bw.setValue(mm_to_cm(geo.b_w))
        self.txt_beff.setValue(mm_to_cm(geo.b_eff))
        self.txt_hf.setValue(mm_to_cm(geo.h_f))
        self.txt_h.setValue(mm_to_cm(geo.h))
        self.txt_d.setValue(mm_to_cm(geo.d))
        self.txt_dprime.setValue(mm_to_cm(geo.d_prime))
        self.txt_cnom.setValue(mm_to_cm(geo.c_nom))
        self.txt_diam_etrier.setValue(geo.diam_etrier)
        self.txt_esp_v.setValue(mm_to_cm(geo.espacement_vertical))
        self.txt_esp_h.setValue(mm_to_cm(geo.espacement_horizontal))
        self.txt_dg.setValue(geo.d_g)
        self.spn_max_lits.setValue(geo.nb_max_lits)
        self.txt_longueur_ext.setValue(geo.longueur_extrusion)
        self.chk_d_auto.setChecked(geo.d_auto)

    def _ecrire_materiaux(self, mat: DonneesMateriaux):
        self.txt_fck.setValue(mat.beton.fck)
        self.txt_alpha_cc.setValue(mat.beton.alpha_cc)
        self.txt_gamma_c.setValue(mat.beton.gamma_c)
        self.txt_fyk.setValue(mat.acier.fyk)
        self.txt_Es.setValue(mat.acier.Es)
        self.txt_gamma_s.setValue(mat.acier.gamma_s)
        duct_map = {ClasseDuctilite.A: 0, ClasseDuctilite.B: 1, ClasseDuctilite.C: 2}
        self.cmb_ductilite.setCurrentIndex(duct_map.get(mat.acier.classe_ductilite, 1))
        diag_map = {DiagrammeAcier.PALIER_HORIZONTAL: 0, DiagrammeAcier.PALIER_INCLINE: 1}
        self.cmb_diagramme.setCurrentIndex(diag_map.get(mat.acier.diagramme, 0))

    def _ecrire_sollicitations(self, sol: DonneesSollicitations):
        self.txt_mu_max.setValue(Nmm_to_MNm(sol.M_Ed))
        self.cmb_signe.setCurrentIndex(0 if sol.moment_positif else 1)

    def _ecrire_ferraillage(self, fer: DonneesFerraillage):
        while self._lits_widgets:
            self._supprimer_lit()
        for lit in fer.lits_tendus:
            self._ajouter_lit()
            w = self._lits_widgets[-1]
            idx = AVAILABLE_DIAMETERS_MM.index(int(lit.diametre_mm)) if int(lit.diametre_mm) in AVAILABLE_DIAMETERS_MM else 0
            w["cmb_diam"].setCurrentIndex(idx)
            w["spn_nb"].setValue(lit.nombre_barres)
        if not fer.lits_tendus:
            self._ajouter_lit()

    def _ecrire_environnement(self, env: DonneesEnvironnement):
        idx = CLASSES_EXPOSITION.index(env.classe_exposition) if env.classe_exposition in CLASSES_EXPOSITION else 0
        self.cmb_exposition.setCurrentIndex(idx)
        self.chk_fissuration.setChecked(env.maitrise_fissuration)
        self.txt_wmax.setValue(env.wmax_impose if env.wmax_impose is not None else 0)
        self.chk_calc_direct.setChecked(env.calcul_direct_fissuration)

    # ──────────────────────────────────────────────
    # Gestion des lits d'armatures (avec monter/descendre)
    # ──────────────────────────────────────────────
    def _ajouter_lit(self):
        idx = len(self._lits_widgets) + 1
        row_widget = QWidget()
        row_layout = QHBoxLayout(row_widget)
        row_layout.setContentsMargins(0, 2, 0, 2)

        lbl = QLabel(f"Lit {idx} :")
        lbl.setFixedWidth(50)
        row_layout.addWidget(lbl)

        cmb_diam = QComboBox()
        for d in AVAILABLE_DIAMETERS_MM:
            cmb_diam.addItem(f"HA{d}")
        cmb_diam.setCurrentIndex(5)  # HA16 par défaut
        row_layout.addWidget(cmb_diam)

        spn_nb = QSpinBox()
        spn_nb.setRange(0, 20)
        spn_nb.setValue(4)
        spn_nb.setSuffix(" barres")
        row_layout.addWidget(spn_nb)

        lbl_section = QLabel("—")
        lbl_section.setFixedWidth(120)
        row_layout.addWidget(lbl_section)

        def update_section(_, cmb=cmb_diam, spn=spn_nb, lbl=lbl_section):
            d = AVAILABLE_DIAMETERS_MM[cmb.currentIndex()]
            n = spn.value()
            from app.core.steel_catalog import get_total_area_cm2, get_table_area_cm2
            area = get_total_area_cm2(d, n)
            table_area = get_table_area_cm2(d, n)
            txt = f"{area:.2f} cm²"
            if table_area is not None:
                txt += f" (tab: {table_area:.2f})"
            lbl.setText(txt)

        cmb_diam.currentIndexChanged.connect(update_section)
        spn_nb.valueChanged.connect(update_section)
        update_section(None)

        self.layout_lits.addWidget(row_widget)
        self._lits_widgets.append({
            "widget": row_widget,
            "cmb_diam": cmb_diam,
            "spn_nb": spn_nb,
            "lbl_section": lbl_section,
            "lbl": lbl,
        })

    def _supprimer_lit(self):
        if self._lits_widgets:
            w = self._lits_widgets.pop()
            w["widget"].setParent(None)
            w["widget"].deleteLater()

    def _renumeroter_lits(self):
        for i, w in enumerate(self._lits_widgets):
            w["lbl"].setText(f"Lit {i+1} :")

    def _monter_lit(self):
        """Monte le dernier lit d'un cran (échange avec l'avant-dernier)."""
        n = len(self._lits_widgets)
        if n < 2:
            return
        # Échange les données des deux derniers lits
        w_last = self._lits_widgets[-1]
        w_prev = self._lits_widgets[-2]
        # Sauvegarder les valeurs
        d1, n1 = w_prev["cmb_diam"].currentIndex(), w_prev["spn_nb"].value()
        d2, n2 = w_last["cmb_diam"].currentIndex(), w_last["spn_nb"].value()
        # Échanger
        w_prev["cmb_diam"].setCurrentIndex(d2); w_prev["spn_nb"].setValue(n2)
        w_last["cmb_diam"].setCurrentIndex(d1); w_last["spn_nb"].setValue(n1)

    def _descendre_lit(self):
        """Descend le premier lit d'un cran (échange avec le second)."""
        n = len(self._lits_widgets)
        if n < 2:
            return
        w_first = self._lits_widgets[0]
        w_second = self._lits_widgets[1]
        d1, n1 = w_first["cmb_diam"].currentIndex(), w_first["spn_nb"].value()
        d2, n2 = w_second["cmb_diam"].currentIndex(), w_second["spn_nb"].value()
        w_first["cmb_diam"].setCurrentIndex(d2); w_first["spn_nb"].setValue(n2)
        w_second["cmb_diam"].setCurrentIndex(d1); w_second["spn_nb"].setValue(n1)

    # ──────────────────────────────────────────────
    # Catalogue des armatures
    # ──────────────────────────────────────────────
    def _remplir_catalogue(self):
        diams = AVAILABLE_DIAMETERS_MM
        self.table_catalogue.setRowCount(len(diams))
        self.table_catalogue.setColumnCount(11)
        headers = ["Ø (mm)"] + [str(i) for i in range(1, 11)]
        self.table_catalogue.setHorizontalHeaderLabels(headers)
        self.table_catalogue.verticalHeader().setVisible(False)

        for row, d in enumerate(diams):
            item0 = QTableWidgetItem(f"HA{d}")
            item0.setFlags(Qt.ItemFlag.ItemIsEnabled)
            item0.setBackground(QColor(COULEUR_PRIMAIRE))
            item0.setForeground(QColor("white"))
            font = item0.font()
            font.setBold(True)
            item0.setFont(font)
            self.table_catalogue.setItem(row, 0, item0)

            for col in range(1, 11):
                val = STEEL_TABLE_CM2.get(d, {}).get(col, 0)
                item = QTableWidgetItem(f"{val:.2f}")
                item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table_catalogue.setItem(row, col, item)

        self.table_catalogue.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

    def _clic_catalogue(self, row: int, col: int):
        if col == 0:
            return
        diam = AVAILABLE_DIAMETERS_MM[row]
        nb = col
        if self._lits_widgets:
            w = self._lits_widgets[-1]
            if w["spn_nb"].value() == 0:
                idx = AVAILABLE_DIAMETERS_MM.index(diam)
                w["cmb_diam"].setCurrentIndex(idx)
                w["spn_nb"].setValue(nb)
                return
        self._ajouter_lit()
        w = self._lits_widgets[-1]
        idx = AVAILABLE_DIAMETERS_MM.index(diam)
        w["cmb_diam"].setCurrentIndex(idx)
        w["spn_nb"].setValue(nb)

    # ──────────────────────────────────────────────
    # Actions
    # ──────────────────────────────────────────────
    def _lancer_calcul(self):
        try:
            geo = self._lire_geometrie()
            mat = self._lire_materiaux()
            sol = self._lire_sollicitations()
            fer = self._lire_ferraillage()
            env = self._lire_environnement()

            self.resultats = calcul_complet(geo, mat, sol, fer, env)
            self._afficher_resultats_elu()
            self._afficher_resultats_ferraillage()
            self._afficher_resultats_fissuration()
            self._afficher_apercu_rapport()

            self.statusBar().showMessage("Calcul terminé avec succès.")
            self.onglets.setCurrentIndex(1)

        except Exception as e:
            QMessageBox.critical(self, "Erreur de calcul", f"Une erreur est survenue :\n{e}\n\n{traceback.format_exc()}")
            self.statusBar().showMessage("Erreur lors du calcul.")

    def _verifier_ferraillage_ui(self):
        self._lancer_calcul()
        self.onglets.setCurrentIndex(2)

    def _proposer_ferraillage(self):
        try:
            if self.resultats is None or not self.resultats.elu.calcul_valide:
                self._lancer_calcul()
            if self.resultats is None or not self.resultats.elu.calcul_valide:
                return

            geo = self._lire_geometrie()
            solutions = proposer_solutions(self.resultats.elu, geo)
            self.resultats.propositions = solutions
            self._afficher_propositions(solutions)
            self.onglets.setCurrentIndex(2)

        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors de la proposition :\n{e}")

    def _charger_exemple(self, type_exemple: str):
        if type_exemple == "rect":
            ex = exemple_rectangulaire()
        elif type_exemple == "T":
            ex = exemple_section_T()
        elif type_exemple == "figure":
            ex = exemple_figure()
        else:
            ex = exemple_aciers_comprimes()

        self._ecrire_geometrie(ex["geometrie"])
        self._ecrire_materiaux(ex["materiaux"])
        self._ecrire_sollicitations(ex["sollicitations"])
        self._ecrire_ferraillage(ex["ferraillage"])
        self._ecrire_environnement(ex["environnement"])

        self.statusBar().showMessage(f"Exemple chargé : {ex['nom']}")

    def _reinitialiser(self):
        self.txt_bw.setValue(0); self.txt_beff.setValue(0); self.txt_hf.setValue(0)
        self.txt_h.setValue(0); self.txt_d.setValue(0); self.txt_dprime.setValue(5.0)
        self.txt_mu_max.setValue(0)
        self._parametres_defaut()
        while self._lits_widgets:
            self._supprimer_lit()
        self._ajouter_lit()
        self.resultats = None
        self.txt_resultats_elu.clear()
        self.txt_resultats_ferraillage.clear()
        self.txt_resultats_fissuration.clear()
        self.txt_propositions.clear()
        self.txt_rapport_apercu.clear()
        self.figure_2d.clear()
        self.canvas_2d.draw()
        self.statusBar().showMessage("Application réinitialisée.")

    def _parametres_defaut(self):
        self.txt_fck.setValue(25); self.txt_fyk.setValue(500); self.txt_Es.setValue(200000)
        self.txt_alpha_cc.setValue(1.0); self.txt_gamma_c.setValue(1.5)
        self.txt_gamma_s.setValue(1.15)
        self.cmb_ductilite.setCurrentIndex(1)
        self.cmb_diagramme.setCurrentIndex(0)

    def _ouvrir_fichier(self):
        chemin, _ = QFileDialog.getOpenFileName(self, "Ouvrir un projet", "", "Fichiers JSON (*.json)")
        if chemin:
            try:
                data = charger_projet(chemin)
                self._ecrire_geometrie(data["geometrie"])
                self._ecrire_materiaux(data["materiaux"])
                self._ecrire_sollicitations(data["sollicitations"])
                self._ecrire_ferraillage(data["ferraillage"])
                self._ecrire_environnement(data["environnement"])
                self.statusBar().showMessage(f"Projet chargé : {chemin}")
            except Exception as e:
                QMessageBox.critical(self, "Erreur", f"Impossible de charger le fichier :\n{e}")

    def _sauvegarder_fichier(self):
        chemin, _ = QFileDialog.getSaveFileName(self, "Sauvegarder le projet", "projet_flexion.json", "Fichiers JSON (*.json)")
        if chemin:
            try:
                sauvegarder_projet(
                    chemin,
                    self._lire_geometrie(),
                    self._lire_materiaux(),
                    self._lire_sollicitations(),
                    self._lire_ferraillage(),
                    self._lire_environnement(),
                )
                self.statusBar().showMessage(f"Projet sauvegardé : {chemin}")
            except Exception as e:
                QMessageBox.critical(self, "Erreur", f"Impossible de sauvegarder :\n{e}")

    # ──────────────────────────────────────────────
    # Affichage des résultats ELU
    # ──────────────────────────────────────────────
    def _afficher_resultats_elu(self):
        if self.resultats is None:
            return
        elu = self.resultats.elu
        html = "<h2>Résultats du calcul ELU en flexion simple</h2>"

        if elu.erreurs:
            for err in elu.erreurs:
                html += carte_html("❌ Erreur", err, COULEUR_ERREUR)
            self.txt_resultats_elu.setHtml(html)
            return

        # ── Encadré de synthèse de la décision ──
        if elu.decision is not None:
            dec = elu.decision
            Mu_MNm = dec.MEd_max / 1e9
            MTu_MNm = dec.MTu / 1e9

            if dec.decision == DecisionSection.RECTANGULAIRE_BW_NEGATIF:
                decision_label = "RECTANGULAIRE (bw) – Moment négatif"
                decision_couleur = COULEUR_AVERTISSEMENT
                comparaison = "Moment négatif : calcul en section rectangulaire de largeur bw"
            elif dec.decision == DecisionSection.RECTANGULAIRE_EQUIVALENTE_BEFF:
                decision_label = "RECTANGULAIRE ÉQUIVALENTE (beff)"
                decision_couleur = COULEUR_SUCCES
                comparaison = (
                    f"Mu,max = {Mu_MNm:.4f} MN·m ≤ MTu = {MTu_MNm:.4f} MN·m<br>"
                    f"→ La section est traitée comme rectangulaire équivalente de largeur beff"
                )
            else:
                decision_label = "SECTION EN T (décomposition)"
                decision_couleur = COULEUR_PRIMAIRE
                comparaison = (
                    f"Mu,max = {Mu_MNm:.4f} MN·m > MTu = {MTu_MNm:.4f} MN·m<br>"
                    f"→ La section doit être calculée en vraie section en T"
                )

            contenu_decision = (
                f"<table cellpadding='6' style='width:100%; border-collapse:collapse;'>"
                f"<tr><td><b>Mu,max (saisi)</b></td><td><b>{Mu_MNm:.4f} MN·m</b></td></tr>"
                f"<tr><td><b>MTu (calculé)</b></td><td><b>{MTu_MNm:.4f} MN·m</b></td></tr>"
                f"<tr><td><b>Signe du moment</b></td><td>{dec.moment_sign.capitalize()}</td></tr>"
                f"<tr><td><b>Comparaison</b></td><td>{comparaison}</td></tr>"
                f"<tr><td><b>Largeur de calcul</b></td><td>{mm_to_cm(dec.design_width):.1f} cm ({dec.design_width:.0f} mm)</td></tr>"
                f"<tr style='background:{decision_couleur}; color:white;'>"
                f"<td colspan='2' style='text-align:center; font-size:14px;'>"
                f"<b>DÉCISION : {decision_label}</b></td></tr>"
                f"</table>"
            )
            html += carte_html("📐 Décision du type de section", contenu_decision, decision_couleur)

        # Type de section
        html += carte_html("Type de section retenu", elu.commentaire_section)

        # Paramètres matériaux
        contenu_mat = (
            f"f<sub>cd</sub> = {elu.fcd:.2f} MPa<br>"
            f"f<sub>cu</sub> = {elu.fcu:.2f} MPa<br>"
            f"b = {mm_to_cm(elu.b_calcul):.1f} cm ({elu.b_calcul:.0f} mm)<br>"
            f"d = {mm_to_cm(elu.d_calcul):.1f} cm ({elu.d_calcul:.0f} mm)"
        )
        html += carte_html("Paramètres", contenu_mat)

        # Moment réduit
        couleur_mu = COULEUR_SUCCES if elu.mu_cu <= elu.mu_ulim else COULEUR_AVERTISSEMENT
        contenu_mu = (
            f"μ<sub>cu</sub> = {elu.mu_cu:.4f}<br>"
            f"μ<sub>ulim</sub> = {elu.mu_ulim:.4f}<br>"
            f"{'μcu ≤ μulim → Pas d\'aciers comprimés' if not elu.necessite_aciers_comprimes else 'μcu > μulim → Aciers comprimés nécessaires'}"
        )
        html += carte_html("Moment réduit", contenu_mu, couleur_mu)

        # Axe neutre et bras de levier
        contenu_axe = (
            f"α<sub>u</sub> = {elu.alpha_u:.4f}<br>"
            f"x<sub>u</sub> = {elu.x_u:.1f} mm ({mm_to_cm(elu.x_u):.2f} cm)<br>"
            f"Z<sub>c</sub> = {elu.Zc:.1f} mm ({mm_to_cm(elu.Zc):.2f} cm)"
        )
        html += carte_html("Position de l'axe neutre", contenu_axe)

        # Pivot
        contenu_pivot = (
            f"Pivot : <b>{elu.pivot.pivot}</b><br>"
            f"ε<sub>s1</sub> = {elu.pivot.epsilon_s1*1000:.2f} ‰<br>"
            f"σ<sub>s1</sub> = {elu.pivot.sigma_s1:.1f} MPa<br>"
            f"{elu.pivot.commentaire}"
        )
        html += carte_html("Détermination du pivot", contenu_pivot)

        # Section T spécifique
        if elu.MTu > 0:
            contenu_T = f"M<sub>Tu</sub> = {Nmm_to_MNm(elu.MTu):.4f} MN·m<br>"
            if elu.MEd1 > 0:
                contenu_T += (
                    f"M<sub>Ed1</sub> (âme) = {Nmm_to_MNm(elu.MEd1):.4f} MN·m<br>"
                    f"M<sub>Ed2</sub> (table) = {Nmm_to_MNm(elu.MEd2):.4f} MN·m<br>"
                    f"A<sub>s1</sub> = {elu.As1/100:.2f} cm²<br>"
                    f"A<sub>s2</sub> = {elu.As2/100:.2f} cm²"
                )
            html += carte_html("Section en T – Décomposition", contenu_T)

        # Aciers comprimés
        if elu.necessite_aciers_comprimes:
            html += carte_html("⚠ Aciers comprimés", elu.commentaire_compression, COULEUR_AVERTISSEMENT)

        # Section requise
        contenu_as = (
            f"<b>A<sub>s,requise</sub> = {elu.As_requise/100:.2f} cm² "
            f"({elu.As_requise:.0f} mm²)</b><br>"
            f"A<sub>s,min</sub> = {elu.As_min/100:.2f} cm²"
        )
        html += carte_html("Section d'acier requise", contenu_as, COULEUR_SUCCES)

        # Avertissements
        for av in elu.avertissements:
            html += carte_html("⚠ Avertissement", av, COULEUR_AVERTISSEMENT)

        self.txt_resultats_elu.setHtml(html)

    def _afficher_resultats_ferraillage(self):
        if self.resultats is None or self.resultats.verification is None:
            return
        verif = self.resultats.verification
        html = "<h2>Vérification du ferraillage proposé</h2>"

        # Détails par lit
        if verif.details_lits:
            tableau = "<table border='1' cellpadding='6' cellspacing='0' style='border-collapse:collapse; width:100%;'>"
            tableau += (
                "<tr style='background:#1565C0; color:white;'>"
                "<th>Lit</th><th>Nb barres</th><th>Ø (mm)</th>"
                "<th>As unit. (mm²)</th><th>As tot. (mm²)</th><th>As tot. (cm²)</th>"
                "<th>Dist. bord (mm)</th><th>d_i (mm)</th></tr>"
            )
            for det in verif.details_lits:
                tableau += (
                    f"<tr><td>{det['lit_numero']}</td>"
                    f"<td>{det['nombre_barres']}</td>"
                    f"<td>HA{det['diametre_mm']:.0f}</td>"
                    f"<td>{det['section_unitaire_mm2']:.1f}</td>"
                    f"<td>{det['section_totale_mm2']:.1f}</td>"
                    f"<td>{det['section_totale_cm2']:.2f}</td>"
                    f"<td>{det['distance_bord_tendu_mm']:.1f}</td>"
                    f"<td>{det['d_i_mm']:.1f}</td></tr>"
                )
            tableau += "</table>"
            html += carte_html("Détail des lits", tableau)

        # Synthèse
        contenu_synth = (
            f"A<sub>s,requise</sub> = {verif.As_requise_mm2/100:.2f} cm²<br>"
            f"A<sub>s,réelle</sub> = {verif.As_reelle_mm2/100:.2f} cm²<br>"
            f"Écart = {verif.ecart_absolu_mm2/100:.2f} cm² ({verif.taux_pourcentage:+.1f}%)<br>"
            f"d<sub>calcul</sub> = {verif.d_calcul:.1f} mm ({mm_to_cm(verif.d_calcul):.2f} cm)<br>"
            f"d<sub>réel</sub> = {verif.d_reel:.1f} mm ({mm_to_cm(verif.d_reel):.2f} cm)"
        )
        html += carte_html("Synthèse", contenu_synth)

        # Contrôles
        badge_s = badge_ok() if verif.controle_section else badge_ko()
        html += carte_html(f"Contrôle de section {badge_s}", verif.message_section,
                           COULEUR_SUCCES if verif.controle_section else COULEUR_ERREUR)

        badge_b = badge_ok() if verif.controle_bras_levier else badge_ko()
        html += carte_html(f"Contrôle du bras de levier {badge_b}", verif.message_bras_levier,
                           COULEUR_SUCCES if verif.controle_bras_levier else COULEUR_ERREUR)

        # Verdict
        if verif.verdict_global:
            html += carte_html(f"Verdict {badge_ok()}", verif.message_verdict, COULEUR_SUCCES)
        else:
            html += carte_html(f"Verdict {badge_ko()}", verif.message_verdict, COULEUR_ERREUR)

        # Constructif
        if self.resultats.constructif:
            constr = self.resultats.constructif
            contenu_c = ""
            for msg in constr.messages:
                icone = "✓" if msg["type"] == "ok" else ("❌" if msg["type"] == "erreur" else "⚠")
                contenu_c += f"{icone} {msg['message']}<br>"
            couleur = COULEUR_SUCCES if constr.verifie else COULEUR_ERREUR
            html += carte_html("Dispositions constructives", contenu_c, couleur)

        self.txt_resultats_ferraillage.setHtml(html)

    def _afficher_resultats_fissuration(self):
        if self.resultats is None or self.resultats.fissuration is None:
            return
        fiss = self.resultats.fissuration
        html = "<h2>Fissuration et vérifications ELS</h2>"

        if fiss.wmax_recommande is not None:
            html += carte_html("Ouverture de fissure admissible",
                               f"w<sub>max</sub> = {fiss.wmax_recommande:.2f} mm")
        else:
            html += carte_html("⚠ Dispositions particulières",
                               "wmax non défini pour cette classe d'exposition. "
                               "Des dispositions particulières sont requises.",
                               COULEUR_AVERTISSEMENT)

        contenu = ""
        for msg in fiss.messages:
            contenu += f"• {msg}<br>"
        html += carte_html("Détail des contrôles", contenu)

        if fiss.verdict == "Vérifié":
            html += carte_html(f"Verdict {badge_ok()}", "Fissuration maîtrisée.", COULEUR_SUCCES)
        elif fiss.verdict == "Non vérifié":
            html += carte_html(f"Verdict {badge_ko()}", "Fissuration non maîtrisée.", COULEUR_ERREUR)
        else:
            html += carte_html(f"Verdict {badge_attention()}", fiss.verdict, COULEUR_AVERTISSEMENT)

        self.txt_resultats_fissuration.setHtml(html)

    def _afficher_propositions(self, solutions):
        html = "<h2>Solutions de ferraillage proposées</h2>"

        if not solutions:
            html += carte_html("Info", "Aucune solution trouvée. Vérifiez les données.", COULEUR_AVERTISSEMENT)
            self.txt_propositions.setHtml(html)
            return

        tableau = (
            "<table border='1' cellpadding='6' cellspacing='0' style='border-collapse:collapse; width:100%;'>"
            "<tr style='background:#1565C0; color:white;'>"
            "<th>#</th><th>Solution</th><th>As (cm²)</th><th>Écart (%)</th>"
            "<th>Lits</th><th>Faisable</th><th>Score</th></tr>"
        )
        for i, sol in enumerate(solutions[:15], 1):
            faisable_txt = "✓" if sol.faisable else "✗"
            couleur = "" if sol.faisable else " style='background:#FFEBEE;'"
            tableau += (
                f"<tr{couleur}><td>{i}</td>"
                f"<td><b>{sol.description}</b></td>"
                f"<td>{sol.As_totale_cm2:.2f}</td>"
                f"<td>{sol.ecart_pourcent:+.1f}</td>"
                f"<td>{sol.nb_lits}</td>"
                f"<td>{faisable_txt}</td>"
                f"<td>{sol.score:.1f}</td></tr>"
            )
        tableau += "</table>"
        html += tableau

        self.txt_propositions.setHtml(html)

    def _afficher_apercu_rapport(self):
        if self.resultats is None:
            return
        html = "<h2>Aperçu du rapport</h2>"
        html += "<p>Cliquez sur « Générer le rapport PDF » pour créer le document complet.</p>"

        geo = self._lire_geometrie()
        mat = self._lire_materiaux()

        Mu_MNm = self.txt_mu_max.value()

        html += carte_html("Données d'entrée",
            f"Type : {geo.type_section.value}<br>"
            f"bw = {mm_to_cm(geo.b_w):.1f} cm, h = {mm_to_cm(geo.h):.1f} cm<br>"
            f"d = {mm_to_cm(geo.hauteur_utile_effective()):.1f} cm<br>"
            f"fck = {mat.beton.fck:.0f} MPa, fyk = {mat.acier.fyk:.0f} MPa<br>"
            f"Mu,max = {Mu_MNm:.4f} MN·m"
        )

        elu = self.resultats.elu
        if elu.calcul_valide:
            html += carte_html("Résultat principal",
                f"As,requise = <b>{elu.As_requise/100:.2f} cm²</b><br>"
                f"μcu = {elu.mu_cu:.4f}, α_u = {elu.alpha_u:.4f}<br>"
                f"Zc = {elu.Zc:.1f} mm, Pivot {elu.pivot.pivot}"
            )

        if self.resultats.verification:
            v = self.resultats.verification
            verdict = "VÉRIFIÉ" if v.verdict_global else "NON VÉRIFIÉ"
            html += carte_html("Verdict ferraillage",
                f"As,réelle = {v.As_reelle_mm2/100:.2f} cm², d_réel = {v.d_reel:.1f} mm<br>"
                f"<b>{verdict}</b>",
                COULEUR_SUCCES if v.verdict_global else COULEUR_ERREUR,
            )

        self.txt_rapport_apercu.setHtml(html)

    # ──────────────────────────────────────────────
    # Vue 2D
    # ──────────────────────────────────────────────
    def _generer_vue_2d(self):
        try:
            if self.resultats is None:
                self._lancer_calcul()
            if self.resultats is None:
                return

            geo = self._lire_geometrie()
            fer = self._lire_ferraillage()

            from app.visualization.section_plot_2d import dessiner_section_2d
            self.figure_2d.clear()
            dessiner_section_2d(self.figure_2d, geo, fer)
            self.canvas_2d.draw()
            self.statusBar().showMessage("Vue 2D générée.")
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors de la génération 2D :\n{e}")

    def _exporter_vue_2d(self):
        chemin, _ = QFileDialog.getSaveFileName(self, "Exporter la vue 2D", "section_2d.png", "Images PNG (*.png)")
        if chemin:
            self.figure_2d.savefig(chemin, dpi=200, bbox_inches="tight")
            self.statusBar().showMessage(f"Vue 2D exportée : {chemin}")

    # ──────────────────────────────────────────────
    # Vue 3D
    # ──────────────────────────────────────────────
    def _generer_vue_3d(self):
        try:
            if self.resultats is None:
                self._lancer_calcul()
            if self.resultats is None:
                return

            geo = self._lire_geometrie()
            fer = self._lire_ferraillage()

            from app.visualization.section_view_3d import creer_vue_3d
            widget_3d = creer_vue_3d(geo, fer)

            if self.lbl_3d_placeholder:
                self.lbl_3d_placeholder.setParent(None)
                self.lbl_3d_placeholder = None

            while self.widget_3d_container.count():
                item = self.widget_3d_container.takeAt(0)
                if item.widget():
                    item.widget().setParent(None)

            self.widget_3d_container.addWidget(widget_3d)
            self.statusBar().showMessage("Vue 3D générée.")
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors de la génération 3D :\n{e}\n\n{traceback.format_exc()}")

    # ──────────────────────────────────────────────
    # Rapport PDF
    # ──────────────────────────────────────────────
    def _generer_rapport(self):
        if self.resultats is None:
            QMessageBox.warning(self, "Attention", "Veuillez d'abord lancer un calcul.")
            return

        chemin, _ = QFileDialog.getSaveFileName(self, "Générer le rapport PDF", "rapport_flexion.pdf", "Fichiers PDF (*.pdf)")
        if not chemin:
            return

        try:
            img_2d_path = None
            try:
                import tempfile
                tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
                tmp.close()
                self._generer_vue_2d()
                self.figure_2d.savefig(tmp.name, dpi=150, bbox_inches="tight")
                img_2d_path = tmp.name
            except Exception:
                pass

            generer_rapport(
                chemin,
                self._lire_geometrie(),
                self._lire_materiaux(),
                self._lire_sollicitations(),
                self._lire_ferraillage(),
                self._lire_environnement(),
                self.resultats,
                image_2d_path=img_2d_path,
            )
            self.statusBar().showMessage(f"Rapport PDF généré : {chemin}")
            QMessageBox.information(self, "Rapport", f"Rapport généré avec succès :\n{chemin}")

            if img_2d_path and os.path.exists(img_2d_path):
                os.unlink(img_2d_path)

        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors de la génération du rapport :\n{e}")
