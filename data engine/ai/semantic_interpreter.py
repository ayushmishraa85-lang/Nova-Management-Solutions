"""
ai/semantic_interpreter.py
LLM/Claude Integration — Part 13 of the NovaMS Data Engine spec.

This module is the ONLY place that talks to Claude. It never receives the
raw DataFrame — only the compact context built by `build_llm_context()`
below (domain, table count, key metrics, top anomaly, etc). If no API key
is configured, `interpret()` degrades gracefully to a rule-based summary
so the rest of NovaMS keeps working with zero external calls.
"""
from __future__ import annotations

import json
import os
from typing import Any, Dict, Optional

import requests

_CLAUDE_API_URL = "https://api.anthropic.com/v1/messages"
_CLAUDE_MODEL = "claude-sonnet-5"
_ANTHROPIC_VERSION = "2023-06-01"


def build_llm_context(engine_output: Dict[str, Any], max_metrics: int = 8) -> Dict[str, Any]:
    """
    Compresses a full DataEngine output into the small context Claude is
    allowed to see (Part 13/14 — never raw rows, never every table).
    """
    metrics = engine_output.get("metrics", {})
    trimmed_metrics = {k: v["value"] for k, v in list(metrics.items())[:max_metrics]}
    top_anomaly = engine_output.get("anomalies", [{}])[0] if engine_output.get("anomalies") else None

    return dict(
        domain=engine_output.get("domain"),
        domain_confidence=engine_output.get("domain_confidence"),
        tables=engine_output.get("tables"),
        rows=engine_output.get("rows"),
        data_quality_score=engine_output.get("data_quality_score"),
        metrics=trimmed_metrics,
        dimensions=engine_output.get("dimensions", [])[:10],
        top_anomaly=top_anomaly,
        recommended_dashboard_sections=engine_output.get("dashboard_recommendations", {}).get("recommended_sections"),
    )


def _rule_based_summary(context: Dict[str, Any]) -> str:
    """Zero-dependency fallback used whenever no API key is available."""
    lines = [
        f"Detected domain: {context.get('domain')} "
        f"(confidence {context.get('domain_confidence', 0):.0%}).",
        f"{context.get('tables')} table(s), {context.get('rows'):,} total rows, "
        f"data quality score {context.get('data_quality_score')}/100.",
    ]
    metrics = context.get("metrics") or {}
    if metrics:
        pretty = ", ".join(f"{k}={v:,.2f}" for k, v in metrics.items())
        lines.append(f"Key metrics: {pretty}.")
    if context.get("top_anomaly"):
        a = context["top_anomaly"]
        lines.append(f"Notable anomaly: {a.get('metric')} in {a.get('period')} "
                      f"({a.get('change_pct')}%, severity {a.get('severity')}).")
    return " ".join(lines)


def interpret(context: Dict[str, Any], question: Optional[str] = None,
              api_key: Optional[str] = None) -> str:
    """
    Interprets an already-built context (see build_llm_context). Falls back
    to a deterministic rule-based summary if no api_key is supplied or the
    request fails for any reason — this function must never raise up into
    the dashboard.
    """
    api_key = api_key or os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        return _rule_based_summary(context)

    system = (
        "You are a senior business analyst. You are given a compact JSON summary of a "
        "dataset (never the raw data). Explain what it means in plain business language, "
        "name likely causes, and suggest one or two concrete actions. Keep it to 4-6 sentences. "
        "Never invent numbers not present in the JSON."
    )
    user_content = f"Dataset summary:\n{json.dumps(context, default=str)}"
    if question:
        user_content += f"\n\nQuestion: {question}"

    try:
        resp = requests.post(
            _CLAUDE_API_URL,
            headers={
                "x-api-key": api_key.strip(),
                "anthropic-version": _ANTHROPIC_VERSION,
                "content-type": "application/json",
            },
            json=dict(
                model=_CLAUDE_MODEL, max_tokens=500, system=system,
                messages=[{"role": "user", "content": user_content}],
            ),
            timeout=30,
        )
        resp.raise_for_status()
        blocks = resp.json().get("content", [])
        text = "".join(b.get("text", "") for b in blocks if b.get("type") == "text")
        return text.strip() or _rule_based_summary(context)
    except Exception:
        return _rule_based_summary(context)
