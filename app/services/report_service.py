"""Service de rapport – délègue à pdf_report."""
from __future__ import annotations

from pathlib import Path

from app.models.section_models import DonneesGeometrie
from app.models.material_models import DonneesMateriaux
from app.models.load_models import DonneesSollicitations
from app.models.reinforcement_models import DonneesFerraillage, DonneesEnvironnement
from app.models.result_models import ResultatsComplets


def generer_rapport(
    chemin: str | Path,
    geometrie: DonneesGeometrie,
    materiaux: DonneesMateriaux,
    sollicitations: DonneesSollicitations,
    ferraillage: DonneesFerraillage,
    environnement: DonneesEnvironnement,
    resultats: ResultatsComplets,
    image_2d_path: str | None = None,
    image_3d_path: str | None = None,
) -> None:
    """Génère un rapport PDF complet."""
    from app.reports.pdf_report import generer_pdf
    generer_pdf(
        chemin, geometrie, materiaux, sollicitations,
        ferraillage, environnement, resultats,
        image_2d_path, image_3d_path,
    )
