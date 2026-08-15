"""
data_engine.engine
──────────────────────
The DataEngine class orchestrates the full pipeline:

    Profile -> Schema -> Validate -> Clean -> Transform -> Quality -> Trust

for one or more named DataFrames, and returns ONE structured dict that the
Streamlit frontend (and, later, an LLM) can consume — without ever handing
raw rows to an AI model. This is the module streamlit_app.py imports as:

    from data_engine.engine import DataEngine
    engine = DataEngine()
    output = engine.run(dataframes={"active_dataset": df})
"""

import pandas as pd

from .profiler import DataProfiler
from .schema import SchemaDetector
from .validator import Validator
from .cleaner import Cleaner
from .transformer import Transformer
from .quality import QualityAnalyzer
from .domain import DomainDetector
from .relationships import RelationshipDiscoverer
from .semantic_mapper import SemanticMapper
from .capabilities import CapabilityEngine


class DataEngine:
    def __init__(self):
        self.profiler = DataProfiler()
        self.schema = SchemaDetector()
        self.validator = Validator()
        self.cleaner = Cleaner()
        self.transformer = Transformer()
        self.quality = QualityAnalyzer()
        self.domain_detector = DomainDetector()
        self.relationship_discoverer = RelationshipDiscoverer()
        self.semantic_mapper = SemanticMapper()
        self.capability_engine = CapabilityEngine()

    def run(self, dataframes: dict) -> dict:
        """dataframes: {table_name: pd.DataFrame, ...} — usually just
        {"active_dataset": df} for NovaMS's single-table Streamlit use case,
        but the engine supports multiple named tables for future connectors."""
        if not dataframes:
            raise ValueError("DataEngine.run() requires at least one named DataFrame.")

        quality_by_table, metrics_by_table = {}, {}
        roles_by_table, cleaning_log_by_table = {}, {}
        semantic_mappings_by_table, capabilities_by_table = {}, {}
        total_rows = 0
        domain_votes = []

        for name, raw_df in dataframes.items():
            if not isinstance(raw_df, pd.DataFrame):
                continue

            profile = self.profiler.profile(raw_df)
            roles = self.schema.detect(raw_df, profile)
            issues = self.validator.validate(raw_df, roles)
            cleaned_df, log = self.cleaner.clean(raw_df, roles)
            q = self.quality.score(profile, issues)
            metrics = self.transformer.compute_metrics(cleaned_df, roles)
            domain, confidence = self.domain_detector.detect(raw_df)
            semantic_mappings = self.semantic_mapper.map(raw_df, profile["date_columns"])
            capabilities = self.capability_engine.evaluate(semantic_mappings)

            roles_by_table[name] = roles
            quality_by_table[name] = q
            metrics_by_table[name] = metrics
            cleaning_log_by_table[name] = log
            semantic_mappings_by_table[name] = semantic_mappings
            capabilities_by_table[name] = capabilities
            total_rows += profile["rows"]
            domain_votes.append((domain, confidence))

        relationships = self.relationship_discoverer.discover(dataframes, roles_by_table)

        best_domain, best_confidence = (
            max(domain_votes, key=lambda x: x[1]) if domain_votes else ("general_business", 0.0)
        )

        primary_table = next(iter(dataframes.keys()))
        primary_metrics = metrics_by_table.get(primary_table, {})
        overall_score = round(
            sum(q["score"] for q in quality_by_table.values()) / max(1, len(quality_by_table))
        )

        return dict(
            rows=total_rows,
            tables=list(dataframes.keys()),
            domain=best_domain,
            domain_confidence=best_confidence,
            data_quality_score=overall_score,
            metrics=primary_metrics,
            metrics_by_table=metrics_by_table,
            quality=quality_by_table,
            roles=roles_by_table,
            relationships=relationships,
            cleaning_log=cleaning_log_by_table,
            semantic_mappings=semantic_mappings_by_table,
            capabilities=capabilities_by_table.get(primary_table, {}),
            capabilities_by_table=capabilities_by_table,
            dashboard_recommendations=self._recommend_sections(
                best_domain, roles_by_table.get(primary_table, {})
            ),
            ready_for_analysis=overall_score >= 50,
        )

    def _recommend_sections(self, domain: str, roles: dict) -> dict:
        sections = ["Executive Overview", "Data Explorer"]
        if any(r == "Measure" for r in roles.values()):
            sections.append("Sales Analytics")
        col_names_low = " ".join(roles.keys()).lower()
        if any(k in col_names_low for k in ["delivery", "distance"]):
            sections.append("Delivery Analytics")
        if any(k in col_names_low for k in ["stock", "inventory"]):
            sections.append("Inventory Intelligence")
        sections.append("Finance")
        return dict(recommended_sections=sections)
