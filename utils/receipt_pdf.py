"""Sale receipt PDF (FR-5.6): A5, Devanagari-capable via bundled Noto font."""

from __future__ import annotations

from io import BytesIO
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A5
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

FONT_PATH = Path(__file__).resolve().parent.parent / "assets" / "NotoSansDevanagari-Regular.ttf"
FONT_NAME = "NotoDevanagari"

SHOP_NAME_DEV = "\u0938\u0902\u0938\u094d\u0915\u0943\u0924 \u0938\u093e\u0939\u093f\u0924\u094d\u092f \u0930\u0924\u094d\u0928\u093e\u0915\u0930"
SHOP_NAME_ROMAN = "Sanskrit Sahitya Ratnakar"


def _font() -> str:
    """Register the Devanagari TTF once; fall back to Helvetica if missing."""
    if FONT_NAME in pdfmetrics.getRegisteredFontNames():
        return FONT_NAME
    if FONT_PATH.exists():
        pdfmetrics.registerFont(TTFont(FONT_NAME, str(FONT_PATH)))
        return FONT_NAME
    return "Helvetica"


def _rs(paise: int) -> str:
    # "Rs." instead of the rupee glyph: guaranteed to render in any font.
    sign = "-" if paise < 0 else ""
    return f"{sign}Rs. {abs(paise) / 100:,.2f}"


def build_receipt_pdf(sale: dict, items: list[dict]) -> bytes:
    """Render a sale receipt. `sale` is a header dict from sale_service.list_sales;
    `items` from sale_service.get_sale_items."""
    font = _font()
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A5,
        leftMargin=12 * mm, rightMargin=12 * mm, topMargin=12 * mm, bottomMargin=12 * mm,
        title=f"Receipt #{sale['id']}")

    h1 = ParagraphStyle("h1", fontName=font, fontSize=14, alignment=1, leading=18)
    h2 = ParagraphStyle("h2", fontName=font, fontSize=10, alignment=1, leading=13)
    body = ParagraphStyle("body", fontName=font, fontSize=9, leading=12)
    cell = ParagraphStyle("cell", fontName=font, fontSize=8.5, leading=11)

    story = [
        Paragraph(SHOP_NAME_DEV, h1),
        Paragraph(SHOP_NAME_ROMAN, h2),
        Spacer(1, 4 * mm),
        Paragraph(
            f"Receipt No: <b>{sale['id']}</b> &nbsp;&nbsp; Date: {sale['sale_date']}"
            f" &nbsp;&nbsp; Type: {sale['sale_type'].capitalize()}", body),
    ]
    if sale.get("customer_name"):
        story.append(Paragraph(f"Customer: {sale['customer_name']}", body))
    story.append(Paragraph(
        f"Payment: {sale.get('payment_method', 'cash').upper()}"
        f" &nbsp;&nbsp; Served by: {sale.get('created_by_name', '')}", body))
    story.append(Spacer(1, 4 * mm))

    data = [["#", "Book", "Qty", "Rate", "Amount"]]
    for n, item in enumerate(items, start=1):
        title = Paragraph(
            f"{item['title_devanagari']}<br/>{item['title_roman']}", cell)
        data.append([str(n), title, str(item["quantity"]),
                     _rs(item["unit_price"]), _rs(item["line_total"])])

    subtotal = sum(i["line_total"] for i in items)
    data.append(["", "", "", "Subtotal", _rs(subtotal)])
    if sale.get("discount"):
        data.append(["", "", "", "Discount", "- " + _rs(sale["discount"])])
    data.append(["", "", "", "TOTAL", _rs(sale["total_amount"])])

    table = Table(data, colWidths=[8 * mm, 58 * mm, 12 * mm, 23 * mm, 25 * mm])
    table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), font),
        ("FONTSIZE", (0, 0), (-1, -1), 8.5),
        ("LINEBELOW", (0, 0), (-1, 0), 0.7, colors.black),
        ("LINEABOVE", (0, len(items) + 1), (-1, len(items) + 1), 0.4, colors.black),
        ("ALIGN", (2, 0), (-1, -1), "RIGHT"),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("FONTSIZE", (3, -1), (-1, -1), 9.5),
    ]))
    story.append(table)

    if sale.get("notes"):
        story.append(Spacer(1, 3 * mm))
        story.append(Paragraph(f"Notes: {sale['notes']}", body))
    story.append(Spacer(1, 6 * mm))
    story.append(Paragraph("\u0927\u0928\u094d\u092f\u0935\u093e\u0926\u0903 | Thank you!", h2))

    doc.build(story)
    return buffer.getvalue()
