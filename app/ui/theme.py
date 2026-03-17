"""Système de thème centralisé pour FlexiBeam — light / dark mode.

Fournit :
  - Deux palettes (PALETTE_LIGHT, PALETTE_DARK)
  - ThemeManager : singleton, toggle, génération QSS
  - Fonctions utilitaires HTML (badge, carte) sensibles au thème
"""
from __future__ import annotations

from dataclasses import dataclass


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  Palette
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
@dataclass(frozen=True)
class Palette:
    name: str
    # Fonds
    bg: str; bg2: str; card: str; inp: str
    sidebar: str; topbar: str; hover: str
    # Textes
    tx: str; tx2: str; txm: str; tx_on: str
    tx_sb: str; tx_sb_a: str
    # Accent
    ac: str; ac_h: str; ac_l: str
    # Sémantique
    ok: str; ok_bg: str
    warn: str; warn_bg: str
    err: str; err_bg: str
    info: str; info_bg: str
    # Bordures
    brd: str; brd_l: str; shadow: str
    # Sidebar
    sb_a_bg: str; sb_h_bg: str; sb_a_brd: str


PALETTE_LIGHT = Palette(
    name="light",
    bg="#F0F2F5", bg2="#FAFBFC", card="#FFFFFF", inp="#FFFFFF",
    sidebar="#1B2838", topbar="#FFFFFF", hover="#F7FAFC",
    tx="#1A202C", tx2="#4A5568", txm="#A0AEC0", tx_on="#FFFFFF",
    tx_sb="#94A3B8", tx_sb_a="#FFFFFF",
    ac="#2B6CB0", ac_h="#2C5282", ac_l="#EBF8FF",
    ok="#276749", ok_bg="#F0FFF4",
    warn="#C05621", warn_bg="#FFFAF0",
    err="#C53030", err_bg="#FFF5F5",
    info="#2B6CB0", info_bg="#EBF8FF",
    brd="#E2E8F0", brd_l="#EDF2F7", shadow="rgba(0,0,0,0.06)",
    sb_a_bg="rgba(99,179,237,0.15)", sb_h_bg="rgba(255,255,255,0.06)",
    sb_a_brd="#63B3ED",
)

