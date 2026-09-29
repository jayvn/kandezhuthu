#!/usr/bin/env python3
"""Generate realistic, authentic Kerala Title Deed and SRO Encumbrance Certificate PDFs.

Generates:
1. data/sample_deeds/kerala_sale_deed_aluva_re_sy_345_1.pdf (Sale Deed / തീറാധാരം)
2. data/sample_deeds/kerala_sro_ec_aluva_30_year_search.pdf (Encumbrance Certificate / കുടിക്കടം - Form 15)
3. Updates data/sample_deeds/sample_aluva_deed.pdf with the full authentic version.
"""

from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


def create_kerala_sale_deed_pdf(output_path: Path):
    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=A4,
        leftMargin=36,
        rightMargin=36,
        topMargin=36,
        bottomMargin=36,
    )
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "GovTitle",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=13,
        leading=16,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#065f46"),
    )
    stamp_hdr_style = ParagraphStyle(
        "StampHdr",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=9,
        leading=12,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#1e293b"),
    )
    section_h2 = ParagraphStyle(
        "SecH2",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=10,
        leading=13,
        textColor=colors.HexColor("#0f5132"),
        spaceBefore=8,
        spaceAfter=4,
    )
    body_style = ParagraphStyle(
        "BodyJustify",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8.5,
        leading=12,
        alignment=TA_JUSTIFY,
        textColor=colors.HexColor("#1e293b"),
    )
    meta_label = ParagraphStyle(
        "MetaLbl",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8,
        leading=10,
        textColor=colors.HexColor("#334155"),
    )
    meta_val = ParagraphStyle(
        "MetaVal",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8,
        leading=10,
        textColor=colors.HexColor("#0f172a"),
    )

    story = []

    # 1. Government e-Stamp Certificate Header Box
    stamp_data = [
        [
            Paragraph("<b>GOVERNMENT OF KERALA — REGISTRATION DEPARTMENT</b><br/><font size=7 color='#64748b'>e-Stamp Certificate · Stock Holding Corporation of India Ltd</font>", stamp_hdr_style),
            Paragraph("<b>Certificate No:</b> IN-KL91847291048122M<br/><b>Date:</b> 14-Aug-2014 11:22 AM<br/><b>Ref:</b> SUBIN-KLKL120040439281729", meta_val),
        ],
        [
            Paragraph("<b>Account Reference:</b> NONACC (SV)/ kl1200404/ ALUVA/ KL-ER<br/><b>Purchased by:</b> SURESH NAIR S/O K. RAMAN NAIR<br/><b>Description:</b> Article 21 Conveyance (Sale Deed / തീറാധാരം)", meta_val),
            Paragraph("<b>Consideration Price:</b> ₹16,50,000/-<br/><b>Stamp Duty (8%):</b> ₹1,32,000/-<br/><b>Reg Fee (2%):</b> ₹33,000/- (Paid)", meta_val),
        ],
    ]
    stamp_table = Table(stamp_data, colWidths=[280, 240])
    stamp_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
        ("BOX", (0, 0), (-1, -1), 1.5, colors.HexColor("#065f46")),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ("PADDING", (0, 0), (-1, -1), 6),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    story.append(stamp_table)
    story.append(Spacer(1, 10))

    # SRO Registration Endorsement Banner
    sro_endorse = [
        [
            Paragraph("<b>SUB-REGISTRAR OFFICE: ALUVA</b> | Book 1, Volume 104, Pages 85 to 94<br/>"
                      "<b>DOCUMENT NUMBER: 1420 / 2014</b> | Date of Registration: 16-Aug-2014", ParagraphStyle("SroBanner", parent=styles["Normal"], fontName="Helvetica-Bold", fontSize=8.5, leading=12, alignment=TA_CENTER, textColor=colors.HexColor("#ffffff")))
        ]
    ]
    sro_table = Table(sro_endorse, colWidths=[520])
    sro_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#0f5132")),
        ("PADDING", (0, 0), (-1, -1), 5),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
    ]))
    story.append(sro_table)
    story.append(Spacer(1, 8))

    # Preamble: Executant & Claimant
    story.append(Paragraph("DEED OF ABSOLUTE SALE (തീറാധാര ഉടമ്പടി)", title_style))
    story.append(Spacer(1, 4))
    story.append(Paragraph(
        "This DEED OF ABSOLUTE SALE (Theeradharam) is executed on this the <b>14th day of August, 2014</b> at Aluva by:<br/>"
        "<b>1. EXECUTANT (SELLER / ഒന്നാം കക്ഷി):</b> Sri. <b>GEORGE CHACKO</b>, aged 54 years, son of late Chacko Varghese, "
        "residing at Varghese Villa, Desom Kara, Aluva West Village, Aluva Taluk, Ernakulam District (Aadhaar No. XXXX-XXXX-4912).<br/>"
        "IN FAVOUR OF:<br/>"
        "<b>2. CLAIMANT (BUYER / രണ്ടാം കക്ഷി):</b> Sri. <b>SURESH NAIR</b>, aged 42 years, son of K. Raman Nair, "
        "residing at Sreerangam, Edathala North, Aluva, Ernakulam District (Aadhaar No. XXXX-XXXX-8821).",
        body_style
    ))
    story.append(Spacer(1, 6))

    # Recital of Prior Title (Munnadharam)
    story.append(Paragraph("I. RECITAL OF TITLE & DERIVATION (മുന്നാധാര ചരിത്രവും അധികാരവും)", section_h2))
    story.append(Paragraph(
        "WHEREAS the property scheduled hereunder originally belonged to the late Chacko Varghese by virtue of "
        "Government Land Assignment (Pattayam No. LA 42/1982 of Aluva Taluk Office). Upon the demise of the said Chacko Varghese in 1996, "
        "the scheduled property along with other properties was partitioned between his sons George Chacko (the Executant herein) "
        "and Thomas Chacko under <b>Registered Partition Deed No. 892 of 1998</b> registered in Book 1 of Aluva Sub-Registrar Office. "
        "The scheduled property was set apart to the exclusive share and possession of the Executant George Chacko (excluding sister Mary Chacko "
        "who was married prior to 1986). The Executant has been paying land tax under Thandaper No. 10842 in Aluva West Village.",
        body_style
    ))
    story.append(Spacer(1, 6))

    # Consideration & Transfer Clause
    story.append(Paragraph("II. CONSIDERATION & CONVEYANCE (പ്രതിഫലവും സ്വത്തു കൈമാറ്റവും)", section_h2))
    story.append(Paragraph(
        "NOW THIS DEED WITNESSETH that in consideration of the total sum of <b>₹16,50,000/- (Rupees Sixteen Lakhs and Fifty Thousand only)</b> "
        "paid by the Claimant to the Executant (the receipt whereof is hereby acknowledged in full), the Executant doth hereby convey, transfer, "
        "and assign unto the Claimant all his absolute right, title, and ownership interest in the Schedule Property.",
        body_style
    ))
    story.append(Spacer(1, 6))

    # A-Schedule of Property
    story.append(Paragraph("III. A-SCHEDULE OF IMMOVABLE PROPERTY (A-ഷെഡ്യൂൾ സ്വത്തുവിവരം)", section_h2))
    schedule_data = [
        [Paragraph("<b>District:</b>", meta_label), Paragraph("Ernakulam (എറണാകുളം)", meta_val), Paragraph("<b>Taluk:</b>", meta_label), Paragraph("Aluva (ആലുവ)", meta_val)],
        [Paragraph("<b>Village:</b>", meta_label), Paragraph("Aluva West (ആലുവ വെസ്റ്റ്)", meta_val), Paragraph("<b>Desom / Kara:</b>", meta_label), Paragraph("Desom Kara", meta_val)],
        [Paragraph("<b>Re-Survey No:</b>", meta_label), Paragraph("<b>345/1</b> (Old Sy: 214/2)", meta_val), Paragraph("<b>Block No:</b>", meta_label), Paragraph("12", meta_val)],
        [Paragraph("<b>Total Extent:</b>", meta_label), Paragraph("<b>11.00 Cents</b> (4.45 Ares / 445.1 m²)", meta_val), Paragraph("<b>Revenue Class (BTR):</b>", meta_label), Paragraph("<b>Nilam (നിലം / Nanja - Wet Land)</b>", meta_val)],
        [Paragraph("<b>Thandaper No:</b>", meta_label), Paragraph("10842", meta_val), Paragraph("<b>Notified Fair Value:</b>", meta_label), Paragraph("₹1,20,000 / Are", meta_val)],
    ]
    sched_table = Table(schedule_data, colWidths=[100, 160, 100, 160])
    sched_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f1f5f9")),
        ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#94a3b8")),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ("PADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(sched_table)
    story.append(Spacer(1, 6))

    # Four Boundaries
    story.append(Paragraph("IV. FOUR BOUNDARIES (ചതുരതിരുകൾ / ചതുർസീമകൾ)", section_h2))
    boundaries_data = [
        [Paragraph("<b>Direction</b>", meta_label), Paragraph("<b>Boundary Description (ചതുർസീമ വിവരണം)</b>", meta_label), Paragraph("<b>Legal Status / Easement Note</b>", meta_label)],
        [Paragraph("<b>East (കിഴക്ക്):</b>", meta_label), Paragraph("3.5 Meter wide Pathway (നടപ്പുവഴി) running North-South", meta_val), Paragraph("Buried Easement: Right of way for western plots", meta_val)],
        [Paragraph("<b>South (തെക്ക്):</b>", meta_label), Paragraph("Compound wall & Property of Mathew Thomas", meta_val), Paragraph("Private land with intact boundary wall", meta_val)],
        [Paragraph("<b>West (പടിഞ്ഞാറ്):</b>", meta_label), Paragraph("Property of Mariamma Chacko (Re-Sy 345/2)", meta_val), Paragraph("Partitioned family parcel", meta_val)],
        [Paragraph("<b>North (വടക്ക്):</b>", meta_label), Paragraph("Panchayat Tarred Road (3.2 meters width)", meta_val), Paragraph("KPBR Rule 26 Compliant Access (Pass ≥3m)", meta_val)],
    ]
    b_table = Table(boundaries_data, colWidths=[90, 240, 190])
    b_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e2e8f0")),
        ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#94a3b8")),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ("PADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(b_table)
    story.append(Spacer(1, 6))

    # Easement Covenants & Maintenance Clause
    story.append(Paragraph("V. STATUTORY COVENANTS & EASEMENT RESERVATIONS", section_h2))
    story.append(Paragraph(
        "<b>1. Pathway Easement (വഴിയവകാശം):</b> The Executant and Claimant hereby covenant that the 3.5 meter wide pathway "
        "running along the Eastern boundary shall remain open for perpetuity as a common pathway (നടപ്പുവഴിയും വാഹനാവകാശവും) "
        "for the beneficial enjoyment of the western adjoining owners under Sections 13 and 15 of the Indian Easements Act, 1882.<br/>"
        "<b>2. Senior Citizen Maintenance (സംരക്ഷണ വ്യവസ്ഥ):</b> This assignment is subject to the condition that the Executant's elderly father "
        "shall retain the right to reside in the outhouse on the western corner during his lifetime without disturbance.",
        body_style
    ))
    story.append(Spacer(1, 8))

    # Attestation & Signatures
    story.append(Paragraph("VI. EXECUTION & WITNESS ATTESTATION", section_h2))
    sig_data = [
        [
            Paragraph("<b>EXECUTANT (സമ്മതിച്ച് ഒപ്പ്):</b><br/><br/><i>Sd/-</i> George Chacko", meta_val),
            Paragraph("<b>CLAIMANT (സ്വീകരിച്ച് ഒപ്പ്):</b><br/><br/><i>Sd/-</i> Suresh Nair", meta_val),
            Paragraph("<b>WITNESSES (സാക്ഷികൾ):</b><br/>1. <i>Sd/-</i> K. G. Radhakrishnan, Aluva<br/>2. <i>Sd/-</i> Joy V. Paul, Desom", meta_val),
        ]
    ]
    sig_table = Table(sig_data, colWidths=[160, 160, 200])
    sig_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
        ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#cbd5e1")),
        ("PADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(sig_table)
    story.append(Spacer(1, 8))

    # SRO Sub-Registrar Seal
    story.append(Paragraph(
        "<font size=7 color='#64748b'>Certified that Document No. 1420 of 2014 was presented by George Chacko at 11:45 AM on 16/08/2014, "
        "properly stamped with ₹1,32,000/- e-Stamp. Thumb impressions and digital photographs recorded. "
        "<b>Sub-Registrar, Sub-Registrar Office, Aluva (Seal & Signature)</b></font>",
        ParagraphStyle("SealNote", parent=styles["Normal"], fontName="Helvetica-Oblique", fontSize=7, leading=9, alignment=TA_CENTER)
    ))

    doc.build(story)


def create_kerala_sro_ec_pdf(output_path: Path):
    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=A4,
        leftMargin=36,
        rightMargin=36,
        topMargin=36,
        bottomMargin=36,
    )
    styles = getSampleStyleSheet()

    hdr_style = ParagraphStyle(
        "EcHdr",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=12,
        leading=15,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#065f46"),
    )
    meta_val = ParagraphStyle(
        "MetaVal",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=7.5,
        leading=10,
        textColor=colors.HexColor("#0f172a"),
    )
    tbl_hdr = ParagraphStyle(
        "TblHdr",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=7.5,
        leading=9.5,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#ffffff"),
    )
    tbl_cell = ParagraphStyle(
        "TblCell",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=7,
        leading=9,
        textColor=colors.HexColor("#0f172a"),
    )
    tbl_cell_bold = ParagraphStyle(
        "TblCellBold",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=7,
        leading=9,
        textColor=colors.HexColor("#991b1b"),
    )

    story = []

    # SRO Certificate Header
    story.append(Paragraph("GOVERNMENT OF KERALA — REGISTRATION DEPARTMENT", hdr_style))
    story.append(Paragraph("<b>CERTIFICATE OF ENCUMBRANCE ON PROPERTY (FORM NO. 15)</b><br/>"
                           "<font size=7 color='#64748b'>Issued under Sections 51 and 57 of the Indian Registration Act, 1908 (PEARL Portal)</font>",
                           ParagraphStyle("SubHdr", parent=hdr_style, fontSize=9, leading=12, fontName="Helvetica")))
    story.append(Spacer(1, 6))

    # Certificate Metadata
    meta_data = [
        [
            Paragraph("<b>Application No:</b> EC/2024/0091823<br/><b>Certificate No:</b> EC-ALV-2024-0041982<br/><b>Issued Date:</b> 28-Sep-2024", meta_val),
            Paragraph("<b>Sub-Registrar Office:</b> Aluva (Ernakulam District)<br/><b>Search Period:</b> 01-Jan-1994 to 28-Sep-2024 (30 Years)<br/><b>Fees Paid:</b> ₹250/- (Challan KL004198)", meta_val),
        ],
        [
            Paragraph("<b>District:</b> Ernakulam | <b>Taluk:</b> Aluva<br/><b>Village:</b> Aluva West | <b>Block:</b> 12", meta_val),
            Paragraph("<b>Re-Survey No:</b> 345/1 (Old Sy: 214/2)<br/><b>Extent:</b> 11.00 Cents (4.45 Ares) | <b>Class:</b> Nilam", meta_val),
        ]
    ]
    meta_tbl = Table(meta_data, colWidths=[260, 260])
    meta_tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
        ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#065f46")),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ("PADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(meta_tbl)
    story.append(Spacer(1, 8))

    # Form 15 Table
    story.append(Paragraph("<b>REGISTERED TRANSACTIONS / ENCUMBRANCES (FORM 15 ENTRIES):</b>",
                           ParagraphStyle("TblTitle", parent=styles["Normal"], fontName="Helvetica-Bold", fontSize=8.5, leading=11, textColor=colors.HexColor("#0f5132"))))
    story.append(Spacer(1, 4))

    ec_rows = [
        [
            Paragraph("<b>Sl</b>", tbl_hdr),
            Paragraph("<b>Date & Reg Details</b>", tbl_hdr),
            Paragraph("<b>Doc No / Book / Vol</b>", tbl_hdr),
            Paragraph("<b>Nature of Act (ആധാര സ്വഭാവം)</b>", tbl_hdr),
            Paragraph("<b>Parties (Executant & Claimant)</b>", tbl_hdr),
            Paragraph("<b>Consideration / Liability (₹)</b>", tbl_hdr),
            Paragraph("<b>Status / Audit Flag</b>", tbl_hdr),
        ],
        [
            Paragraph("1", tbl_cell),
            Paragraph("Exec: 10-May-1998<br/>Reg: 12-May-1998", tbl_cell),
            Paragraph("<b>892 / 1998</b><br/>Book 1, Vol 82<br/>Pages 45-52", tbl_cell),
            Paragraph("Partition Deed (ഭാഗപത്രം)", tbl_cell),
            Paragraph("<b>Exec:</b> Heirs of Chacko<br/><b>Claim:</b> George Chacko", tbl_cell),
            Paragraph("₹75,000/-<br/>(Declared Share)", tbl_cell),
            Paragraph("<font color='#d97706'><b>Mary Roy Defect:</b><br/>Sister excluded</font>", tbl_cell),
        ],
        [
            Paragraph("2", tbl_cell),
            Paragraph("Exec: 14-Aug-2014<br/>Reg: 16-Aug-2014", tbl_cell),
            Paragraph("<b>1420 / 2014</b><br/>Book 1, Vol 104<br/>Pages 85-94", tbl_cell),
            Paragraph("Absolute Sale Deed (തീറാധാരം)", tbl_cell),
            Paragraph("<b>Exec:</b> George Chacko<br/><b>Claim:</b> Suresh Nair", tbl_cell),
            Paragraph("₹16,50,000/-<br/>(₹1.50L / Cent)", tbl_cell),
            Paragraph("<font color='#d97706'><b>Extent Inflation:</b><br/>+1.0 Cent Phantom</font>", tbl_cell),
        ],
        [
            Paragraph("3", tbl_cell),
            Paragraph("Exec: 20-Oct-2021<br/>Reg: 22-Oct-2021", tbl_cell),
            Paragraph("<b>2105 / 2021</b><br/>Book 1, Vol 128<br/>Pages 110-116", tbl_cell),
            Paragraph("<b>Mortgage by Deposit of Title Deeds (ഗെഹാൻ / ബാങ്ക് ബാധ്യത)</b>", tbl_cell_bold),
            Paragraph("<b>Exec:</b> Suresh Nair<br/><b>Claim:</b> The Federal Bank Ltd (Aluva SME Branch)", tbl_cell),
            Paragraph("<b>₹45,00,000/-</b><br/>(Outstanding Lien)", tbl_cell_bold),
            Paragraph("<font color='#dc2626'><b>CRITICAL DEFECT:</b><br/>Undischarged Bank Mortgage (SARFAESI)</font>", tbl_cell_bold),
        ],
    ]
    ec_table = Table(ec_rows, colWidths=[20, 80, 80, 95, 115, 65, 65])
    ec_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#065f46")),
        ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#94a3b8")),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ("PADDING", (0, 0), (-1, -1), 4),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BACKGROUND", (0, 3), (-1, 3), colors.HexColor("#fef2f2")),
    ]))
    story.append(ec_table)
    story.append(Spacer(1, 10))

    # Legal Analysis Notes
    story.append(Paragraph("<b>ENCUMBRANCE ANALYSIS & DISCLOSURE SUMMARY:</b>",
                           ParagraphStyle("NoteHdr", parent=styles["Normal"], fontName="Helvetica-Bold", fontSize=8, leading=10, textColor=colors.HexColor("#991b1b"))))
    story.append(Paragraph(
        "1. <b>Active Bank Mortgage:</b> Document No. 2105/2021 records a valid first charge in favour of <b>The Federal Bank Ltd</b> "
        "securing credit facilities of ₹45,00,000/-. As on 28-Sep-2024, <b>no Release Deed (ഒഴിവുമുറി) or Satisfaction of Charge</b> has been registered in Book 1.<br/>"
        "2. <b>Title Defect:</b> Any purchaser advancing earnest money without a formal Bank Closure Letter and original title deed release from Federal Bank is exposed to summary SARFAESI recovery proceedings under Section 13(4) of SARFAESI Act, 2002.<br/>"
        "3. <b>Discrepancy in Extent:</b> Partition Deed 892/1998 allotted 10.00 Cents, whereas Sale Deed 1420/2014 conveyed 11.00 Cents (+1.00 Cent extent inflation).",
        ParagraphStyle("NoteBody", parent=styles["Normal"], fontName="Helvetica", fontSize=7.5, leading=10.5, textColor=colors.HexColor("#334155"))
    ))
    story.append(Spacer(1, 10))

    # SRO Digital Signatory Seal
    cert_seal = [
        [
            Paragraph("<b>Digitally Signed By:</b><br/>P. K. MANOJ KUMAR<br/>Sub-Registrar, Aluva SRO<br/>Date: 28-Sep-2024 16:42:10 IST", meta_val),
            Paragraph("<b>Verification QR Code:</b><br/>PEARL-EC-VERIFY-KL-2024-0041982<br/>Scan via <i>pearl.registration.kerala.gov.in</i>", meta_val),
            Paragraph("<b>Statutory Notice:</b><br/>This certificate reflects entries registered in Book 1 only. Physical boundary inspection & revenue records verification mandated.", meta_val),
        ]
    ]
    seal_table = Table(cert_seal, colWidths=[180, 160, 180])
    seal_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
        ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#065f46")),
        ("PADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(seal_table)

    doc.build(story)


def main():
    base_dir = Path(__file__).resolve().parent.parent / "data" / "sample_deeds"
    base_dir.mkdir(parents=True, exist_ok=True)

    deed_pdf = base_dir / "kerala_sale_deed_aluva_re_sy_345_1.pdf"
    ec_pdf = base_dir / "kerala_sro_ec_aluva_30_year_search.pdf"
    compat_deed = base_dir / "sample_aluva_deed.pdf"

    print(f"Generating Kerala Sale Deed PDF -> {deed_pdf}")
    create_kerala_sale_deed_pdf(deed_pdf)

    print(f"Generating Kerala SRO Encumbrance Certificate PDF -> {ec_pdf}")
    create_kerala_sro_ec_pdf(ec_pdf)

    # Also update sample_aluva_deed.pdf with the full authentic version
    print(f"Updating default sample deed -> {compat_deed}")
    create_kerala_sale_deed_pdf(compat_deed)

    print("\n✅ All sample test PDFs successfully generated:")
    for p in [deed_pdf, ec_pdf, compat_deed]:
        size_kb = p.stat().st_size / 1024
        print(f" - {p.name} ({size_kb:.1f} KB)")


if __name__ == "__main__":
    main()
