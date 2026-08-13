"""
data_engine/domain_detector.py
Business Domain Detection — Part 6 of the NovaMS Data Engine spec.

Scores each candidate domain by how many of its keyword hints appear
across all table/column names, then returns the best match with a
confidence score. Never forces a classification — low-confidence results
fall back to "unknown/general_business".
"""
from __future__ import annotations

import re
from typing import Any, Dict, List

_DOMAIN_KEYWORDS: Dict[str, List[str]] = {
    "ecommerce": ["order", "product", "sku", "cart", "checkout", "revenue", "discount",
                  "customer", "shipping", "refund", "session", "conversion"],
    "retail": ["store", "pos", "inventory", "sku", "footfall", "till", "outlet"],
    "finance": ["invoice", "ledger", "expense", "revenue", "cash_flow", "balance", "account",
                "transaction", "budget", "cost"],
    "sales": ["deal", "pipeline", "lead", "quota", "opportunity", "won", "lost", "sales_rep"],
    "marketing": ["campaign", "impression", "click", "ctr", "cpc", "cpm", "utm", "channel", "ad_spend"],
    "hr": ["employee", "hire", "attrition", "salary", "department", "manager", "payroll", "headcount"],
    "education": ["student", "course", "grade", "enrollment", "teacher", "class", "score", "exam"],
    "healthcare": ["patient", "diagnosis", "treatment", "doctor", "hospital", "prescription", "appointment"],
    "operations": ["shift", "process_time", "warehouse", "workflow", "bottleneck", "throughput"],
    "inventory": ["stock", "reorder", "warehouse", "sku", "quantity_on_hand", "supplier"],
    "logistics": ["shipment", "delivery", "carrier", "route", "distance", "rider", "tracking"],
    "customer_support": ["ticket", "resolution", "sla", "agent", "csat", "escalation"],
}

_CONFIDENCE_FLOOR = 0.30


def _normalize(text: str) -> str:
    return re.sub(r"[^a-z0-9 _]", " ", str(text).lower())


def detect_domain(profiles: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    """
    profiles: {table_name: table_profile_dict} — uses table names and every
    column name across all tables as the text corpus to score against.
    """
    corpus_tokens: List[str] = []
    for table_name, profile in profiles.items():
        corpus_tokens.append(_normalize(table_name))
        corpus_tokens.extend(_normalize(c) for c in profile["columns"].keys())
    corpus = " ".join(corpus_tokens)

    scores: Dict[str, float] = {}
    for domain, keywords in _DOMAIN_KEYWORDS.items():
        hits = sum(1 for kw in keywords if kw in corpus)
        scores[domain] = round(hits / len(keywords), 4)

    if not scores or max(scores.values()) == 0:
        return dict(domain="unknown/general_business", confidence=0.0, scores=scores)

    best_domain = max(scores, key=scores.get)
    best_score = scores[best_domain]

    if best_score < _CONFIDENCE_FLOOR:
        return dict(domain="unknown/general_business", confidence=best_score, scores=scores)

    return dict(domain=best_domain, confidence=best_score, scores=scores)
