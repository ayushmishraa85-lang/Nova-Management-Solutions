"""
report_templates.py — Page/Section Builders
==============================================
Each function takes the validated ReportMetrics (+ Schema, + options) and
returns a list of Platypus flowables for one report section. A section that
the data can't honestly support returns an EMPTY list rather than a
placeholder — report_export.py skips empty sections entirely so the PDF
never shows a hollow page (per spec: "If a field doesn't exist, DO NOT
generate an empty section").
"""

from __future__ import annotations
from datetime import datetime
import pandas as pd

from reportlab.platypus import (
    Paragraph, Spacer, Table, TableStyle, Image, PageBreak, HRFlowable, KeepTogether
)
from reportlab.lib.units import mm
from reportlab.lib import colors

from . import report_layout as _layout
from .report_layout import (
    LAZY_STYLES, BORDER, CARD_BG, INK, INK_SOFT, MUTED,
    GREEN, GREEN_TINT, RED, RED_TINT, AMBER, AMBER_TINT, WHITE,
    fmt_currency, fmt_number, fmt_pct,
)
from .report_metrics import ReportMetrics, KPI
from .report_schema import Schema
from . import report_charts as charts
from .report_tables import ranking_table, kpi_row_table, checklist_table

S = LAZY_STYLES
CONTENT_WIDTH = 174 * mm  # A4 minus margins


def _section_title(doc, title: str):
    doc.section_no += 1
    return Paragraph(f'<font color="{_layout.PRIMARY.hexval()}">{doc.section_no:02d}</font>&nbsp;&nbsp;{title}',
                      S["SectionHeading"])


def _fmt_kpi_value(kpi: KPI) -> str:
    if kpi.is_percent:
        return fmt_pct(kpi.current)
    if kpi.is_currency:
        return fmt_currency(kpi.current)
    return fmt_number(kpi.current)


def _kpi_row_flowables(cells: list, max_per_row: int = 4):
    """Chunks KPI cells into rows of at most `max_per_row` so tiles stay
    wide enough to hold currency values without wrapping awkwardly."""
    flows = []
    for i in range(0, len(cells), max_per_row):
        chunk = cells[i:i + max_per_row]
        col_w = CONTENT_WIDTH / len(chunk)
        flows.append(kpi_row_table(chunk, col_widths=[col_w] * len(chunk)))
        flows.append(Spacer(1, 3 * mm))
    return flows


def _kpi_cells(m: ReportMetrics, keys: list[str]):
    cells = []
    for k in keys:
        kpi = m.kpis.get(k)
        if not kpi:
            continue
        delta_text, positive = None, True
        if kpi.change_pct is not None:
            positive = kpi.change_pct >= 0
            arrow = "\u2191" if positive else "\u2193"
            delta_text = f"{arrow} {abs(kpi.change_pct):.1f}% vs prior period"
        cells.append((kpi.label, _fmt_kpi_value(kpi), delta_text, positive))
    return cells


# ══════════════════════════════════════════════════════════════════════════
# PAGE 1 — COVER
# ══════════════════════════════════════════════════════════════════════════

