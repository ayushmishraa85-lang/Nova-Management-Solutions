"""
database/models.py — schema for the NovaMS PostgreSQL sales warehouse.

Uses SQLAlchemy Core (Table + MetaData) rather than the ORM, since this
layer only ever needs simple insert/read/delete operations — no relational
mapping, no lazy-loading concerns, and it's trivially portable to any
SQLAlchemy-supported backend for testing (this schema is verified against
both SQLite and PostgreSQL).

Column names are the *normalized* target schema. The actual uploaded
CSV/Excel file almost never matches these names exactly — see
services/data_loader.py + services/data_validator.py for the
alias-based mapping layer that translates arbitrary source columns
(e.g. "Total Revenue", "Selling Price", "Order Date") onto this schema
before anything is inserted.
"""

from __future__ import annotations

from sqlalchemy import (
    Boolean, Column, Date, DateTime, Integer, MetaData, Numeric, String, Table, func,
)

metadata = MetaData()

SALES_TABLE_NAME = "novams_sales"

sales_table = Table(
    SALES_TABLE_NAME,
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("order_id", String(128), nullable=True, index=True),
    Column("order_date", Date, nullable=True, index=True),
    Column("year", Integer, nullable=True, index=True),
    Column("month", Integer, nullable=True),
    Column("day", Integer, nullable=True),
    Column("city", String(128), nullable=True, index=True),
    Column("region", String(128), nullable=True),
    Column("store", String(128), nullable=True),
    Column("category", String(128), nullable=True, index=True),
    Column("product", String(256), nullable=True),
    Column("quantity", Integer, nullable=True),
    Column("selling_price", Numeric(14, 2), nullable=True),
    Column("cost_price", Numeric(14, 2), nullable=True),
    Column("revenue", Numeric(16, 2), nullable=True),
    Column("profit", Numeric(16, 2), nullable=True),
    Column("profit_margin", Numeric(6, 2), nullable=True),
    Column("influencer_active", Boolean, nullable=True),
    # Provenance — which upload this row came from, so a re-import of the
    # same file can safely replace only its own rows (see
    # queries.delete_by_source_file) instead of ever wiping unrelated data.
    Column("source_file", String(256), nullable=True, index=True),
    Column("imported_at", DateTime, server_default=func.now()),
)

# Columns a caller is allowed to insert (excludes the auto-generated id and
# imported_at, which the database fills in itself).
INSERTABLE_COLUMNS = [
    c.name for c in sales_table.columns if c.name not in ("id", "imported_at")
]
