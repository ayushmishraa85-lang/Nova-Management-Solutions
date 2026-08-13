"""
data_engine/profiler.py
Automatic data profiling — Part 2 of the NovaMS Data Engine spec.

Computes a compact, JSON-safe structural profile per table/column. This
module never sends raw rows anywhere — only aggregated statistics and a
handful of example values. Role tagging here is a lightweight heuristic
("role_hint"); the deeper IDENTIFIER/DATE/MEASURE/... classification used
for business logic lives in semantic.py and builds on these hints.
"""
from __future__ import annotations

import logging
import re
from typing import Any, Dict

import numpy as np
import pandas as pd

logger = logging.getLogger("novams.data_engine.profiler")

_ID_NAME_PATTERN = re.compile(r"(^|_)(id|code|sku|uuid|guid)($|_)", re.IGNORECASE)
_DATE_NAME_PATTERN = re.compile(r"(date|_at$|_on$|time|timestamp|dob)", re.IGNORECASE)
_MAX_EXAMPLES = 5


def _json_safe(value: Any) -> Any:
    """Convert numpy/pandas scalars to plain Python types for JSON output."""
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return None
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        return float(value)
    if isinstance(value, (pd.Timestamp,)):
        return value.isoformat()
    if isinstance(value, (np.bool_,)):
        return bool(value)
    return value


def _looks_like_date(series: pd.Series, name: str) -> bool:
    if pd.api.types.is_datetime64_any_dtype(series):
        return True
    if not _DATE_NAME_PATTERN.search(name):
        return False
    sample = series.dropna().astype(str).head(50)
    if sample.empty:
        return False
    parsed = pd.to_datetime(sample, errors="coerce", format="mixed")
    return parsed.notna().mean() >= 0.8


def profile_column(series: pd.Series, name: str, n_rows: int) -> Dict[str, Any]:
    missing = int(series.isna().sum())
    non_null = series.dropna()
    unique_count = int(non_null.nunique())
    cardinality_ratio = round(unique_count / n_rows, 4) if n_rows else 0.0
    is_constant = unique_count <= 1

    is_date = _looks_like_date(series, name)
    is_numeric = pd.api.types.is_numeric_dtype(series) and not is_date

    role_hint = "unknown"
    min_v = max_v = mean_v = median_v = None

    if is_date:
        role_hint = "potential_date"
        parsed = pd.to_datetime(non_null, errors="coerce", format="mixed")
        parsed = parsed.dropna()
        if len(parsed):
            min_v, max_v = _json_safe(parsed.min()), _json_safe(parsed.max())
    elif is_numeric:
        if cardinality_ratio > 0.95 and _ID_NAME_PATTERN.search(name):
            role_hint = "potential_id"
        else:
            role_hint = "potential_numeric_measure"
            if len(non_null):
                min_v = _json_safe(non_null.min())
                max_v = _json_safe(non_null.max())
                mean_v = round(float(non_null.mean()), 4)
                median_v = round(float(non_null.median()), 4)
    else:
        if cardinality_ratio > 0.95 or _ID_NAME_PATTERN.search(name):
            role_hint = "potential_id"
        elif cardinality_ratio <= 0.5 and unique_count <= max(50, n_rows * 0.2):
            role_hint = "potential_categorical"

    examples = [_json_safe(v) for v in non_null.unique()[:_MAX_EXAMPLES]]

    return dict(
        name=name,
        dtype=str(series.dtype),
        role_hint=role_hint,
        missing_count=missing,
        missing_pct=round(missing / n_rows * 100, 2) if n_rows else 0.0,
        unique_count=unique_count,
        cardinality_ratio=cardinality_ratio,
        is_constant=is_constant,
        example_values=examples,
        min_value=min_v,
        max_value=max_v,
        mean_value=mean_v,
        median_value=median_v,
    )


def profile_table(df: pd.DataFrame, table_name: str) -> Dict[str, Any]:
    """Build the compact structural profile for one table (Part 2 example format)."""
    n_rows = len(df)
    columns = {}
    for col in df.columns:
        try:
            columns[col] = profile_column(df[col], str(col), n_rows)
        except Exception:  # pragma: no cover - defensive, never crash the whole profile
            logger.exception("Failed to profile column '%s' in table '%s'", col, table_name)
            columns[col] = dict(name=col, dtype=str(df[col].dtype), role_hint="unknown",
                                 missing_count=0, missing_pct=0.0, unique_count=0,
                                 cardinality_ratio=0.0, is_constant=False, example_values=[],
                                 min_value=None, max_value=None, mean_value=None, median_value=None)

    return dict(
        table=table_name,
        rows=n_rows,
        n_columns=len(df.columns),
        duplicate_rows=int(df.duplicated().sum()),
        columns=columns,
    )
