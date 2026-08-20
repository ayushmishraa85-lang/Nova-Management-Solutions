"""
report_export.py — PDF / Excel Assembly
==========================================
Takes the already-validated ReportMetrics and produces the final files.
Never lets a single broken section take down the whole PDF — each template
call is wrapped so one bad section degrades to "omitted", not a crash.
"""

from __future__ import annotations
import io
import os
import re
from datetime import datetime

import pandas as pd

from .report_layout import make_document
from .report_metrics import ReportMetrics
from .report_schema import Schema
from . import report_templates as tpl
from . import report_templates_notebook as nbtpl
from . import report_eda as eda
from . import report_charts as charts


def safe_filename(text: str) -> str:
    text = re.sub(r"[^A-Za-z0-9_\-]+", "", text.replace(" ", ""))
    return text or "Dataset"


def build_filename(report_type: str, dataset_name: str, ext: str = "pdf") -> str:
    date_str = datetime.now().strftime("%Y-%m-%d")
    return f"NovaMS_{safe_filename(report_type)}_{safe_filename(dataset_name)}_{date_str}.{ext}"


def _safe_section(build_fn, *args, **kwargs) -> list:
    """Wraps a template-page builder so a single failing section is skipped
    (with the failure recorded) instead of crashing the whole export."""
    try:
        return build_fn(*args, **kwargs), None
    except Exception as e:
        return [], str(e)


def build_pdf(
    filepath: str,
    df: pd.DataFrame,
    schema: Schema,
    metrics: ReportMetrics,
    dataset_name: str,
    report_type: str = "Executive Report",
    company_name: str | None = None,
    period_label: str | None = None,
    ai_brief_text: str | None = None,
    ai_error: str | None = None,
) -> list:
    """Builds the PDF at `filepath`. Returns a list of section-level warnings
    (non-fatal — the PDF is still produced)."""
    section_warnings: list[str] = []
    doc = make_document(filepath, f"{report_type} \u2014 {dataset_name}", dataset_name)
    story: list = []

    section_builders = [
        ("Cover", lambda: tpl.cover_page(dataset_name, report_type, company_name, period_label)),
        ("Executive Summary", lambda: tpl.executive_summary_page(doc, metrics)),
        ("Business Performance", lambda: tpl.business_performance_page(doc, metrics)),
        ("Regional Performance", lambda: tpl.regional_page(doc, metrics)),
        ("Product & Category", lambda: tpl.product_page(doc, metrics)),
        ("Profitability", lambda: tpl.profitability_page(doc, metrics)),
        ("Data Trust & Quality", lambda: tpl.data_trust_page(doc, metrics)),
        ("Forecast & Outlook", lambda: tpl.forecast_page(doc, metrics)),
        ("Decision Brief", lambda: tpl.decision_brief_page(doc, ai_brief_text, ai_error)),
        ("Conclusion", lambda: tpl.conclusion_page(doc, metrics)),
    ]

    any_content = False
    for name, builder in section_builders:
        flow, err = _safe_section(builder)
        if err:
            section_warnings.append(f"Section '{name}' skipped due to an internal error: {err}")
            continue
        if flow:
            story.extend(flow)
            if name not in ("Cover",):
                any_content = True

    if not any_content:
        # Absolute fallback — never ship a PDF with nothing but a cover page
        # and no explanation of why.
        from reportlab.platypus import Paragraph, Spacer
        from reportlab.lib.units import mm
        from .report_layout import get_styles
        styles = get_styles()
        story.append(Paragraph("Report Notice", styles["SectionHeading"]))
        story.append(Spacer(1, 4 * mm))
        story.append(Paragraph(
            "This dataset did not contain enough recognizable business columns "
            "(revenue, orders, dates, or dimensions) to generate report sections. "
            "Upload a dataset with at least a revenue-equivalent numeric column to "
            "enable the full report.", styles["Body"]))
        section_warnings.append("No sections had sufficient data — fallback notice page shown.")

    doc.build(story)
    return section_warnings


