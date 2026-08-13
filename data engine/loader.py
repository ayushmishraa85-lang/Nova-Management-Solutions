"""
data_engine/loader.py
Universal data loader — Part 1 of the NovaMS Data Engine spec.

Detects file type automatically (CSV / XLSX / XLS / JSON), loads one or
many files, splits multi-sheet Excel workbooks into separate tables, and
never mutates the caller's original files. Every table gets a unique
internal name so downstream modules (profiler, relationships, etc.) can
refer to it unambiguously.
"""
from __future__ import annotations

import json
import logging
import os
from typing import Dict, List, Union

import pandas as pd

logger = logging.getLogger("novams.data_engine.loader")

SUPPORTED_EXTENSIONS = {".csv", ".xlsx", ".xls", ".json"}


class DataLoadError(ValueError):
    """Raised when a file can't be read into a DataFrame."""


class DataLoader:
    """
    Loads structured business files into independent, named pandas
    DataFrames. Call `.load(path)` per file (or `.load_many([...])`), then
    read back `.tables` — a dict of {table_name: DataFrame}.
    """

    def __init__(self) -> None:
        self.tables: Dict[str, pd.DataFrame] = {}

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #
    def load_many(self, paths: List[Union[str, os.PathLike]]) -> Dict[str, pd.DataFrame]:
        loaded: Dict[str, pd.DataFrame] = {}
        for path in paths:
            loaded.update(self.load(path))
        return loaded

    def load(self, path: Union[str, os.PathLike], base_name: str | None = None) -> Dict[str, pd.DataFrame]:
        """
        Load a single file. Returns only the table(s) newly added by this
        call (an Excel workbook with multiple sheets returns multiple
        tables). Also merges them into `self.tables`.
        """
        path = str(path)
        ext = os.path.splitext(path)[1].lower()
        if ext not in SUPPORTED_EXTENSIONS:
            raise DataLoadError(
                f"Unsupported file type '{ext}'. Supported: {sorted(SUPPORTED_EXTENSIONS)}"
            )
        name = base_name or os.path.splitext(os.path.basename(path))[0]
        newly_loaded: Dict[str, pd.DataFrame] = {}

        try:
            if ext == ".csv":
                df = pd.read_csv(path)
                newly_loaded[self._unique_name(name)] = df

            elif ext in (".xlsx", ".xls"):
                sheets = pd.read_excel(path, sheet_name=None, engine="openpyxl" if ext == ".xlsx" else None)
                if len(sheets) == 1:
                    only_df = next(iter(sheets.values()))
                    newly_loaded[self._unique_name(name)] = only_df
                else:
                    for sheet_name, sheet_df in sheets.items():
                        table_name = self._unique_name(f"{name}_{self._slugify(sheet_name)}")
                        newly_loaded[table_name] = sheet_df

            elif ext == ".json":
                with open(path, "r", encoding="utf-8") as fh:
                    raw = json.load(fh)
                df = pd.json_normalize(raw) if isinstance(raw, (list, dict)) else pd.DataFrame(raw)
                newly_loaded[self._unique_name(name)] = df

        except Exception as exc:  # pragma: no cover - defensive
            logger.exception("Failed to load %s", path)
            raise DataLoadError(f"Could not read '{path}': {exc}") from exc

        for table_name, df in newly_loaded.items():
            # Preserve original data: store a defensive copy so later
            # mutation elsewhere in the pipeline never touches the source.
            self.tables[table_name] = df.copy()
            logger.info("Loaded table '%s' with shape %s", table_name, df.shape)

        return newly_loaded

    def get(self, table_name: str) -> pd.DataFrame:
        if table_name not in self.tables:
            raise KeyError(f"No table named '{table_name}'. Available: {list(self.tables.keys())}")
        return self.tables[table_name]

    def list_tables(self) -> List[str]:
        return list(self.tables.keys())

    # ------------------------------------------------------------------ #
    # Internal helpers
    # ------------------------------------------------------------------ #
    def _unique_name(self, candidate: str) -> str:
        candidate = self._slugify(candidate) or "table"
        if candidate not in self.tables:
            return candidate
        i = 2
        while f"{candidate}_{i}" in self.tables:
            i += 1
        return f"{candidate}_{i}"

    @staticmethod
    def _slugify(text: str) -> str:
        text = str(text).strip().lower()
        return "".join(c if (c.isalnum() or c == "_") else "_" for c in text).strip("_")
