"""
data_engine/relationships.py
Relationship Discovery — Part 4 of the NovaMS Data Engine spec.

Finds primary/foreign-key candidates across tables. Column-name matching
is only a *trigger* to check a pair — the relationship is never reported
unless actual value overlap between the two columns validates it.
"""
from __future__ import annotations

import re
from typing import Any, Dict, List

import pandas as pd

_OVERLAP_THRESHOLD = 0.80   # fraction of child values that must exist in parent
_MIN_SAMPLE = 5


def _normalize(name: str) -> str:
    return re.sub(r"[^a-z0-9]", "", str(name).lower())


def _is_id_like(col_profile: Dict[str, Any]) -> bool:
    return col_profile["role_hint"] == "potential_id"


def discover_relationships(
    tables: Dict[str, pd.DataFrame],
    profiles: Dict[str, Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    For every pair of distinct tables, look for column-name matches where
    at least one side looks like an identifier, then validate with real
    value overlap before reporting a relationship.
    """
    relationships: List[Dict[str, Any]] = []
    table_names = list(tables.keys())

    for i, left_name in enumerate(table_names):
        for right_name in table_names[i + 1:]:
            left_df, right_df = tables[left_name], tables[right_name]
            left_cols = profiles[left_name]["columns"]
            right_cols = profiles[right_name]["columns"]

            for lcol, lprofile in left_cols.items():
                for rcol, rprofile in right_cols.items():
                    if _normalize(lcol) != _normalize(rcol):
                        continue
                    if not (_is_id_like(lprofile) or _is_id_like(rprofile)):
                        continue

                    rel = _validate_pair(left_name, lcol, left_df, right_name, rcol, right_df,
                                          lprofile, rprofile)
                    if rel:
                        relationships.append(rel)

    return relationships


def _validate_pair(
    left_name: str, lcol: str, left_df: pd.DataFrame,
    right_name: str, rcol: str, right_df: pd.DataFrame,
    lprofile: Dict[str, Any], rprofile: Dict[str, Any],
) -> Dict[str, Any] | None:
    l_vals = left_df[lcol].dropna()
    r_vals = right_df[rcol].dropna()
    if len(l_vals) < _MIN_SAMPLE or len(r_vals) < _MIN_SAMPLE:
        return None

    l_set, r_set = set(l_vals.astype(str)), set(r_vals.astype(str))
    if not l_set or not r_set:
        return None

    # Try both directions — whichever side is the parent (unique) key.
    l_is_unique = lprofile["cardinality_ratio"] >= 0.98
    r_is_unique = rprofile["cardinality_ratio"] >= 0.98

    if r_is_unique and not l_is_unique:
        parent_set, child_name, parent_name = r_set, left_name, right_name
        overlap = len(l_set & r_set) / len(l_set)
        rel_type = "many_to_one"
        left_table, left_column, right_table, right_column = left_name, lcol, right_name, rcol
    elif l_is_unique and not r_is_unique:
        overlap = len(r_set & l_set) / len(r_set)
        rel_type = "one_to_many"
        left_table, left_column, right_table, right_column = left_name, lcol, right_name, rcol
    elif l_is_unique and r_is_unique:
        overlap = len(l_set & r_set) / max(len(l_set), 1)
        rel_type = "one_to_one"
        left_table, left_column, right_table, right_column = left_name, lcol, right_name, rcol
    else:
        overlap = len(l_set & r_set) / min(len(l_set), len(r_set))
        rel_type = "many_to_many"
        left_table, left_column, right_table, right_column = left_name, lcol, right_name, rcol

    if overlap < _OVERLAP_THRESHOLD:
        return None

    confidence = round(min(1.0, overlap), 4)
    return dict(
        relationship=f"{left_table}.{left_column} -> {right_table}.{right_column}",
        left_table=left_table, left_column=left_column,
        right_table=right_table, right_column=right_column,
        type=rel_type, confidence=confidence,
    )
