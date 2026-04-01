"""Convert DiffuSVG_Changes.md → DiffuSVG_Changes.pdf using reportlab."""

import re
from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Preformatted,
    Table, TableStyle, HRFlowable, KeepTogether,
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER

MD   = Path(__file__).parent / "DiffuSVG_Changes.md"
OUT  = Path(__file__).parent / "DiffuSVG_Changes.pdf"

# ── Styles ──────────────────────────────────────────────────────────────────
base   = getSampleStyleSheet()

H1 = ParagraphStyle("H1", parent=base["Heading1"],
    fontSize=20, spaceAfter=8, spaceBefore=14, textColor=colors.HexColor("#1a1a2e"))
H2 = ParagraphStyle("H2", parent=base["Heading2"],
    fontSize=14, spaceAfter=6, spaceBefore=14, textColor=colors.HexColor("#16213e"),
    borderPad=4, backColor=colors.HexColor("#f0f4ff"),
    borderColor=colors.HexColor("#4a90d9"), borderWidth=0, leftIndent=0)
H3 = ParagraphStyle("H3", parent=base["Heading3"],
    fontSize=11, spaceAfter=4, spaceBefore=10, textColor=colors.HexColor("#0f3460"))

BODY = ParagraphStyle("Body", parent=base["Normal"],
    fontSize=9.5, leading=14, spaceAfter=6, textColor=colors.HexColor("#222222"))

CODE_LABEL = ParagraphStyle("CodeLabel", parent=base["Normal"],
    fontSize=8, leading=10, textColor=colors.HexColor("#888888"),
    spaceBefore=6, spaceAfter=1)

MONO = ParagraphStyle("Mono", parent=base["Code"],
    fontSize=8, leading=11, leftIndent=8,
    fontName="Courier", textColor=colors.HexColor("#1e1e1e"),
    backColor=colors.HexColor("#f5f5f5"), spaceAfter=4)

NOTE = ParagraphStyle("Note", parent=base["Normal"],
    fontSize=9, leading=13, leftIndent=12,
    textColor=colors.HexColor("#444444"), spaceAfter=4)

# ── Markdown parser → flowables ──────────────────────────────────────────────
def md_inline(text: str) -> str:
    """Convert inline markdown (bold, code, italic) to reportlab XML.

    Process order matters: extract backtick spans first so their content
    (which may contain * or other markers) is never touched by bold/italic regex.
    """
    # 1. Pull out all backtick spans into placeholders
    placeholders = {}
    def store_code(m):
        key = f"\x00CODE{len(placeholders)}\x00"
        inner = m.group(1)
        # Escape XML special chars inside code span
        inner = inner.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        placeholders[key] = f'<font name="Courier" color="#c7254e">{inner}</font>'
        return key
    text = re.sub(r"`([^`]+)`", store_code, text)

    # 2. Escape remaining XML special chars in the non-code parts
    def escape_segment(s):
        return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    parts = re.split(r"(\x00CODE\d+\x00)", text)
    text = "".join(
        p if p.startswith("\x00CODE") else escape_segment(p)
        for p in parts
    )

    # 3. Bold and italic (only outside placeholders — placeholders don't contain * )
    text = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"\*([^*\n]+)\*",   r"<i>\1</i>", text)

    # 4. Restore code placeholders
    for key, val in placeholders.items():
        text = text.replace(key, val)

    return text


