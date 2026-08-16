"""
data_engine.chart_commands
──────────────────────────────
Turns short natural-language chart commands ("switch to a bar chart",
"show profit instead", "top 5") into ChartConfig mutations — entirely with
keyword matching, no LLM call required for these common cases. This keeps
basic two-way AI control fast and free; a real LLM (BlinkBot/Nova Analyst)
can still be layered on top for open-ended questions like "why did this
change", which needs actual reasoning rather than a config edit.
"""

import re

_CHART_TYPE_WORDS = {
    "bar": "bar", "horizontal bar": "horizontal_bar", "bar chart": "bar",
    "line": "line", "line chart": "line", "trend": "line",
    "pie": "pie", "pie chart": "pie", "donut": "donut", "doughnut": "donut",
    "scatter": "scatter", "table": "table",
}
_AGG_WORDS = {
    "sum": "sum", "total": "sum", "average": "mean", "avg": "mean", "mean": "mean",
    "count": "count", "median": "median", "minimum": "min", "min": "min",
    "maximum": "max", "max": "max",
}


def apply_command(config: dict, df_columns: list, roles: dict, command: str) -> tuple:
    """Returns (new_config, message). Never raises — an unrecognized
    command returns the config unchanged with an explanatory message."""
    q = command.lower().strip()
    new_config = dict(config)
    changes = []

    for phrase, chart_type in sorted(_CHART_TYPE_WORDS.items(), key=lambda x: -len(x[0])):
        if phrase in q and ("chart" in q or "graph" in q or phrase in ("scatter", "table")):
            new_config["chart_type"] = chart_type
            changes.append(f"chart type → {chart_type.replace('_', ' ')}")
            break

    for word, agg in _AGG_WORDS.items():
        if re.search(rf"\b{word}\b", q):
            new_config["aggregation"] = agg
            changes.append(f"aggregation → {agg}")
            break

    n_match = re.search(r"top\s+(\d+)|(\d+)\s+(?:cities|categories|products|items|rows)", q)
    if n_match:
        n = int(n_match.group(1) or n_match.group(2))
        new_config["top_n"] = n
        new_config["sort"] = "desc"
        changes.append(f"top N → {n}")
    elif "bottom" in q:
        b_match = re.search(r"bottom\s+(\d+)", q)
        if b_match:
            new_config["top_n"] = int(b_match.group(1))
            new_config["sort"] = "asc"
            changes.append(f"bottom N → {b_match.group(1)}")

    dimension_cols = [c for c, r in roles.items() if r == "Dimension"]
    measure_cols = [c for c, r in roles.items() if r == "Measure"]

    for col in dimension_cols:
        if re.search(rf"\b(show|by|change to|switch to)\s+{re.escape(col.lower())}\b", q):
            new_config["dimension"] = col
            changes.append(f"dimension → {col}")
            break

    for col in measure_cols:
        if re.search(rf"\b(show|change to|switch to)\s+{re.escape(col.lower())}\b", q):
            new_config["metric"] = col
            changes.append(f"metric → {col}")
            break

    if not changes:
        return config, (
            "I couldn't map that to a change — try things like 'switch to a bar chart', "
            "'show top 5', 'change dimension to City', or 'use average instead of sum'."
        )
    return new_config, "Updated: " + ", ".join(changes) + "."
