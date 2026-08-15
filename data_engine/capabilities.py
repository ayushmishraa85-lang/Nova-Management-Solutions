"""
data_engine.capabilities
────────────────────────────
Decides what analyses a dataset can honestly support, based on which
semantic concepts were mapped with sufficient confidence (see
semantic_mapper.py). This is the single place that decision gets made —
NovaMS should never generate a revenue KPI without a revenue-like measure,
and never generate a time-series forecast without a real, confident date
column.
"""

_CONFIDENCE_THRESHOLD = 0.6


class CapabilityEngine:
    def evaluate(self, mappings: list) -> dict:
        by_concept = {}
        for m in mappings:
            if m["confidence"] >= _CONFIDENCE_THRESHOLD:
                by_concept.setdefault(m["semantic_name"], []).append(m["original_name"])

        has = lambda c: c in by_concept
        cols = lambda c: ", ".join(by_concept.get(c, []))

        caps = {}
        caps["time_series_analysis"] = self._cap(
            has("date") and (has("revenue") or has("quantity") or has("cost")),
            "Requires a confidently-mapped date column plus at least one numeric measure.",
            f"Enabled via {cols('date')} + {cols('revenue') or cols('quantity') or cols('cost')}",
        )
        caps["forecasting"] = self._cap(
            caps["time_series_analysis"]["enabled"],
            "Forecasting needs the same date + measure combination as time-series analysis.",
            "Enabled — same basis as time-series analysis",
        )
        caps["revenue_kpis"] = self._cap(
            has("revenue"),
            "No column was confidently mapped to revenue/sales.",
            f"Enabled via {cols('revenue')}",
        )
        caps["profitability_analysis"] = self._cap(
            has("revenue") and (has("cost") or has("profit")),
            "Requires both a revenue-like and a cost/profit-like column.",
            f"Enabled via {cols('revenue')} and {cols('cost') or cols('profit')}",
        )
        caps["category_performance"] = self._cap(
            has("category") and (has("revenue") or has("quantity")),
            "Requires a category-style dimension plus a numeric measure.",
            f"Enabled via {cols('category')}",
        )
        caps["regional_analysis"] = self._cap(
            (has("region") or has("city")) and (has("revenue") or has("quantity")),
            "Requires a region/city column plus a numeric measure.",
            f"Enabled via {cols('region') or cols('city')}",
        )
        caps["customer_analysis"] = self._cap(
            has("customer_id") and (has("revenue") or has("quantity")),
            "Requires a customer identifier plus a numeric measure.",
            f"Enabled via {cols('customer_id')}",
        )
        caps["hr_analysis"] = self._cap(
            has("salary") or (has("employee_id") and has("department")),
            "Requires a salary column, or an employee ID plus a department column.",
            f"Enabled via {cols('salary') or (cols('employee_id') + ' + ' + cols('department'))}",
        )
        return caps

    def _cap(self, enabled: bool, disabled_reason: str, enabled_reason: str) -> dict:
        return dict(enabled=bool(enabled), reason=enabled_reason if enabled else disabled_reason)
