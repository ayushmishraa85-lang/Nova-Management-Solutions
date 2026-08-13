"""
data_engine.domain
──────────────────────
Cheap keyword-overlap guess at the dataset's business domain (retail,
e-commerce, finance, HR, logistics, ...). Deterministic and free — an LLM
call is never needed just to guess what kind of data this is.
"""

_DOMAIN_SIGNATURES = {
    "quick_commerce_retail": ["revenue", "orders", "discount", "category", "city", "product"],
    "e_commerce": ["order_id", "customer_id", "product", "price", "quantity"],
    "finance": ["transaction", "account", "balance", "debit", "credit"],
    "hr": ["employee", "salary", "department", "hire_date"],
    "logistics": ["delivery", "shipment", "tracking", "warehouse", "route"],
}


class DomainDetector:
    def detect(self, df) -> tuple:
        cols_low = " ".join(str(c).lower() for c in df.columns)
        best_domain, best_score = "general_business", 0.0
        for domain, keywords in _DOMAIN_SIGNATURES.items():
            hits = sum(1 for k in keywords if k in cols_low)
            score = hits / len(keywords)
            if score > best_score:
                best_domain, best_score = domain, score
        return best_domain, round(best_score, 2)
