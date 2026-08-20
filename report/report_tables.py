"""
report_tables.py — Table Builders
====================================
Compact, professional Platypus tables. Used only where a table communicates
better than a chart (per spec: "Do not use a chart if a simple KPI/table
communicates the information better").
"""

from __future__ import annotations
from reportlab.platypus import Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.units import mm

from . import report_layout as _layout
from .report_layout import BORDER, CARD_BG, INK, INK_SOFT, GREEN, RED, WHITE, FONT_REGULAR, FONT_BOLD


def ranking_table(headers: list[str], rows: list[list[str]], col_widths=None,
                   highlight_first_last: bool = True) -> Table:
    data = [headers] + rows
    t = Table(data, colWidths=col_widths, repeatRows=1)
    style = [
        ("BACKGROUND", (0, 0), (-1, 0), _layout.PRIMARY),
        ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
        ("FONTNAME", (0, 0), (-1, 0), FONT_BOLD),
        ("FONTSIZE", (0, 0), (-1, -1), 8.5),
        ("FONTNAME", (0, 1), (-1, -1), FONT_REGULAR),
        ("TEXTCOLOR", (0, 1), (-1, -1), INK),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, CARD_BG]),
        ("GRID", (0, 0), (-1, -1), 0.5, BORDER),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
    ]
    if highlight_first_last and len(rows) > 1:
        style.append(("TEXTCOLOR", (0, 1), (-1, 1), GREEN))
        style.append(("TEXTCOLOR", (0, len(rows)), (-1, len(rows)), RED))
    t.setStyle(TableStyle(style))
    return t


def kpi_row_table(cells: list[tuple], col_widths=None) -> Table:
    """`cells` is a list of (label, value, delta_text_or_None, delta_positive) tuples,
    rendered as a single-row strip of flat KPI tiles."""
    from reportlab.platypus import Paragraph
    from .report_layout import get_styles
    styles = get_styles()

    row = []
    for label, value, delta, positive in cells:
        delta_color = GREEN if positive else RED
        delta_html = f'<font color="{delta_color.hexval()}">{delta}</font>' if delta else ""
        block = [
            Paragraph(label.upper(), styles["KPILabel"]),
            Paragraph(str(value), styles["KPIValue"]),
        ]
        if delta:
            block.append(Paragraph(delta_html, styles["KPIDelta"]))
        row.append(block)

    t = Table([row], colWidths=col_widths)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), CARD_BG),
        ("BOX", (0, 0), (-1, -1), 0.6, BORDER),
        ("INNERGRID", (0, 0), (-1, -1), 0.6, BORDER),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
    ]))
    return t


def checklist_table(checks: list[dict], col_widths=None) -> Table:
    from reportlab.platypus import Paragraph
    from .report_layout import get_styles
    styles = get_styles()
    rows = []
    for c in checks:
        mark = "\u2713" if c["ok"] else "\u26a0"
        color = GREEN.hexval() if c["ok"] else "#D97706"
        rows.append([Paragraph(f'<font color="{color}"><b>{mark}</b></font>', styles["Body"]),
                     Paragraph(c["label"], styles["Body"])])
    t = Table(rows, colWidths=col_widths or [10 * mm, None])
    t.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    return t
