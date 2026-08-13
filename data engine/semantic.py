"""
data_engine/semantic.py
Semantic Column Understanding — Part 5 of the NovaMS Data Engine spec.

Rule-based classifier that assigns each column a business role:
IDENTIFIER / DATE / MEASURE / DIMENSION / MARKETING / CUSTOMER / PRODUCT /
UNKNOWN. Uses column name keywords first, falling back to the structural
role_hint from profiler.py (dtype + cardinality + sample values) when the
name alone is ambiguous.
"""
from __future__ import annotations

import re
from typing import Any, Dict

_KEYWORDS = {
    "IDENTIFIER": ["customer_id", "order_id", "product_id", "user_id", "id", "code", "sku", "uuid"],
    "DATE": ["order_date", "created_at", "signup_date", "date", "timestamp", "_at", "_on", "time"],
    "MEASURE": ["revenue", "price", "quantity", "cost", "profit", "amount", "sales", "qty", "units",
                "margin", "aov", "spend", "budget"],
    "DIMENSION": ["category", "region", "country", "city", "state", "segment", "type", "tier", "status"],
    "MARKETING": ["source", "medium", "campaign", "channel", "influencer", "ad_", "utm_"],
    "CUSTOMER": ["customer", "user", "account", "client", "member"],
    "PRODUCT": ["product", "sku", "item", "brand"],
}

_ORDER = ["IDENTIFIER", "DATE", "MARKETING", "CUSTOMER", "PRODUCT", "MEASURE", "DIMENSION"]


def _normalize(name: str) -> str:
    return re.sub(r"[^a-z0-9_]", "", str(name).lower().replace(" ", "_"))


def classify_column(col_name: str, col_profile: Dict[str, Any]) -> str:
    norm = _normalize(col_name)

    for role in _ORDER:
        for kw in _KEYWORDS[role]:
            if kw in norm:
                return role

    # Fall back to the structural hint computed during profiling.
    hint_map = {
        "potential_id": "IDENTIFIER",
        "potential_date": "DATE",
        "potential_numeric_measure": "MEASURE",
        "potential_categorical": "DIMENSION",
    }
    return hint_map.get(col_profile.get("role_hint", "unknown"), "UNKNOWN")


def classify_table(profile: Dict[str, Any]) -> Dict[str, str]:
    """Returns {column_name: ROLE} for every column in a table profile."""
    return {name: classify_column(name, col_profile) for name, col_profile in profile["columns"].items()}
