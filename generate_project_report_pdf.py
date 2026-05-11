"""Generate DiffuSVG_Project_Report.pdf from DiffuSVG_Project_Report.md using reportlab."""

import re
from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Preformatted,
    Table, TableStyle, HRFlowable, KeepTogether, PageBreak,
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT

MD  = Path(__file__).parent / "DiffuSVG_Project_Report.md"
OUT = Path(__file__).parent / "DiffuSVG_Project_Report.pdf"

W, H = A4  # 595.27 x 841.89 pts

# ── Styles ────────────────────────────────────────────────────────────────────
base = getSampleStyleSheet()

TITLE = ParagraphStyle("TITLE", parent=base["Normal"],
    fontSize=26, fontName="Helvetica-Bold",
    textColor=colors.HexColor("#1a1a2e"),
    alignment=TA_CENTER, spaceAfter=8)

SUBTITLE = ParagraphStyle("SUBTITLE", parent=base["Normal"],
    fontSize=12, fontName="Helvetica",
    textColor=colors.HexColor("#555555"),
    alignment=TA_CENTER, spaceAfter=4)

H1 = ParagraphStyle("H1", parent=base["Heading1"],
    fontSize=16, fontName="Helvetica-Bold",
    spaceAfter=6, spaceBefore=18,
    textColor=colors.HexColor("#1a1a2e"))

H2 = ParagraphStyle("H2", parent=base["Heading2"],
    fontSize=12, fontName="Helvetica-Bold",
    spaceAfter=5, spaceBefore=14,
    textColor=colors.HexColor("#16213e"),
    backColor=colors.HexColor("#eef2f8"),
    borderPad=4)

H3 = ParagraphStyle("H3", parent=base["Heading3"],
    fontSize=10.5, fontName="Helvetica-BoldOblique",
    spaceAfter=4, spaceBefore=10,
    textColor=colors.HexColor("#0f3460"))

BODY = ParagraphStyle("BODY", parent=base["Normal"],
    fontSize=9.5, leading=14.5, spaceAfter=5,
    textColor=colors.HexColor("#222222"))

CODE_LABEL = ParagraphStyle("CodeLabel", parent=base["Normal"],
    fontSize=7.5, leading=10, textColor=colors.HexColor("#888888"),
    spaceBefore=4, spaceAfter=1)

MONO = ParagraphStyle("Mono", parent=base["Code"],
    fontSize=7.5, leading=10.5, leftIndent=8,
    fontName="Courier", textColor=colors.HexColor("#1e1e1e"),
    backColor=colors.HexColor("#f5f5f5"), spaceAfter=4)

NOTE = ParagraphStyle("Note", parent=base["Normal"],
    fontSize=9, leading=13, leftIndent=14,
    textColor=colors.HexColor("#333333"), spaceAfter=3)

META = ParagraphStyle("Meta", parent=base["Normal"],
    fontSize=9, fontName="Helvetica",
    textColor=colors.HexColor("#777777"),
    alignment=TA_CENTER, spaceAfter=2)


# ── Inline markdown → reportlab XML ──────────────────────────────────────────
def md_inline(text: str) -> str:
    placeholders = {}

    def store_code(m):
        key = f"\x00CODE{len(placeholders)}\x00"
        inner = m.group(1).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        placeholders[key] = f'<font name="Courier" color="#c7254e">{inner}</font>'
        return key

    text = re.sub(r"`([^`]+)`", store_code, text)

    parts = re.split(r"(\x00CODE\d+\x00)", text)
    text = "".join(
        p if p.startswith("\x00CODE") else
        p.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        for p in parts
    )

    text = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"\*([^*\n]+)\*",   r"<i>\1</i>", text)

    for key, val in placeholders.items():
        text = text.replace(key, val)

    return text


# ── GFM table → reportlab Table ──────────────────────────────────────────────
def parse_table(lines):
    rows = []
    for line in lines:
        if re.match(r"^\|[-| :]+\|$", line.strip()):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        rows.append(cells)
    if not rows:
        return None

    col_count = max(len(r) for r in rows)
    col_width  = (W - 4 * cm) / col_count

    table_data = []
    for r_idx, row in enumerate(rows):
        # pad short rows
        while len(row) < col_count:
            row.append("")
        formatted = []
        for cell in row:
            style = ParagraphStyle("TC",
                fontSize=8, leading=11,
                fontName="Helvetica-Bold" if r_idx == 0 else "Helvetica",
                textColor=colors.white if r_idx == 0 else colors.HexColor("#222222"))
            formatted.append(Paragraph(md_inline(cell), style))
        table_data.append(formatted)

    tbl = Table(table_data, colWidths=[col_width] * col_count, repeatRows=1)
    tbl.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, 0),  colors.HexColor("#2c3e50")),
        ("ROWBACKGROUNDS",(0, 1), (-1, -1),
            [colors.HexColor("#f7f9fc"), colors.HexColor("#eef2f8")]),
        ("GRID",          (0, 0), (-1, -1), 0.4, colors.HexColor("#cccccc")),
        ("VALIGN",        (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING",    (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING",   (0, 0), (-1, -1), 6),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 6),
    ]))
    return tbl