def cover_page(dataset_name: str, report_type: str, company_name: str | None,
                period_label: str | None) -> list:
    flow = []
    flow.append(Spacer(1, 40 * mm))
    # Brand mark
    from reportlab.platypus import Table as _T
    mark = _T([[Paragraph('<font color="white"><b>N</b></font>', S["CoverTitle"])]], colWidths=[16*mm], rowHeights=[16*mm])
    mark.setStyle(TableStyle([("BACKGROUND", (0,0), (-1,-1), _layout.PRIMARY), ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
                               ("ALIGN", (0,0), (-1,-1), "CENTER")]))
    flow.append(mark)
    flow.append(Spacer(1, 10 * mm))
    flow.append(Paragraph(report_type.upper(), S["CoverKicker"]))
    flow.append(Paragraph(f"{dataset_name}", S["CoverTitle"]))
    flow.append(Spacer(1, 4 * mm))
    sub_bits = []
    if company_name:
        sub_bits.append(company_name)
    sub_bits.append(period_label or "Full dataset period")
    flow.append(Paragraph(" \u00b7 ".join(sub_bits), S["CoverSub"]))
    flow.append(Spacer(1, 30 * mm))
    flow.append(HRFlowable(width=CONTENT_WIDTH, thickness=0.75, color=BORDER))
    flow.append(Spacer(1, 4 * mm))
    meta_table = Table(
        [["Report Generated", datetime.now().strftime("%d %B %Y, %H:%M")],
         ["Prepared By", "NovaMS \u2014 Nova Management Solutions"],
         ["Report Type", report_type]],
        colWidths=[45 * mm, CONTENT_WIDTH - 45 * mm],
    )
    meta_table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("TEXTCOLOR", (0, 0), (0, -1), MUTED),
        ("TEXTCOLOR", (1, 0), (1, -1), INK),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    flow.append(meta_table)
    flow.append(PageBreak())
    return flow


# ══════════════════════════════════════════════════════════════════════════
# PAGE 2 — EXECUTIVE SUMMARY
# ══════════════════════════════════════════════════════════════════════════

def executive_summary_page(doc, m: ReportMetrics) -> list:
    if not m.kpis:
        return []
    flow = [_section_title(doc, "Executive Summary"), Spacer(1, 4 * mm)]

    key_order = ["revenue", "profit", "orders", "aov", "margin", "growth"]
    cells = _kpi_cells(m, key_order)
    if cells:
        flow.extend(_kpi_row_flowables(cells))
        flow.append(Spacer(1, 5 * mm))

    if m.highlights:
        flow.append(Paragraph("Executive Highlights", S["SubHeading"]))
        for h in m.highlights:
            flow.append(Paragraph(f"\u2022 {h}", S["Bullet"]))
    flow.append(PageBreak())
    return flow


# ══════════════════════════════════════════════════════════════════════════
# PAGE 3 — BUSINESS PERFORMANCE (trend)
# ══════════════════════════════════════════════════════════════════════════

