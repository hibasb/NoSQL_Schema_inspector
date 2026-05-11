"""
exporter.py
Export du schéma et des rapports de sécurité en JSON, CSV et PDF.
"""
import json
import io
import csv
import datetime
from datetime import date


class SafeJSONEncoder(json.JSONEncoder):
    """Encoder JSON robuste : gère datetime, ObjectId, bytes, etc."""
    def default(self, obj):
        try:
            from bson import ObjectId
            if isinstance(obj, ObjectId):
                return str(obj)
        except ImportError:
            pass
        if isinstance(obj, (datetime.datetime, date)):
            return obj.isoformat()
        if isinstance(obj, bytes):
            return obj.decode("utf-8", errors="replace")
        return str(obj)



# ── JSON ─────────────────────────────────────────────────────

def export_security_report_json(audit_result: dict, collection_name: str = "collection") -> str:
    """Retourne le rapport d'audit au format JSON (str)."""
    report = {
        "collection": collection_name,
        "generated_at": datetime.datetime.now().isoformat(),
        "score": audit_result["score"],
        "summary": audit_result["summary"],
        "findings": audit_result["findings"]
    }
    return json.dumps(report, indent=2, ensure_ascii=False, cls=SafeJSONEncoder)


# ── CSV ──────────────────────────────────────────────────────

def export_security_report_csv(audit_result: dict) -> bytes:
    """Retourne le rapport d'audit au format CSV (bytes)."""
    output = io.StringIO()
    fieldnames = ["field", "rule", "severity", "message", "affected_docs", "sample"]
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    for finding in audit_result["findings"]:
        writer.writerow({k: finding.get(k, "") for k in fieldnames})
    return output.getvalue().encode("utf-8")


# ── PDF ──────────────────────────────────────────────────────

APP_NAME    = "NoSQL Schema Inspector"
APP_VERSION = "2.0"
APP_AUTHOR  = "NoSQL Schema Inspector Team"

# Recommandations par règle
_RECOMMENDATIONS = {
    "PLAINTEXT_PASSWORD":      "Hachez les mots de passe avec bcrypt ou Argon2 avant stockage.",
    "WEAK_HASH_MD5":           "Remplacez MD5 par bcrypt ($2b$) ou Argon2 pour le hachage.",
    "PII_EXPOSED":             "Chiffrez les donnees personnelles (AES-256) ou utilisez un vault.",
    "TOKEN_EXPOSED":           "Stockez les tokens dans un secret manager, pas en base.",
    "NOSQL_INJECTION_RISK":    "Validez et assainissez les entrees avant insertion en base.",
    "TYPE_JUGGLING":           "Imposez un schema strict (JSON Schema / Mongoose) pour ces champs.",
    "CARD_DATA_EXPOSED":       "Ne stockez jamais de donnees bancaires en clair (norme PCI-DSS).",
    "MISSING_TIMESTAMPS":      "Ajoutez createdAt / updatedAt pour la tracabilite.",
    "ROLE_FIELD_EXPOSED":      "Protegez les champs de role avec un controle d'acces cote serveur.",
    "UNSTRUCTURED_PERMISSIONS":"Structurez les permissions en array/object, pas en string libre.",
}


def _build_footer(canvas, doc):
    """Pied de page avec numero de page et nom de l'application."""
    canvas.saveState()
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor("#6b7280")
    page_num = canvas.getPageNumber()
    canvas.drawCentredString(
        doc.pagesize[0] / 2, 1.2 * 28.35,
        f"{APP_NAME} v{APP_VERSION}  |  Rapport de securite  |  Page {page_num}"
    )
    canvas.restoreState()


