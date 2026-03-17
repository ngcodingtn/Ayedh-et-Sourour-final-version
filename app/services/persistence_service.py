"""Service de persistance – sauvegarde et chargement JSON."""
from __future__ import annotations

import json
from pathlib import Path

from app.models.section_models import DonneesGeometrie
from app.models.material_models import DonneesMateriaux
from app.models.load_models import DonneesSollicitations
from app.models.reinforcement_models import DonneesFerraillage, DonneesEnvironnement
from app.config import DEFAULT_JSON_INDENT


def sauvegarder_projet(
    chemin: str | Path,
    geometrie: DonneesGeometrie,
    materiaux: DonneesMateriaux,
    sollicitations: DonneesSollicitations,
    ferraillage: DonneesFerraillage,
    environnement: DonneesEnvironnement,
) -> None:
    """Sauvegarde toutes les données du projet en JSON."""
    data = {
        "version": "1.0",
        "geometrie": geometrie.to_dict(),
        "materiaux": materiaux.to_dict(),
        "sollicitations": sollicitations.to_dict(),
        "ferraillage": ferraillage.to_dict(),
        "environnement": environnement.to_dict(),
    }
    chemin = Path(chemin)
    chemin.parent.mkdir(parents=True, exist_ok=True)
    with open(chemin, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=DEFAULT_JSON_INDENT)


def charger_projet(chemin: str | Path) -> dict:
    """Charge un projet depuis un fichier JSON.

    Returns:
        Dictionnaire avec les clés : geometrie, materiaux, sollicitations,
        ferraillage, environnement.
    """
    chemin = Path(chemin)
    with open(chemin, "r", encoding="utf-8") as f:
        data = json.load(f)

    return {
        "geometrie": DonneesGeometrie.from_dict(data["geometrie"]),
        "materiaux": DonneesMateriaux.from_dict(data["materiaux"]),
        "sollicitations": DonneesSollicitations.from_dict(data["sollicitations"]),
        "ferraillage": DonneesFerraillage.from_dict(data.get("ferraillage", {})),
        "environnement": DonneesEnvironnement.from_dict(data.get("environnement", {})),
    }


def generer_exemple_json(chemin: str | Path) -> None:
    """Génère un fichier JSON d'exemple."""
    from app.core.examples import exemple_rectangulaire
    ex = exemple_rectangulaire()
    sauvegarder_projet(
        chemin,
        ex["geometrie"],
        ex["materiaux"],
        ex["sollicitations"],
        ex["ferraillage"],
        ex["environnement"],
    )
