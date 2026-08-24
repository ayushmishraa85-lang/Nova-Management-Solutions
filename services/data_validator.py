"""
services/data_validator.py — column-normalization + validation for the
PostgreSQL sales warehouse import pipeline.

Two responsibilities, kept separate on purpose:
  1. normalize_columns()  — maps arbitrary source column names onto the
     database.models.sales_table schema, without assuming the uploaded
     file uses any particular naming convention.
  2. validate_dataframe() — checks the *normalized* data for the concrete
     problems the spec calls out (missing required columns, invalid
     dates, non-numeric numeric fields, duplicate order IDs, negative
     values, missing category/product, malformed rows), and returns a
     structured report. Nothing here silently drops or destroys data —
     it only reports; the caller (data_loader.py) decides what to do.
"""

from __future__ import annotations

import re

import numpy as np
import pandas as pd

# Target schema column -> known source-file aliases (normalized: lowercase,
# alphanumeric + spaces only, so "Order-Date", "order_date", "Order Date"
# all match the same alias).
COLUMN_ALIASES: dict[str, list[str]] = {
    "order_id":         ["order id", "orderid", "invoice id", "invoice no", "transaction id"],
    "order_date":       ["date", "order date", "sales date", "transaction date", "created at",
                          "timestamp", "invoice date", "transaction date", "purchase date"],
    "city":             ["location", "region city", "store city", "delivery city"],
    "region":           ["zone", "area", "state"],
    "store":            ["store name", "outlet", "warehouse", "branch"],
    "category":         ["product category", "segment", "item category", "type"],
    "product":          ["product name", "item name", "item", "sku", "product title"],
    "quantity":         ["orders", "units sold", "qty", "order count", "units"],
    "selling_price":    ["current price", "sale price", "final price", "price"],
    "cost_price":       ["original price", "mrp", "list price", "base price", "actual price"],
    "revenue":          ["total revenue", "sales", "amount", "sales amount", "gross revenue", "net sales"],
    "profit":           ["net profit", "total profit"],
    "profit_margin":    ["margin", "profit %", "profit percentage"],
    "influencer_active": ["influencer", "has influencer"],
}

REQUIRED_COLUMNS = ["city", "category", "product"]
NUMERIC_COLUMNS = ["quantity", "selling_price", "cost_price", "revenue", "profit", "profit_margin"]


def _normalize_colname(s: str) -> str:
    return "".join(ch for ch in str(s).lower().strip() if ch.isalnum() or ch == " ").strip()


def suggest_mapping(raw_columns: list[str]) -> dict[str, str]:
    """{raw_column_name: canonical_target_name} — suggestions only, applied by normalize_columns()."""
    norm_raw = {_normalize_colname(c): c for c in raw_columns}
    mapping = {}
    for canonical in list(COLUMN_ALIASES.keys()):
        if canonical in norm_raw:
            mapping[norm_raw[canonical]] = canonical
            continue
        if _normalize_colname(canonical.replace("_", " ")) in norm_raw:
            mapping[norm_raw[_normalize_colname(canonical.replace("_", " "))]] = canonical
            continue
        for alias in COLUMN_ALIASES[canonical]:
            if alias in norm_raw:
                mapping[norm_raw[alias]] = canonical
                break
    return mapping


def normalize_columns(raw_df: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, str]]:
    """
    Returns (df_with_canonical_columns, mapping_applied). Never assumes the
    file already uses the target names — only columns matched via
    suggest_mapping() are renamed; everything else is left as-is (and
    simply won't be inserted, since bulk_insert() only writes
    INSERTABLE_COLUMNS).
    """
    df = raw_df.copy()
    df.columns = [str(c).strip() for c in df.columns]
    mapping = suggest_mapping(list(df.columns))
    if mapping:
        df = df.rename(columns=mapping)
    return df, mapping


def validate_dataframe(df: pd.DataFrame) -> dict:
    """
    Validates an already-normalized dataframe (post normalize_columns()).
    Returns a report dict; `blocking=True` means the import must not
    proceed until the caller resolves the listed errors. Everything else
    is a warning shown to the user, not a reason to refuse the import.
    """
    errors: list[str] = []
    warnings: list[str] = []

    missing_required = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing_required:
        errors.append(
            "Missing required column(s) after mapping: " + ", ".join(missing_required) +
            ". Expected City, Category, and Product (or a recognizable equivalent)."
        )

    has_financials = ("revenue" in df.columns) or (
        "quantity" in df.columns and "selling_price" in df.columns
    )
    if not has_financials:
        errors.append(
            "Can't calculate revenue — the file needs either a Revenue column, "
            "or both a Quantity and a Selling Price column."
        )

    invalid_dates = 0
    if "order_date" in df.columns:
        original_missing = df["order_date"].isna().sum()
        parsed = pd.to_datetime(df["order_date"], errors="coerce", format="mixed")
        invalid_dates = int(parsed.isna().sum() - original_missing)
        if invalid_dates:
            warnings.append(f"{invalid_dates} row(s) have an order_date value that couldn't be parsed.")

    non_numeric: dict[str, int] = {}
    for col in NUMERIC_COLUMNS:
        if col in df.columns:
            original_missing = df[col].isna().sum()
            coerced = pd.to_numeric(df[col], errors="coerce")
            bad = int(coerced.isna().sum() - original_missing)
            if bad:
                non_numeric[col] = bad
    if non_numeric:
        warnings.append(
            "Non-numeric values found in: " +
            ", ".join(f"{c} ({n} row(s))" for c, n in non_numeric.items())
        )

    duplicate_order_ids = 0
    if "order_id" in df.columns:
        non_null_ids = df["order_id"].dropna().astype(str)
        duplicate_order_ids = int(non_null_ids.duplicated().sum())
        if duplicate_order_ids:
            warnings.append(f"{duplicate_order_ids} duplicate order_id value(s) detected.")

    negative_counts: dict[str, int] = {}
    for col in ["quantity", "selling_price", "cost_price", "revenue"]:
        if col in df.columns:
            numeric = pd.to_numeric(df[col], errors="coerce")
            neg = int((numeric < 0).sum())
            if neg:
                negative_counts[col] = neg
    if negative_counts:
        warnings.append(
            "Negative values found in: " +
            ", ".join(f"{c} ({n} row(s))" for c, n in negative_counts.items())
        )

    missing_required_values = 0
    for col in REQUIRED_COLUMNS:
        if col in df.columns:
            missing_required_values += int(df[col].isna().sum())
    if missing_required_values:
        warnings.append(f"{missing_required_values} row(s) are missing City/Category/Product.")

    malformed_rows = int(df.isna().all(axis=1).sum())
    if malformed_rows:
        warnings.append(f"{malformed_rows} completely empty row(s) will be skipped.")

    return dict(
        errors=errors,
        warnings=warnings,
        blocking=bool(errors),
        missing_required=missing_required,
        invalid_dates=invalid_dates,
        non_numeric=non_numeric,
        duplicate_order_ids=duplicate_order_ids,
        negative_counts=negative_counts,
        missing_required_values=missing_required_values,
        malformed_rows=malformed_rows,
        total_rows=len(df),
    )
