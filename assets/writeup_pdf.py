"""Render writeup.md to a PDF with embedded figures.

Usage: .venv/bin/python -P assets/writeup_pdf.py [writeup.md] [writeup.pdf]
Handles the Markdown subset the writeup uses: headings, paragraphs, bold/italic/code/links,
lists, block quotes, tables, fenced code (ASCII diagrams), images and rules.
"""
import html
import re
import sys
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (Image, KeepTogether, ListFlowable, ListItem, Paragraph, Preformatted,
                                SimpleDocTemplate, Spacer, Table, TableStyle)
from reportlab.lib.fonts import addMapping

ROOT = Path(__file__).resolve().parents[1]
FONTS = "/usr/share/fonts/truetype/dejavu/"
for name, file in [("Body", "DejaVuSans.ttf"), ("Body-Bold", "DejaVuSans-Bold.ttf"), ("Mono", "DejaVuSansMono.ttf")]:
    pdfmetrics.registerFont(TTFont(name, FONTS + file))
# DejaVu Sans ships without an oblique cut here, so italics render upright
addMapping("Body", 0, 0, "Body")
addMapping("Body", 1, 0, "Body-Bold")
addMapping("Body", 0, 1, "Body")
addMapping("Body", 1, 1, "Body-Bold")

INK, MUTED, ACCENT, RULE, FILL = (colors.HexColor(c) for c in ("#1b1b1a", "#5a5955", "#a35f00", "#d9d8d3", "#f4f3ef"))
# glyphs the PDF fonts lack
SYMBOLS = {"✅": "Supported", "❌": "Refuted", "◐": "Partly"}

base = dict(fontName="Body", textColor=INK, alignment=TA_LEFT)


def style(name, **kw):
    return ParagraphStyle(name, **{**base, **kw})


S = {
    "title": style("title", fontSize=22, leading=27, fontName="Body-Bold", spaceAfter=4),
    "h3": style("h3", fontSize=12.5, leading=16, textColor=MUTED, spaceAfter=10),
    "h2": style("h2", fontSize=15, leading=19, fontName="Body-Bold", spaceBefore=14, spaceAfter=6, keepWithNext=1),
    "h3b": style("h3b", fontSize=12, leading=15, fontName="Body-Bold", spaceBefore=10, spaceAfter=4, keepWithNext=1),
    "body": style("body", fontSize=9.6, leading=13.2, spaceAfter=5),
    "quote": style("quote", fontSize=9.8, leading=13.8, leftIndent=10, textColor=INK),
    "cell": style("cell", fontSize=8.2, leading=10.6),
    "cellh": style("cellh", fontSize=8.2, leading=10.6, fontName="Body-Bold"),
    "caption": style("caption", fontSize=8, leading=10, textColor=MUTED, spaceAfter=10),
    "code": ParagraphStyle("code", fontName="Mono", fontSize=6.4, leading=7.8, textColor=INK),
}
WIDTH = A4[0] - 36 * mm


def inline(text):
    """Markdown inline -> ReportLab mini-HTML."""
    for k, v in SYMBOLS.items():
        text = text.replace(k, v)
    text = html.escape(text, quote=False).replace("\\|", "|")
    text = re.sub(r"`([^`]+)`", r'<font name="Mono" size="8.4">\1</font>', text)
    text = re.sub(r"\*\*\[([^\]]+)\]\(([^)]+)\)\*\*", r'<b><link href="\2" color="#a35f00">\1</link></b>', text)
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<link href="\2" color="#a35f00">\1</link>', text)
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])", r"<i>\1</i>", text)
    return text


def table(lines):
    rows = [[c.strip() for c in re.split(r"(?<!\\)\|", l.strip().strip("|"))] for l in lines if not re.match(r"^\|\s*-", l)]
    ncol = len(rows[0])
    data = [[Paragraph(inline(c), S["cellh" if i == 0 else "cell"]) for c in r] for i, r in enumerate(rows)]
    # size columns by their longest cell, within limits
    plain = lambda c: re.sub(r"[*`]", "", "".join(SYMBOLS.get(ch, ch) for ch in c))
    lens = [max(len(plain(r[j])) for r in rows) for j in range(ncol)]
    lens = [min(max(l, 12), 60) for l in lens]
    widths = [WIDTH * l / sum(lens) for l in lens]
    t = Table(data, colWidths=widths, repeatRows=1, hAlign="LEFT")
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), FILL), ("LINEBELOW", (0, 0), (-1, 0), 0.8, MUTED),
        ("LINEBELOW", (0, 1), (-1, -1), 0.4, RULE), ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING", (0, 0), (-1, -1), 4), ("RIGHTPADDING", (0, 0), (-1, -1), 4)]))
    # short tables never split across pages
    return [KeepTogether([t]) if len(rows) <= 10 else t, Spacer(1, 8)]


def image(alt, src):
    path = ROOT / src
    from PIL import Image as PILImage
    w, h = PILImage.open(path).size
    width = WIDTH
    # each chart carries its own title, so no separate caption
    return [Image(str(path), width=width, height=width * h / w), Spacer(1, 10)]


