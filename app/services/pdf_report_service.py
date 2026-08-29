from __future__ import annotations

import io
import json
from datetime import datetime
from typing import Any

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    HRFlowable,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


def generate_clinical_health_pdf(
    user_name: str,
    user_email: str,
    snapshot_data: dict[str, Any],
) -> bytes:
    """Generates a publication-grade, multi-disease clinical health summary PDF using ReportLab."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40,
    )

    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        "ReportTitle",
        parent=styles["Heading1"],
        fontSize=20,
        leading=24,
        textColor=colors.HexColor("#065F46"),
        fontName="Helvetica-Bold",
        spaceAfter=4,
    )
    subtitle_style = ParagraphStyle(
        "ReportSubtitle",
        parent=styles["Normal"],
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#4B5563"),
        spaceAfter=12,
    )
    section_heading = ParagraphStyle(
        "SectionHeading",
        parent=styles["Heading2"],
        fontSize=12,
        leading=16,
        textColor=colors.HexColor("#111827"),
        fontName="Helvetica-Bold",
        spaceBefore=10,
        spaceAfter=6,
    )
    body_style = ParagraphStyle(
        "ReportBody",
        parent=styles["Normal"],
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#374151"),
    )
    disclaimer_style = ParagraphStyle(
        "DisclaimerText",
        parent=styles["Normal"],
        fontSize=7.5,
        leading=10,
        textColor=colors.HexColor("#92400E"),
    )

    elements = []

    # 1. Header Banner
    elements.append(Paragraph("LifeOS Preventive Health Intelligence Report", title_style))
    elements.append(Paragraph("Comprehensive Multi-System Clinical Screening & Decision Support", subtitle_style))
    elements.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#10B981"), spaceAfter=12))

    # 2. Patient & Report Metadata
    now_str = datetime.now().strftime("%B %d, %Y - %I:%M %p")
    snap_id = snapshot_data.get("id", "N/A")
    meta_data = [
        [
            Paragraph(f"<b>Patient Name:</b> {user_name}", body_style),
            Paragraph(f"<b>Generated:</b> {now_str}", body_style),
        ],
        [
            Paragraph(f"<b>Patient Email:</b> {user_email}", body_style),
            Paragraph(f"<b>Assessment ID:</b> {snap_id}", body_style),
        ],
    ]
    meta_table = Table(meta_data, colWidths=[260, 272])
    meta_table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F9FAFB")),
            ("PADDING", (0, 0), (-1, -1), 6),
            ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#E5E7EB")),
        ])
    )
    elements.append(meta_table)
    elements.append(Spacer(1, 10))

    # 3. Overall Risk Fusion & Health Score
    risk_fusion = snapshot_data.get("risk_fusion") or {}
    ov_pct = risk_fusion.get("overall_risk_percentage", 0.0)
    health_score = risk_fusion.get("overall_health_score", 100 - int(ov_pct))
    top_priority = risk_fusion.get("top_priority_disease", "Cardiometabolic Normal")
    ov_level = risk_fusion.get("overall_risk_level", "low").upper()

    score_color = "#10B981" if ov_level == "LOW" else "#F59E0B" if ov_level == "MODERATE" else "#EF4444"

    elements.append(Paragraph("Executive Screening Summary", section_heading))
    summary_data = [
        [
            Paragraph("<b>Overall Health Score:</b>", body_style),
            Paragraph(f"<b>{health_score} / 100</b>", ParagraphStyle("Score", parent=body_style, textColor=colors.HexColor(score_color), fontName="Helvetica-Bold")),
            Paragraph("<b>Composite Risk Score:</b>", body_style),
            Paragraph(f"{ov_pct:.1f}% ({ov_level})", body_style),
        ],
        [
            Paragraph("<b>Primary Elevation:</b>", body_style),
            Paragraph(f"{top_priority}", body_style),
            Paragraph("<b>Risk Fusion Model:</b>", body_style),
            Paragraph("Equal-Weighted 4-Disease Matrix", body_style),
        ],
    ]
    summary_table = Table(summary_data, colWidths=[130, 136, 130, 136])
    summary_table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F0FDF4")),
            ("PADDING", (0, 0), (-1, -1), 6),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#D1FAE5")),
        ])
    )
    elements.append(summary_table)
    elements.append(Spacer(1, 10))

    # 4. Multi-Disease Screening Breakdown Table
    elements.append(Paragraph("Six-Vertical Clinical Screening Breakdown", section_heading))

    disease_results = snapshot_data.get("disease_results") or {}
    table_rows = [
        ["Clinical Vertical", "Model Architecture", "Probability", "Operating Threshold", "Risk Classification"]
    ]

    disease_order = [
        ("Heart Disease", "heart", "XGBoost Classifier", "0.40"),
        ("Diabetes", "diabetes", "LightGBM Classifier", "0.70"),
        ("Hypertension", "hypertension", "Framingham XGBoost", "0.60"),
        ("Obesity Risk", "obesity", "LightGBM (Target Protected)", "0.50"),
        ("Stroke Risk", "stroke", "Weighted LightGBM", "0.50"),
        ("Chronic Kidney Disease", "ckd", "UCI XGBoost Clinical", "0.33"),
    ]

    for label, key, arch, def_thresh in disease_order:
        data_item = disease_results.get(key) or {}
        prob = data_item.get("risk_score") or data_item.get("probability")
        prob_str = f"{prob:.1%}" if isinstance(prob, (int, float)) else "Evaluated (Low)"
        thresh = str(data_item.get("threshold", def_thresh))
        level = (data_item.get("risk_level") or "low").upper()
        
        table_rows.append([label, arch, prob_str, thresh, level])

    disease_table = Table(table_rows, colWidths=[130, 142, 80, 95, 85])
    disease_table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#065F46")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("PADDING", (0, 0), (-1, -1), 5),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E5E7EB")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F9FAFB")]),
        ])
    )
    elements.append(disease_table)
    elements.append(Spacer(1, 10))

    # 5. Personalized Recommendations
    recs = snapshot_data.get("recommendations") or []
    if recs:
        elements.append(Paragraph("Personalized Lifestyle & Clinical Guidance", section_heading))
        rec_rows = []
        for idx, rec in enumerate(recs[:4], start=1):
            title = rec.get("title") if isinstance(rec, dict) else str(rec)
            desc = rec.get("description", "") if isinstance(rec, dict) else ""
            action = rec.get("action", "") if isinstance(rec, dict) else ""
            prio = rec.get("priority", "MODERATE").upper() if isinstance(rec, dict) else "MODERATE"
            
            p_text = f"<b>{idx}. [{prio}] {title}</b><br/>{desc} <i>Action: {action}</i>"
            rec_rows.append([Paragraph(p_text, body_style)])

        rec_table = Table(rec_rows, colWidths=[532])
        rec_table.setStyle(
            TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#FEF3C7")),
                ("PADDING", (0, 0), (-1, -1), 6),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#FDE68A")),
            ])
        )
        elements.append(rec_table)
        elements.append(Spacer(1, 10))

    # 6. Non-diagnostic Regulatory Disclaimer Box
    elements.append(Spacer(1, 6))
    disclaimer_text = (
        "<b>CLINICAL REGULATORY NOTICE & MEDICAL DISCLAIMER:</b><br/>"
        "LifeOS is a preventive health intelligence and early lifestyle screening system. It is NOT an FDA, CE, or JCI "
        "certified medical device, nor a substitute for professional clinical diagnosis. Risk probabilities are generated via "
        "statistical machine learning models. High or elevated indicators should be promptly validated by a licensed medical "
        "practitioner using diagnostic pathology laboratories and clinical examinations before altering any treatment regimens."
    )
    disc_data = [[Paragraph(disclaimer_text, disclaimer_style)]]
    disc_table = Table(disc_data, colWidths=[532])
    disc_table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#FFFBEB")),
            ("PADDING", (0, 0), (-1, -1), 8),
            ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#F59E0B")),
        ])
    )
    elements.append(disc_table)

    # Build Document
    doc.build(elements)
    return buffer.getvalue()
