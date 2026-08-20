"""
report_eda.py — Notebook / Lab Report Analysis Planner
==========================================================
Drives the second report style: a chart-by-chart academic EDA report (like
the "Airline Passenger Satisfaction Analysis" reference) — Objective, Data
Cleaning, then a sequence of [chart + "Interpretation:" paragraph] blocks,
ending in a Conclusion.

Unlike the fixed airline-specific notebook, this planner is schema-agnostic:
it inspects whatever dataset is loaded and decides which of the standard EDA
chart types actually apply (target distribution, categorical breakdowns,
numeric distributions, spread, relationship, group comparison, correlation),
skipping anything the data can't honestly support — same "never invent,
never show an empty section" rule as the Executive report.

Every interpretation sentence is generated from the real computed numbers
in this file — nothing here is written by an LLM.
"""

from __future__ import annotations
import numpy as np
import pandas as pd
from dataclasses import dataclass, field


def _is_text_dtype(series: pd.Series) -> bool:
    """True for classic object-dtype columns AND pandas' newer native
    string dtype (pandas >= 2.x with `future.infer_string`, or pandas 3.x
    where plain strings default to dtype "str"/StringDtype instead of
    "object"). Using only `dtype == object` silently misses every text
    column on newer pandas — this keeps the EDA planner correct either way."""
    return (pd.api.types.is_object_dtype(series) or pd.api.types.is_string_dtype(series)) \
        and not pd.api.types.is_numeric_dtype(series)


_ID_LIKE_HINTS = ["id", "unnamed", "index", "row"]
_TARGET_NAME_HINTS = ["satisfaction", "status", "outcome", "target", "label",
                       "churn", "result", "class_label", "response", "approved"]


def _is_id_like(col: str, series: pd.Series, n_rows: int) -> bool:
    name = col.lower().strip()
    if any(h in name for h in _ID_LIKE_HINTS):
        return True
    if series.nunique(dropna=True) >= max(20, int(n_rows * 0.9)):
        return True
    return False


@dataclass
class EDAPlan:
    target_col: str | None = None
    categorical_cols: list = field(default_factory=list)   # for pie / group-compare charts
    numeric_cols: list = field(default_factory=list)       # for histogram / boxplot / scatter / corr
    warnings: list = field(default_factory=list)


def plan_eda(df: pd.DataFrame) -> EDAPlan:
    plan = EDAPlan()
    if df is None or df.empty:
        plan.warnings.append("Dataset is empty.")
        return plan

    n_rows = len(df)
    obj_cols = [c for c in df.columns if _is_text_dtype(df[c]) and not _is_id_like(c, df[c], n_rows)]
    num_cols = [c for c in df.select_dtypes(include="number").columns if not _is_id_like(c, df[c], n_rows)]

    # ── Target column: prefer a name match, else any well-balanced binary/
    # low-cardinality categorical column.
    target = None
    for c in obj_cols:
        if any(h in c.lower() for h in _TARGET_NAME_HINTS):
            target = c
            break
    if not target:
        candidates = [c for c in obj_cols if 2 <= df[c].nunique(dropna=True) <= 6]
        if candidates:
            # Prefer the most balanced one (closest to 50/50 for binary, or
            # most even spread for multi-class) — a skewed near-constant
            # column makes for a boring/uninformative "target" chart.
            def _balance_score(c):
                counts = df[c].value_counts(normalize=True)
                return -counts.std()  # lower std = more balanced = higher score
            candidates.sort(key=_balance_score, reverse=True)
            target = candidates[0]

    plan.target_col = target
    remaining_obj = [c for c in obj_cols if c != target]
    plan.categorical_cols = [c for c in remaining_obj if df[c].nunique(dropna=True) <= 10][:4]
    plan.numeric_cols = num_cols[:8]

    if not plan.target_col and not plan.categorical_cols and not plan.numeric_cols:
        plan.warnings.append("No usable categorical or numeric columns were detected for analysis.")

    return plan


# ── Helpers ──────────────────────────────────────────────────────────────

