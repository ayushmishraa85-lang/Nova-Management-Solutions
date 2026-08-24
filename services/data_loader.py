"""
services/data_loader.py — orchestrates the full import pipeline:

    raw upload -> normalize_columns() -> validate_dataframe()
    -> prepare_records() -> database.queries.bulk_insert()

Only ever called explicitly by the user confirming an import (see the
"PostgreSQL Sales Warehouse" section in streamlit_app.py) — nothing here
runs automatically or silently on page load.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from sqlalchemy.engine import Engine

from database import queries as db_queries
from services.data_validator import normalize_columns, validate_dataframe

_TRUTHY = {"yes", "y", "true", "1", "1.0"}
_FALSY = {"no", "n", "false", "0", "0.0"}


def _coerce_bool(v) -> bool | None:
    if pd.isna(v):
        return None
    if isinstance(v, bool):
        return v
    s = str(v).strip().lower()
    if s in _TRUTHY:
        return True
    if s in _FALSY:
        return False
    return None


def prepare_records(df: pd.DataFrame, source_file: str) -> tuple[list[dict], int]:
    """
    Converts a normalized (but still raw-typed) dataframe into a list of
    plain-Python dicts ready for database.queries.bulk_insert() — deriving
    revenue/profit/profit_margin where they're computable but missing, and
    year/month/day from order_date where present. Completely empty rows
    are dropped. Returns (records, skipped_malformed_row_count).
    """
    work = df.copy()
    before = len(work)
    work = work.dropna(how="all")
    skipped = before - len(work)

    if "order_date" in work.columns:
        work["_dt"] = pd.to_datetime(work["order_date"], errors="coerce", format="mixed")
    else:
        work["_dt"] = pd.NaT

    for col in ["quantity", "selling_price", "cost_price", "revenue", "profit", "profit_margin"]:
        if col in work.columns:
            work[col] = pd.to_numeric(work[col], errors="coerce")
        else:
            work[col] = np.nan

    # Derive revenue from quantity * selling_price when revenue itself is missing.
    needs_revenue = work["revenue"].isna()
    if needs_revenue.any():
        derivable = needs_revenue & work["quantity"].notna() & work["selling_price"].notna()
        work.loc[derivable, "revenue"] = work.loc[derivable, "quantity"] * work.loc[derivable, "selling_price"]

    # Derive profit from revenue - (cost_price * quantity) when possible.
    needs_profit = work["profit"].isna()
    if needs_profit.any():
        derivable = (
            needs_profit & work["revenue"].notna() & work["cost_price"].notna() & work["quantity"].notna()
        )
        work.loc[derivable, "profit"] = work.loc[derivable, "revenue"] - (
            work.loc[derivable, "cost_price"] * work.loc[derivable, "quantity"]
        )

    # Derive margin from profit / revenue when possible.
    needs_margin = work["profit_margin"].isna()
    if needs_margin.any():
        derivable = needs_margin & work["profit"].notna() & work["revenue"].notna() & (work["revenue"] != 0)
        work.loc[derivable, "profit_margin"] = (
            work.loc[derivable, "profit"] / work.loc[derivable, "revenue"] * 100
        )

    records: list[dict] = []
    for _, row in work.iterrows():
        dt = row["_dt"]
        has_date = pd.notna(dt)
        rec = dict(
            order_id=str(row["order_id"]).strip() if "order_id" in work.columns and pd.notna(row.get("order_id")) else None,
            order_date=dt.date() if has_date else None,
            year=int(dt.year) if has_date else None,
            month=int(dt.month) if has_date else None,
            day=int(dt.day) if has_date else None,
            city=str(row["city"]).strip() if "city" in work.columns and pd.notna(row.get("city")) else None,
            region=str(row["region"]).strip() if "region" in work.columns and pd.notna(row.get("region")) else None,
            store=str(row["store"]).strip() if "store" in work.columns and pd.notna(row.get("store")) else None,
            category=str(row["category"]).strip() if "category" in work.columns and pd.notna(row.get("category")) else None,
            product=str(row["product"]).strip() if "product" in work.columns and pd.notna(row.get("product")) else None,
            quantity=int(row["quantity"]) if pd.notna(row.get("quantity")) else None,
            selling_price=float(row["selling_price"]) if pd.notna(row.get("selling_price")) else None,
            cost_price=float(row["cost_price"]) if pd.notna(row.get("cost_price")) else None,
            revenue=float(row["revenue"]) if pd.notna(row.get("revenue")) else None,
            profit=float(row["profit"]) if pd.notna(row.get("profit")) else None,
            profit_margin=float(row["profit_margin"]) if pd.notna(row.get("profit_margin")) else None,
            influencer_active=_coerce_bool(row.get("influencer_active")) if "influencer_active" in work.columns else None,
            source_file=source_file,
        )
        records.append(rec)

    return records, int(skipped)


def load_and_import(
    raw_df: pd.DataFrame, filename: str, engine: Engine, replace_existing: bool = True
) -> dict:
    """
    Full pipeline entry point. Returns a result dict:
        success, rows_imported, rows_replaced, mapping_applied, validation
    `validation` always contains the full validate_dataframe() report,
    even on success, so warnings are never silently dropped.
    Raises nothing — database/network errors are caught and reported in
    the result dict instead of crashing the app.
    """
    df, mapping = normalize_columns(raw_df)
    validation = validate_dataframe(df)

    result = dict(
        success=False, rows_imported=0, rows_replaced=0,
        mapping_applied=mapping, validation=validation, error=None,
    )

    if validation["blocking"]:
        return result

    try:
        db_queries.create_tables(engine)
        if replace_existing:
            result["rows_replaced"] = db_queries.delete_by_source_file(engine, filename)
        records, _skipped = prepare_records(df, filename)
        result["rows_imported"] = db_queries.bulk_insert(engine, records)
        result["success"] = True
    except Exception as e:
        result["error"] = str(e)

    return result
