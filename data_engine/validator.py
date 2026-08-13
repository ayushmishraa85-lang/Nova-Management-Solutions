"""
data_engine.validator
────────────────────────
Flags suspicious data WITHOUT modifying it — missing values, invalid dates,
unexpected negatives, constant columns, duplicate rows, inconsistent
category naming. The Cleaner decides what (if anything) to do about each flag.
"""

import difflib

import pandas as pd


class Validator:
    def validate(self, df: pd.DataFrame, roles: dict) -> list:
        issues = []
        if len(df) == 0:
            return [dict(severity="High", issue="Dataset has zero rows.", column=None)]

        for col in df.columns:
            s = df[col]
            missing_pct = float(s.isna().mean()) * 100
            if missing_pct > 0:
                sev = "High" if missing_pct > 20 else "Medium" if missing_pct > 5 else "Low"
                issues.append(dict(severity=sev, issue=f"{missing_pct:.1f}% missing values", column=col))

            if s.nunique(dropna=True) <= 1:
                issues.append(dict(severity="Medium", issue="Column has a constant or empty value", column=col))

            role = roles.get(col)
            if role == "Measure" and pd.api.types.is_numeric_dtype(s):
                neg = int((s.dropna() < 0).sum())
                if neg and any(k in col.lower() for k in ["revenue", "price", "orders", "quantity", "cost", "amount"]):
                    issues.append(dict(
                        severity="Medium",
                        issue=f"{neg} negative value(s) in a column normally expected to be non-negative",
                        column=col,
                    ))
            if role == "Date":
                parsed = pd.to_datetime(s, errors="coerce", format="mixed")
                invalid = int(parsed.isna().sum() - s.isna().sum())
                if invalid > 0:
                    issues.append(dict(severity="Medium", issue=f"{invalid} value(s) could not be parsed as dates", column=col))

        dup = int(df.duplicated().sum())
        if dup:
            issues.append(dict(severity="Medium", issue=f"{dup} exact duplicate row(s)", column=None))

        for col in [c for c, r in roles.items() if r == "Dimension" and df[c].dtype == object]:
            issues.extend(self._check_inconsistent_categories(df, col))

        return issues

    def _check_inconsistent_categories(self, df: pd.DataFrame, col: str) -> list:
        uniques = [str(v) for v in df[col].dropna().unique()]
        if len(uniques) < 2:
            return []
        seen, groups = set(), []
        for v in uniques:
            if v in seen:
                continue
            close = [m for m in difflib.get_close_matches(v, uniques, n=4, cutoff=0.85) if m != v]
            if close:
                group = sorted(set([v] + close))
                seen.update(group)
                groups.append(group)
        return [
            dict(severity="Low", issue=f"Possible inconsistent naming: {', '.join(g)}", column=col)
            for g in groups
        ]
