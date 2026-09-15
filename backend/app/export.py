"""
Export to Document — turns a saved research idea into a downloadable
research-proposal PDF using reportlab (free, pure-Python, no external
service needed).
"""
import os
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib import colors

EXPORT_DIR = os.path.join(os.path.dirname(__file__), "..", "exports")
os.makedirs(EXPORT_DIR, exist_ok=True)


def export_idea_to_pdf(idea: dict) -> str:
    """
    idea: dict with title, problem, approach, required_skills_text, difficulty
    Returns the absolute file path of the generated PDF.
    """
    safe_title = "".join(c if c.isalnum() or c in " -_" else "" for c in idea["title"])[:60]
    file_path = os.path.join(EXPORT_DIR, f"idea_{idea['id']}_{safe_title}.pdf".replace(" ", "_"))

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "ProposalTitle", parent=styles["Title"], textColor=colors.HexColor("#2f49b0")
    )
    heading_style = ParagraphStyle(
        "SectionHeading", parent=styles["Heading2"], textColor=colors.HexColor("#3b5bdb"),
        spaceBefore=14,
    )
    body_style = styles["BodyText"]

    doc = SimpleDocTemplate(file_path, pagesize=LETTER,
                             topMargin=0.9 * inch, bottomMargin=0.9 * inch)
    story = [
        Paragraph("Research Project Proposal", title_style),
        Spacer(1, 6),
        Paragraph(idea["title"], styles["Heading1"]),
        Spacer(1, 12),

        Paragraph("Problem Statement", heading_style),
        Paragraph(idea.get("problem") or "—", body_style),

        Paragraph("Proposed Approach", heading_style),
        Paragraph(idea.get("approach") or "—", body_style),

        Paragraph("Required Skills", heading_style),
        Paragraph(idea.get("required_skills_text") or "—", body_style),

        Paragraph("Difficulty Level", heading_style),
        Paragraph(idea.get("difficulty") or "—", body_style),
    ]
    doc.build(story)
    return file_path
