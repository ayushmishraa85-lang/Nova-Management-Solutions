"""
report_templates_notebook.py — Notebook / Lab Report Page Builders
========================================================================
Mirrors the reference format: Title + Objective -> Data Cleaning Process ->
a sequence of [Chart, "Interpretation:" paragraph] blocks -> Conclusion.
No code cells are shown (chart + interpretation only, per the chosen style).
"""

from __future__ import annotations
from reportlab.platypus import Paragraph, Spacer, Image, PageBreak, Table, TableStyle, HRFlowable
from reportlab.lib.units import mm

from . import report_layout as _layout
from .report_layout import LAZY_STYLES, BORDER, CARD_BG, INK, MUTED, GREEN, RED, FONT_BOLD, FONT_REGULAR
from .report_tables import checklist_table

S = LAZY_STYLES
CONTENT_WIDTH = 174 * mm


def title_objective_page(dataset_name: str, objective_text: str) -> list:
    flow = []
    flow.append(Spacer(1, 8 * mm))
    flow.append(Paragraph(f"{dataset_name} Analysis", S["CoverTitle"]))
    flow.append(Spacer(1, 4 * mm))
    flow.append(HRFlowable(width=CONTENT_WIDTH, thickness=0.75, color=BORDER))
    flow.append(Spacer(1, 6 * mm))
    flow.append(Paragraph("Objective", S["SectionHeading"]))
    flow.append(Paragraph(objective_text, S["Body"]))
    flow.append(Spacer(1, 6 * mm))
    return flow


def data_cleaning_page(doc, cleaning: dict) -> list:
    flow = []
    doc.section_no += 1
    flow.append(Paragraph(f'<font color="{_layout.PRIMARY.hexval()}">{doc.section_no:02d}</font>&nbsp;&nbsp;Data Cleaning Process',
                           S["SectionHeading"]))
    flow.append(Spacer(1, 3 * mm))

    rows = [
        ["Rows (before cleaning)", f"{cleaning['rows_before']:,}"],
        ["Columns", f"{cleaning['cols_before']}"],
        ["Duplicate records", f"{cleaning['duplicates']:,}"],
        ["Rows after removing missing values", f"{cleaning['rows_after']:,}"],
    ]
    t = Table(rows, colWidths=[85 * mm, 89 * mm])
    t.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (0, -1), FONT_BOLD),
        ("FONTNAME", (1, 0), (1, -1), FONT_REGULAR),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("TEXTCOLOR", (0, 0), (0, -1), MUTED),
        ("TEXTCOLOR", (1, 0), (1, -1), INK),
        ("BACKGROUND", (0, 0), (-1, -1), CARD_BG),
        ("BOX", (0, 0), (-1, -1), 0.5, BORDER),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, BORDER),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
    ]))
    flow.append(t)
    flow.append(Spacer(1, 4 * mm))

    checks = [
        dict(ok=cleaning["duplicates"] == 0,
             label="No duplicate records found" if cleaning["duplicates"] == 0
             else f"{cleaning['duplicates']:,} duplicate record(s) detected"),
        dict(ok=len(cleaning["missing_by_col"]) == 0,
             label="No missing values found" if not cleaning["missing_by_col"]
             else f"Missing values found in {len(cleaning['missing_by_col'])} column(s) "
                  f"({', '.join(list(cleaning['missing_by_col'].keys())[:5])}"
                  f"{'...' if len(cleaning['missing_by_col']) > 5 else ''}) — rows with missing "
                  f"values were removed"),
        dict(ok=True, label=f"Data types validated across all {cleaning['cols_before']} columns"),
    ]
    flow.append(checklist_table(checks, col_widths=[10 * mm, CONTENT_WIDTH - 10 * mm]))
    flow.append(PageBreak())
    return flow


def chart_interpretation_block(doc, image_buf, chart_title: str, interpretation: str,
                                 image_width_frac: float = 1.0, new_section: bool = False) -> list:
    """The core recurring unit of this report style: a chart followed by an
    explicit 'Interpretation:' paragraph, matching the reference format."""
    flow = []
    if new_section:
        doc.section_no += 1
        flow.append(Paragraph(f'<font color="{_layout.PRIMARY.hexval()}">{doc.section_no:02d}</font>&nbsp;&nbsp;{chart_title}',
                               S["SectionHeading"]))
        flow.append(Spacer(1, 2 * mm))
    img_w = CONTENT_WIDTH * image_width_frac
    flow.append(Image(image_buf, width=img_w, height=img_w * 0.62))
    flow.append(Spacer(1, 3 * mm))
    flow.append(Paragraph("Interpretation:", S["SubHeading"]))
    flow.append(Paragraph(interpretation, S["Body"]))
    flow.append(Spacer(1, 6 * mm))
    return flow


def conclusion_page(doc, conclusion_text: str) -> list:
    flow = []
    doc.section_no += 1
    flow.append(Paragraph(f'<font color="{_layout.PRIMARY.hexval()}">{doc.section_no:02d}</font>&nbsp;&nbsp;Conclusion',
                           S["SectionHeading"]))
    flow.append(Spacer(1, 3 * mm))
    flow.append(Paragraph(conclusion_text, S["Body"]))
    return flow
