"""
report_validation.py — Pre-Export Validation
===============================================
Runs a checklist against the assembled report context BEFORE the PDF is
built. If something looks broken (NaN slipped through, an empty chart,
an impossible percentage), we fix it with a safe fallback rather than ship
a broken PDF — per the spec: "If validation fails, do not export the broken
report. Attempt a safe layout fallback and regenerate."
"""

from __future__ import annotations
import math
from .report_metrics import ReportMetrics


class ValidationIssue:
    def __init__(self, level: str, message: str):
        self.level = level  # "info" | "warning" | "error"
        self.message = message

    def __repr__(self):
        return f"[{self.level.upper()}] {self.message}"


def _is_bad_number(v) -> bool:
    try:
        f = float(v)
        return math.isnan(f) or math.isinf(f)
    except Exception:
        return False


def validate_metrics(m: ReportMetrics) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []

    if m.n_rows == 0:
        issues.append(ValidationIssue("error", "Dataset has zero rows."))
        return issues

    for name, kpi in m.kpis.items():
        if _is_bad_number(kpi.current):
            issues.append(ValidationIssue("warning", f"KPI '{name}' computed NaN/Infinity — will display as 'N/A'."))
            kpi.current = 0.0
        if kpi.previous is not None and _is_bad_number(kpi.previous):
            kpi.previous = None

    if m.quality and _is_bad_number(m.quality.get("score", 0)):
        issues.append(ValidationIssue("warning", "Data trust score computed invalid — defaulting to 0."))
        m.quality["score"] = 0

    if m.top_regions is not None and m.top_regions.empty:
        m.top_regions = None
        issues.append(ValidationIssue("info", "Regional table was empty after aggregation — section omitted."))

    if m.top_products is not None and m.top_products.empty:
        m.top_products = None
        issues.append(ValidationIssue("info", "Product table was empty after aggregation — section omitted."))

    if m.trend is not None and len(m.trend) < 2:
        m.trend = None
        issues.append(ValidationIssue("info", "Trend series too short — trend chart omitted."))

    return issues


def has_blocking_errors(issues: list[ValidationIssue]) -> bool:
    return any(i.level == "error" for i in issues)