def build(md_path, pdf_path):
    lines = Path(md_path).read_text().splitlines()
    story, i, first_h1 = [], 0, True
    while i < len(lines):
        line = lines[i]
        if line.startswith("```"):
            j = i + 1
            while not lines[j].startswith("```"):
                j += 1
            block = "\n".join(lines[i + 1:j])
            pre = Preformatted(block, S["code"])
            box = Table([[pre]], colWidths=[WIDTH], hAlign="LEFT")
            box.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), FILL), ("BOX", (0, 0), (-1, -1), 0.4, RULE),
                                     ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 6)]))
            story += [KeepTogether([box]), Spacer(1, 8)]
            i = j + 1
        elif line.startswith("|"):
            j = i
            while j < len(lines) and lines[j].startswith("|"):
                j += 1
            story += table(lines[i:j])
            i = j
        elif m := re.match(r"!\[([^\]]*)\]\(([^)]+)\)", line):
            story += image(m.group(1), m.group(2))
            i += 1
        elif line.startswith("# "):
            story.append(Paragraph(inline(line[2:]), S["title"] if first_h1 else S["h2"]))
            first_h1 = False
            i += 1
        elif line.startswith("### ") and len(story) <= 1:
            story.append(Paragraph(inline(line[4:]), S["h3"]))
            i += 1
        elif line.startswith("### "):
            story.append(Paragraph(inline(line[4:]), S["h3b"]))
            i += 1
        elif line.startswith("## "):
            story.append(Paragraph(inline(line[3:]), S["h2"]))
            i += 1
        elif line.startswith("> "):
            q = Table([[Paragraph(inline(line[2:]), S["quote"])]], colWidths=[WIDTH], hAlign="LEFT")
            q.setStyle(TableStyle([("LINEBEFORE", (0, 0), (0, -1), 2.5, ACCENT), ("LEFTPADDING", (0, 0), (-1, -1), 8),
                                   ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4)]))
            story += [q, Spacer(1, 8)]
            i += 1
        elif re.match(r"^(\d+\.|-)\s", line):
            ordered = line[0].isdigit()
            items = []
            while i < len(lines) and re.match(r"^(\d+\.|-)\s", lines[i]):
                items.append(ListItem(Paragraph(inline(re.sub(r"^(\d+\.|-)\s+", "", lines[i])), S["body"]), leftIndent=12))
                i += 1
            story += [ListFlowable(items, bulletType="1" if ordered else "bullet", start=1 if ordered else None, bulletFormat="%s." if ordered else None,
                                   bulletFontName="Body", bulletFontSize=9, leftIndent=14), Spacer(1, 4)]
        elif line.strip() == "---":
            rule = Table([[""]], colWidths=[WIDTH], rowHeights=[2])
            rule.setStyle(TableStyle([("LINEABOVE", (0, 0), (-1, -1), 0.6, RULE)]))
            story += [Spacer(1, 4), rule, Spacer(1, 4)]
            i += 1
        elif line.strip():
            para = [line]
            i += 1
            while i < len(lines) and lines[i].strip() and not re.match(r"^(#|\||>|```|!\[|\d+\.\s|-\s|---)", lines[i]):
                para.append(lines[i])
                i += 1
            story.append(Paragraph(inline(" ".join(para)), S["body"]))
        else:
            i += 1

    # bind every heading to the block after it so headings never end a page
    bound, k = [], 0
    while k < len(story):
        f = story[k]
        if isinstance(f, Paragraph) and f.style.name in ("h2", "h3b") and k + 1 < len(story):
            nxt = story[k + 1]
            # flatten rather than nest KeepTogether, which makes ReportLab break pages early
            bound.append(KeepTogether([f] + (list(nxt._content) if isinstance(nxt, KeepTogether) else [nxt])))
            k += 2
        else:
            bound.append(f)
            k += 1
    story = bound

    def footer(canvas, doc):
        canvas.saveState()
        canvas.setFont("Body", 7.5)
        canvas.setFillColor(MUTED)
        canvas.drawString(18 * mm, 10 * mm, "NFL Big Data Bowl 2027 · Explosiveness Transfers, Smoothness Misleads")
        canvas.drawRightString(A4[0] - 18 * mm, 10 * mm, f"{doc.page}")
        canvas.restoreState()

    doc = SimpleDocTemplate(str(pdf_path), pagesize=A4, leftMargin=18 * mm, rightMargin=18 * mm,
                            topMargin=14 * mm, bottomMargin=16 * mm,
                            title="Explosiveness Transfers, Smoothness Misleads",
                            subject="Rebuilding the Movement Efficiency Index (MEI) with Combine sensor tracking",
                            author="Simphiwe Twala")
    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    print("wrote", pdf_path)


if __name__ == "__main__":
    src = sys.argv[1] if len(sys.argv) > 1 else ROOT / "writeup.md"
    out = sys.argv[2] if len(sys.argv) > 2 else ROOT / "writeup.pdf"
    build(src, out)
