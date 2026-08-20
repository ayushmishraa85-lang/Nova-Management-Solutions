"""
report_engine.py — Report Engine Orchestrator
=================================================
The single entry point the rest of NovaMS should ever call. Wires together:

    Dataset -> Schema Detection -> Analytics -> Validation -> Charts/Tables
             -> PDF/Excel Export

Every stage is wrapped so a failure anywhere produces a clear `success=False`
result with a human-readable reason, rather than raising into the Streamlit
app and breaking the rest of the dashboard.
"""

from __future__ import annotations
import os
import tempfile
import time
from dataclasses import dataclass, field

import pandas as pd

REPORT_ENGINE_IMPORT_ERROR = None
try:
    from .report_schema import detect_schema, Schema
    from .report_metrics import compute_metrics, ReportMetrics
    from .report_validation import validate_metrics, has_blocking_errors
    from .report_export import build_pdf, build_pdf_notebook, build_excel, build_filename
    from .report_ai import generate_decision_brief
    REPORT_ENGINE_AVAILABLE = True
except Exception as _e:  # pragma: no cover - defensive; e.g. reportlab/matplotlib missing
    REPORT_ENGINE_AVAILABLE = False
    REPORT_ENGINE_IMPORT_ERROR = str(_e)


# Datasets larger than this are aggregated down before charting so the PDF
# build stays fast and memory-bounded — per spec section 12 (Large Dataset
# Performance): "aggregate before visualization", "avoid sending raw
# datasets to Claude".
_LARGE_DATASET_ROW_LIMIT = 200_000


@dataclass
class ReportResult:
    success: bool
    pdf_path: str | None = None
    excel_path: str | None = None
    pdf_filename: str | None = None
    excel_filename: str | None = None
    pdf_bytes: bytes | None = None
    excel_bytes: bytes | None = None
    warnings: list = field(default_factory=list)
    errors: list = field(default_factory=list)
    metrics: "ReportMetrics | None" = None
    ai_used: bool = False
    generation_seconds: float = 0.0
    theme_applied: dict = field(default_factory=dict)


