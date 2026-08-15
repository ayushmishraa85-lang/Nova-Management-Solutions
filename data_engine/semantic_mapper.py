"""
data_engine.semantic_mapper
────────────────────────────
Maps arbitrary column names onto a small set of canonical business concepts
(revenue, cost, profit, quantity, price, discount, salary, customer_id,
product_id, order_id, date, category, region, ...) using name similarity +
dtype agreement — NOT a hardcoded list of exact column names. Every mapping
carries a confidence score and a plain-language reason, so a low-confidence
guess can be surfaced as ambiguous instead of silently trusted.

The original column names are never modified — this only produces a
parallel list of {original_name, semantic_name, confidence, reason}.
"""

import difflib

import pandas as pd

_CONCEPT_SYNONYMS = {
    "revenue": ["revenue", "sales", "sales amount", "net sales", "total sales", "gmv", "turnover", "amount"],
    "cost": ["cost", "cogs", "expense", "expenditure"],
    "profit": ["profit", "net income", "margin amount"],
    "quantity": ["quantity", "qty", "units", "units sold", "orders", "order count"],
    "price": ["price", "mrp", "unit price", "selling price", "list price"],
    "discount": ["discount", "discount pct", "discount amount", "markdown"],
    "salary": ["salary", "compensation", "pay", "wage", "ctc"],
    "customer_id": ["customer id", "cust id", "client id", "buyer id"],
    "product_id": ["product id", "item id", "sku", "product code"],
    "order_id": ["order id", "transaction id", "invoice id"],
    "employee_id": ["employee id", "emp id", "staff id"],
    "date": ["date", "order date", "transaction date", "timestamp", "created at"],
    "category": ["category", "product category", "segment", "item type"],
    "region": ["region", "state", "country", "territory"],
    "city": ["city", "location", "store city", "outlet"],
    "channel": ["channel", "sales channel", "platform"],
    "department": ["department", "team", "division"],
}

_CONCEPT_DTYPE = {
    "revenue": "numeric", "cost": "numeric", "profit": "numeric", "quantity": "numeric",
    "price": "numeric", "discount": "numeric", "salary": "numeric",
    "customer_id": "identifier", "product_id": "identifier", "order_id": "identifier", "employee_id": "identifier",
    "date": "date", "category": "text", "region": "text", "city": "text",
    "channel": "text", "department": "text",
}

_MIN_CONFIDENCE = 0.35
_AMBIGUOUS_BELOW = 0.60


class SemanticMapper:
    def map(self, df: pd.DataFrame, date_columns: list) -> list:
        mappings = []
        for col in df.columns:
            best_concept, best_score, best_reason = None, 0.0, ""
            norm_col = self._normalize(col)

            for concept, synonyms in _CONCEPT_SYNONYMS.items():
                norm_synonyms = [self._normalize(s) for s in synonyms]
                if norm_col in norm_synonyms:
                    name_score = 1.0
                elif any(ns in norm_col or norm_col in ns for ns in norm_synonyms):
                    name_score = 0.85
                else:
                    name_score = max(difflib.SequenceMatcher(None, norm_col, ns).ratio() for ns in norm_synonyms)

                dtype_ok = self._dtype_matches(df[col], concept, col in date_columns)
                if not dtype_ok:
                    name_score *= 0.4  # heavy penalty, not a hard veto — the name is still informative

                if name_score > best_score:
                    best_concept, best_score = concept, name_score
                    best_reason = self._explain(name_score, dtype_ok)

            if best_concept and best_score >= _MIN_CONFIDENCE:
                mappings.append(dict(
                    original_name=col,
                    semantic_name=best_concept,
                    confidence=round(best_score, 2),
                    reason=best_reason,
                    ambiguous=best_score < _AMBIGUOUS_BELOW,
                ))
        return mappings

    def _normalize(self, s: str) -> str:
        return "".join(ch for ch in str(s).lower().strip() if ch.isalnum() or ch == " ").strip()

    def _dtype_matches(self, s: pd.Series, concept: str, is_date_col: bool) -> bool:
        expected = _CONCEPT_DTYPE.get(concept, "any")
        if expected == "numeric":
            return bool(pd.api.types.is_numeric_dtype(s))
        if expected == "date":
            return bool(is_date_col or pd.api.types.is_datetime64_any_dtype(s))
        if expected == "text":
            return not pd.api.types.is_numeric_dtype(s)
        if expected == "identifier":
            return not is_date_col and not pd.api.types.is_datetime64_any_dtype(s)
        return True

    def _explain(self, score: float, dtype_ok: bool) -> str:
        if score >= 0.85 and dtype_ok:
            return "strong name match with matching data type"
        if score >= _AMBIGUOUS_BELOW:
            return "partial name match" + ("" if dtype_ok else " but data type mismatch — treat with caution")
        return "weak/ambiguous name match — verify before relying on this"