def build_pdf_notebook(
    filepath: str,
    df: pd.DataFrame,
    raw_df: pd.DataFrame,
    dataset_name: str,
    objective_text: str | None = None,
) -> tuple[list, dict]:
    """Builds the Notebook / Lab Report style PDF: Objective -> Data
    Cleaning -> [chart + Interpretation] blocks -> Conclusion. Returns
    (section_warnings, eda_summary_for_reference)."""
    section_warnings: list[str] = []
    doc = make_document(filepath, f"EDA Report \u2014 {dataset_name}", dataset_name)
    story: list = []

    plan = eda.plan_eda(df)
    section_warnings.extend(plan.warnings)

    objective_text = objective_text or (
        f"To analyze the {dataset_name} dataset \u2014 its structure, key variables, and their "
        f"relationships \u2014 using data cleaning, statistical summarization, and visualization."
    )
    flow, err = _safe_section(nbtpl.title_objective_page, dataset_name, objective_text)
    if err:
        section_warnings.append(f"Title/Objective section skipped: {err}")
    story.extend(flow)

    cleaning = eda.data_cleaning_summary(raw_df, df)
    flow, err = _safe_section(nbtpl.data_cleaning_page, doc, cleaning)
    if err:
        section_warnings.append(f"Data Cleaning section skipped: {err}")
    story.extend(flow)

    any_chart = False

    # 1) Target distribution — vertical bar (matches reference "Customer Satisfaction" chart)
    if plan.target_col:
        try:
            info = eda.target_distribution(df, plan.target_col)
            buf = charts.bar_chart(info["labels"], info["values"], f"{plan.target_col} Distribution")
            story.extend(nbtpl.chart_interpretation_block(
                doc, buf, f"{plan.target_col} Distribution", info["interpretation"], new_section=True))
            any_chart = True
        except Exception as e:
            section_warnings.append(f"Target distribution chart skipped: {e}")

    # 2) Categorical breakdowns — pie charts
    for col in plan.categorical_cols[:2]:
        try:
            info = eda.categorical_breakdown(df, col)
            buf = charts.pie_chart(info["labels"], info["values"], f"{col} Distribution")
            story.extend(nbtpl.chart_interpretation_block(
                doc, buf, f"{col} Distribution", info["interpretation"], image_width_frac=0.72))
            any_chart = True
        except Exception as e:
            section_warnings.append(f"'{col}' breakdown chart skipped: {e}")

    # 3) Numeric distribution — histogram (first numeric column)
    if plan.numeric_cols:
        col = plan.numeric_cols[0]
        try:
            info = eda.numeric_distribution(df, col)
            if info["values"]:
                buf = charts.histogram_chart(info["values"], f"{col} Distribution", x_label=col)
                story.extend(nbtpl.chart_interpretation_block(
                    doc, buf, f"{col} Distribution", info["interpretation"], new_section=True))
                any_chart = True
        except Exception as e:
            section_warnings.append(f"'{col}' histogram skipped: {e}")

    # 4) Spread — boxplot (second numeric column, or first if only one exists)
    if plan.numeric_cols:
        col = plan.numeric_cols[1] if len(plan.numeric_cols) > 1 else plan.numeric_cols[0]
        try:
            info = eda.numeric_spread(df, col)
            if info["values"]:
                buf = charts.box_chart(info["values"], f"{col} Spread", y_label=col)
                story.extend(nbtpl.chart_interpretation_block(
                    doc, buf, f"{col} Spread", info["interpretation"], image_width_frac=0.6))
                any_chart = True
        except Exception as e:
            section_warnings.append(f"'{col}' box plot skipped: {e}")

    # 5) Relationship — scatter (first two numeric columns)
    if len(plan.numeric_cols) >= 2:
        c1, c2 = plan.numeric_cols[0], plan.numeric_cols[1]
        try:
            info = eda.numeric_relationship(df, c1, c2)
            if info["x"]:
                buf = charts.scatter_chart(info["x"], info["y"], f"{c1} vs {c2}", c1, c2)
                story.extend(nbtpl.chart_interpretation_block(
                    doc, buf, f"{c1} vs {c2}", info["interpretation"], new_section=True))
                any_chart = True
        except Exception as e:
            section_warnings.append(f"Relationship chart skipped: {e}")

    # 6) Group comparison — grouped bar (categorical dims vs target)
    if plan.target_col:
        for col in plan.categorical_cols[:2]:
            try:
                info = eda.group_comparison(df, col, plan.target_col)
                buf = charts.grouped_bar_chart(info["categories"], info["series"],
                                                 f"{plan.target_col} by {col}", x_label=col)
                story.extend(nbtpl.chart_interpretation_block(
                    doc, buf, f"{plan.target_col} by {col}", info["interpretation"]))
                any_chart = True
            except Exception as e:
                section_warnings.append(f"'{plan.target_col} by {col}' chart skipped: {e}")

    # 7) Correlation heatmap
    if len(plan.numeric_cols) >= 3:
        try:
            info = eda.correlation_analysis(df, plan.numeric_cols)
            if info:
                buf = charts.correlation_heatmap_chart(info["corr"], "Correlation Heatmap of Numerical Variables")
                story.extend(nbtpl.chart_interpretation_block(
                    doc, buf, "Correlation Heatmap", info["interpretation"], new_section=True, image_width_frac=0.85))
                any_chart = True
        except Exception as e:
            section_warnings.append(f"Correlation heatmap skipped: {e}")

    if not any_chart:
        from reportlab.platypus import Paragraph as _P
        from .report_layout import get_styles as _gs
        _s = _gs()
        story.append(_P(
            "This dataset did not contain enough recognizable categorical or numeric columns "
            "to generate chart sections.", _s["Body"]))
        section_warnings.append("No chart sections had sufficient data.")

    conclusion_text = eda.build_conclusion(dataset_name, plan, len(df), len(df.columns))
    flow, err = _safe_section(nbtpl.conclusion_page, doc, conclusion_text)
    if err:
        section_warnings.append(f"Conclusion section skipped: {err}")
    story.extend(flow)

    doc.build(story)
    return section_warnings, dict(target_col=plan.target_col, categorical_cols=plan.categorical_cols,
                                    numeric_cols=plan.numeric_cols)


