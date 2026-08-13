"""
data_engine.profiler
─────────────────────
Builds a structural profile of a raw DataFrame — row/column counts, missing
values, duplicates, per-column stats, and candidate ID/date columns — BEFORE
anything is validated, cleaned, or transformed. Nothing here mutates the
input DataFrame.
"""

import pandas as pd


class DataProfiler:
    def profile(self, df: pd.DataFrame) -> dict:
        n_rows, n_cols = df.shape
        n_cells = max(1, n_rows * n_cols)
        missing_total = int(df.isna().sum().sum())
        dup_rows = int(df.duplicated().sum())

        date_cols = self._detect_date_columns(df)
        numeric_cols = [c for c in df.select_dtypes(include="number").columns]
        categorical_cols = [
            c for c in df.select_dtypes(include="object").columns if c not in date_cols
        ]
        id_cols = self._detect_id_columns(df)

        return dict(
            rows=n_rows,
            columns=n_cols,
            missing_total=missing_total,
            missing_pct=round(missing_total / n_cells * 100, 2),
            duplicate_rows=dup_rows,
            duplicate_pct=round(dup_rows / max(1, n_rows) * 100, 2),
            numeric_columns=numeric_cols,
            categorical_columns=categorical_cols,
            date_columns=date_cols,
            id_columns=id_cols,
            column_profiles={c: self._profile_column(df[c]) for c in df.columns},
        )

    def _profile_column(self, s: pd.Series) -> dict:
        prof = dict(
            dtype=str(s.dtype),
            missing=int(s.isna().sum()),
            missing_pct=round(float(s.isna().mean()) * 100, 2),
            unique=int(s.nunique(dropna=True)),
            constant=bool(s.nunique(dropna=True) <= 1),
        )
        if pd.api.types.is_numeric_dtype(s):
            clean = s.dropna()
            if len(clean):
                prof.update(
                    min=float(clean.min()),
                    max=float(clean.max()),
                    mean=float(clean.mean()),
                    negative_count=int((clean < 0).sum()),
                )
        return prof

    def _detect_date_columns(self, df: pd.DataFrame) -> list:
        found = []
        for col in df.columns:
            if pd.api.types.is_datetime64_any_dtype(df[col]):
                found.append(col)
                continue
            if df[col].dtype != object:
                continue
            hint = any(k in col.lower() for k in ["date", "time", "created", "updated", "timestamp"])
            if not hint:
                continue
            sample = df[col].dropna().astype(str).head(20)
            if sample.empty:
                continue
            parsed = pd.to_datetime(sample, errors="coerce", format="mixed")
            if parsed.notna().mean() > 0.7:
                found.append(col)
        return found

    def _detect_id_columns(self, df: pd.DataFrame) -> list:
        found = []
        for col in df.columns:
            hint = any(k in col.lower() for k in ["id", "code", "sku", "uuid"])
            uniqueness = df[col].nunique(dropna=True) / max(1, len(df))
            if hint and uniqueness > 0.9:
                found.append(col)
        return found
