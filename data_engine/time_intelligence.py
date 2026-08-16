"""
data_engine.time_intelligence
──────────────────────────────
Turns a detected Date column into monthly time intelligence: derived time
dimensions, monthly aggregation with a semantically-aware aggregation
function per measure (SUM for revenue/quantity, AVG for price/discount —
not a blind SUM of every numeric column), MoM/YoY growth with safe
zero/null handling, a date-range honesty check, seasonality, and a simple
monthly forecast — each gated behind a minimum amount of history so nothing
here claims a trend the data can't actually support. Nothing modifies the
original dataset; everything is derived into a separate working frame.
"""

import numpy as np
import pandas as pd

# Canonical semantic concept -> aggregation function for monthly rollups.
_AGG_BY_CONCEPT = {
    "revenue": "sum", "cost": "sum", "profit": "sum", "quantity": "sum",
    "price": "mean", "discount": "mean", "salary": "mean",
}
_MIN_MONTHS_FOR_YOY = 13
_MIN_MONTHS_FOR_SEASONALITY = 24
_MIN_MONTHS_FOR_FORECAST = 6


class TimeIntelligence:
    def parse_dates(self, df: pd.DataFrame, date_col: str) -> pd.Series:
        return pd.to_datetime(df[date_col], errors="coerce", format="mixed")

    def date_range_summary(self, df: pd.DataFrame, date_col: str) -> dict:
        dates = self.parse_dates(df, date_col).dropna()
        if dates.empty:
            return dict(valid=False)
        start, end = dates.min(), dates.max()
        return dict(
            valid=True, start=start, end=end, span_days=(end - start).days + 1,
            distinct_months=dates.dt.to_period("M").nunique(),
            distinct_years=dates.dt.year.nunique(), total_records=len(dates),
        )

    def agg_func_for(self, semantic_mappings: list, column: str) -> str:
        for m in semantic_mappings:
            if m["original_name"] == column and m["confidence"] >= 0.6:
                return _AGG_BY_CONCEPT.get(m["semantic_name"], "sum")
        return "sum"  # honest default for an unmapped measure, not a silent guess

    def build_monthly_table(self, df: pd.DataFrame, date_col: str, measure_cols: list, semantic_mappings: list) -> pd.DataFrame:
        work = df[[date_col] + measure_cols].copy()
        work[date_col] = self.parse_dates(work, date_col)
        work = work.dropna(subset=[date_col])
        if work.empty:
            return pd.DataFrame()
        work["Year"] = work[date_col].dt.year
        work["Month_Number"] = work[date_col].dt.month
        work["Month_Name"] = work[date_col].dt.strftime("%b")
        work["Quarter"] = "Q" + work[date_col].dt.quarter.astype(str)
        work["Year_Month"] = work[date_col].dt.to_period("M").astype(str)

        agg_dict = {c: self.agg_func_for(semantic_mappings, c) for c in measure_cols}
        grouped = work.groupby(["Year_Month", "Year", "Month_Number", "Month_Name", "Quarter"], as_index=False).agg(agg_dict)
        return grouped.sort_values(["Year", "Month_Number"]).reset_index(drop=True)

    def mom_growth(self, monthly: pd.DataFrame, measure: str) -> dict:
        if len(monthly) < 2:
            return dict(available=False)
        current, previous = monthly.iloc[-1], monthly.iloc[-2]
        cur_val, prev_val = current[measure], previous[measure]
        growth = None if (pd.isna(prev_val) or prev_val == 0) else (cur_val - prev_val) / abs(prev_val) * 100
        return dict(
            available=True, current_period=current["Year_Month"], previous_period=previous["Year_Month"],
            current_value=cur_val, previous_value=prev_val, growth_pct=growth,
        )

    def yoy_growth(self, monthly: pd.DataFrame, measure: str) -> dict:
        if len(monthly) < _MIN_MONTHS_FOR_YOY:
            return dict(available=False, reason=f"Needs at least {_MIN_MONTHS_FOR_YOY} months of history; this file has {len(monthly)}.")
        current = monthly.iloc[-1]
        match = monthly[(monthly["Month_Number"] == current["Month_Number"]) & (monthly["Year"] == current["Year"] - 1)]
        if match.empty:
            return dict(available=False, reason="No matching month found exactly one year earlier.")
        prev = match.iloc[0]
        cur_val, prev_val = current[measure], prev[measure]
        growth = None if (pd.isna(prev_val) or prev_val == 0) else (cur_val - prev_val) / abs(prev_val) * 100
        return dict(
            available=True, current_period=current["Year_Month"], previous_period=prev["Year_Month"],
            current_value=cur_val, previous_value=prev_val, growth_pct=growth,
        )

    def seasonality(self, monthly: pd.DataFrame, measure: str) -> dict:
        if len(monthly) < _MIN_MONTHS_FOR_SEASONALITY:
            return dict(available=False, reason=f"Needs at least {_MIN_MONTHS_FOR_SEASONALITY} months (2 full years) of history; this file has {len(monthly)}.")
        overall_mean = monthly[measure].mean()
        by_month = monthly.groupby("Month_Name")[measure].mean()
        order = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
        by_month = by_month.reindex([m for m in order if m in by_month.index])
        deviation_pct = ((by_month - overall_mean) / overall_mean * 100).round(1) if overall_mean else by_month * 0
        return dict(available=True, deviation_by_month=deviation_pct.to_dict())

    def forecast_monthly(self, monthly: pd.DataFrame, measure: str, periods: int = 3) -> dict:
        if len(monthly) < _MIN_MONTHS_FOR_FORECAST:
            return dict(available=False, reason=f"Needs at least {_MIN_MONTHS_FOR_FORECAST} months of history; this file has {len(monthly)}.")
        from sklearn.linear_model import LinearRegression
        y = monthly[measure].values.astype(float)
        X = np.arange(len(y)).reshape(-1, 1)
        model = LinearRegression().fit(X, y)
        future_X = np.arange(len(y), len(y) + periods).reshape(-1, 1)
        forecast_vals = np.clip(model.predict(future_X), 0, None)
        last_period = pd.Period(monthly.iloc[-1]["Year_Month"], freq="M")
        forecast_periods = [str(last_period + i) for i in range(1, periods + 1)]
        return dict(
            available=True, r2=round(float(model.score(X, y)), 3),
            actual_periods=monthly["Year_Month"].tolist(), actual_values=y.tolist(),
            forecast_periods=forecast_periods, forecast_values=forecast_vals.tolist(),
        )

    def category_by_month(self, df: pd.DataFrame, date_col: str, dimension_col: str, measure_col: str, agg: str = "sum") -> pd.DataFrame:
        work = df[[date_col, dimension_col, measure_col]].copy()
        work[date_col] = self.parse_dates(work, date_col)
        work = work.dropna(subset=[date_col])
        if work.empty:
            return pd.DataFrame()
        work["Year_Month"] = work[date_col].dt.to_period("M").astype(str)
        pivot = work.pivot_table(index=dimension_col, columns="Year_Month", values=measure_col, aggfunc=agg, fill_value=0)
        return pivot[pivot.columns[-12:]]  # cap at the most recent 12 months so it never explodes