def build_excel(filepath: str, df: pd.DataFrame, metrics: ReportMetrics) -> None:
    """Optional analytical workbook: KPI summary + raw filtered data."""
    with pd.ExcelWriter(filepath, engine="openpyxl") as writer:
        kpi_rows = []
        for key, kpi in metrics.kpis.items():
            kpi_rows.append(dict(
                Metric=kpi.label, Current=kpi.current, Previous=kpi.previous,
                Change_Pct=kpi.change_pct,
            ))
        pd.DataFrame(kpi_rows).to_excel(writer, sheet_name="KPI Summary", index=False)

        if metrics.top_regions is not None:
            metrics.top_regions.rename("Revenue").to_frame().to_excel(writer, sheet_name="Regional")
        if metrics.top_products is not None:
            metrics.top_products.rename("Revenue").to_frame().to_excel(writer, sheet_name="Top Products")
        if metrics.top_categories is not None:
            metrics.top_categories.rename("Revenue").to_frame().to_excel(writer, sheet_name="Categories")

        quality_df = pd.DataFrame([metrics.quality]) if metrics.quality else pd.DataFrame()
        if not quality_df.empty:
            quality_df.drop(columns=["checks"], errors="ignore").to_excel(writer, sheet_name="Data Quality", index=False)

        # Raw data — capped so huge datasets don't blow up the workbook.
        df.head(50000).to_excel(writer, sheet_name="Raw Data", index=False)
