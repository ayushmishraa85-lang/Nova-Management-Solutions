"""
data_engine.quality
───────────────────────
Produces a 0-100 Data Quality Score. This is explicitly a QUALITY score
(completeness / validity / consistency / uniqueness), not an ACCURACY claim —
the engine has no external source of truth to verify facts against.
"""


class QualityAnalyzer:
    def score(self, profile: dict, issues: list) -> dict:
        n_cells = max(1, profile["rows"] * profile["columns"])
        completeness = 1 - (profile["missing_total"] / n_cells)
        uniqueness = 1 - (profile["duplicate_rows"] / max(1, profile["rows"]))

        high = sum(1 for i in issues if i["severity"] == "High")
        med = sum(1 for i in issues if i["severity"] == "Medium")
        low = sum(1 for i in issues if i["severity"] == "Low")
        penalty = min(1.0, high * 0.15 + med * 0.07 + low * 0.02)
        validity_consistency = 1 - penalty

        raw = completeness * 0.35 + uniqueness * 0.25 + validity_consistency * 0.40
        score = max(0, min(100, round(raw * 100)))
        status = (
            "Excellent" if score >= 90 else
            "Good" if score >= 75 else
            "Needs Review" if score >= 50 else
            "Poor Quality"
        )
        return dict(
            score=score,
            status=status,
            issues=issues,
            sub_scores=dict(
                completeness=round(completeness * 100, 1),
                uniqueness=round(uniqueness * 100, 1),
                validity=round(validity_consistency * 100, 1),
            ),
            accuracy_note="Not verified — no external source of truth was provided to check facts against.",
        )
