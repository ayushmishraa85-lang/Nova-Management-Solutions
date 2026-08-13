"""
data_engine.transformer
───────────────────────────
Computes reusable business metrics (Profit, Margin, AOV, ...) — but ONLY
when the columns they depend on actually exist. Nothing is fabricated for a
metric whose inputs aren't present in the dataset.
"""

import pandas as pd


class Transformer:
    def compute_metrics(self, df: pd.DataFrame, roles: dict) -> dict:
        cols_lower = {c.lower(): c for c in df.columns}

        def find(*keywords):
            for kw in keywords:
                for lower, orig in cols_lower.items():
                    if kw in lower:
                        return orig
            return None

        revenue_col = find("total revenue", "revenue", "sales", "amount")
        cost_col = find("cost", "cogs")
        orders_col = find("orders", "quantity", "qty")
        profit_col = find("profit")

        metrics = {}

        if revenue_col:
            total_rev = float(pd.to_numeric(df[revenue_col], errors="coerce").sum())
            metrics["total_revenue"] = dict(value=total_rev, formula=f"SUM({revenue_col})")

        if profit_col:
            metrics["profit"] = dict(
                value=float(pd.to_numeric(df[profit_col], errors="coerce").sum()),
                formula=f"SUM({profit_col})",
            )
        elif revenue_col and cost_col:
            rev = pd.to_numeric(df[revenue_col], errors="coerce")
            cost = pd.to_numeric(df[cost_col], errors="coerce")
            metrics["profit"] = dict(
                value=float((rev - cost).sum()),
                formula=f"SUM({revenue_col} - {cost_col})",
            )

        if "profit" in metrics and "total_revenue" in metrics and metrics["total_revenue"]["value"]:
            metrics["profit_margin_pct"] = dict(
                value=metrics["profit"]["value"] / metrics["total_revenue"]["value"] * 100,
                formula="Profit / Total Revenue x 100",
            )

        if orders_col:
            orders_total = float(pd.to_numeric(df[orders_col], errors="coerce").sum())
            metrics["total_orders"] = dict(value=orders_total, formula=f"SUM({orders_col})")
            if orders_total and "total_revenue" in metrics:
                metrics["average_order_value"] = dict(
                    value=metrics["total_revenue"]["value"] / orders_total,
                    formula=f"SUM({revenue_col}) / SUM({orders_col})",
                )

        return metrics
