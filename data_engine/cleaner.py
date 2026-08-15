"""
data_engine.cleaner
──────────────────────
Applies a controlled, logged set of cleaning operations. Every change is
recorded so the caller can show "Raw Data → Processed Data" — nothing here
happens silently, and the original DataFrame passed in is never mutated
in place (a copy is returned).
"""

import pandas as pd


class Cleaner:
    def clean(self, df: pd.DataFrame, roles: dict) -> tuple[pd.DataFrame, list]:
        log = []
        out = df.copy()

        before = len(out)
        out = out.drop_duplicates()
        if before != len(out):
            log.append(f"Removed {before - len(out)} duplicate row(s)")

        out.columns = [str(c).strip() for c in out.columns]

        empty_cols = [c for c in out.columns if out[c].isna().all()]
        if empty_cols:
            out = out.drop(columns=empty_cols)
            log.append(f"Dropped empty column(s): {', '.join(empty_cols)}")

        for col, role in roles.items():
            if col not in out.columns:
                continue
            if role == "Measure" and pd.api.types.is_numeric_dtype(out[col]):
                n_missing = int(out[col].isna().sum())
                if n_missing:
                    out[col] = out[col].fillna(out[col].median())
                    log.append(f"Imputed {n_missing} missing value(s) in '{col}' with the column median")
            elif role == "Dimension" and (pd.api.types.is_object_dtype(out[col]) or pd.api.types.is_string_dtype(out[col])):
                n_missing = int(out[col].isna().sum())
                if n_missing and not out[col].mode().empty:
                    out[col] = out[col].fillna(out[col].mode()[0])
                    log.append(f"Filled {n_missing} missing value(s) in '{col}' with the most common value")
                out[col] = out[col].astype(str).str.strip()
            elif role == "Date":
                parsed = pd.to_datetime(out[col], errors="coerce", format="mixed")
                n_invalid = int(parsed.isna().sum() - out[col].isna().sum())
                out[col] = parsed
                if n_invalid:
                    log.append(f"Standardized '{col}' to datetime — {n_invalid} value(s) could not be parsed and are now null")

        if not log:
            log.append("No cleaning operations were necessary — dataset was already clean")

        return out, log
