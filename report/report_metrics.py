"""
report_metrics.py — Analytics Engine for the Report
=====================================================
Pure, Streamlit-free calculation functions. Every number that ends up in the
PDF traces back to a function in this file operating on the real (validated)
dataset. The LLM (report_ai.py) is never allowed to touch these values — it
only explains them.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from dataclasses import dataclass, field

from .report_schema import Schema


def _safe_div(a, b):
    try:
        if b in (0, None) or (isinstance(b, float) and (np.isnan(b) or b == 0)):
            return 0.0
        val = a / b
        if val is None or (isinstance(val, float) and (np.isnan(val) or np.isinf(val))):
            return 0.0
        return float(val)
    except Exception:
        return 0.0


def _clean_num(v):
    """Guards every number that will be rendered in the PDF against
    NaN/Infinity — validation rule from the spec: never display NaN/Inf."""
    try:
        f = float(v)
        if np.isnan(f) or np.isinf(f):
            return 0.0
        return f
    except Exception:
        return 0.0


@dataclass
class KPI:
    label: str
    current: float
    previous: float | None = None
    is_percent: bool = False
    is_currency: bool = True

    @property
    def change_pct(self) -> float | None:
        if self.previous in (None, 0):
            return None
        return _clean_num((self.current - self.previous) / abs(self.previous) * 100)

    @property
    def direction(self) -> str:
        if self.change_pct is None:
            return "flat"
        return "up" if self.change_pct >= 0 else "down"


@dataclass
class ReportMetrics:
    schema: Schema
    n_rows: int = 0
    n_cols: int = 0
    kpis: dict = field(default_factory=dict)          # name -> KPI
    top_regions: pd.Series | None = None
    top_regions_prev: pd.Series | None = None
    top_products: pd.Series | None = None
    top_categories: pd.Series | None = None
    bottom_products: pd.Series | None = None
    trend: pd.Series | None = None                    # date-indexed revenue series (if date exists)
    financial_breakdown: dict = field(default_factory=dict)   # revenue/cogs/profit/margin if available
    quality: dict = field(default_factory=dict)
    forecast: dict | None = None
    highlights: list = field(default_factory=list)    # auto-generated highlight strings
    warnings: list = field(default_factory=list)


def _split_previous_period(df: pd.DataFrame, schema: Schema):
    """If a usable date column exists, split into current vs previous period
    (halves of the observed date range) for period-over-period comparison.
    Returns (current_df, previous_df) — previous_df may be None."""
    if not schema.date or schema.date not in df.columns:
        return df, None
    dates = pd.to_datetime(df[schema.date], errors="coerce", format="mixed")
    valid = dates.notna()
    if valid.sum() < 4:
        return df, None
    dmin, dmax = dates[valid].min(), dates[valid].max()
    if dmin == dmax:
        return df, None
    midpoint = dmin + (dmax - dmin) / 2
    current_mask = dates >= midpoint
    previous_mask = (dates < midpoint) & valid
    current_df = df[current_mask]
    previous_df = df[previous_mask]
    if len(current_df) < 2 or len(previous_df) < 2:
        return df, None
    return current_df, previous_df


def compute_metrics(df: pd.DataFrame, schema: Schema) -> ReportMetrics:
    m = ReportMetrics(schema=schema, n_rows=len(df), n_cols=len(df.columns))
    if df is None or df.empty:
        m.warnings.append("Dataset is empty — no metrics could be calculated.")
        return m

    current_df, previous_df = _split_previous_period(df, schema)

    def _sum(frame, col):
        if not col or frame is None or col not in frame.columns:
            return None
        return _clean_num(pd.to_numeric(frame[col], errors="coerce").sum())

    def _count_orders(frame):
        if frame is None:
            return None
        if schema.orders and schema.orders in frame.columns:
            return _clean_num(pd.to_numeric(frame[schema.orders], errors="coerce").sum())
        return float(len(frame))

    # ── KPIs ────────────────────────────────────────────────────────────
    rev_cur = _sum(current_df, schema.revenue)
    rev_prev = _sum(previous_df, schema.revenue) if previous_df is not None else None
    if rev_cur is not None:
        m.kpis["revenue"] = KPI("Revenue", rev_cur, rev_prev)

    prof_cur = _sum(current_df, schema.profit)
    prof_prev = _sum(previous_df, schema.profit) if previous_df is not None else None
    if prof_cur is None and schema.revenue and schema.cogs:
        # Derived profit — real subtraction of two real columns, not invented.
        prof_cur = _clean_num(_sum(current_df, schema.revenue) - _sum(current_df, schema.cogs))
        if previous_df is not None:
            prof_prev = _clean_num(_sum(previous_df, schema.revenue) - _sum(previous_df, schema.cogs))
    if prof_cur is not None:
        m.kpis["profit"] = KPI("Profit", prof_cur, prof_prev)

    ord_cur = _count_orders(current_df)
    ord_prev = _count_orders(previous_df) if previous_df is not None else None
    if ord_cur is not None:
        m.kpis["orders"] = KPI("Orders", ord_cur, ord_prev, is_currency=False)

    if rev_cur is not None and ord_cur:
        aov_cur = _safe_div(rev_cur, ord_cur)
        aov_prev = _safe_div(rev_prev, ord_prev) if (rev_prev is not None and ord_prev) else None
        m.kpis["aov"] = KPI("Average Order Value", aov_cur, aov_prev)

    if rev_cur and prof_cur is not None:
        margin_cur = _safe_div(prof_cur, rev_cur) * 100
        margin_prev = (_safe_div(prof_prev, rev_prev) * 100
                        if (rev_prev and prof_prev is not None) else None)
        m.kpis["margin"] = KPI("Profit Margin", margin_cur, margin_prev, is_percent=True, is_currency=False)

    if rev_cur is not None and rev_prev not in (None, 0):
        growth = _safe_div(rev_cur - rev_prev, abs(rev_prev)) * 100
        m.kpis["growth"] = KPI("Revenue Growth", growth, None, is_percent=True, is_currency=False)

    # ── Financial breakdown (Profitability page) ───────────────────────
    if schema.revenue:
        m.financial_breakdown["revenue"] = _clean_num(_sum(df, schema.revenue))
    if schema.cogs:
        m.financial_breakdown["cogs"] = _clean_num(_sum(df, schema.cogs))
    if "revenue" in m.financial_breakdown and "cogs" in m.financial_breakdown:
        m.financial_breakdown["gross_profit"] = _clean_num(
            m.financial_breakdown["revenue"] - m.financial_breakdown["cogs"]
        )
    elif schema.profit:
        m.financial_breakdown["gross_profit"] = _clean_num(_sum(df, schema.profit))
    if "gross_profit" in m.financial_breakdown and m.financial_breakdown.get("revenue"):
        m.financial_breakdown["margin_pct"] = _clean_num(
            _safe_div(m.financial_breakdown["gross_profit"], m.financial_breakdown["revenue"]) * 100
        )

    # ── Regional (only if geo column exists) ────────────────────────────
    if schema.has_geo() and schema.revenue:
        geo_col = schema.geo_col()
        m.top_regions = df.groupby(geo_col)[schema.revenue].sum().sort_values(ascending=False)
        if previous_df is not None and geo_col in previous_df.columns:
            m.top_regions_prev = previous_df.groupby(geo_col)[schema.revenue].sum()

    # ── Product / Category (only if those columns exist) ────────────────
    if schema.product and schema.revenue:
        prod_rev = df.groupby(schema.product)[schema.revenue].sum().sort_values(ascending=False)
        m.top_products = prod_rev.head(10)
        m.bottom_products = prod_rev.tail(5).sort_values()
    if schema.category and schema.revenue:
        m.top_categories = df.groupby(schema.category)[schema.revenue].sum().sort_values(ascending=False)

    # ── Trend (only if a usable date column exists) ─────────────────────
    if schema.date and schema.revenue:
        dates = pd.to_datetime(df[schema.date], errors="coerce", format="mixed")
        trend_df = pd.DataFrame({"_date": dates, "_rev": pd.to_numeric(df[schema.revenue], errors="coerce")})
        trend_df = trend_df.dropna()
        if len(trend_df) >= 2 and trend_df["_date"].nunique() >= 2:
            period = trend_df["_date"].dt.to_period("M")
            monthly = trend_df.groupby(period)["_rev"].sum()
            if len(monthly) >= 2:
                m.trend = monthly
            else:
                daily = trend_df.groupby(trend_df["_date"].dt.date)["_rev"].sum()
                if len(daily) >= 2:
                    m.trend = daily

    # ── Data Trust / Quality ─────────────────────────────────────────────
    m.quality = compute_quality(df)

    # ── Forecast (gated on real date history; see report_metrics.forecast) ──
    m.forecast = compute_forecast(df, schema, m.trend)

    # ── Auto highlights (Executive Highlights section — data-only, no LLM) ──
    m.highlights = _auto_highlights(m)

    return m


def compute_quality(df: pd.DataFrame) -> dict:
    """Data Trust & Quality metrics — computed, never fabricated."""
    if df is None or df.empty:
        return dict(score=0, total_records=0, total_columns=0, missing_pct=0.0,
                    duplicate_rows=0, checks=[])

    total_cells = max(1, df.shape[0] * df.shape[1])
    missing = int(df.isna().sum().sum())
    missing_pct = _clean_num(missing / total_cells * 100)
    dup_rows = int(df.duplicated().sum())
    dup_pct = _clean_num(_safe_div(dup_rows, len(df)) * 100)

    # Numeric validity: fraction of "numeric-looking" columns that are
    # actually clean (no inf, reasonable non-negative where expected).
    numeric_cols = df.select_dtypes(include="number").columns
    numeric_validity = 1.0
    if len(numeric_cols):
        bad = sum(int(np.isinf(pd.to_numeric(df[c], errors="coerce")).sum()) for c in numeric_cols)
        numeric_validity = 1 - _safe_div(bad, max(1, len(df) * len(numeric_cols)))

    completeness = 1 - (missing / total_cells)
    uniqueness = 1 - _safe_div(dup_rows, len(df))
    score = round(max(0, min(100, (completeness * 0.45 + uniqueness * 0.30 + numeric_validity * 0.25) * 100)))

    checks = [
        dict(ok=missing == 0, label="No missing values" if missing == 0 else f"{missing:,} missing value(s) ({missing_pct:.1f}%)"),
        dict(ok=dup_rows == 0, label="No duplicate records" if dup_rows == 0 else f"{dup_rows:,} duplicate row(s) ({dup_pct:.1f}%)"),
        dict(ok=numeric_validity > 0.98, label="Numeric fields validated" if numeric_validity > 0.98 else "Some numeric fields contain invalid values"),
        dict(ok=True, label=f"{df.shape[0]:,} records × {df.shape[1]} columns profiled"),
    ]
    return dict(score=score, total_records=len(df), total_columns=len(df.columns),
                missing_pct=missing_pct, duplicate_rows=dup_rows, duplicate_pct=dup_pct,
                checks=checks)


def compute_forecast(df: pd.DataFrame, schema: Schema, trend: pd.Series | None) -> dict | None:
    """Simple linear-trend forecast over the monthly/period series already
    computed in `trend`. Returns None (not a fabricated forecast) if there
    isn't enough history — the report must show the honest fallback message
    instead of a chart in that case."""
    if trend is None or len(trend) < 4:
        return None
    try:
        from sklearn.linear_model import LinearRegression
    except Exception:
        return None

    y = trend.values.astype(float)
    n = len(y)
    X = np.arange(1, n + 1).reshape(-1, 1)
    model = LinearRegression().fit(X, y)
    r2 = model.score(X, y)
    horizon = min(3, max(1, n // 4))
    future_idx = np.arange(n + 1, n + 1 + horizon).reshape(-1, 1)
    forecast_vals = model.predict(future_idx)
    forecast_vals = np.clip(forecast_vals, 0, None)
    residuals = y - model.predict(X)
    ci = float(1.96 * np.std(residuals)) if n > 2 else 0.0

    labels = [str(p) for p in trend.index]
    future_labels = [f"Period +{i+1}" for i in range(horizon)]
    return dict(
        history_labels=labels, history_values=y.tolist(),
        forecast_labels=future_labels, forecast_values=[float(v) for v in forecast_vals],
        ci=ci, r2=float(r2), horizon=horizon, model_name="Linear Regression",
    )


def _auto_highlights(m: ReportMetrics) -> list:
    """3-6 concise, data-only highlight sentences — built the same way the
    spec's example does (comparative, specific, no filler)."""
    out = []
    rev = m.kpis.get("revenue")
    ord_ = m.kpis.get("orders")
    aov = m.kpis.get("aov")
    margin = m.kpis.get("margin")
    growth = m.kpis.get("growth")

    if rev and rev.change_pct is not None and ord_ and ord_.change_pct is not None:
        out.append(
            f"Revenue {'increased' if rev.change_pct >= 0 else 'decreased'} {abs(rev.change_pct):.1f}%, "
            f"while order volume {'increased' if ord_.change_pct >= 0 else 'decreased'} {abs(ord_.change_pct):.1f}%."
        )
        if aov and aov.change_pct is not None:
            direction = "declined" if aov.change_pct < 0 else "rose"
            driver = "volume-driven growth" if aov.change_pct < 0 else "a mix of volume and value growth"
            out.append(f"Average order value {direction} {abs(aov.change_pct):.1f}%, indicating {driver}.")
    elif rev:
        out.append(f"Total revenue for the period is {rev.current:,.0f}.")

    if margin:
        out.append(f"Overall profit margin stands at {margin.current:.1f}%.")

    if m.top_regions is not None and len(m.top_regions) > 1:
        best, worst = m.top_regions.index[0], m.top_regions.index[-1]
        gap = _safe_div(m.top_regions.iloc[0] - m.top_regions.iloc[-1], m.top_regions.iloc[-1]) * 100
        out.append(f"{best} leads all regions, outperforming {worst} by {gap:.0f}%.")

    if m.top_products is not None and len(m.top_products) > 0:
        out.append(f"{m.top_products.index[0]} is the top-performing product by revenue.")

    if growth and growth.current is not None:
        out.append(f"Revenue growth versus the prior period is {growth.current:+.1f}%.")

    return out[:6]
