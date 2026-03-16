"""Configuration globale de l'application."""
from __future__ import annotations

APP_NAME = "FlexiBeam – Dimensionnement Flexion Simple EC2"
APP_VERSION = "1.0.0"
APP_AUTHOR = "Ingénierie Structurelle"
APP_DESCRIPTION = (
    "Application de dimensionnement et de vérification en flexion simple "
    "d'une poutre en béton armé selon l'Eurocode 2."
)

# Unités internes de calcul
# Longueurs : mm
# Contraintes : MPa (N/mm²)
# Moments : N·mm
# Sections acier : mm²

# Unités d'affichage
# Moments : kN·m
# Longueurs : mm (petites) / m (grandes)
# Sections acier : cm²
# Contraintes : MPa

DEFAULT_JSON_INDENT = 4
REPORT_TITLE = "Rapport de dimensionnement en flexion simple"
REPORT_SUBTITLE = "Béton armé – Eurocode 2"
