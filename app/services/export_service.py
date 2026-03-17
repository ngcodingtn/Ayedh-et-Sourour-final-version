"""Service d'export – export des résultats."""
from __future__ import annotations

import json
from pathlib import Path


def exporter_resultats_json(
    chemin: str | Path,
    resultats: dict,
) -> None:
    """Exporte les résultats de calcul en JSON."""
    chemin = Path(chemin)
    chemin.parent.mkdir(parents=True, exist_ok=True)
    with open(chemin, "w", encoding="utf-8") as f:
        json.dump(resultats, f, ensure_ascii=False, indent=4, default=str)