def business_performance_page(doc, m: ReportMetrics) -> list:
    if m.trend is None or len(m.trend) < 2:
        return []
    flow = [_section_title(doc, "Business Performance"), Spacer(1, 4 * mm)]

    labels = [str(i) for i in m.trend.index]
    values = list(m.trend.values)
    buf = charts.line_trend_chart(labels, values, "Revenue Trend Over Time", y_label="Revenue")
    flow.append(Image(buf, width=CONTENT_WIDTH, height=CONTENT_WIDTH * (2.6 / 6.4)))

    first_half = sum(values[: len(values) // 2]) or 1
    second_half = sum(values[len(values) // 2:])
    accel = (second_half - first_half) / abs(first_half) * 100
    trend_note = (
        f"Revenue {'accelerated' if accel > 5 else 'declined' if accel < -5 else 'held steady'} "
        f"through the back half of the reporting period "
        f"({'up' if accel >= 0 else 'down'} {abs(accel):.1f}% vs. the first half)."
    )
    flow.append(Spacer(1, 3 * mm))
    flow.append(Paragraph("Interpretation:", S["SubHeading"]))
    flow.append(Paragraph(trend_note, S["Body"]))

    orders_kpi = m.kpis.get("orders")
    profit_kpi = m.kpis.get("profit")
    if orders_kpi or profit_kpi:
        flow.append(Spacer(1, 5 * mm))
        cells = _kpi_cells(m, ["orders", "profit", "growth"])
        if cells:
            flow.extend(_kpi_row_flowables(cells))
    flow.append(PageBreak())
    return flow


# ══════════════════════════════════════════════════════════════════════════
# PAGE 4 — REGIONAL / GEOGRAPHIC
# ══════════════════════════════════════════════════════════════════════════

def regional_page(doc, m: ReportMetrics) -> list:
    if m.top_regions is None or m.top_regions.empty:
        return []
    flow = [_section_title(doc, "Regional Performance"), Spacer(1, 4 * mm)]

    top = m.top_regions.head(10)
    buf = charts.horizontal_ranking_chart(
        [str(i) for i in top.index], list(top.values), "Revenue by Region", x_label="Revenue"
    )
    flow.append(Image(buf, width=CONTENT_WIDTH, height=CONTENT_WIDTH * (buf and 0.5 or 0.5)))

    rows = []
    total = m.top_regions.sum() or 1
    for region, val in top.items():
        share = val / total * 100
        growth_txt = "\u2014"
        if m.top_regions_prev is not None and region in m.top_regions_prev.index:
            prev_val = m.top_regions_prev[region]
            if prev_val:
                growth_txt = fmt_pct((val - prev_val) / abs(prev_val) * 100, signed=True)
        rows.append([str(region), fmt_currency(val), f"{share:.1f}%", growth_txt])

    flow.append(Spacer(1, 4 * mm))
    flow.append(ranking_table(["Region", "Revenue", "Share", "vs Prior Period"], rows,
                               col_widths=[55*mm, 40*mm, 30*mm, 49*mm]))

    best, worst = top.index[0], top.index[-1]
    flow.append(Spacer(1, 4 * mm))
    flow.append(Paragraph("Interpretation:", S["SubHeading"]))
    flow.append(Paragraph(
        f"<b>{best}</b> is the strongest performing region; <b>{worst}</b> is the weakest "
        f"and represents the clearest opportunity for targeted promotions.", S["Body"]
    ))
    flow.append(PageBreak())
    return flow


# ══════════════════════════════════════════════════════════════════════════
# PAGE 5 — PRODUCT / CATEGORY
# ══════════════════════════════════════════════════════════════════════════

def product_page(doc, m: ReportMetrics) -> list:
    if (m.top_products is None or m.top_products.empty) and (m.top_categories is None or m.top_categories.empty):
        return []
    flow = [_section_title(doc, "Product & Category Performance"), Spacer(1, 4 * mm)]

    if m.top_products is not None and not m.top_products.empty:
        top = m.top_products.head(min(10, len(m.top_products)))
        if len(top) > 6:
            buf = charts.pareto_chart([str(i)[:16] for i in top.index], list(top.values), "Top Products \u2014 Revenue & Cumulative Share")
        else:
            buf = charts.horizontal_ranking_chart([str(i) for i in top.index], list(top.values), "Top Products by Revenue")
        flow.append(Image(buf, width=CONTENT_WIDTH, height=CONTENT_WIDTH * 0.44))
        flow.append(Spacer(1, 3 * mm))

    if m.top_categories is not None and not m.top_categories.empty:
        cats = m.top_categories
        total = cats.sum() or 1
        rows = [[str(c), fmt_currency(v), f"{v/total*100:.1f}%"] for c, v in cats.items()]
        flow.append(Paragraph("Category Contribution", S["SubHeading"]))
        flow.append(ranking_table(["Category", "Revenue", "Share"], rows,
                                   col_widths=[70*mm, 55*mm, 49*mm]))
        flow.append(Spacer(1, 4 * mm))

    if m.bottom_products is not None and not m.bottom_products.empty:
        flow.append(Paragraph("Bottom Performers", S["SubHeading"]))
        rows = [[str(p), fmt_currency(v)] for p, v in m.bottom_products.items()]
        flow.append(ranking_table(["Product", "Revenue"], rows, col_widths=[110*mm, 64*mm],
                                   highlight_first_last=False))

    flow.append(PageBreak())
    return flow


# ══════════════════════════════════════════════════════════════════════════
# PAGE 6 — PROFITABILITY
# ══════════════════════════════════════════════════════════════════════════

def profitability_page(doc, m: ReportMetrics) -> list:
    fb = m.financial_breakdown
    if "revenue" not in fb:
        return []
    flow = [_section_title(doc, "Profitability Analysis"), Spacer(1, 4 * mm)]

    if "cogs" in fb and "gross_profit" in fb:
        labels = ["Revenue", "COGS", "Gross Profit"]
        values = [fb["revenue"], -fb["cogs"], fb["gross_profit"]]
        buf = charts.waterfall_chart(labels, values, "Revenue to Gross Profit")
        flow.append(Image(buf, width=CONTENT_WIDTH, height=CONTENT_WIDTH * (2.8/6.4)))
        flow.append(Spacer(1, 3 * mm))
    elif "gross_profit" in fb:
        flow.append(Paragraph(
            f"Revenue of {fmt_currency(fb['revenue'])} generated {fmt_currency(fb['gross_profit'])} "
            f"in profit. A detailed cost breakdown (COGS) was not present in the dataset, so a full "
            f"waterfall isn't shown \u2014 only the fields that exist in the data are reported.",
            S["Body"]))
        flow.append(Spacer(1, 3 * mm))

    cells = []
    cells.append(("Revenue", fmt_currency(fb["revenue"]), None, True))
    if "cogs" in fb:
        cells.append(("COGS", fmt_currency(fb["cogs"]), None, True))
    if "gross_profit" in fb:
        cells.append(("Gross Profit", fmt_currency(fb["gross_profit"]), None, fb["gross_profit"] >= 0))
    if "margin_pct" in fb:
        cells.append(("Margin", fmt_pct(fb["margin_pct"]), None, fb["margin_pct"] >= 0))
    if cells:
        flow.extend(_kpi_row_flowables(cells))

    flow.append(PageBreak())
    return flow


# ══════════════════════════════════════════════════════════════════════════
# PAGE 7 — DATA TRUST & QUALITY
# ══════════════════════════════════════════════════════════════════════════

def data_trust_page(doc, m: ReportMetrics) -> list:
    q = m.quality
    if not q or q.get("total_records", 0) == 0:
        return []
    flow = [_section_title(doc, "Data Trust & Quality"), Spacer(1, 4 * mm)]

    score = q["score"]
    score_color = GREEN if score >= 90 else (AMBER if score >= 70 else RED)
    score_tint = GREEN_TINT if score >= 90 else (AMBER_TINT if score >= 70 else RED_TINT)

    score_table = Table(
        [[Paragraph(f'<font color="{score_color.hexval()}" size="28"><b>{score}</b></font>'
                    f'<font color="{MUTED.hexval()}" size="11">/100</font>', S["Body"]),
          Paragraph(f"Total Records: <b>{q['total_records']:,}</b><br/>"
                    f"Total Columns: <b>{q['total_columns']}</b><br/>"
                    f"Missing Values: <b>{q['missing_pct']:.1f}%</b><br/>"
                    f"Duplicate Records: <b>{q['duplicate_rows']:,}</b>", S["Body"])]],
        colWidths=[55 * mm, CONTENT_WIDTH - 55 * mm],
    )
    score_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), score_tint),
        ("BOX", (0, 0), (-1, -1), 0.6, BORDER),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 14),
        ("TOPPADDING", (0, 0), (-1, -1), 12),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
    ]))
    flow.append(score_table)
    flow.append(Spacer(1, 5 * mm))

    if q.get("checks"):
        flow.append(checklist_table(q["checks"], col_widths=[10 * mm, CONTENT_WIDTH - 10 * mm]))

    flow.append(PageBreak())
    return flow