PALETTE_DARK = Palette(
    name="dark",
    bg="#0F1923", bg2="#172033", card="#1A2744", inp="#1E2D45",
    sidebar="#0A1220", topbar="#131D2E", hover="#1E2D45",
    tx="#E2E8F0", tx2="#A0AEC0", txm="#4A5568", tx_on="#FFFFFF",
    tx_sb="#64748B", tx_sb_a="#E2E8F0",
    ac="#63B3ED", ac_h="#4299E1", ac_l="rgba(99,179,237,0.12)",
    ok="#48BB78", ok_bg="rgba(72,187,120,0.12)",
    warn="#ED8936", warn_bg="rgba(237,137,54,0.12)",
    err="#FC8181", err_bg="rgba(252,129,129,0.12)",
    info="#63B3ED", info_bg="rgba(99,179,237,0.12)",
    brd="#2D3748", brd_l="#1A202C", shadow="rgba(0,0,0,0.25)",
    sb_a_bg="rgba(99,179,237,0.12)", sb_h_bg="rgba(255,255,255,0.04)",
    sb_a_brd="#63B3ED",
)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  ThemeManager (singleton)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
class ThemeManager:
    _inst: "ThemeManager | None" = None
    _pal: Palette = PALETTE_LIGHT
    _cbs: list = []

    @classmethod
    def get(cls) -> "ThemeManager":
        if cls._inst is None:
            cls._inst = cls()
        return cls._inst

    @property
    def p(self) -> Palette:
        return self._pal

    @property
    def is_dark(self) -> bool:
        return self._pal.name == "dark"

    def toggle(self):
        self._pal = PALETTE_DARK if not self.is_dark else PALETTE_LIGHT
        for cb in self._cbs:
            cb()

    def on_change(self, cb):
        self._cbs.append(cb)

    def apply(self, app):
        app.setStyleSheet(self.qss())

    # ── Génération QSS ──────────────────────────────
    def qss(self) -> str:
        p = self._pal
        return f"""
/* ═══ GLOBAL ═══ */
QMainWindow {{ background:{p.bg}; }}
QWidget {{ font-family:'Segoe UI','Inter',sans-serif; font-size:13px; color:{p.tx}; }}

/* ═══ TOP BAR ═══ */
#topbar {{ background:{p.topbar}; border-bottom:1px solid {p.brd}; min-height:54px; max-height:54px; }}
#topbar QLabel {{ color:{p.tx}; background:transparent; }}
#topbar_title {{ font-size:17px; font-weight:700; color:{p.ac}; }}
#topbar_sub {{ font-size:11px; color:{p.tx2}; }}
#topbar QPushButton {{
  background:transparent; color:{p.tx2}; border:1px solid {p.brd};
  border-radius:6px; padding:5px 13px; font-size:12px; min-height:28px;
}}
#topbar QPushButton:hover {{ background:{p.hover}; border-color:{p.ac}; color:{p.ac}; }}
#topbar QPushButton[accent="true"] {{
  background:{p.ac}; color:{p.tx_on}; border:none;
}}
#topbar QPushButton[accent="true"]:hover {{ background:{p.ac_h}; }}

/* ═══ SIDEBAR ═══ */
#sidebar {{ background:{p.sidebar}; min-width:210px; max-width:210px; }}
#sidebar QLabel {{ color:{p.tx_sb}; background:transparent; }}
#sb_logo {{ color:#E2E8F0; font-size:17px; font-weight:700; padding:18px 16px 2px 16px; }}
#sb_sub  {{ color:{p.tx_sb}; font-size:10px; padding:0 16px 14px 16px; }}
#sb_sect {{ color:{p.txm}; font-size:10px; font-weight:700; padding:14px 16px 4px 16px; }}

QPushButton[nav="true"] {{
  text-align:left; padding:10px 16px 10px 18px;
  border:none; border-left:3px solid transparent; border-radius:0;
  background:transparent; color:{p.tx_sb}; font-size:13px; min-height:36px;
}}
QPushButton[nav="true"]:hover {{ background:{p.sb_h_bg}; color:{p.tx_sb_a}; }}
QPushButton[nav="true"][active="true"] {{
  border-left:3px solid {p.sb_a_brd}; background:{p.sb_a_bg};
  color:{p.tx_sb_a}; font-weight:600;
}}

/* ═══ CARDS ═══ */
QFrame[card="true"] {{
  background:{p.card}; border:1px solid {p.brd}; border-radius:10px;
}}
QFrame[metric="true"] {{
  background:{p.card}; border:1px solid {p.brd}; border-radius:10px;
  min-width:150px;
}}

/* ═══ INPUTS ═══ */
QLineEdit, QSpinBox, QDoubleSpinBox {{
  padding:7px 12px; border:1px solid {p.brd}; border-radius:6px;
  background:{p.inp}; color:{p.tx}; min-height:26px;
}}
QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus {{ border:2px solid {p.ac}; padding:6px 11px; }}
QComboBox {{
  padding:7px 12px; border:1px solid {p.brd}; border-radius:6px;
  background:{p.inp}; color:{p.tx}; min-height:26px;
}}
QComboBox:focus {{ border:2px solid {p.ac}; }}
QComboBox::drop-down {{ border:none; width:24px; }}
QComboBox::down-arrow {{
  border-left:4px solid transparent; border-right:4px solid transparent;
  border-top:5px solid {p.tx2}; margin-right:8px;
}}
QComboBox QAbstractItemView {{
  background:{p.card}; color:{p.tx}; border:1px solid {p.brd};
  selection-background-color:{p.ac_l}; selection-color:{p.ac}; padding:4px;
}}

/* ═══ BUTTONS ═══ */
QPushButton {{
  background:{p.ac}; color:{p.tx_on}; border:none; border-radius:6px;
  padding:8px 18px; font-size:13px; font-weight:500; min-height:34px;
}}
QPushButton:hover {{ background:{p.ac_h}; }}
QPushButton:pressed {{ padding-top:9px; }}
QPushButton:disabled {{ background:{p.brd}; color:{p.txm}; }}
QPushButton[class="success"]       {{ background:{p.ok}; }}
QPushButton[class="success"]:hover {{ background:#22543D; }}
QPushButton[class="danger"]        {{ background:{p.err}; }}
QPushButton[class="danger"]:hover  {{ background:#9B2C2C; }}
QPushButton[class="warning"]       {{ background:{p.warn}; }}
QPushButton[class="secondary"] {{
  background:transparent; color:{p.tx2}; border:1px solid {p.brd};
}}
QPushButton[class="secondary"]:hover {{ background:{p.hover}; border-color:{p.ac}; color:{p.ac}; }}
QPushButton[class="ghost"] {{ background:transparent; color:{p.ac}; border:none; }}
QPushButton[class="ghost"]:hover {{ background:{p.ac_l}; }}

/* ═══ CHECKBOX ═══ */
QCheckBox {{ spacing:8px; color:{p.tx}; }}
QCheckBox::indicator {{ width:18px; height:18px; border:2px solid {p.brd}; border-radius:4px; background:{p.inp}; }}
QCheckBox::indicator:checked {{ background:{p.ac}; border-color:{p.ac}; }}
QCheckBox::indicator:hover {{ border-color:{p.ac}; }}

/* ═══ GROUPBOX ═══ */
QGroupBox {{
  font-weight:bold; font-size:13px; color:{p.ac}; border:1px solid {p.brd};
  border-radius:8px; margin-top:16px; padding:20px 16px 16px 16px; background:{p.card};
}}
QGroupBox::title {{ subcontrol-origin:margin; left:14px; padding:0 8px; }}

/* ═══ TABLES ═══ */
QTableWidget {{
  border:1px solid {p.brd}; border-radius:6px; background:{p.card};
  gridline-color:{p.brd_l}; alternate-background-color:{p.bg2};
}}
QTableWidget::item {{ padding:6px 10px; border:none; }}
QTableWidget::item:selected {{ background:{p.ac_l}; color:{p.ac}; }}
QHeaderView::section {{
  background:{p.ac}; color:{p.tx_on}; padding:8px 6px; border:none; font-weight:600;
}}

/* ═══ TEXT BROWSER ═══ */
QTextBrowser, QTextEdit {{
  border:1px solid {p.brd}; border-radius:6px; background:{p.card};
  color:{p.tx}; font-family:'Segoe UI',sans-serif; font-size:13px; padding:12px;
}}

/* ═══ SCROLLBAR ═══ */
QScrollBar:vertical {{ background:transparent; width:8px; }}
QScrollBar::handle:vertical {{ background:{p.brd}; border-radius:4px; min-height:30px; }}
QScrollBar::handle:vertical:hover {{ background:{p.txm}; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height:0; }}
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{ background:transparent; }}
QScrollBar:horizontal {{ background:transparent; height:8px; }}
QScrollBar::handle:horizontal {{ background:{p.brd}; border-radius:4px; min-width:30px; }}
QScrollBar::handle:horizontal:hover {{ background:{p.txm}; }}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ width:0; }}

QScrollArea {{ border:none; background:transparent; }}

/* ═══ STATUS BAR ═══ */
QStatusBar {{
  background:{p.sidebar}; color:{p.tx_sb}; font-size:12px;
  border-top:1px solid {p.brd_l}; min-height:26px;
}}

QToolTip {{
  background:{p.card}; color:{p.tx}; border:1px solid {p.brd};
  border-radius:4px; padding:6px 10px; font-size:12px;
}}
"""

    # ── Utilitaires HTML sensibles au thème ──
    def badge_html(self, texte: str, couleur: str) -> str:
        return (
            f'<span style="background:{couleur};color:{self.p.tx_on};'
            f'padding:3px 12px;border-radius:12px;font-weight:600;'
            f'font-size:12px;">{texte}</span>'
        )

    def badge_ok(self) -> str:
        return self.badge_html("VÉRIFIÉ", self.p.ok)

    def badge_ko(self) -> str:
        return self.badge_html("NON VÉRIFIÉ", self.p.err)

    def badge_warn(self) -> str:
        return self.badge_html("ATTENTION", self.p.warn)

    def carte(self, titre: str, contenu: str, couleur: str = "") -> str:
        p = self.p
        c = couleur or p.ac
        return (
            f'<div style="border:1px solid {p.brd};border-radius:10px;'
            f'margin:8px 0;padding:0;background:{p.card};overflow:hidden;">'
            f'<div style="background:{c};padding:10px 18px;'
            f'font-weight:700;color:{p.tx_on};font-size:14px;">{titre}</div>'
            f'<div style="padding:14px 18px;font-size:13px;color:{p.tx};'
            f'line-height:1.6;">{contenu}</div></div>'
        )

    def carte_light(self, titre: str, contenu: str, couleur: str = "") -> str:
        p = self.p
        c = couleur or p.ac
        return (
            f'<div style="border:1px solid {p.brd};border-left:4px solid {c};'
            f'border-radius:8px;margin:8px 0;padding:16px 18px;background:{p.card};">'
            f'<div style="font-weight:700;color:{c};font-size:14px;'
            f'margin-bottom:8px;">{titre}</div>'
            f'<div style="font-size:13px;color:{p.tx};line-height:1.6;">'
            f'{contenu}</div></div>'
        )

    def metric_html(self, label: str, value: str, unit: str = "",
                     couleur: str = "") -> str:
        p = self.p
        c = couleur or p.ac
        return (
            f'<div style="display:inline-block;background:{p.card};'
            f'border:1px solid {p.brd};border-radius:10px;padding:14px 20px;'
            f'margin:4px 8px 4px 0;min-width:130px;text-align:center;">'
            f'<div style="font-size:11px;color:{p.tx2};font-weight:600;'
            f'text-transform:uppercase;letter-spacing:0.5px;">{label}</div>'
            f'<div style="font-size:22px;font-weight:700;color:{c};'
            f'margin:4px 0;">{value}</div>'
            f'<div style="font-size:11px;color:{p.txm};">{unit}</div></div>'
        )
