"""
data_engine/quality.py
Data Quality Engine — Part 3 of the NovaMS Data Engine spec.

Flags issues (missing values, duplicates, invalid/negative values, empty
or constant columns, outliers) and produces a 0-100 Data Quality Score.
Nothing here deletes or silently changes data — every problem is reported,
never auto-fixed.
"""
from __future__ import annotations

from typing import Any, Dict, List

import numpy as np
import pandas as pd

# Columns whose values should never legitimately be negative (heuristic
# keyword match against the column name).
_NON_NEGATIVE_KEYWORDS = ("price", "revenue", "amount", "quantity", "orders",
                           "cost", "qty", "units", "sales")


def _issue(severity: str, issue: str, column: str | None = None) -> Dict[str, Any]:
    return dict(severity=severity, column=column, issue=issue)


def check_table_quality(df: pd.DataFrame, table_name: str, profile: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Run every quality check from Part 3 and return a list of issue dicts."""
    issues: List[Dict[str, Any]] = []
    n_rows = len(df)
    if n_rows == 0:
        return [_issue("critical", "Table has zero rows.")]

    # Missing values
    for col_name, col_profile in profile["columns"].items():
        pct = col_profile["missing_pct"]
        if pct > 0:
            sev = "critical" if pct > 30 else "warning" if pct > 5 else "info"
            issues.append(_issue(sev, f"{pct:.1f}% missing values", col_name))

    # Duplicate rows
    dup_rows = int(df.duplicated().sum())
    if dup_rows:
        pct = dup_rows / n_rows * 100
        issues.append(_issue("warning" if pct < 10 else "critical",
                              f"{dup_rows} duplicate row(s) ({pct:.1f}%)"))

    # Duplicate IDs (any column flagged as a potential identifier)
    for col_name, col_profile in profile["columns"].items():
        if col_profile["role_hint"] == "potential_id":
            dup_ids = int(df[col_name].duplicated().sum())
            if dup_ids:
                issues.append(_issue("critical", f"{dup_ids} duplicate value(s) in identifier column", col_name))

    # Empty / constant columns
    for col_name, col_profile in profile["columns"].items():
        if col_profile["missing_count"] == n_rows:
            issues.append(_issue("warning", "Column is entirely empty", col_name))
        elif col_profile["is_constant"] and col_profile["missing_count"] < n_rows:
            issues.append(_issue("info", "Column has only one distinct value (constant)", col_name))

    # Negative / impossible values on columns that shouldn't be negative
    for col_name, col_profile in profile["columns"].items():
        if col_profile["role_hint"] != "potential_numeric_measure":
            continue
        if not any(kw in col_name.lower() for kw in _NON_NEGATIVE_KEYWORDS):
            continue
        numeric = pd.to_numeric(df[col_name], errors="coerce")
        bad = int((numeric < 0).sum())
        if bad:
            issues.append(_issue("critical", f"{bad} row(s) with negative values", col_name))

    # Invalid dates (name suggests a date but couldn't be parsed)
    for col_name, col_profile in profile["columns"].items():
        if col_profile["role_hint"] != "potential_date":
            continue
        parsed = pd.to_datetime(df[col_name], errors="coerce", format="mixed")
        invalid = int(parsed.isna().sum() - df[col_name].isna().sum())
        if invalid > 0:
            issues.append(_issue("warning", f"{invalid} value(s) that don't parse as valid dates", col_name))

    # Suspicious outliers (z-score, numeric measures only, needs >=8 points)
    for col_name, col_profile in profile["columns"].items():
        if col_profile["role_hint"] != "potential_numeric_measure":
            continue
        numeric = pd.to_numeric(df[col_name], errors="coerce").dropna()
        if len(numeric) < 8 or numeric.std(ddof=0) == 0:
            continue
        z = np.abs((numeric - numeric.mean()) / numeric.std(ddof=0))
        n_outliers = int((z > 3).sum())
        if n_outliers:
            issues.append(_issue("info", f"{n_outliers} statistical outlier(s) (|Z|>3)", col_name))

    return issues


def score_table_quality(profile: Dict[str, Any], issues: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Blend completeness / validity / uniqueness into one 0-100 score.
    Weighting: completeness 40%, validity 30%, uniqueness 30% — matches the
    spirit of Part 3's example output (`score`, `status`, `issues`).
    """
    n_rows = profile["rows"]
    n_cols = profile["n_columns"] or 1

    total_missing_pct = np.mean([c["missing_pct"] for c in profile["columns"].values()]) if profile["columns"] else 0
    completeness = max(0.0, 1 - total_missing_pct / 100)

    critical_issues = sum(1 for i in issues if i["severity"] == "critical")
    validity = max(0.0, 1 - 0.15 * critical_issues)

    dup_pct = profile["duplicate_rows"] / n_rows if n_rows else 0
    uniqueness = max(0.0, 1 - dup_pct)

    raw_score = completeness * 0.40 + validity * 0.30 + uniqueness * 0.30
    score = int(round(max(0, min(100, raw_score * 100))))

    if score >= 90:
        status = "analysis_ready"
    elif score >= 65:
        status = "needs_review"
    else:
        status = "poor_quality"

    return dict(table=profile["table"], score=score, status=status, issues=issues)