class ReportEngine:
    """Usage:

        engine = ReportEngine()
        result = engine.generate(
            df=filtered_dataframe,
            dataset_name="Zepto Sales",
            report_type="Executive Report",
            company_name=None,
            ai_enabled=True,
            api_key=api_key_or_None,
            output_dir="/mnt/user-data/outputs",
            include_excel=True,
        )
        if result.success:
            ...use result.pdf_path / result.excel_path...
    """

    def __init__(self):
        self.available = REPORT_ENGINE_AVAILABLE
        self.import_error = REPORT_ENGINE_IMPORT_ERROR

    def generate(
        self,
        df: pd.DataFrame,
        dataset_name: str = "Dataset",
        report_type: str = "Executive Report",
        company_name: str | None = None,
        ai_enabled: bool = False,
        api_key: str | None = None,
        output_dir: str | None = None,
        include_excel: bool = False,
        period_label: str | None = None,
        style: str = "executive",
        theme: dict | None = None,
    ) -> ReportResult:
        start = time.time()
        result = ReportResult(success=False)

        if not self.available:
            result.errors.append(f"Report Engine is unavailable: {self.import_error}")
            return result

        try:
            if df is None or df.empty:
                result.errors.append("No data available to generate a report from.")
                return result

            # Apply (or reset) the report's accent color + chart palette to
            # match the caller's active dashboard theme. Reset happens even
            # when `theme` is None so one report's colors never leak into
            # the next report generated in the same long-running process
            # (Streamlit keeps the same Python process alive across reruns).
            from .report_layout import set_theme
            theme = theme or {}
            set_theme(theme.get("primary"), theme.get("chart_palette"))
            result.theme_applied = dict(theme) if theme else {}

            work_df = df
            if len(df) > _LARGE_DATASET_ROW_LIMIT:
                # Deterministic downsample for chart/metric computation only —
                # keeps the report fast on very large uploads without silently
                # fabricating anything (aggregates are still computed from a
                # large, representative sample, and this is disclosed below).
                work_df = df.sample(n=_LARGE_DATASET_ROW_LIMIT, random_state=42)
                result.warnings.append(
                    f"Dataset has {len(df):,} rows — metrics were computed from a "
                    f"{_LARGE_DATASET_ROW_LIMIT:,}-row representative sample for performance."
                )

            output_dir = output_dir or tempfile.gettempdir()
            os.makedirs(output_dir, exist_ok=True)

            if style == "notebook":
                from .report_export import build_pdf_notebook
                clean_df = work_df.dropna()
                if clean_df.empty:
                    result.errors.append("Dataset has no complete rows after removing missing values.")
                    return result
                pdf_filename = build_filename(report_type, dataset_name, "pdf")
                pdf_path = os.path.join(output_dir, pdf_filename)
                section_warnings, eda_summary = build_pdf_notebook(
                    pdf_path, clean_df, work_df, dataset_name,
                )
                result.warnings.extend(section_warnings)
                result.pdf_path = pdf_path
                result.pdf_filename = pdf_filename
                with open(pdf_path, "rb") as f:
                    result.pdf_bytes = f.read()

                if include_excel:
                    try:
                        excel_filename = build_filename(report_type, dataset_name, "xlsx")
                        excel_path = os.path.join(output_dir, excel_filename)
                        clean_df.to_excel(excel_path, index=False, sheet_name="Cleaned Data")
                        result.excel_path = excel_path
                        result.excel_filename = excel_filename
                        with open(excel_path, "rb") as f:
                            result.excel_bytes = f.read()
                    except Exception as e:
                        result.warnings.append(f"Excel workbook could not be generated: {e}")

                result.success = True
                return result

            schema = detect_schema(work_df)
            result.warnings.extend(schema.warnings)

            metrics = compute_metrics(work_df, schema)
            issues = validate_metrics(metrics)
            for issue in issues:
                (result.errors if issue.level == "error" else result.warnings).append(issue.message)

            if has_blocking_errors(issues):
                result.errors.append("Report generation stopped — the dataset failed validation.")
                return result

            result.metrics = metrics

            ai_brief_text, ai_error = None, None
            if ai_enabled and api_key:
                summary = self._metrics_summary_for_ai(metrics)
                ai_brief_text, ai_error = generate_decision_brief(summary, api_key)
                result.ai_used = ai_brief_text is not None
                if ai_error:
                    result.warnings.append(f"AI insights unavailable: {ai_error}")

            output_dir = output_dir or tempfile.gettempdir()
            os.makedirs(output_dir, exist_ok=True)

            pdf_filename = build_filename(report_type, dataset_name, "pdf")
            pdf_path = os.path.join(output_dir, pdf_filename)
            section_warnings = build_pdf(
                pdf_path, work_df, schema, metrics, dataset_name,
                report_type=report_type, company_name=company_name,
                period_label=period_label, ai_brief_text=ai_brief_text, ai_error=ai_error,
            )
            result.warnings.extend(section_warnings)
            result.pdf_path = pdf_path
            result.pdf_filename = pdf_filename
            with open(pdf_path, "rb") as f:
                result.pdf_bytes = f.read()

            if include_excel:
                try:
                    excel_filename = build_filename(report_type, dataset_name, "xlsx")
                    excel_path = os.path.join(output_dir, excel_filename)
                    build_excel(excel_path, work_df, metrics)
                    result.excel_path = excel_path
                    result.excel_filename = excel_filename
                    with open(excel_path, "rb") as f:
                        result.excel_bytes = f.read()
                except Exception as e:
                    result.warnings.append(f"Excel workbook could not be generated: {e}")

            result.success = True
            return result

        except Exception as e:
            result.errors.append(f"Unexpected error during report generation: {e}")
            return result
        finally:
            result.generation_seconds = round(time.time() - start, 2)

    @staticmethod
    def _metrics_summary_for_ai(metrics: "ReportMetrics") -> dict:
        """Only aggregated, already-validated numbers — never raw rows —
        get sent to the LLM (spec section 12)."""
        summary = {"kpis": {}, "quality_score": None}
        for key, kpi in metrics.kpis.items():
            summary["kpis"][kpi.label] = dict(
                current=round(kpi.current, 2),
                previous=round(kpi.previous, 2) if kpi.previous is not None else None,
                change_pct=round(kpi.change_pct, 2) if kpi.change_pct is not None else None,
            )
        if metrics.quality:
            summary["quality_score"] = metrics.quality.get("score")
        if metrics.top_regions is not None:
            summary["top_regions"] = {str(k): round(float(v), 2) for k, v in metrics.top_regions.head(5).items()}
        if metrics.top_products is not None:
            summary["top_products"] = {str(k): round(float(v), 2) for k, v in metrics.top_products.head(5).items()}
        if metrics.top_categories is not None:
            summary["top_categories"] = {str(k): round(float(v), 2) for k, v in metrics.top_categories.items()}
        if metrics.forecast:
            summary["forecast"] = {
                "r2": round(metrics.forecast["r2"], 3),
                "horizon": metrics.forecast["horizon"],
                "forecast_values": [round(v, 2) for v in metrics.forecast["forecast_values"]],
            }
        return summary
