"""Styles et thème visuel de l'application.

Ce module délègue au ThemeManager centralisé (theme.py).
Il conserve les anciens noms exportés pour rétro-compatibilité.
"""
from __future__ import annotations

from app.ui.theme import ThemeManager

# ── Couleurs rétro-compatibles (lues dynamiquement) ──
COULEUR_PRIMAIRE = "#2B6CB0"
COULEUR_SECONDAIRE = "#2C5282"
COULEUR_ACCENT = "#63B3ED"
COULEUR_SUCCES = "#276749"
COULEUR_ERREUR = "#C53030"
COULEUR_AVERTISSEMENT = "#C05621"
COULEUR_FOND = "#F0F2F5"
COULEUR_CARTE = "#FFFFFF"
COULEUR_TEXTE = "#1A202C"
COULEUR_TEXTE_SECONDAIRE = "#4A5568"
COULEUR_BORDURE = "#E2E8F0"

# Le QSS est désormais géré par ThemeManager.qss()
STYLESHEET = ""


def badge_html(texte: str, couleur: str) -> str:
    return ThemeManager.get().badge_html(texte, couleur)

def badge_ok() -> str:
    return ThemeManager.get().badge_ok()

def badge_ko() -> str:
    return ThemeManager.get().badge_ko()

def badge_attention() -> str:
    return ThemeManager.get().badge_warn()

def carte_html(titre: str, contenu: str, couleur_titre: str = COULEUR_PRIMAIRE) -> str:
    return ThemeManager.get().carte(titre, contenu, couleur_titre)
