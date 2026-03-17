"""Fenêtre principale de l'application FlexiBeam — refonte UI premium."""
from __future__ import annotations

import os
import traceback
from typing import Optional

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QStackedWidget,
    QGroupBox, QLabel, QComboBox, QPushButton, QFormLayout,
    QTextBrowser, QTableWidget, QTableWidgetItem, QSpinBox,
    QDoubleSpinBox, QCheckBox, QScrollArea, QFileDialog,
    QMessageBox, QHeaderView, QFrame, QSizePolicy,
    QGraphicsDropShadowEffect, QApplication, QTabWidget,
    QSlider,
)
from PySide6.QtCore import Qt, QSize, QTimer
from PySide6.QtGui import QFont, QColor

from app.config import APP_NAME, APP_VERSION
from app.constants import AVAILABLE_DIAMETERS_MM, STEEL_TABLE_CM2, CLASSES_EXPOSITION
from app.models.section_models import DonneesGeometrie, TypeSection
from app.models.material_models import (
    DonneesBeton, DonneesAcier, DonneesMateriaux,
    ClasseDuctilite, DiagrammeAcier,
)
from app.models.load_models import DonneesSollicitations, DonneesPoutre, ChargeConcentree
from app.models.reinforcement_models import (
    LitArmature, DonneesFerraillage, DonneesEnvironnement,
)
from app.models.result_models import ResultatsComplets, ResultatSollicitations
from app.core.units import (
    cm_to_mm, mm_to_cm, MNm_to_Nmm, Nmm_to_MNm, Nmm_to_kNm,
    mm2_to_cm2, m_to_mm, mm_to_m, kNm_to_Nmm, N_to_kN, kN_to_N,
)
from app.core.examples import (
    exemple_rectangulaire, exemple_section_T,
    exemple_aciers_comprimes, exemple_figure,
)
from app.core.section_decision import DecisionSection
from app.services.calculation_service import (
    calcul_complet, calculer_sollicitations_poutre,
    calculer_effort_tranchant, calcul_complet_avec_poutre,
)
from app.services.suggestion_service import proposer_solutions
from app.services.persistence_service import sauvegarder_projet, charger_projet
from app.services.report_service import generer_rapport

from app.ui.theme import ThemeManager
from app.ui.widgets.sidebar import Sidebar
from app.ui.widgets.top_bar import TopBar
from app.ui.widgets.card_widget import CardWidget
from app.ui.widgets.metric_card import MetricCard
from app.ui.widgets.layer_editor import LayerEditor

