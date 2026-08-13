"""
data_engine/anomalies.py
Anomaly Detection — Part 11 of the NovaMS Data Engine spec.

Statistical (z-score on period-over-period % change) anomaly flags for a
named metric's time series, produced by trends.py. Deliberately
conservative — only flags genuinely large swings, not every small wiggle.
"""
from __future__ import annotations

from typing import Any, Dict, List

import numpy as np


def detect_anomalies(period_series: Dict[str, float], metric_name: str,
                      z_threshold: float = 2.0) -> List[Dict[str, Any]]:
    """
    period_series: {period_label: value}, e.g. the "monthly" dict from
    trends.compute_time_analysis(). Flags periods whose % change from the
    previous period is a statistical outlier relative to all other
    period-over-period changes.
    """
    periods = list(period_series.keys())
    values = list(period_series.values())
    if len(values) < 4:
        return []

    pct_changes = []
    for i in range(1, len(values)):
        prev = values[i - 1]
        pct_changes.append(((values[i] - prev) / abs(prev) * 100) if prev else 0.0)

    arr = np.array(pct_changes)
    std = arr.std(ddof=0)
    if std == 0:
        return []
    mean = arr.mean()

    anomalies: List[Dict[str, Any]] = []
    for i, change in enumerate(pct_changes):
        z = abs((change - mean) / std)
        if z >= z_threshold:
            severity = "high" if z >= 3 else "medium"
            anomalies.append(dict(
                metric=metric_name,
                period=periods[i + 1],
                change_pct=round(change, 2),
                severity=severity,
                reason=f"{'increase' if change > 0 else 'decrease'} of {abs(change):.1f}% vs prior period "
                       f"(Z={z:.2f} vs typical period-over-period swings)",
            ))
    return anomalies
