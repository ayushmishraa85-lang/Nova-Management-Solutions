"""
data_engine.root_cause
──────────────────────────
Generic, schema-agnostic root-cause drill-down. Given a metric and
whichever Dimension columns actually exist in the current dataset, this
walks from broad to narrow (State → City → Area → Store → Category →
Product → SKU, whenever those are present — any other dimension still
participates, just after the known hierarchy hints) and finds, at each
step, which specific value contributes most to a weakness or a decline —
built entirely from real aggregates. Nothing here invents a dimension the
data doesn't have, and nothing claims a cause without showing the number
behind it.
"""

import pandas as pd

# Ordering hints only — used to walk broad-to-narrow when multiple
# dimensions are available. A dimension not in this list still
# participates in the drill-down, just after the recognized ones.
_HIERARCHY_ORDER_HINTS = [
    "state", "region", "city", "area", "pincode", "store", "dark store",
    "category", "subcategory", "brand", "product", "sku",
]


def order_dimensions(dimensions: list) -> list:
    def rank(col):
        low = col.lower()
        for i, hint in enumerate(_HIERARCHY_ORDER_HINTS):
            if hint in low:
                return i
        return len(_HIERARCHY_ORDER_HINTS)
    return sorted(dimensions, key=rank)


def find_weakest_segment(df: pd.DataFrame, dimension: str, metric: str, agg: str = "sum") -> dict | None:
    if dimension not in df.columns or metric not in df.columns:
        return None
    series = df.groupby(dimension)[metric].agg(agg).sort_values()
    if series.empty:
        return None
    total = series.sum()
    return dict(
        dimension=dimension, value=series.index[0], metric_value=float(series.iloc[0]),
        share_of_total=float(series.iloc[0] / total * 100) if total else 0,
        n_segments=len(series),
    )


def drill_down_weakest(df: pd.DataFrame, dimensions: list, metric: str, agg: str = "sum", max_levels: int = 4) -> list:
    """Walks the given dimensions broad-to-narrow, narrowing the working
    dataframe to the weakest segment at each level, and returns the
    evidence chain — exactly the 'City → Store → Category → Product'
    style drill-down a Quick-Commerce analyst would do by hand."""
    ordered = order_dimensions([d for d in dimensions if d in df.columns])
    chain = []
    working_df = df
    for dim in ordered[:max_levels]:
        if working_df[dim].nunique(dropna=True) < 2:
            continue  # nothing to differentiate on at this level — skip, don't fabricate
        weak = find_weakest_segment(working_df, dim, metric, agg)
        if weak is None:
            break
        chain.append(weak)
        working_df = working_df[working_df[dim] == weak["value"]]
        if len(working_df) < 2:
            break
    return chain


def contributors_to_change(current_df: pd.DataFrame, previous_df: pd.DataFrame,
                            dimension: str, metric: str, agg: str = "sum", top_n: int = 5) -> list:
    """Ranks each value of `dimension` by how much it contributed to the
    overall change in `metric` between two periods — the 'main
    contributors' list behind a MoM/WoW decline, e.g. which stores or
    categories drove a revenue drop, in order of impact."""
    if dimension not in current_df.columns or dimension not in previous_df.columns:
        return []
    cur = current_df.groupby(dimension)[metric].agg(agg)
    prev = previous_df.groupby(dimension)[metric].agg(agg)
    both = pd.DataFrame({"current": cur, "previous": prev}).fillna(0)
    both["change"] = both["current"] - both["previous"]
    both = both.reindex(both["change"].abs().sort_values(ascending=False).index)
    total_change = both["change"].sum()
    results = []
    for name, row in both.head(top_n).iterrows():
        results.append(dict(
            value=name, current=float(row["current"]), previous=float(row["previous"]),
            change=float(row["change"]),
            contribution_pct=float(row["change"] / total_change * 100) if total_change else 0,
        ))
    return results