def data_cleaning_summary(raw_df: pd.DataFrame, clean_df: pd.DataFrame) -> dict:
    dup = int(raw_df.duplicated().sum())
    missing_by_col = raw_df.isna().sum()
    missing_by_col = missing_by_col[missing_by_col > 0]
    return dict(
        rows_before=len(raw_df), cols_before=len(raw_df.columns),
        rows_after=len(clean_df), duplicates=dup,
        missing_by_col={str(k): int(v) for k, v in missing_by_col.items()},
        dtypes={str(c): str(t) for c, t in raw_df.dtypes.items()},
    )


def target_distribution(df: pd.DataFrame, target_col: str) -> dict:
    counts = df[target_col].value_counts()
    total = counts.sum()
    top_label, top_val = counts.index[0], int(counts.iloc[0])
    interpretation = (
        f"The chart shows that {top_val:,} records fall under \u2018{top_label}\u2019"
        + (f", while {int(counts.iloc[1]):,} fall under \u2018{counts.index[1]}\u2019" if len(counts) > 1 else "")
        + f", indicating that \u2018{top_label}\u2019 is the {'larger' if len(counts) > 1 else 'dominant'} group "
        f"in the dataset ({top_val/total*100:.1f}% of records)."
    )
    return dict(labels=[str(i) for i in counts.index], values=[int(v) for v in counts.values],
                interpretation=interpretation)


def categorical_breakdown(df: pd.DataFrame, col: str, max_slices: int = 6) -> dict:
    counts = df[col].value_counts()
    if len(counts) > max_slices:
        head = counts.head(max_slices - 1)
        other = counts.iloc[max_slices - 1:].sum()
        counts = pd.concat([head, pd.Series({"Other": other})])
    total = counts.sum()
    top_label, top_pct = counts.index[0], counts.iloc[0] / total * 100
    interpretation = (
        f"The pie chart shows that \u2018{top_label}\u2019 forms the majority at {top_pct:.1f}% of {col}, "
        + (f"while \u2018{counts.index[-1]}\u2019 represents the smallest share "
           f"({counts.iloc[-1]/total*100:.1f}%)." if len(counts) > 1 else ".")
    )
    return dict(labels=[str(i) for i in counts.index], values=[float(v) for v in counts.values],
                interpretation=interpretation)


def numeric_distribution(df: pd.DataFrame, col: str) -> dict:
    s = pd.to_numeric(df[col], errors="coerce").dropna()
    if len(s) < 5:
        return dict(values=[], interpretation="Not enough data to summarize this column.")
    mode_bin_desc = f"{s.quantile(0.25):.0f}\u2013{s.quantile(0.75):.0f}"
    skew = s.skew()
    shape_note = ("fairly symmetric" if abs(skew) < 0.5 else
                  "right-skewed, with a long tail of higher values" if skew >= 0.5 else
                  "left-skewed, with a long tail of lower values")
    interpretation = (
        f"Most values are concentrated between {mode_bin_desc} (the middle 50%), with a median of "
        f"{s.median():.1f}. The distribution is {shape_note}."
    )
    return dict(values=s.tolist(), interpretation=interpretation, median=float(s.median()))


def numeric_spread(df: pd.DataFrame, col: str) -> dict:
    s = pd.to_numeric(df[col], errors="coerce").dropna()
    if len(s) < 5:
        return dict(values=[], interpretation="Not enough data to summarize this column.")
    q1, q3 = s.quantile(0.25), s.quantile(0.75)
    iqr = q3 - q1
    outliers = int(((s < q1 - 1.5 * iqr) | (s > q3 + 1.5 * iqr)).sum())
    interpretation = (
        f"The box plot shows a median of {s.median():.1f}, with the middle 50% of values falling between "
        f"{q1:.1f} and {q3:.1f}. "
        + (f"{outliers} value(s) fall outside the typical range and are flagged as outliers."
           if outliers > 0 else "No significant outliers are present.")
    )
    return dict(values=s.tolist(), interpretation=interpretation)


