"""
reports_ui.py — "Reports" page for NovaMS
=============================================
Additive, self-contained Streamlit page. Wraps the standalone `reports/`
package (which has zero Streamlit/UI dependencies and is independently
testable) for use inside the NovaMS dashboard.

INTEGRATION (streamlit_app.py) — 3 small, additive edits, nothing else:

1. Near the other optional-import try/except blocks at the top of
   streamlit_app.py, add:

       try:
           from reports_ui import render_reports_page
           _REPORTS_UI_AVAILABLE = True
       except ImportError:
           _REPORTS_UI_AVAILABLE = False

2. In the NAV_PAGES list, add "Reports" (anywhere — e.g. right after
   "Data Explorer"):

       NAV_PAGES = [
           ...,
           "Data Explorer",
           "Reports",          # <-- add this line
           "Sales by Location",
           ...
       ]

3. In the _PAGE_RENDERERS dict at the bottom, add:

       _PAGE_RENDERERS = {
           ...,
           "Data Explorer": render_data_explorer,
           "Reports": lambda: render_reports_page(
               df, st.session_state.get("_active_dataset_meta", {}).get("name", "Demo Dataset"),
               use_ai_mode, api_key,
           ) if _REPORTS_UI_AVAILABLE else st.error("Report Engine module not found — add reports_ui.py and the reports/ package."),
           ...,
       }

That's it — no existing calculation, filter, page, or style is touched.
`df`, `use_ai_mode`, and `api_key` are the same variables already defined
earlier in streamlit_app.py (the sidebar-filtered dataframe and the
existing BlinkBot AI Mode toggle/key), reused here rather than duplicated.
"""

from __future__ import annotations
import os
import tempfile

import streamlit as st
import pandas as pd

from reports import ReportEngine, REPORT_ENGINE_AVAILABLE, REPORT_ENGINE_IMPORT_ERROR

_REPORT_TYPES = ["Executive Report", "Board Summary", "Investor Update", "Monthly Business Review"]
_NOTEBOOK_REPORT_TYPES = ["EDA / Analysis Report", "Lab Report", "Project Report"]
_OUTPUT_DIR = os.path.join(tempfile.gettempdir(), "novams_reports")


def _preview_available() -> bool:
    try:
        import pymupdf  # noqa: F401
        return True
    except Exception:
        return False


def _render_pdf_preview(pdf_bytes: bytes, max_pages: int = 3):
    try:
        import pymupdf
        doc = pymupdf.open(stream=pdf_bytes, filetype="pdf")
        n = min(max_pages, doc.page_count)
        cols = st.columns(n)
        for i in range(n):
            pix = doc[i].get_pixmap(dpi=110)
            with cols[i]:
                st.image(pix.tobytes("png"), use_container_width=True, caption=f"Page {i+1} of {doc.page_count}")
    except Exception as e:
        st.caption(f"Preview unavailable ({e}) — download the PDF to view it.")


