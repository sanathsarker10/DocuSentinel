from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage
from reportlab.lib import colors
from reportlab.lib.units import inch
from xml.sax.saxutils import escape


def create_pdf_report(filename: str, result: dict) -> bytes:
    output = BytesIO()
    doc = SimpleDocTemplate(output, pagesize=letter, rightMargin=45, leftMargin=45, topMargin=45, bottomMargin=45)
    styles = getSampleStyleSheet()
    story = [
        Paragraph("DocuSentinel — Document Screening Report", styles["Title"]),
        Spacer(1, 10),
        Paragraph(f"<b>File:</b> {escape(filename)}", styles["BodyText"]),
        Spacer(1, 6),
        Paragraph(f"<b>Review status:</b> {escape(result['overall_status'])}", styles["BodyText"]),
        Spacer(1, 12),
        Paragraph("Important limitation", styles["Heading2"]),
        Paragraph(
            "This report lists screening indicators only. It does not prove that a document is genuine or forged. "
            "A qualified reviewer should assess findings and verify the document with its issuing authority where possible.",
            styles["BodyText"]
        ),
        Spacer(1, 12),
        Paragraph("Findings", styles["Heading2"]),
    ]
    if not result["findings"]:
        story.append(Paragraph("No issues were flagged by the basic checks. Authenticity remains unverified.", styles["BodyText"]))
    else:
        for i, item in enumerate(result["findings"], 1):
            story.append(Paragraph(f"{i}. {escape(item['title'])} ({escape(item['severity'])})", styles["Heading3"]))
            story.append(Paragraph(escape(item["details"]), styles["BodyText"]))
            story.append(Paragraph(f"<b>Recommended action:</b> {escape(item['recommendation'])}", styles["BodyText"]))
            story.append(Spacer(1, 8))

    story.extend([Spacer(1, 10), Paragraph("Extracted text", styles["Heading2"])])
    text = result["extracted_text"].strip() or "[No text extracted]"
    text = text[:7000].replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("\n", "<br/>")
    story.append(Paragraph(text, styles["Code"]))

    story.append(Spacer(1, 12))
    story.append(Paragraph("Technical metadata", styles["Heading2"]))
    metadata_rows = [["Field", "Value"]]
    for key, value in result["metadata"].items():
        if isinstance(value, dict):
            for subkey, subvalue in value.items():
                metadata_rows.append([str(subkey), str(subvalue)[:250]])
        else:
            metadata_rows.append([str(key), str(value)[:250]])
    table = Table(metadata_rows, colWidths=[2.0 * inch, 4.5 * inch], repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(table)
    doc.build(story)
    return output.getvalue()