def parse_table(lines: list[str]):
    """Parse a GFM table into a reportlab Table."""
    rows = []
    for line in lines:
        if re.match(r"^\|[-| :]+\|$", line.strip()):
            continue  # separator row
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        rows.append(cells)
    if not rows:
        return None

    # Style header row differently
    col_count = len(rows[0])
    col_width  = (A4[0] - 4*cm) / col_count

    table_data = []
    for r_idx, row in enumerate(rows):
        formatted = []
        for cell in row:
            style = ParagraphStyle("TC",
                fontSize=8.5, leading=11,
                fontName="Helvetica-Bold" if r_idx == 0 else "Helvetica",
                textColor=colors.white if r_idx == 0 else colors.HexColor("#222222"))
            formatted.append(Paragraph(md_inline(cell), style))
        table_data.append(formatted)

    tbl = Table(table_data, colWidths=[col_width] * col_count, repeatRows=1)
    tbl.setStyle(TableStyle([
        ("BACKGROUND",  (0, 0), (-1, 0),  colors.HexColor("#2c3e50")),
        ("BACKGROUND",  (0, 1), (-1, -1), colors.HexColor("#fdfdfd")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1),
            [colors.HexColor("#f7f9fc"), colors.HexColor("#eef2f8")]),
        ("GRID",        (0, 0), (-1, -1), 0.4, colors.HexColor("#cccccc")),
        ("VALIGN",      (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING",  (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING",(0,0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
    ]))
    return tbl


def build_story(md_text: str):
    story = []
    lines = md_text.splitlines()
    i = 0

    while i < len(lines):
        line = lines[i]

        # ── Heading ──
        m = re.match(r"^(#{1,3})\s+(.*)", line)
        if m:
            level = len(m.group(1))
            text  = md_inline(m.group(2))
            style = {1: H1, 2: H2, 3: H3}[level]
            p = Paragraph(text, style)
            if level == 1:
                story.append(Spacer(1, 0.15*cm))
                story.append(HRFlowable(width="100%", thickness=1.5,
                    color=colors.HexColor("#4a90d9"), spaceAfter=4))
            story.append(p)
            i += 1
            continue

        # ── Fenced code block ──
        if line.startswith("```"):
            label = line[3:].strip()
            code_lines = []
            i += 1
            while i < len(lines) and not lines[i].startswith("```"):
                code_lines.append(lines[i])
                i += 1
            i += 1  # skip closing ```
            code_text = "\n".join(code_lines)
            block = []
            if label:
                block.append(Paragraph(label, CODE_LABEL))
            block.append(Preformatted(code_text, MONO,
                maxLineLength=90, newLineChars=""))
            story.append(KeepTogether(block))
            continue

        # ── Table ──
        if line.startswith("|"):
            table_lines = []
            while i < len(lines) and lines[i].startswith("|"):
                table_lines.append(lines[i])
                i += 1
            tbl = parse_table(table_lines)
            if tbl:
                story.append(Spacer(1, 0.2*cm))
                story.append(tbl)
                story.append(Spacer(1, 0.2*cm))
            continue

        # ── Horizontal rule ──
        if re.match(r"^---+$", line.strip()):
            story.append(HRFlowable(width="100%", thickness=0.5,
                color=colors.HexColor("#cccccc"), spaceBefore=4, spaceAfter=4))
            i += 1
            continue

        # ── Blank line ──
        if not line.strip():
            story.append(Spacer(1, 0.15*cm))
            i += 1
            continue

        # ── Bullet ──
        if re.match(r"^[-*]\s+", line):
            text = re.sub(r"^[-*]\s+", "", line)
            story.append(Paragraph("• " + md_inline(text), NOTE))
            i += 1
            continue

        # ── Numbered list ──
        if re.match(r"^\d+\.\s+", line):
            text = re.sub(r"^\d+\.\s+", "", line)
            num  = re.match(r"^(\d+)\.", line).group(1)
            story.append(Paragraph(f"{num}. " + md_inline(text), NOTE))
            i += 1
            continue

        # ── Normal paragraph ──
        story.append(Paragraph(md_inline(line), BODY))
        i += 1

    return story


# ── Build PDF ────────────────────────────────────────────────────────────────
def main():
    md_text = MD.read_text(encoding="utf-8")

    doc = SimpleDocTemplate(
        str(OUT),
        pagesize=A4,
        leftMargin=2*cm, rightMargin=2*cm,
        topMargin=2*cm,  bottomMargin=2*cm,
        title="DiffuSVG Pipeline — Changes & Rationale",
        author="DiffuSVG",
    )

    story = build_story(md_text)
    doc.build(story)
    print(f"PDF written -> {OUT}  ({OUT.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
