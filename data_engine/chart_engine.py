"""
data_engine.chart_engine
────────────────────────────
A reusable, schema-agnostic chart configuration engine — the core of the
two-way (manual + AI) dynamic visualization system. A ChartConfig dict
drives everything: what data gets aggregated, how, and which chart type
renders it. Both the manual dropdown controls and the natural-language
command parser (chart_commands.py) mutate the SAME config dict, so they
stay perfectly in sync — neither one is a special case of the other.

Nothing here performs LLM calls or requires one; every calculation is
plain pandas, matching the token-efficiency requirement that the LLM only
ever handles intent, never arithmetic.
"""

import pandas as pd

_AGG_FUNCS = {
    "sum": "sum", "average": "mean", "mean": "mean", "count": "count",
    "count_distinct": pd.Series.nunique, "median": "median",
    "min": "min", "max": "max",
}

CHART_TYPES_BY_SHAPE = {
    ("categorical", "numeric"): ["bar", "horizontal_bar", "pie", "donut", "table"],
    ("temporal", "numeric"): ["line", "bar", "table"],
    ("numeric", "numeric"): ["scatter", "table"],
    (None, "numeric"): ["table"],
}


def default_config(dimension: str | None, metric: str, chart_type: str = "bar") -> dict:
    return dict(
        chart_type=chart_type, dimension=dimension, metric=metric, metric2=None,
        aggregation="sum", top_n=10, sort="desc",
    )


def recommend_chart_types(dimension_kind: str | None, metric_kind: str = "numeric") -> list:
    return CHART_TYPES_BY_SHAPE.get((dimension_kind, metric_kind), ["table"])


def aggregate_chart_data(df: pd.DataFrame, config: dict) -> pd.Series:
    """Runs the actual pandas aggregation described by the config. This is
    the ONLY place chart data gets computed — both manual controls and AI
    commands go through this same function, so results are always
    identical regardless of who changed the config."""
    metric = config["metric"]
    dimension = config.get("dimension")
    agg = _AGG_FUNCS.get(config.get("aggregation", "sum"), "sum")

    if dimension and dimension in df.columns:
        series = df.groupby(dimension)[metric].agg(agg)
    else:
        series = pd.Series({metric: df[metric].agg(agg)})

    ascending = config.get("sort", "desc") == "asc"
    series = series.sort_values(ascending=ascending)

    top_n = config.get("top_n")
    if top_n and dimension:
        series = series.head(top_n) if not ascending else series.head(top_n)

    return series


def compute_chart_insight(series: pd.Series, config: dict) -> str:
    """Deterministic, data-grounded insight text — no LLM. Every number in
    this string comes directly from the aggregated series."""
    if series.empty:
        return "No data available for this combination."
    metric, dim = config["metric"], config.get("dimension")
    total = series.sum()
    leader, leader_val = series.index[0], series.iloc[0]
    share = (leader_val / total * 100) if total else 0
    avg = series.mean()
    vs_avg = ((leader_val - avg) / avg * 100) if avg else 0

    parts = [f"**{leader}** leads with **{leader_val:,.2f}**"]
    if dim and len(series) > 1:
        parts.append(f", representing {share:.1f}% of the total and {vs_avg:+.0f}% vs the {dim.lower()} average")
    if len(series) > 1:
        weakest, weakest_val = series.index[-1], series.iloc[-1]
        parts.append(f". **{weakest}** trails at **{weakest_val:,.2f}**")
    return "".join(parts) + "."


def build_figure(series: pd.Series, config: dict, palette: list):
    """Renders the aggregated series as the requested chart type. Returns a
    plotly graph_objects Figure. Falls back to a table-friendly bar if the
    requested chart type doesn't suit the data shape (e.g. pie with 30+
    slices), rather than producing an unreadable chart."""
    import plotly.graph_objects as go

    chart_type = config["chart_type"]
    metric, dim = config["metric"], config.get("dimension") or "Value"
    labels = series.index.astype(str).tolist()
    values = series.values.tolist()
    colors = [palette[i % len(palette)] for i in range(len(series))]

    if chart_type in ("pie", "donut") and len(series) > 12:
        chart_type = "bar"  # too many slices to read — degrade gracefully, don't crash

    if chart_type == "horizontal_bar":
        fig = go.Figure(go.Bar(x=values, y=labels, orientation="h", marker_color=colors))
    elif chart_type == "line":
        fig = go.Figure(go.Scatter(x=labels, y=values, mode="lines+markers", line=dict(width=2)))
    elif chart_type in ("pie", "donut"):
        fig = go.Figure(go.Pie(labels=labels, values=values, hole=0.55 if chart_type == "donut" else 0,
                                marker=dict(colors=colors), textinfo="label+percent"))
        if chart_type == "donut":
            fig.add_annotation(text=f"<b>{sum(values):,.0f}</b><br>Total {metric}", showarrow=False, font=dict(size=13))
    elif chart_type == "scatter":
        fig = go.Figure(go.Scatter(x=labels, y=values, mode="markers", marker=dict(size=10, color=colors)))
    elif chart_type == "table":
        fig = go.Figure(go.Table(
            header=dict(values=[dim, metric]),
            cells=dict(values=[labels, [f"{v:,.2f}" for v in values]]),
        ))
    else:  # bar (default)
        fig = go.Figure(go.Bar(x=labels, y=values, marker_color=colors))

    title_verb = {"sum": "Total", "mean": "Average", "count": "Count of", "median": "Median",
                  "min": "Minimum", "max": "Maximum", "count_distinct": "Distinct count of"}
    verb = title_verb.get(config.get('aggregation', 'sum'), '')
    metric_title = metric if metric.lower().startswith(verb.lower()) else f"{verb} {metric}".strip()
    fig.update_layout(
        title=metric_title + (f" by {dim}" if config.get("dimension") else ""),
        margin=dict(l=10, r=10, t=40, b=10), height=340,
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    )
    return fig
