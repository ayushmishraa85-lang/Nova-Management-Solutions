"""
data_engine.schema
────────────────────
Assigns a likely role — Identifier / Date / Measure / Dimension — to every
column using deterministic name + dtype rules. This runs BEFORE any AI call,
so most datasets never need an LLM just to understand their own schema
(per the spec's "reduce unnecessary AI/token usage" requirement).
"""

import pandas as pd

_MEASURE_HINTS = [
    "revenue", "sales", "profit", "cost", "price", "amount", "orders",
    "quantity", "qty", "margin", "discount", "rating", "count", "spend",
]
_DIMENSION_HINTS = [
    "category", "region", "city", "product", "segment", "channel",
    "store", "brand", "status", "type", "partner", "influencer",
]


class SchemaDetector:
    def detect(self, df: pd.DataFrame, profile: dict) -> dict:
        return {col: self._classify(col, df[col], profile) for col in df.columns}

    def _classify(self, col: str, s: pd.Series, profile: dict) -> str:
        low = col.lower()
        if col in profile["id_columns"]:
            return "Identifier"
        if col in profile["date_columns"]:
            return "Date"
        if pd.api.types.is_numeric_dtype(s):
            if any(h in low for h in _MEASURE_HINTS):
                return "Measure"
            # low-cardinality numeric columns behave like dimensions (e.g. star ratings)
            if s.nunique(dropna=True) <= max(10, int(len(s) * 0.02)):
                return "Dimension"
            return "Measure"
        if any(h in low for h in _DIMENSION_HINTS):
            return "Dimension"
        if s.nunique(dropna=True) / max(1, len(s)) < 0.5:
            return "Dimension"
        return "Unclassified"

    def confidence(self, roles: dict) -> float:
        """Fraction of columns confidently classified — a low value is the
        signal the caller can use to decide whether an AI fallback is worth it."""
        if not roles:
            return 0.0
        classified = sum(1 for r in roles.values() if r != "Unclassified")
        return round(classified / len(roles), 2)
