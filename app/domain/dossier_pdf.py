"""Advocate-Ready Kerala Property Title Diligence Dossier Generator.

Produces comprehensive, publication-grade PDF legal audit reports adhering to
Kerala High Court precedents, Registration Department norms, and statutory
due-diligence checklists for prospective land buyers and NRI investors.
"""

from __future__ import annotations

import io
from datetime import datetime
from typing import Any

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import (
    HRFlowable,
    KeepTogether,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


class AdvocateDossierGenerator:
    """Builds an advocate-ready legal title diligence PDF dossier."""

    PRIMARY_COLOR = colors.HexColor("#0f5132")      # Forest Green
    ACCENT_COLOR = colors.HexColor("#1e3a8a")       # Navy Blue
    DANGER_COLOR = colors.HexColor("#991b1b")       # Crimson Red
    WARNING_COLOR = colors.HexColor("#b45309")      # Amber
    LIGHT_BG = colors.HexColor("#f8fafc")          # Slate Light
    CARD_BORDER = colors.HexColor("#cbd5e1")       # Slate Border

    @classmethod
    def generate_pdf_bytes(cls, audit_data: dict[str, Any]) -> bytes:
        """Renders audit dictionary into PDF binary stream."""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            leftMargin=36,
            rightMargin=36,
            topMargin=36,
            bottomMargin=36,
        )

        styles = getSampleStyleSheet()

        title_style = ParagraphStyle(
            "DossierTitle",
            parent=styles["Heading1"],
            fontSize=18,
            leading=22,
            textColor=cls.PRIMARY_COLOR,
            fontName="Helvetica-Bold",
            spaceAfter=4,
        )
        subtitle_style = ParagraphStyle(
            "DossierSubtitle",
            parent=styles["Normal"],
            fontSize=9,
            leading=13,
            textColor=colors.HexColor("#475569"),
            spaceAfter=12,
        )
        h2_style = ParagraphStyle(
            "DossierH2",
            parent=styles["Heading2"],
            fontSize=12,
            leading=16,
            textColor=cls.ACCENT_COLOR,
            fontName="Helvetica-Bold",
            spaceBefore=10,
            spaceAfter=6,
        )
        body_style = ParagraphStyle(
            "DossierBody",
            parent=styles["Normal"],
            fontSize=8.5,
            leading=12,
            textColor=colors.HexColor("#1e293b"),
        )
        body_bold = ParagraphStyle(
            "DossierBodyBold",
            parent=body_style,
            fontName="Helvetica-Bold",
        )
        disclaimer_style = ParagraphStyle(
            "DossierDisclaimer",
            parent=styles["Normal"],
            fontSize=8,
            leading=11,
            textColor=colors.HexColor("#334155"),
        )

        story = []

        # Header Title
        story.append(Paragraph("KANDEZUTHTHU AI · കണ്ടഴുത്ത് ആധാരംനോക്കി", title_style))
        story.append(
            Paragraph(
                "PRE-TRANSACTION TITLE AUDIT & STATUTORY RED-FLAG DOSSIER | ADVOCATE VETTING BRIEF<br/>"
                f"Generated on {datetime.now().strftime('%d %B %Y at %I:%M %p')} · Jurisdiction: Kerala, India",
                subtitle_style,
            )
        )
        story.append(HRFlowable(width="100%", thickness=1.5, color=cls.PRIMARY_COLOR, spaceAfter=10))

        # Extract core fields
        meta = audit_data.get("metadata", {})
        prop_id = audit_data.get("property_identifier") or f"Sy {meta.get('survey_no', 'N/A')}, {meta.get('village', 'Kerala')}"
        doc_no = meta.get("document_number") or audit_data.get("document_number", "Unregistered / Under Audit")
        sro = meta.get("sro_name") or audit_data.get("sro", "Kerala SRO")
        extent_cents = meta.get("extent_cents", audit_data.get("extent_cents", 0.0))
        extent_ares = meta.get("extent_ares", round(extent_cents * 0.404686, 2) if extent_cents else 0.0)
        classification = meta.get("revenue_classification", audit_data.get("classification", "Purayidam"))
        verdict = audit_data.get("risk_verdict") or ("DEFECTIVE / HIGH RISK" if audit_data.get("sanity_score", 100) < 50 else "PASS WITH CONDITIONS")
        score = audit_data.get("sanity_score", audit_data.get("score", 75))

        # Executive Property Summary Table
        score_color = cls.DANGER_COLOR if score < 50 else (cls.WARNING_COLOR if score < 85 else cls.PRIMARY_COLOR)
        summary_data = [
            [
                Paragraph("<b>Property Identifier:</b>", body_style),
                Paragraph(str(prop_id), body_bold),
                Paragraph("<b>Diligence Score:</b>", body_style),
                Paragraph(f"<font color='{score_color.hexval()}'><b>{score}/100 ({verdict})</b></font>", body_bold),
            ],
            [
                Paragraph("<b>Document Reference:</b>", body_style),
                Paragraph(f"Doc #{doc_no} (SRO {sro})", body_style),
                Paragraph("<b>Land Classification:</b>", body_style),
                Paragraph(f"<b>{classification}</b> {'(2008 Act Risk)' if 'nilam' in str(classification).lower() else '(Purayidam)'}", body_style),
            ],
            [
                Paragraph("<b>Documented Extent:</b>", body_style),
                Paragraph(f"<b>{extent_cents} Cents</b> ({extent_ares} Ares / {round(extent_cents * 40.4686, 1)} sq.m)", body_style),
                Paragraph("<b>Statutory Audit Status:</b>", body_style),
                Paragraph("Pre-Advance Earnest Money Verification", body_style),
            ],
        ]

        summary_table = Table(summary_data, colWidths=[110, 160, 110, 142])
        summary_table.setStyle(
            TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), cls.LIGHT_BG),
                ("BOX", (0, 0), (-1, -1), 1, cls.CARD_BORDER),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ])
        )
        story.append(summary_table)
        story.append(Spacer(1, 10))

        # 4 Fatal Traps & Findings
        findings = []
        sanity = audit_data.get("sanity_result", {})
        if isinstance(sanity, dict) and "findings" in sanity:
            findings = sanity["findings"]
        elif "findings" in audit_data:
            findings = audit_data["findings"]

        story.append(Paragraph("1. STATUTORY RED-FLAG AUDIT (KERALA PROPERTY LAW DISCLOSURES)", h2_style))

        if findings:
            findings_data = [
                [
                    Paragraph("<b>Risk Category</b>", body_bold),
                    Paragraph("<b>Severity</b>", body_bold),
                    Paragraph("<b>Governing Kerala Statute</b>", body_bold),
                    Paragraph("<b>Legal Risk Analysis & Recital Finding</b>", body_bold),
                ]
            ]
            for f in findings:
                f_title = f.get("title") or f.get("flag_type", "Statutory Flag")
                f_sev = f.get("severity", "MEDIUM")
                f_statute = f.get("kerala_statute") or f.get("statute", "Kerala Real Estate Law")
                f_exp = f.get("explanation") or f.get("description", "")
                sev_color = cls.DANGER_COLOR if f_sev == "CRITICAL" else cls.WARNING_COLOR

                findings_data.append([
                    Paragraph(f"<b>{f_title}</b>", body_style),
                    Paragraph(f"<font color='{sev_color.hexval()}'><b>{f_sev}</b></font>", body_bold),
                    Paragraph(f_statute, body_style),
                    Paragraph(f_exp, body_style),
                ])

            findings_table = Table(findings_data, colWidths=[120, 60, 130, 212])
            findings_table.setStyle(
                TableStyle([
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f1f5f9")),
                    ("BOX", (0, 0), (-1, -1), 1, cls.CARD_BORDER),
                    ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
                    ("TOPPADDING", (0, 0), (-1, -1), 5),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ])
            )
            story.append(findings_table)
        else:
            story.append(
                Paragraph(
                    "<i>No fatal statutory red flags were extracted from the submitted deed recital text. "
                    "Prior deed lineage and SRO registers must still be vetted.</i>",
                    body_style,
                )
            )

        story.append(Spacer(1, 10))

        # Four Boundaries (ചതുരതിരുകൾ)
        boundaries = meta.get("boundaries") or audit_data.get("boundaries", [])
        if boundaries:
            story.append(Paragraph("2. SCHEDULE BOUNDARIES AUDIT (ചതുരതിരുകൾ)", h2_style))
            b_data = [
                [
                    Paragraph("<b>Direction</b>", body_bold),
                    Paragraph("<b>Document Description</b>", body_bold),
                    Paragraph("<b>Easement / Access Implication</b>", body_bold),
                ]
            ]
            for b in boundaries:
                b_dir = b.get("direction", "")
                b_desc = b.get("boundary_description", "")
                implication = "Standard Abutting Boundary"
                if any(w in b_desc.lower() for w in ["vazhi", "pathway", "road", "വഴി", "നടപ്പുവഴി"]):
                    implication = "Access Pathway (Subject to Indian Easements Act Sec 13/15)"
                elif any(w in b_desc.lower() for w in ["thodu", "canal", "തോട്"]):
                    implication = "Watercourse / Canal buffer setback required"

                b_data.append([
                    Paragraph(f"<b>{b_dir}</b>", body_style),
                    Paragraph(b_desc, body_style),
                    Paragraph(implication, body_style),
                ])

            b_table = Table(b_data, colWidths=[100, 220, 202])
            b_table.setStyle(
                TableStyle([
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f1f5f9")),
                    ("BOX", (0, 0), (-1, -1), 1, cls.CARD_BORDER),
                    ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ])
            )
            story.append(b_table)
            story.append(Spacer(1, 10))

        # KPBR 2019 Building Rules & Conversion Fees
        br = audit_data.get("building_rules")
        pc = audit_data.get("paddy_conversion")
        if br or pc:
            story.append(Paragraph("3. KPBR 2019 BUILDING FEASIBILITY & REVENUE REGULARIZATION", h2_style))
            feasibility_rows = []
            if br:
                feasibility_rows.append([
                    Paragraph("<b>KPBR 2019 Rules:</b>", body_style),
                    Paragraph(
                        f"Rule Citation: <b>{br.get('rule_citation', 'KPBR 2019')}</b><br/>"
                        f"Minimum Motorable Access Road: <b>{br.get('min_road_width_m', 3.0)} meters</b><br/>"
                        f"Mandatory Setbacks: Front: {br.get('front_setback_m', 3.0)}m | Rear: {br.get('rear_setback_m', 1.5)}m | Sides: {br.get('side_setback_1_m', 1.0)}m & {br.get('side_setback_2_m', 1.2)}m",
                        body_style,
                    ),
                ])
            if pc and pc.get("statutory_conversion_fee_inr", 0) > 0:
                feasibility_rows.append([
                    Paragraph("<b>Paddy Land Conversion:</b>", body_style),
                    Paragraph(
                        f"<b>Section 27A Form 6 Estimated Fee:</b> ₹{pc.get('statutory_conversion_fee_inr', 0):,}<br/>"
                        f"Slab: {pc.get('applicable_slab_percentage', 10)}% of fair value. "
                        f"Residential Free Exemption: {pc.get('free_exemption_cents', 25)} Cents.",
                        body_style,
                    ),
                ])

            if feasibility_rows:
                fe_table = Table(feasibility_rows, colWidths=[140, 382])
                fe_table.setStyle(
                    TableStyle([
                        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
                        ("BOX", (0, 0), (-1, -1), 1, cls.CARD_BORDER),
                        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
                        ("TOPPADDING", (0, 0), (-1, -1), 5),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                    ])
                )
                story.append(fe_table)
                story.append(Spacer(1, 10))

        # SRO Advocate Vetting Checklist (5 Essential Checks)
        story.append(KeepTogether([
            Paragraph("4. SRO SUB-REGISTRAR OFFICE ADVOCATE VETTING CHECKLIST", h2_style),
            Paragraph(
                "The buyer's advocate or document writer must verify the following items at the jurisdictional Sub-Registrar Office prior to disbursing earnest money:",
                body_style,
            ),
            Spacer(1, 4),
        ]))

        sro_checks = [
            ("1. Prior Deed Boundary Comparison", "Examine Book 1 registers for prior deeds (മുന്നാധാരം) to verify that the 4 boundaries match and no pathway rights were omitted during subsequent transfers."),
            ("2. BTR & Form 5 Data Bank Verification", "Confirm that the land is excluded from the Kerala Agricultural Data Bank and verify whether Thandapper Register matches Purayidam or unnotified Nilam."),
            ("3. Minor Sanction Court Order Search", "If any seller or co-heir is a minor, inspect the Principal District Court records for prior sanction order under Sec 8(2) of Hindu Minority & Guardianship Act."),
            ("4. Senior Citizen Maintenance Caveats", "Verify that no maintenance petition or revocation caveat is pending before the Revenue Divisional Officer (RDO) Maintenance Tribunal under Section 23 of the 2007 Act."),
            ("5. 30-Year Encumbrance Certificate (EC)", "Obtain an official computerized EC spanning minimum 30 years and verify Nil-encumbrance status across both pre-resurvey and resurvey numbers."),
        ]

        chk_data = [[Paragraph(f"<b>{title}</b>", body_style), Paragraph(desc, body_style)] for title, desc in sro_checks]
        chk_table = Table(chk_data, colWidths=[150, 372])
        chk_table.setStyle(
            TableStyle([
                ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f1f5f9")),
                ("BACKGROUND", (1, 0), (1, -1), colors.white),
                ("BOX", (0, 0), (-1, -1), 1, cls.CARD_BORDER),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ])
        )
        story.append(chk_table)
        story.append(Spacer(1, 10))

        # WhatsApp draft if available
        wa_text = audit_data.get("whatsapp_draft") or audit_data.get("whatsapp_inquiry")
        if wa_text:
            story.append(Paragraph("5. BILINGUAL SELLER / BROKER INQUIRY DRAFT (MALAYALAM)", h2_style))
            wa_table = Table([[Paragraph(f"<i>{wa_text}</i>", body_style)]], colWidths=[522])
            wa_table.setStyle(
                TableStyle([
                    ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f0fdf4")),
                    ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#86efac")),
                    ("TOPPADDING", (0, 0), (-1, -1), 6),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                    ("LEFTPADDING", (0, 0), (-1, -1), 8),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ])
            )
            story.append(wa_table)
            story.append(Spacer(1, 10))

        # Ethical Non-AI Guardrails & Legal Disclaimer Box
        story.append(KeepTogether([
            Paragraph("6. STATUTORY DISCLAIMERS & WHAT AI CANNOT VERIFY ON PAPER", h2_style),
            Table([
                [
                    Paragraph(
                        "<b>MANDATORY GROUND INSPECTION ITEMS (NON-VERIFIABLE BY AI OR PAPER AUDIT):</b><br/>"
                        "1. <b>Physical Survey Kallu & Encroachment:</b> AI cannot detect whether physical boundary stones (സർവേ കല്ല്) have been moved or if adjacent neighbors have encroached on the property.<br/>"
                        "2. <b>Road Motorability:</b> AI verifies deed recitals only; physical motorability, steep gradient, unpaved status, or cul-de-sac turning radius requires on-site inspection.<br/>"
                        "3. <b>Oral Family Covenants:</b> Unregistered family understandings (വായ്മൊഴി ഉടമ്പടി) or unfiled court caveats cannot be ascertained from registered deeds alone.<br/>"
                        "4. <b>Topography & Flooding:</b> Ground waterlogging, flood levels (e.g. 2018/2019 Kerala floods), high-tension power line clearance, and slope stability must be inspected in person.<br/><br/>"
                        "<b>LEGAL COUNSEL ADVISORY:</b> This dossier is an algorithmic pre-audit tool designed to highlight red-flags before advance payment. "
                        "It does NOT constitute a formal Title Certificate or 100% legal guarantee. A licensed Kerala High Court or District advocate must inspect original parent deeds at the SRO.",
                        disclaimer_style,
                    )
                ]
            ],
            colWidths=[522],
            style=[
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#fef2f2")),
                ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#fca5a5")),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ]),
        ]))

        doc.build(story)
        return buffer.getvalue()