# ══════════════════════════════════════════════════════════════════════════
# PAGE 8 — FORECAST / OUTLOOK
# ══════════════════════════════════════════════════════════════════════════

def forecast_page(doc, m: ReportMetrics) -> list:
    flow = [_section_title(doc, "Forecast & Outlook"), Spacer(1, 4 * mm)]
    fc = m.forecast
    if not fc:
        flow.append(Paragraph(
            "Forecast unavailable because the dataset does not contain sufficient historical "
            "information (a valid date column with enough distinct periods is required).",
            S["Body"]))
        flow.append(PageBreak())
        return flow

    buf = charts.line_trend_chart(
        fc["history_labels"], fc["history_values"], "Revenue Forecast",
        forecast_labels=fc["forecast_labels"], forecast_values=fc["forecast_values"], ci=fc["ci"],
    )
    flow.append(Image(buf, width=CONTENT_WIDTH, height=CONTENT_WIDTH * (2.6 / 6.4)))
    flow.append(Spacer(1, 4 * mm))

    cells = [
        ("Model", fc["model_name"], None, True),
        ("Forecast Horizon", f"{fc['horizon']} period(s)", None, True),
        ("Model Fit (R\u00b2)", f"{fc['r2']:.2f}", None, fc["r2"] > 0.5),
        ("95% CI Band", fmt_currency(fc["ci"]), None, True),
    ]
    flow.extend(_kpi_row_flowables(cells))
    quality_note = ("This is a reasonably confident trend estimate." if fc["r2"] > 0.6 else
                     "Model fit is low \u2014 treat this as a rough directional signal only, not a precise prediction.")
    flow.append(Paragraph(quality_note, S["Caption"]))
    flow.append(PageBreak())
    return flow


