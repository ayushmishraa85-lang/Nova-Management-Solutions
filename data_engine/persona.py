"""
data_engine.persona
───────────────────────
Turns the deterministic Data Engine output (column roles) into a short,
persona-tailored insight briefing — no LLM call required. Manager, HR, and
Analyst personas each surface a different subset/framing of the SAME
underlying facts; nothing is fabricated per persona, only prioritized
differently, and every persona falls back honestly when the data doesn't
support that view (e.g. HR insights on a toy-sales file).
"""

import numpy as np
import pandas as pd


class PersonaInsightGenerator:
    def generate(self, df: pd.DataFrame, roles: dict, persona: str) -> list:
        measures = [c for c, r in roles.items() if r == "Measure" and c in df.columns and pd.api.types.is_numeric_dtype(df[c])]
        dimensions = [c for c, r in roles.items() if r == "Dimension" and c in df.columns]
        dates = [c for c, r in roles.items() if r == "Date" and c in df.columns]

        if persona == "HR":
            return self._hr_insights(df, measures, dimensions, dates)
        if persona == "Analyst":
            return self._analyst_insights(df, measures, dimensions, dates)
        return self._manager_insights(df, measures, dimensions, dates)

    # ---------- shared helper ----------
    def _top_breakdown(self, df, measure, dimension, n=3):
        try:
            g = df.groupby(dimension)[measure].sum().sort_values(ascending=False)
        except Exception:
            return None
        return g.head(n) if len(g) else None

    # ---------- Manager view: revenue/volume, best & worst segment, trend ----------
    def _manager_insights(self, df, measures, dimensions, dates):
        bullets = []
        if measures:
            top_measure = measures[0]
            total = df[top_measure].sum()
            bullets.append(f"Total {top_measure}: **{total:,.2f}** across {len(df):,} record(s).")
            if dimensions:
                top = self._top_breakdown(df, top_measure, dimensions[0])
                if top is not None and len(top):
                    share = f" ({top.iloc[0]/total*100:.1f}% of total)" if total else ""
                    bullets.append(f"**{top.index[0]}** leads on {top_measure} by {dimensions[0]} at **{top.iloc[0]:,.2f}**{share}.")
                    if len(top) > 1:
                        bullets.append(f"**{top.index[-1]}** trails furthest behind in this breakdown — a candidate for review.")
        if dates and measures:
            bullets.append(f"A time trend is available on **{dates[0]}** — check the trend chart for momentum.")
        if not bullets:
            bullets.append("Not enough numeric/categorical structure was detected to summarize this file for a manager view.")
        else:
            bullets.append("**Recommendation:** protect the top-performing segment above, and investigate the weakest one for a quick win.")
        return bullets

    # ---------- HR view: salary/department/tenure/attrition if present ----------
    def _hr_insights(self, df, measures, dimensions, dates):
        bullets = []
        cols_low = {c.lower(): c for c in df.columns}

        def find(*keywords):
            for kw in keywords:
                for lower, orig in cols_low.items():
                    if kw in lower:
                        return orig
            return None

        salary_col     = find("salary", "compensation", "pay", "wage")
        dept_col       = find("department", "team", "division")
        tenure_col     = find("tenure", "experience", "years")
        attrition_col  = find("attrition", "status", "active")

        if salary_col:
            bullets.append(f"Average {salary_col}: **{df[salary_col].mean():,.2f}** across {len(df):,} record(s).")
            if dept_col:
                top = self._top_breakdown(df, salary_col, dept_col)
                if top is not None and len(top):
                    bullets.append(f"**{top.index[0]}** has the highest total {salary_col} by {dept_col}.")
        elif dept_col:
            counts = df[dept_col].value_counts()
            if len(counts):
                bullets.append(f"**{counts.index[0]}** is the largest group in {dept_col} with {int(counts.iloc[0])} record(s).")
        if tenure_col:
            bullets.append(f"Average {tenure_col}: **{df[tenure_col].mean():,.1f}**.")
        if attrition_col:
            vc = df[attrition_col].value_counts(normalize=True)
            if len(vc):
                bullets.append(f"'{vc.index[0]}' is the most common value in {attrition_col} ({vc.iloc[0]*100:.1f}% of records).")

        if not bullets:
            bullets.append(
                "This file doesn't look like people/workforce data (no salary, department, tenure, or "
                "attrition-style columns were detected) — showing the general breakdown instead."
            )
            bullets.extend(self._manager_insights(df, measures, dimensions, dates)[:2])
        return bullets

    # ---------- Analyst view: distributions, correlation, cardinality ----------
    def _analyst_insights(self, df, measures, dimensions, dates):
        bullets = [
            f"**{len(df):,} rows × {len(df.columns)} columns.** "
            f"{len(measures)} Measure(s), {len(dimensions)} Dimension(s), {len(dates)} Date column(s) detected."
        ]
        for m in measures[:3]:
            s = df[m].dropna()
            if len(s) < 2:
                continue
            bullets.append(
                f"**{m}** — mean {s.mean():,.2f}, median {s.median():,.2f}, std {s.std():,.2f}, "
                f"range {s.min():,.2f} to {s.max():,.2f}."
            )
        if len(measures) >= 2:
            try:
                corr = df[measures].corr().round(2)
                mask = ~np.eye(len(corr), dtype=bool)
                vals = corr.where(mask)
                if not vals.isna().all().all():
                    idx = vals.abs().stack().idxmax()
                    bullets.append(f"Strongest correlation: **{idx[0]}** ↔ **{idx[1]}** (r={corr.loc[idx[0], idx[1]]}).")
            except Exception:
                pass
        for d in dimensions[:2]:
            bullets.append(f"**{d}** has {df[d].nunique(dropna=True)} distinct value(s).")
        if len(bullets) <= 1:
            bullets.append("Not enough numeric structure was detected for a statistical summary.")
        return bullets
