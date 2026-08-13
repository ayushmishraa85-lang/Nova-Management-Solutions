"""
schemas/data_models.py
Pydantic models used across the Data Engine so every module hands back a
typed, JSON-serializable structure instead of an ad-hoc dict. Kept
intentionally permissive (Optional / default-heavy) because different
datasets will populate different subsets of these fields.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ColumnProfile(BaseModel):
    name: str
    dtype: str
    role_hint: str = "unknown"
    missing_count: int = 0
    missing_pct: float = 0.0
    unique_count: int = 0
    cardinality_ratio: float = 0.0
    is_constant: bool = False
    example_values: List[Any] = Field(default_factory=list)
    min_value: Optional[Any] = None
    max_value: Optional[Any] = None
    mean_value: Optional[float] = None
    median_value: Optional[float] = None


class TableProfile(BaseModel):
    table: str
    rows: int
    n_columns: int
    duplicate_rows: int = 0
    columns: Dict[str, ColumnProfile] = Field(default_factory=dict)


class QualityIssue(BaseModel):
    severity: str
    column: Optional[str] = None
    issue: str


class QualityReport(BaseModel):
    table: str
    score: int
    status: str
    issues: List[QualityIssue] = Field(default_factory=list)


class Relationship(BaseModel):
    relationship: str
    left_table: str
    left_column: str
    right_table: str
    right_column: str
    type: str
    confidence: float


class DomainDetection(BaseModel):
    domain: str
    confidence: float
    scores: Dict[str, float] = Field(default_factory=dict)


class MetricValue(BaseModel):
    value: float
    formula: str
    inputs: List[str] = Field(default_factory=list)


class TrendPoint(BaseModel):
    period: str
    value: float


class AnomalyRecord(BaseModel):
    metric: str
    period: str
    change_pct: float
    severity: str
    reason: str


class EngineOutput(BaseModel):
    generated_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    domain: str = "unknown/general_business"
    domain_confidence: float = 0.0
    data_quality_score: int = 0
    tables: int = 0
    rows: int = 0
    entities: List[str] = Field(default_factory=list)
    metrics: Dict[str, MetricValue] = Field(default_factory=dict)
    dimensions: List[str] = Field(default_factory=list)
    profiles: Dict[str, TableProfile] = Field(default_factory=dict)
    quality: Dict[str, QualityReport] = Field(default_factory=dict)
    relationships: List[Relationship] = Field(default_factory=list)
    semantic_roles: Dict[str, Dict[str, str]] = Field(default_factory=dict)
    trends: Dict[str, Any] = Field(default_factory=dict)
    anomalies: List[AnomalyRecord] = Field(default_factory=list)
    dashboard_recommendations: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        arbitrary_types_allowed = True