TM = ThemeManager.get


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
class FenetrePrincipale(QMainWindow):
    """Fenêtre principale de l'application FlexiBeam."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{APP_NAME} v{APP_VERSION}")
        self.setMinimumSize(1200, 800)
        self.resize(1440, 900)

        self.resultats: Optional[ResultatsComplets] = None
        self.resultats_sol: Optional[ResultatSollicitations] = None

        self._build_ui()
        TM().on_change(self._on_theme_changed)
        self.statusBar().showMessage("Prêt — chargez un exemple ou saisissez vos données.")

    # ── Construction de l'interface ──────────────────────────────────────
    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Top bar
        self._topbar = TopBar()
        self._topbar.theme_toggled.connect(self._toggle_theme)
        self._topbar.example_clicked.connect(self._charger_exemple)
        self._topbar.reinit_clicked.connect(self._reinitialiser)
        self._topbar.open_clicked.connect(self._ouvrir_fichier)
        self._topbar.save_clicked.connect(self._sauvegarder_fichier)
        root.addWidget(self._topbar)

        body = QHBoxLayout()
        body.setContentsMargins(0, 0, 0, 0)
        body.setSpacing(0)

        # Sidebar
        self._sidebar = Sidebar()
        self._sidebar.page_changed.connect(self._go_page)
        body.addWidget(self._sidebar)

        # Stacked pages
        self._pages = QStackedWidget()
        self._pages.setStyleSheet("background:transparent;")
        body.addWidget(self._pages, 1)
        root.addLayout(body, 1)

        # Créer les 9 pages
        self._pages.addWidget(self._build_page_donnees())       # 0
        self._pages.addWidget(self._build_page_elu())           # 1
        self._pages.addWidget(self._build_page_ferraillage())   # 2
        self._pages.addWidget(self._build_page_fissuration())   # 3
        self._pages.addWidget(self._build_page_sollicitations()) # 4
        self._pages.addWidget(self._build_page_effort_tranchant()) # 5
        self._pages.addWidget(self._build_page_vue2d())         # 6
        self._pages.addWidget(self._build_page_vue3d())         # 7
        self._pages.addWidget(self._build_page_rapport())       # 8

    def _go_page(self, idx: int):
        self._pages.setCurrentIndex(idx)

    def _toggle_theme(self):
        TM().toggle()
        app = QApplication.instance()
        if app:
            TM().apply(app)

    def _on_theme_changed(self):
        pass  # widgets auto-refreshed via QSS

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    #  PAGE 1 – DONNÉES
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    def _build_page_donnees(self) -> QWidget:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        page = QWidget()
        page.setStyleSheet("background:transparent;")
        lay = QVBoxLayout(page)
        lay.setContentsMargins(24, 20, 24, 20)
        lay.setSpacing(16)

        # Titre
        t = QLabel("📊  Données du projet")
        t.setStyleSheet("font-size:20px; font-weight:700; background:transparent;")
        lay.addWidget(t)

        cols = QHBoxLayout()
        cols.setSpacing(16)

        # ── Col gauche : géometrie + sollicitations ──
        col_g = QVBoxLayout()
        col_g.setSpacing(12)

        # Géométrie
        card_geo = CardWidget("📐  Géométrie de la section")
        fg = QFormLayout()
        fg.setSpacing(8)
        fg.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self.cmb_type = QComboBox()
        self.cmb_type.addItems(["Rectangulaire", "T", "Auto"])
        fg.addRow("Type de section :", self.cmb_type)

        self.txt_bw = self._dspin(0, 999, " cm", 1); fg.addRow("bw  (largeur âme) :", self.txt_bw)
        self.txt_beff = self._dspin(0, 9999, " cm", 1); fg.addRow("beff  (largeur table) :", self.txt_beff)
        self.txt_hf = self._dspin(0, 999, " cm", 1); fg.addRow("hf  (hauteur table) :", self.txt_hf)
        self.txt_h = self._dspin(0, 999, " cm", 1); fg.addRow("h  (hauteur totale) :", self.txt_h)
        self.txt_d = self._dspin(0, 999, " cm", 1); fg.addRow("d  (hauteur utile) :", self.txt_d)

        self.chk_d_auto = QCheckBox("d auto = 0.9 × h")
        self.chk_d_auto.setChecked(True)
        fg.addRow("", self.chk_d_auto)

        self.txt_dprime = self._dspin(0, 99, " cm", 1, 5.0); fg.addRow("d'  (aciers compr.) :", self.txt_dprime)
        self.txt_cnom = self._dspin(0, 20, " cm", 1, 3.0); fg.addRow("c_nom  (enrobage) :", self.txt_cnom)
        self.txt_diam_etrier = self._dspin(0, 50, " mm", 0, 8.0); fg.addRow("Ø étrier :", self.txt_diam_etrier)
        self.txt_esp_v = self._dspin(0, 20, " cm", 1, 2.5); fg.addRow("Espacement vertical :", self.txt_esp_v)
        self.txt_esp_h = self._dspin(0, 20, " cm", 1, 2.5); fg.addRow("Espacement horizontal :", self.txt_esp_h)
        self.txt_dg = self._dspin(0, 100, " mm", 0, 20.0); fg.addRow("d_g  (granulat max) :", self.txt_dg)
        self.spn_max_lits = QSpinBox(); self.spn_max_lits.setRange(1, 10); self.spn_max_lits.setValue(4)
        fg.addRow("Nb max lits :", self.spn_max_lits)
        self.txt_longueur_ext = self._dspin(100, 10000, " mm", 0, 1000.0); fg.addRow("Longueur extrusion 3D :", self.txt_longueur_ext)

        card_geo.content_layout().addLayout(fg)
        col_g.addWidget(card_geo)

        # Sollicitations
        card_sol = CardWidget("⚡  Sollicitations")
        fs = QFormLayout()
        fs.setSpacing(8)
        fs.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        self.txt_mu_max = self._dspin(0, 9999, " MN·m", 4)
        fs.addRow("Mu,max  (moment ultime) :", self.txt_mu_max)
        self.txt_mser = self._dspin(0, 9999, " MN·m", 4)
        fs.addRow("Mser  (moment service) :", self.txt_mser)
        self.cmb_signe = QComboBox(); self.cmb_signe.addItems(["Positif", "Négatif"])
        fs.addRow("Signe du moment :", self.cmb_signe)
        card_sol.content_layout().addLayout(fs)
        col_g.addWidget(card_sol)

        col_g.addStretch()
        cols.addLayout(col_g, 1)

        # ── Col droite : matériaux + environnement + actions ──
        col_d = QVBoxLayout()
        col_d.setSpacing(12)

        card_mat = CardWidget("🧱  Matériaux")
        fm = QFormLayout(); fm.setSpacing(8)
        fm.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        self.txt_fck = self._dspin(12, 90, " MPa", 0, 25); fm.addRow("fck :", self.txt_fck)
        self.txt_fyk = self._dspin(200, 700, " MPa", 0, 500); fm.addRow("fyk :", self.txt_fyk)
        self.txt_Es = self._dspin(100000, 250000, " MPa", 0, 200000); fm.addRow("Es :", self.txt_Es)
        self.txt_alpha_cc = self._dspin(0.5, 1.5, "", 2, 1.0); fm.addRow("α_cc :", self.txt_alpha_cc)
        self.txt_gamma_c = self._dspin(1.0, 2.0, "", 2, 1.5); fm.addRow("γ_c :", self.txt_gamma_c)
        self.txt_gamma_s = self._dspin(1.0, 2.0, "", 2, 1.15); fm.addRow("γ_s :", self.txt_gamma_s)
        self.cmb_ductilite = QComboBox(); self.cmb_ductilite.addItems(["A", "B", "C"]); self.cmb_ductilite.setCurrentIndex(1)
        fm.addRow("Classe de ductilité :", self.cmb_ductilite)
        self.cmb_diagramme = QComboBox(); self.cmb_diagramme.addItems(["Palier horizontal", "Palier incliné"])
        fm.addRow("Diagramme acier :", self.cmb_diagramme)
        btn_def = QPushButton("Paramètres EC2 par défaut")
        btn_def.setProperty("class", "secondary")
        btn_def.clicked.connect(self._parametres_defaut)
        fm.addRow("", btn_def)
        card_mat.content_layout().addLayout(fm)
        col_d.addWidget(card_mat)

        card_env = CardWidget("🌍  Environnement / ELS")
        fe = QFormLayout(); fe.setSpacing(8)
        fe.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        self.cmb_exposition = QComboBox(); self.cmb_exposition.addItems(CLASSES_EXPOSITION)
        fe.addRow("Classe d'exposition :", self.cmb_exposition)
        self.chk_fissuration = QCheckBox("Maîtrise de la fissuration"); self.chk_fissuration.setChecked(True)
        fe.addRow("", self.chk_fissuration)
        self.txt_wmax = self._dspin(0, 1, " mm", 2); self.txt_wmax.setSpecialValueText("Auto")
        fe.addRow("w_max imposé :", self.txt_wmax)
        self.chk_calc_direct = QCheckBox("Calcul direct de fissuration")
        fe.addRow("", self.chk_calc_direct)
        card_env.content_layout().addLayout(fe)
        col_d.addWidget(card_env)

        # Bouton calculer
        card_act = CardWidget("🚀  Actions")
        btn_calc = QPushButton("⚡  CALCULER")
        btn_calc.setProperty("class", "success")
        btn_calc.setStyleSheet(
            "font-size:16px; padding:14px; font-weight:700; min-height:40px;"
        )
        btn_calc.clicked.connect(self._lancer_calcul)
        card_act.content_layout().addWidget(btn_calc)
        btn_prop = QPushButton("💡  Proposer un ferraillage")
        btn_prop.clicked.connect(self._proposer_ferraillage)
        card_act.content_layout().addWidget(btn_prop)
        col_d.addWidget(card_act)

        col_d.addStretch()
        cols.addLayout(col_d, 1)

        lay.addLayout(cols)
        scroll.setWidget(page)
        return scroll

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    #  PAGE 2 – CALCUL ELU
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    def _build_page_elu(self) -> QWidget:
        scroll = QScrollArea(); scroll.setWidgetResizable(True)
        page = QWidget(); page.setStyleSheet("background:transparent;")
        lay = QVBoxLayout(page)
        lay.setContentsMargins(24, 20, 24, 20); lay.setSpacing(12)
        t = QLabel("📐  Résultats du calcul ELU")
        t.setStyleSheet("font-size:20px; font-weight:700; background:transparent;")
        lay.addWidget(t)

        self.txt_resultats_elu = QTextBrowser()
        self.txt_resultats_elu.setOpenExternalLinks(False)
        self.txt_resultats_elu.setMinimumHeight(500)
        lay.addWidget(self.txt_resultats_elu)
        scroll.setWidget(page)
        return scroll

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    #  PAGE 3 – FERRAILLAGE
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    def _build_page_ferraillage(self) -> QWidget:
        scroll = QScrollArea(); scroll.setWidgetResizable(True)
        page = QWidget(); page.setStyleSheet("background:transparent;")
        lay = QVBoxLayout(page)
        lay.setContentsMargins(24, 20, 24, 20); lay.setSpacing(12)
        t = QLabel("🔩  Ferraillage — Éditeur de lits")
        t.setStyleSheet("font-size:20px; font-weight:700; background:transparent;")
        lay.addWidget(t)

        cols = QHBoxLayout(); cols.setSpacing(16)

        # Colonne gauche – éditeur + catalogue
        col_g = QVBoxLayout(); col_g.setSpacing(12)

        card_editor = CardWidget("Lits d'armatures")
        self.layer_editor = LayerEditor()
        card_editor.content_layout().addWidget(self.layer_editor)
        col_g.addWidget(card_editor)

        btn_verif = QPushButton("✓  Vérifier le ferraillage")
        btn_verif.setProperty("class", "success")
        btn_verif.setStyleSheet("font-size:14px; padding:12px; font-weight:600;")
        btn_verif.clicked.connect(self._verifier_ferraillage_ui)
        col_g.addWidget(btn_verif)

        # Catalogue
        card_cat = CardWidget("📖  Catalogue des armatures (cm²)")
        self.table_catalogue = QTableWidget()
        self.table_catalogue.setAlternatingRowColors(True)
        self._remplir_catalogue()
        self.table_catalogue.cellClicked.connect(self._clic_catalogue)
        card_cat.content_layout().addWidget(self.table_catalogue)
        col_g.addWidget(card_cat)

        cols.addLayout(col_g, 3)

        # Colonne droite – résultats + propositions
        col_d = QVBoxLayout(); col_d.setSpacing(12)

        self.txt_resultats_ferraillage = QTextBrowser()
        self.txt_resultats_ferraillage.setMinimumHeight(300)
        col_d.addWidget(self.txt_resultats_ferraillage)

        card_prop = CardWidget("💡  Solutions proposées")
        self.txt_propositions = QTextBrowser()
        self.txt_propositions.setMinimumHeight(150)
        card_prop.content_layout().addWidget(self.txt_propositions)
        btn_comp = QPushButton("📊  Comparer des solutions")
        btn_comp.setProperty("class", "secondary")
        btn_comp.clicked.connect(self._proposer_ferraillage)
        card_prop.content_layout().addWidget(btn_comp)
        col_d.addWidget(card_prop)

        cols.addLayout(col_d, 2)
        lay.addLayout(cols)
        scroll.setWidget(page)
        return scroll

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    #  PAGE 4 – FISSURATION (ELS améliorée)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    def _build_page_fissuration(self) -> QWidget:
        scroll = QScrollArea(); scroll.setWidgetResizable(True)
        page = QWidget(); page.setStyleSheet("background:transparent;")
        lay = QVBoxLayout(page)
        lay.setContentsMargins(24, 20, 24, 20); lay.setSpacing(12)
        t = QLabel("🔍  Fissuration / ELS")
        t.setStyleSheet("font-size:20px; font-weight:700; background:transparent;")
        lay.addWidget(t)
        self.txt_resultats_fissuration = QTextBrowser()
        self.txt_resultats_fissuration.setMinimumHeight(600)
        lay.addWidget(self.txt_resultats_fissuration)
        scroll.setWidget(page)
        return scroll

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    #  PAGE 5 – SOLLICITATIONS
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    def _build_page_sollicitations(self) -> QWidget:
        scroll = QScrollArea(); scroll.setWidgetResizable(True)
        page = QWidget(); page.setStyleSheet("background:transparent;")
        lay = QVBoxLayout(page)
        lay.setContentsMargins(24, 20, 24, 20); lay.setSpacing(12)
        t = QLabel("⚡  Sollicitations de la poutre")
        t.setStyleSheet("font-size:20px; font-weight:700; background:transparent;")
        lay.addWidget(t)

        # Sous-onglets
        tabs = QTabWidget()

        # -- Onglet Données poutre --
        tab_data = QWidget()
        td_lay = QVBoxLayout(tab_data); td_lay.setContentsMargins(12, 12, 12, 12)

        cols = QHBoxLayout(); cols.setSpacing(16)

        # Colonne gauche : géométrie poutre
        col_g = QVBoxLayout()
        card_poutre = CardWidget("📏  Géométrie de la poutre")
        fp = QFormLayout(); fp.setSpacing(8)
        fp.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self.cmb_type_poutre = QComboBox()
        self.cmb_type_poutre.addItems([
            "Poutre simple", "Console gauche", "Console droite", "Deux consoles",
        ])
        fp.addRow("Type de poutre :", self.cmb_type_poutre)

        self.txt_L_total = self._dspin(0, 50000, " mm", 0, 5000)
        fp.addRow("Longueur totale (mm) :", self.txt_L_total)

        self.txt_pos_A = self._dspin(0, 50000, " mm", 0, 0)
        fp.addRow("Position appui A (mm) :", self.txt_pos_A)

        self.txt_pos_B = self._dspin(0, 50000, " mm", 0, 5000)
        fp.addRow("Position appui B (mm) :", self.txt_pos_B)

        card_poutre.content_layout().addLayout(fp)
        col_g.addWidget(card_poutre)

        # Charges réparties
        card_charges = CardWidget("📦  Charges réparties")
        fc = QFormLayout(); fc.setSpacing(8)
        fc.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self.txt_g = self._dspin(0, 1000, " kN/m", 2, 0)
        fc.addRow("g (permanente) :", self.txt_g)

        self.txt_q = self._dspin(0, 1000, " kN/m", 2, 0)
        fc.addRow("q (exploitation) :", self.txt_q)

        card_charges.content_layout().addLayout(fc)
        col_g.addWidget(card_charges)

        # Coefficients psi
        card_psi = CardWidget("Coefficients ψ")
        fpsi = QFormLayout(); fpsi.setSpacing(8)
        self.txt_psi1 = self._dspin(0, 1, "", 2, 0.5)
        fpsi.addRow("ψ₁ (fréquente) :", self.txt_psi1)
        self.txt_psi2 = self._dspin(0, 1, "", 2, 0.3)
        fpsi.addRow("ψ₂ (quasi-perm.) :", self.txt_psi2)
        card_psi.content_layout().addLayout(fpsi)
        col_g.addWidget(card_psi)

        col_g.addStretch()
        cols.addLayout(col_g, 1)

        # Colonne droite : charges concentrées + actions
        col_d = QVBoxLayout()

        card_conc = CardWidget("🎯  Charges concentrées")
        self.table_charges_conc = QTableWidget()
        self.table_charges_conc.setColumnCount(4)
        self.table_charges_conc.setHorizontalHeaderLabels(["Position (mm)", "G (kN)", "Q (kN)", "Label"])
        self.table_charges_conc.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table_charges_conc.setRowCount(0)
        card_conc.content_layout().addWidget(self.table_charges_conc)

        btn_row = QHBoxLayout()
        btn_add = QPushButton("➕ Ajouter"); btn_add.clicked.connect(self._ajouter_charge_conc)
        btn_rem = QPushButton("➖ Supprimer"); btn_rem.setProperty("class", "danger")
        btn_rem.clicked.connect(self._supprimer_charge_conc)
        btn_row.addWidget(btn_add); btn_row.addWidget(btn_rem); btn_row.addStretch()
        card_conc.content_layout().addLayout(btn_row)
        col_d.addWidget(card_conc)

        # Combinaison et position x
        card_calcul = CardWidget("🚀  Calcul")
        fcalc = QFormLayout(); fcalc.setSpacing(8)

        self.cmb_combinaison = QComboBox()
        self.cmb_combinaison.addItems(["ELU", "ELS caractéristique", "ELS fréquente", "ELS quasi-permanente"])
        fcalc.addRow("Combinaison :", self.cmb_combinaison)

        self.txt_x_choisi = self._dspin(0, 50000, " mm", 0, 2500)
        fcalc.addRow("Position x (mm) :", self.txt_x_choisi)

        card_calcul.content_layout().addLayout(fcalc)

        btn_sol = QPushButton("⚡  Calculer les sollicitations")
        btn_sol.setProperty("class", "success")
        btn_sol.setStyleSheet("font-size:14px; padding:12px; font-weight:600;")
        btn_sol.clicked.connect(self._calculer_sollicitations)
        card_calcul.content_layout().addWidget(btn_sol)

        btn_envoyer = QPushButton("📤  Envoyer vers ELU / ELS / Effort tranchant")
        btn_envoyer.clicked.connect(self._envoyer_sollicitations)
        card_calcul.content_layout().addWidget(btn_envoyer)

        col_d.addWidget(card_calcul)
        col_d.addStretch()
        cols.addLayout(col_d, 1)
        td_lay.addLayout(cols)
        tabs.addTab(tab_data, "📊 Données")

        # -- Onglet Résultats --
        tab_res = QWidget()
        tr_lay = QVBoxLayout(tab_res); tr_lay.setContentsMargins(12, 12, 12, 12)
        self.txt_resultats_sol = QTextBrowser()
        self.txt_resultats_sol.setMinimumHeight(400)
        tr_lay.addWidget(self.txt_resultats_sol)
        tabs.addTab(tab_res, "📋 Résultats")

        # -- Onglet Diagrammes --
        tab_diag = QWidget()
        tdiag_lay = QVBoxLayout(tab_diag); tdiag_lay.setContentsMargins(12, 12, 12, 12)

        from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
        from matplotlib.figure import Figure
        self.figure_sol = Figure(figsize=(12, 8), dpi=100)
        self.canvas_sol = FigureCanvasQTAgg(self.figure_sol)
        tdiag_lay.addWidget(self.canvas_sol, 1)

        btn_diag_row = QHBoxLayout()
        btn_schema = QPushButton("Schéma poutre"); btn_schema.clicked.connect(lambda: self._dessiner_sol("schema_poutre"))
        btn_diagrams = QPushButton("Diagrammes"); btn_diagrams.clicked.connect(lambda: self._dessiner_sol("diagrammes"))
        btn_full = QPushButton("Vue complète"); btn_full.clicked.connect(lambda: self._dessiner_sol("vue_complete"))
        btn_export_sol = QPushButton("💾 Exporter PNG"); btn_export_sol.setProperty("class", "secondary")
        btn_export_sol.clicked.connect(self._exporter_sol_2d)
        btn_diag_row.addWidget(btn_schema); btn_diag_row.addWidget(btn_diagrams)
        btn_diag_row.addWidget(btn_full); btn_diag_row.addWidget(btn_export_sol)
        btn_diag_row.addStretch()
        tdiag_lay.addLayout(btn_diag_row)
        tabs.addTab(tab_diag, "📈 Diagrammes")

        # -- Onglet Vue 3D sollicitations --
        tab_3d = QWidget()
        t3d_lay = QVBoxLayout(tab_3d); t3d_lay.setContentsMargins(12, 12, 12, 12)

        self.figure_sol_3d = Figure(figsize=(12, 8), dpi=100)
        self.canvas_sol_3d = FigureCanvasQTAgg(self.figure_sol_3d)
        t3d_lay.addWidget(self.canvas_sol_3d, 1)

        btn_3d_row = QHBoxLayout()
        btn_3d_struct = QPushButton("Structure"); btn_3d_struct.clicked.connect(lambda: self._dessiner_sol_3d("vue_structure"))
        btn_3d_charges = QPushButton("Charges"); btn_3d_charges.clicked.connect(lambda: self._dessiner_sol_3d("vue_charges"))
        btn_3d_sol = QPushButton("Sollicitations"); btn_3d_sol.clicked.connect(lambda: self._dessiner_sol_3d("vue_sollicitations"))
        btn_3d_full = QPushButton("Complète"); btn_3d_full.clicked.connect(lambda: self._dessiner_sol_3d("vue_complete"))
        btn_3d_export = QPushButton("💾 Export"); btn_3d_export.setProperty("class", "secondary")
        btn_3d_export.clicked.connect(self._exporter_sol_3d)
        btn_3d_row.addWidget(btn_3d_struct); btn_3d_row.addWidget(btn_3d_charges)
        btn_3d_row.addWidget(btn_3d_sol); btn_3d_row.addWidget(btn_3d_full)
        btn_3d_row.addWidget(btn_3d_export); btn_3d_row.addStretch()
        t3d_lay.addLayout(btn_3d_row)
        tabs.addTab(tab_3d, "🧊 Vue 3D")

        lay.addWidget(tabs, 1)
        scroll.setWidget(page)
        return scroll

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    #  PAGE 6 – EFFORT TRANCHANT
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    def _build_page_effort_tranchant(self) -> QWidget:
        scroll = QScrollArea(); scroll.setWidgetResizable(True)
        page = QWidget(); page.setStyleSheet("background:transparent;")
        lay = QVBoxLayout(page)
        lay.setContentsMargins(24, 20, 24, 20); lay.setSpacing(12)
        t = QLabel("🔧  Effort tranchant")
        t.setStyleSheet("font-size:20px; font-weight:700; background:transparent;")
        lay.addWidget(t)

        cols = QHBoxLayout(); cols.setSpacing(16)

        # Colonne gauche : entrées
        col_g = QVBoxLayout()
        card_et = CardWidget("⚡  Données effort tranchant")
        fe = QFormLayout(); fe.setSpacing(8)
        fe.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self.txt_Ved = self._dspin(0, 99999, " kN", 1, 0)
        fe.addRow("Ved (effort tranchant) :", self.txt_Ved)

        self.txt_et_diam = self._dspin(4, 32, " mm", 0, 8)
        fe.addRow("Ø étrier :", self.txt_et_diam)

        self.spn_nb_branches = QSpinBox(); self.spn_nb_branches.setRange(2, 8); self.spn_nb_branches.setValue(2)
        fe.addRow("Nb branches :", self.spn_nb_branches)

        self.txt_esp_etriers = self._dspin(50, 600, " mm", 0, 200)
        fe.addRow("Espacement étriers :", self.txt_esp_etriers)

        self.txt_theta = self._dspin(21.8, 45, " °", 1, 45)
        fe.addRow("θ (angle bielles) :", self.txt_theta)

        card_et.content_layout().addLayout(fe)

        btn_et = QPushButton("🔧  Vérifier l'effort tranchant")
        btn_et.setProperty("class", "success")
        btn_et.setStyleSheet("font-size:14px; padding:12px; font-weight:600;")
        btn_et.clicked.connect(self._calculer_effort_tranchant)
        card_et.content_layout().addWidget(btn_et)

        col_g.addWidget(card_et)
        col_g.addStretch()
        cols.addLayout(col_g, 1)

        # Colonne droite : résultats
        col_d = QVBoxLayout()
        self.txt_resultats_et = QTextBrowser()
        self.txt_resultats_et.setMinimumHeight(500)
        col_d.addWidget(self.txt_resultats_et)
        cols.addLayout(col_d, 1)

        lay.addLayout(cols)
        scroll.setWidget(page)
        return scroll

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    #  PAGE 7 – VUE 2D
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    def _build_page_vue2d(self) -> QWidget:
        page = QWidget(); page.setStyleSheet("background:transparent;")
        lay = QVBoxLayout(page)
        lay.setContentsMargins(24, 20, 24, 20); lay.setSpacing(12)
        t = QLabel("📏  Vue 2D de la section")
        t.setStyleSheet("font-size:20px; font-weight:700; background:transparent;")
        lay.addWidget(t)

        btns = QHBoxLayout(); btns.setSpacing(8)
        b1 = QPushButton("🖼  Générer la vue 2D"); b1.clicked.connect(self._generer_vue_2d); btns.addWidget(b1)
        b2 = QPushButton("💾  Exporter PNG"); b2.setProperty("class", "secondary"); b2.clicked.connect(self._exporter_vue_2d); btns.addWidget(b2)
        btns.addStretch()
        lay.addLayout(btns)

        from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
        from matplotlib.figure import Figure
        self.figure_2d = Figure(figsize=(10, 8), dpi=100)
        self.canvas_2d = FigureCanvasQTAgg(self.figure_2d)
        lay.addWidget(self.canvas_2d, 1)
        return page

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    #  PAGE 8 – VUE 3D
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    def _build_page_vue3d(self) -> QWidget:
        page = QWidget(); page.setStyleSheet("background:transparent;")
        lay = QVBoxLayout(page)
        lay.setContentsMargins(24, 20, 24, 20); lay.setSpacing(12)
        t = QLabel("🧊  Vue 3D de la section")
        t.setStyleSheet("font-size:20px; font-weight:700; background:transparent;")
        lay.addWidget(t)
        btns = QHBoxLayout()
        b = QPushButton("🧊  Générer la vue 3D"); b.clicked.connect(self._generer_vue_3d); btns.addWidget(b)
        btns.addStretch()
        lay.addLayout(btns)
        self.widget_3d_container = QVBoxLayout()
        lay.addLayout(self.widget_3d_container, 1)
        self.lbl_3d_placeholder = QLabel("Cliquez sur « Générer la vue 3D » après avoir lancé un calcul.")
        self.lbl_3d_placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_3d_placeholder.setStyleSheet("font-size:14px; padding:40px; background:transparent;")
        self.widget_3d_container.addWidget(self.lbl_3d_placeholder)
        return page

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    #  PAGE 9 – RAPPORT
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    def _build_page_rapport(self) -> QWidget:
        page = QWidget(); page.setStyleSheet("background:transparent;")
        lay = QVBoxLayout(page)
        lay.setContentsMargins(24, 20, 24, 20); lay.setSpacing(12)
        t = QLabel("📄  Rapport de synthèse")
        t.setStyleSheet("font-size:20px; font-weight:700; background:transparent;")
        lay.addWidget(t)
        btn = QPushButton("📄  Générer le rapport PDF")
        btn.setStyleSheet("font-size:16px; padding:14px; font-weight:700;")
        btn.clicked.connect(self._generer_rapport)
        lay.addWidget(btn)
        self.txt_rapport_apercu = QTextBrowser()
        self.txt_rapport_apercu.setMinimumHeight(500)
        lay.addWidget(self.txt_rapport_apercu, 1)
        return page

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    #  UTILITAIRE DE CRÉATION DE SPINBOX
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    @staticmethod
    def _dspin(lo, hi, suffix="", decimals=2, value=0.0) -> QDoubleSpinBox:
        s = QDoubleSpinBox()
        s.setRange(lo, hi)
        if suffix:
            s.setSuffix(suffix)
        s.setDecimals(decimals)
        s.setValue(value)
        return s

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    #  LECTURE DES DONNÉES (UI cm → modèle mm)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    def _lire_geometrie(self) -> DonneesGeometrie:
        type_map = {"Rectangulaire": TypeSection.RECTANGULAIRE,
                    "T": TypeSection.T, "Auto": TypeSection.AUTO}
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
        duct = {"A": ClasseDuctilite.A, "B": ClasseDuctilite.B, "C": ClasseDuctilite.C}
        diag = {"Palier horizontal": DiagrammeAcier.PALIER_HORIZONTAL,
                "Palier incliné": DiagrammeAcier.PALIER_INCLINE}
        return DonneesMateriaux(
            beton=DonneesBeton(fck=self.txt_fck.value(),
                               alpha_cc=self.txt_alpha_cc.value(),
                               gamma_c=self.txt_gamma_c.value()),
            acier=DonneesAcier(fyk=self.txt_fyk.value(),
                               Es=self.txt_Es.value(),
                               gamma_s=self.txt_gamma_s.value(),
                               classe_ductilite=duct[self.cmb_ductilite.currentText()],
                               diagramme=diag[self.cmb_diagramme.currentText()]),
        )

    def _lire_sollicitations(self) -> DonneesSollicitations:
        return DonneesSollicitations(
            M_Ed=MNm_to_Nmm(self.txt_mu_max.value()),
            M_ser=MNm_to_Nmm(self.txt_mser.value()),
            moment_positif=(self.cmb_signe.currentText() == "Positif"),
        )

    def _lire_ferraillage(self) -> DonneesFerraillage:
        lits: list[LitArmature] = []
        for i, item in enumerate(self.layer_editor.get_lits()):
            lits.append(LitArmature(
                numero=i + 1,
                nombre_barres=item["nb"],
                diametre_mm=float(item["diam_mm"]),
                type_lit=item.get("type", "tendu"),
                espacement_precedent_cm=item.get("spacing_cm", 5.0),
                distance_fibre_tendue_cm=item.get("distance_cm", 0.0),
                auto_first=item.get("auto_first", False),
                label=item.get("label", ""),
            ))
        return DonneesFerraillage(lits_tendus=lits)

    def _lire_environnement(self) -> DonneesEnvironnement:
        wmax = self.txt_wmax.value()
        return DonneesEnvironnement(
            classe_exposition=self.cmb_exposition.currentText(),
            maitrise_fissuration=self.chk_fissuration.isChecked(),
            wmax_impose=wmax if wmax > 0 else None,
            calcul_direct_fissuration=self.chk_calc_direct.isChecked(),
        )

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    #  ÉCRITURE DES DONNÉES (modèle mm → UI cm)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    def _ecrire_geometrie(self, g: DonneesGeometrie):
        m = {TypeSection.RECTANGULAIRE: 0, TypeSection.T: 1, TypeSection.AUTO: 2}
        self.cmb_type.setCurrentIndex(m.get(g.type_section, 0))
        self.txt_bw.setValue(mm_to_cm(g.b_w))
        self.txt_beff.setValue(mm_to_cm(g.b_eff))
        self.txt_hf.setValue(mm_to_cm(g.h_f))
        self.txt_h.setValue(mm_to_cm(g.h))
        self.txt_d.setValue(mm_to_cm(g.d))
        self.txt_dprime.setValue(mm_to_cm(g.d_prime))
        self.txt_cnom.setValue(mm_to_cm(g.c_nom))
        self.txt_diam_etrier.setValue(g.diam_etrier)
        self.txt_esp_v.setValue(mm_to_cm(g.espacement_vertical))
        self.txt_esp_h.setValue(mm_to_cm(g.espacement_horizontal))
        self.txt_dg.setValue(g.d_g)
        self.spn_max_lits.setValue(g.nb_max_lits)
        self.txt_longueur_ext.setValue(g.longueur_extrusion)
        self.chk_d_auto.setChecked(g.d_auto)

    def _ecrire_materiaux(self, m: DonneesMateriaux):
        self.txt_fck.setValue(m.beton.fck)
        self.txt_alpha_cc.setValue(m.beton.alpha_cc)
        self.txt_gamma_c.setValue(m.beton.gamma_c)
        self.txt_fyk.setValue(m.acier.fyk)
        self.txt_Es.setValue(m.acier.Es)
        self.txt_gamma_s.setValue(m.acier.gamma_s)
        dm = {ClasseDuctilite.A: 0, ClasseDuctilite.B: 1, ClasseDuctilite.C: 2}
        self.cmb_ductilite.setCurrentIndex(dm.get(m.acier.classe_ductilite, 1))
        dg = {DiagrammeAcier.PALIER_HORIZONTAL: 0, DiagrammeAcier.PALIER_INCLINE: 1}
        self.cmb_diagramme.setCurrentIndex(dg.get(m.acier.diagramme, 0))

    def _ecrire_sollicitations(self, s: DonneesSollicitations):
        self.txt_mu_max.setValue(Nmm_to_MNm(s.M_Ed))
        self.txt_mser.setValue(Nmm_to_MNm(s.M_ser))
        self.cmb_signe.setCurrentIndex(0 if s.moment_positif else 1)

    def _ecrire_ferraillage(self, f: DonneesFerraillage):
        lits_data = [
            {
                "diam_mm": int(l.diametre_mm),
                "nb": l.nombre_barres,
                "type": l.type_lit,
                "spacing_cm": l.espacement_precedent_cm,
                "auto_first": l.auto_first,
                "label": l.label,
            }
            for l in f.lits_tendus
        ]
        self.layer_editor.set_lits(lits_data)

    def _ecrire_environnement(self, e: DonneesEnvironnement):
        idx = CLASSES_EXPOSITION.index(e.classe_exposition) if e.classe_exposition in CLASSES_EXPOSITION else 0
        self.cmb_exposition.setCurrentIndex(idx)
        self.chk_fissuration.setChecked(e.maitrise_fissuration)
        self.txt_wmax.setValue(e.wmax_impose if e.wmax_impose is not None else 0)
        self.chk_calc_direct.setChecked(e.calcul_direct_fissuration)

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    #  CATALOGUE D'ARMATURES
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    def _remplir_catalogue(self):
        diams = AVAILABLE_DIAMETERS_MM
        self.table_catalogue.setRowCount(len(diams))
        self.table_catalogue.setColumnCount(11)
        self.table_catalogue.setHorizontalHeaderLabels(
            ["Ø (mm)"] + [str(i) for i in range(1, 11)]
        )
        self.table_catalogue.verticalHeader().setVisible(False)
        p = TM().p
        for row, d in enumerate(diams):
            it = QTableWidgetItem(f"HA{d}")
            it.setFlags(Qt.ItemFlag.ItemIsEnabled)
            it.setBackground(QColor(p.ac))
            it.setForeground(QColor("white"))
            f = it.font(); f.setBold(True); it.setFont(f)
            self.table_catalogue.setItem(row, 0, it)
            for col in range(1, 11):
                v = STEEL_TABLE_CM2.get(d, {}).get(col, 0)
                item = QTableWidgetItem(f"{v:.2f}")
                item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table_catalogue.setItem(row, col, item)
        self.table_catalogue.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )

    def _clic_catalogue(self, row: int, col: int):
        if col == 0:
            return
        self.layer_editor.set_from_catalogue(AVAILABLE_DIAMETERS_MM[row], col)

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    #  ACTIONS
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    def _lancer_calcul(self):
        try:
            geo = self._lire_geometrie()
            self._sync_layer_geometry(geo)
            mat = self._lire_materiaux()
            sol = self._lire_sollicitations()
            fer = self._lire_ferraillage()
            env = self._lire_environnement()
            self.resultats = calcul_complet(geo, mat, sol, fer, env)
            self._afficher_resultats_elu()
            self._afficher_resultats_ferraillage()
            self._afficher_resultats_fissuration()
            self._afficher_apercu_rapport()
            self.statusBar().showMessage("✓ Calcul terminé avec succès.")
            self._go_page(1)
            self._sidebar.set_page(1)
        except Exception as e:
            QMessageBox.critical(self, "Erreur de calcul",
                                 f"{e}\n\n{traceback.format_exc()}")
            self.statusBar().showMessage("Erreur lors du calcul.")

    def _verifier_ferraillage_ui(self):
        self._lancer_calcul()
        self._go_page(2)
        self._sidebar.set_page(2)

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
            self._go_page(2)
            self._sidebar.set_page(2)
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur proposition :\n{e}")

    def _charger_exemple(self, t: str):
        exf = {"rect": exemple_rectangulaire, "T": exemple_section_T,
               "figure": exemple_figure, "comp": exemple_aciers_comprimes}
        ex = exf.get(t, exemple_aciers_comprimes)()
        self._ecrire_geometrie(ex["geometrie"])
        self._ecrire_materiaux(ex["materiaux"])
        self._ecrire_sollicitations(ex["sollicitations"])
        self._sync_layer_geometry(ex["geometrie"])
        self._ecrire_ferraillage(ex["ferraillage"])
        self._ecrire_environnement(ex["environnement"])
        self.statusBar().showMessage(f"Exemple chargé : {ex['nom']}")

    def _reinitialiser(self):
        self.txt_bw.setValue(0); self.txt_beff.setValue(0)
        self.txt_hf.setValue(0); self.txt_h.setValue(0)
        self.txt_d.setValue(0); self.txt_dprime.setValue(5.0)
        self.txt_mu_max.setValue(0); self.txt_mser.setValue(0)
        self._parametres_defaut()
        self.layer_editor.clear()
        self.resultats = None
        self.resultats_sol = None
        self.txt_resultats_elu.clear()
        self.txt_resultats_ferraillage.clear()
        self.txt_resultats_fissuration.clear()
        self.txt_propositions.clear()
        self.txt_rapport_apercu.clear()
        self.txt_resultats_sol.clear()
        self.txt_resultats_et.clear()
        self.figure_2d.clear(); self.canvas_2d.draw()
        self.figure_sol.clear(); self.canvas_sol.draw()
        self.figure_sol_3d.clear(); self.canvas_sol_3d.draw()
        self.statusBar().showMessage("Application réinitialisée.")

    def _parametres_defaut(self):
        self.txt_fck.setValue(25); self.txt_fyk.setValue(500)
        self.txt_Es.setValue(200000); self.txt_alpha_cc.setValue(1.0)
        self.txt_gamma_c.setValue(1.5); self.txt_gamma_s.setValue(1.15)
        self.cmb_ductilite.setCurrentIndex(1); self.cmb_diagramme.setCurrentIndex(0)

    def _sync_layer_geometry(self, geo: DonneesGeometrie = None):
        """Synchronise les paramètres géométriques vers le LayerEditor."""
        if geo is None:
            geo = self._lire_geometrie()
        self.layer_editor.set_geometry_params(
            h_mm=geo.h,
            d_mm=geo.hauteur_utile_effective(),
            c_nom_mm=geo.c_nom,
            diam_etrier_mm=geo.diam_etrier,
        )

    def _ouvrir_fichier(self):
        chemin, _ = QFileDialog.getOpenFileName(self, "Ouvrir", "", "JSON (*.json)")
        if chemin:
            try:
                d = charger_projet(chemin)
                self._ecrire_geometrie(d["geometrie"])
                self._ecrire_materiaux(d["materiaux"])
                self._ecrire_sollicitations(d["sollicitations"])
                self._sync_layer_geometry(d["geometrie"])
                self._ecrire_ferraillage(d["ferraillage"])
                self._ecrire_environnement(d["environnement"])
                self.statusBar().showMessage(f"Projet chargé : {chemin}")
            except Exception as e:
                QMessageBox.critical(self, "Erreur", str(e))

    def _sauvegarder_fichier(self):
        chemin, _ = QFileDialog.getSaveFileName(
            self, "Sauvegarder", "projet_flexion.json", "JSON (*.json)"
        )
        if chemin:
            try:
                sauvegarder_projet(chemin, self._lire_geometrie(),
                                   self._lire_materiaux(),
                                   self._lire_sollicitations(),
                                   self._lire_ferraillage(),
                                   self._lire_environnement())
                self.statusBar().showMessage(f"Projet sauvegardé : {chemin}")
            except Exception as e:
                QMessageBox.critical(self, "Erreur", str(e))

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    #  SOLLICITATIONS
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    def _lire_poutre(self) -> DonneesPoutre:
        """Lit les données de la poutre depuis l'interface."""
        type_map = {
            "Poutre simple": "simple",
            "Console gauche": "console_gauche",
            "Console droite": "console_droite",
            "Deux consoles": "deux_consoles",
        }
        charges = []
        for row in range(self.table_charges_conc.rowCount()):
            try:
                pos = float(self.table_charges_conc.item(row, 0).text()) if self.table_charges_conc.item(row, 0) else 0
                G = float(self.table_charges_conc.item(row, 1).text()) * 1000 if self.table_charges_conc.item(row, 1) else 0  # kN→N
                Q = float(self.table_charges_conc.item(row, 2).text()) * 1000 if self.table_charges_conc.item(row, 2) else 0
                label = self.table_charges_conc.item(row, 3).text() if self.table_charges_conc.item(row, 3) else ""
                charges.append(ChargeConcentree(position_mm=pos, G_N=G, Q_N=Q, label=label))
            except (ValueError, AttributeError):
                pass

        return DonneesPoutre(
            type_poutre=type_map.get(self.cmb_type_poutre.currentText(), "simple"),
            longueur_totale_mm=self.txt_L_total.value(),
            position_appui_A_mm=self.txt_pos_A.value(),
            position_appui_B_mm=self.txt_pos_B.value(),
            g_N_mm=self.txt_g.value(),  # kN/m → N/mm (même valeur numérique)
            q_N_mm=self.txt_q.value(),
            charges_concentrees=charges,
            psi_1=self.txt_psi1.value(),
            psi_2=self.txt_psi2.value(),
        )

    def _ajouter_charge_conc(self):
        """Ajoute une ligne dans le tableau des charges concentrées."""
        row = self.table_charges_conc.rowCount()
        self.table_charges_conc.insertRow(row)
        self.table_charges_conc.setItem(row, 0, QTableWidgetItem("2500"))
        self.table_charges_conc.setItem(row, 1, QTableWidgetItem("0"))
        self.table_charges_conc.setItem(row, 2, QTableWidgetItem("0"))
        self.table_charges_conc.setItem(row, 3, QTableWidgetItem(f"P{row+1}"))

    def _supprimer_charge_conc(self):
        """Supprime la ligne sélectionnée."""
        row = self.table_charges_conc.currentRow()
        if row >= 0:
            self.table_charges_conc.removeRow(row)

    def _calculer_sollicitations(self):
        """Lance le calcul des sollicitations."""
        try:
            poutre = self._lire_poutre()
            x = self.txt_x_choisi.value()
            comb = self.cmb_combinaison.currentText()

            self.resultats_sol = calculer_sollicitations_poutre(poutre, x, comb)

            self._afficher_resultats_sollicitations()
            self._dessiner_sol("vue_complete")
            self._dessiner_sol_3d("vue_complete")
            self.statusBar().showMessage("Sollicitations calculées.")
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"{e}\n\n{traceback.format_exc()}")

    def _envoyer_sollicitations(self):
        """Transfère les sollicitations au point x vers ELU / ELS / effort tranchant."""
        if self.resultats_sol is None or not self.resultats_sol.calcul_valide:
            self._calculer_sollicitations()
        if self.resultats_sol is None or not self.resultats_sol.calcul_valide:
            return

        # Mettre à jour Mu et Mser
        self.txt_mu_max.setValue(Nmm_to_MNm(self.resultats_sol.MEd))
        self.txt_mser.setValue(Nmm_to_MNm(self.resultats_sol.Mser))

        # Mettre à jour Ved
        self.txt_Ved.setValue(N_to_kN(self.resultats_sol.Ved))

        self.statusBar().showMessage(
            f"Sollicitations transférées : MEd = {Nmm_to_kNm(self.resultats_sol.MEd):.2f} kN·m, "
            f"Mser = {Nmm_to_kNm(self.resultats_sol.Mser):.2f} kN·m, "
            f"Ved = {N_to_kN(self.resultats_sol.Ved):.1f} kN"
        )

    def _afficher_resultats_sollicitations(self):
        """Affiche les résultats des sollicitations."""
        if self.resultats_sol is None:
            return
        r = self.resultats_sol
        tm = TM(); p = tm.p
        html = ""

        if r.erreurs:
            for err in r.erreurs:
                html += tm.carte("❌ Erreur", err, p.err)
            self.txt_resultats_sol.setHtml(html)
            return

        # Métriques
        html += '<table cellspacing="8" style="width:100%;"><tr>'
        html += f'<td>{tm.metric_html("RA", f"{r.RA/1000:.1f}", "kN")}</td>'
        html += f'<td>{tm.metric_html("RB", f"{r.RB/1000:.1f}", "kN")}</td>'
        html += f'<td>{tm.metric_html("V(x)", f"{r.Vx/1000:.1f}", "kN")}</td>'
        html += f'<td>{tm.metric_html("M(x)", f"{r.Mx/1e6:.2f}", "kN·m")}</td>'
        html += f'<td>{tm.metric_html("Zone", r.zone, "")}</td>'
        html += '</tr></table>'

        # Réactions
        html += tm.carte_light("Réactions d'appui",
            f"R<sub>A</sub> = {r.RA/1000:.2f} kN<br>"
            f"R<sub>B</sub> = {r.RB/1000:.2f} kN<br>"
            f"Combinaison : <b>{r.combinaison}</b>")

        # Valeurs au point x
        html += tm.carte_light(f"Position x = {r.x_choisi:.0f} mm",
            f"V(x) = {r.Vx/1000:.2f} kN<br>"
            f"M(x) = {r.Mx/1e6:.4f} kN·m<br>"
            f"Zone : <b>{r.zone}</b>")

        # Extrema
        html += tm.carte_light("Valeurs extrêmes",
            f"M<sub>max</sub> = {r.M_max/1e6:.2f} kN·m à x = {r.x_M_max:.0f} mm<br>"
            f"M<sub>min</sub> = {r.M_min/1e6:.2f} kN·m<br>"
            f"V<sub>max</sub> = {r.V_max/1000:.1f} kN à x = {r.x_V_max:.0f} mm<br>"
            f"V<sub>min</sub> = {r.V_min/1000:.1f} kN")

        # Moments pour autres calculs
        html += tm.carte("Sollicitations de calcul au point x",
            f"M<sub>Ed</sub> (ELU) = {r.MEd/1e6:.2f} kN·m = {Nmm_to_MNm(r.MEd):.4f} MN·m<br>"
            f"M<sub>ser</sub> (ELS) = {r.Mser/1e6:.2f} kN·m<br>"
            f"V<sub>Ed</sub> (ELU) = {r.Ved/1000:.1f} kN", p.ac)

        # Tableau récapitulatif
        if r.x_values and r.V_values and r.M_values:
            step = max(len(r.x_values) // 20, 1)
            tab = ("<table cellpadding='4' cellspacing='0' style='width:100%; border-collapse:collapse;'>"
                   f"<tr style='background:{p.ac};color:white;'>"
                   "<th>x (mm)</th><th>V (kN)</th><th>M (kN·m)</th></tr>")
            for i in range(0, len(r.x_values), step):
                tab += (f"<tr><td>{r.x_values[i]:.0f}</td>"
                        f"<td>{r.V_values[i]/1000:.2f}</td>"
                        f"<td>{r.M_values[i]/1e6:.4f}</td></tr>")
            tab += "</table>"
            html += tm.carte_light("Tableau des valeurs", tab)

        self.txt_resultats_sol.setHtml(html)

    def _dessiner_sol(self, mode: str = "vue_complete"):
        """Dessine le schéma de la poutre et les diagrammes."""
        try:
            from app.visualization.beam_plot_2d import draw_beam_2d
            poutre = self._lire_poutre()
            x = self.txt_x_choisi.value()
            comb = self.cmb_combinaison.currentText()
            draw_beam_2d(self.figure_sol, poutre, self.resultats_sol, x, mode, comb)
            self.canvas_sol.draw()
        except Exception as e:
            QMessageBox.critical(self, "Erreur", str(e))

    def _dessiner_sol_3d(self, mode: str = "vue_complete"):
        """Dessine la vue 3D de la poutre."""
        try:
            from app.visualization.beam_view_3d import render_beam_scene_3d
            poutre = self._lire_poutre()
            geo = self._lire_geometrie()
            x = self.txt_x_choisi.value()
            comb = self.cmb_combinaison.currentText()
            render_beam_scene_3d(
                self.figure_sol_3d, poutre, self.resultats_sol, x,
                section_width=geo.b_w if geo.b_w > 0 else 300,
                section_height=geo.h if geo.h > 0 else 500,
                mode=mode, combinaison=comb,
            )
            self.canvas_sol_3d.draw()
        except Exception as e:
            QMessageBox.critical(self, "Erreur", str(e))

    def _exporter_sol_2d(self):
        ch, _ = QFileDialog.getSaveFileName(self, "Exporter", "sollicitations_2d.png", "PNG (*.png)")
        if ch:
            self.figure_sol.savefig(ch, dpi=200, bbox_inches="tight")
            self.statusBar().showMessage(f"Export 2D : {ch}")

    def _exporter_sol_3d(self):
        ch, _ = QFileDialog.getSaveFileName(self, "Exporter", "sollicitations_3d.png", "PNG (*.png)")
        if ch:
            self.figure_sol_3d.savefig(ch, dpi=200, bbox_inches="tight")
            self.statusBar().showMessage(f"Export 3D : {ch}")

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    #  EFFORT TRANCHANT
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    def _calculer_effort_tranchant(self):
        """Lance le calcul d'effort tranchant."""
        try:
            geo = self._lire_geometrie()
            mat = self._lire_materiaux()
            fer = self._lire_ferraillage()
            Ved = kN_to_N(self.txt_Ved.value())
            As = fer.As_reelle_mm2
            if As <= 0 and self.resultats is not None and self.resultats.elu.calcul_valide:
                As = self.resultats.elu.As_requise

            res_et = calculer_effort_tranchant(
                Ved=Ved,
                geometrie=geo,
                materiaux=mat,
                As_mm2=As,
                diam_etrier=self.txt_et_diam.value(),
                nb_branches=self.spn_nb_branches.value(),
                espacement_etriers=self.txt_esp_etriers.value(),
                theta=self.txt_theta.value(),
            )

            if self.resultats is None:
                self.resultats = ResultatsComplets()
            self.resultats.effort_tranchant = res_et

            self._afficher_resultats_effort_tranchant()
            self.statusBar().showMessage("Effort tranchant calculé.")
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"{e}\n\n{traceback.format_exc()}")

    def _afficher_resultats_effort_tranchant(self):
        """Affiche les résultats de l'effort tranchant."""
        if self.resultats is None or self.resultats.effort_tranchant is None:
            return
        et = self.resultats.effort_tranchant
        tm = TM(); p = tm.p
        html = ""

        # Métriques header
        html += '<table cellspacing="8" style="width:100%;"><tr>'
        html += f'<td>{tm.metric_html("Ved", f"{et.Ved/1000:.1f}", "kN")}</td>'
        html += f'<td>{tm.metric_html("VRd,c", f"{et.VRdc/1000:.1f}", "kN")}</td>'
        if et.besoin_armatures:
            html += f'<td>{tm.metric_html("VRd,s", f"{et.VRds/1000:.1f}", "kN")}</td>'
        html += f'<td>{tm.metric_html("VRd,max", f"{et.VRd_max/1000:.1f}", "kN")}</td>'
        verdict_c = p.ok if et.verdict == "Vérifié" else p.err
        html += f'<td>{tm.metric_html("Verdict", et.verdict, "", verdict_c)}</td>'
        html += '</tr></table>'

        # Besoin d'armatures
        if et.besoin_armatures:
            html += tm.carte("Armatures transversales nécessaires",
                f"V<sub>Ed</sub> = {et.Ved/1000:.1f} kN > V<sub>Rd,c</sub> = {et.VRdc/1000:.1f} kN", p.warn)
        else:
            html += tm.carte("Pas d'armatures par calcul",
                f"V<sub>Ed</sub> = {et.Ved/1000:.1f} kN ≤ V<sub>Rd,c</sub> = {et.VRdc/1000:.1f} kN<br>"
                "Dispositions minimales à respecter.", p.ok)

        # Détails
        contenu = (
            f"<table cellpadding='6' style='width:100%; border-collapse:collapse;'>"
            f"<tr><td><b>Asw/s requis</b></td><td>{et.Asw_s_requis:.3f} mm²/mm</td></tr>"
            f"<tr><td><b>Asw/s réel</b></td><td>{et.Asw_s_reel:.3f} mm²/mm</td>"
            f"<td>{'✓' if et.controle_section else '❌'}</td></tr>"
            f"<tr><td><b>Espacement réel</b></td><td>{et.espacement_reel:.0f} mm</td></tr>"
            f"<tr><td><b>Espacement max</b></td><td>{et.espacement_max:.0f} mm</td>"
            f"<td>{'✓' if et.controle_espacement else '❌'}</td></tr>"
            f"</table>"
        )
        html += tm.carte_light("Détails du calcul", contenu)

        # Messages
        txt = ""
        for m in et.messages:
            txt += f"• {m}<br>"
        html += tm.carte_light("Détail des contrôles", txt)

        # Verdict
        if et.verdict == "Vérifié":
            html += tm.carte(f"Verdict {tm.badge_ok()}", "Effort tranchant vérifié.", p.ok)
        else:
            html += tm.carte(f"Verdict {tm.badge_ko()}", "Effort tranchant non vérifié.", p.err)

        self.txt_resultats_et.setHtml(html)

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    #  AFFICHAGE DES RÉSULTATS
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    def _afficher_resultats_elu(self):
        if self.resultats is None:
            return
        elu = self.resultats.elu
        tm = TM()
        p = tm.p
        html = ""

        if elu.erreurs:
            for err in elu.erreurs:
                html += tm.carte("❌ Erreur", err, p.err)
            self.txt_resultats_elu.setHtml(html)
            return

        # ── Métriques header ──
        Mu_MNm = self.txt_mu_max.value()
        html += '<table cellspacing="8" style="width:100%;"><tr>'
        html += f'<td>{tm.metric_html("Mu,max", f"{Mu_MNm:.4f}", "MN·m")}</td>'
        if elu.decision:
            MTu_MNm = elu.decision.MTu / 1e9
            html += f'<td>{tm.metric_html("MTu", f"{MTu_MNm:.4f}", "MN·m")}</td>'
        html += f'<td>{tm.metric_html("As requise", f"{elu.As_requise/100:.2f}", "cm²", p.ok)}</td>'
        html += f'<td>{tm.metric_html("μcu", f"{elu.mu_cu:.4f}", "")}</td>'
        html += f'<td>{tm.metric_html("Pivot", elu.pivot.pivot, "")}</td>'
        html += '</tr></table>'

        # ── Décision ──
        if elu.decision is not None:
            dec = elu.decision
            Mu = dec.MEd_max / 1e9
            MTu = dec.MTu / 1e9
            if dec.decision == DecisionSection.RECTANGULAIRE_BW_NEGATIF:
                lbl = "RECTANGULAIRE (bw) — Moment négatif"
                coul = p.warn
                comp = "Moment négatif → calcul en section rectangulaire de largeur bw"
            elif dec.decision == DecisionSection.RECTANGULAIRE_EQUIVALENTE_BEFF:
                lbl = "RECTANGULAIRE ÉQUIVALENTE (beff)"
                coul = p.ok
                comp = (f"Mu,max = {Mu:.4f} MN·m ≤ MTu = {MTu:.4f} MN·m<br>"
                        "→ Section rectangulaire équivalente de largeur beff")
            else:
                lbl = "SECTION EN T (décomposition)"
                coul = p.warn
                comp = (f"Mu,max = {Mu:.4f} MN·m > MTu = {MTu:.4f} MN·m<br>"
                        "→ La section doit être calculée en vraie section en T")

            contenu = (
                f"<table cellpadding='6' style='width:100%;border-collapse:collapse;'>"
                f"<tr><td><b>Mu,max (saisi)</b></td><td><b>{Mu:.4f} MN·m</b></td></tr>"
                f"<tr><td><b>MTu (calculé)</b></td><td><b>{MTu:.4f} MN·m</b></td></tr>"
                f"<tr><td><b>Signe</b></td><td>{dec.moment_sign.capitalize()}</td></tr>"
                f"<tr><td><b>Comparaison</b></td><td>{comp}</td></tr>"
                f"<tr><td><b>Largeur de calcul</b></td>"
                f"<td>{mm_to_cm(dec.design_width):.1f} cm</td></tr>"
                f"<tr style='background:{coul};color:white;'>"
                f"<td colspan='2' style='text-align:center;font-size:14px;'>"
                f"<b>DÉCISION : {lbl}</b></td></tr></table>"
            )
            html += tm.carte("📐 Décision du type de section", contenu, coul)

        # Type retenu
        html += tm.carte_light("Type de section retenu", elu.commentaire_section)

        # Paramètres
        html += tm.carte_light("Paramètres",
            f"f<sub>cd</sub> = {elu.fcd:.2f} MPa &nbsp;|&nbsp; "
            f"f<sub>cu</sub> = {elu.fcu:.2f} MPa<br>"
            f"b = {mm_to_cm(elu.b_calcul):.1f} cm &nbsp;|&nbsp; "
            f"d = {mm_to_cm(elu.d_calcul):.1f} cm"
        )

        # Moment réduit
        c_mu = p.ok if elu.mu_cu <= elu.mu_ulim else p.warn
        txt_mu = ("μcu ≤ μulim → Pas d'aciers comprimés" if not elu.necessite_aciers_comprimes
                  else "μcu > μulim → Aciers comprimés nécessaires")
        html += tm.carte_light("Moment réduit",
            f"μ<sub>cu</sub> = {elu.mu_cu:.4f} &nbsp;|&nbsp; "
            f"μ<sub>ulim</sub> = {elu.mu_ulim:.4f}<br>{txt_mu}", c_mu)

        # Axe neutre
        html += tm.carte_light("Position de l'axe neutre",
            f"α<sub>u</sub> = {elu.alpha_u:.4f}<br>"
            f"x<sub>u</sub> = {mm_to_cm(elu.x_u):.2f} cm<br>"
            f"Z<sub>c</sub> = {mm_to_cm(elu.Zc):.2f} cm")

        # Pivot
        html += tm.carte_light("Pivot",
            f"Pivot <b>{elu.pivot.pivot}</b><br>"
            f"ε<sub>s1</sub> = {elu.pivot.epsilon_s1*1000:.2f} ‰ &nbsp;|&nbsp; "
            f"σ<sub>s1</sub> = {elu.pivot.sigma_s1:.1f} MPa<br>"
            f"{elu.pivot.commentaire}")

        # Section T
        if elu.MTu > 0:
            c = f"M<sub>Tu</sub> = {Nmm_to_MNm(elu.MTu):.4f} MN·m<br>"
            if elu.MEd1 > 0:
                c += (f"M<sub>Ed1</sub> (âme) = {Nmm_to_MNm(elu.MEd1):.4f} MN·m<br>"
                      f"M<sub>Ed2</sub> (table) = {Nmm_to_MNm(elu.MEd2):.4f} MN·m<br>"
                      f"A<sub>s1</sub> = {elu.As1/100:.2f} cm² &nbsp;|&nbsp; "
                      f"A<sub>s2</sub> = {elu.As2/100:.2f} cm²")
            html += tm.carte_light("Section en T — Décomposition", c)

        if elu.necessite_aciers_comprimes:
            html += tm.carte("⚠ Aciers comprimés", elu.commentaire_compression, p.warn)

        html += tm.carte("Section d'acier requise",
            f"<b>A<sub>s,requise</sub> = {elu.As_requise/100:.2f} cm² "
            f"({elu.As_requise:.0f} mm²)</b><br>"
            f"A<sub>s,min</sub> = {elu.As_min/100:.2f} cm²", p.ok)

        for av in elu.avertissements:
            html += tm.carte("⚠ Avertissement", av, p.warn)

        self.txt_resultats_elu.setHtml(html)

    def _afficher_resultats_ferraillage(self):
        if self.resultats is None or self.resultats.verification is None:
            return
        v = self.resultats.verification
        tm = TM(); p = tm.p
        html = ""

        # Métriques header
        html += '<table cellspacing="8" style="width:100%;"><tr>'
        html += f'<td>{tm.metric_html("As requise", f"{v.As_requise_mm2/100:.2f}", "cm²")}</td>'
        html += f'<td>{tm.metric_html("As réelle", f"{v.As_reelle_mm2/100:.2f}", "cm²", p.ok if v.controle_section else p.err)}</td>'
        html += f'<td>{tm.metric_html("Écart", f"{v.taux_pourcentage:+.1f}%", "")}</td>'
        html += f'<td>{tm.metric_html("d réel", f"{mm_to_cm(v.d_reel):.2f}", "cm")}</td>'
        verdict_c = p.ok if v.verdict_global else p.err
        verdict_t = "VÉRIFIÉ" if v.verdict_global else "NON VÉRIFIÉ"
        html += f'<td>{tm.metric_html("Verdict", verdict_t, "", verdict_c)}</td>'
        html += '</tr></table>'

        # Détails lits
        if v.details_lits:
            tab = ("<table cellpadding='6' cellspacing='0' style='width:100%;"
                   "border-collapse:collapse;'>"
                   f"<tr style='background:{p.ac};color:white;'>"
                   "<th>Lit</th><th>Nb</th><th>Ø</th>"
                   "<th>As unit.</th><th>As tot.</th><th>cm²</th>"
                   "<th>Dist. bord</th><th>d<sub>i</sub></th></tr>")
            for d in v.details_lits:
                tab += (f"<tr><td>{d['lit_numero']}</td>"
                        f"<td>{d['nombre_barres']}</td>"
                        f"<td>HA{d['diametre_mm']:.0f}</td>"
                        f"<td>{d['section_unitaire_mm2']:.1f}</td>"
                        f"<td>{d['section_totale_mm2']:.1f}</td>"
                        f"<td>{d['section_totale_cm2']:.2f}</td>"
                        f"<td>{d['distance_bord_tendu_mm']:.1f}</td>"
                        f"<td>{d['d_i_mm']:.1f}</td></tr>")
            tab += "</table>"
            html += tm.carte_light("Détail des lits", tab)

        # Contrôles
        bs = tm.badge_ok() if v.controle_section else tm.badge_ko()
        html += tm.carte_light(f"Contrôle de section {bs}", v.message_section,
                               p.ok if v.controle_section else p.err)
        bb = tm.badge_ok() if v.controle_bras_levier else tm.badge_ko()
        html += tm.carte_light(f"Bras de levier {bb}", v.message_bras_levier,
                               p.ok if v.controle_bras_levier else p.err)
        bv = tm.badge_ok() if v.verdict_global else tm.badge_ko()
        html += tm.carte(f"Verdict {bv}", v.message_verdict,
                         p.ok if v.verdict_global else p.err)

        # Constructif
        if self.resultats.constructif:
            c = self.resultats.constructif
            txt = ""
            for m in c.messages:
                ic = "✓" if m["type"] == "ok" else ("❌" if m["type"] == "erreur" else "⚠")
                txt += f"{ic} {m['message']}<br>"
            html += tm.carte_light("Dispositions constructives", txt,
                                   p.ok if c.verifie else p.err)

        self.txt_resultats_ferraillage.setHtml(html)

    def _afficher_resultats_fissuration(self):
        if self.resultats is None or self.resultats.fissuration is None:
            return
        f = self.resultats.fissuration
        tm = TM(); p = tm.p
        html = ""

        # Métriques header
        html += '<table cellspacing="8" style="width:100%;"><tr>'
        html += f'<td>{tm.metric_html("Mser", f"{self.txt_mser.value():.4f}", "MN·m")}</td>'
        html += f'<td>{tm.metric_html("Mcr", f"{Nmm_to_kNm(f.Mcr):.2f}", "kN·m")}</td>'
        etat = "Fissurée" if f.section_fissuree else "Non fissurée"
        etat_c = p.warn if f.section_fissuree else p.ok
        html += f'<td>{tm.metric_html("État", etat, "", etat_c)}</td>'
        html += f'<td>{tm.metric_html("σ_c", f"{f.sigma_c_service:.1f}", "MPa")}</td>'
        html += f'<td>{tm.metric_html("σ_s", f"{f.sigma_s_service:.1f}", "MPa")}</td>'
        html += '</tr></table>'

        # Carte Mser
        sol = self._lire_sollicitations()
        html += tm.carte_light("Moment de service",
            f"M<sub>ser</sub> = {Nmm_to_kNm(sol.M_ser):.2f} kN·m = {Nmm_to_MNm(sol.M_ser):.4f} MN·m")

        # Carte Mcr
        html += tm.carte_light("Moment de fissuration",
            f"M<sub>cr</sub> = {Nmm_to_kNm(f.Mcr):.2f} kN·m")

        # Carte État de la section
        if f.section_fissuree:
            html += tm.carte("État de la section",
                f"M<sub>ser</sub> > M<sub>cr</sub> → <b>Section fissurée</b>", p.warn)
        else:
            html += tm.carte("État de la section",
                f"M<sub>ser</sub> ≤ M<sub>cr</sub> → <b>Section non fissurée</b>", p.ok)

        # Carte Contraintes en service
        contenu_stress = (
            f"<table cellpadding='6' style='width:100%; border-collapse:collapse;'>"
            f"<tr><td><b>σ<sub>c</sub></b></td><td>{f.sigma_c_service:.2f} MPa</td>"
            f"<td>Limite : {f.sigma_c_lim:.1f} MPa</td>"
            f"<td>{'✓ OK' if f.controle_sigma_c else '❌ NON VÉRIFIÉ'}</td></tr>"
            f"<tr><td><b>σ<sub>s</sub></b></td><td>{f.sigma_s_service:.2f} MPa</td>"
            f"<td>Limite : {f.sigma_s_lim:.1f} MPa</td>"
            f"<td>{'✓ OK' if f.controle_sigma_s else '❌ NON VÉRIFIÉ'}</td></tr>"
        )
        if f.section_fissuree:
            contenu_stress += (
                f"<tr><td><b>Axe neutre</b></td><td colspan='3'>x = {f.x_ser:.1f} mm</td></tr>"
            )
        contenu_stress += "</table>"
        stress_color = p.ok if (f.controle_sigma_c and f.controle_sigma_s) else p.err
        html += tm.carte_light("Contraintes en service", contenu_stress, stress_color)

        # Carte Section minimale
        contenu_as = (
            f"A<sub>s,min</sub> = {f.As_min_mm2/100:.2f} cm²<br>"
            f"A<sub>s,réelle</sub> = {f.As_reelle_mm2/100:.2f} cm²<br>"
        )
        if f.controle_As_min:
            contenu_as += f"✓ A<sub>s,réelle</sub> ≥ A<sub>s,min</sub>"
        else:
            contenu_as += f"❌ A<sub>s,réelle</sub> < A<sub>s,min</sub>"
        asmin_color = p.ok if f.controle_As_min else p.err
        html += tm.carte_light("Section minimale", contenu_as, asmin_color)

        # Carte Vérification fissuration (simplifiée)
        if f.section_fissuree:
            contenu_fiss = "<table cellpadding='4' style='width:100%; border-collapse:collapse;'>"
            contenu_fiss += (
                f"<tr><td><b>Diamètre proposé</b></td><td>HA{f.diam_propose:.0f}</td>"
                f"<td><b>Max admissible</b></td>"
                f"<td>{('HA' + str(int(f.diametre_max_admissible))) if f.diametre_max_admissible else 'N/A'}</td>"
                f"<td>{'✓' if f.controle_diametre else '❌'}</td></tr>"
            )
            contenu_fiss += (
                f"<tr><td><b>Espacement proposé</b></td><td>{f.espacement_propose:.0f} mm</td>"
                f"<td><b>Max admissible</b></td>"
                f"<td>{f.espacement_max_admissible:.0f} mm</td>"
                f"<td>{'✓' if f.controle_espacement else '❌'}</td></tr>"
            ) if f.espacement_max_admissible else ""
            contenu_fiss += "</table>"
            fiss_color = p.ok if (f.controle_diametre and f.controle_espacement) else p.err
            html += tm.carte_light("Vérification fissuration (simplifiée)", contenu_fiss, fiss_color)

        # Détail des contrôles
        if f.wmax_recommande is not None:
            html += tm.carte_light("Ouverture de fissure admissible",
                                   f"w<sub>max</sub> = {f.wmax_recommande:.2f} mm")

        txt_msg = ""
        for m in f.messages:
            txt_msg += f"• {m}<br>"
        html += tm.carte_light("Détail des contrôles", txt_msg)

        # Verdict global
        if f.verdict == "Vérifié":
            html += tm.carte(f"Verdict global {tm.badge_ok()}",
                f"<b>Fissuration maîtrisée</b><br>"
                f"{'Section non fissurée' if not f.section_fissuree else 'Section fissurée — contrôles satisfaits'}", p.ok)
        elif f.verdict == "Non vérifié":
            html += tm.carte(f"Verdict global {tm.badge_ko()}",
                "<b>Fissuration non maîtrisée</b>", p.err)
        else:
            html += tm.carte(f"Verdict {tm.badge_warn()}", f.verdict, p.warn)

        self.txt_resultats_fissuration.setHtml(html)

    def _afficher_propositions(self, solutions):
        tm = TM(); p = tm.p
        html = ""
        if not solutions:
            html += tm.carte("Info", "Aucune solution trouvée.", p.warn)
            self.txt_propositions.setHtml(html)
            return
        tab = (f"<table cellpadding='6' cellspacing='0' style='width:100%;"
               f"border-collapse:collapse;'>"
               f"<tr style='background:{p.ac};color:white;'>"
               "<th>#</th><th>Solution</th><th>As (cm²)</th><th>Écart</th>"
               "<th>Lits</th><th>Faisable</th><th>Score</th></tr>")
        for i, s in enumerate(solutions[:15], 1):
            ok = "✓" if s.faisable else "✗"
            bg = "" if s.faisable else f" style='background:{p.err_bg};'"
            tab += (f"<tr{bg}><td>{i}</td><td><b>{s.description}</b></td>"
                    f"<td>{s.As_totale_cm2:.2f}</td><td>{s.ecart_pourcent:+.1f}%</td>"
                    f"<td>{s.nb_lits}</td><td>{ok}</td><td>{s.score:.1f}</td></tr>")
        tab += "</table>"
        html += tab
        self.txt_propositions.setHtml(html)

    def _afficher_apercu_rapport(self):
        if self.resultats is None:
            return
        tm = TM(); p = tm.p
        geo = self._lire_geometrie()
        mat = self._lire_materiaux()
        elu = self.resultats.elu
        html = "<p>Cliquez sur « Générer le rapport PDF » pour le document complet.</p>"
        html += tm.carte_light("Données d'entrée",
            f"Type : {geo.type_section.value}<br>"
            f"bw = {mm_to_cm(geo.b_w):.1f} cm &nbsp;|&nbsp; h = {mm_to_cm(geo.h):.1f} cm<br>"
            f"d = {mm_to_cm(geo.hauteur_utile_effective()):.1f} cm<br>"
            f"fck = {mat.beton.fck:.0f} MPa &nbsp;|&nbsp; fyk = {mat.acier.fyk:.0f} MPa<br>"
            f"Mu,max = {self.txt_mu_max.value():.4f} MN·m")

        if elu.calcul_valide:
            html += tm.carte_light("Résultat principal",
                f"As,requise = <b>{elu.As_requise/100:.2f} cm²</b><br>"
                f"μcu = {elu.mu_cu:.4f} &nbsp;|&nbsp; α_u = {elu.alpha_u:.4f}<br>"
                f"Zc = {elu.Zc:.1f} mm &nbsp;|&nbsp; Pivot {elu.pivot.pivot}")

        if self.resultats.verification:
            vr = self.resultats.verification
            verdict = "VÉRIFIÉ" if vr.verdict_global else "NON VÉRIFIÉ"
            html += tm.carte("Verdict ferraillage",
                f"As,réelle = {vr.As_reelle_mm2/100:.2f} cm² &nbsp;|&nbsp; "
                f"d_réel = {vr.d_reel:.1f} mm<br><b>{verdict}</b>",
                p.ok if vr.verdict_global else p.err)

        # Fissuration
        if self.resultats.fissuration:
            f = self.resultats.fissuration
            html += tm.carte("Verdict fissuration",
                f"État : {'fissurée' if f.section_fissuree else 'non fissurée'}<br>"
                f"σ_c = {f.sigma_c_service:.1f} MPa | σ_s = {f.sigma_s_service:.1f} MPa<br>"
                f"<b>{f.verdict}</b>",
                p.ok if f.verdict == "Vérifié" else p.err)

        # Effort tranchant
        if self.resultats.effort_tranchant:
            et = self.resultats.effort_tranchant
            html += tm.carte("Verdict effort tranchant",
                f"Ved = {et.Ved/1000:.1f} kN<br>"
                f"VRd,c = {et.VRdc/1000:.1f} kN<br>"
                f"<b>{et.verdict}</b>",
                p.ok if et.verdict == "Vérifié" else p.err)

        # Conclusion synthétique
        html += '<div style="margin-top:16px; padding:16px; border:2px solid ' + p.ac + '; border-radius:10px;">'
        html += f'<h3 style="color:{p.ac};">Conclusion synthétique</h3>'
        html += f'<p>ELU flexion : <b>{"VÉRIFIÉ" if elu.calcul_valide else "NON VÉRIFIÉ"}</b></p>'
        if self.resultats.fissuration:
            html += f'<p>ELS fissuration : <b>{self.resultats.fissuration.verdict}</b></p>'
        if self.resultats.effort_tranchant:
            html += f'<p>Effort tranchant : <b>{self.resultats.effort_tranchant.verdict}</b></p>'
        html += '</div>'

        self.txt_rapport_apercu.setHtml(html)

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    #  VISUALISATIONS
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    def _generer_vue_2d(self):
        try:
            if self.resultats is None:
                self._lancer_calcul()
            if self.resultats is None:
                return
            from app.visualization.section_plot_2d import dessiner_section_2d
            self.figure_2d.clear()
            dessiner_section_2d(self.figure_2d, self._lire_geometrie(), self._lire_ferraillage())
            self.canvas_2d.draw()
            self.statusBar().showMessage("Vue 2D générée.")
        except Exception as e:
            QMessageBox.critical(self, "Erreur", str(e))

    def _exporter_vue_2d(self):
        ch, _ = QFileDialog.getSaveFileName(self, "Exporter", "section_2d.png", "PNG (*.png)")
        if ch:
            self.figure_2d.savefig(ch, dpi=200, bbox_inches="tight")
            self.statusBar().showMessage(f"Vue 2D exportée : {ch}")

    def _generer_vue_3d(self):
        try:
            if self.resultats is None:
                self._lancer_calcul()
            if self.resultats is None:
                return
            from app.visualization.section_view_3d import creer_vue_3d
            w3d = creer_vue_3d(self._lire_geometrie(), self._lire_ferraillage())
            if self.lbl_3d_placeholder:
                self.lbl_3d_placeholder.setParent(None)
                self.lbl_3d_placeholder = None
            while self.widget_3d_container.count():
                it = self.widget_3d_container.takeAt(0)
                if it.widget():
                    it.widget().setParent(None)
            self.widget_3d_container.addWidget(w3d)
            self.statusBar().showMessage("Vue 3D générée.")
        except Exception as e:
            QMessageBox.critical(self, "Erreur",
                                 f"{e}\n\n{traceback.format_exc()}")

    def _generer_rapport(self):
        if self.resultats is None:
            QMessageBox.warning(self, "Attention", "Lancez d'abord un calcul.")
            return
        ch, _ = QFileDialog.getSaveFileName(
            self, "Rapport PDF", "rapport_flexion.pdf", "PDF (*.pdf)"
        )
        if not ch:
            return
        try:
            img_path = None
            try:
                import tempfile
                tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
                tmp.close()
                self._generer_vue_2d()
                self.figure_2d.savefig(tmp.name, dpi=150, bbox_inches="tight")
                img_path = tmp.name
            except Exception:
                pass
            generer_rapport(ch, self._lire_geometrie(), self._lire_materiaux(),
                            self._lire_sollicitations(), self._lire_ferraillage(),
                            self._lire_environnement(), self.resultats,
                            image_2d_path=img_path)
            self.statusBar().showMessage(f"Rapport PDF généré : {ch}")
            QMessageBox.information(self, "Rapport", f"Rapport généré :\n{ch}")
            if img_path and os.path.exists(img_path):
                os.unlink(img_path)
        except Exception as e:
            QMessageBox.critical(self, "Erreur", str(e))
