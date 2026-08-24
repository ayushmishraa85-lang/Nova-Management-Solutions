"""
database/queries.py — safe, parameterized operations on novams_sales.

Every function takes an explicit `engine` (from database.connection.get_engine())
and never opens a fresh connection per call — each uses `engine.connect()`
as a short-lived context manager backed by the engine's shared connection
pool, so pooling/reuse is handled by SQLAlchemy itself.

No function here ever builds SQL by string-formatting user input. All
values pass through SQLAlchemy Core's parameter binding.
"""

from __future__ import annotations

from typing import Optional

import pandas as pd
from sqlalchemy import delete, func, select
from sqlalchemy.engine import Engine

from database.models import INSERTABLE_COLUMNS, metadata, sales_table


def create_tables(engine: Engine) -> None:
    """Idempotent — safe to call on every app start (CREATE TABLE IF NOT EXISTS)."""
    metadata.create_all(engine, checkfirst=True)


def bulk_insert(engine: Engine, records: list[dict], chunk_size: int = 1000) -> int:
    """
    Inserts records (already normalized to the target schema — see
    services/data_loader.py) in chunks, wrapped in one transaction per
    chunk. Returns the number of rows inserted. Any record key not in
    INSERTABLE_COLUMNS is silently dropped rather than raising, since the
    validator upstream is responsible for schema conformance.
    """
    if not records:
        return 0
    clean_records = [
        {k: v for k, v in rec.items() if k in INSERTABLE_COLUMNS} for rec in records
    ]
    inserted = 0
    with engine.begin() as conn:
        for i in range(0, len(clean_records), chunk_size):
            chunk = clean_records[i : i + chunk_size]
            conn.execute(sales_table.insert(), chunk)
            inserted += len(chunk)
    return inserted


def read_all(engine: Engine) -> pd.DataFrame:
    """Reads the full sales table into a DataFrame. Empty DataFrame if the table has no rows."""
    with engine.connect() as conn:
        return pd.read_sql(select(sales_table), conn)


def read_filtered(
    engine: Engine,
    city: Optional[str] = None,
    category: Optional[str] = None,
    source_file: Optional[str] = None,
) -> pd.DataFrame:
    """Reads a filtered slice — all filters are parameterized, never string-built."""
    stmt = select(sales_table)
    if city:
        stmt = stmt.where(sales_table.c.city == city)
    if category:
        stmt = stmt.where(sales_table.c.category == category)
    if source_file:
        stmt = stmt.where(sales_table.c.source_file == source_file)
    with engine.connect() as conn:
        return pd.read_sql(stmt, conn)


def count_records(engine: Engine, source_file: Optional[str] = None) -> int:
    stmt = select(func.count()).select_from(sales_table)
    if source_file:
        stmt = stmt.where(sales_table.c.source_file == source_file)
    with engine.connect() as conn:
        return int(conn.execute(stmt).scalar_one())


def list_source_files(engine: Engine) -> pd.DataFrame:
    """Summary of what's currently loaded — one row per import, with row counts."""
    stmt = (
        select(
            sales_table.c.source_file,
            func.count().label("rows"),
            func.max(sales_table.c.imported_at).label("imported_at"),
        )
        .group_by(sales_table.c.source_file)
        .order_by(func.max(sales_table.c.imported_at).desc())
    )
    with engine.connect() as conn:
        return pd.read_sql(stmt, conn)


def delete_by_source_file(engine: Engine, source_file: str) -> int:
    """
    Deletes only the rows belonging to one prior import — used when
    re-importing the same file, so re-uploads replace rather than
    duplicate. Never touches rows from any other source_file.
    """
    stmt = delete(sales_table).where(sales_table.c.source_file == source_file)
    with engine.begin() as conn:
        result = conn.execute(stmt)
        return result.rowcount or 0


def clear_table(engine: Engine) -> int:
    """Deletes every row (not the table itself). Explicit, user-triggered only."""
    stmt = delete(sales_table)
    with engine.begin() as conn:
        result = conn.execute(stmt)
        return result.rowcount or 0
