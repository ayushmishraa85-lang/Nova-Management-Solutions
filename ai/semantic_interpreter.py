"""
ai.semantic_interpreter
───────────────────────────
Bridges the deterministic Data Engine output to an optional natural-language
interpretation. Per the spec's token-optimization requirement, the LLM only
ever sees compact metadata (schema, scores, pre-computed metric VALUES) —
never raw rows. If no API key is configured, a deterministic template-based
summary is returned instead, so this page never hard-fails.
"""

import json


def build_llm_context(engine_output: dict) -> dict:
    """The exact, privacy-safe payload sent to Claude — metadata and
    pre-computed numbers only."""
    return dict(
        domain=engine_output.get("domain"),
        domain_confidence=engine_output.get("domain_confidence"),
        data_quality_score=engine_output.get("data_quality_score"),
        rows=engine_output.get("rows"),
        tables=engine_output.get("tables"),
        metrics={k: v["value"] for k, v in engine_output.get("metrics", {}).items()},
        quality_summary={
            table: dict(score=q["score"], status=q["status"], issue_count=len(q["issues"]))
            for table, q in engine_output.get("quality", {}).items()
        },
        relationships=engine_output.get("relationships", []),
        recommended_sections=engine_output.get("dashboard_recommendations", {}).get("recommended_sections", []),
    )


def interpret(context: dict, api_key: str | None = None) -> str:
    """Returns a short natural-language interpretation of the context.
    Falls back to a deterministic summary when no API key is available."""
    if not api_key:
        return _fallback_interpretation(context)

    import requests

    prompt = (
        "You are a data engineer summarizing a dataset profiling report for a "
        "business user. Be concise (4-6 sentences), plain language, no jargon. "
        f"Report:\n{json.dumps(context, indent=2, default=str)}"
    )
    try:
        resp = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": api_key.strip(),
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json=dict(
                model="claude-sonnet-5",
                max_tokens=400,
                messages=[{"role": "user", "content": prompt}],
            ),
            timeout=30,
        )
        if not resp.ok:
            return _fallback_interpretation(context) + f"\n\n_(LLM call failed: HTTP {resp.status_code})_"
        data = resp.json()
        texts = [b["text"] for b in data.get("content", []) if b.get("type") == "text"]
        return "\n".join(texts) if texts else _fallback_interpretation(context)
    except Exception as exc:
        return _fallback_interpretation(context) + f"\n\n_(LLM call failed: {exc})_"


def _fallback_interpretation(context: dict) -> str:
    domain = str(context.get("domain", "general_business")).replace("_", " ").title()
    score = context.get("data_quality_score", 0)
    rows = context.get("rows", 0)
    issues = sum(v.get("issue_count", 0) for v in context.get("quality_summary", {}).values())
    verdict = (
        "The data looks solid enough to analyze as-is."
        if score >= 75 else
        "Consider reviewing the flagged issues before drawing firm conclusions."
    )
    return (
        f"This looks like a **{domain}** dataset with **{rows:,} rows**. "
        f"Overall data quality scores **{score}/100**, with **{issues}** flagged issue(s) "
        f"across the profiled table(s). {verdict}"
    )
