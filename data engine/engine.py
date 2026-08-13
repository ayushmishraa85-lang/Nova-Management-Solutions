"""
data_engine/engine.py
DataEngine — orchestrates loader -> profiler -> quality -> relationships ->
semantic -> domain_detector -> metrics -> trends -> anomalies ->
dashboard_recommender, and assembles the final structured JSON profile
described in Part 15 of the spec.

Works entirely offline (no LLM/API key required). Claude/LLM involvement,
if any, happens *after* this engine runs, via ai/semantic_interpreter.py,
and only ever receives the compact output below — never raw rows.
"""
from __future__ import annotations

import hashlib
import logging
from typing import Any, Dict, List, Union

import pandas as pd

from .loader import DataLoader
from .profiler import profile_table
from .quality import check_table_quality, score_table_quality
from .relationships import discover_relationships
from .semantic import classify_table
from .domain_detector import detect_domain
from .metrics import compute_metrics
from .trends import compute_time_analysis
from .anomalies import detect_anomalies
from .dashboard_recommender import recommend_dashboard

logger = logging.getLogger("novams.data_engine.engine")


def _table_hash(df: pd.DataFrame) -> str:
    """Cheap fingerprint used to cache repeated profile/metric computations
    (Part 14: cache dataset profiles, cache calculated metrics)."""
    try:
        return hashlib.md5(pd.util.hash_pandas_object(df, index=True).values.tobytes()).hexdigest()
    except Exception:  # pragma: no cover - fallback for exotic dtypes
        return hashlib.md5(str(df.shape).encode() + str(list(df.columns)).encode()).hexdigest()


class DataEngine:
    """
    Usage:
        engine = DataEngine()
        output = engine.run(["orders.csv", "customers.xlsx"])
        # output is a plain JSON-serializable dict (see EngineOutput schema)
    """

    def __init__(self) -> None:
        self.loader = DataLoader()
        self._profile_cache: Dict[str, Dict[str, Any]] = {}
        self._quality_cache: Dict[str, Dict[str, Any]] = {}
        self._metrics_cache: Dict[str, Dict[str, Any]] = {}

    # ------------------------------------------------------------------ #
    def run(self, files: List[Union[str, Any]] | None = None,
            dataframes: Dict[str, pd.DataFrame] | None = None) -> Dict[str, Any]:
        """
        `files`: paths to load via DataLoader (CSV/XLSX/JSON).
        `dataframes`: pre-loaded {table_name: DataFrame} to merge in as-is
                      (useful when the caller — e.g. Streamlit's uploader —
                      already has a DataFrame in memory).
        """
        if files:
            self.loader.load_many(files)
        if dataframes:
            for name, df in dataframes.items():
                self.loader.tables[name] = df.copy()

        tables = self.loader.tables
        if not tables:
            raise ValueError("No tables loaded — pass `files` and/or `dataframes`.")

        # 1) Profile every table (cached by content hash)
        profiles: Dict[str, Dict[str, Any]] = {}
        for name, df in tables.items():
            h = _table_hash(df)
            if h not in self._profile_cache:
                self._profile_cache[h] = profile_table(df, name)
            profiles[name] = self._profile_cache[h]

        # 2) Data quality per table
        quality: Dict[str, Dict[str, Any]] = {}
        for name, df in tables.items():
            issues = check_table_quality(df, name, profiles[name])
            quality[name] = score_table_quality(profiles[name], issues)

        # 3) Relationship discovery across tables (validated, not just name match)
        relationships = discover_relationships(tables, profiles) if len(tables) > 1 else []

        # 4) Semantic column classification per table
        semantic_roles = {name: classify_table(profiles[name]) for name in tables}

        # 5) Business domain detection (uses table + column names across everything loaded)
        domain_result = detect_domain(profiles)

        # 6) Pick the "primary" fact table for metrics/trends — the one with
        #    the most rows is a reasonable, simple heuristic.
        primary_table_name = max(tables, key=lambda n: len(tables[n]))
        primary_df = tables[primary_table_name]

        # 7) Metrics (cached by content hash) — only computed for what the data supports
        h = _table_hash(primary_df)
        if h not in self._metrics_cache:
            self._metrics_cache[h] = compute_metrics(primary_df)
        metrics = self._metrics_cache[h]

        # 8) Trends + anomalies — only if a date column and a measure column exist
        trends: Dict[str, Any] = {}
        anomalies: List[Dict[str, Any]] = []
        date_col = next((c for c, role in semantic_roles[primary_table_name].items() if role == "DATE"), None)
        measure_col = next((c for c, role in semantic_roles[primary_table_name].items() if role == "MEASURE"), None)
        if date_col and measure_col:
            trends = compute_time_analysis(primary_df, date_col, measure_col)
            if trends.get("monthly"):
                anomalies = detect_anomalies(trends["monthly"], metric_name=measure_col)
            elif trends.get("weekly"):
                anomalies = detect_anomalies(trends["weekly"], metric_name=measure_col)

        # 9) Business entity model — every table is an entity; dimensions are
        #    every column classified as DIMENSION anywhere.
        entities = list(tables.keys())
        dimensions = sorted({
            col for roles in semantic_roles.values()
            for col, role in roles.items() if role == "DIMENSION"
        })

        # 10) Dashboard recommendation
        dashboard_recs = recommend_dashboard(domain_result["domain"], list(metrics.keys()))

        overall_quality_score = int(round(
            sum(q["score"] for q in quality.values()) / len(quality)
        )) if quality else 0

        output = dict(
            domain=domain_result["domain"],
            domain_confidence=domain_result["confidence"],
            data_quality_score=overall_quality_score,
            tables=len(tables),
            rows=sum(len(df) for df in tables.values()),
            primary_table=primary_table_name,
            entities=entities,
            metrics=metrics,
            dimensions=dimensions,
            profiles=profiles,
            quality=quality,
            relationships=relationships,
            semantic_roles=semantic_roles,
            trends=trends,
            anomalies=anomalies,
            dashboard_recommendations=dashboard_recs,
        )
        logger.info("DataEngine.run complete: %s tables, domain=%s (%.2f confidence)",
                    len(tables), domain_result["domain"], domain_result["confidence"])
        return output
