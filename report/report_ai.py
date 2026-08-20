"""
report_ai.py — Optional AI Narrative Layer (Nova Analyst / Decision Brief)
=============================================================================
Claude is ONLY allowed to explain numbers that report_metrics.py already
calculated — never to compute KPIs, invent forecasts, or replace the Python
analytics. If the API is unavailable, unset, or errors out, the report still
generates in full; this module's failure mode is always "return None", never
an exception.
"""

from __future__ import annotations
import json
import requests

_CLAUDE_API_URL = "https://api.anthropic.com/v1/messages"
_MODEL = "claude-sonnet-5"
_ANTHROPIC_VERSION = "2023-06-01"

_SYSTEM_PROMPT = """You are the Nova Analyst, writing the "Decision Brief" page of a formal \
business intelligence PDF report. You will be given a JSON object of ALREADY-CALCULATED, \
validated metrics. You must:

1. Only reference numbers present in the JSON — never invent, estimate, or recompute any value.
2. Write in a confident, senior-analyst register: plain, factual sentences, no filler like \
   "Great news!" and no exclamation marks.
3. Produce exactly four sections in this order: KEY FINDINGS, BUSINESS RISKS, OPPORTUNITIES, \
   RECOMMENDED ACTIONS. Each section is 2-4 short bullet points.
4. Every bullet must cite at least one concrete figure from the JSON (with its currency/percent \
   formatting preserved as given).
5. Output plain text only, using this exact structure with these exact headers, nothing else:

KEY FINDINGS
- ...

BUSINESS RISKS
- ...

OPPORTUNITIES
- ...

RECOMMENDED ACTIONS
- ...
"""


def build_ai_context(metrics_summary: dict) -> str:
    """Serializes only the aggregated/validated numbers — never raw rows —
    into compact JSON for the LLM prompt."""
    return json.dumps(metrics_summary, indent=2, default=str)


def generate_decision_brief(metrics_summary: dict, api_key: str | None) -> tuple[str | None, str | None]:
    """Returns (brief_text, error_reason). brief_text is None if AI insights
    aren't available for any reason — the caller must show the report's
    honest fallback message and continue generating the PDF regardless."""
    if not api_key or not api_key.strip():
        return None, "No API key configured."
    try:
        context_json = build_ai_context(metrics_summary)
        payload = {
            "model": _MODEL,
            "max_tokens": 700,
            "system": _SYSTEM_PROMPT,
            "messages": [{"role": "user", "content": f"Validated metrics JSON:\n{context_json}"}],
        }
        headers = {
            "x-api-key": api_key.strip(),
            "anthropic-version": _ANTHROPIC_VERSION,
            "content-type": "application/json",
        }
        resp = requests.post(_CLAUDE_API_URL, headers=headers, json=payload, timeout=30)
        if not resp.ok:
            return None, f"API error {resp.status_code}"
        data = resp.json()
        text_parts = [b.get("text", "") for b in data.get("content", []) if b.get("type") == "text"]
        text = "\n".join(text_parts).strip()
        if not text:
            return None, "Empty response from model."
        return text, None
    except requests.exceptions.Timeout:
        return None, "Request timed out."
    except Exception as e:
        return None, str(e)


def parse_decision_brief(text: str) -> dict:
    """Splits the fixed-format brief into {section_name: [bullets]}."""
    sections = {"KEY FINDINGS": [], "BUSINESS RISKS": [], "OPPORTUNITIES": [], "RECOMMENDED ACTIONS": []}
    current = None
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        upper = line.upper().rstrip(":")
        if upper in sections:
            current = upper
            continue
        if current and line.startswith("-"):
            sections[current].append(line.lstrip("- ").strip())
    return sections
