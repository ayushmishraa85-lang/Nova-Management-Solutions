"""
data_engine/trends.py
Automatic Time Analysis — Part 9 of the NovaMS Data Engine spec.

Only runs when a genuine date column exists. Computes daily/weekly/
monthly aggregates for one measure column plus period-over-period growth,
and reports the available date range. Nothing here is invented if there
isn't enough date coverage to support a given granularity.
"""
from __future__ import annotations

from typing import Any, Dict, Optional

import pandas as pd

_MIN_POINTS_FOR_GROWTH = 2


def _growth(series: pd.Series) -> Optional[float]:
    if len(series) < _MIN_POINTS_FOR_GROWTH or series.iloc[-2] == 0:
        return None
    return round((series.iloc[-1] - series.iloc[-2]) / abs(series.iloc[-2]) * 100, 2)


def compute_time_analysis(df: pd.DataFrame, date_col: str, measure_col: str) -> Dict[str, Any]:
    work = df[[date_col, measure_col]].copy()
    work[date_col] = pd.to_datetime(work[date_col], errors="coerce", format="mixed")
    work[measure_col] = pd.to_numeric(work[measure_col], errors="coerce")
    work = work.dropna()
    if work.empty:
        return {}

    work = work.set_index(date_col).sort_index()
    span_days = (work.index.max() - work.index.min()).days

    result: Dict[str, Any] = dict(
        date_range=dict(start=work.index.min().date().isoformat(),
                         end=work.index.max().date().isoformat()),
    )

    daily = work[measure_col].resample("D").sum()
    result["daily"] = {str(k.date()): round(float(v), 2) for k, v in daily.items()}

    if span_days >= 14:
        weekly = work[measure_col].resample("W").sum()
        result["weekly"] = {str(k.date()): round(float(v), 2) for k, v in weekly.items()}
        result["week_over_week_growth_pct"] = _growth(weekly)

    if span_days >= 60:
        monthly = work[measure_col].resample("ME").sum()
        result["monthly"] = {str(k.date()): round(float(v), 2) for k, v in monthly.items()}
        result["month_over_month_growth_pct"] = _growth(monthly)

    if span_days >= 730:
        yearly = work[measure_col].resample("YE").sum()
        result["yearly"] = {str(k.date()): round(float(v), 2) for k, v in yearly.items()}
        result["year_over_year_growth_pct"] = _growth(yearly)

    return result