# ── Cover page ────────────────────────────────────────────────────────────────
def cover_page():
    elems = []
    elems.append(Spacer(1, 3.5 * cm))

    # Decorative top bar
    elems.append(HRFlowable(width="100%", thickness=4,
        color=colors.HexColor("#1a1a2e"), spaceAfter=18))

    elems.append(Paragraph("DiffuSVG", TITLE))
    elems.append(Paragraph("Text-to-SVG Generation Pipeline", SUBTITLE))

    elems.append(Spacer(1, 0.4 * cm))
    elems.append(HRFlowable(width="60%", thickness=1.5,
        color=colors.HexColor("#4a90d9"), spaceAfter=18))

    elems.append(Paragraph("Full Project Report", ParagraphStyle("CoverSub",
        parent=base["Normal"], fontSize=14, fontName="Helvetica-BoldOblique",
        textColor=colors.HexColor("#4a90d9"), alignment=TA_CENTER, spaceAfter=4)))

    elems.append(Spacer(1, 2.5 * cm))

    meta_style = ParagraphStyle("MetaBlock", parent=base["Normal"],
        fontSize=10, fontName="Helvetica",
        textColor=colors.HexColor("#444444"),
        alignment=TA_CENTER, leading=18)

    elems.append(Paragraph("Author: Ayush Debnath", meta_style))
    elems.append(Paragraph("Date: April 8, 2026", meta_style))
    elems.append(Paragraph("Branch: main", meta_style))

    elems.append(Spacer(1, 3 * cm))
    elems.append(HRFlowable(width="100%", thickness=1,
        color=colors.HexColor("#cccccc"), spaceAfter=0))

    elems.append(PageBreak())
    return elems


# ── Main markdown parser → flowables ─────────────────────────────────────────
def build_story(md_text: str):
    story = []
    lines = md_text.splitlines()
    i = 0

    while i < len(lines):
        line = lines[i]

        # Skip the top-level title line (already on cover page)
        if re.match(r"^# DiffuSVG", line):
            i += 1
            continue

        # Skip the "Date / Author / Branch" meta line
        if re.match(r"^\*\*Date:\*\*", line):
            i += 1
            continue

        # Horizontal rule
        if re.match(r"^---+$", line.strip()):
            story.append(HRFlowable(width="100%", thickness=0.5,
                color=colors.HexColor("#cccccc"), spaceBefore=4, spaceAfter=4))
            i += 1
            continue

        # Headings
        m = re.match(r"^(#{1,3})\s+(.*)", line)
        if m:
            level = len(m.group(1))
            text  = md_inline(m.group(2))
            style = {1: H1, 2: H2, 3: H3}[level]
            p = Paragraph(text, style)
            if level == 1:
                story.append(Spacer(1, 0.1 * cm))
                story.append(HRFlowable(width="100%", thickness=1.5,
                    color=colors.HexColor("#4a90d9"), spaceAfter=4))
            story.append(p)
            i += 1
            continue

        # Fenced code block
        if line.startswith("```"):
            label = line[3:].strip()
            code_lines = []
            i += 1
            while i < len(lines) and not lines[i].startswith("```"):
                code_lines.append(lines[i])
                i += 1
            i += 1
            code_text = "\n".join(code_lines)
            block = []
            if label:
                block.append(Paragraph(label, CODE_LABEL))
            block.append(Preformatted(code_text, MONO,
                maxLineLength=88, newLineChars=""))
            story.append(KeepTogether(block))
            continue

        # Table
        if line.startswith("|"):
            table_lines = []
            while i < len(lines) and lines[i].startswith("|"):
                table_lines.append(lines[i])
                i += 1
            tbl = parse_table(table_lines)
            if tbl:
                story.append(Spacer(1, 0.2 * cm))
                story.append(tbl)
                story.append(Spacer(1, 0.2 * cm))
            continue

        # Blank line
        if not line.strip():
            story.append(Spacer(1, 0.12 * cm))
            i += 1
            continue

        # Bullet (- or *)
        if re.match(r"^[-*]\s+", line):
            text = re.sub(r"^[-*]\s+", "", line)
            story.append(Paragraph("&#8226; " + md_inline(text), NOTE))
            i += 1
            continue

        # Numbered list
        if re.match(r"^\d+\.\s+", line):
            num  = re.match(r"^(\d+)\.", line).group(1)
            text = re.sub(r"^\d+\.\s+", "", line)
            story.append(Paragraph(f"{num}. " + md_inline(text), NOTE))
            i += 1
            continue

        # Normal paragraph
        story.append(Paragraph(md_inline(line), BODY))
        i += 1

    return story


# ── Page numbering ────────────────────────────────────────────────────────────
def _footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 7.5)
    canvas.setFillColor(colors.HexColor("#aaaaaa"))
    canvas.drawCentredString(W / 2, 1.2 * cm, f"DiffuSVG Project Report — Page {doc.page}")
    canvas.restoreState()


# ── Build PDF ─────────────────────────────────────────────────────────────────
def main():
    md_text = MD.read_text(encoding="utf-8")

    doc = SimpleDocTemplate(
        str(OUT),
        pagesize=A4,
        leftMargin=2 * cm, rightMargin=2 * cm,
        topMargin=2 * cm,  bottomMargin=2.2 * cm,
        title="DiffuSVG — Full Project Report",
        author="Ayush Debnath",
        subject="Text-to-SVG generation pipeline",
    )

    story = cover_page() + build_story(md_text)
    doc.build(story, onFirstPage=_footer, onLaterPages=_footer)
    size_kb = OUT.stat().st_size // 1024
    print(f"PDF written -> {OUT}  ({size_kb} KB)")


if __name__ == "__main__":
    main()
