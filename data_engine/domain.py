"""
data_engine.domain
──────────────────────
Guesses the dataset's business domain from its column names. Covers many
kinds of commerce — not just quick-commerce — plus a few common non-commerce
domains, so a fashion retailer, an electronics marketplace, a subscription
business, or a B2B wholesaler each get identified as what they actually
are, instead of everything with "revenue"/"category"/"product" defaulting
to one narrow bucket.

Each domain has two keyword tiers:
  - "strong": fairly unique to that domain (weight 2)
  - "supporting": common across several commerce domains (weight 1)
A domain's score is its weighted keyword overlap; this naturally favors
whichever domain has more DISTINCTIVE (strong) matches, not just more
generic retail overlap. Below a low confidence floor, the result is
"general_business" rather than a forced guess — matches the "do not force
a domain if confidence is low" principle.
"""

_DOMAIN_SIGNATURES = {
    "quick_commerce": dict(
        strong=["dark store", "instant delivery", "10 minute", "rider", "eta", "delivery time"],
        supporting=["delivery", "orders", "discount", "city"],
    ),
    "grocery_fmcg_retail": dict(
        strong=["sku", "mrp", "fmcg", "grocery", "expiry", "batch"],
        supporting=["category", "product", "price", "quantity", "stock"],
    ),
    "fashion_apparel_retail": dict(
        strong=["size", "color", "apparel", "fashion", "collection", "season"],
        supporting=["category", "product", "brand", "price"],
    ),
    "electronics_retail": dict(
        strong=["warranty", "model number", "specification", "electronics", "serial"],
        supporting=["category", "product", "brand", "price"],
    ),
    "marketplace_ecommerce": dict(
        strong=["seller", "vendor", "marketplace", "commission", "listing"],
        supporting=["order_id", "customer_id", "product", "price", "quantity"],
    ),
    "general_ecommerce": dict(
        strong=["cart", "checkout", "shipping", "order_id", "sku"],
        supporting=["customer_id", "product", "price", "quantity", "revenue"],
    ),
    "subscription_commerce": dict(
        strong=["subscription", "renewal", "churn", "mrr", "plan"],
        supporting=["customer_id", "revenue", "billing"],
    ),
    "b2b_wholesale": dict(
        strong=["wholesale", "bulk", "purchase order", "vendor", "distributor"],
        supporting=["quantity", "price", "order_id"],
    ),
    "finance": dict(
        strong=["transaction", "account", "balance", "debit", "credit", "ledger"],
        supporting=["amount", "date"],
    ),
    "hr": dict(
        strong=["employee", "salary", "department", "hire date", "attrition"],
        supporting=["id", "date"],
    ),
    "logistics": dict(
        strong=["shipment", "tracking", "warehouse", "route", "freight"],
        supporting=["delivery", "date"],
    ),
    "healthcare": dict(
        strong=["patient", "diagnosis", "treatment", "physician", "prescription"],
        supporting=["date", "id"],
    ),
    "education": dict(
        strong=["student", "grade", "course", "enrollment", "gpa"],
        supporting=["date", "id"],
    ),
}

_MIN_CONFIDENCE = 0.15


class DomainDetector:
    def detect(self, df) -> tuple:
        cols_low = " ".join(str(c).lower() for c in df.columns)
        best_domain, best_score = "general_business", 0.0

        for domain, sig in _DOMAIN_SIGNATURES.items():
            strong_hits = sum(1 for k in sig["strong"] if k in cols_low)
            supporting_hits = sum(1 for k in sig["supporting"] if k in cols_low)
            total_weight = len(sig["strong"]) * 2 + len(sig["supporting"])
            score = (strong_hits * 2 + supporting_hits) / total_weight if total_weight else 0.0
            if score > best_score:
                best_domain, best_score = domain, score

        if best_score < _MIN_CONFIDENCE:
            return "general_business", round(best_score, 2)
        return best_domain, round(min(best_score, 1.0), 2)
