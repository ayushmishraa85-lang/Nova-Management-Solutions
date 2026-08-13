# NovaMS Data Engine — Milestone 1

A schema-agnostic data intelligence engine: it accepts **any** structured
business file (CSV / XLSX / JSON — SQL later), and produces a compact
JSON profile without ever sending raw rows to an LLM.

```
ANY STRUCTURED DATA → UNDERSTAND → VALIDATE → CONNECT → CALCULATE → ANALYZE → RECOMMEND DASHBOARD
```

## Files added (all new — nothing in your existing app.py is touched)

```
novams/
├── data_engine/
│   ├── loader.py                 # Part 1 — universal CSV/XLSX/JSON loader
│   ├── profiler.py               # Part 2 — per-column structural profile
│   ├── quality.py                # Part 3 — issue flags + 0-100 trust score
│   ├── relationships.py          # Part 4 — PK/FK discovery, value-validated
│   ├── semantic.py               # Part 5 — IDENTIFIER/DATE/MEASURE/... roles
│   ├── domain_detector.py        # Part 6 — ecommerce/finance/hr/... + confidence
│   ├── metrics.py                # Part 8 — Revenue/AOV/Profit/Margin/... (only if columns exist)
│   ├── trends.py                 # Part 9 — daily/weekly/monthly + growth %
│   ├── anomalies.py              # Part 11 — z-score anomaly flags on trend data
│   ├── dashboard_recommender.py  # Part 16 — suggested dashboard sections per domain
│   └── engine.py                 # Orchestrator — DataEngine.run(...) -> one JSON dict
├── ai/
│   └── semantic_interpreter.py   # Part 13 — Claude layer, receives ONLY the compact JSON
├── schemas/
│   └── data_models.py            # Pydantic models for every structured output
└── tests/
    └── test_engine.py            # pytest — 10 tests, all passing
```

Sections **not** built in this milestone (per the spec's own "final
requirement" — add these only after Milestone 1 is solid):
Claude interpretation is wired but off-by-default, automatic dashboard
*rendering* (recommendation JSON is there, actual chart generation isn't),
and SQL database ingestion.

## Quick start

```bash
pip install -r requirements-data-engine.txt
pytest tests/ -q          # 10 passed
```

```python
from data_engine.engine import DataEngine

engine = DataEngine()
output = engine.run(files=["zepto_sales_dataset.csv"])
# or, from an in-memory DataFrame (e.g. Streamlit's file_uploader):
# output = engine.run(dataframes={"zepto_sales": df})

print(output["domain"], output["data_quality_score"])
print(output["metrics"])
```

`output` is a plain JSON-serializable dict shaped like the spec's Part 15
example: `domain`, `data_quality_score`, `tables`, `rows`, `entities`,
`metrics`, `dimensions`, `relationships`, `anomalies`,
`dashboard_recommendations`, plus the full per-table `profiles` and
`quality` reports.

## Adding this to your existing NovaMS app.py

Nothing here modifies your current file. To wire in a new **"Data
Engine"** page next to your existing 12 nav pages, add three small,
additive edits (exact snippets in `STREAMLIT_INTEGRATION.md`):

1. Copy the `data_engine/`, `ai/`, and `schemas/` folders into your repo
   root (next to `app.py`).
2. Paste the `render_data_engine()` function (provided) anywhere near your
   other `render_*` functions.
3. Add `"Data Engine"` to `NAV_PAGES` and `"Data Engine": render_data_engine`
   to `_PAGE_RENDERERS`.

That's it — every existing page, filter, and calculation is untouched.