def numeric_relationship(df: pd.DataFrame, col_x: str, col_y: str) -> dict:
    sub = df[[col_x, col_y]].apply(pd.to_numeric, errors="coerce").dropna()
    if len(sub) < 5:
        return dict(x=[], y=[], interpretation="Not enough paired data to assess this relationship.")
    r = sub[col_x].corr(sub[col_y])
    if pd.isna(r):
        r = 0.0
    strength = "no clear" if abs(r) < 0.15 else "a weak" if abs(r) < 0.35 else "a moderate" if abs(r) < 0.6 else "a strong"
    direction = "" if abs(r) < 0.15 else (" positive" if r > 0 else " negative")
    interpretation = (
        f"The scatter plot shows {strength}{direction} relationship between {col_x} and {col_y} "
        f"(correlation r = {r:.2f})."
    )
    return dict(x=sub[col_x].tolist(), y=sub[col_y].tolist(), interpretation=interpretation, r=float(r))


def group_comparison(df: pd.DataFrame, group_col: str, target_col: str, max_groups: int = 8) -> dict:
    ct = pd.crosstab(df[group_col], df[target_col])
    if len(ct) > max_groups:
        ct = ct.loc[ct.sum(axis=1).sort_values(ascending=False).head(max_groups).index]
    # Find the group with the highest share of the "first" target category
    first_target_val = ct.columns[0]
    shares = ct[first_target_val] / ct.sum(axis=1)
    best_group = shares.idxmax()
    worst_group = shares.idxmin()
    interpretation = (
        f"\u2018{best_group}\u2019 has the highest proportion of \u2018{first_target_val}\u2019 "
        f"({shares[best_group]*100:.0f}%), while \u2018{worst_group}\u2019 has the lowest "
        f"({shares[worst_group]*100:.0f}%) \u2014 suggesting {group_col} has a meaningful influence on {target_col}."
    )
    return dict(categories=[str(i) for i in ct.index],
                series={str(c): ct[c].tolist() for c in ct.columns},
                interpretation=interpretation)


def correlation_analysis(df: pd.DataFrame, numeric_cols: list) -> dict | None:
    if len(numeric_cols) < 3:
        return None
    corr = df[numeric_cols].apply(pd.to_numeric, errors="coerce").corr()
    # Find the strongest off-diagonal pair
    corr_abs = corr.abs().to_numpy(copy=True)
    np.fill_diagonal(corr_abs, 0)
    if corr_abs.max() == 0:
        strongest_note = "No strong linear relationships were found among the numeric variables."
    else:
        idx = np.unravel_index(np.argmax(corr_abs), corr_abs.shape)
        c1, c2 = corr.index[idx[0]], corr.columns[idx[1]]
        r = corr.iloc[idx]
        strongest_note = f"The strongest relationship is between {c1} and {c2} (r = {r:.2f})."
    interpretation = (
        "The heatmap shows the correlation between numerical variables in the dataset, helping identify "
        f"strong and weak relationships. {strongest_note}"
    )
    return dict(corr=corr, interpretation=interpretation)


def build_conclusion(dataset_name: str, plan: EDAPlan, n_rows: int, n_cols: int) -> str:
    bits = [
        f"This report analyzed the {dataset_name} dataset ({n_rows:,} records, {n_cols} columns) "
        f"using Python-based data cleaning, analysis, and visualization."
    ]
    if plan.target_col:
        bits.append(f"The analysis centered on \u2018{plan.target_col}\u2019 as the primary outcome of interest.")
    covered = []
    if plan.categorical_cols:
        covered.append("categorical breakdowns")
    if plan.numeric_cols:
        covered.append("numeric distributions and spread")
    if len(plan.numeric_cols) >= 2:
        covered.append("relationships between variables")
    if covered:
        bits.append(f"Charts covered {', '.join(covered)}, using histograms, box plots, bar charts, "
                     f"pie charts, scatter plots, and a correlation heatmap where applicable.")
    bits.append("Overall, the analysis surfaces the key patterns and relationships present in the data.")
    return " ".join(bits)
