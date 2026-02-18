"""
Label generation for Avery 5167 sheets (4 cols × 20 rows = 80 labels/sheet).
Label size: 1.75" × 0.5"
"""

import io
from typing import List, Tuple

import pandas as pd
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.pdfgen import canvas


# Avery 5167 layout constants
LABEL_W = 1.75 * inch
LABEL_H = 0.5 * inch
COLS = 4
ROWS = 20
LEFT_MARGIN = 0.3 * inch
TOP_MARGIN = 0.5 * inch
H_GAP = 0.31 * inch  # horizontal gap between columns

FONT_NAME = 'STSong-Light'
FONT_SIZE = 8


def _register_font():
    try:
        pdfmetrics.registerFont(UnicodeCIDFont(FONT_NAME))
    except Exception:
        pass  # font may already be registered


def _build_label_text(item_short_zh: str, item_id: int) -> str:
    """Format a single label: [id]  short_zh"""
    return f"[{item_id}]  {item_short_zh}"


def generate_labels_pdf(sorted_items: List[Tuple[str, int]], menu_df: pd.DataFrame) -> bytes:
    """
    Generate an Avery 5167 label sheet PDF.

    Args:
        sorted_items: List of (item_zh, quantity) tuples from DeliveryOrderAnalyzer.analyze()
        menu_df: DataFrame loaded from data/menu.csv with columns id, item_zh, item_short_zh, item_en

    Returns:
        PDF bytes
    """
    _register_font()

    # Build lookup: item_zh -> (id, item_short_zh)
    lookup = {
        row['item_zh']: (row['id'], row['item_short_zh'])
        for _, row in menu_df.iterrows()
    }

    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=letter)
    page_w, page_h = letter

    label_index = 0

    for item_zh, quantity in sorted_items:
        if item_zh not in lookup:
            continue
        item_id, item_short_zh = lookup[item_zh]

        # Repeat label once per item ordered (quantity copies)
        for _ in range(quantity):
            col = label_index % COLS
            row = (label_index // COLS) % ROWS

            if label_index > 0 and label_index % (COLS * ROWS) == 0:
                c.showPage()

            x = LEFT_MARGIN + col * (LABEL_W + H_GAP)
            # ReportLab y=0 is bottom; convert from top-down
            y = page_h - TOP_MARGIN - (row + 1) * LABEL_H

            # Center text vertically within the label
            c.setFont(FONT_NAME, FONT_SIZE)
            text = _build_label_text(item_short_zh, item_id)
            text_y = y + (LABEL_H - FONT_SIZE) / 2
            c.drawString(x + 4, text_y, text)

            label_index += 1

    c.save()
    return buf.getvalue()
