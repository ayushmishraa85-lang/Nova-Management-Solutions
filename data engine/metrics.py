"""
data_engine/metrics.py
Metric Engine — Part 8 of the NovaMS Data Engine spec.

All calculations happen in pandas — never delegated to an LLM. A metric
is only computed (and only appears in the output) when every column it
needs is actually present; nothing is invented or estimated.
"""
from __future__ import annotations

from typing import Any, Dict

import pandas as pd

# column-role -> candidate raw column name keywords, checked in order.
_CANDIDATES = {
    "revenue":  ["total revenue", "revenue", "sales", "amount", "gross revenue", "net sales"],
    "cost":     ["cogs", "cost", "total cost"],
    "profit":   ["profit", "net profit"],
    "orders":   ["orders", "order count", "order_id", "quantity", "units", "units sold"],
    "sessions": ["sessions", "visits", "website sessions"],
    "refunds":  ["refund", "refunds", "returned"],
    "customer_id": ["customer_id", "customer id", "user_id", "user id"],
    "discount": ["discount"],
}


def _find_column(df: pd.DataFrame, keywords: list[str]) -> str | None:
    lower_map = {c.lower().strip(): c for c in df.columns}
    for kw in keywords:
        if kw in lower_map:
            return lower_map[kw]
    # loose substring fallback
    for kw in keywords:
        for lower_name, original in lower_map.items():
            if kw in lower_name:
                return original
    return None


def compute_metrics(df: pd.DataFrame) -> Dict[str, Dict[str, Any]]:
    """
    Returns {metric_name: {"value": float, "formula": str, "inputs": [cols]}}
    — only for metrics whose required columns were actually found.
    """
    cols = {role: _find_column(df, kws) for role, kws in _CANDIDATES.items()}
    metrics: Dict[str, Dict[str, Any]] = {}

    revenue_sum = None
    if cols["revenue"]:
        revenue_sum = float(pd.to_numeric(df[cols["revenue"]], errors="coerce").sum())
        metrics["revenue"] = dict(value=revenue_sum, formula="sum(revenue_column)", inputs=[cols["revenue"]])

    orders_count = None
    if cols["orders"]:
        orders_series = pd.to_numeric(df[cols["orders"]], errors="coerce")
        # If the "orders" column looks like a row-count identifier (order_id),
        # count rows instead of summing; otherwise sum a quantity/units column.
        if orders_series.notna().mean() < 0.5:
            orders_count = float(len(df))
        else:
            orders_count = float(orders_series.sum())
        metrics["orders"] = dict(value=orders_count, formula="sum(orders_column) or row count",
                                  inputs=[cols["orders"]])

    if revenue_sum is not None and orders_count:
        metrics["aov"] = dict(value=round(revenue_sum / orders_count, 4),
                               formula="Revenue / Orders", inputs=[cols["revenue"], cols["orders"]])

    profit_sum = None
    if cols["profit"]:
        profit_sum = float(pd.to_numeric(df[cols["profit"]], errors="coerce").sum())
        metrics["profit"] = dict(value=profit_sum, formula="sum(profit_column)", inputs=[cols["profit"]])
    elif revenue_sum is not None and cols["cost"]:
        cost_sum = float(pd.to_numeric(df[cols["cost"]], errors="coerce").sum())
        profit_sum = revenue_sum - cost_sum
        metrics["profit"] = dict(value=profit_sum, formula="Revenue - COGS",
                                  inputs=[cols["revenue"], cols["cost"]])

    if profit_sum is not None and revenue_sum:
        metrics["profit_margin"] = dict(value=round(profit_sum / revenue_sum * 100, 4),
                                         formula="Profit / Revenue * 100",
                                         inputs=[cols["revenue"]])

    if cols["refunds"] and orders_count:
        refund_sum = float(pd.to_numeric(df[cols["refunds"]], errors="coerce").sum())
        metrics["refund_rate"] = dict(value=round(refund_sum / orders_count * 100, 4),
                                       formula="Refunds / Orders * 100",
                                       inputs=[cols["refunds"], cols["orders"]])

    if orders_count is not None and cols["sessions"]:
        sessions_sum = float(pd.to_numeric(df[cols["sessions"]], errors="coerce").sum())
        if sessions_sum:
            metrics["conversion_rate"] = dict(value=round(orders_count / sessions_sum * 100, 4),
                                               formula="Orders / Sessions * 100",
                                               inputs=[cols["orders"], cols["sessions"]])

    if cols["customer_id"]:
        cust_series = df[cols["customer_id"]].dropna()
        n_customers = int(cust_series.nunique())
        metrics["customer_count"] = dict(value=float(n_customers),
                                          formula="nunique(customer_id)", inputs=[cols["customer_id"]])
        if n_customers:
            counts = cust_series.value_counts()
            repeat = int((counts > 1).sum())
            metrics["repeat_customer_rate"] = dict(
                value=round(repeat / n_customers * 100, 4),
                formula="customers_with_>1_orders / total_customers * 100",
                inputs=[cols["customer_id"]],
            )

    if cols["discount"]:
        metrics["avg_discount"] = dict(
            value=round(float(pd.to_numeric(df[cols["discount"]], errors="coerce").mean()), 4),
            formula="mean(discount_column)", inputs=[cols["discount"]],
        )

    return metrics
