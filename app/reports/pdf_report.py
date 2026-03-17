"""Génération de rapport PDF avec reportlab."""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    Image, PageBreak, HRFlowable,
)

from app.config import REPORT_TITLE, REPORT_SUBTITLE, APP_VERSION
from app.models.section_models import DonneesGeometrie
from app.models.material_models import DonneesMateriaux
from app.models.load_models import DonneesSollicitations
from app.models.reinforcement_models import DonneesFerraillage, DonneesEnvironnement
from app.models.result_models import ResultatsComplets
from app.core.units import Nmm_to_kNm, mm2_to_cm2

# Couleurs
BLEU = HexColor("#1565C0")
VERT = HexColor("#2E7D32")
ROUGE = HexColor("#C62828")
GRIS = HexColor("#757575")
GRIS_CLAIR = HexColor("#F5F5F5")


def generer_pdf(
    chemin: str | Path,
    geometrie: DonneesGeometrie,
    materiaux: DonneesMateriaux,
    sollicitations: DonneesSollicitations,
    ferraillage: DonneesFerraillage,
    environnement: DonneesEnvironnement,
    resultats: ResultatsComplets,
    image_2d_path: Optional[str] = None,
    image_3d_path: Optional[str] = None,
) -> None:
    """Génère le rapport PDF complet."""
    chemin = Path(chemin)
    doc = SimpleDocTemplate(
        str(chemin),
        pagesize=A4,
        leftMargin=20 * mm,
        rightMargin=20 * mm,
        topMargin=20 * mm,
        bottomMargin=20 * mm,
    )

    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        "Titre1",
        parent=styles["Heading1"],
        textColor=BLEU,
        fontSize=18,
        spaceAfter=12,
    ))
    styles.add(ParagraphStyle(
        "Titre2",
        parent=styles["Heading2"],
        textColor=BLEU,
        fontSize=14,
        spaceAfter=8,
        spaceBefore=12,
    ))
    styles.add(ParagraphStyle(
        "Normal_FR",
        parent=styles["Normal"],
        fontSize=10,
        leading=14,
        alignment=TA_JUSTIFY,
    ))
    styles.add(ParagraphStyle(
        "Centre",
        parent=styles["Normal"],
        alignment=TA_CENTER,
        fontSize=10,
    ))
    styles.add(ParagraphStyle(
        "Resultat",
        parent=styles["Normal"],
        fontSize=12,
        textColor=BLEU,
        spaceAfter=6,
        fontName="Helvetica-Bold",
    ))

    elements: list = []

    # ── Page de titre ──
    elements.append(Spacer(1, 60 * mm))
    elements.append(Paragraph(REPORT_TITLE, styles["Titre1"]))
    elements.append(Paragraph(REPORT_SUBTITLE, styles["Titre2"]))
    elements.append(Spacer(1, 10 * mm))
    elements.append(HRFlowable(width="100%", color=BLEU, thickness=2))
    elements.append(Spacer(1, 10 * mm))
    elements.append(Paragraph(f"FlexiBeam v{APP_VERSION}", styles["Centre"]))
    elements.append(PageBreak())

    # ── 1. Données d'entrée ──
    elements.append(Paragraph("1. Données d'entrée", styles["Titre2"]))

    # Géométrie
    elements.append(Paragraph("<b>Géométrie</b>", styles["Normal_FR"]))
    data_geo = [
        ["Paramètre", "Valeur"],
        ["Type de section", geometrie.type_section.value],
        ["b_w", f"{geometrie.b_w:.0f} mm"],
        ["h", f"{geometrie.h:.0f} mm"],
        ["d", f"{geometrie.hauteur_utile_effective():.1f} mm"],
    ]
    if geometrie.b_eff > 0:
        data_geo.append(["b_eff", f"{geometrie.b_eff:.0f} mm"])
    if geometrie.h_f > 0:
        data_geo.append(["h_f", f"{geometrie.h_f:.0f} mm"])
    data_geo.append(["c_nom", f"{geometrie.c_nom:.0f} mm"])
    data_geo.append(["Ø étrier", f"{geometrie.diam_etrier:.0f} mm"])

    elements.append(_creer_tableau(data_geo))
    elements.append(Spacer(1, 5 * mm))

    # Matériaux
    elements.append(Paragraph("<b>Matériaux</b>", styles["Normal_FR"]))
    data_mat = [
        ["Paramètre", "Valeur"],
        ["f_ck", f"{materiaux.beton.fck:.0f} MPa"],
        ["f_yk", f"{materiaux.acier.fyk:.0f} MPa"],
        ["E_s", f"{materiaux.acier.Es:.0f} MPa"],
        ["α_cc", f"{materiaux.beton.alpha_cc:.2f}"],
        ["γ_c", f"{materiaux.beton.gamma_c:.2f}"],
        ["γ_s", f"{materiaux.acier.gamma_s:.2f}"],
        ["Ductilité", materiaux.acier.classe_ductilite.value],
        ["Diagramme", materiaux.acier.diagramme.value],
    ]
    elements.append(_creer_tableau(data_mat))
    elements.append(Spacer(1, 5 * mm))

    # Sollicitations
    elements.append(Paragraph("<b>Sollicitations</b>", styles["Normal_FR"]))
    data_sol = [
        ["Paramètre", "Valeur"],
        ["M_Ed", f"{Nmm_to_kNm(sollicitations.M_Ed):.2f} kN·m"],
        ["M_ser", f"{Nmm_to_kNm(sollicitations.M_ser):.2f} kN·m"],
        ["Signe", "Positif" if sollicitations.moment_positif else "Négatif"],
    ]
    elements.append(_creer_tableau(data_sol))
    elements.append(Spacer(1, 5 * mm))

    # ── 2. Résultats ELU ──
    elements.append(Paragraph("2. Calcul ELU – Flexion simple", styles["Titre2"]))
    elu = resultats.elu

    if elu.erreurs:
        for err in elu.erreurs:
            elements.append(Paragraph(f"<font color='red'>❌ {err}</font>", styles["Normal_FR"]))
    else:
        elements.append(Paragraph(elu.commentaire_section, styles["Normal_FR"]))
        elements.append(Spacer(1, 3 * mm))

        data_elu = [
            ["Paramètre", "Valeur"],
            ["f_cd", f"{elu.fcd:.2f} MPa"],
            ["f_cu", f"{elu.fcu:.2f} MPa"],
            ["μ_cu", f"{elu.mu_cu:.4f}"],
            ["μ_ulim", f"{elu.mu_ulim:.4f}"],
            ["α_u", f"{elu.alpha_u:.4f}"],
            ["x_u", f"{elu.x_u:.1f} mm"],
            ["Z_c", f"{elu.Zc:.1f} mm"],
            ["Pivot", elu.pivot.pivot],
            ["ε_s1", f"{elu.pivot.epsilon_s1*1000:.2f} ‰"],
            ["σ_s1", f"{elu.pivot.sigma_s1:.1f} MPa"],
        ]
        elements.append(_creer_tableau(data_elu))
        elements.append(Spacer(1, 5 * mm))

        if elu.necessite_aciers_comprimes:
            elements.append(Paragraph(
                f"<font color='orange'>⚠ {elu.commentaire_compression}</font>",
                styles["Normal_FR"],
            ))
            elements.append(Spacer(1, 3 * mm))

        elements.append(Paragraph(
            f"<b>Section d'acier requise : As = {elu.As_requise/100:.2f} cm² "
            f"({elu.As_requise:.0f} mm²)</b>",
            styles["Resultat"],
        ))
        elements.append(Paragraph(
            f"Section minimale : As,min = {elu.As_min/100:.2f} cm²",
            styles["Normal_FR"],
        ))

    # ── 3. Vérification du ferraillage ──
    if resultats.verification:
        elements.append(PageBreak())
        elements.append(Paragraph("3. Vérification du ferraillage", styles["Titre2"]))
        verif = resultats.verification

        if verif.details_lits:
            data_lits = [["Lit", "Nb", "Ø (mm)", "As (cm²)", "d_i (mm)"]]
            for det in verif.details_lits:
                data_lits.append([
                    str(det["lit_numero"]),
                    str(det["nombre_barres"]),
                    f"HA{det['diametre_mm']:.0f}",
                    f"{det['section_totale_cm2']:.2f}",
                    f"{det['d_i_mm']:.1f}",
                ])
            elements.append(_creer_tableau(data_lits))
            elements.append(Spacer(1, 5 * mm))

        data_verif = [
            ["Contrôle", "Résultat"],
            ["As,requise", f"{verif.As_requise_mm2/100:.2f} cm²"],
            ["As,réelle", f"{verif.As_reelle_mm2/100:.2f} cm²"],
            ["Écart", f"{verif.ecart_absolu_mm2/100:.2f} cm² ({verif.taux_pourcentage:+.1f}%)"],
            ["d calcul", f"{verif.d_calcul:.1f} mm"],
            ["d réel", f"{verif.d_reel:.1f} mm"],
            ["Section", "OK" if verif.controle_section else "NON"],
            ["Bras de levier", "OK" if verif.controle_bras_levier else "NON"],
        ]
        elements.append(_creer_tableau(data_verif))
        elements.append(Spacer(1, 5 * mm))

        verdict = "VÉRIFIÉ" if verif.verdict_global else "NON VÉRIFIÉ"
        couleur = "green" if verif.verdict_global else "red"
        elements.append(Paragraph(
            f"<font color='{couleur}' size='14'><b>Verdict : {verdict}</b></font>",
            styles["Resultat"],
        ))

    # ── 4. Dispositions constructives ──
    if resultats.constructif:
        elements.append(Spacer(1, 5 * mm))
        elements.append(Paragraph("4. Dispositions constructives", styles["Titre2"]))
        for msg in resultats.constructif.messages:
            icone = "✓" if msg["type"] == "ok" else ("❌" if msg["type"] == "erreur" else "⚠")
            elements.append(Paragraph(f"{icone} {msg['message']}", styles["Normal_FR"]))

    # ── 5. Fissuration ──
    if resultats.fissuration:
        elements.append(Spacer(1, 5 * mm))
        elements.append(Paragraph("5. Fissuration et ELS", styles["Titre2"]))
        fiss = resultats.fissuration
        for msg in fiss.messages:
            elements.append(Paragraph(f"• {msg}", styles["Normal_FR"]))
        elements.append(Paragraph(
            f"<b>Verdict : {fiss.verdict}</b>", styles["Resultat"],
        ))

    # ── 6. Schéma 2D ──
    if image_2d_path and Path(image_2d_path).exists():
        elements.append(PageBreak())
        elements.append(Paragraph("6. Schéma de la section", styles["Titre2"]))
        img = Image(image_2d_path, width=160 * mm, height=120 * mm)
        elements.append(img)

    # ── 7. Conclusion ──
    elements.append(Spacer(1, 10 * mm))
    elements.append(HRFlowable(width="100%", color=BLEU, thickness=1))
    elements.append(Spacer(1, 5 * mm))

    if resultats.verification and resultats.verification.verdict_global:
        elements.append(Paragraph(
            "<font color='green' size='14'><b>CONCLUSION : SECTION VÉRIFIÉE</b></font>",
            styles["Resultat"],
        ))
    elif resultats.verification:
        elements.append(Paragraph(
            "<font color='red' size='14'><b>CONCLUSION : SECTION NON VÉRIFIÉE</b></font>",
            styles["Resultat"],
        ))
    else:
        elements.append(Paragraph(
            "Conclusion : calcul ELU effectué. Aucun ferraillage proposé pour vérification.",
            styles["Normal_FR"],
        ))

    # Build
    doc.build(elements)


def _creer_tableau(data: list[list[str]]) -> Table:
    """Crée un tableau formaté."""
    t = Table(data, hAlign="LEFT")
    style = TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), BLEU),
        ("TEXTCOLOR", (0, 0), (-1, 0), HexColor("#FFFFFF")),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -1), 0.5, GRIS),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [HexColor("#FFFFFF"), GRIS_CLAIR]),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
    ])
    t.setStyle(style)
    return t
