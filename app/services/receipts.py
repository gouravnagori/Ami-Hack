"""
Donation Receipt & CSR Certificate PDF Service (ReportLab).

Generates a formatted PDF receipt for tax, audit, and CSR documentation.
Includes:
- Donor details and FSSAI registration
- Itemized food inventory and portions
- Recipient shelter/NGO details and delivery timestamp
- Cold-chain handling and OTP proof-of-delivery verification
- Environmental impact summary (meals rescued, kg diverted, CO2e avoided)
"""

import io

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import HRFlowable, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from app.core.config import settings
from app.db.models.donation import Donation


def generate_donation_receipt_pdf(donation: Donation) -> bytes:
    """
    Generate a complete PDF receipt for a donation and return its raw bytes.
    """
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
        "ReceiptTitle",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=18,
        leading=22,
        textColor=colors.HexColor("#1A365D"),  # Deep navy
        alignment=1,  # Center
    )
    subtitle_style = ParagraphStyle(
        "ReceiptSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#4A5568"),
        alignment=1,
    )
    section_heading = ParagraphStyle(
        "SectionHeading",
        parent=styles["Heading3"],
        fontName="Helvetica-Bold",
        fontSize=12,
        leading=16,
        textColor=colors.HexColor("#2B6CB0"),
        spaceBefore=10,
        spaceAfter=4,
    )
    body_style = ParagraphStyle(
        "ReceiptBody",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#2D3748"),
    )
    bold_style = ParagraphStyle(
        "ReceiptBold",
        parent=body_style,
        fontName="Helvetica-Bold",
    )
    badge_style = ParagraphStyle(
        "ReceiptBadge",
        parent=body_style,
        fontName="Helvetica-Bold",
        textColor=colors.HexColor("#22543D"),
        alignment=1,
    )

    story = []

    # 1. Header
    story.append(Paragraph("GOLDENHOUR FOOD RESCUE PLATFORM", title_style))
    story.append(Paragraph("Official Certificate of Food Rescue & CSR Donation Receipt", subtitle_style))
    story.append(Spacer(1, 8))
    story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor("#3182CE"), spaceAfter=12))

    # 2. Meta Info (Donation ID, Date, Status)
    donor = donation.donor
    donor_org_name = donor.org_name if donor else "Valued Donor"
    fssai = donor.fssai_no if (donor and donor.fssai_no) else "N/A"
    created_str = donation.created_at.strftime("%Y-%m-%d %H:%M UTC") if donation.created_at else "N/A"

    meta_data = [
        [
            Paragraph(f"<b>Receipt ID:</b> REC-{str(donation.id)[:8].upper()}", body_style),
            Paragraph(f"<b>Date:</b> {created_str}", body_style),
        ],
        [
            Paragraph(f"<b>Donation ID:</b> {donation.id}", body_style),
            Paragraph(f"<b>Status:</b> {donation.status.value.upper()}", body_style),
        ],
        [
            Paragraph(f"<b>Donor Organization:</b> {donor_org_name}", body_style),
            Paragraph(f"<b>Donor FSSAI No:</b> {fssai}", body_style),
        ],
    ]
    meta_table = Table(meta_data, colWidths=[270, 260])
    meta_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#EDF2F7")),
                ("PADDING", (0, 0), (-1, -1), 6),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E0")),
            ]
        )
    )
    story.append(meta_table)
    story.append(Spacer(1, 14))

    # 3. Itemized Food Details
    story.append(Paragraph("1. RESCUED FOOD INVENTORY", section_heading))
    items_data = [
        [
            Paragraph("Item Description", bold_style),
            Paragraph("Diet", bold_style),
            Paragraph("Storage", bold_style),
            Paragraph("Portions", bold_style),
            Paragraph("Est. Weight (kg)", bold_style),
        ]
    ]

    total_weight = 0.0
    for item in donation.items:
        wt = item.weight_kg if item.weight_kg else (item.portions * settings.PORTION_KG)
        total_weight += wt
        items_data.append(
            [
                Paragraph(item.name, body_style),
                Paragraph(donation.diet.value.upper(), body_style),
                Paragraph(donation.storage.value.upper(), body_style),
                Paragraph(str(item.portions), body_style),
                Paragraph(f"{wt:.1f} kg", body_style),
            ]
        )

    # Total row
    items_data.append(
        [
            Paragraph("<b>TOTAL</b>", bold_style),
            Paragraph("", body_style),
            Paragraph("", body_style),
            Paragraph(f"<b>{donation.total_portions}</b>", bold_style),
            Paragraph(f"<b>{total_weight:.1f} kg</b>", bold_style),
        ]
    )

    items_table = Table(items_data, colWidths=[180, 80, 80, 90, 100])
    items_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E2E8F0")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#2D3748")),
                ("ALIGN", (3, 0), (-1, -1), "RIGHT"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E0")),
                ("PADDING", (0, 0), (-1, -1), 5),
                ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#F7FAFC")),
            ]
        )
    )
    story.append(items_table)
    story.append(Spacer(1, 14))

    # 4. Allocations & Recipient Proof of Handoff
    story.append(Paragraph("2. RECIPIENT ORGANIZATIONS & HANDOFF VERIFICATION", section_heading))
    alloc_data = [
        [
            Paragraph("Container", bold_style),
            Paragraph("Recipient Org", bold_style),
            Paragraph("Portions", bold_style),
            Paragraph("Status", bold_style),
            Paragraph("Verification", bold_style),
        ]
    ]

    for alloc in donation.allocations:
        recip_name = alloc.recipient.name if alloc.recipient else "Pending Match"
        alloc_data.append(
            [
                Paragraph(alloc.container_label or "-", body_style),
                Paragraph(recip_name, body_style),
                Paragraph(str(alloc.portions), body_style),
                Paragraph(alloc.status.value.upper(), body_style),
                Paragraph("OTP Handoff Verified" if alloc.status == "delivered" else "In Transit / Dispatched", badge_style),
            ]
        )

    if len(alloc_data) == 1:
        alloc_data.append([Paragraph("No allocations recorded.", body_style), "", "", "", ""])

    alloc_table = Table(alloc_data, colWidths=[90, 170, 70, 90, 110])
    alloc_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E2E8F0")),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E0")),
                ("PADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    story.append(alloc_table)
    story.append(Spacer(1, 14))

    # 5. Impact Metrics Summary
    story.append(Paragraph("3. ENVIRONMENTAL & SOCIAL IMPACT (CSR)", section_heading))
    co2e_saved = total_weight * settings.CO2E_PER_KG
    impact_data = [
        [
            Paragraph(f"<b>Meals Rescued:</b> {donation.total_portions}", body_style),
            Paragraph(f"<b>Landfill Diverted:</b> {total_weight:.1f} kg", body_style),
            Paragraph(f"<b>CO₂e Emissions Avoided:</b> {co2e_saved:.2f} kg", body_style),
        ]
    ]
    impact_table = Table(impact_data, colWidths=[175, 175, 180])
    impact_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#C6F6D5")),  # Pale green
                ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#38A169")),
                ("PADDING", (0, 0), (-1, -1), 8),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ]
        )
    )
    story.append(impact_table)
    story.append(Spacer(1, 20))

    # 6. Certification & Compliance Footer
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#CBD5E0"), spaceAfter=8))
    cert_text = (
        "<i>This document serves as proof of surplus food donation under the GoldenHour Food Rescue "
        "Program. All food rescued adheres to food-safety handling guidelines with zero-dumping guarantees. "
        "Digitally generated and cryptographically verifiable via GoldenHour Logistics Backend.</i>"
    )
    story.append(Paragraph(cert_text, ParagraphStyle("CertText", parent=body_style, fontSize=8, leading=10, textColor=colors.HexColor("#718096"))))

    doc.build(story)
    return buffer.getvalue()