def render_reports_page(df: pd.DataFrame, dataset_name: str, use_ai_mode: bool, api_key: str,
                          theme_primary: str | None = None, theme_chart_palette: list | None = None):
    """Main 'Reports' page. `df` is the already-filtered dataframe the rest
    of NovaMS uses; `use_ai_mode`/`api_key` come from the existing BlinkBot
    AI Mode sidebar toggle, reused here rather than duplicated.

    `theme_primary`/`theme_chart_palette` come from NovaMS's own
    "Customize Dashboard" theme system (`_theme_vars['primary']` /
    `_theme_vars['chart_palette']` in streamlit_app.py) — when provided,
    the PDF's accent color and chart colors match whatever dashboard theme
    is currently active. The PDF's background/text/borders stay fixed for
    print legibility even when the dashboard itself uses a dark theme —
    only the brand accent and chart palette follow the theme."""

    st.markdown("""
    <div class="page-header">
      <div class="page-kicker">NovaMS</div>
      <h1 class="page-title">Reports</h1>
      <p class="page-sub">Generate a professional, board-ready Business Intelligence PDF from the current dataset</p>
    </div>
    """, unsafe_allow_html=True)

    if not REPORT_ENGINE_AVAILABLE:
        st.error(
            "⚠️ The Report Engine couldn't be loaded "
            f"({REPORT_ENGINE_IMPORT_ERROR}). Make sure `reportlab`, `matplotlib`, and "
            "`scikit-learn` are installed (see `reports/requirements-reports.txt`)."
        )
        return

    if df is None or df.empty:
        st.warning("⚠️ No data available for the current filter selection.")
        return

    st.markdown(
        '<div class="narrative-box">Every number in this report is calculated directly from your '
        'data by the Report Engine — nothing is invented. Sections the current dataset can\'t support '
        '(e.g. no date column → no forecast) are automatically omitted rather than faked.</div>',
        unsafe_allow_html=True,
    )

    report_style = st.radio(
        "Report Style",
        ["Executive BI Report", "Notebook / Lab Report (EDA)"],
        horizontal=True, key="report_style_choice",
        help="Executive BI Report: KPI cards, trends, regional/product breakdowns, forecast — "
             "for management, clients, investors. Notebook / Lab Report: chart + 'Interpretation:' "
             "paragraph for each variable, in the style of an academic/analysis writeup — no code shown.",
    )
    is_notebook = report_style.startswith("Notebook")

    c1, c2, c3 = st.columns([1.3, 1.3, 1])
    with c1:
        report_type = st.selectbox(
            "Report Type", _NOTEBOOK_REPORT_TYPES if is_notebook else _REPORT_TYPES,
            key="report_type_select",
        )
    with c2:
        company_name = st.text_input("Client / Company Name (optional)", key="report_company_name",
                                      placeholder="e.g. Nova Retail Pvt. Ltd.",
                                      disabled=is_notebook)
    with c3:
        include_excel = st.checkbox("Also generate Excel workbook", value=True, key="report_include_excel")

    match_theme = st.checkbox(
        "🎨 Match NovaMS dashboard theme", value=bool(theme_primary), key="report_match_theme",
        help="Uses your current dashboard theme's accent color and chart palette in the PDF. "
             "The report's background stays white for print legibility — only the brand color "
             "and chart colors follow the theme. Turn off to use NovaMS's default blue.",
        disabled=not bool(theme_primary),
    )
    if theme_primary and match_theme:
        _swatch = "".join(
            f'<span style="display:inline-block;width:14px;height:14px;border-radius:50%;'
            f'background:{c};margin-right:5px;border:1px solid rgba(255,255,255,.15)"></span>'
            for c in ([theme_primary] + list(theme_chart_palette or []))[:7]
        )
        st.markdown(f'<div style="margin:-4px 0 4px">{_swatch}</div>', unsafe_allow_html=True)
    elif not theme_primary:
        st.caption("No dashboard theme detected — the report will use NovaMS's default blue.")

    ai_default = bool(use_ai_mode and api_key)
    ai_enabled = False
    if not is_notebook:
        ai_enabled = st.checkbox(
            "🤖 Include AI Insights (Nova Analyst Decision Brief)", value=ai_default,
            key="report_ai_toggle",
            help="Uses the same Claude key as BlinkBot's LLM Mode. Claude only explains numbers the "
                 "Data/Analytics Engine already calculated — it never computes KPIs itself. "
                 "If unavailable, the report still generates in full.",
            disabled=not bool(api_key),
        )
        if ai_enabled and not api_key:
            st.caption("Enable LLM Mode and set a Claude API key in the sidebar to use AI Insights.")

    gen_col, prev_col, dl_col1, dl_col2 = st.columns(4)
    generate_clicked = gen_col.button("📊 Generate Report", type="primary", use_container_width=True)

    if generate_clicked:
        with st.spinner("Analyzing data, building charts, and assembling the PDF..."):
            engine = ReportEngine()
            result = engine.generate(
                df=df,
                dataset_name=dataset_name or "Dataset",
                report_type=report_type,
                company_name=company_name or None,
                ai_enabled=ai_enabled,
                api_key=api_key if ai_enabled else None,
                output_dir=_OUTPUT_DIR,
                include_excel=include_excel,
                style="notebook" if is_notebook else "executive",
                theme=(dict(primary=theme_primary, chart_palette=theme_chart_palette)
                       if (match_theme and theme_primary) else None),
            )
            st.session_state["_report_result"] = result

    result = st.session_state.get("_report_result")
    if not result:
        st.caption("Click **Generate Report** to build a PDF from the current (filtered) dataset.")
        return

    if not result.success:
        st.error("❌ Report generation failed:")
        for err in result.errors:
            st.markdown(f"- {err}")
        return

    st.success(f"✅ Report generated in {result.generation_seconds:.1f}s"
               + (" — with AI Insights" if result.ai_used else ""))

    if result.warnings:
        with st.expander(f"ℹ️ {len(result.warnings)} note(s) about this report"):
            for w in result.warnings:
                st.caption(f"• {w}")

    with dl_col1:
        st.download_button(
            "⬇ Download PDF", data=result.pdf_bytes, file_name=result.pdf_filename,
            mime="application/pdf", use_container_width=True,
        )
    with dl_col2:
        if result.excel_bytes:
            st.download_button(
                "⬇ Download Excel", data=result.excel_bytes, file_name=result.excel_filename,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )
        else:
            st.caption("No Excel workbook generated.")
    with prev_col:
        preview_clicked = st.button("👁 Preview", use_container_width=True, disabled=not _preview_available())
        if not _preview_available():
            st.caption("Install `pymupdf` for in-app preview.")

    if 'preview_clicked' in dir() and preview_clicked:
        st.markdown("---")
        _render_pdf_preview(result.pdf_bytes)

    if result.metrics and result.metrics.kpis:
        st.markdown('<div class="section-head">Quick Preview — Key Numbers</div>', unsafe_allow_html=True)
        cols = st.columns(min(4, len(result.metrics.kpis)) or 1)
        for i, (key, kpi) in enumerate(result.metrics.kpis.items()):
            with cols[i % len(cols)]:
                val = f"{kpi.current:.1f}%" if kpi.is_percent else (
                    f"₹{kpi.current:,.0f}" if kpi.is_currency else f"{kpi.current:,.0f}")
                delta = f"{kpi.change_pct:+.1f}% vs prior" if kpi.change_pct is not None else None
                st.metric(kpi.label, val, delta)
