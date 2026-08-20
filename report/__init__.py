"""
NovaMS Report Engine
=====================
Modular, additive Business Intelligence report generator.

This package is intentionally self-contained: importing it must never raise,
even if a dependency (reportlab/matplotlib) is missing, so a failure here can
never break the rest of the NovaMS dashboard. Callers should always go
through `report_engine.ReportEngine` and check `.available` before use.
"""

try:
    from .report_engine import ReportEngine, REPORT_ENGINE_AVAILABLE, REPORT_ENGINE_IMPORT_ERROR
except Exception as _e:  # pragma: no cover - defensive
    ReportEngine = None
    REPORT_ENGINE_AVAILABLE = False
    REPORT_ENGINE_IMPORT_ERROR = str(_e)

__all__ = ["ReportEngine", "REPORT_ENGINE_AVAILABLE", "REPORT_ENGINE_IMPORT_ERROR"]
