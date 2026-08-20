"""
report_schema.py — Schema Detection & Validation Layer
========================================================
Inspects a dataset BEFORE any report generation happens and figures out,
honestly, what the file actually contains. Nothing downstream is allowed to
assume a column exists — every section of the report checks `Schema.has(...)`
first and omits itself cleanly if the data isn't there.

Design rules (from the report spec):
- Never blindly assume equivalence (e.g. "Amount" == Revenue) — validate the
  column is actually numeric and plausible before mapping it.
- Never invent a column that doesn't exist.
- Must not crash on missing columns, weird dtypes, empty data, etc.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
import pandas as pd
import numpy as np


# Canonical concept -> alias keywords (normalized: lowercase, alnum + space only)
_ALIASES = {
    "revenue":  ["revenue", "total revenue", "sales", "net sales", "gross revenue",
                 "sales amount", "amount", "total sales", "order value"],
    "profit":   ["profit", "net profit", "gross profit", "margin amount", "net income"],
    "cogs":     ["cogs", "cost of goods sold", "cost", "total cost"],
    "orders":   ["orders", "order count", "units sold", "quantity", "qty", "units"],
    "date":     ["date", "order date", "transaction date", "invoice date", "created at",
                 "created", "timestamp", "order_date", "month", "period"],
    "city":     ["city", "location", "region", "store city", "delivery city", "market"],
    "state":    ["state", "province"],
    "country":  ["country"],
    "category": ["category", "product category", "segment", "type", "department"],
    "product":  ["product name", "product", "item", "item name", "sku", "product title"],
    "brand":    ["brand"],
    "customer": ["customer id", "customer", "client id", "user id"],
    "discount": ["discount", "discount %", "discount percentage", "discount pct"],
    "price":    ["price", "current price", "selling price", "unit price"],
    "delivery_time": ["delivery time", "delivery minutes", "time to deliver"],
    "cancelled": ["cancelled", "canceled", "cancellation"],
}


def _norm(s: str) -> str:
    return "".join(ch for ch in str(s).lower().strip() if ch.isalnum() or ch == " ").strip()


def _is_numeric(series: pd.Series) -> bool:
    coerced = pd.to_numeric(series, errors="coerce")
    valid_ratio = coerced.notna().mean() if len(series) else 0
    return valid_ratio >= 0.8  # allow some dirty values, but must be mostly numeric


def _is_datelike(series: pd.Series) -> bool:
    try:
        coerced = pd.to_datetime(series, errors="coerce", format="mixed")
    except Exception:
        try:
            coerced = pd.to_datetime(series, errors="coerce")
        except Exception:
            return False
    valid_ratio = coerced.notna().mean() if len(series) else 0
    return valid_ratio >= 0.7


@dataclass
class Schema:
    """Validated concept -> real column-name mapping. Every field is either a
    real column name present in the dataframe, or None."""
    revenue: str | None = None
    profit: str | None = None
    cogs: str | None = None
    orders: str | None = None
    date: str | None = None
    city: str | None = None
    state: str | None = None
    country: str | None = None
    category: str | None = None
    product: str | None = None
    brand: str | None = None
    customer: str | None = None
    discount: str | None = None
    price: str | None = None
    delivery_time: str | None = None
    cancelled: str | None = None

    financial_extra: list = field(default_factory=list)   # other plausible numeric $ columns
    dimension_extra: list = field(default_factory=list)   # other plausible categorical columns
    warnings: list = field(default_factory=list)

    def has(self, *concepts: str) -> bool:
        return all(getattr(self, c, None) is not None for c in concepts)

    def has_geo(self) -> bool:
        return self.has("city") or self.has("state") or self.has("country")

    def geo_col(self) -> str | None:
        for c in ("city", "state", "country"):
            v = getattr(self, c)
            if v:
                return v
        return None

    def any_dimension(self) -> list:
        dims = [c for c in (self.category, self.product, self.brand, self.city) if c]
        return dims + self.dimension_extra


def detect_schema(df: pd.DataFrame) -> Schema:
    """Detect the report-relevant schema of `df`. Never raises — worst case
    returns a mostly-empty Schema with warnings explaining what's missing."""
    schema = Schema()
    if df is None or df.empty:
        schema.warnings.append("Dataset is empty — no columns could be validated.")
        return schema

    norm_cols = {_norm(c): c for c in df.columns}
    used: set[str] = set()

    def _claim(concept: str, must_be_numeric: bool = False, must_be_date: bool = False) -> str | None:
        # 1. Exact/alias name match
        candidates = [concept] + _ALIASES.get(concept, [])
        for cand in candidates:
            key = _norm(cand)
            if key in norm_cols:
                real_col = norm_cols[key]
                if real_col in used:
                    continue
                series = df[real_col]
                if must_be_numeric and not _is_numeric(series):
                    continue
                if must_be_date and not _is_datelike(series):
                    continue
                used.add(real_col)
                return real_col
        return None

    schema.revenue  = _claim("revenue", must_be_numeric=True)
    schema.profit   = _claim("profit", must_be_numeric=True)
    schema.cogs     = _claim("cogs", must_be_numeric=True)
    schema.orders   = _claim("orders", must_be_numeric=True)
    schema.date     = _claim("date", must_be_date=True)
    schema.city     = _claim("city")
    schema.state    = _claim("state")
    schema.country  = _claim("country")
    schema.category = _claim("category")
    schema.product  = _claim("product")
    schema.brand    = _claim("brand")
    schema.customer = _claim("customer")
    schema.discount = _claim("discount", must_be_numeric=True)
    schema.price    = _claim("price", must_be_numeric=True)
    schema.delivery_time = _claim("delivery_time", must_be_numeric=True)
    schema.cancelled = _claim("cancelled")

    # Fallback: if Profit wasn't found but Revenue and COGS exist, that's a
    # legitimate derived metric (computed later, not invented here).
    if not schema.revenue:
        schema.warnings.append(
            "No Revenue-equivalent column detected — financial KPIs will be limited or omitted."
        )

    # Extra plausible numeric/dimension columns (not already claimed), used
    # for optional "Customer / Operational" style pages.
    for col in df.columns:
        if col in used:
            continue
        series = df[col]
        if pd.api.types.is_numeric_dtype(series) or _is_numeric(series):
            if any(k in _norm(col) for k in ["cost", "price", "amount", "revenue", "spend", "value", "fee"]):
                schema.financial_extra.append(col)
        elif (pd.api.types.is_object_dtype(series) or pd.api.types.is_string_dtype(series)) \
                and not pd.api.types.is_numeric_dtype(series) \
                and 1 < series.nunique(dropna=True) <= max(50, int(len(df) * 0.5)):
            schema.dimension_extra.append(col)

    return schema