# ══════════════════════════════════════════════════════════════════════════
# PAGE 9 — NOVA ANALYST DECISION BRIEF (AI, optional)
# ══════════════════════════════════════════════════════════════════════════

def decision_brief_page(doc, brief_text: str | None, ai_error: str | None) -> list:
    flow = [_section_title(doc, "Nova Analyst \u2014 Decision Brief"), Spacer(1, 4 * mm)]
    if not brief_text:
        flow.append(Paragraph("AI insights unavailable for this report.", S["Body"]))
        if ai_error:
            flow.append(Paragraph(f"({ai_error})", S["Caption"]))
        flow.append(PageBreak())
        return flow

    from .report_ai import parse_decision_brief
    sections = parse_decision_brief(brief_text)
    icon_num = 0
    for section_name, bullets in sections.items():
        if not bullets:
            continue
        flow.append(Paragraph(section_name.title(), S["SubHeading"]))
        for b in bullets:
            icon_num += 1
            flow.append(Paragraph(f"\u2022 {b}", S["Bullet"]))
        flow.append(Spacer(1, 2 * mm))
    flow.append(PageBreak())
    return flow


# ══════════════════════════════════════════════════════════════════════════
# FINAL PAGE — EXECUTIVE CONCLUSION
# ══════════════════════════════════════════════════════════════════════════

def conclusion_page(doc, m: ReportMetrics) -> list:
    flow = [_section_title(doc, "Executive Conclusion"), Spacer(1, 4 * mm)]

    rev = m.kpis.get("revenue")
    margin = m.kpis.get("margin")
    parts = []
    if rev:
        trend_word = "growing" if (rev.change_pct or 0) >= 0 else "under pressure"
        parts.append(f"Overall performance is {trend_word}, with revenue of {fmt_currency(rev.current)}.")
    if margin:
        parts.append(f"Profitability stands at a {fmt_pct(margin.current)} margin.")
    if m.top_regions is not None and len(m.top_regions) > 1:
        parts.append(f"The clearest opportunity is closing the gap between "
                      f"{m.top_regions.index[0]} and {m.top_regions.index[-1]}.")
    if margin and margin.current is not None and margin.current < 15:
        parts.append("Margin compression is the primary risk to monitor going forward.")

    summary_text = " ".join(parts) if parts else "Insufficient data to generate an executive conclusion."
    flow.append(Paragraph(summary_text, S["ConclusionBig"]))
    flow.append(Spacer(1, 10 * mm))
    flow.append(HRFlowable(width=CONTENT_WIDTH, thickness=0.75, color=BORDER))
    flow.append(Spacer(1, 4 * mm))
    flow.append(Paragraph("NovaMS", S["BodyBold"]))
    flow.append(Paragraph("Business Intelligence \u2022 Data Analytics \u2022 AI-Assisted Insights", S["Caption"]))
    return flow