def export_security_report_pdf(audit_result: dict, collection_name: str = "collection") -> bytes:
    """
    Retourne le rapport d'audit au format PDF (bytes).
    Necessite : pip install reportlab
    """
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
    )

    now_str = datetime.datetime.now().strftime("%d/%m/%Y a %H:%M")

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        topMargin=2.5 * cm, bottomMargin=2 * cm,
        leftMargin=2 * cm, rightMargin=2 * cm,
        title=f"Rapport Securite - {collection_name}",
        author=APP_AUTHOR,
        subject=f"Audit de vulnerabilites NoSQL pour la collection {collection_name}",
        creator=f"{APP_NAME} v{APP_VERSION}",
        keywords=[APP_NAME, "securite", "audit", "NoSQL", collection_name],
    )
    styles = getSampleStyleSheet()

    # ── Styles personnalises ──
    sty_title = ParagraphStyle(
        "RptTitle", parent=styles["Title"],
        fontSize=22, textColor=colors.HexColor("#1e3a5f"),
        spaceAfter=14, fontName="Helvetica-Bold"
    )
    sty_subtitle = ParagraphStyle(
        "RptSubtitle", fontSize=10, textColor=colors.HexColor("#6b7280"),
        spaceAfter=6
    )
    sty_section = ParagraphStyle(
        "RptSection", parent=styles["Heading2"],
        fontSize=15, textColor=colors.HexColor("#1e3a5f"),
        spaceBefore=14, spaceAfter=6, fontName="Helvetica-Bold"
    )
    sty_body = styles["Normal"]

    SEV_COLORS = {
        "CRITICAL": colors.HexColor("#dc2626"),
        "HIGH":     colors.HexColor("#ea580c"),
        "MEDIUM":   colors.HexColor("#ca8a04"),
        "INFO":     colors.HexColor("#2563eb"),
    }
    SEV_LABELS = {
        "CRITICAL": "CRITIQUE",
        "HIGH":     "ELEVE",
        "MEDIUM":   "MOYEN",
        "INFO":     "INFO",
    }

    story = []

    # ════════════════════════════════════════════════════════════
    #  EN-TETE
    # ════════════════════════════════════════════════════════════
    header_data = [[
        Paragraph(f"<b>{APP_NAME}</b>", ParagraphStyle(
            "HdrLeft", fontSize=13, textColor=colors.white, fontName="Helvetica-Bold"
        )),
        Paragraph(f"<b>v{APP_VERSION}</b>", ParagraphStyle(
            "HdrRight", fontSize=11, textColor=colors.white, alignment=2
        ))
    ]]
    header = Table(header_data, colWidths=[12 * cm, 5 * cm])
    header.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#1e3a5f")),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("LEFTPADDING", (0, 0), (-1, -1), 14),
        ("RIGHTPADDING", (0, 0), (-1, -1), 14),
        ("ROUNDEDCORNERS", [6, 6, 6, 6]),
    ]))
    story.append(header)
    story.append(Spacer(1, 0.5 * cm))

    story.append(Paragraph("Rapport d'Audit de Securite", sty_title))
    story.append(Paragraph(
        f"Collection : <b>{collection_name}</b> &nbsp;&nbsp;|&nbsp;&nbsp; "
        f"Date : <b>{now_str}</b> &nbsp;&nbsp;|&nbsp;&nbsp; "
        f"Outil : <b>{APP_NAME} v{APP_VERSION}</b>",
        sty_subtitle
    ))
    story.append(HRFlowable(
        width="100%", thickness=2, color=colors.HexColor("#1e3a5f"),
        spaceAfter=10
    ))

    # ════════════════════════════════════════════════════════════
    #  1. SCORE DE SECURITE
    # ════════════════════════════════════════════════════════════
    score = audit_result["score"]
    score_color = (
        colors.HexColor("#16a34a") if score >= 70
        else colors.HexColor("#ea580c") if score >= 40
        else colors.HexColor("#dc2626")
    )
    score_label = "BON" if score >= 70 else "MOYEN" if score >= 40 else "DANGER"

    story.append(Paragraph("1. Score de Securite", sty_section))

    score_data = [[
        Paragraph(
            f"<font size='28'><b>{score}</b></font>"
            f"<font size='14' color='#6b7280'> / 100</font>",
            ParagraphStyle("ScoreNum", alignment=1, textColor=score_color)
        ),
        Paragraph(
            f"<font size='16'><b>[{score_label}]</b></font><br/><br/>"
            f"<font size='9' color='#6b7280'>"
            f"{'Aucune vulnerabilite critique detectee.' if score >= 70 else 'Des vulnerabilites ont ete detectees. Consultez le detail ci-dessous.'}"
            f"</font>",
            ParagraphStyle("ScoreDesc", alignment=0, textColor=score_color)
        )
    ]]
    score_table = Table(score_data, colWidths=[5 * cm, 12 * cm])
    score_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, 0), colors.HexColor("#f8fafc")),
        ("BACKGROUND", (1, 0), (1, 0), colors.HexColor("#f8fafc")),
        ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#e5e7eb")),
        ("ROUNDEDCORNERS", [6, 6, 6, 6]),
        ("TOPPADDING", (0, 0), (-1, -1), 12),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    story.append(score_table)
    story.append(Spacer(1, 0.5 * cm))

    # ════════════════════════════════════════════════════════════
    #  2. RESUME PAR SEVERITE
    # ════════════════════════════════════════════════════════════
    summary = audit_result["summary"]
    story.append(Paragraph("2. Resume par Severite", sty_section))

    summary_data = [
        [
            Paragraph("<b>Severite</b>", ParagraphStyle("TH", textColor=colors.white, fontSize=10)),
            Paragraph("<b>Findings</b>", ParagraphStyle("TH2", textColor=colors.white, fontSize=10, alignment=1)),
            Paragraph("<b>Impact</b>", ParagraphStyle("TH3", textColor=colors.white, fontSize=10)),
        ],
        ["CRITIQUE", str(summary.get("CRITICAL", 0)), "Exploitation immediate possible"],
        ["ELEVE",    str(summary.get("HIGH",     0)), "Risque significatif"],
        ["MOYEN",    str(summary.get("MEDIUM",   0)), "Amelioration recommandee"],
        ["INFO",     str(summary.get("INFO",     0)), "Bonne pratique"],
    ]

    sev_row_colors = [
        colors.HexColor("#fef2f2"),
        colors.HexColor("#fff7ed"),
        colors.HexColor("#fefce8"),
        colors.HexColor("#eff6ff"),
    ]

    t = Table(summary_data, colWidths=[5 * cm, 4 * cm, 8 * cm])
    style_cmds = [
        ("BACKGROUND",  (0, 0), (-1, 0), colors.HexColor("#1e3a5f")),
        ("FONTNAME",    (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE",    (0, 0), (-1, -1), 10),
        ("GRID",        (0, 0), (-1, -1), 0.5, colors.HexColor("#d1d5db")),
        ("ALIGN",       (1, 0), (1, -1), "CENTER"),
        ("TOPPADDING",  (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]
    for i, bg in enumerate(sev_row_colors):
        style_cmds.append(("BACKGROUND", (0, i + 1), (-1, i + 1), bg))
    t.setStyle(TableStyle(style_cmds))
    story.append(t)
    story.append(Spacer(1, 0.6 * cm))

    # ════════════════════════════════════════════════════════════
    #  3. DETAIL DES VULNERABILITES
    # ════════════════════════════════════════════════════════════
    findings = audit_result["findings"]

    story.append(Paragraph("3. Detail des Vulnerabilites", sty_section))

    if not findings:
        story.append(Paragraph(
            "Aucune vulnerabilite detectee. La collection est conforme.",
            sty_body
        ))
    else:
        sev_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "INFO": 3}
        sorted_findings = sorted(findings, key=lambda x: sev_order.get(x["severity"], 99))

        for i, finding in enumerate(sorted_findings, 1):
            sev = finding.get("severity", "INFO")
            sev_color = SEV_COLORS.get(sev, colors.grey)
            sev_label = SEV_LABELS.get(sev, sev)

            # Titre numerote
            finding_title = ParagraphStyle(
                f"FT{i}", fontSize=11, textColor=sev_color,
                fontName="Helvetica-Bold", spaceBefore=8, spaceAfter=2
            )
            story.append(Paragraph(
                f"3.{i}  [{sev_label}]  {finding['rule']}"
                f"  -  champ : <font color='#374151'><b>{finding['field']}</b></font>",
                finding_title
            ))

            # Description
            story.append(Paragraph(finding["message"], sty_body))

            # Details en tableau compact
            detail_data = [[
                Paragraph(f"<b>Documents touches :</b> {finding['affected_docs']}", sty_body),
                Paragraph(f"<b>Exemple (masque) :</b> <font face='Courier'>{finding['sample']}</font>", sty_body),
            ]]
            dt = Table(detail_data, colWidths=[8.5 * cm, 8.5 * cm])
            dt.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#e5e7eb")),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ]))
            story.append(dt)

            # Recommandation
            reco = _RECOMMENDATIONS.get(finding["rule"], "")
            if reco:
                reco_style = ParagraphStyle(
                    f"Reco{i}", fontSize=9, textColor=colors.HexColor("#166534"),
                    fontName="Helvetica-Oblique", spaceBefore=2, spaceAfter=4
                )
                story.append(Paragraph(f"Recommandation : {reco}", reco_style))

            story.append(HRFlowable(
                width="100%", thickness=0.5,
                color=colors.HexColor("#e5e7eb"), spaceAfter=4
            ))

    # ════════════════════════════════════════════════════════════
    #  4. INFORMATIONS DU RAPPORT
    # ════════════════════════════════════════════════════════════
    story.append(Spacer(1, 0.8 * cm))
    story.append(Paragraph("4. Informations du Rapport", sty_section))

    meta_data = [
        ["Propriete", "Valeur"],
        ["Application", f"{APP_NAME} v{APP_VERSION}"],
        ["Collection analysee", collection_name],
        ["Date de generation", now_str],
        ["Nombre de findings", str(len(findings))],
        ["Score de securite", f"{score}/100 ({score_label})"],
    ]
    mt = Table(meta_data, colWidths=[6 * cm, 11 * cm])
    mt.setStyle(TableStyle([
        ("BACKGROUND",  (0, 0), (-1, 0), colors.HexColor("#1e3a5f")),
        ("TEXTCOLOR",   (0, 0), (-1, 0), colors.white),
        ("FONTNAME",    (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE",    (0, 0), (-1, -1), 10),
        ("GRID",        (0, 0), (-1, -1), 0.5, colors.HexColor("#d1d5db")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#f9fafb"), colors.white]),
        ("TOPPADDING",  (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(mt)

    # ── Build avec footer ──
    doc.build(story, onFirstPage=_build_footer, onLaterPages=_build_footer)
    buffer.seek(0)
    return buffer.read()
