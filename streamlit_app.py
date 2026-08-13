"""
NovaMS — Nova Management Solutions
Quick-Commerce Business Intelligence Platform
Phase 6: Modular sidebar navigation (Executive Overview, Sales, Delivery,
Inventory, Operations, Customer, Finance, AI Analyst, Data Explorer)
Developed by Ayush Mishra
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from scipy import stats
from sklearn.linear_model import LinearRegression
import warnings, io, os, json, requests

warnings.filterwarnings("ignore")

import sys as _sys
_sys.path.insert(0, os.path.dirname(__file__))

try:
    from data_engine.engine import DataEngine
    _DATA_ENGINE_AVAILABLE = True
except ImportError as _e:
    DataEngine = None
    _DATA_ENGINE_AVAILABLE = False
    _DATA_ENGINE_IMPORT_ERROR = str(_e)

try:
    from ai.semantic_interpreter import build_llm_context, interpret as interpret_with_claude
    _SEMANTIC_INTERPRETER_AVAILABLE = True
except ImportError as _e:
    build_llm_context = None
    interpret_with_claude = None
    _SEMANTIC_INTERPRETER_AVAILABLE = False
# ══════════════════════════════════════════════════════════════════════════════════
# ── PAGE CONFIG & STYLES
# ══════════════════════════════════════════════════════════════════════════════════

st.set_page_config(
    page_title="NovaMS — Nova Management Solutions",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
[data-testid="stDecoration"]   { visibility: hidden; }
[data-testid="stDeployButton"] { visibility: hidden; }
[data-testid="stToolbarActions"]{ display: none !important; }
footer   { visibility: hidden; }
#MainMenu{ visibility: hidden; }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

:root {
  --nova-ink:      #F1F5F9;
  --nova-ink-soft: #9AA4B2;
  --nova-muted:    #6B7688;
  --nova-border:   #262B33;
  --nova-bg:       #0A0C0F;
  --nova-card:     #14171C;
  --nova-blue:     #1D4DFF;
  --nova-blue-tint:rgba(29,77,255,.14);
  --nova-green:    #22C55E;
  --nova-green-tint:rgba(34,197,94,.14);
  --nova-red:      #EF4444;
  --nova-red-tint: rgba(239,68,68,.14);
  --nova-amber:    #D97706;
  --nova-amber-tint:rgba(217,119,6,.14);
  --nova-sidebar:  #07090B;
  --nova-sidebar-2:#14181D;
}

html, body, [class*="css"] { font-family: 'Inter', -apple-system, sans-serif; }
.main, [data-testid="stAppViewContainer"] { background: var(--nova-bg); }
.block-container { padding: 1.75rem 2.25rem 3rem; max-width: 1360px; }
h1, h2, h3, h4 { color: var(--nova-ink); letter-spacing: -.01em; }
p, span, div { -webkit-font-smoothing: antialiased; }

/* ── KPI cards — flat, left-aligned, single ink color, no gradients ── */
.kpi-card {
  background: var(--nova-card);
  border: 1px solid var(--nova-border);
  border-radius: 10px; padding: 16px 18px;
  text-align: left; position: relative;
}
.kpi-label { font-size: 11px; font-weight: 600; color: var(--nova-ink-soft); text-transform: uppercase; letter-spacing: .06em; margin-bottom: 8px; }
.kpi-value { font-size: 24px; font-weight: 700; color: var(--nova-ink); margin-bottom: 6px; line-height: 1.1; font-variant-numeric: tabular-nums; }
.kpi-sub   { font-size: 11px; color: var(--nova-muted); }
.kpi-badge { display: inline-block; font-size: 10px; font-weight: 600; border-radius: 4px; padding: 2px 7px; margin-bottom: 6px; }
.up   { background: var(--nova-green-tint); color: var(--nova-green); }
.down { background: var(--nova-red-tint);   color: var(--nova-red); }

/* ── Executive Overview KPI redesign — namespaced separately (nova-kpi-*)
   from the .kpi-card system above so every other page's KPI tiles
   (Data Explorer, Inventory, Operations, Finance, Trust Center, etc.)
   are completely unaffected. Restrained, flat, no gradients/glow —
   matches the existing narrative-box / insight-card visual language. ── */
.nova-kpi-card {
  background: var(--nova-card);
  border: 1px solid var(--nova-border);
  border-radius: 10px;
  padding: 13px 14px 15px;
  height: 100%;
  box-sizing: border-box;
  position: relative;
  opacity: 0;
  animation: novaKpiFadeIn .5s ease-out forwards;
  animation-delay: var(--kpi-delay, 0s);
}
@keyframes novaKpiFadeIn {
  from { opacity: 0; transform: translateY(4px); }
  to   { opacity: 1; transform: translateY(0); }
}
.nova-kpi-top {
  display: flex; align-items: center; gap: 8px;
  margin-bottom: 11px;
}
.nova-kpi-icon-chip {
  width: 26px; height: 26px; border-radius: 7px; flex-shrink: 0;
  display: flex; align-items: center; justify-content: center;
  background: var(--chip-bg, var(--nova-blue-tint));
  color: var(--chip-fg, var(--nova-blue));
}
.nova-kpi-icon-chip svg { width: 13px; height: 13px; display: block; }
.nova-kpi-label {
  font-size: 10px; font-weight: 600; color: var(--nova-ink-soft);
  text-transform: uppercase; letter-spacing: .04em;
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis; min-width: 0;
}
.nova-kpi-badge {
  display: inline-block; font-size: 10.5px; font-weight: 600;
  border-radius: 4px; padding: 2px 7px; margin-bottom: 8px;
}
.nova-kpi-badge.up      { background: var(--nova-green-tint); color: var(--nova-green); }
.nova-kpi-badge.down    { background: var(--nova-red-tint);   color: var(--nova-red); }
.nova-kpi-badge.neutral { background: rgba(148,163,184,.12);  color: var(--nova-ink-soft); }
.nova-kpi-value {
  font-size: 19px; font-weight: 700; color: var(--nova-ink);
  line-height: 1.15; font-variant-numeric: tabular-nums;
  margin-bottom: 4px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.nova-kpi-sub {
  font-size: 10.5px; color: var(--nova-muted); line-height: 1.5;
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.nova-kpi-body { display: flex; align-items: flex-end; justify-content: space-between; gap: 6px; flex-wrap: nowrap; }
.nova-kpi-body .nova-kpi-text { flex: 1 1 auto; min-width: 0; }

/* Real per-row-data sparkline, drawn in with a stroke animation */
.nova-kpi-spark { width: 46px; height: 26px; flex: 0 0 46px; margin-bottom: 2px; }
.nova-kpi-spark svg { width: 100%; height: 100%; display: block; }
.nova-kpi-spark path.line {
  animation: novaSparkDraw 1.1s cubic-bezier(.3,.8,.4,1) forwards;
  animation-delay: var(--kpi-delay, 0s);
}
@keyframes novaSparkDraw { to { stroke-dashoffset: 0; } }

/* Progress ring — filled to the real percentage, fades/scales in on load */
.nova-kpi-ring-wrap {
  position: relative; width: 48px; height: 48px; flex: 0 0 48px;
  transform: scale(.85); opacity: 0;
  animation: novaRingIn .55s cubic-bezier(.3,.8,.4,1) forwards;
  animation-delay: calc(var(--kpi-delay, 0s) + .15s);
}
@keyframes novaRingIn { to { transform: scale(1); opacity: 1; } }
.nova-kpi-ring {
  width: 100%; height: 100%; border-radius: 50%;
  background: conic-gradient(var(--ring-color, var(--nova-blue)) calc(var(--ring-pct, 0) * 1%), var(--nova-border) 0);
  display: flex; align-items: center; justify-content: center;
}
.nova-kpi-ring-inner {
  width: 70%; height: 70%; border-radius: 50%; background: var(--nova-card);
  display: flex; align-items: center; justify-content: center;
  font-size: 10.5px; font-weight: 700; color: var(--nova-ink);
}

/* Bottom accent bar — animates its width in from 0 on load */
.nova-kpi-growbar {
  position: absolute; left: 0; bottom: 0; height: 3px; width: 0%;
  background: var(--bar-color, var(--nova-blue));
  animation: novaKpiGrow 1s cubic-bezier(.22,.85,.35,1) forwards;
  animation-delay: calc(var(--kpi-delay, 0s) + .1s);
}
@keyframes novaKpiGrow { to { width: 100%; } }

/* ── Section labels ── */
.section-head {
  font-size: 11px; font-weight: 700; color: var(--nova-ink-soft);
  text-transform: uppercase; letter-spacing: .08em;
  border-left: 3px solid var(--nova-blue); padding-left: 10px;
  margin: 28px 0 14px;
}

/* ── Page header — flat, no colored box, eyebrow + title + divider ── */
.page-header {
  border-bottom: 1px solid var(--nova-border);
  padding: 4px 0 18px; margin-bottom: 22px;
}
.page-kicker {
  font-size: 11px; font-weight: 700; color: var(--nova-blue);
  text-transform: uppercase; letter-spacing: .1em; margin-bottom: 6px;
}
.page-title { margin: 0; font-size: 26px; font-weight: 700; color: var(--nova-ink); }
.page-sub { margin: 6px 0 0; font-size: 13px; color: var(--nova-ink-soft); }

/* ── Callouts ── */
.narrative-box {
  background: var(--nova-blue-tint); border-left: 3px solid var(--nova-blue);
  border-radius: 0 8px 8px 0; padding: 12px 16px; margin-bottom: 18px;
  font-size: 12.5px; color: var(--nova-ink-soft); line-height: 1.65;
}
.narrative-box b { color: var(--nova-ink); font-weight: 600; }
.missing-box {
  background: var(--nova-amber-tint); border-left: 3px solid var(--nova-amber);
  border-radius: 0 8px 8px 0; padding: 12px 16px; margin: 10px 0;
  font-size: 12.5px; color: #FBBF24; line-height: 1.65;
}

/* ── Insight cards ── */
.insight-card {
  background: var(--nova-card); border: 1px solid var(--nova-border);
  border-radius: 10px; padding: 16px; height: 100%; margin-bottom: 4px;
}
.insight-title { font-size: 10.5px; font-weight: 700; color: var(--nova-blue); text-transform: uppercase; letter-spacing: .06em; margin-bottom: 6px; }
.insight-body  { font-size: 12.5px; color: var(--nova-ink-soft); line-height: 1.6; }
.insight-body strong { color: var(--nova-ink); }

/* ── Stat rows (used inside white panel cards) ── */
.stat-row  { display: flex; justify-content: space-between; padding: 7px 0; border-bottom: 1px solid var(--nova-border); }
.stat-label{ font-size: 11.5px; color: var(--nova-ink-soft); }
.stat-value{ font-size: 11.5px; font-weight: 700; color: var(--nova-ink); font-family: 'SF Mono', monospace; }

/* ── Footer ── */
.footer { text-align: center; padding: 24px 0; color: var(--nova-muted); font-size: 11.5px; border-top: 1px solid var(--nova-border); margin-top: 34px; }
.footer .dev { color: var(--nova-blue); font-weight: 700; }

/* ── BlinkBot chat ── */
.chat-message-bot {
  background: var(--nova-card); border: 1px solid var(--nova-border);
  border-left: 3px solid var(--nova-blue); border-radius: 4px 10px 10px 4px;
  padding: 14px 16px; margin: 8px 0; font-size: 13px; color: var(--nova-ink); line-height: 1.65;
}
.chat-message-user {
  background: var(--nova-blue); border-radius: 10px 10px 4px 10px;
  padding: 12px 16px; margin: 8px 0 8px auto; max-width: 78%;
  font-size: 13px; color: #14171C; text-align: left;
}
div[data-testid="metric-container"] {
  background: var(--nova-card); border: 1px solid var(--nova-border); border-radius: 10px; padding: 12px;
}
.blinkbot-header {
  background: var(--nova-card); border: 1px solid var(--nova-border);
  border-left: 3px solid var(--nova-blue);
  padding: 14px 18px; display: flex; align-items: center; gap: 12px;
  border-radius: 4px 10px 10px 4px; margin-bottom: 16px;
}

/* ══════════════════════════════════════════════════════════════════════
   PREMIUM SIDEBAR — enterprise SaaS redesign (visual layer only).
   Every underlying Streamlit widget (radio/selectbox/checkbox/toggle/
   text_input/button) keeps its default DOM + key + behavior; only its
   appearance is restyled here. No routing, session_state, or business
   logic is touched by this block.
   ══════════════════════════════════════════════════════════════════════ */

section[data-testid="stSidebar"] {
  background: var(--nova-sidebar) !important;
  border-right: 1px solid var(--nova-border);
  overflow-x: hidden !important;
}
section[data-testid="stSidebar"] > div { background: var(--nova-sidebar) !important; overflow-x: hidden !important; }
/* NOTE: color-only, no font-family here — the page already sets Inter
   globally via html/body above, and overriding font-family a second time
   here also clobbers Streamlit's own icon font (used by its native
   sidebar-collapse control etc.), which caused an earlier glitch. */
section[data-testid="stSidebar"] * { color: var(--nova-ink); }
section[data-testid="stSidebar"] h1, section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3, section[data-testid="stSidebar"] h4 { color: var(--nova-ink); }
section[data-testid="stSidebar"] .stMarkdown p { color: var(--nova-ink-soft); }
section[data-testid="stSidebar"] hr { border-color: var(--nova-border); margin: 14px 0; }
section[data-testid="stSidebar"] .block-container { padding: 18px 16px 20px !important; overflow-x: hidden; }

/* Collapsed-sidebar expand control (the ">>" shown when the sidebar is
   closed) — Streamlit renders this outside section[data-testid="stSidebar"],
   so it needs its own styling. Using a substring/case-insensitive attribute
   match (rather than one exact testid) so this keeps working across
   Streamlit versions that name this element differently. */
[data-testid*="ollaps" i] {
  background: var(--nova-card) !important;
  border: 1px solid var(--nova-border) !important;
  border-radius: 8px !important;
  margin: 10px !important;
  padding: 4px !important;
}
[data-testid*="ollaps" i] * {
  color: var(--nova-ink-soft) !important;
}
[data-testid*="ollaps" i]:hover {
  border-color: var(--nova-blue) !important;
}
[data-testid*="ollaps" i] button {
  background: transparent !important;
  border: none !important;
}

/* Section labels (Navigation / Data Source / Filters / Settings / etc.) */
section[data-testid="stSidebar"] [data-testid="stWidgetLabel"] p,
section[data-testid="stSidebar"] h4 {
  font-size: 10.5px !important; font-weight: 700 !important; color: var(--nova-muted) !important;
  text-transform: uppercase !important; letter-spacing: .08em !important;
  margin-top: 4px;
}

/* ── Brand section — flat, matches the rest of the dashboard's cards ─── */
.nav-brand { text-align:center; padding:6px 0 18px; }
.nav-brand .logo {
  width:42px;height:42px;
  background: var(--nova-blue);
  border-radius:10px;display:inline-flex;align-items:center;justify-content:center;
  font-size:19px;font-weight:700;color:#fff;margin-bottom:12px;
}
.nav-brand .name { font-size:18px;font-weight:700;color:var(--nova-ink);letter-spacing:-.01em; }
.nav-brand .tag { font-size:11px;color:var(--nova-ink-soft);margin-top:4px; font-weight:500; }
.nav-brand .caption {
  font-size:9.5px;color:var(--nova-muted);margin-top:6px; letter-spacing:.08em; text-transform:uppercase;
  font-weight:700;
}

/* ── Navigation — turn the st.radio group into quiet nav rows ────────── */
section[data-testid="stSidebar"] [role="radiogroup"] {
  display: flex; flex-direction: column; gap: 2px;
}
/* Hide BaseWeb's native radio dot graphic — row look only (targets the
   stable data-baseweb wrapper first, with a positional fallback) */
section[data-testid="stSidebar"] [role="radiogroup"] label [data-baseweb="radio"] {
  display: none !important;
}
section[data-testid="stSidebar"] [role="radiogroup"] label > div:first-child {
  display: none !important;
}
/* Extra fallback: hide every child of the label except the last one
   (the text wrapper), regardless of exactly how Streamlit/BaseWeb nests
   the radio circle in this version. */
section[data-testid="stSidebar"] [role="radiogroup"] label > *:not(:last-child) {
  display: none !important;
}
section[data-testid="stSidebar"] [role="radiogroup"] label {
  position: relative;
  display: flex; align-items: center;
  height: 42px; padding: 0 12px; margin-bottom: 1px;
  border-radius: 8px;
  border-left: 3px solid transparent;
  background: transparent;
  color: var(--nova-ink-soft);
  font-weight: 500; font-size: 13.5px;
  cursor: pointer; box-sizing: border-box; overflow: visible;
  transition: background-color .15s ease, color .15s ease, border-color .15s ease;
}
section[data-testid="stSidebar"] [role="radiogroup"] label * { color: inherit !important; font-weight: inherit !important; }
section[data-testid="stSidebar"] [role="radiogroup"] label:hover {
  background: var(--nova-sidebar-2);
  color: var(--nova-ink);
}
section[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) {
  background: var(--nova-blue-tint) !important;
  border-left-color: var(--nova-blue);
  color: var(--nova-ink) !important;
  font-weight: 600;
}

/* Icons — inline-SVG CSS masks (font-independent, cannot silently fail
   like a webfont ligature can). One shared base rule + per-item shape. */
section[data-testid="stSidebar"] [role="radiogroup"] label:nth-of-type(1)::before,
section[data-testid="stSidebar"] [role="radiogroup"] label:nth-of-type(2)::before,
section[data-testid="stSidebar"] [role="radiogroup"] label:nth-of-type(3)::before,
section[data-testid="stSidebar"] [role="radiogroup"] label:nth-of-type(4)::before,
section[data-testid="stSidebar"] [role="radiogroup"] label:nth-of-type(5)::before,
section[data-testid="stSidebar"] [role="radiogroup"] label:nth-of-type(6)::before,
section[data-testid="stSidebar"] [role="radiogroup"] label:nth-of-type(7)::before,
section[data-testid="stSidebar"] [role="radiogroup"] label:nth-of-type(8)::before,
section[data-testid="stSidebar"] [role="radiogroup"] label:nth-of-type(9)::before,
section[data-testid="stSidebar"] [role="radiogroup"] label:nth-of-type(10)::after {
  content: "";
  display: inline-block; flex-shrink: 0;
  width: 17px; height: 17px; margin-right: 11px;
  background-color: var(--nova-ink-soft);
  -webkit-mask-repeat: no-repeat; mask-repeat: no-repeat;
  -webkit-mask-position: center; mask-position: center;
  -webkit-mask-size: contain; mask-size: contain;
  transition: background-color .15s ease;
}
section[data-testid="stSidebar"] [role="radiogroup"] label:hover::before,
section[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked)::before {
  background-color: var(--nova-blue);
}
/* Item 10 is the only item whose icon lives on ::after (its ::before holds
   the "SYSTEM" header instead) — scoped separately so this never touches
   item 9's ::after, which holds the "NEW" badge, not an icon. */
section[data-testid="stSidebar"] [role="radiogroup"] label:nth-of-type(10):hover::after,
section[data-testid="stSidebar"] [role="radiogroup"] label:nth-of-type(10):has(input:checked)::after {
  background-color: var(--nova-blue);
}
section[data-testid="stSidebar"] [role="radiogroup"] label:nth-of-type(1)::before {
  -webkit-mask-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'%3E%3Crect x='3' y='3' width='8' height='8' rx='2'/%3E%3Crect x='13' y='3' width='8' height='8' rx='2'/%3E%3Crect x='3' y='13' width='8' height='8' rx='2'/%3E%3Crect x='13' y='13' width='8' height='8' rx='2'/%3E%3C/svg%3E");
  mask-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'%3E%3Crect x='3' y='3' width='8' height='8' rx='2'/%3E%3Crect x='13' y='3' width='8' height='8' rx='2'/%3E%3Crect x='3' y='13' width='8' height='8' rx='2'/%3E%3Crect x='13' y='13' width='8' height='8' rx='2'/%3E%3C/svg%3E");
}
section[data-testid="stSidebar"] [role="radiogroup"] label:nth-of-type(2)::before {
  -webkit-mask-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'%3E%3Crect x='3' y='13' width='4' height='8' rx='1'/%3E%3Crect x='10' y='8' width='4' height='13' rx='1'/%3E%3Crect x='17' y='3' width='4' height='18' rx='1'/%3E%3C/svg%3E");
  mask-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'%3E%3Crect x='3' y='13' width='4' height='8' rx='1'/%3E%3Crect x='10' y='8' width='4' height='13' rx='1'/%3E%3Crect x='17' y='3' width='4' height='18' rx='1'/%3E%3C/svg%3E");
}
section[data-testid="stSidebar"] [role="radiogroup"] label:nth-of-type(3)::before {
  -webkit-mask-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'%3E%3Crect x='9' y='6' width='6' height='11' rx='1.5'/%3E%3Crect x='11' y='2' width='2' height='4'/%3E%3Crect x='11' y='17' width='2' height='4'/%3E%3C/svg%3E");
  mask-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'%3E%3Crect x='9' y='6' width='6' height='11' rx='1.5'/%3E%3Crect x='11' y='2' width='2' height='4'/%3E%3Crect x='11' y='17' width='2' height='4'/%3E%3C/svg%3E");
}
section[data-testid="stSidebar"] [role="radiogroup"] label:nth-of-type(4)::before {
  -webkit-mask-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'%3E%3Cpath d='M12 2 L21 7 V17 L12 22 L3 17 V7 Z'/%3E%3C/svg%3E");
  mask-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'%3E%3Cpath d='M12 2 L21 7 V17 L12 22 L3 17 V7 Z'/%3E%3C/svg%3E");
}
section[data-testid="stSidebar"] [role="radiogroup"] label:nth-of-type(5)::before {
  -webkit-mask-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'%3E%3Crect x='3' y='4' width='18' height='7' rx='1.5'/%3E%3Crect x='3' y='13' width='18' height='7' rx='1.5'/%3E%3C/svg%3E");
  mask-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'%3E%3Crect x='3' y='4' width='18' height='7' rx='1.5'/%3E%3Crect x='3' y='13' width='18' height='7' rx='1.5'/%3E%3C/svg%3E");
}
section[data-testid="stSidebar"] [role="radiogroup"] label:nth-of-type(6)::before {
  -webkit-mask-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'%3E%3Ccircle cx='6' cy='7' r='2.5'/%3E%3Crect x='9' y='6' width='12' height='2' rx='1'/%3E%3Ccircle cx='18' cy='14' r='2.5'/%3E%3Crect x='3' y='13' width='12' height='2' rx='1'/%3E%3Ccircle cx='9' cy='20' r='2.5'/%3E%3Crect x='12' y='19' width='9' height='2' rx='1'/%3E%3C/svg%3E");
  mask-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'%3E%3Ccircle cx='6' cy='7' r='2.5'/%3E%3Crect x='9' y='6' width='12' height='2' rx='1'/%3E%3Ccircle cx='18' cy='14' r='2.5'/%3E%3Crect x='3' y='13' width='12' height='2' rx='1'/%3E%3Ccircle cx='9' cy='20' r='2.5'/%3E%3Crect x='12' y='19' width='9' height='2' rx='1'/%3E%3C/svg%3E");
}
section[data-testid="stSidebar"] [role="radiogroup"] label:nth-of-type(7)::before {
  -webkit-mask-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'%3E%3Ccircle cx='9' cy='9' r='4'/%3E%3Ccircle cx='17' cy='8' r='3'/%3E%3C/svg%3E");
  mask-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'%3E%3Ccircle cx='9' cy='9' r='4'/%3E%3Ccircle cx='17' cy='8' r='3'/%3E%3C/svg%3E");
}
section[data-testid="stSidebar"] [role="radiogroup"] label:nth-of-type(8)::before {
  -webkit-mask-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'%3E%3Ccircle cx='12' cy='12' r='9'/%3E%3C/svg%3E");
  mask-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'%3E%3Ccircle cx='12' cy='12' r='9'/%3E%3C/svg%3E");
}
section[data-testid="stSidebar"] [role="radiogroup"] label:nth-of-type(9)::before {
  -webkit-mask-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'%3E%3Cpath d='M12 2 L14 9 L21 12 L14 15 L12 22 L10 15 L3 12 L10 9 Z'/%3E%3C/svg%3E");
  mask-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'%3E%3Cpath d='M12 2 L14 9 L21 12 L14 15 L12 22 L10 15 L3 12 L10 9 Z'/%3E%3C/svg%3E");
}
section[data-testid="stSidebar"] [role="radiogroup"] label:nth-of-type(10) { padding-left: 42px; }
section[data-testid="stSidebar"] [role="radiogroup"] label:nth-of-type(10)::after {
  position: absolute; left: 12px; top: 50%; transform: translateY(-50%); margin-right: 0;
  -webkit-mask-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'%3E%3Cellipse cx='12' cy='5' rx='9' ry='3'/%3E%3Cellipse cx='12' cy='12' rx='9' ry='3'/%3E%3Cellipse cx='12' cy='19' rx='9' ry='3'/%3E%3C/svg%3E");
  mask-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'%3E%3Cellipse cx='12' cy='5' rx='9' ry='3'/%3E%3Cellipse cx='12' cy='12' rx='9' ry='3'/%3E%3Cellipse cx='12' cy='19' rx='9' ry='3'/%3E%3C/svg%3E");
}

/* Section headers — attached to the preceding/following item so no
   pseudo-element ever needs to serve two purposes on the same label */
section[data-testid="stSidebar"] [role="radiogroup"] label:nth-of-type(1)::after {
  content: "ANALYTICS";
  position: absolute; left: 12px; top: 100%; margin-top: 12px;
  font-size: 10px; font-weight: 700; color: var(--nova-muted);
  letter-spacing: .1em; text-transform: uppercase;
}
section[data-testid="stSidebar"] [role="radiogroup"] label:nth-of-type(1) { margin-bottom: 30px; }

section[data-testid="stSidebar"] [role="radiogroup"] label:nth-of-type(8)::after {
  content: "AI MODULES";
  position: absolute; left: 12px; top: 100%; margin-top: 12px;
  font-size: 10px; font-weight: 700; color: var(--nova-muted);
  letter-spacing: .1em; text-transform: uppercase;
}
section[data-testid="stSidebar"] [role="radiogroup"] label:nth-of-type(8) { margin-bottom: 30px; }

section[data-testid="stSidebar"] [role="radiogroup"] label:nth-of-type(10)::before {
  content: "SYSTEM";
  position: absolute; left: 12px; top: -20px;
  font-size: 10px; font-weight: 700; color: var(--nova-muted);
  letter-spacing: .1em; text-transform: uppercase;
}
section[data-testid="stSidebar"] [role="radiogroup"] label:nth-of-type(10) { margin-top: 18px; }

/* "NEW" badge — AI Analyst (BlinkBot) item only. Flat tint, matching the
   .up/.down WoW-delta badges already used on the KPI cards elsewhere. */
section[data-testid="stSidebar"] [role="radiogroup"] label:nth-of-type(9) {
  position: relative;
}
section[data-testid="stSidebar"] [role="radiogroup"] label:nth-of-type(9)::after {
  content: "NEW";
  position: absolute; right: 10px; top: 50%; transform: translateY(-50%);
  font-size: 9px; font-weight: 700; letter-spacing: .04em;
  color: var(--nova-blue); background: var(--nova-blue-tint);
  padding: 2px 6px; border-radius: 4px;
}

/* Icon + section label for the new 11th nav item (Sales by Location) —
   standalone rules only, so items 1-10 and all their existing icon/section
   CSS above are completely untouched. */
section[data-testid="stSidebar"] [role="radiogroup"] label:nth-of-type(11) {
  margin-top: 8px;
}
section[data-testid="stSidebar"] [role="radiogroup"] label:nth-of-type(11)::before {
  content: "";
  display: inline-block; flex-shrink: 0;
  width: 17px; height: 17px; margin-right: 11px;
  background-color: var(--nova-ink-soft);
  -webkit-mask-repeat: no-repeat; mask-repeat: no-repeat;
  -webkit-mask-position: center; mask-position: center;
  -webkit-mask-size: contain; mask-size: contain;
  transition: background-color .15s ease;
  -webkit-mask-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'%3E%3Cpath d='M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7Zm0 9.5A2.5 2.5 0 1 1 12 6.5a2.5 2.5 0 0 1 0 5Z'/%3E%3C/svg%3E");
  mask-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'%3E%3Cpath d='M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7Zm0 9.5A2.5 2.5 0 1 1 12 6.5a2.5 2.5 0 0 1 0 5Z'/%3E%3C/svg%3E");
}
section[data-testid="stSidebar"] [role="radiogroup"] label:nth-of-type(11):hover::before,
section[data-testid="stSidebar"] [role="radiogroup"] label:nth-of-type(11):has(input:checked)::before {
  background-color: var(--nova-blue);
}

/* Icon for the new 12th nav item (Product Analytics) — standalone rule
   only, items 1-11 above are completely untouched. */
section[data-testid="stSidebar"] [role="radiogroup"] label:nth-of-type(12)::before {
  content: "";
  display: inline-block; flex-shrink: 0;
  width: 17px; height: 17px; margin-right: 11px;
  background-color: var(--nova-ink-soft);
  -webkit-mask-repeat: no-repeat; mask-repeat: no-repeat;
  -webkit-mask-position: center; mask-position: center;
  -webkit-mask-size: contain; mask-size: contain;
  transition: background-color .15s ease;
  -webkit-mask-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'%3E%3Crect x='3' y='11' width='4' height='10' rx='1'/%3E%3Crect x='10' y='6' width='4' height='15' rx='1'/%3E%3Crect x='17' y='2' width='4' height='19' rx='1'/%3E%3C/svg%3E");
  mask-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'%3E%3Crect x='3' y='11' width='4' height='10' rx='1'/%3E%3Crect x='10' y='6' width='4' height='15' rx='1'/%3E%3Crect x='17' y='2' width='4' height='19' rx='1'/%3E%3C/svg%3E");
}
section[data-testid="stSidebar"] [role="radiogroup"] label:nth-of-type(12):hover::before,
section[data-testid="stSidebar"] [role="radiogroup"] label:nth-of-type(12):has(input:checked)::before {
  background-color: var(--nova-blue);
}

/* ── Inputs / selects inside the sidebar ─────────────────────────────── */
section[data-testid="stSidebar"] .stTextInput input,
section[data-testid="stSidebar"] .stSelectbox div[data-baseweb="select"] > div {
  background: var(--nova-sidebar-2) !important;
  border: 1px solid var(--nova-border) !important;
  border-radius: 8px !important;
  color: var(--nova-ink) !important;
}
section[data-testid="stSidebar"] .stSelectbox div[data-baseweb="select"]:focus-within > div,
section[data-testid="stSidebar"] .stTextInput input:focus {
  border-color: var(--nova-blue) !important;
  box-shadow: 0 0 0 2px var(--nova-blue-tint) !important;
}
section[data-testid="stSidebar"] .stCheckbox label, section[data-testid="stSidebar"] .stToggle label {
  font-size: 12.5px; color: var(--nova-ink-soft);
}

/* ── Workspace status card — flat, same treatment as .insight-card ──── */
.nova-workspace-card {
  background: var(--nova-card);
  border: 1px solid var(--nova-border);
  border-radius: 10px;
  padding: 12px 14px;
  margin: 6px 0 12px;
}
.nova-workspace-card .ws-label {
  font-size: 9.5px; font-weight: 700; color: var(--nova-muted);
  text-transform: uppercase; letter-spacing: .08em; margin-bottom: 8px;
}
.nova-workspace-card .ws-row {
  display: flex; align-items: center; justify-content: space-between;
  font-size: 12px; color: var(--nova-ink); padding: 3px 0;
}
.nova-workspace-card .ws-dot {
  display:inline-block; width:6px; height:6px; border-radius:50%;
  background: var(--nova-green); margin-right:7px;
}

/* ── User profile / logout footer — flat card, matches .insight-card ── */
.nova-profile-card {
  display:flex; align-items:center; gap:10px;
  background: var(--nova-card); border: 1px solid var(--nova-border);
  border-radius: 10px; padding: 10px 12px; margin-bottom: 8px;
}
.nova-profile-avatar {
  position:relative; width:32px; height:32px; border-radius:50%;
  background: var(--nova-blue);
  display:flex; align-items:center; justify-content:center;
  font-size:12px; font-weight:700; color:#fff; flex-shrink:0;
}
.nova-profile-avatar .dot {
  position:absolute; bottom:-1px; right:-1px; width:8px; height:8px;
  background: var(--nova-green); border:2px solid var(--nova-card); border-radius:50%;
}
.nova-profile-name { font-size:12.5px; font-weight:600; color:var(--nova-ink); line-height:1.3; }
.nova-profile-role  { font-size:10.5px; color:var(--nova-ink-soft); }

/* ── Global Streamlit primary accent (buttons, tabs, focus rings) ── */
.stButton>button, [data-testid="stFormSubmitButton"] button, [data-testid="stBaseButton-primary"] {
  border-radius: 7px; font-weight: 600;
}
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════════
# ── AUTHENTICATION
# Simple, real credential check against st.secrets — no new database tables,
# no new dependencies. Add a [auth] section to .streamlit/secrets.toml:
#
#   [auth]
#   users = { ayush = "your-password", judge = "demo-pass" }
#
# If [auth] isn't configured at all (e.g. running locally without secrets
# set up yet), a single fallback demo password is used instead, with a
# visible on-screen warning so it's never silently insecure.
# ══════════════════════════════════════════════════════════════════════════════════

_FALLBACK_AUTH_USER = "demo"
_FALLBACK_AUTH_PASS = "novams2026"


def _get_configured_users() -> dict:
    try:
        users = dict(st.secrets["auth"]["users"])
        if users:
            return users
    except Exception:
        pass
    return {}


def _render_login_screen():
    configured_users = _get_configured_users()
    using_fallback = not configured_users

    st.markdown("""
    <div style="max-width:380px;margin:8vh auto 0;text-align:center">
      <div style="width:48px;height:48px;background:#1D4DFF;border-radius:11px;
                  display:inline-flex;align-items:center;justify-content:center;
                  font-size:22px;font-weight:700;color:#fff;margin-bottom:14px">N</div>
      <h1 style="font-size:24px;font-weight:700;color:#F1F5F9;margin:0 0 4px">NovaMS</h1>
      <p style="font-size:13px;color:#9AA4B2;margin:0 0 28px">Sign in to continue</p>
    </div>
    """, unsafe_allow_html=True)

    _, mid, _ = st.columns([1, 1.4, 1])
    with mid:
        if using_fallback:
            st.markdown(
                '<div class="missing-box">⚠️ No <code>[auth]</code> section found in '
                '<code>secrets.toml</code> — using a fallback demo login '
                f'(<code>{_FALLBACK_AUTH_USER}</code> / <code>{_FALLBACK_AUTH_PASS}</code>). '
                'Set real credentials before sharing this deployment.</div>',
                unsafe_allow_html=True,
            )
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Sign in", use_container_width=True, type="primary")

        if submitted:
            valid_users = configured_users if configured_users else {_FALLBACK_AUTH_USER: _FALLBACK_AUTH_PASS}
            if username in valid_users and password == valid_users[username]:
                st.session_state["_authenticated"] = True
                st.session_state["_auth_user"] = username
                st.rerun()
            else:
                st.error("❌ Incorrect username or password.")


def require_login():
    if not st.session_state.get("_authenticated"):
        _render_login_screen()
        st.stop()


# Authentication temporarily disabled — uncomment the line below to re-enable.
# require_login()

# ══════════════════════════════════════════════════════════════════════════════════
# ── CONSTANTS
# ══════════════════════════════════════════════════════════════════════════════════

PAL      = ["#6366f1","#06b6d4","#10b981","#f59e0b","#ef4444","#8b5cf6","#ec4899","#14b8a6","#f97316","#3b82f6"]
CAT_CLR  = {"Snacks":"#6366f1","Beverages":"#06b6d4","Grocery":"#10b981","Instant Food":"#f59e0b","Confectionery":"#ec4899","Dairy":"#8b5cf6"}
CITY_CLR = {"Delhi":"#6366f1","Mumbai":"#06b6d4","Bangalore":"#10b981","Hyderabad":"#f59e0b","Chennai":"#ef4444","Pune":"#8b5cf6"}

PLOTLY_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Inter", color="#9AA4B2", size=11),
    margin=dict(l=10, r=10, t=30, b=10),
    xaxis=dict(gridcolor="rgba(255,255,255,.05)", linecolor="rgba(255,255,255,.09)"),
    yaxis=dict(gridcolor="rgba(255,255,255,.05)", linecolor="rgba(255,255,255,.09)"),
    legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(size=10)),
)

_AXIS_DEFAULTS = dict(gridcolor="rgba(255,255,255,.05)", linecolor="rgba(255,255,255,.09)")


def _hex_to_rgba(hex_color: str, alpha: float = 0.08) -> str:
    if not (isinstance(hex_color, str) and hex_color.startswith("#") and len(hex_color) == 7):
        return hex_color
    r = int(hex_color[1:3], 16)
    g = int(hex_color[3:5], 16)
    b = int(hex_color[5:7], 16)
    return f"rgba({r},{g},{b},{alpha})"


def _lighten_hex(hex_color: str, amount: int = 12) -> str:
    """Nudges a hex color lighter by a fixed amount per channel — used to
    derive the secondary sidebar shade for the Custom theme automatically,
    since the customization panel doesn't expose a separate picker for it."""
    if not (isinstance(hex_color, str) and hex_color.startswith("#") and len(hex_color) == 7):
        return hex_color
    r = min(255, int(hex_color[1:3], 16) + amount)
    g = min(255, int(hex_color[3:5], 16) + amount)
    b = min(255, int(hex_color[5:7], 16) + amount)
    return f"#{r:02X}{g:02X}{b:02X}"


def _relative_luminance(hex_color: str) -> float:
    def _chan(c):
        c = c / 255
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = int(hex_color[1:3], 16), int(hex_color[3:5], 16), int(hex_color[5:7], 16)
    return 0.2126 * _chan(r) + 0.7152 * _chan(g) + 0.0722 * _chan(b)


def _contrast_ratio(hex1: str, hex2: str) -> float:
    """WCAG-style contrast ratio between two hex colors — used to warn the
    user in the theme customizer if their chosen Text/Background pair would
    be hard to read (Part 17: 'Do not allow customization to reduce data
    readability')."""
    try:
        l1, l2 = _relative_luminance(hex1), _relative_luminance(hex2)
    except Exception:
        return 21.0  # can't evaluate — don't block the user with a false warning
    lighter, darker = max(l1, l2), min(l1, l2)
    return (lighter + 0.05) / (darker + 0.05)


# ══════════════════════════════════════════════════════════════════════════════════
# ── CUSTOMIZE DASHBOARD — THEME PRESETS
# Every value below maps directly onto the CSS custom properties (--nova-*)
# already defined in the main stylesheet above, so switching themes reaches
# every component that already references var(--nova-...) — KPI cards,
# section headers, narrative/insight boxes, chat bubbles, sidebar, buttons,
# badges — with no changes to any of that existing CSS or Python.
# Known limitation: a handful of page-specific HTML snippets elsewhere in
# the app (e.g. the Data Trust Center score card, a few summary cards) use
# literal hex colors rather than var(--nova-...) and won't reflect a theme
# change. Converting those is a good follow-up, not done in this pass.
# ══════════════════════════════════════════════════════════════════════════════════

THEME_PRESETS = {
    "Nova Blue": dict(       # the current/original NovaMS look — default
        primary="#1D4DFF", bg="#0A0C0F", card="#14171C", sidebar="#07090B",
        sidebar2="#14181D", text="#F1F5F9", muted="#9AA4B2",
        success="#22C55E", warning="#D97706", danger="#EF4444", border="#262B33",
    ),
    "Executive Dark": dict(
        primary="#4F6BFF", bg="#0B0D12", card="#171A22", sidebar="#0A0C11",
        sidebar2="#171B24", text="#F5F7FA", muted="#98A2B3",
        success="#22C55E", warning="#F59E0B", danger="#EF4444", border="#262B33",
    ),
    "Growth Green": dict(
        primary="#16A34A", bg="#0A0F0C", card="#131C16", sidebar="#070B08",
        sidebar2="#101A14", text="#F1F5F9", muted="#9CA8A1",
        success="#22C55E", warning="#D97706", danger="#EF4444", border="#223028",
    ),
    "Premium Purple": dict(
        primary="#7C3AED", bg="#0C0A0F", card="#17141C", sidebar="#0A080D",
        sidebar2="#1C1826", text="#F5F3F7", muted="#A79FB0",
        success="#22C55E", warning="#D97706", danger="#EF4444", border="#2A2433",
    ),
    "Minimal Light": dict(
        primary="#2563EB", bg="#F8FAFC", card="#FFFFFF", sidebar="#F1F5F9",
        sidebar2="#E9EEF5", text="#0F172A", muted="#64748B",
        success="#16A34A", warning="#D97706", danger="#DC2626", border="#E2E8F0",
    ),
    "Commerce": dict(
        primary="#EA580C", bg="#0B0D12", card="#151A22", sidebar="#0A0C11",
        sidebar2="#171B24", text="#F5F1EA", muted="#A6A196",
        success="#22C55E", warning="#F59E0B", danger="#EF4444", border="#262B33",
    ),
}

_theme_name = st.session_state.get("_theme_name", "Nova Blue")
_theme_vars = dict(THEME_PRESETS.get(_theme_name, THEME_PRESETS["Nova Blue"]))
if _theme_name == "Custom":
    # Live preview: read straight from each color-picker's own widget state
    # (set the instant the user picks a color, before this rerun even
    # starts) rather than waiting for an explicit "Apply" click — so moving
    # any picker updates the whole dashboard immediately.
    _cd = THEME_PRESETS["Nova Blue"]
    _c_primary = st.session_state.get("_tc_primary", _cd["primary"])
    _c_bg      = st.session_state.get("_tc_bg", _cd["bg"])
    _c_card    = st.session_state.get("_tc_card", _cd["card"])
    _c_sidebar = st.session_state.get("_tc_sidebar", _cd["sidebar"])
    _c_text    = st.session_state.get("_tc_text", _cd["text"])
    _c_muted   = st.session_state.get("_tc_muted", _cd["muted"])
    _c_success = st.session_state.get("_tc_success", _cd["success"])
    _c_warning = st.session_state.get("_tc_warning", _cd["warning"])
    _c_danger  = st.session_state.get("_tc_danger", _cd["danger"])
    _theme_vars.update(dict(
        primary=_c_primary, bg=_c_bg, card=_c_card, sidebar=_c_sidebar,
        text=_c_text, muted=_c_muted, success=_c_success, warning=_c_warning, danger=_c_danger,
        border=_hex_to_rgba(_c_muted, .3), sidebar2=_lighten_hex(_c_sidebar, 12),
    ))

st.markdown(f"""
<style>
/* Theme override injected by "Customize Dashboard" (sidebar). Targets the
   same :root selector as the base stylesheet above with equal specificity —
   coming later in source order, it wins for exactly these variables and
   nothing else. No existing selector/class is modified. */
:root {{
  --nova-ink: {_theme_vars['text']};
  --nova-ink-soft: {_theme_vars['muted']};
  --nova-muted: {_theme_vars['muted']};
  --nova-border: {_theme_vars['border']};
  --nova-bg: {_theme_vars['bg']};
  --nova-card: {_theme_vars['card']};
  --nova-blue: {_theme_vars['primary']};
  --nova-blue-tint: {_hex_to_rgba(_theme_vars['primary'], .14)};
  --nova-green: {_theme_vars['success']};
  --nova-green-tint: {_hex_to_rgba(_theme_vars['success'], .14)};
  --nova-red: {_theme_vars['danger']};
  --nova-red-tint: {_hex_to_rgba(_theme_vars['danger'], .14)};
  --nova-amber: {_theme_vars['warning']};
  --nova-amber-tint: {_hex_to_rgba(_theme_vars['warning'], .14)};
  --nova-sidebar: {_theme_vars['sidebar']};
  --nova-sidebar-2: {_theme_vars['sidebar2']};
}}
</style>
""", unsafe_allow_html=True)


_LEGEND_DEFAULT = dict(bgcolor="rgba(0,0,0,0)", font=dict(size=10))
PLOTLY_BASE = {k: v for k, v in PLOTLY_LAYOUT.items()
               if k not in ("xaxis", "yaxis", "legend")}

UNIT_ECON = dict(cogs=0.52, rider=0.12, packaging=0.03, gateway=0.02, promos=0.05)
DELIVERY_PARAMS = dict(mean=11.5, std=3.5, lo=5, hi=35, promise=10)

# City name standardization — merges aliases that represent the same city
# so "Bangalore" and "Bengaluru" (etc.) never get double-counted.
CITY_ALIASES = {
    "bengaluru": "Bangalore",
    "bangalore": "Bangalore",
    "bombay":    "Mumbai",
    "mumbai":    "Mumbai",
    "delhi":     "Delhi",
    "new delhi": "Delhi",
    "calcutta":  "Kolkata",
    "kolkata":   "Kolkata",
    "madras":    "Chennai",
    "chennai":   "Chennai",
    "hyderabad": "Hyderabad",
    "pune":      "Pune",
}

# ══════════════════════════════════════════════════════════════════════════════════
# ── UTILITY / FORMATTING
# ══════════════════════════════════════════════════════════════════════════════════

def fmt(n: float) -> str:
    if pd.isna(n):  return "—"
    if n >= 1e7:    return f"₹{n/1e7:.1f}Cr"
    if n >= 1e5:    return f"₹{n/1e5:.2f}L"
    if n >= 1e3:    return f"₹{n/1e3:.1f}K"
    return f"₹{int(n):,}"


def pct_change_label(current: float, previous: float) -> tuple[str, bool]:
    if previous == 0:
        return "+0.0%", True
    chg = (current - previous) / abs(previous) * 100
    arrow = "↑" if chg >= 0 else "↓"
    return f"{arrow} {abs(chg):.1f}% WoW", chg >= 0


# ══════════════════════════════════════════════════════════════════════════════════
# ── DATA LOADING & CLEANING
# ══════════════════════════════════════════════════════════════════════════════════

_FALLBACK_CSV = """Product Name,Category,City,Original Price,Current Price,Discount,Orders,Total Revenue,Influencer Active
Britannia Cake,Snacks,Delhi,148,163,5,283,44714,No
Britannia Cake,Snacks,Pune,81,86,10,284,21584,Yes
Fortune Oil 1L,Grocery,Hyderabad,138,143,10,69,9177,No
Pepsi 500ml,Beverages,Delhi,127,127,10,83,9711,No
Aashirvaad Atta,Grocery,Chennai,34,49,10,169,6591,Yes
Amul Milk 500ml,Dairy,Delhi,149,159,0,246,39114,No
Britannia Cake,Snacks,Bangalore,82,87,0,254,22098,Yes
Amul Milk 500ml,Dairy,Bangalore,46,51,5,179,8234,No
Aashirvaad Atta,Grocery,Mumbai,137,137,10,268,34036,No
Maggi Noodles,Instant Food,Hyderabad,196,201,0,59,11859,Yes
Coca Cola 1L,Beverages,Delhi,140,140,10,269,34970,No
Oreo Biscuits,Snacks,Delhi,188,203,10,279,53847,No
Parle-G,Snacks,Chennai,96,101,0,299,30199,No
Nestle Munch,Confectionery,Mumbai,195,205,0,223,45715,No
Pepsi 500ml,Beverages,Hyderabad,154,159,5,253,38962,No
Amul Milk 500ml,Dairy,Pune,120,135,0,291,39285,Yes
Parle-G,Snacks,Bangalore,139,144,0,253,36432,Yes
Fortune Oil 1L,Grocery,Bangalore,143,153,0,299,45747,Yes
Coca Cola 1L,Beverages,Hyderabad,177,187,5,299,54418,No
Amul Milk 500ml,Dairy,Chennai,199,204,0,269,54876,No
Maggi Noodles,Instant Food,Hyderabad,182,197,0,294,57918,No
Nestle Munch,Confectionery,Bangalore,191,206,10,297,58212,No
Coca Cola 1L,Beverages,Delhi,175,190,5,288,53280,Yes
Oreo Biscuits,Snacks,Delhi,171,176,10,291,48306,No
Britannia Cake,Snacks,Mumbai,177,192,0,253,48576,No
Parle-G,Snacks,Delhi,184,194,0,271,52574,Yes
Amul Milk 500ml,Dairy,Pune,169,184,10,267,46458,No
Fortune Oil 1L,Grocery,Bangalore,143,153,0,299,45747,Yes
Nestle Munch,Confectionery,Mumbai,195,205,0,223,45715,No
Britannia Cake,Snacks,Delhi,148,163,5,283,44714,No"""

_NUMERIC_COLS = ["Original Price", "Current Price", "Discount", "Orders", "Total Revenue"]
_PRICE_BINS   = [0, 60, 100, 140, 180, np.inf]
_PRICE_LABELS = ["₹20–60", "₹61–100", "₹101–140", "₹141–180", "₹181+"]

REQUIRED_COLUMNS = [
    "Product Name", "Category", "City",
    "Original Price", "Current Price", "Discount",
    "Orders", "Total Revenue",
]

# Optional columns the Delivery Analytics / Operations pages will use
# *if* they exist in the uploaded file. Nothing here is invented.
OPTIONAL_DELIVERY_COLS = [
    "Order ID", "Delivery Partner", "Delivery Time", "Pickup Time",
    "Packing Time", "Rider Waiting Time", "Distance", "Delivery Cost",
    "Delay Reason", "SLA Target", "SLA Achieved", "Customer Rating",
]
OPTIONAL_OPERATIONS_COLS = [
    "Order Processing Time", "Picking Time", "Packing Time", "Store",
]


def standardize_cities(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """
    Merge known city-name aliases (e.g. Bangalore/Bengaluru) into one
    canonical name so they don't get double-counted as separate cities.
    Returns (df, mapping_applied) where mapping_applied only contains
    aliases that were actually present and changed.
    """
    if "City" not in df.columns:
        return df, {}
    applied = {}
    def _map(city):
        key = str(city).strip().lower()
        canonical = CITY_ALIASES.get(key)
        if canonical and canonical != city:
            applied[city] = canonical
            return canonical
        return city
    df = df.copy()
    df["City"] = df["City"].apply(_map)
    return df, applied


def clean(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize, impute, standardize cities, and engineer features on a raw DataFrame."""
    df = df.copy()
    df.columns = [c.strip() for c in df.columns]
    df.dropna(how="all", inplace=True)

    for col in _NUMERIC_COLS:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    num_cols = df.select_dtypes(include="number").columns
    df[num_cols] = df[num_cols].fillna(df[num_cols].median())
    for col in df.select_dtypes(include="object").columns:
        df[col] = df[col].fillna(df[col].mode()[0]).str.strip()

    df, city_map = standardize_cities(df)
    st.session_state["_city_standardization"] = city_map

    df["Profit"]        = (df["Current Price"] - df["Original Price"]) * df["Orders"]
    df["Profit Margin"] = np.where(
        df["Total Revenue"] > 0,
        df["Profit"] / df["Total Revenue"] * 100,
        0,
    )
    df["Price Tier"] = pd.cut(
        df["Current Price"], bins=_PRICE_BINS, labels=_PRICE_LABELS
    )
    return df


@st.cache_data
def load_default() -> pd.DataFrame:
    path = os.path.join(os.path.dirname(__file__), "..", "data", "zepto_sales_dataset.csv")
    if os.path.exists(path):
        return clean(pd.read_csv(path))
    return clean(pd.read_csv(io.StringIO(_FALLBACK_CSV)))


def _read_uploaded_dataframe(uploaded_file) -> pd.DataFrame:
    filename = uploaded_file.name.lower()

    if filename.endswith(".csv"):
        try:
            return pd.read_csv(uploaded_file)
        except Exception as e:
            raise ValueError(
                f"Couldn't parse **{uploaded_file.name}** as CSV. "
                f"Check that it's a valid comma-separated file. ({e})"
            )

    elif filename.endswith(".xlsx"):
        try:
            return pd.read_excel(uploaded_file, engine="openpyxl")
        except ImportError:
            raise ValueError(
                "Reading .xlsx files requires the `openpyxl` package. "
                "Install it with `pip install openpyxl` and retry."
            )
        except Exception as e:
            raise ValueError(
                f"Couldn't parse **{uploaded_file.name}** as an Excel file. "
                f"Make sure it's a valid, non-password-protected .xlsx workbook. ({e})"
            )
    else:
        raise ValueError(
            "Unsupported file type. Please upload a **.csv** or **.xlsx** file."
        )


def _validate_columns(df: pd.DataFrame, filename: str) -> None:
    df.columns = [str(c).strip() for c in df.columns]
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(
            f"**{filename}** is missing required column(s): "
            + ", ".join(f"`{m}`" for m in missing)
            + ". Expected columns: " + ", ".join(f"`{c}`" for c in REQUIRED_COLUMNS)
            + " (optional: `Influencer Active`)."
        )
    if df.dropna(how="all").empty:
        raise ValueError(f"**{filename}** was read successfully but contains no data rows.")


def load_user_file(uploaded_file) -> pd.DataFrame:
    raw_df = _read_uploaded_dataframe(uploaded_file)
    _validate_columns(raw_df, uploaded_file.name)
    return clean(raw_df)


def data_quality_report(df: pd.DataFrame) -> dict:
    """Compute data-trust indicators shown on the Data Explorer page."""
    missing_by_col = df.isna().sum()
    missing_by_col = missing_by_col[missing_by_col > 0].sort_values(ascending=False)
    dup_rows = int(df.duplicated().sum())
    return dict(
        total_rows    = len(df),
        total_cols    = len(df.columns),
        missing_total = int(df.isna().sum().sum()),
        missing_by_col= missing_by_col,
        dup_rows      = dup_rows,
        dtypes        = df.dtypes.astype(str),
        city_map      = st.session_state.get("_city_standardization", {}),
    )


# ══════════════════════════════════════════════════════════════════════════════════
# ── DATA IMPORT & TRUST CENTER — HELPERS
# (Additive only — none of the functions above/below this block are modified.
#  Nothing here silently changes user data; every fix is opt-in via the UI.)
# ══════════════════════════════════════════════════════════════════════════════════

import difflib
import re

# Aliases map onto the ACTUAL columns NovaMS's calculations depend on
# (REQUIRED_COLUMNS). Generic BI terms (Revenue, City, Product, Category,
# Quantity, etc.) are normalized to those exact names; nothing is renamed
# until the user confirms the import.
_COLUMN_ALIASES: dict[str, list[str]] = {
    "Product Name":   ["product", "item name", "item", "sku", "product title"],
    "Category":       ["product category", "segment", "item category", "type"],
    "City":           ["location", "region", "store city", "delivery city"],
    "Original Price": ["mrp", "list price", "base price", "actual price"],
    "Current Price":  ["selling price", "sale price", "final price", "price"],
    "Discount":       ["discount %", "discount percentage", "discount pct"],
    "Orders":         ["quantity", "units sold", "qty", "order count", "units"],
    "Total Revenue":  ["revenue", "sales", "amount", "sales amount", "gross revenue", "net sales"],
}


def _normalize_colname(s: str) -> str:
    return "".join(ch for ch in str(s).lower().strip() if ch.isalnum() or ch == " ").strip()


def suggest_column_mapping(raw_columns: list[str]) -> dict:
    """
    For each REQUIRED_COLUMNS name not already present verbatim, look for a
    raw column whose normalized name matches a known alias. Returns
    {raw_column_name: canonical_name} SUGGESTIONS ONLY — nothing is applied.
    """
    norm_raw = {_normalize_colname(c): c for c in raw_columns}
    suggestions = {}
    for canonical in REQUIRED_COLUMNS:
        if canonical in raw_columns:
            continue
        if _normalize_colname(canonical) in norm_raw:
            suggestions[norm_raw[_normalize_colname(canonical)]] = canonical
            continue
        for alias in _COLUMN_ALIASES.get(canonical, []):
            if alias in norm_raw:
                suggestions[norm_raw[alias]] = canonical
                break
    return suggestions


def dataset_compatibility_report(raw_df: pd.DataFrame, colmap: dict) -> dict:
    """
    Check whether raw_df (optionally with `colmap` renames applied on paper)
    can power NovaMS. All REQUIRED_COLUMNS are critical — every existing
    calculation (revenue, profit, margin, KPIs) depends on all 8 of them.
    Optional columns only unlock the Delivery/Operations pages' extra detail.
    """
    effective_cols = set(raw_df.columns) | set(colmap.values())
    required_detected = [c for c in REQUIRED_COLUMNS if c in effective_cols]
    required_missing  = [c for c in REQUIRED_COLUMNS if c not in effective_cols]
    optional_cols     = OPTIONAL_DELIVERY_COLS + OPTIONAL_OPERATIONS_COLS + ["Influencer Active"]
    optional_detected = [c for c in optional_cols if c in effective_cols]
    optional_missing  = [c for c in optional_cols if c not in effective_cols]
    return dict(
        required_detected=required_detected, required_missing=required_missing,
        optional_detected=optional_detected, optional_missing=optional_missing,
        can_import=len(required_missing) == 0,
    )


def compute_data_quality_findings(raw_df: pd.DataFrame) -> dict:
    """Inspect raw_df (pre-clean) and report concrete, evidence-backed issues."""
    findings = dict(
        missing_by_col={}, dup_rows=0, empty_cols=[], negative_or_zero={},
        city_aliases={}, similar_categories=[], total_rows=len(raw_df), total_cols=len(raw_df.columns),
    )
    if raw_df.empty:
        return findings

    missing = raw_df.isna().sum()
    findings["missing_by_col"] = {c: int(v) for c, v in missing[missing > 0].items()}
    findings["dup_rows"] = int(raw_df.duplicated().sum())
    findings["empty_cols"] = [c for c in raw_df.columns if raw_df[c].isna().all()]

    for col in ["Original Price", "Current Price", "Orders", "Total Revenue"]:
        if col in raw_df.columns:
            numeric = pd.to_numeric(raw_df[col], errors="coerce")
            bad = int(((numeric <= 0) | numeric.isna()).sum())
            if bad:
                findings["negative_or_zero"][col] = bad

    if "City" in raw_df.columns:
        for city in raw_df["City"].dropna().unique():
            canon = CITY_ALIASES.get(str(city).strip().lower())
            if canon and canon != city:
                findings["city_aliases"][city] = canon

    if "Category" in raw_df.columns:
        uniques = [str(c) for c in raw_df["Category"].dropna().unique()]
        seen = set()
        for c in uniques:
            if c in seen:
                continue
            close = [m for m in difflib.get_close_matches(c, uniques, n=4, cutoff=0.82) if m != c]
            if close:
                group = sorted(set([c] + close))
                seen.update(group)
                findings["similar_categories"].append(group)

    return findings


def compute_trust_score(raw_df: pd.DataFrame, findings: dict, compat: dict) -> dict:
    """
    Blend completeness / validity / consistency / uniqueness into one 0-100
    Data Trust Score, plus a plain-English explanation of the main issue.
    """
    n = max(1, findings["total_rows"] * max(1, findings["total_cols"]))
    completeness = 1 - (sum(findings["missing_by_col"].values()) / n)
    validity     = 1 - (sum(findings["negative_or_zero"].values()) / max(1, findings["total_rows"] * 4))
    consistency  = 1 - (0.08 * len(findings["city_aliases"]) + 0.08 * len(findings["similar_categories"]))
    uniqueness   = 1 - (findings["dup_rows"] / max(1, findings["total_rows"]))
    completeness_req = 1.0 if compat["can_import"] else 0.4

    weights = dict(completeness=.30, validity=.20, consistency=.15, uniqueness=.20, req=.15)
    raw_score = (
        completeness * weights["completeness"] + validity * weights["validity"] +
        consistency * weights["consistency"] + uniqueness * weights["uniqueness"] +
        completeness_req * weights["req"]
    )
    score = max(0, min(100, round(raw_score * 100)))

    if score >= 90:   status = "Excellent"
    elif score >= 75: status = "Good"
    elif score >= 50: status = "Needs Review"
    else:             status = "Poor Quality"

    issues = []
    if not compat["can_import"]:
        issues.append((3, f"Missing required column(s): {', '.join(compat['required_missing'])}"))
    if findings["dup_rows"]:
        issues.append((2, f"{findings['dup_rows']} duplicate row(s) detected"))
    if findings["missing_by_col"]:
        worst_col = max(findings["missing_by_col"], key=findings["missing_by_col"].get)
        pct = findings["missing_by_col"][worst_col] / max(1, findings["total_rows"]) * 100
        issues.append((2, f"{pct:.1f}% missing values in the {worst_col} column"))
    if findings["city_aliases"]:
        issues.append((1, f"Inconsistent city naming ({', '.join(findings['city_aliases'].keys())})"))
    if findings["similar_categories"]:
        issues.append((1, "Similar category spellings detected — likely duplicates"))
    if findings["negative_or_zero"]:
        col, cnt = next(iter(findings["negative_or_zero"].items()))
        issues.append((1, f"{cnt} row(s) with zero/negative values in {col}"))

    issues.sort(key=lambda x: -x[0])
    main_issue = issues[0][1] if issues else "No significant data quality issues detected."

    return dict(score=score, status=status, main_issue=main_issue,
                sub_scores=dict(completeness=completeness, validity=validity,
                                 consistency=consistency, uniqueness=uniqueness))


def generate_cleaning_suggestions(findings: dict, colmap: dict) -> list[dict]:
    """Build the opt-in list of recommended fixes shown with checkboxes in the UI."""
    suggestions = []
    if colmap:
        pretty = ", ".join(f"{k} → {v}" for k, v in colmap.items())
        suggestions.append(dict(id="colmap", label=f"Map detected columns ({pretty})",
                                 detail="Renames columns to the names NovaMS's calculations expect.", default=True))
    if findings["dup_rows"]:
        suggestions.append(dict(id="dupes", label=f"Remove {findings['dup_rows']} duplicate row(s)",
                                 detail="Exact duplicate rows will be dropped, keeping the first occurrence.", default=True))
    if findings["city_aliases"]:
        pretty = ", ".join(f"{k}→{v}" for k, v in findings["city_aliases"].items())
        suggestions.append(dict(id="city_std", label=f"Standardize city names ({pretty})",
                                 detail="Merges known aliases so they aren't double-counted as separate cities.", default=True))
    if findings["missing_by_col"]:
        cols = ", ".join(findings["missing_by_col"].keys())
        suggestions.append(dict(id="fill_missing", label=f"Fill missing values in: {cols}",
                                 detail="Numeric columns are filled with the column median; text columns with the most common value.", default=True))
    if findings["similar_categories"]:
        for group in findings["similar_categories"]:
            suggestions.append(dict(id=f"cat_std::{group[0]}", label=f"Merge similar categories: {', '.join(group)}",
                                     detail="Groups near-identical spellings under the most frequent variant.", default=False))
    return suggestions


def apply_cleaning_suggestions(raw_df: pd.DataFrame, selected_ids: set, colmap: dict, findings: dict) -> tuple[pd.DataFrame, list]:
    """Apply only the fixes the user explicitly checked. Returns (df, human-readable log)."""
    df = raw_df.copy()
    log = []

    if "colmap" in selected_ids and colmap:
        df = df.rename(columns=colmap)
        log.append(f"Mapped columns: {', '.join(f'{k}→{v}' for k, v in colmap.items())}")

    if "dupes" in selected_ids and findings["dup_rows"]:
        before = len(df)
        df = df.drop_duplicates()
        log.append(f"Removed {before - len(df)} duplicate row(s)")

    if "city_std" in selected_ids and "City" in df.columns:
        df, applied = standardize_cities(df)
        if applied:
            log.append("Standardized city names: " + ", ".join(f"{k}→{v}" for k, v in applied.items()))

    if "fill_missing" in selected_ids:
        num_cols = df.select_dtypes(include="number").columns
        if len(num_cols):
            df[num_cols] = df[num_cols].fillna(df[num_cols].median())
        for col in df.select_dtypes(include="object").columns:
            if df[col].isna().any() and not df[col].mode().empty:
                df[col] = df[col].fillna(df[col].mode()[0])
        log.append("Filled missing values (median for numeric, most-common for text)")

    for sid in selected_ids:
        if sid.startswith("cat_std::") and "Category" in df.columns:
            group_leader = sid.split("::", 1)[1]
            group = next((g for g in findings["similar_categories"] if g[0] == group_leader), None)
            if group:
                target = df[df["Category"].isin(group)]["Category"].mode()
                target = target.iloc[0] if not target.empty else group[0]
                df["Category"] = df["Category"].replace({g: target for g in group})
                log.append(f"Merged categories {group} → '{target}'")

    return df, log


def record_dataset_version(label: str, rows: int, note: str = ""):
    versions = st.session_state.setdefault("_dataset_versions", [])
    versions.append(dict(label=label, rows=rows, note=note))


# ══════════════════════════════════════════════════════════════════════════════════
# ── POSTGRESQL PERSISTENCE  (optional — app works identically if not configured)
# Datasets imported via the Data Import & Trust Center can be saved to a
# Postgres database so they survive a browser refresh / new session, instead
# of only living in st.session_state for the current visit.
# ══════════════════════════════════════════════════════════════════════════════════

_DB_TABLE = "novams_datasets"


def get_db_connection():
    """
    Returns a Streamlit SQL connection to the [connections.postgresql] entry
    in secrets.toml, or None if it isn't configured / reachable. Every
    caller must handle None — the rest of the app must keep working
    exactly as before when no database is set up.
    """
    try:
        return st.connection("postgresql", type="sql")
    except Exception:
        return None


def _ensure_db_schema(conn) -> bool:
    from sqlalchemy import text
    try:
        with conn.session as s:
            s.execute(text(f"""
                CREATE TABLE IF NOT EXISTS {_DB_TABLE} (
                    id SERIAL PRIMARY KEY,
                    name TEXT NOT NULL,
                    source TEXT NOT NULL,
                    rows INTEGER NOT NULL,
                    trust_score INTEGER,
                    status TEXT,
                    saved_at TIMESTAMP DEFAULT NOW(),
                    data_csv TEXT NOT NULL
                );
            """))
            s.commit()
        return True
    except Exception as e:
        st.session_state["_db_last_error"] = str(e)
        return False


def save_dataset_to_db(conn, df: pd.DataFrame, meta: dict) -> bool:
    """Persist df + its metadata as one row (CSV text) in Postgres."""
    from sqlalchemy import text
    if not _ensure_db_schema(conn):
        return False
    try:
        with conn.session as s:
            s.execute(
                text(f"""INSERT INTO {_DB_TABLE} (name, source, rows, trust_score, status, data_csv)
                         VALUES (:name, :source, :rows, :trust_score, :status, :data_csv)"""),
                dict(name=meta.get("name", "Untitled"), source=meta.get("source", "User Uploaded Dataset"),
                     rows=int(len(df)), trust_score=meta.get("trust_score"), status=meta.get("status"),
                     data_csv=df.to_csv(index=False)),
            )
            s.commit()
        return True
    except Exception as e:
        st.session_state["_db_last_error"] = str(e)
        return False


def list_saved_datasets(conn) -> pd.DataFrame:
    """Return the catalog of saved datasets (metadata only, not the data itself)."""
    if not _ensure_db_schema(conn):
        return pd.DataFrame()
    try:
        return conn.query(
            f"SELECT id, name, source, rows, trust_score, status, saved_at "
            f"FROM {_DB_TABLE} ORDER BY saved_at DESC;", ttl=0,
        )
    except Exception as e:
        st.session_state["_db_last_error"] = str(e)
        return pd.DataFrame()


def load_dataset_from_db(conn, dataset_id: int) -> pd.DataFrame | None:
    """Fetch one saved dataset's full data back out as a DataFrame."""
    try:
        result = conn.query(
            f"SELECT data_csv FROM {_DB_TABLE} WHERE id = :id;",
            params=dict(id=int(dataset_id)), ttl=0,
        )
        if result.empty:
            return None
        return pd.read_csv(io.StringIO(result.iloc[0]["data_csv"]))
    except Exception as e:
        st.session_state["_db_last_error"] = str(e)
        return None


def delete_dataset_from_db(conn, dataset_id: int) -> bool:
    from sqlalchemy import text
    try:
        with conn.session as s:
            s.execute(text(f"DELETE FROM {_DB_TABLE} WHERE id = :id;"), dict(id=int(dataset_id)))
            s.commit()
        return True
    except Exception as e:
        st.session_state["_db_last_error"] = str(e)
        return False


# ══════════════════════════════════════════════════════════════════════════════════
# ── CALCULATION FUNCTIONS  (pure — no Streamlit calls)
# ══════════════════════════════════════════════════════════════════════════════════

def compute_kpis(df: pd.DataFrame) -> dict:
    total_rev    = df["Total Revenue"].sum()
    total_profit = df["Profit"].sum()
    total_orders = df["Orders"].sum()
    margin       = (total_profit / total_rev * 100) if total_rev else 0
    rev_std      = df["Total Revenue"].std()

    cat_rev  = df.groupby("Category")["Total Revenue"].sum().sort_values(ascending=False)
    city_rev = df.groupby("City")["Total Revenue"].sum().sort_values(ascending=False)

    return dict(
        total_rev=total_rev, total_profit=total_profit, total_orders=total_orders,
        margin=margin, rev_std=rev_std, cat_rev=cat_rev, city_rev=city_rev,
        aov=total_rev / total_orders if total_orders else 0,
    )


def compute_influencer_stats(df: pd.DataFrame) -> dict:
    has_inf = "Influencer Active" in df.columns
    if not has_inf:
        return dict(available=False)
    grp_y = df[df["Influencer Active"] == "Yes"]
    grp_n = df[df["Influencer Active"] == "No"]
    rev_y = grp_y["Total Revenue"].mean() if len(grp_y) else 0
    rev_n = grp_n["Total Revenue"].mean() if len(grp_n) else 0
    rev_lift = ((rev_y - rev_n) / rev_n * 100) if rev_n > 0 else 0
    ord_y = grp_y["Orders"].mean() if len(grp_y) else 0
    ord_n = grp_n["Orders"].mean() if len(grp_n) else 0
    ord_lift = ((ord_y - ord_n) / ord_n * 100) if ord_n > 0 else 0
    _, p_inf = (
        stats.ttest_ind(grp_y["Total Revenue"], grp_n["Total Revenue"])
        if len(grp_y) > 1 and len(grp_n) > 1 else (0, 1)
    )
    return dict(
        available=True, rev_y=rev_y, rev_n=rev_n, rev_lift=rev_lift, ord_lift=ord_lift,
        p_value=p_inf, significant=p_inf < 0.05, count_y=len(grp_y), count_n=len(grp_n),
    )


def compute_statistics(df: pd.DataFrame) -> dict:
    rev_arr  = df["Total Revenue"].values
    z_scores = np.abs(stats.zscore(rev_arr))
    outlier_mask = z_scores > 2
    outliers     = df[outlier_mask].copy()
    outliers["Z-Score"] = z_scores[outlier_mask].round(2)
    _, p_norm    = stats.shapiro(rev_arr[:5000])
    r_disc, p_disc = stats.pearsonr(df["Discount"], df["Orders"])
    r_rev,  p_rev  = stats.pearsonr(df["Total Revenue"], df["Profit"])
    return dict(
        rev_arr=rev_arr, mean=np.mean(rev_arr), median=np.median(rev_arr), std=np.std(rev_arr),
        skewness=stats.skew(rev_arr), kurtosis=stats.kurtosis(rev_arr), p_norm=p_norm,
        is_normal=p_norm > 0.05, outliers=outliers, r_disc=r_disc, p_disc=p_disc,
        r_rev=r_rev, p_rev=p_rev,
        corr_matrix=df[["Original Price","Current Price","Discount","Orders","Total Revenue","Profit","Profit Margin"]].corr().round(3),
    )


def compute_forecast(df: pd.DataFrame) -> dict | None:
    prod_rev = df.groupby("Product Name")["Total Revenue"].sum().sort_values().values
    n = len(prod_rev)
    if n < 5:
        return None
    X = np.arange(1, n + 1).reshape(-1, 1)
    y = prod_rev.astype(float)
    model      = LinearRegression().fit(X, y)
    next_val   = max(0.0, float(model.predict([[n + 1]])[0]))
    r2         = model.score(X, y)
    residuals  = y - model.predict(X)
    ci         = 1.96 * float(np.std(residuals))
    mean_y     = float(np.mean(y))
    growth_pct = ((next_val - mean_y) / mean_y * 100) if mean_y else 0
    step = max(1, n // 20)
    xs   = list(range(1, n + 1, step)) + [n + 1]
    trend_vals   = [float(model.predict([[i]])[0]) for i in xs]
    actual_vals  = [float(prod_rev[i - 1]) if i <= n else None for i in xs]
    return dict(
        n=n, next_val=next_val, r2=r2, ci=ci, growth_pct=growth_pct, slope=float(model.coef_[0]),
        xs=xs, trend_vals=trend_vals, actual_vals=actual_vals,
        upper=[t + ci for t in trend_vals], lower=[max(0.0, t - ci) for t in trend_vals],
    )


def compute_delivery_stats(n_samples: int) -> dict:
    np.random.seed(42)
    p = DELIVERY_PARAMS
    times = np.clip(np.random.normal(p["mean"], p["std"], max(n_samples, 50)), p["lo"], p["hi"])
    otd_pct = float(np.mean(times <= p["promise"] + 2) * 100)
    avg     = float(np.mean(times))
    p90     = float(np.percentile(times, 90))
    p50     = float(np.percentile(times, 50))
    if otd_pct >= 95:
        status, status_color = "🟢 EXCELLENT",       "#10b981"
    elif otd_pct >= 85:
        status, status_color = "🟡 NEEDS ATTENTION", "#f59e0b"
    else:
        status, status_color = "🔴 CRITICAL",        "#ef4444"
    hist_counts, hist_edges = np.histogram(times, bins=12)
    hist_centers = [(hist_edges[i] + hist_edges[i + 1]) / 2 for i in range(len(hist_counts))]
    return dict(
        times=times, otd_pct=otd_pct, avg=avg, p90=p90, p50=p50, status=status,
        status_color=status_color, promise=p["promise"], hist_counts=hist_counts, hist_centers=hist_centers,
    )


def compute_unit_economics(avg_rev: float) -> dict:
    e = UNIT_ECON
    costs = {k: avg_rev * v for k, v in e.items()}
    net   = avg_rev - sum(costs.values())
    cm    = (net / avg_rev * 100) if avg_rev > 0 else 0
    return dict(avg_rev=avg_rev, net_profit=net, cm_pct=cm, **costs)


def compute_inventory(df: pd.DataFrame, top_n: int = 10) -> pd.DataFrame:
    np.random.seed(123)
    prod_velocity = df.groupby("Product Name")["Orders"].sum().sort_values(ascending=False)
    rows = []
    for prod, velocity in prod_velocity.head(top_n).items():
        stock_left  = int(np.random.randint(5, 200))
        daily_sales = max(1, int(velocity * 0.3))
        days_cover  = round(stock_left / daily_sales, 1)
        if days_cover < 1:
            risk, risk_color, action = "🔴 CRITICAL", "#ef4444", "⚡ ORDER NOW"
            bg, border = "rgba(239,68,68,.08)", "rgba(239,68,68,.3)"
        elif days_cover < 2:
            risk, risk_color, action = "🟡 LOW",      "#f59e0b", "📋 Plan Reorder"
            bg, border = "rgba(245,158,11,.08)", "rgba(245,158,11,.3)"
        else:
            risk, risk_color, action = "🟢 OK",       "#10b981", "✅ Sufficient"
            bg, border = "rgba(16,185,129,.06)",  "rgba(16,185,129,.2)"
        rows.append(dict(
            Product=prod, Stock_Left=stock_left, Daily_Sales=daily_sales, Days_Cover=days_cover,
            Risk=risk, Action=action, _color=risk_color, _bg=bg, _border=border,
        ))
    return pd.DataFrame(rows)


def compute_wow_metrics(kpis: dict, factor: float = 0.88) -> dict:
    prev = dict(
        total_rev=kpis["total_rev"] * factor,
        total_orders=int(kpis["total_orders"] * factor),
        total_profit=kpis["total_profit"] * factor,
        margin=kpis["margin"] * 0.95,
    )
    badges = {k: pct_change_label(kpis[k], prev[k]) for k in ["total_rev", "total_profit", "margin"]}
    badges["total_orders"] = pct_change_label(kpis["total_orders"], prev["total_orders"])
    return dict(current=kpis, previous=prev, badges=badges)


def compute_order_defects(total_orders: int) -> dict:
    expired       = int(total_orders * 0.018)
    missing       = int(total_orders * 0.024)
    cancelled_oos = int(total_orders * 0.031)
    total_defects = expired + missing + cancelled_oos
    perfect       = total_orders - total_defects
    odr_pct       = total_defects / total_orders * 100 if total_orders > 0 else 0
    return dict(
        total_orders=total_orders, expired=expired, missing=missing, cancelled_oos=cancelled_oos,
        total_defects=total_defects, perfect=perfect, odr_pct=odr_pct,
        funnel_y=[total_orders, total_orders-expired, total_orders-expired-missing,
                  total_orders-expired-missing-cancelled_oos, perfect],
        funnel_labels=["Total Orders","After Expired/Damaged","After Missing Items","After OOS Cancels","✅ Perfect Orders"],
    )


def compute_ai_insights(df: pd.DataFrame, kpis: dict, inf: dict) -> list[tuple]:
    cat_rev  = kpis["cat_rev"]
    city_rev = kpis["city_rev"]
    margin   = kpis["margin"]
    prod_rev = df.groupby("Product Name")["Total Revenue"].sum().sort_values(ascending=False)
    r_d, p_d = (stats.pearsonr(df["Discount"], df["Orders"]) if len(df) >= 5 else (0, 1))
    best_margin_cat = (
        df.groupby("Category")["Profit Margin"].mean().sort_values(ascending=False).index[0]
        if "Profit Margin" in df.columns and len(df) > 0 else "N/A"
    )
    city_gap_pct = (
        (city_rev.iloc[0] - city_rev.iloc[-1]) / city_rev.iloc[-1] * 100
        if len(city_rev) > 1 and city_rev.iloc[-1] > 0 else 0
    )
    return [
        ("🏆", "Best Category",
         f"<strong>{cat_rev.index[0]}</strong> drives {cat_rev.iloc[0]/cat_rev.sum()*100:.1f}% of total revenue "
         f"({fmt(cat_rev.iloc[0])}). Maximize marketing budget here for peak ROI."),
        ("🌍", "Regional Gap",
         f"<strong>{city_rev.index[0]}</strong> ({fmt(city_rev.iloc[0])}) outperforms "
         f"<strong>{city_rev.index[-1]}</strong> ({fmt(city_rev.iloc[-1])}) by {city_gap_pct:.0f}%. "
         f"Target promotions in underperforming regions."),
        ("⚡", "Influencer Lift",
         f"Influencer-active products generate <strong>{inf.get('rev_lift',0):+.1f}%</strong> more revenue. "
         f"{'Statistically significant ✓' if inf.get('significant') else 'Not yet significant'} "
         f"(p={inf.get('p_value', 1):.3f})."),
        ("📈", "Profit Margin",
         f"Overall margin is <strong>{margin:.1f}%</strong>. {best_margin_cat} has the highest avg margin."),
        ("💡", "Discount Intelligence",
         f"Discount is {'positively' if r_d > 0 else 'negatively'} correlated with orders "
         f"(r={r_d:.3f}, p={p_d:.3f}). {'Discounting drives volume.' if r_d > 0 else 'Review your discount strategy.'}"),
        ("🎯", "Top Product",
         f"<strong>{prod_rev.index[0]}</strong> generates {fmt(prod_rev.iloc[0])} — the highest single-product revenue. "
         f"Expand distribution and pair with influencer activation."),
    ]


def compute_executive_summary(df: pd.DataFrame, kpis: dict) -> str:
    """
    One compact, auto-generated paragraph for the top of the Executive
    Overview page — biggest positive/negative signal, best region/category/
    product, and the single most useful recommendation. Built entirely from
    kpis/df that are already computed elsewhere; nothing here is invented.
    """
    cat_rev  = kpis["cat_rev"]
    city_rev = kpis["city_rev"]
    if cat_rev is None or city_rev is None or len(cat_rev) == 0 or len(city_rev) == 0:
        return "Not enough data in the current filter to generate a summary."

    prod_rev = df.groupby("Product Name")["Total Revenue"].sum().sort_values(ascending=False)
    top_prod = prod_rev.index[0] if len(prod_rev) else "N/A"
    best_cat, best_city, weak_city = cat_rev.index[0], city_rev.index[0], city_rev.index[-1]
    gap_pct = ((city_rev.iloc[0] - city_rev.iloc[-1]) / city_rev.iloc[-1] * 100
               if len(city_rev) > 1 and city_rev.iloc[-1] > 0 else 0)

    return (
        f"Revenue totals <b>{fmt(kpis['total_rev'])}</b> at a <b>{kpis['margin']:.1f}%</b> margin, "
        f"led by <b>{best_cat}</b> in <b>{best_city}</b> and anchored by <b>{top_prod}</b> as the top "
        f"single product. <b>{weak_city}</b> trails the leading region by <b>{gap_pct:.0f}%</b> — the "
        f"clearest opportunity for targeted promotions right now."
    )


def detect_top_anomaly(df: pd.DataFrame, z_threshold: float = 3.0) -> dict | None:
    """
    Lightweight anomaly flag for the Executive Overview: the single most
    extreme Total Revenue row (by z-score) in the current filtered view,
    only surfaced when it's a genuinely strong outlier (|z| >= z_threshold).
    Reuses the same z-score approach as the Sales Analytics outlier
    detector — no new statistical method is introduced.
    """
    if len(df) < 5:
        return None
    z = np.abs(stats.zscore(df["Total Revenue"]))
    if z.max() < z_threshold:
        return None
    idx = int(np.argmax(z))
    row = df.iloc[idx]
    direction = "spike" if row["Total Revenue"] > df["Total Revenue"].mean() else "drop"
    return dict(
        product=row["Product Name"], city=row["City"], category=row["Category"],
        revenue=float(row["Total Revenue"]), z=float(z[idx]), direction=direction,
    )


# ══════════════════════════════════════════════════════════════════════════════════
# ── BLINKBOT — MULTI-TURN MEMORY & RICH RESPONSE FORMATTING
# ══════════════════════════════════════════════════════════════════════════════════

class ConversationMemory:
    def __init__(self):
        self.last_intent   : str | None = None
        self.last_city     : str | None = None
        self.last_product  : str | None = None
        self.last_category : str | None = None
        self.turn_count    : int        = 0
        self.intent_stack  : list[str]  = []

    def update(self, intent: str, city=None, product=None, category=None):
        self.last_intent = intent
        if city:     self.last_city     = city
        if product:  self.last_product  = product
        if category: self.last_category = category
        self.turn_count += 1
        self.intent_stack = (self.intent_stack + [intent])[-3:]

    def to_dict(self) -> dict:
        return {k: v for k, v in self.__dict__.items()}

    @classmethod
    def from_dict(cls, d: dict) -> "ConversationMemory":
        m = cls()
        for k, v in d.items():
            setattr(m, k, v)
        return m


def _get_memory() -> ConversationMemory:
    if "bb_memory" not in st.session_state:
        st.session_state.bb_memory = ConversationMemory().to_dict()
    return ConversationMemory.from_dict(st.session_state.bb_memory)


def _save_memory(mem: ConversationMemory):
    st.session_state.bb_memory = mem.to_dict()


def extract_entities(question: str, df: pd.DataFrame) -> dict:
    q_low = question.lower()
    found = dict(city=None, product=None, category=None)
    for city in df["City"].unique():
        if city.lower() in q_low:
            found["city"] = city
            break
    for cat in df["Category"].unique():
        if cat.lower() in q_low:
            found["category"] = cat
            break
    for prod in df["Product Name"].unique():
        if prod.lower() in q_low:
            found["product"] = prod
            break
    return found


# Bare follow-ups like "why" / "why is that" are handled by a dedicated
# _bb_why handler (which has full access to ConversationMemory), so
# resolve_references no longer rewrites them into a generic re-ask —
# that used to just re-trigger the same handler instead of explaining.
_WHY_PHRASES = {"why", "why?", "why is that", "why is that so", "how come", "why so"}


def _replace_word(q: str, word: str, replacement: str) -> str:
    """Word-boundary-safe replace — used instead of str.replace() for short
    pronoun references so e.g. replacing 'it' doesn't corrupt 'profit'."""
    return re.sub(rf"\b{re.escape(word)}\b", replacement, q)


def resolve_references(question: str, mem: ConversationMemory) -> str:
    q = question.lower().strip()
    if q in _WHY_PHRASES:
        return q  # let _bb_why handle it directly, with full memory context

    city_refs = ["that city", "that region", "that location", "there", "that place"]
    if any(_kw_hit(q, ref) for ref in city_refs) and mem.last_city:
        for ref in city_refs:
            q = _replace_word(q, ref, mem.last_city)
    prod_refs = ["that product", "that item", "the same product", "that one", "it"]
    if any(_kw_hit(q, ref) for ref in prod_refs) and mem.last_product:
        for ref in prod_refs:
            q = _replace_word(q, ref, mem.last_product)
    cat_refs = ["that category", "that segment", "that section"]
    if any(_kw_hit(q, ref) for ref in cat_refs) and mem.last_category:
        for ref in cat_refs:
            q = _replace_word(q, ref, mem.last_category)
    more_refs = ["tell me more", "more details", "expand", "elaborate", "explain more", "go deeper",
                 "explain in detail", "detailed analysis", "give me a detailed analysis",
                 "explain simply", "in simple terms", "simple words"]
    if any(_kw_hit(q, ref) for ref in more_refs) and mem.last_intent:
        q = mem.last_intent
    return q


def _kw_hit(q: str, keyword: str) -> bool:
    """Substring match for multi-word phrases (safe — phrases can't accidentally
    appear inside unrelated words), word-boundary match for single words
    (prevents e.g. 'hi' matching inside 'which'/'this'/'Delhi'/'highest')."""
    if " " in keyword:
        return keyword in q
    return re.search(rf"\b{re.escape(keyword)}\b", q) is not None


def _any_kw(q: str, keywords: list[str]) -> bool:
    return any(_kw_hit(q, k) for k in keywords)


def _detect_detail_level(question: str) -> str:
    """Returns 'detailed', 'simple', or 'normal' based on phrasing in the raw question."""
    q = question.lower()
    if any(p in q for p in ["explain in detail", "detailed analysis", "in detail", "deep dive",
                             "more detail", "give me a detailed", "elaborate"]):
        return "detailed"
    if any(p in q for p in ["explain simply", "in simple terms", "simple words", "eli5",
                             "like i'm five", "keep it simple"]):
        return "simple"
    return "normal"


class ResponseBuilder:
    def __init__(self, emoji: str, title: str):
        self._emoji   = emoji
        self._title   = title
        self._answer  : str        = ""
        self._metrics : list[tuple]= []
        self._context : str        = ""
        self._tip     : str        = ""
        self._followup: str        = ""

    def answer(self, text: str) -> "ResponseBuilder":
        self._answer = text
        return self

    def metric(self, label: str, value: str, icon: str = "▸") -> "ResponseBuilder":
        self._metrics.append((label, value, icon))
        return self

    def context(self, text: str) -> "ResponseBuilder":
        self._context = text
        return self

    def tip(self, text: str) -> "ResponseBuilder":
        self._tip = text
        return self

    def followup(self, text: str) -> "ResponseBuilder":
        self._followup = text
        return self

    def build(self) -> str:
        parts = [f"**{self._emoji} {self._title}**\n"]
        if self._answer:
            parts.append(self._answer + "\n")
        if self._metrics:
            parts.append("")
            for label, value, icon in self._metrics:
                parts.append(f"{icon} **{label}:** {value}")
        if self._context:
            parts.append(f"\n💬 *{self._context}*")
        if self._tip:
            parts.append(f"\n💡 **Recommendation:** {self._tip}")
        if self._followup:
            parts.append(f"\n🔍 *You can also ask: {self._followup}*")
        return "\n".join(parts)


def _bb_context(df: pd.DataFrame) -> dict:
    """
    Precomputed aggregates every handler shares. Cheap groupbys only —
    heavier analysis (stats/trust/forecast/delivery) is computed lazily,
    only by the specific handlers that need it, to keep BlinkBot fast.

    NOTE: every key that existed before this upgrade is still present with
    the same meaning (total_r, total_o, total_p, mgn, cat_r, city_r, prod_r,
    best_m, inf_y_rev, inf_n_rev, inf_lift, ord_lift, disc_grp, n_inf_y) —
    chart factories and the LLM system prompt builder both depend on these
    exact keys and are unchanged.
    """
    total_r  = df["Total Revenue"].sum()
    total_o  = df["Orders"].sum()
    total_p  = df["Profit"].sum()
    mgn      = (total_p / total_r * 100) if total_r > 0 else 0
    cat_r    = df.groupby("Category")["Total Revenue"].sum().sort_values(ascending=False) if "Category"     in df.columns else None
    city_r   = df.groupby("City")["Total Revenue"].sum().sort_values(ascending=False)     if "City"         in df.columns else None
    prod_r   = df.groupby("Product Name")["Total Revenue"].sum().sort_values(ascending=False) if "Product Name" in df.columns else None
    best_m   = df.groupby("Category")["Profit Margin"].mean().sort_values(ascending=False) if "Profit Margin" in df.columns else None
    inf_y_rev= df[df["Influencer Active"]=="Yes"]["Total Revenue"].mean() if "Influencer Active" in df.columns else 0
    inf_n_rev= df[df["Influencer Active"]=="No"]["Total Revenue"].mean()  if "Influencer Active" in df.columns else 0
    inf_lift = ((inf_y_rev - inf_n_rev) / inf_n_rev * 100) if inf_n_rev > 0 else 0
    inf_y_ord= df[df["Influencer Active"]=="Yes"]["Orders"].mean() if "Influencer Active" in df.columns else 0
    inf_n_ord= df[df["Influencer Active"]=="No"]["Orders"].mean()  if "Influencer Active" in df.columns else 0
    ord_lift = ((inf_y_ord - inf_n_ord) / inf_n_ord * 100) if inf_n_ord > 0 else 0
    disc_grp = df.groupby("Discount").agg(avg_rev=("Total Revenue","mean"), avg_orders=("Orders","mean")).reset_index() if "Discount" in df.columns else None

    # --- Additive context (new, cheap aggregates for the upgraded BlinkBot) ---
    city_ord    = df.groupby("City")["Orders"].sum().sort_values(ascending=False) if "City" in df.columns else None
    cat_ord     = df.groupby("Category")["Orders"].sum().sort_values(ascending=False) if "Category" in df.columns else None
    prod_profit = df.groupby("Product Name")["Profit"].sum().sort_values(ascending=False) if "Product Name" in df.columns else None
    cat_profit  = df.groupby("Category")["Profit"].sum().sort_values(ascending=False) if "Category" in df.columns else None
    city_profit = df.groupby("City")["Profit"].sum().sort_values(ascending=False) if "City" in df.columns else None
    city_margin = df.groupby("City")["Profit Margin"].mean().sort_values(ascending=False) if "Profit Margin" in df.columns and "City" in df.columns else None
    city_disc   = df.groupby("City")["Discount"].mean() if "Discount" in df.columns and "City" in df.columns else None
    cat_disc    = df.groupby("Category")["Discount"].mean() if "Discount" in df.columns and "Category" in df.columns else None
    aov         = total_r / total_o if total_o else 0

    return dict(total_r=total_r, total_o=total_o, total_p=total_p, mgn=mgn,
                cat_r=cat_r, city_r=city_r, prod_r=prod_r, best_m=best_m,
                inf_y_rev=inf_y_rev, inf_n_rev=inf_n_rev, inf_lift=inf_lift,
                ord_lift=ord_lift, disc_grp=disc_grp,
                n_inf_y=len(df[df["Influencer Active"]=="Yes"]) if "Influencer Active" in df.columns else 0,
                city_ord=city_ord, cat_ord=cat_ord, prod_profit=prod_profit,
                cat_profit=cat_profit, city_profit=city_profit, city_margin=city_margin,
                city_disc=city_disc, cat_disc=cat_disc, aov=aov,
                n_products=df["Product Name"].nunique() if "Product Name" in df.columns else 0,
                n_cities=df["City"].nunique() if "City" in df.columns else 0,
                n_categories=df["Category"].nunique() if "Category" in df.columns else 0)


# ── Chart Factories — used by BlinkBot + Sales/Delivery/etc pages ───────────────

def _chart_revenue_by_category(ctx: dict) -> go.Figure:
    cat_r = ctx["cat_r"]
    total = cat_r.sum()
    pct = (cat_r / total * 100) if total else cat_r * 0
    avg = cat_r.mean()
    fig = go.Figure(go.Bar(
        x=cat_r.index.tolist(), y=cat_r.values,
        marker_color=[CAT_CLR.get(c, "#6366f1") for c in cat_r.index],
        marker_line_width=0, opacity=0.85,
        text=[fmt(v) for v in cat_r.values], textposition="outside",
        textfont=dict(color="#F1F5F9", size=10),
        customdata=pct.values,
        hovertemplate="<b>%{x}</b><br>Revenue: ₹%{y:,.0f}<br>Share of total: %{customdata:.1f}%<extra></extra>",
    ))
    fig.add_hline(y=avg, line_dash="dot", line_color="rgba(255,255,255,.35)", line_width=1,
                  annotation_text="avg", annotation_font=dict(size=9, color="#9AA4B2"), annotation_position="right")
    fig.update_layout(**PLOTLY_BASE,
        title=dict(text="💬 Revenue by Category", font=dict(color="#1D4DFF", size=12)),
        height=240, yaxis=dict(tickprefix="₹", **_AXIS_DEFAULTS), showlegend=False)
    return fig


def _chart_city_ranking(ctx: dict) -> go.Figure:
    cr = ctx["city_r"]
    total = cr.sum()
    pct = (cr / total * 100) if total else cr * 0
    avg = cr.mean()
    colors = ["#10b981" if i == 0 else "#ef4444" if i == len(cr)-1 else "#6366f1"
              for i in range(len(cr))]
    fig = go.Figure(go.Bar(
        x=cr.values, y=cr.index.tolist(), orientation="h",
        marker_color=colors, marker_line_width=0, opacity=0.85,
        text=[fmt(v) for v in cr.values], textposition="outside",
        textfont=dict(color="#F1F5F9", size=10),
        customdata=pct.values,
        hovertemplate="<b>%{y}</b><br>Revenue: ₹%{x:,.0f}<br>Share of total: %{customdata:.1f}%<extra></extra>",
    ))
    fig.add_vline(x=avg, line_dash="dot", line_color="rgba(255,255,255,.35)", line_width=1,
                  annotation_text="avg", annotation_font=dict(size=9, color="#9AA4B2"), annotation_position="top")
    fig.update_layout(**PLOTLY_BASE,
        title=dict(text="💬 City Revenue Ranking", font=dict(color="#1D4DFF", size=12)),
        height=240, xaxis=dict(tickprefix="₹", **_AXIS_DEFAULTS),
        yaxis=dict(autorange="reversed", **_AXIS_DEFAULTS), showlegend=False)
    return fig


def _chart_top_products(ctx: dict, n: int = 8) -> go.Figure:
    pr = ctx["prod_r"].head(n)
    total = ctx["prod_r"].sum()
    pct = (pr / total * 100) if total else pr * 0
    fig = go.Figure(go.Bar(
        x=pr.values, y=pr.index.tolist(), orientation="h",
        marker=dict(color=pr.values, colorscale=[[0,"#312e81"],[0.5,"#6366f1"],[1,"#06b6d4"]], showscale=False),
        marker_line_width=0,
        text=[fmt(v) for v in pr.values], textposition="outside",
        textfont=dict(color="#F1F5F9", size=10),
        customdata=pct.values,
        hovertemplate="<b>%{y}</b><br>Revenue: ₹%{x:,.0f}<br>Share of total: %{customdata:.1f}%<extra></extra>",
    ))
    fig.update_layout(**PLOTLY_BASE,
        title=dict(text=f"💬 Top {n} Products by Revenue", font=dict(color="#1D4DFF", size=12)),
        height=260, xaxis=dict(tickprefix="₹", **_AXIS_DEFAULTS),
        yaxis=dict(autorange="reversed", **_AXIS_DEFAULTS), showlegend=False)
    return fig


def _chart_influencer_lift(ctx: dict, df: pd.DataFrame) -> go.Figure:
    grp = df.groupby(["Category","Influencer Active"])["Total Revenue"].mean().reset_index()
    grp.columns = ["Category","Influencer","Avg Revenue"]
    fig = px.bar(grp, x="Category", y="Avg Revenue", color="Influencer",
                 barmode="group", color_discrete_map={"Yes":"#6366f1","No":"#64748B"})
    fig.update_layout(**PLOTLY_BASE,
        title=dict(text="💬 Influencer Lift by Category", font=dict(color="#1D4DFF", size=12)),
        height=240, yaxis=dict(tickprefix="₹", **_AXIS_DEFAULTS))
    fig.update_traces(marker_line_width=0, opacity=0.85)
    return fig


def _chart_discount_curve(ctx: dict) -> go.Figure:
    dg = ctx["disc_grp"]
    if dg is None: return None
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(go.Bar(
        x=dg["Discount"].astype(str)+"%", y=dg["avg_rev"],
        name="Avg Revenue", marker_color="#6366f1", opacity=0.85, marker_line_width=0,
    ), secondary_y=False)
    fig.add_trace(go.Scatter(
        x=dg["Discount"].astype(str)+"%", y=dg["avg_orders"],
        name="Avg Orders", mode="lines+markers+text",
        text=[f"{v:.0f}" for v in dg["avg_orders"]],
        textposition="top center", textfont=dict(color="#06b6d4", size=9),
        line=dict(color="#06b6d4", width=2), marker=dict(size=7),
    ), secondary_y=True)
    fig.update_layout(**PLOTLY_BASE,
        title=dict(text="💬 Discount Sweet Spot", font=dict(color="#1D4DFF", size=12)),
        height=240)
    fig.update_yaxes(tickprefix="₹", secondary_y=False)
    return fig


def _chart_profit_margin_by_category(ctx: dict, df: pd.DataFrame) -> go.Figure:
    bm = ctx["best_m"]
    if bm is None: return None
    colors = ["#10b981" if v >= 0 else "#ef4444" for v in bm.values]
    fig = go.Figure(go.Bar(
        x=bm.index.tolist(), y=bm.values,
        marker_color=colors, marker_line_width=0, opacity=0.85,
        text=[f"{v:.1f}%" for v in bm.values], textposition="outside",
        textfont=dict(color="#F1F5F9", size=10),
    ))
    fig.update_layout(**PLOTLY_BASE,
        title=dict(text="💬 Avg Profit Margin by Category", font=dict(color="#1D4DFF", size=12)),
        height=240, yaxis=dict(ticksuffix="%", **_AXIS_DEFAULTS), showlegend=False)
    return fig


def _chart_orders_by_city(df: pd.DataFrame) -> go.Figure:
    city_ord = df.groupby("City")["Orders"].sum().sort_values(ascending=False)
    fig = go.Figure(go.Bar(
        x=city_ord.index.tolist(), y=city_ord.values,
        marker_color=[CITY_CLR.get(c,"#6366f1") for c in city_ord.index],
        marker_line_width=0, opacity=0.85,
        text=city_ord.values, textposition="outside",
        textfont=dict(color="#F1F5F9", size=10),
    ))
    fig.update_layout(**PLOTLY_LAYOUT,
        title=dict(text="💬 Orders by City", font=dict(color="#1D4DFF", size=12)),
        height=240, showlegend=False)
    return fig


def _chart_summary_snapshot(ctx: dict) -> go.Figure:
    cat_r  = ctx["cat_r"]
    city_r = ctx["city_r"]
    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=["Revenue by Category", "Revenue by City"],
        specs=[[{"type":"pie"}, {"type":"bar"}]],
    )
    fig.add_trace(go.Pie(
        labels=cat_r.index.tolist(), values=cat_r.values,
        marker_colors=[CAT_CLR.get(c,"#6366f1") for c in cat_r.index],
        hole=0.5, textinfo="label+percent", textfont_size=9, showlegend=False,
    ), row=1, col=1)
    fig.add_trace(go.Bar(
        x=city_r.index.tolist(), y=city_r.values,
        marker_color=[CITY_CLR.get(c,"#6366f1") for c in city_r.index],
        marker_line_width=0, opacity=0.85,
        text=[fmt(v) for v in city_r.values], textposition="outside",
        textfont=dict(color="#F1F5F9", size=9), showlegend=False,
    ), row=1, col=2)
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter", color="#9AA4B2", size=10),
        margin=dict(l=10, r=10, t=40, b=10), height=260,
        title=dict(text="💬 Snapshot", font=dict(color="#1D4DFF", size=12)),
    )
    fig.update_annotations(font_color="#9AA4B2", font_size=10)
    fig.update_yaxes(tickprefix="₹", gridcolor="rgba(255,255,255,.05)")
    return fig


def _fig_to_json(fig: go.Figure) -> str | None:
    if fig is None: return None
    return fig.to_json()


def _fig_from_json(s: str | None) -> go.Figure | None:
    if not s: return None
    return go.Figure(json.loads(s))


BotReply = tuple[str, "go.Figure | None"]


# ── Evidence helper — used by comparisons + "why" follow-ups so the reasoning
#    behind an answer is built from the same numbers every time, not restated
#    ad hoc in each handler. ───────────────────────────────────────────────

def _dimension_evidence(kind: str, name: str, ctx: dict, df: pd.DataFrame) -> list[str]:
    """Returns a short list of evidence bullet-strings explaining why `name`
    (a city/category/product) performs the way it does, vs the overall data."""
    bullets = []
    if kind == "city" and "City" in df.columns and name in df["City"].values:
        sub = df[df["City"] == name]
        rev = sub["Total Revenue"].sum()
        share = rev / ctx["total_r"] * 100 if ctx["total_r"] else 0
        bullets.append(f"{name} contributes {fmt(rev)} — {share:.1f}% of total revenue.")
        if ctx["cat_r"] is not None and len(sub):
            top_cat = sub.groupby("Category")["Total Revenue"].sum().idxmax()
            bullets.append(f"Its top category is **{top_cat}**.")
        if "Profit Margin" in sub.columns:
            local_margin = sub["Profit Margin"].mean()
            bullets.append(f"Average margin there is {local_margin:.1f}% vs {ctx['mgn']:.1f}% overall.")
        if "Discount" in sub.columns:
            bullets.append(f"Average discount there is {sub['Discount'].mean():.1f}%.")
        if "Influencer Active" in sub.columns and len(sub):
            inf_share = (sub["Influencer Active"] == "Yes").mean() * 100
            bullets.append(f"{inf_share:.0f}% of its orders are influencer-driven.")

    elif kind == "category" and "Category" in df.columns and name in df["Category"].values:
        sub = df[df["Category"] == name]
        rev = sub["Total Revenue"].sum()
        share = rev / ctx["total_r"] * 100 if ctx["total_r"] else 0
        bullets.append(f"{name} contributes {fmt(rev)} — {share:.1f}% of total revenue.")
        if ctx["city_r"] is not None and len(sub):
            top_city = sub.groupby("City")["Total Revenue"].sum().idxmax()
            bullets.append(f"Its strongest city is **{top_city}**.")
        if "Profit Margin" in sub.columns:
            local_margin = sub["Profit Margin"].mean()
            bullets.append(f"Average margin is {local_margin:.1f}% vs {ctx['mgn']:.1f}% overall.")
        if "Discount" in sub.columns:
            bullets.append(f"Average discount is {sub['Discount'].mean():.1f}%.")

    elif kind == "product" and "Product Name" in df.columns and name in df["Product Name"].values:
        sub = df[df["Product Name"] == name]
        rev = sub["Total Revenue"].sum()
        share = rev / ctx["total_r"] * 100 if ctx["total_r"] else 0
        bullets.append(f"{name} generates {fmt(rev)} — {share:.1f}% of total revenue.")
        if "Profit Margin" in sub.columns:
            bullets.append(f"Average margin is {sub['Profit Margin'].mean():.1f}%.")
        if ctx["city_r"] is not None and len(sub):
            top_city = sub.groupby("City")["Total Revenue"].sum().idxmax()
            bullets.append(f"Sells best in **{top_city}**.")

    return bullets


# ── Intent handlers. Every handler has the signature
#    (q, ctx, df, mem, detailed) -> (text, fig) | None
#    so blinkbot_analyze can dispatch through them uniformly. ───────────────

def _bb_greeting(q, ctx, df, mem, detailed=False):
    if not _any_kw(q, ["hello","hi","hey","namaste","hii"]): return None
    c         = ctx
    returning = mem.turn_count > 0
    opener    = (f"Welcome back! You've asked **{mem.turn_count}** question(s) so far."
                 if returning else f"I've analyzed **{len(df):,} records** and I'm ready to help.")
    mem.update("greeting")
    text = (
        ResponseBuilder("👋", "Hi! I'm BlinkBot — your AI Data & Business Analyst")
        .answer(opener)
        .metric("Total Revenue", fmt(c["total_r"]), "💰")
        .metric("Top Category",  c["cat_r"].index[0]  if c["cat_r"]  is not None else "N/A", "🏆")
        .metric("Top City",      c["city_r"].index[0] if c["city_r"] is not None else "N/A", "📍")
        .metric("Total Orders",  f"{int(c['total_o']):,}", "🛒")
        .followup("'Give me a summary' · 'Give me 3 insights' · 'What's the data trust score?'")
        .build()
    )
    return text, _chart_revenue_by_category(ctx)


def _bb_unsupported(q, ctx, df, mem, detailed=False):
    """Honest 'I don't have enough information' responses for asks the
    current schema genuinely cannot answer — checked early so these
    questions don't get mis-matched by looser keyword handlers below."""
    checks = [
        (["customer retention", "repeat customer", "repeat purchase", "churn", "customer lifetime",
          "returning customer", "customer id"],
         "I can't calculate customer retention or repeat-purchase behavior because the dataset "
         "doesn't contain a customer ID or order history per customer — only aggregated product/"
         "city/category rows."),
        (["customer segment", "customer demographics", "age group", "gender"],
         "I can't segment by customer demographics — there's no customer-level data in this "
         "dataset, only product/city/category/order aggregates."),
    ]

    # Word-set match (not an exact phrase) so "monthly revenue trend" and
    # "weekly sales trend" are both caught regardless of word order.
    q_words = set(q.replace("?", "").replace(",", "").split())
    _TIME_WORDS  = {"month", "monthly", "week", "weekly", "season", "seasonal", "daily",
                    "date", "quarter", "quarterly", "yoy"}
    _TREND_WORDS = {"trend", "trends", "breakdown"}
    if (q_words & _TIME_WORDS) and ((q_words & _TREND_WORDS) or "over time" in q or "year over year" in q or "month over month" in q):
        checks.append(([w for w in q_words if w in _TIME_WORDS] or ["time-based"],
            "I can't break performance down by month/week/day because the dataset has no Date or "
            "timestamp column — it's a snapshot, not a time series. The Sales Analytics page's "
            "forecast uses product-rank ordering as a proxy trend, which I can explain if useful."))

    if _any_kw(q, ["delivery time", "delivery speed", "delivery minutes", "pickup time", "packing time"]) \
       and "Delivery Time" not in df.columns and "Delivery Cost" not in df.columns:
        checks.append((
            ["delivery time", "delivery speed", "delivery minutes", "pickup time", "packing time"],
            "I can't answer that from raw data — this dataset has no Delivery Time/Pickup Time column. "
            "The Delivery Analytics page shows a simulated delivery-time model instead, calibrated to a "
            "10-minute promise, since no real timing data was uploaded."
        ))
    for keywords, missing_msg in checks:
        if any(k in q for k in keywords):
            mem.update("unsupported")
            text = (
                ResponseBuilder("🤷", "I don't have enough information for that")
                .answer(missing_msg)
                .tip("Ask me about revenue, profit, margin, cities, categories, products, "
                     "influencer impact, discounts, statistics, or data quality instead — "
                     "all of those are fully supported by the current dataset.")
                .build()
            )
            return text, None
    return None


def _bb_why(q, ctx, df, mem, detailed=False):
    if q.strip() not in _WHY_PHRASES:
        return None
    if not mem.last_intent:
        return ("I'm not sure what you're asking 'why' about yet — ask me something first, "
                "like 'which city has the highest revenue', then follow up with 'why'."), None

    subject_kind, subject_name = None, None
    if mem.last_city:
        subject_kind, subject_name = "city", mem.last_city
    elif mem.last_category:
        subject_kind, subject_name = "category", mem.last_category
    elif mem.last_product:
        subject_kind, subject_name = "product", mem.last_product

    if not subject_name:
        return (f"Your last question was about **{mem.last_intent}**, but I don't have a specific "
                f"city, category, or product to explain — ask about a specific one and then say 'why'."), None

    bullets = _dimension_evidence(subject_kind, subject_name, ctx, df)
    if not bullets:
        return f"I don't have enough evidence in the current data to explain why {subject_name} performs this way.", None

    mem.update("why")
    body = "\n".join(f"- {b}" for b in bullets)
    text = (
        ResponseBuilder("🔍", f"Why {subject_name} stands out")
        .answer(f"Here's the evidence behind {subject_name}'s numbers:\n\n{body}")
        .tip(f"If you want to replicate this elsewhere, start with whichever factor above has "
             f"the biggest gap vs the overall average.")
        .followup(f"'Compare {subject_name} with...' · 'What about profit?' · 'Give me a recommendation'")
        .build()
    )
    fig = _chart_city_ranking(ctx) if subject_kind == "city" else (
          _chart_revenue_by_category(ctx) if subject_kind == "category" else _chart_top_products(ctx))
    return text, fig


def _bb_insights(q, ctx, df, mem, detailed=False):
    if not _any_kw(q, ["insight", "insights", "key insight", "important insight",
                                 "quick insight", "biggest opportunity", "biggest risk"]):
        return None
    kpis_local = compute_kpis(df)
    inf_local  = compute_influencer_stats(df)
    insights   = compute_ai_insights(df, kpis_local, inf_local if inf_local.get("available") else {"rev_lift": 0, "p_value": 1, "significant": False})
    mem.update("insights")
    n = 5 if detailed else 3
    lines = "\n".join(f"{emoji} **{title}** — {body}" for emoji, title, body in insights[:n])
    text = (
        ResponseBuilder("💡", f"Top {n} Insights")
        .answer(lines)
        .followup("'Give me a recommendation' · 'Explain the statistics' · 'What's the data trust score?'")
        .build()
    )
    return text, _chart_summary_snapshot(ctx)


def _bb_trust(q, ctx, df, mem, detailed=False):
    if not _any_kw(q, ["trust score", "data quality", "data trust", "is this data clean",
                                 "is the data reliable", "reliable data", "unusual data",
                                 "duplicate data", "missing data", "bengaluru", "bangalore"]):
        return None
    findings = compute_data_quality_findings(df)
    compat   = dataset_compatibility_report(df, {})
    trust    = compute_trust_score(df, findings, compat)
    mem.update("trust")

    issues = []
    if findings["dup_rows"]:
        issues.append(f"{findings['dup_rows']} duplicate row(s)")
    if findings["missing_by_col"]:
        issues.append(f"missing values in {', '.join(findings['missing_by_col'].keys())}")
    if findings["city_aliases"]:
        issues.append("inconsistent city names: " + ", ".join(f"{k}→{v}" for k, v in findings["city_aliases"].items()))
    if findings["similar_categories"]:
        issues.append("similar/misspelled category names: " + "; ".join(", ".join(g) for g in findings["similar_categories"]))
    if findings["negative_or_zero"]:
        issues.append("zero/negative values in " + ", ".join(findings["negative_or_zero"].keys()))

    rb = (
        ResponseBuilder("🛡️", "Data Trust Score")
        .answer(f"**{trust['score']}/100 — {trust['status']}**\n\n{trust['main_issue']}")
        .metric("Completeness", f"{max(0,trust['sub_scores']['completeness'])*100:.0f}%", "📋")
        .metric("Validity",     f"{max(0,trust['sub_scores']['validity'])*100:.0f}%", "✅")
        .metric("Consistency",  f"{max(0,trust['sub_scores']['consistency'])*100:.0f}%", "🔗")
        .metric("Uniqueness",   f"{max(0,trust['sub_scores']['uniqueness'])*100:.0f}%", "🔑")
    )
    if issues:
        rb = rb.context("Issues found: " + "; ".join(issues) + ".")
    else:
        rb = rb.context("No significant issues detected in the current (filtered) view.")
    rb = rb.tip("Standardize any inconsistent city/category names before drawing regional conclusions — "
                "use the Data Import & Trust Center to apply fixes." if issues else
                "Data looks clean — safe to base decisions on it.")
    rb = rb.followup("'Explain the statistics' · 'Are there outliers?' · 'Give me a summary'")
    return rb.build(), None


def _bb_statistics(q, ctx, df, mem, detailed=False):
    if not _any_kw(q, ["statistic", "statistics", "mean", "median", "mode", "std dev",
                                 "standard deviation", "variance", "percentile", "distribution"]):
        return None
    if len(df) < 5:
        return "I need at least 5 rows in the current (filtered) view to compute meaningful statistics.", None
    sd = compute_statistics(df)
    mem.update("statistics")

    skew_note = ("A few unusually high-value orders are pulling the average up above the typical order."
                 if sd["mean"] > sd["median"] else
                 "The average and typical order are close, so there aren't many extreme high-value orders.")

    rb = (
        ResponseBuilder("📐", "Revenue Statistics — Plain Language")
        .answer(f"The average order revenue is **{fmt(sd['mean'])}**, while the median (typical order) is "
                f"**{fmt(sd['median'])}**. {skew_note}")
        .metric("Mean",   fmt(sd["mean"]), "📊")
        .metric("Median", fmt(sd["median"]), "📍")
        .metric("Std Dev", fmt(sd["std"]), "📏")
        .metric("Range",  f"{fmt(df['Total Revenue'].min())} – {fmt(df['Total Revenue'].max())}", "↔️")
    )
    if detailed:
        rb = rb.context(
            f"Skewness is {sd['skewness']:.2f} ({'right-skewed, a few big orders' if sd['skewness']>0.5 else 'left-skewed' if sd['skewness']<-0.5 else 'fairly symmetric'}); "
            f"kurtosis is {sd['kurtosis']:.2f}. Shapiro-Wilk normality test p={sd['p_norm']:.4f} "
            f"({'looks normally distributed' if sd['is_normal'] else 'not normally distributed — expect some skew or outliers'}). "
            f"{len(sd['outliers'])} row(s) flagged as statistical outliers (|Z|>2)."
        )
    else:
        rb = rb.context(f"{len(sd['outliers'])} row(s) are statistical outliers — ask 'are there outliers?' for details.")
    rb = rb.followup("'Are there any outliers?' · 'Explain the correlation' · 'Explain in detail'")
    return rb.build(), None


def _bb_outliers(q, ctx, df, mem, detailed=False):
    if not _any_kw(q, ["outlier", "outliers", "unusual value", "unusual data", "anomaly", "anomalies"]):
        return None
    if len(df) < 5:
        return "I need at least 5 rows in the current (filtered) view to detect outliers.", None
    sd = compute_statistics(df)
    mem.update("outliers")
    outliers = sd["outliers"]
    if len(outliers) == 0:
        text = (
            ResponseBuilder("🔎", "Outlier Check")
            .answer("No statistical outliers detected in Total Revenue for the current view (all values within ~2 standard deviations of the mean).")
            .build()
        )
        return text, None
    top = outliers.sort_values("Z-Score", ascending=False).head(5)
    lines = "\n".join(
        f"- **{r['Product Name']}** in {r['City']} — {fmt(r['Total Revenue'])} (Z={r['Z-Score']:.2f})"
        for _, r in top.iterrows()
    )
    text = (
        ResponseBuilder("🔎", f"{len(outliers)} Outlier(s) Detected")
        .answer(f"These rows have unusually high or low revenue vs the rest of the dataset:\n\n{lines}")
        .tip("Check these rows for data-entry errors first; if they're genuine, they may represent bulk orders or premium products worth investigating separately.")
        .followup("'Explain the statistics' · 'What's the data trust score?'")
        .build()
    )
    return text, None


def _bb_correlation(q, ctx, df, mem, detailed=False):
    if not _any_kw(q, ["correlation", "correlated", "relationship between", "does discount affect",
                                 "does discount increase"]):
        return None
    if len(df) < 5:
        return "I need at least 5 rows in the current (filtered) view to compute correlations.", None
    sd = compute_statistics(df)
    mem.update("correlation")
    r_disc, p_disc = sd["r_disc"], sd["p_disc"]
    r_rev, p_rev   = sd["r_rev"], sd["p_rev"]

    def _explain(r, p, a, b):
        strength = "strong" if abs(r) > 0.5 else "moderate" if abs(r) > 0.3 else "weak"
        direction = "positive" if r > 0 else "negative"
        sig = "statistically significant" if p < 0.05 else "not statistically significant"
        return f"{a} and {b} have a **{strength} {direction}** relationship (r={r:.2f}, {sig})."

    text = (
        ResponseBuilder("🔗", "Correlation Analysis")
        .answer(_explain(r_disc, p_disc, "Discount", "Orders") + "\n\n" + _explain(r_rev, p_rev, "Revenue", "Profit"))
        .context("A positive Discount↔Orders correlation means deeper discounts are associated with more orders — "
                 "but that doesn't automatically mean discounting is profitable; check margin impact too.")
        .followup("'Discount impact on margin?' · 'Give me a recommendation'")
        .build()
    )
    return text, None


def _bb_forecast(q, ctx, df, mem, detailed=False):
    if not _any_kw(q, ["forecast", "will revenue increase", "sales trend", "is the business growing",
                                 "growth", "growing", "trend", "predict", "next month"]):
        return None
    fc = compute_forecast(df)
    mem.update("forecast")
    if fc is None:
        text = (
            ResponseBuilder("📈", "Trend Estimate")
            .answer("I need at least 5 distinct products in the current view to fit a trend estimate.")
            .build()
        )
        return text, None

    direction = "growing" if fc["growth_pct"] >= 0 else "declining"
    quality = "a reasonably good fit" if fc["r2"] > 0.6 else "a noisy, low-confidence fit"
    rb = (
        ResponseBuilder("📈", "Trend Estimate (not a real time-series forecast)")
        .answer(f"Based on product-level revenue ranking (this dataset has no date column, so this is a "
                f"rank-based proxy trend, not a calendar forecast), the estimate is **{direction}** at "
                f"{abs(fc['growth_pct']):.1f}% vs the average product.")
        .metric("Estimated next value", fmt(fc["next_val"]), "🎯")
        .metric("Model fit (R²)", f"{fc['r2']:.2f}", "📐")
        .metric("95% CI band", fmt(fc["ci"]), "↕️")
    )
    rb = rb.context(f"This is {quality} — {'trust it a bit more' if fc['r2']>0.6 else 'treat it as a rough signal only, not a precise prediction'}.")
    rb = rb.tip("Always label this as an estimate to stakeholders — it depends heavily on how much and how clean the historical data is.")
    rb = rb.followup("'Give me a recommendation' · 'Explain the statistics'")
    return rb.build(), None


def _bb_recommendation(q, ctx, df, mem, detailed=False):
    if not _any_kw(q, ["recommend", "recommendation", "what should i improve", "how can i improve",
                                 "improve profit", "improve my business", "what should i do",
                                 "business recommendation", "advice", "increase profit", "increase revenue",
                                 "boost profit", "boost revenue", "grow profit", "grow revenue", "grow the business"]):
        return None
    mem.update("recommendation")
    c = ctx
    recs = []

    if c["city_r"] is not None and len(c["city_r"]) > 1:
        weakest_city = c["city_r"].index[-1]
        recs.append(f"**Investigate {weakest_city}** — it's your lowest-revenue city; find out if it's a market-size issue or an execution gap.")
    if c["best_m"] is not None and len(c["best_m"]) > 1:
        weak_margin_cat = c["best_m"].index[-1]
        recs.append(f"**Review pricing/costs in {weak_margin_cat}** — it has the lowest average profit margin of your categories.")
    if c["disc_grp"] is not None and len(c["disc_grp"]):
        best_disc = c["disc_grp"].loc[c["disc_grp"]["avg_rev"].idxmax(), "Discount"]
        recs.append(f"**Standardize discounts around {int(best_disc)}%** — that level shows the best average revenue per order in this data.")
    if c["city_r"] is not None and c["city_ord"] is not None:
        # cities with high orders but low revenue-per-order (high volume, low value)
        rev_per_order = (c["city_r"] / c["city_ord"]).dropna().sort_values()
        if len(rev_per_order):
            low_value_city = rev_per_order.index[0]
            recs.append(f"**Look at {low_value_city}** — it has high order volume but the lowest revenue-per-order, suggesting heavy discounting or low-value basket sizes.")
    if c["n_inf_y"] and c["inf_lift"] > 5:
        recs.append(f"**Expand influencer marketing** — influencer-active listings show a {c['inf_lift']:+.1f}% revenue lift.")

    findings = compute_data_quality_findings(df)
    if findings["dup_rows"] or findings["city_aliases"] or findings["similar_categories"]:
        recs.append("**Clean the data first** — duplicate rows or inconsistent city/category names can distort every metric above.")

    if not recs:
        recs.append("Data looks healthy across the board — focus on scaling what's already working (top category × top city).")

    n = len(recs) if detailed else min(3, len(recs))
    lines = "\n".join(f"{i+1}. {r}" for i, r in enumerate(recs[:n]))
    text = (
        ResponseBuilder("🎯", "Business Recommendations")
        .answer(lines)
        .context("Every recommendation above is derived from this dataset's actual numbers, not generic advice.")
        .followup("'Give me 3 insights' · 'What's the data trust score?' · 'Explain in detail'")
        .build()
    )
    return text, _chart_summary_snapshot(ctx)


def _bb_explain_dashboard(q, ctx, df, mem, detailed=False):
    if not _any_kw(q, ["explain this dashboard", "explain the dashboard", "how does this work",
                                 "what is this dashboard", "what can you do", "what can this do",
                                 "help me understand this app"]):
        return None
    mem.update("explain_dashboard")
    text = (
        ResponseBuilder("🧭", "About NovaMS")
        .answer(
            "NovaMS is a quick-commerce business intelligence platform with 9 pages: Executive Overview, "
            "Sales Analytics, Delivery Analytics, Inventory Intelligence, Operations, Customer Analytics, "
            "Finance, AI Analyst (me), and Data Explorer.\n\n"
            "I (BlinkBot) can answer questions directly from your currently filtered dataset — revenue, "
            "profit, margin, city/category/product/influencer performance, statistics, data quality, "
            "correlations, outliers, trend estimates, comparisons, and recommendations — all using the "
            "same calculations as the charts, respecting any filters you've applied in the sidebar."
        )
        .followup("'Give me a summary' · 'What's the data trust score?' · 'Give me a recommendation'")
        .build()
    )
    return text, None


def _bb_summary(q, ctx, df, mem, detailed=False):
    if not _any_kw(q, ["summary","summarize","summarise","overview","analyze","brief","tell me"]): return None
    c       = ctx
    aov     = c["aov"]
    weakest = c["city_r"].index[-1] if c["city_r"] is not None else "N/A"
    mem.update("summary",
               city     = c["city_r"].index[0] if c["city_r"] is not None else None,
               product  = c["prod_r"].index[0] if c["prod_r"] is not None else None,
               category = c["cat_r"].index[0]  if c["cat_r"]  is not None else None)

    findings = compute_data_quality_findings(df)
    dq_bits = []
    if findings["dup_rows"]: dq_bits.append(f"{findings['dup_rows']} duplicate rows")
    if findings["missing_by_col"]: dq_bits.append("some missing values")
    if findings["city_aliases"]: dq_bits.append("inconsistent city names")
    dq_line = "; ".join(dq_bits) if dq_bits else "no significant issues detected"

    rb = (
        ResponseBuilder("📋", "Business Summary")
        .answer(f"Here's everything at a glance across **{len(df):,} records**.")
        .metric("1. Total Revenue",  fmt(c["total_r"]), "💰")
        .metric("2. Total Profit",   f"{fmt(c['total_p'])} ({c['mgn']:.1f}% margin)", "📈")
        .metric("3. Total Orders",   f"{int(c['total_o']):,} | AOV: {fmt(aov)}", "🛒")
        .metric("4. Best Segment",   f"{c['cat_r'].index[0] if c['cat_r'] is not None else 'N/A'} in "
                                     f"{c['city_r'].index[0] if c['city_r'] is not None else 'N/A'}", "🏆")
        .metric("5. Weak Segment",   f"{weakest}", "⚠️")
        .metric("6. Data Quality",   dq_line, "🛡️")
    )
    rb = rb.context(f"⚠️ **{weakest}** is your weakest region — investigate and run targeted promotions there.")
    rb = rb.tip(f"Focus on {c['cat_r'].index[0] if c['cat_r'] is not None else 'top category'} "
                f"in {c['city_r'].index[0] if c['city_r'] is not None else 'top city'} — this is your growth engine.")
    if detailed:
        rb = rb.followup(f"'Give me a recommendation' · 'Give me 3 insights' · 'Explain the statistics' · 'Tell me about {weakest}'")
    else:
        rb = rb.followup(f"'Tell me about {weakest}' · 'Give me a recommendation' · 'Explain in detail'")
    return rb.build(), _chart_summary_snapshot(ctx)


def _bb_revenue(q, ctx, df, mem, detailed=False):
    if not _any_kw(q, ["revenue","how much","earnings","sales total"]): return None
    c        = ctx
    top_cat  = c["cat_r"].index[0]  if c["cat_r"]  is not None else "N/A"
    top_city = c["city_r"].index[0] if c["city_r"] is not None else "N/A"
    target_city = mem.last_city
    extra_ctx   = ""
    if target_city and target_city in df["City"].values:
        city_rev_val = df[df["City"]==target_city]["Total Revenue"].sum()
        share        = city_rev_val / c["total_r"] * 100 if c["total_r"] else 0
        extra_ctx    = f"{target_city} contributes **{fmt(city_rev_val)}** ({share:.1f}% of total)."
    mem.update("revenue", category=top_cat, city=top_city)
    top_cat_share = c["cat_r"].iloc[0]/c["total_r"]*100 if c["cat_r"] is not None and c["total_r"] else 0
    rb = (
        ResponseBuilder("📊", "Revenue Analysis")
        .answer(f"Total revenue is **{fmt(c['total_r'])}** across **{len(df):,} transactions**.")
        .metric("Best category",   f"{top_cat} ({top_cat_share:.1f}%)" if c["cat_r"] is not None else "N/A", "🏆")
        .metric("Top city",        top_city, "📍")
        .metric("Net profit",      f"{fmt(c['total_p'])} ({c['mgn']:.1f}% margin)", "💰")
        .metric("Avg order value", fmt(c["aov"]), "🛒")
    )
    if not extra_ctx and top_cat_share:
        extra_ctx = (f"{top_cat} alone drives {top_cat_share:.1f}% of revenue, but overall margin is "
                     f"{c['mgn']:.1f}% — so revenue concentration isn't automatically translating into "
                     f"proportional profit. Check the margin breakdown by category too.")
    if extra_ctx: rb = rb.context(extra_ctx)
    rb = rb.tip(f"Double down on **{top_cat}** in **{top_city}** — allocate more marketing budget here.")
    rb = rb.followup("'Break down by category' · 'Which product earns most?' · 'Why?'")
    return rb.build(), _chart_revenue_by_category(ctx)


def _bb_margin(q, ctx, df, mem, detailed=False):
    """Dedicated handler for explicit margin-comparison questions (checked
    before the more general _bb_profit handler)."""
    if not _any_kw(q, ["lowest margin", "highest margin", "best margin", "worst margin",
                                 "which category has the lowest profit margin", "margin comparison"]):
        return None
    bm = ctx["best_m"]
    if bm is None or len(bm) == 0:
        return "Profit margin data isn't available for the current view.", None
    mem.update("margin", category=bm.index[0])
    best_cat, worst_cat = bm.index[0], bm.index[-1]
    text = (
        ResponseBuilder("📐", "Margin Comparison by Category")
        .answer(f"**{best_cat}** has the highest average margin ({bm.iloc[0]:.1f}%); "
                f"**{worst_cat}** has the lowest ({bm.iloc[-1]:.1f}%).")
        .context(f"That's a {bm.iloc[0]-bm.iloc[-1]:.1f} percentage-point gap — "
                 f"worth checking whether {worst_cat}'s pricing or discounting is too aggressive.")
        .tip(f"Consider raising prices slightly or reducing discount depth in {worst_cat}, "
             f"or shifting marketing spend toward {best_cat}.")
        .followup(f"'Why does {worst_cat} have low margin?' · 'Compare {best_cat} and {worst_cat}'")
        .build()
    )
    return text, _chart_profit_margin_by_category(ctx, df)


def _bb_profit(q, ctx, df, mem, detailed=False):
    if not _any_kw(q, ["profit","margin","net"]): return None
    c          = ctx
    bm         = c["best_m"]
    prev_topic = mem.last_intent
    target_city = mem.last_city
    city_note   = ""
    if target_city and target_city in df["City"].values and prev_topic in ("city", "revenue", "compare", "why"):
        city_profit_val = df[df["City"] == target_city]["Profit"].sum()
        city_margin_val = df[df["City"] == target_city]["Profit Margin"].mean()
        city_note = (f"Sticking with **{target_city}**: its profit is **{fmt(city_profit_val)}** "
                     f"at a **{city_margin_val:.1f}%** margin (overall margin is {c['mgn']:.1f}%).")
    mem.update("profit", category=bm.index[0] if bm is not None else None)
    rb = (
        ResponseBuilder("💰", "Profit & Margin Analysis")
        .answer(city_note if city_note else f"Total profit is **{fmt(c['total_p'])}** on revenue of **{fmt(c['total_r'])}**.")
        .metric("Total profit",       fmt(c["total_p"]), "💰")
        .metric("Profit margin",      f"{c['mgn']:.1f}%", "📈")
        .metric("Highest-margin cat", f"{bm.index[0] if bm is not None else 'N/A'} ({bm.iloc[0]:.1f}%)" if bm is not None else "N/A", "🏆")
        .metric("Lowest-margin cat",  f"{bm.index[-1] if bm is not None else 'N/A'} — needs review"     if bm is not None else "N/A", "⚠️")
    )
    if not city_note and prev_topic == "revenue":
        rb = rb.context("You were just looking at revenue — margin tells you how much you actually keep after costs.")
    rb = rb.tip(f"Grow **{bm.index[0] if bm is not None else 'top category'}** volume — best return per rupee sold.")
    rb = rb.followup("'Which category has lowest margin?' · 'Discount impact on margin?' · 'Why?'")
    return rb.build(), _chart_profit_margin_by_category(ctx, df)


def _bb_best_product(q, ctx, df, mem, detailed=False):
    if not _any_kw(q, ["best product","top product","number one","highest selling","top 5 product","top products"]): return None
    by_profit = "profit" in q
    pr = ctx["prod_profit"] if (by_profit and ctx["prod_profit"] is not None) else ctx["prod_r"]
    basis = "Profit" if by_profit else "Revenue"
    if pr is None: return "Product data not available.", None
    n = 5 if ("top 5" in q or detailed) else 3
    topn   = pr.head(n)
    medals = ["🥇","🥈","🥉"] + ["▫️"] * max(0, n - 3)
    lines  = "\n".join([f"{medals[i]} **{topn.index[i]}** — {fmt(topn.iloc[i])}" for i in range(len(topn))])
    mem.update("best_product", product=topn.index[0])
    text = (
        ResponseBuilder("🏆", f"Top {n} Products by {basis}")
        .answer(f"Your #1 product is **{topn.index[0]}** generating **{fmt(topn.iloc[0])}** in {basis.lower()}.\n\n{lines}")
        .metric("Share of total", f"{topn.iloc[0]/(ctx['total_p'] if by_profit else ctx['total_r'])*100:.1f}%", "📊")
        .metric("Runner-up gap",  fmt(topn.iloc[0]-topn.iloc[1]) if len(topn)>1 else "—", "↔️")
        .tip(f"Keep **{topn.index[0]}** always in stock. Bundle with **{topn.index[1] if len(topn)>1 else '#2'}** to boost AOV.")
        .followup(f"'Worst products?' · 'Why does {topn.index[0]} do well?' · 'Top products by revenue instead'")
        .build()
    )
    return text, _chart_top_products(ctx)


def _bb_worst_product(q, ctx, df, mem, detailed=False):
    if not _any_kw(q, ["worst product","lowest","weakest product","losing money","low-performing product"]): return None
    pr = ctx["prod_r"]
    if pr is None: return "Product data not available.", None
    worst = pr.tail(3).sort_values()
    lines = "\n".join([f"{['🔴','🟡','🟡'][i]} **{worst.index[i]}** — {fmt(worst.iloc[i])}" for i in range(len(worst))])
    mem.update("worst_product", product=worst.index[0])

    losing_note = ""
    if ctx["prod_profit"] is not None:
        losers = ctx["prod_profit"][ctx["prod_profit"] < 0]
        if len(losers):
            losing_note = f" {len(losers)} product(s) have **negative total profit** — see the chart for detail."

    text = (
        ResponseBuilder("⚠️", "Underperforming Products")
        .answer(f"Lowest revenue: **{worst.index[0]}** at only **{fmt(worst.iloc[0])}**.{losing_note}\n\n{lines}")
        .metric("Gap to #1", fmt(ctx["prod_r"].iloc[0] - worst.iloc[0]), "↕️")
        .tip("Run a 30-day promotion on these. If no improvement, discontinue the lowest performer.")
        .followup(f"'Best product?' · 'Why is {worst.index[0]} weak?' · 'Discount to boost it?'")
        .build()
    )
    return text, _chart_top_products(ctx, n=8)


def _bb_city(q, ctx, df, mem, detailed=False):
    if not _any_kw(q, ["city","region","location","where"]): return None
    cr      = ctx["city_r"]
    if cr is None: return "City data not found.", None
    weakest  = cr.index[-1]
    best     = cr.index[0]
    gap_pct  = ((cr.iloc[0]-cr.iloc[-1])/cr.iloc[-1]*100) if len(cr)>1 and cr.iloc[-1]>0 else 0
    ranking  = "\n".join([
        f"{i+1}. {'🟢' if i==0 else '🟡' if i<len(cr)-1 else '🔴'} **{c}** — {fmt(v)}"
        for i,(c,v) in enumerate(cr.items())
    ])
    prev_city = mem.last_city
    mem.update("city", city=best)
    rb = (
        ResponseBuilder("📍", "City & Region Performance")
        .answer(f"**{best}** is your strongest market at **{fmt(cr.iloc[0])}**.\n\n{ranking}")
        .metric("Performance gap", f"{gap_pct:.0f}% between best and worst", "↕️")
    )
    if prev_city and prev_city != best and prev_city in cr.index:
        prev_val = cr[prev_city]
        rb = rb.context(f"You asked about **{prev_city}** earlier — {fmt(prev_val)}, ranked #{list(cr.index).index(prev_city)+1}.")
    elif gap_pct > 50:
        rb = rb.context(f"⚠️ {weakest} underperforms by **{gap_pct:.0f}%** — big opportunity here.")
    rb = rb.tip(f"Replicate {best}'s success in {weakest} — start with influencer campaigns for top 3 products.")
    rb = rb.followup(f"'Why is {best} performing well?' · 'Compare {best} and {weakest}' · 'Revenue in {weakest}'")
    return rb.build(), _chart_city_ranking(ctx)


def _bb_category(q, ctx, df, mem, detailed=False):
    if not _any_kw(q, ["category","segment","best category"]): return None
    cat_r   = ctx["cat_r"]
    total_r = ctx["total_r"]
    if cat_r is None: return "Category data not available.", None
    medals  = ["🥇","🥈","🥉"] + ["▫️"]*(len(cat_r)-3)
    lines   = "\n".join([f"{medals[i]} **{c}** — {fmt(v)} ({v/total_r*100:.1f}%)" for i,(c,v) in enumerate(cat_r.items())])
    weakest = cat_r.index[-1]
    mem.update("category", category=cat_r.index[0])
    text = (
        ResponseBuilder("🏷️", "Category Performance Breakdown")
        .answer(f"**{cat_r.index[0]}** leads with **{fmt(cat_r.iloc[0])}** ({cat_r.iloc[0]/total_r*100:.1f}% of total).\n\n{lines}")
        .metric("Categories tracked", str(len(cat_r)), "📂")
        .metric("Weakest segment",    f"{weakest} ({cat_r.iloc[-1]/total_r*100:.1f}%)", "⚠️")
        .tip(f"**{weakest}** is weakest at {cat_r.iloc[-1]/total_r*100:.1f}%. Promote it or shift budget to **{cat_r.index[0]}**.")
        .followup(f"'Should I focus on {cat_r.index[0]} or {weakest}?' · 'Margin by category' · 'Why?'")
        .build()
    )
    return text, _chart_revenue_by_category(ctx)


def _bb_influencer(q, ctx, df, mem, detailed=False):
    if not _any_kw(q, ["influencer","marketing","campaign"]): return None
    if "Influencer Active" not in df.columns: return "Influencer data not available.", None
    c           = ctx
    significant = abs(c["inf_lift"]) > 5
    mem.update("influencer")
    text = (
        ResponseBuilder("⚡", "Influencer Marketing Impact")
        .answer(f"Influencer-active products generate a **{c['inf_lift']:+.1f}% revenue lift**.")
        .metric("With influencer (avg rev)",    fmt(c["inf_y_rev"]), "✅")
        .metric("Without influencer (avg rev)", fmt(c["inf_n_rev"]), "❌")
        .metric("Order volume lift",            f"{c['ord_lift']:+.1f}%", "📦")
        .metric("Influencer-active SKUs",       f"{c['n_inf_y']} of {len(df)}", "🎯")
        .context("Lift is statistically meaningful ✓" if significant else "Lift is small — run a larger test.")
        .tip("Scale up — activate influencers for ALL top-category products!" if c["inf_lift"]>5 else "Small lift — focus on micro-influencers in specific cities.")
        .followup("'Which category benefits most?' · 'Top cities for campaigns?' · 'Compare influencer vs non-influencer'")
        .build()
    )
    return text, _chart_influencer_lift(ctx, df)


def _bb_aov(q, ctx, df, mem, detailed=False):
    if not _any_kw(q, ["average order value", "aov", "average order size", "average basket"]):
        return None
    mem.update("aov")
    c = ctx
    text = (
        ResponseBuilder("🛒", "Average Order Value")
        .answer(f"The average order value is **{fmt(c['aov'])}**.")
        .metric("Total Orders", f"{int(c['total_o']):,}", "📦")
        .metric("Total Revenue", fmt(c["total_r"]), "💰")
        .tip(f"Bundle deals or minimum-order incentives could push AOV from {fmt(c['aov'])} toward {fmt(c['aov']*1.15)} (+15%).")
        .followup("'Explain the statistics' · 'Which product has the most orders?'")
        .build()
    )
    return text, None


def _bb_orders(q, ctx, df, mem, detailed=False):
    if not _any_kw(q, ["orders","order count","volume","how many orders"]): return None
    c      = ctx
    aov    = c["aov"]
    top_co = c["city_ord"]
    mem.update("orders", city=top_co.index[0] if top_co is not None else None)
    text = (
        ResponseBuilder("🛒", "Order Volume Analysis")
        .answer(f"**{int(c['total_o']):,} total orders** have been processed.")
        .metric("Average order value",  fmt(aov), "💰")
        .metric("Top city by orders",   f"{top_co.index[0] if top_co is not None else 'N/A'} ({int(top_co.iloc[0]):,})", "📍")
        .metric("Revenue per order",    fmt(c["total_r"]/c["total_o"] if c["total_o"] else 0), "📊")
        .metric("Target AOV (+15%)",    fmt(aov*1.15), "🎯")
        .tip(f"Increase AOV from **{fmt(aov)}** to **{fmt(aov*1.15)}** with bundle deals. 15% AOV lift = 15% more revenue at zero extra cost.")
        .followup("'Which product has most orders?' · 'Orders by city?' · 'Discount impact?'")
        .build()
    )
    return text, _chart_orders_by_city(df)


def _bb_discount(q, ctx, df, mem, detailed=False):
    if not _any_kw(q, ["discount","offer","deal","promo"]): return None
    dg = ctx["disc_grp"]
    if dg is None: return "Discount data not available.", None
    best  = dg.loc[dg["avg_rev"].idxmax()]
    lines = "\n".join([
        f"- **{int(r.Discount)}%** → Avg Rev: {fmt(r.avg_rev)} | Avg Orders: {r.avg_orders:.0f}"
        for _, r in dg.iterrows()
    ])
    mem.update("discount")
    text = (
        ResponseBuilder("🏷️", "Discount Effectiveness Analysis")
        .answer(f"Most effective discount: **{int(best['Discount'])}%** generating **{fmt(best['avg_rev'])}** avg revenue.\n\n{lines}")
        .metric("Sweet-spot discount", f"{int(best['Discount'])}%", "🎯")
        .metric("Peak avg revenue",    fmt(best["avg_rev"]), "💰")
        .metric("Peak avg orders",     f"{best['avg_orders']:.0f}", "🛒")
        .tip(f"Stick to **{int(best['Discount'])}%** as your standard promo rate. Avoid deeper discounts — they train customers to wait.")
        .followup("'Discount vs profit margin?' · 'Which category discounts best?' · 'Explain the correlation'")
        .build()
    )
    return text, _chart_discount_curve(ctx)


def _bb_inventory(q, ctx, df, mem, detailed=False):
    if not _any_kw(q, ["stock","inventory","reorder","shortage"]): return None
    pr = ctx["prod_r"]
    if pr is None: return "Product data not available.", None
    top5  = pr.head(5)
    items = "\n".join([f"{i+1}. 🔴 **{p}** — {fmt(v)} revenue" for i,(p,v) in enumerate(top5.items())])
    mem.update("inventory", product=top5.index[0])
    text = (
        ResponseBuilder("📦", "Inventory Risk Alert")
        .answer(f"Top 5 products by sales velocity (highest reorder priority):\n\n{items}")
        .metric("Priority reorder",    top5.index[0], "⚡")
        .metric("Safety stock target", "50+ units for top SKUs", "🎯")
        .metric("Auto-reorder trigger","20 units remaining",     "⚠️")
        .tip(f"Set auto-reorder alerts at 20 units for top products. Keep **{top5.index[0]}** at 100+ units safety stock.")
        .followup(f"'Days of cover for {top5.index[0]}?' · 'Which city sells it fastest?' · 'OOS impact on revenue?'")
        .build()
    )
    return text, _chart_top_products(ctx, n=5)


def _bb_compare(q, ctx, df, mem, detailed=False):
    if not _any_kw(q, ["compare","vs","versus","against","difference between","better:",
                        "should i focus","focus more on","which is better"]): return None

    # Try to find two named entities of the SAME kind mentioned in the question.
    def _find_two(values):
        found = [v for v in values if v.lower() in q]
        return found[:2]

    def _find_two_cities():
        """Like _find_two, but also recognizes known aliases (e.g. 'Bengaluru' in
        the question resolves to 'Bangalore' if that's the canonical name in df)
        — the raw text might use a pre-standardization spelling even though the
        dataset itself was already cleaned."""
        present = list(df["City"].unique()) if "City" in df.columns else []
        found, seen = [], set()
        for city in present:
            if city.lower() in q and city not in seen:
                found.append(city); seen.add(city)
        for alias, canonical in CITY_ALIASES.items():
            if alias in q and canonical in present and canonical not in seen:
                found.append(canonical); seen.add(canonical)
        return found[:2]

    cities_in_q = _find_two_cities()
    cats_in_q   = _find_two(df["Category"].unique()) if "Category" in df.columns else []
    prods_in_q  = _find_two(df["Product Name"].unique()) if "Product Name" in df.columns else []

    def _compare_block(kind, a, b, series_rev, series_profit, series_margin=None):
        va, vb = series_rev.get(a, 0), series_rev.get(b, 0)
        winner, loser = (a, b) if va >= vb else (b, a)
        wv, lv = max(va, vb), min(va, vb)
        gap = (wv - lv) / lv * 100 if lv else 0
        pa, pb = (series_profit.get(a, 0), series_profit.get(b, 0)) if series_profit is not None else (None, None)
        bullets = _dimension_evidence(kind, winner, ctx, df)
        rb = (
            ResponseBuilder("⚖️", f"Comparison: {a} vs {b}")
            .answer(f"**{winner}** outperforms **{loser}** by **{gap:.0f}%** in revenue.")
            .metric(a, fmt(va), "🟢" if a == winner else "🔴")
            .metric(b, fmt(vb), "🟢" if b == winner else "🔴")
            .metric("Revenue gap", fmt(abs(va - vb)), "↕️")
        )
        if pa is not None:
            rb = rb.metric(f"Profit ({winner})", fmt(pa if winner == a else pb), "💰")
        if bullets:
            rb = rb.context(bullets[0] + (" " + bullets[1] if len(bullets) > 1 else ""))
        rb = rb.tip(f"Investigate what makes {winner} strong and test replicating it in {loser}.")
        rb = rb.followup(f"'Why is {winner} better?' · 'Give me a recommendation'")
        return rb.build()

    mem.update("compare")
    if len(cities_in_q) == 2 and ctx["city_r"] is not None:
        mem.update("compare", city=cities_in_q[0])
        return _compare_block("city", cities_in_q[0], cities_in_q[1], ctx["city_r"], ctx["city_profit"]), _chart_city_ranking(ctx)
    if len(cats_in_q) == 2 and ctx["cat_r"] is not None:
        mem.update("compare", category=cats_in_q[0])
        return _compare_block("category", cats_in_q[0], cats_in_q[1], ctx["cat_r"], ctx["cat_profit"]), _chart_revenue_by_category(ctx)
    if len(prods_in_q) == 2 and ctx["prod_r"] is not None:
        mem.update("compare", product=prods_in_q[0])
        return _compare_block("product", prods_in_q[0], prods_in_q[1], ctx["prod_r"], ctx["prod_profit"]), _chart_top_products(ctx)
    if "influencer" in q and ctx["inf_y_rev"] is not None:
        mem.update("compare")
        text = (
            ResponseBuilder("⚖️", "Influencer vs Non-Influencer")
            .answer(f"Influencer-active listings average **{fmt(ctx['inf_y_rev'])}** vs **{fmt(ctx['inf_n_rev'])}** "
                    f"without — a **{ctx['inf_lift']:+.1f}%** difference.")
            .tip("Expand influencer coverage if the lift is consistent across categories." if ctx["inf_lift"] > 5 else
                 "The lift is small — test with a larger, more targeted influencer campaign before scaling.")
            .build()
        )
        return text, _chart_influencer_lift(ctx, df)

    # Fallback: no two named entities recognized — default to top vs bottom city (previous behavior)
    cr = ctx["city_r"]
    if cr is not None and len(cr) >= 2:
        c1, c2 = cr.index[0], cr.index[-1]
        mem.update("compare", city=c1)
        return _compare_block("city", c1, c2, ctx["city_r"], ctx["city_profit"]), _chart_city_ranking(ctx)
    return None


def _bb_executive_summary(q, ctx, df, mem, detailed=False):
    if not _any_kw(q, ["executive summary", "business summary", "overall summary",
                        "give me the summary", "top level summary"]):
        return None
    kpis_local = compute_kpis(df)
    mem.update("executive_summary")
    text = (
        ResponseBuilder("📋", "Executive Summary")
        .answer(compute_executive_summary(df, kpis_local))
        .followup("'Why did Delhi perform well?' · 'Are there any anomalies?' · 'Give me a recommendation'")
        .build()
    )
    return text, _chart_summary_snapshot(ctx)


def _bb_anomaly(q, ctx, df, mem, detailed=False):
    if not _any_kw(q, ["anomaly", "anomalies", "unusual", "spike", "sudden drop",
                        "sudden increase", "irregular"]):
        return None
    mem.update("anomaly")
    anomaly = detect_top_anomaly(df)
    if not anomaly:
        text = (
            ResponseBuilder("✅", "No Significant Anomalies")
            .answer("Nothing in the current (filtered) view stands out as a strong statistical outlier "
                    "(|Z| < 3) in Total Revenue.")
            .build()
        )
        return text, None
    text = (
        ResponseBuilder("⚠️", "Anomaly Detected")
        .answer(f"**{anomaly['product']}** in **{anomaly['city']}** ({anomaly['category']}) shows an "
                f"unusual revenue **{anomaly['direction']}** — {fmt(anomaly['revenue'])} "
                f"(Z-score {anomaly['z']:.1f} vs the rest of the current view).")
        .tip("Check this row for a data-entry error first; if genuine, it may be a bulk order or a "
             "one-off promotion worth investigating separately.")
        .followup(f"'Why is {anomaly['city']} performing this way?' · 'What's the data trust score?'")
        .build()
    )
    return text, None


def _bb_product_quadrant(q, ctx, df, mem, detailed=False):
    if not _any_kw(q, ["profitability matrix", "product quadrant", "star product",
                        "growth opportunity", "which products are stars"]):
        return None
    if "Product Name" not in df.columns or "Profit Margin" not in df.columns:
        return "Product-level profitability data isn't available for the current view.", None
    prod_agg = df.groupby("Product Name").agg(Revenue=("Total Revenue", "sum"), Profit=("Profit", "sum"))
    prod_agg["Margin"] = np.where(prod_agg["Revenue"] > 0, prod_agg["Profit"] / prod_agg["Revenue"] * 100, 0)
    median_rev, median_mgn = prod_agg["Revenue"].median(), prod_agg["Margin"].median()
    prod_agg["Quadrant"] = prod_agg.apply(
        lambda r: _classify_profitability_quadrant(r["Revenue"], r["Margin"], median_rev, median_mgn), axis=1
    )
    counts = prod_agg["Quadrant"].value_counts()
    stars  = prod_agg[prod_agg["Quadrant"] == "Star"].sort_values("Revenue", ascending=False)
    mem.update("product_quadrant")
    rb = (
        ResponseBuilder("🧭", "Product Profitability Matrix")
        .answer(f"Splitting products at the median Revenue and Margin: "
                f"**{counts.get('Star', 0)} Star**, **{counts.get('Volume Driver', 0)} Volume Driver**, "
                f"**{counts.get('Growth Opportunity', 0)} Growth Opportunity**, "
                f"**{counts.get('Review', 0)} Review** candidate(s).")
    )
    if len(stars):
        rb = rb.context(f"Top Star product: **{stars.index[0]}** — high revenue and above-median margin.")
    rb = rb.tip("Protect Star products first, then look at Growth Opportunities for wider distribution.")
    rb = rb.followup("'Give me a recommendation' · 'Which category has the lowest margin?'")
    return rb.build(), _chart_top_products(ctx)


def _bb_fallback(q, ctx, df, mem, detailed=False):
    hint    = f"\n\n💬 *Last topic: **{mem.last_intent}** — say 'tell me more' to expand.*" if mem.last_intent else ""
    cols_av = ", ".join(df.columns.tolist())
    text = (
        ResponseBuilder("🤔", "I didn't quite catch that")
        .answer(
            "I can help you with:\n"
            "- 💰 Revenue, profit & margin\n- 🏆 Best / worst products (by revenue or profit)\n- 📍 City performance\n"
            "- 🏷️ Category breakdown\n- ⚡ Influencer impact\n- 🛒 Orders & AOV\n"
            "- 🏷️ Discount analysis\n- 📦 Inventory alerts\n- ⚖️ Compare any two cities/categories/products\n"
            "- 📐 Statistics, correlations & outliers\n- 🛡️ Data trust score\n- 📈 Trend estimates\n"
            "- 📋 Executive summary\n- ⚠️ Anomaly detection\n- 🧭 Product profitability matrix\n"
            "- 🎯 Recommendations\n- 💡 Quick insights" + hint
        )
        .context(f"Available columns: {cols_av}")
        .followup("'Give me a summary' · 'Give me 3 insights' · 'What's the data trust score?'")
        .build()
    )
    return text, None


# Dispatch order matters: unsupported/why/compare/insights are checked early
# so they aren't shadowed by looser single-keyword handlers further down.
_BB_HANDLERS = [
    _bb_greeting, _bb_unsupported, _bb_why, _bb_compare, _bb_insights, _bb_trust,
    _bb_executive_summary, _bb_anomaly, _bb_product_quadrant,
    _bb_statistics, _bb_outliers, _bb_correlation, _bb_forecast, _bb_recommendation,
    _bb_explain_dashboard, _bb_summary, _bb_best_product, _bb_margin, _bb_worst_product,
    _bb_revenue, _bb_profit, _bb_aov, _bb_city, _bb_category,
    _bb_influencer, _bb_orders, _bb_discount, _bb_inventory,
]


def blinkbot_analyze(question: str, df: pd.DataFrame) -> BotReply:
    if df is None or len(df) == 0:
        return "⚠️ No data loaded yet. Please upload a CSV or Excel file to get started!", None
    mem      = _get_memory()
    entities = extract_entities(question, df)
    q_raw    = question.lower().strip()
    if entities["city"]:     mem.last_city     = entities["city"]
    if entities["product"]:  mem.last_product  = entities["product"]
    if entities["category"]: mem.last_category = entities["category"]
    q        = resolve_references(q_raw, mem)
    detailed = _detect_detail_level(question) == "detailed"
    ctx      = _bb_context(df)
    for handler in _BB_HANDLERS:
        result = handler(q, ctx, df, mem, detailed)
        if result is not None:
            _save_memory(mem)
            return result
    _save_memory(mem)
    return _bb_fallback(q, ctx, df, mem, detailed)


# ══════════════════════════════════════════════════════════════════════════════════
# ── LLM INTEGRATION  (Anthropic API · streaming · chart detection)
# ══════════════════════════════════════════════════════════════════════════════════

_CLAUDE_API_URL      = "https://api.anthropic.com/v1/messages"
_CLAUDE_MODEL        = "claude-sonnet-5"
_ANTHROPIC_VERSION   = "2023-06-01"
_MAX_LLM_TOKENS      = 1024
_LLM_HISTORY_LIMIT   = 12


def _build_llm_system_prompt(df: pd.DataFrame, kpis: dict) -> str:
    cat_r  = kpis["cat_rev"]
    city_r = kpis["city_rev"]
    prod_r = df.groupby("Product Name")["Total Revenue"].sum().sort_values(ascending=False)

    def _top_list(series, n=5):
        return "\n".join([f"  {i+1}. {k}: {fmt(v)}" for i,(k,v) in enumerate(series.head(n).items())])

    inf_y = df[df["Influencer Active"]=="Yes"]["Total Revenue"].mean() if "Influencer Active" in df.columns else 0
    inf_n = df[df["Influencer Active"]=="No"]["Total Revenue"].mean()  if "Influencer Active" in df.columns else 0
    inf_lift = ((inf_y - inf_n) / inf_n * 100) if inf_n > 0 else 0

    discount_sweet = ""
    if "Discount" in df.columns:
        dg = df.groupby("Discount")["Total Revenue"].mean()
        best_disc = dg.idxmax()
        discount_sweet = f"  Optimal discount rate: {int(best_disc)}% (highest avg revenue)"

    return f"""You are **BlinkBot**, the AI Business Analyst embedded in NovaMS — a quick-commerce operations platform.

## LIVE DATA SNAPSHOT  ({len(df):,} records, filters active)

### Core KPIs
- Total Revenue      : {fmt(kpis['total_rev'])}
- Total Profit       : {fmt(kpis['total_profit'])} ({kpis['margin']:.1f}% margin)
- Total Orders       : {int(kpis['total_orders']):,}
- Avg Order Value    : {fmt(kpis['aov'])}
- Revenue Std Dev    : {fmt(kpis['rev_std'])}

### Top Products
{_top_list(prod_r)}

### Revenue by City
{_top_list(city_r)}

### Revenue by Category
{_top_list(cat_r, n=len(cat_r))}

### Influencer & Discount
- Influencer lift    : {inf_lift:+.1f}% revenue uplift (active vs inactive)
- Avg price range    : ₹{df['Current Price'].min():.0f}–₹{df['Current Price'].max():.0f}
- Avg discount       : {df['Discount'].mean():.1f}%
{discount_sweet}

## PERSONALITY & RULES
1. You are direct and data-driven — lead with the specific number, not a hedge
2. Always use Indian currency format: ₹12.3L (lakhs), ₹2.1Cr (crores)
3. Structure every answer as: (1) direct answer, (2) supporting KPI, (3) likely reason, (4) 💡 recommendation
4. Keep answers concise (3-6 sentences) unless the user explicitly asks for detail
5. You have full conversation context — use it for follow-up questions
6. NEVER invent data not in the snapshot above; say "data not available" if uncertain
7. When comparing, cite the exact gap (₹ and %)
8. Tone: confident senior analyst, not a chatbot — no filler phrases like "Great question!"
"""


def _sanitise_messages(messages: list[dict]) -> list[dict]:
    clean = [
        m for m in messages
        if isinstance(m.get("content"), str)
        and m["content"].strip()
        and not m["content"].strip().startswith("⚠️")
        and m.get("role") in ("user", "assistant")
    ]
    merged: list[dict] = []
    for msg in clean:
        if merged and merged[-1]["role"] == msg["role"]:
            merged[-1]["content"] += "\n" + msg["content"]
        else:
            merged.append({"role": msg["role"], "content": msg["content"]})
    while merged and merged[0]["role"] != "user":
        merged.pop(0)
    return merged


def _call_claude_stream(messages: list[dict], system: str, api_key: str):
    headers = {
        "x-api-key": api_key.strip(),
        "anthropic-version": _ANTHROPIC_VERSION,
        "content-type": "application/json",
    }
    payload = {
        "model": _CLAUDE_MODEL,
        "max_tokens": _MAX_LLM_TOKENS,
        "system": system,
        "messages": messages,
        "stream": True,
    }
    if not messages:
        yield "\n\n⚠️ **No messages to send.** Please type your question and try again."
        return
    try:
        with requests.post(
            _CLAUDE_API_URL, headers=headers, json=payload,
            stream=True, timeout=45
        ) as resp:
            if resp.status_code == 400:
                try:   err = resp.json().get("error", {}).get("message", resp.text[:300])
                except Exception: err = resp.text[:300]
                yield f"\n\n⚠️ **Bad request (400):** {err}"
                return
            if resp.status_code == 401:
                yield "\n\n⚠️ **Invalid API key.** Get yours at console.anthropic.com → API Keys."
                return
            if resp.status_code == 429:
                yield "\n\n⚠️ **Rate limit hit.** Please wait a moment and retry."
                return
            if not resp.ok:
                try:   err = resp.json().get("error", {}).get("message", resp.text[:300])
                except Exception: err = resp.text[:300]
                yield f"\n\n⚠️ **API error {resp.status_code}:** {err}"
                return
            for raw_line in resp.iter_lines():
                if not raw_line:
                    continue
                line = raw_line.decode("utf-8") if isinstance(raw_line, bytes) else raw_line
                if not line.startswith("data: "):
                    continue
                data_str = line[6:].strip()
                if not data_str:
                    continue
                try:
                    chunk = json.loads(data_str)
                except json.JSONDecodeError:
                    continue
                chunk_type = chunk.get("type")
                if chunk_type == "content_block_delta":
                    delta = chunk.get("delta", {})
                    if delta.get("type") == "text_delta":
                        text = delta.get("text", "")
                        if text:
                            yield text
                elif chunk_type == "error":
                    err_msg = chunk.get("error", {}).get("message", "Unknown error")
                    yield f"\n\n⚠️ **Claude API error:** {err_msg}"
                    return
                elif chunk_type == "message_stop":
                    break
    except requests.exceptions.Timeout:
        yield "\n\n⚠️ **Request timed out.** Try again in a moment."
    except requests.exceptions.ConnectionError:
        yield "\n\n⚠️ **Connection error.** Check network access to api.anthropic.com."
    except Exception as exc:
        yield f"\n\n⚠️ **Unexpected error:** {exc}"


def _detect_chart_for_question(question: str, ctx: dict, df: pd.DataFrame) -> "go.Figure | None":
    q = question.lower()
    if _any_kw(q, ["anomaly", "anomalies", "unusual", "spike"]):
        return None
    if _any_kw(q, ["profitability matrix", "product quadrant", "star product"]):
        return _chart_top_products(ctx)
    if _any_kw(q, ["compare","vs","versus","against","city","region","where","location"]):
        return _chart_city_ranking(ctx)
    if _any_kw(q, ["category","segment"]):
        return _chart_revenue_by_category(ctx)
    if _any_kw(q, ["best product","top product","worst","lowest","product","sku","item"]):
        return _chart_top_products(ctx)
    if _any_kw(q, ["profit","margin","net"]):
        return _chart_profit_margin_by_category(ctx, df)
    if _any_kw(q, ["influencer","marketing","campaign"]):
        return _chart_influencer_lift(ctx, df)
    if _any_kw(q, ["orders","volume","order count"]):
        return _chart_orders_by_city(df)
    if _any_kw(q, ["discount","promo","offer","deal"]):
        return _chart_discount_curve(ctx)
    if _any_kw(q, ["summary","overview","revenue","earnings","how much"]):
        return _chart_summary_snapshot(ctx)
    if _any_kw(q, ["hello","hi","hey"]):
        return _chart_revenue_by_category(ctx)
    return None


# ══════════════════════════════════════════════════════════════════════════════════
# ── SHARED UI HELPERS
# ══════════════════════════════════════════════════════════════════════════════════

def page_header(title: str, subtitle: str):
    st.markdown(f"""
    <div class="page-header">
      <div class="page-kicker">NovaMS</div>
      <h1 class="page-title">{title}</h1>
      <p class="page-sub">{subtitle}</p>
    </div>
    """, unsafe_allow_html=True)


def narrative(html: str):
    st.markdown(f'<div class="narrative-box">{html}</div>', unsafe_allow_html=True)


def kpi_card(label: str, value: str, sub: str = "", delta: str = "", delta_positive: bool = True):
    """Render one flat, left-aligned KPI tile — no emoji, single ink color, optional delta pill."""
    delta_html = f'<div class="kpi-badge {"up" if delta_positive else "down"}">{delta}</div>' if delta else ""
    sub_html   = f'<div class="kpi-sub">{sub}</div>' if sub else ""
    st.markdown(f"""
    <div class="kpi-card">
      <div class="kpi-label">{label}</div>
      {delta_html}
      <div class="kpi-value">{value}</div>
      {sub_html}
    </div>""", unsafe_allow_html=True)


# ── Executive Overview KPI redesign — used ONLY by render_executive_overview().
# Every other page keeps calling kpi_card() above, completely unchanged. ──────

_NOVA_KPI_ICON_ATTRS = 'viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"'
_NOVA_KPI_ICONS = {
    "trending-up":  f'<svg {_NOVA_KPI_ICON_ATTRS}><polyline points="23 6 13.5 15.5 8.5 10.5 1 18"/><polyline points="17 6 23 6 23 12"/></svg>',
    "activity":     f'<svg {_NOVA_KPI_ICON_ATTRS}><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>',
    "shopping-bag": f'<svg {_NOVA_KPI_ICON_ATTRS}><path d="M6 2 3 6v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V6l-3-4Z"/><path d="M3 6h18"/><path d="M16 10a4 4 0 0 1-8 0"/></svg>',
    "percent":      f'<svg {_NOVA_KPI_ICON_ATTRS}><line x1="19" y1="5" x2="5" y2="19"/><circle cx="6.5" cy="6.5" r="2.5"/><circle cx="17.5" cy="17.5" r="2.5"/></svg>',
    "clock":        f'<svg {_NOVA_KPI_ICON_ATTRS}><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>',
    "map-pin":      f'<svg {_NOVA_KPI_ICON_ATTRS}><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0Z"/><circle cx="12" cy="10" r="3"/></svg>',
    "tag":          f'<svg {_NOVA_KPI_ICON_ATTRS}><path d="M20.59 13.41 11 3.83a2 2 0 0 0-1.41-.58H4a2 2 0 0 0-2 2v5.58c0 .53.21 1.04.59 1.42l9.58 9.59a2 2 0 0 0 2.82 0l6.6-6.6a2 2 0 0 0 0-2.83Z"/><circle cx="7.5" cy="7.5" r="1.5"/></svg>',
    "receipt":      f'<svg {_NOVA_KPI_ICON_ATTRS}><path d="M4 2h16v20l-2.5-1.5L15 22l-2.5-1.5L10 22l-2.5-1.5L5 22l-1-1V2Z"/><line x1="8" y1="7" x2="16" y2="7"/><line x1="8" y1="11" x2="16" y2="11"/></svg>',
    "truck":        f'<svg {_NOVA_KPI_ICON_ATTRS}><rect x="1" y="3" width="14" height="13"/><path d="M15 8h4l3 3v5h-7V8Z"/><circle cx="5.5" cy="18.5" r="2.5"/><circle cx="17.5" cy="18.5" r="2.5"/></svg>',
}


def _nova_sparkline_svg(values, color: str, width: int = 46, height: int = 26) -> str:
    """Small inline-SVG sparkline built from real per-row values already in the
    filtered dataframe — no synthetic/random data. Downsamples to <=24 points
    for a clean line on larger datasets."""
    vals = [float(v) for v in values if pd.notna(v)]
    if len(vals) < 2:
        return ""
    max_pts = 24
    if len(vals) > max_pts:
        step = len(vals) / max_pts
        vals = [vals[int(i * step)] for i in range(max_pts)]
    lo, hi = min(vals), max(vals)
    span = (hi - lo) or 1.0
    n = len(vals)
    pts = [
        ((i / (n - 1)) * width, height - ((v - lo) / span) * (height - 6) - 3)
        for i, v in enumerate(vals)
    ]
    line_d = "M " + " L ".join(f"{x:.1f} {y:.1f}" for x, y in pts)
    area_d = f"{line_d} L {width} {height} L 0 {height} Z"
    path_len = int(width * 1.5)
    return (
        f'<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" preserveAspectRatio="none">'
        f'<path d="{area_d}" fill="{color}" fill-opacity="0.12" stroke="none"/>'
        f'<path class="line" d="{line_d}" fill="none" stroke="{color}" stroke-width="1.6" '
        f'stroke-linecap="round" stroke-linejoin="round" '
        f'style="stroke-dasharray:{path_len};stroke-dashoffset:{path_len}"/>'
        f'</svg>'
    )


_NOVA_KPI_ACCENTS = {
    # (chip background, chip foreground — CSS var(), safe in plain CSS)  (literal hex — used inside raw SVG attributes)
    "blue":   ("var(--nova-blue-tint)",  "var(--nova-blue)",  "#1D4DFF"),
    "green":  ("var(--nova-green-tint)", "var(--nova-green)", "#22C55E"),
    "amber":  ("var(--nova-amber-tint)", "var(--nova-amber)", "#D97706"),
    "red":    ("var(--nova-red-tint)",   "var(--nova-red)",   "#EF4444"),
    "violet": ("rgba(139,92,246,.14)",   "#8b5cf6",            "#8b5cf6"),
}


def kpi_card_v2(label: str, value: str, icon: str, sub_lines: list[str] | None = None,
                 badge_text: str = "", badge_kind: str = "neutral", accent: str = "blue",
                 spark_values=None, ring_pct: float | None = None, delay: float = 0.0):
    """
    Restrained, enterprise-style KPI tile for the Executive Overview page only:
    colored icon chip + label -> optional status/delta badge -> large value ->
    supporting context, with an optional real-data sparkline or percentage
    ring, and a subtle grow-in animation on load. No gradients/glow, and no
    fabricated data — sparklines/rings only render when real values are given.
    """
    icon_svg = _NOVA_KPI_ICONS.get(icon, "")
    chip_bg, chip_fg, hex_color = _NOVA_KPI_ACCENTS.get(accent, _NOVA_KPI_ACCENTS["blue"])
    badge_html = f'<div class="nova-kpi-badge {badge_kind}">{badge_text}</div>' if badge_text else ""
    sub_html   = "".join(f'<div class="nova-kpi-sub">{s}</div>' for s in (sub_lines or []) if s)

    visual_html = ""
    if spark_values is not None:
        spark_svg = _nova_sparkline_svg(spark_values, hex_color)
        if spark_svg:
            visual_html = f'<div class="nova-kpi-spark">{spark_svg}</div>'
    if not visual_html and ring_pct is not None:
        pct = max(0.0, min(100.0, ring_pct))
        visual_html = (
            f'<div class="nova-kpi-ring-wrap">'
            f'<div class="nova-kpi-ring" style="--ring-pct:{pct:.1f}; --ring-color:{hex_color}">'
            f'<div class="nova-kpi-ring-inner">{pct:.0f}%</div>'
            f'</div></div>'
        )

    st.markdown(f"""
    <div class="nova-kpi-card" style="--kpi-delay:{delay:.2f}s">
      <div class="nova-kpi-top">
        <span class="nova-kpi-icon-chip" style="--chip-bg:{chip_bg}; --chip-fg:{chip_fg}">{icon_svg}</span>
        <span class="nova-kpi-label">{label}</span>
      </div>
      {badge_html}
      <div class="nova-kpi-body">
        <div class="nova-kpi-text">
          <div class="nova-kpi-value">{value}</div>
          {sub_html}
        </div>
        {visual_html}
      </div>
      <div class="nova-kpi-growbar" style="--bar-color:{chip_fg}"></div>
    </div>""", unsafe_allow_html=True)


def missing_data_notice(missing_cols: list[str], context: str):
    st.markdown(f"""
    <div class="missing-box">
      ⚠️ <b>Limited data for {context}.</b> Your uploaded file doesn't include: {", ".join(f"<code>{c}</code>" for c in missing_cols)}.
      This section only shows analytics that can be computed honestly from the columns you do have —
      nothing below is simulated to fill the gap.
    </div>
    """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════════
# ── SALES BY LOCATION — GEOGRAPHIC MAP  (additive only)
# New, self-contained visualization. Does not modify any existing calculation,
# filter, chart, or session-state logic — it only reads the already-filtered
# `df` that every other page already uses, and reuses fmt() / CITY_CLR for
# consistent formatting and color language.
# ══════════════════════════════════════════════════════════════════════════════════

# Approximate lat/lon for major Indian cities, used only to place bubbles on
# the map. Any city name in the data that isn't in this list is skipped
# gracefully (shown as a small note under the map) rather than crashing.
INDIA_CITY_COORDS = {
    "Delhi": (28.6139, 77.2090), "New Delhi": (28.6139, 77.2090),
    "Mumbai": (19.0760, 72.8777), "Bangalore": (12.9716, 77.5946),
    "Bengaluru": (12.9716, 77.5946), "Hyderabad": (17.3850, 78.4867),
    "Chennai": (13.0827, 80.2707), "Pune": (18.5204, 73.8567),
    "Kolkata": (22.5726, 88.3639), "Ahmedabad": (23.0225, 72.5714),
    "Jaipur": (26.9124, 75.7873), "Surat": (21.1702, 72.8311),
    "Lucknow": (26.8467, 80.9462), "Kanpur": (26.4499, 80.3319),
    "Nagpur": (21.1458, 79.0882), "Indore": (22.7196, 75.8577),
    "Bhopal": (23.2599, 77.4126), "Patna": (25.5941, 85.1376),
    "Chandigarh": (30.7333, 76.7794), "Gurgaon": (28.4595, 77.0266),
    "Gurugram": (28.4595, 77.0266), "Noida": (28.5355, 77.3910),
    "Kochi": (9.9312, 76.2673), "Cochin": (9.9312, 76.2673),
    "Coimbatore": (11.0168, 76.9558), "Visakhapatnam": (17.6868, 83.2185),
    "Vadodara": (22.3072, 73.1812), "Ludhiana": (30.9010, 75.8573),
    "Agra": (27.1767, 78.0081), "Nashik": (19.9975, 73.7898),
    "Ranchi": (23.3441, 85.3096), "Guwahati": (26.1445, 91.7362),
    "Bhubaneswar": (20.2961, 85.8245), "Thiruvananthapuram": (8.5241, 76.9366),
    "Amritsar": (31.6340, 74.8723), "Varanasi": (25.3176, 82.9739),
    "Faridabad": (28.4089, 77.3178), "Meerut": (28.9845, 77.7064),
    "Rajkot": (22.3039, 70.8022), "Jodhpur": (26.2389, 73.0243),
    "Madurai": (9.9252, 78.1198), "Raipur": (21.2514, 81.6296),
    "Dehradun": (30.3165, 78.0322), "Mysore": (12.2958, 76.6394),
    "Mysuru": (12.2958, 76.6394),
}


def _aggregate_city_metrics(filtered_df: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    """Group the already-filtered df by City into Revenue/Orders/Profit/Margin,
    attach lat/lon from INDIA_CITY_COORDS, and split out any city names that
    can't be geocoded (returned separately so the page can note them without
    ever crashing on unknown/uncleaned city names)."""
    agg_cols = [c for c in ["Total Revenue", "Orders", "Profit"] if c in filtered_df.columns]
    agg = filtered_df.groupby("City")[agg_cols].sum().reset_index()
    if "Profit Margin" in filtered_df.columns:
        agg = agg.merge(
            filtered_df.groupby("City")["Profit Margin"].mean().reset_index(),
            on="City", how="left",
        )
    agg["_lat"] = agg["City"].map(lambda c: INDIA_CITY_COORDS.get(c, (None, None))[0])
    agg["_lon"] = agg["City"].map(lambda c: INDIA_CITY_COORDS.get(c, (None, None))[1])
    mappable = agg.dropna(subset=["_lat", "_lon"]).copy()
    unmapped = agg[agg["_lat"].isna()]["City"].tolist()
    return mappable, unmapped


def _build_sales_map_figure(mappable: pd.DataFrame, metric_col: str, metric_choice: str) -> go.Figure:
    """Builds the Scattergeo bubble map. Bubbles are colored by performance
    rank on the selected metric — green for the top city, red for the
    weakest, blue for everything in between — matching the same
    best/middle/worst color language _chart_city_ranking() already uses
    elsewhere in NovaMS, so the map reads consistently with the rest of the
    dashboard at a glance."""
    ranked = mappable.sort_values(metric_col, ascending=False).reset_index(drop=True)
    rank_of = {row["City"]: i for i, row in ranked.iterrows()}
    n = len(ranked)

    def _rank_color(city: str) -> str:
        r = rank_of.get(city, 0)
        if r == 0:          return "#22C55E"   # top performer
        if r == n - 1 and n > 1: return "#EF4444"   # weakest
        return "#1D4DFF"                        # everyone else

    max_val  = float(mappable[metric_col].clip(lower=0).max()) or 1.0
    size_ref = 2.0 * max_val / (50.0 ** 2)  # keeps the largest bubble ~50px, scales the rest proportionally
    metric_total = float(mappable[metric_col].clip(lower=0).sum()) or 1.0

    def _hover_line(row) -> str:
        rank = rank_of.get(row["City"], 0) + 1
        share = max(0.0, row[metric_col]) / metric_total * 100
        parts = [f"<b>#{rank} {row['City']}</b> — {share:.1f}% of total {metric_choice.lower()}"]
        if "Total Revenue" in mappable.columns:
            parts.append(f"Revenue: {fmt(row['Total Revenue'])}")
        if "Orders" in mappable.columns:
            parts.append(f"Orders: {int(row['Orders']):,}")
        if "Profit" in mappable.columns:
            parts.append(f"Profit: {fmt(row['Profit'])}")
        if "Profit Margin" in mappable.columns and pd.notna(row.get("Profit Margin")):
            parts.append(f"Margin: {row['Profit Margin']:.1f}%")
        return "<br>".join(parts)

    hover_text = [_hover_line(row) for _, row in mappable.iterrows()]

    fig = go.Figure()

    # Soft outer glow ring beneath each bubble — same marker positions at a
    # larger, translucent size, purely decorative, adds map depth without
    # any new data or extra hover targets (hoverinfo is disabled on this trace).
    fig.add_trace(go.Scattergeo(
        lat=mappable["_lat"], lon=mappable["_lon"], hoverinfo="skip", mode="markers",
        marker=dict(
            size=mappable[metric_col].clip(lower=0), sizemode="area",
            sizeref=size_ref * 0.55, sizemin=10,
            color=[_rank_color(c) for c in mappable["City"]],
            opacity=0.18, line=dict(width=0),
        ),
        showlegend=False,
    ))
    fig.add_trace(go.Scattergeo(
        lat=mappable["_lat"], lon=mappable["_lon"],
        text=hover_text, hoverinfo="text", hoverlabel=dict(bgcolor="#14171C", font=dict(color="#F1F5F9", size=12)),
        mode="markers+text",
        textposition="top center",
        texttemplate=[f"<b>{c}</b>" for c in mappable["City"]],
        textfont=dict(size=10, color="#F1F5F9", family="Inter"),
        marker=dict(
            size=mappable[metric_col].clip(lower=0),
            sizemode="area", sizeref=size_ref, sizemin=8,
            color=[_rank_color(c) for c in mappable["City"]],
            line=dict(width=1.5, color="rgba(255,255,255,.45)"),
            opacity=0.92,
        ),
        showlegend=False,
    ))

    fig.update_geos(
        scope="asia", resolution=50,
        lataxis_range=[6, 36], lonaxis_range=[66, 98],
        showcountries=True, countrycolor="rgba(255,255,255,.18)",
        showsubunits=True, subunitcolor="rgba(255,255,255,.10)",
        showland=True, landcolor="#14171C",
        showocean=True, oceancolor="#0A0C0F",
        showlakes=False, showcoastlines=True, coastlinecolor="rgba(255,255,255,.12)",
        bgcolor="rgba(0,0,0,0)",
    )
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter", color="#9AA4B2", size=11),
        margin=dict(l=0, r=0, t=10, b=0), height=520,
        title=dict(text=f"{metric_choice} by City", font=dict(color="#F1F5F9", size=12)),
    )
    return fig


def _classify_profitability_quadrant(revenue: float, margin: float, median_rev: float, median_margin: float) -> str:
    """Classifies a product into a quadrant using median splits on Revenue
    and Profit Margin — a standard, data-driven way to label performance
    without inventing thresholds."""
    high_rev = revenue >= median_rev
    high_mgn = margin >= median_margin
    if high_rev and high_mgn:   return "Star"
    if high_rev and not high_mgn: return "Volume Driver"
    if not high_rev and high_mgn: return "Growth Opportunity"
    return "Review"


_QUADRANT_COLORS = {
    "Star": "#22C55E", "Volume Driver": "#1D4DFF",
    "Growth Opportunity": "#D97706", "Review": "#EF4444",
}


def render_product_analytics():
    """
    Dedicated 'Product Analytics' page. Reuses the already-filtered `df`
    (every sidebar filter applies automatically), fmt(), and CAT_CLR for
    visual consistency. Two components: a metric-switchable Top Products
    ranking, and a Revenue-vs-Margin Profitability Matrix with quadrant
    classification — both computed purely from existing Revenue/Profit/
    Orders/Profit Margin columns, nothing fabricated. No existing page,
    calculation, or filter is touched by this function.
    """
    page_header("Product Analytics", "Top Performers · Profitability Matrix")

    if df is None or df.empty or "Product Name" not in df.columns:
        st.info("No product data available for the current filter selection.")
        return

    prod_agg = df.groupby("Product Name").agg(
        Revenue=("Total Revenue", "sum"), Profit=("Profit", "sum"), Orders=("Orders", "sum"),
    )
    prod_agg["Margin"] = np.where(prod_agg["Revenue"] > 0, prod_agg["Profit"] / prod_agg["Revenue"] * 100, 0)
    if "Category" in df.columns:
        prod_agg = prod_agg.join(df.groupby("Product Name")["Category"].agg(lambda s: s.mode().iloc[0]))

    narrative(
        f"<b>What's happening:</b> {len(prod_agg)} distinct products are active in the current view. "
        f"<b>What to do:</b> switch the metric below to see rankings shift, then check the Profitability "
        f"Matrix to spot which top-sellers are also genuinely profitable."
    )

    st.markdown('<div class="section-head">Top Products</div>', unsafe_allow_html=True)
    _prod_metric = st.radio(
        "Ranking Metric", ["Revenue", "Profit", "Orders", "Margin"],
        horizontal=True, key="prod_rank_metric", label_visibility="collapsed",
    )
    top10 = prod_agg.sort_values(_prod_metric, ascending=False).head(10).sort_values(_prod_metric)
    is_pct = _prod_metric == "Margin"
    fig = go.Figure(go.Bar(
        x=top10[_prod_metric], y=top10.index.tolist(), orientation="h",
        marker=dict(color=top10[_prod_metric], colorscale=[[0,"#312e81"],[0.5,"#6366f1"],[1,"#06b6d4"]], showscale=False),
        marker_line_width=0,
        text=[f"{v:.1f}%" for v in top10[_prod_metric]] if is_pct else [fmt(v) for v in top10[_prod_metric]],
        textposition="outside", textfont=dict(color="#F1F5F9", size=10),
    ))
    fig.update_layout(**PLOTLY_BASE,
        title=dict(text=f"Top 10 Products by {_prod_metric}", font=dict(color="#1D4DFF", size=13)),
        height=340, xaxis=dict(ticksuffix="%" if is_pct else "", tickprefix="" if is_pct else "₹", **_AXIS_DEFAULTS),
        showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

    st.markdown('<div class="section-head">Profitability Matrix</div>', unsafe_allow_html=True)
    st.caption("Revenue (x-axis) vs. Profit Margin (y-axis) — quadrants split at the median of each.")
    median_rev = prod_agg["Revenue"].median()
    median_mgn = prod_agg["Margin"].median()
    prod_agg["Quadrant"] = prod_agg.apply(
        lambda r: _classify_profitability_quadrant(r["Revenue"], r["Margin"], median_rev, median_mgn), axis=1
    )
    fig = go.Figure()
    for q, clr in _QUADRANT_COLORS.items():
        sub = prod_agg[prod_agg["Quadrant"] == q]
        if sub.empty:
            continue
        fig.add_trace(go.Scatter(
            x=sub["Revenue"], y=sub["Margin"], mode="markers", name=q,
            marker=dict(size=np.clip(sub["Orders"] / max(1, prod_agg["Orders"].max()) * 40 + 6, 6, 46),
                        color=clr, opacity=0.75, line=dict(width=1, color="rgba(255,255,255,.35)")),
            text=sub.index, customdata=np.stack([sub["Orders"], sub["Profit"]], axis=-1),
            hovertemplate="<b>%{text}</b><br>Revenue: ₹%{x:,.0f}<br>Margin: %{y:.1f}%<br>"
                          "Orders: %{customdata[0]:,.0f}<br>Profit: ₹%{customdata[1]:,.0f}<extra></extra>",
        ))
    fig.add_vline(x=median_rev, line_dash="dash", line_color="rgba(255,255,255,.2)")
    fig.add_hline(y=median_mgn, line_dash="dash", line_color="rgba(255,255,255,.2)")
    fig.update_layout(**PLOTLY_BASE,
        title=dict(text="Revenue vs. Profit Margin by Product", font=dict(color="#1D4DFF", size=13)),
        height=420, xaxis=dict(title="Revenue (₹)", tickprefix="₹", **_AXIS_DEFAULTS),
        yaxis=dict(title="Profit Margin (%)", ticksuffix="%", **_AXIS_DEFAULTS),
        legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(size=10)))
    st.plotly_chart(fig, use_container_width=True)

    q_counts = prod_agg["Quadrant"].value_counts()
    stars = prod_agg[prod_agg["Quadrant"] == "Star"].sort_values("Revenue", ascending=False)
    review = prod_agg[prod_agg["Quadrant"] == "Review"].sort_values("Revenue")
    insight_lines = [
        f"<b>{q_counts.get('Star', 0)} Star</b> product(s) combine above-median revenue and margin — your best all-round performers"
        + (f", led by <b>{stars.index[0]}</b>." if len(stars) else "."),
        f"<b>{q_counts.get('Volume Driver', 0)} Volume Driver(s)</b> sell well but sit below the median margin — good for reach, thinner on profit.",
        f"<b>{q_counts.get('Growth Opportunity', 0)} Growth Opportunity(ies)</b> have strong margins but low volume — candidates for wider distribution.",
        f"<b>{q_counts.get('Review', 0)} product(s)</b> sit below median on both revenue and margin"
        + (f", starting with <b>{review.index[0]}</b> — worth a pricing or delisting review." if len(review) else "."),
    ]
    st.markdown('<div class="section-head">AI Insight</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="narrative-box">' + "<br>".join(insight_lines) + "</div>",
        unsafe_allow_html=True,
    )

    st.markdown('<div class="section-head">Product Detail</div>', unsafe_allow_html=True)
    detail_cols = ["Category", "Revenue", "Profit", "Orders", "Margin", "Quadrant"] if "Category" in prod_agg.columns \
                  else ["Revenue", "Profit", "Orders", "Margin", "Quadrant"]
    detail = prod_agg[detail_cols].sort_values("Revenue", ascending=False).reset_index()
    detail["Revenue"] = detail["Revenue"].map(fmt)
    detail["Profit"]  = detail["Profit"].map(fmt)
    detail["Orders"]  = detail["Orders"].map(lambda v: f"{int(v):,}")
    detail["Margin"]  = detail["Margin"].map(lambda v: f"{v:.1f}%")
    st.dataframe(detail, use_container_width=True, height=min(420, 46 + 38 * len(detail)), hide_index=True)


def render_sales_by_location():
    """
    Dedicated 'Sales by Location' page — its own nav item, separate from
    every other page. Reuses the already-filtered `df` (so every existing
    sidebar filter applies automatically), fmt(), CITY_CLR-style rank
    coloring, page_header()/narrative()/kpi_card() for visual consistency,
    and INDIA_CITY_COORDS / the map builders above. No existing page,
    calculation, filter, or chart is touched by this function.
    """
    page_header("Sales by Location", "Where are we generating the most business?")

    if df is None or df.empty or "City" not in df.columns:
        st.info("No location data available for the current filter selection.")
        return

    metric_choice = st.selectbox("Map metric", ["Revenue", "Orders", "Profit"], key="sales_map_metric")
    metric_col = {"Revenue": "Total Revenue", "Orders": "Orders", "Profit": "Profit"}[metric_choice]
    if metric_col not in df.columns:
        st.info(f"'{metric_choice}' isn't available in the current dataset.")
        return

    mappable, unmapped = _aggregate_city_metrics(df)
    if mappable.empty:
        st.info(
            "None of the cities in the current filter could be plotted on the map — their "
            "names aren't recognized as known Indian city locations yet."
        )
        return

    ranked  = mappable.sort_values(metric_col, ascending=False).reset_index(drop=True)
    best    = ranked.iloc[0]
    weakest = ranked.iloc[-1]
    gap_pct = ((best[metric_col] - weakest[metric_col]) / weakest[metric_col] * 100
               if len(ranked) > 1 and weakest[metric_col] > 0 else 0)

    narrative(
        f"<b>What's happening:</b> <b>{best['City']}</b> leads on {metric_choice.lower()} at "
        f"<b>{fmt(best[metric_col]) if metric_col != 'Orders' else f'{int(best[metric_col]):,}'}</b>, "
        f"while <b>{weakest['City']}</b> trails by <b>{gap_pct:.0f}%</b>. "
        f"<b>What to do:</b> replicate {best['City']}'s playbook in {weakest['City']} — start with its "
        f"top category and any active influencer campaigns."
    )

    k1, k2, k3, k4 = st.columns(4)
    with k1: kpi_card("Locations Mapped", f"{len(mappable)}")
    with k2: kpi_card("Top Location", best["City"], fmt(best[metric_col]) if metric_col != "Orders" else f"{int(best[metric_col]):,} orders")
    with k3: kpi_card("Weakest Location", weakest["City"], fmt(weakest[metric_col]) if metric_col != "Orders" else f"{int(weakest[metric_col]):,} orders")
    with k4: kpi_card("Performance Gap", f"{gap_pct:.0f}%", "Best vs. weakest")

    st.markdown("<br>", unsafe_allow_html=True)

    map_col, panel_col = st.columns([7, 3])
    with map_col:
        fig = _build_sales_map_figure(mappable, metric_col, metric_choice)
        st.plotly_chart(fig, use_container_width=True)
        st.caption(
            f"🟢 Top city · 🔵 Mid-range · 🔴 Weakest — bubble size scales with {metric_choice.lower()}. "
            f"Hover any bubble for rank, share of total, and the full metric breakdown."
        )
        if unmapped:
            st.caption(f"Not shown on map (unrecognized location): {', '.join(unmapped)}")
    with panel_col:
        st.markdown("""
        <div style="background:#14171C;border:1px solid #262B33;box-shadow:0 1px 2px rgba(0,0,0,.35);border-radius:12px;padding:16px">
          <div style="font-size:10px;font-weight:600;color:#1D4DFF;text-transform:uppercase;letter-spacing:.08em;margin-bottom:12px">
            🏆 Location Leaderboard
          </div>
        """, unsafe_allow_html=True)
        max_v = float(ranked[metric_col].clip(lower=0).max()) or 1.0
        medals = ["🥇", "🥈", "🥉"] + ["▫️"] * max(0, len(ranked) - 3)
        for i, row in ranked.iterrows():
            val_disp = fmt(row[metric_col]) if metric_col != "Orders" else f"{int(row[metric_col]):,}"
            bar_w = max(4, int(row[metric_col] / max_v * 100))
            clr = "#22C55E" if i == 0 else "#EF4444" if i == len(ranked) - 1 and len(ranked) > 1 else "#1D4DFF"
            st.markdown(f"""
            <div style="margin-bottom:10px">
              <div style="display:flex;justify-content:space-between;margin-bottom:3px">
                <span style="font-size:11px;color:#F1F5F9">{medals[i]} {row['City']}</span>
                <span style="font-size:10px;font-weight:600;color:{clr};font-family:monospace">{val_disp}</span>
              </div>
              <div style="background:rgba(99,130,255,.08);border-radius:4px;height:5px">
                <div style="width:{bar_w}%;background:{clr};height:5px;border-radius:4px"></div>
              </div>
            </div>
            """, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="section-head">Location Detail</div>', unsafe_allow_html=True)
    table_cols  = ["City"] + [c for c in ["Total Revenue", "Orders", "Profit", "Profit Margin"] if c in ranked.columns]
    display_tbl = ranked[table_cols].copy()
    if "Total Revenue" in display_tbl.columns:
        display_tbl["Total Revenue"] = display_tbl["Total Revenue"].map(fmt)
    if "Profit" in display_tbl.columns:
        display_tbl["Profit"] = display_tbl["Profit"].map(fmt)
    if "Profit Margin" in display_tbl.columns:
        display_tbl["Profit Margin"] = display_tbl["Profit Margin"].map(lambda v: f"{v:.1f}%")
    if "Orders" in display_tbl.columns:
        display_tbl["Orders"] = display_tbl["Orders"].map(lambda v: f"{int(v):,}")
    st.dataframe(display_tbl, use_container_width=True, height=min(360, 46 + 38 * len(display_tbl)), hide_index=True)


def render_data_trust_center():
    """Full-page 'Data Import & Trust Center' — shown only while an uploaded
    file is staged for review. Nothing here touches the active dashboard
    dataset until the user explicitly clicks Import."""
    raw_df   = st.session_state["_staged_raw_df"]
    filename = st.session_state["_staged_filename"]

    page_header("Data Import & Trust Center", f'Reviewing "{filename}" — nothing is applied until you import it')

    size_kb = raw_df.memory_usage(deep=True).sum() / 1024
    m1, m2, m3, m4 = st.columns(4)
    with m1: kpi_card("File", filename)
    with m2: kpi_card("Rows", f"{len(raw_df):,}")
    with m3: kpi_card("Columns", f"{len(raw_df.columns)}")
    with m4: kpi_card("Est. Size", f"{size_kb:,.0f} KB")

    colmap        = suggest_column_mapping(list(raw_df.columns))
    compat        = dataset_compatibility_report(raw_df, colmap)
    strict_missing = [c for c in REQUIRED_COLUMNS if c not in raw_df.columns]
    findings      = compute_data_quality_findings(raw_df)
    trust         = compute_trust_score(raw_df, findings, compat)
    status_clr    = {"Excellent": "#22C55E", "Good": "#22C55E", "Needs Review": "#D97706", "Poor Quality": "#EF4444"}[trust["status"]]

    st.markdown('<div class="section-head">Data Trust Score</div>', unsafe_allow_html=True)
    st.markdown(f"""
    <div style="background:#14171C;border:1px solid #262B33;border-left:4px solid {status_clr};border-radius:10px;padding:18px 20px;margin-bottom:14px">
      <div style="display:flex;align-items:baseline;gap:10px">
        <div style="font-size:34px;font-weight:800;color:{status_clr}">{trust['score']}</div>
        <div style="font-size:13px;color:#9AA4B2">/100 — <b style="color:{status_clr}">{trust['status']}</b></div>
      </div>
      <div style="margin-top:8px;font-size:12.5px;color:#9AA4B2">Main issue: {trust['main_issue']}</div>
    </div>
    """, unsafe_allow_html=True)

    sc1, sc2, sc3, sc4 = st.columns(4)
    for col, label, val in [
        (sc1, "Completeness", trust["sub_scores"]["completeness"]), (sc2, "Validity", trust["sub_scores"]["validity"]),
        (sc3, "Consistency",  trust["sub_scores"]["consistency"]),  (sc4, "Uniqueness", trust["sub_scores"]["uniqueness"]),
    ]:
        with col: kpi_card(label, f"{max(0, val) * 100:.0f}%")

    st.markdown('<div class="section-head">Dataset Compatibility</div>', unsafe_allow_html=True)
    if compat["can_import"]:
        narrative(f"✓ All required columns detected{' (via smart mapping below)' if colmap else ''}. This dataset can fully power NovaMS's calculations.")
    else:
        st.markdown(
            f'<div class="missing-box">✕ This dataset cannot fully support the current dashboard because '
            f'{", ".join(compat["required_missing"])} column(s) are missing or unrecognized. '
            f'Import stays disabled until they\'re present or mapped.</div>', unsafe_allow_html=True,
        )
    cc1, cc2 = st.columns(2)
    with cc1:
        st.markdown(f"**✓ Required columns detected** ({len(compat['required_detected'])}/{len(REQUIRED_COLUMNS)})")
        st.caption(", ".join(compat["required_detected"]) or "None")
        if compat["required_missing"]:
            st.markdown("**✕ Critical columns missing**")
            st.caption(", ".join(compat["required_missing"]))
    with cc2:
        st.markdown(f"**⚠ Optional columns detected** ({len(compat['optional_detected'])}/{len(compat['optional_detected']) + len(compat['optional_missing'])})")
        st.caption("Unlock extra detail on the Delivery Analytics and Operations pages — the dashboard works fine without them.")

    st.markdown('<div class="section-head">Preview</div>', unsafe_allow_html=True)
    st.dataframe(raw_df.head(20), use_container_width=True, height=320)
    with st.expander(f"Columns & data types ({len(raw_df.columns)})"):
        dt_df = raw_df.dtypes.astype(str).reset_index()
        dt_df.columns = ["Column", "Type"]
        st.dataframe(dt_df, use_container_width=True, height=min(300, 40 + 32 * len(dt_df)))

    st.markdown('<div class="section-head">Smart Cleaning Suggestions</div>', unsafe_allow_html=True)
    suggestions = generate_cleaning_suggestions(findings, colmap)
    selected_ids = set()
    if suggestions:
        for s in suggestions:
            if st.checkbox(s["label"], value=s["default"], key=f"fix_{s['id']}", help=s["detail"]):
                selected_ids.add(s["id"])
    else:
        st.caption("No issues detected — this dataset looks clean.")

    st.markdown('<div class="section-head">Import</div>', unsafe_allow_html=True)
    mode = st.radio("Import mode", ["Replace Current Dataset", "Add to Current Dataset"], horizontal=True, key="import_mode")

    _db_conn_for_save = get_db_connection()
    save_to_db = False
    if _db_conn_for_save is not None:
        save_to_db = st.checkbox("💾 Also save this import to the database (persists across sessions)", value=False, key="save_to_db_checkbox")
    else:
        st.caption("💡 Connect a PostgreSQL database (see sidebar → Database) to save imports permanently.")

    b1, b2, b3 = st.columns(3)
    with b1:
        apply_clicked = st.button(
            "Apply Recommended Fixes & Import", type="primary", use_container_width=True,
            disabled=not compat["can_import"],
        )
    with b2:
        raw_clicked = st.button("Import Without Fixing", use_container_width=True, disabled=bool(strict_missing))
    with b3:
        cancel_clicked = st.button("Cancel — Keep Current Dataset", use_container_width=True)

    if apply_clicked or raw_clicked:
        ids = selected_ids if apply_clicked else ({"colmap"} if colmap else set())
        cleaned_raw, log = apply_cleaning_suggestions(raw_df, ids, colmap, findings)
        try:
            _validate_columns(cleaned_raw, filename)
            cleaned = clean(cleaned_raw)
        except ValueError as e:
            st.error(f"❌ {e}")
            return

        if mode == "Add to Current Dataset":
            base    = st.session_state.get("_active_df_raw")
            base    = base if base is not None else load_default()
            cleaned = pd.concat([base, cleaned], ignore_index=True)

        new_trust = compute_trust_score(cleaned_raw, compute_data_quality_findings(cleaned_raw), compat)
        meta = dict(
            name=filename, source=("Cleaned Dataset" if ids else "User Uploaded Dataset"),
            rows=len(cleaned), trust_score=new_trust["score"], status=new_trust["status"],
        )
        st.session_state["_active_df_raw"] = cleaned
        st.session_state["_active_dataset_meta"] = meta
        record_dataset_version(
            label="Cleaned Import" if ids else "Original Upload",
            rows=len(cleaned), note="; ".join(log) if log else "Imported as-is",
        )

        db_note = ""
        if save_to_db and _db_conn_for_save is not None:
            if save_dataset_to_db(_db_conn_for_save, cleaned, meta):
                db_note = " and saved to the database"
            else:
                db_note = " (database save failed — see sidebar → Database for the error)"

        st.session_state["_show_trust_center"] = False
        st.session_state["_staged_raw_df"]     = None
        st.success(f"✅ Imported {len(cleaned):,} rows into NovaMS{db_note}.")
        st.rerun()

    if cancel_clicked:
        st.session_state["_show_trust_center"] = False
        st.session_state["_staged_raw_df"]     = None
        st.rerun()


# ══════════════════════════════════════════════════════════════════════════════════
# ── BOX PLOT ANALYSIS  (additive — new page, does not touch anything above)
# Reuses the already-filtered `df` from the rest of NovaMS, so it stays in
# sync with the sidebar filters, uploaded dataset, and everything else.
# ══════════════════════════════════════════════════════════════════════════════════

def _inject_boxplot_css():
    st.markdown("""
    <style>
    @keyframes bpFadeIn {
      from { opacity: 0; transform: translateY(8px); }
      to   { opacity: 1; transform: translateY(0); }
    }
    .bp-section { animation: bpFadeIn .45s ease-out; }
    .bp-card {
      background: var(--nova-card, #14171C);
      border: 1px solid var(--nova-border, #262B33);
      border-radius: 18px;
      padding: 18px 20px;
      transition: border-color .2s ease, transform .2s ease, box-shadow .2s ease;
    }
    .bp-card:hover {
      border-color: rgba(29,77,255,.35);
      box-shadow: 0 6px 22px rgba(29,77,255,.08);
      transform: translateY(-1px);
    }
    .bp-title { font-size: 15px; font-weight: 700; color: var(--nova-ink, #F1F5F9); display:flex; align-items:center; gap:8px; }
    .bp-subtitle { font-size: 12px; color: var(--nova-ink-soft, #9AA4B2); margin-top: 2px; margin-bottom: 14px; }
    .bp-stat-row {
      display: flex; justify-content: space-between; align-items: center;
      padding: 8px 10px; border-radius: 8px; margin-bottom: 5px;
      background: rgba(255,255,255,.02);
    }
    .bp-stat-label { font-size: 11.5px; color: var(--nova-ink-soft, #9AA4B2); }
    .bp-stat-value { font-size: 12px; font-weight: 700; font-family: 'SF Mono', monospace; }
    .bp-dot { display:inline-block; width:7px; height:7px; border-radius:50%; margin-right:7px; }
    .bp-blue  { background: #1D4DFF; }
    .bp-green { background: #22C55E; }
    .bp-red   { background: #EF4444; }
    .bp-insight-line {
      font-size: 12.5px; color: var(--nova-ink-soft, #9AA4B2); line-height: 1.75;
      padding-left: 18px; position: relative; margin-bottom: 4px;
    }
    .bp-insight-line::before {
      content: "✨"; position: absolute; left: 0; top: 0; font-size: 11px;
    }
    .bp-reco {
      margin-top: 10px; padding: 10px 14px; border-radius: 10px;
      background: rgba(29,77,255,.1); border-left: 3px solid #1D4DFF;
      font-size: 12.5px; color: var(--nova-ink, #F1F5F9); line-height: 1.6;
    }
    .bp-badge {
      display:inline-block; font-size:10px; font-weight:700; padding:2px 9px;
      border-radius: 20px; background: rgba(29,77,255,.12); color:#1D4DFF; margin-left:8px;
    }
    div[data-testid="stDownloadButton"] button, .bp-section .stButton>button {
      transition: transform .15s ease, box-shadow .15s ease;
    }
    div[data-testid="stDownloadButton"] button:hover, .bp-section .stButton>button:hover {
      transform: translateY(-1px); box-shadow: 0 4px 14px rgba(29,77,255,.25);
    }
    </style>
    """, unsafe_allow_html=True)


def _bp_numeric_columns(df: pd.DataFrame) -> list[str]:
    candidates = ["Total Revenue", "Profit", "Profit Margin", "Orders", "Discount",
                  "Original Price", "Current Price", "Delivery Time", "Delivery Cost"]
    present = [c for c in candidates if c in df.columns]
    other_numeric = [c for c in df.select_dtypes(include="number").columns if c not in present]
    return present + other_numeric


def _bp_groupby_columns(df: pd.DataFrame) -> list[str]:
    candidates = ["City", "Category", "Product Name", "Influencer Active",
                  "Delivery Partner", "Price Tier", "Customer Segment"]
    return [c for c in candidates if c in df.columns and df[c].nunique() > 1]


def compute_boxplot_stats(series: pd.Series) -> dict | None:
    """Overall distribution stats + 1.5xIQR outlier flags for one numeric column."""
    s = pd.to_numeric(series, errors="coerce").dropna()
    if len(s) == 0:
        return None
    q1, median, q3 = s.quantile([0.25, 0.5, 0.75])
    iqr = q3 - q1
    lo_fence = q1 - 1.5 * iqr
    hi_fence = q3 + 1.5 * iqr
    outlier_mask = (s < lo_fence) | (s > hi_fence)
    return dict(
        n=len(s), min=float(s.min()), max=float(s.max()), q1=float(q1), median=float(median),
        q3=float(q3), mean=float(s.mean()), std=float(s.std(ddof=1)) if len(s) > 1 else 0.0,
        variance=float(s.var(ddof=1)) if len(s) > 1 else 0.0, iqr=float(iqr),
        lo_fence=float(lo_fence), hi_fence=float(hi_fence),
        outlier_count=int(outlier_mask.sum()),
        outlier_pct=float(outlier_mask.sum() / len(s) * 100),
        skew=float(s.skew()) if len(s) > 2 else 0.0,
        outlier_index=s[outlier_mask].index,
    )


def _generate_boxplot_insights(stats_d: dict, column: str, group_by: str | None,
                                group_extreme: tuple | None) -> list[str]:
    lines = []
    lines.append(f"Median {column} is <b>{fmt(stats_d['median'])}</b>, representing the typical value.")
    skew_word = ("positively skewed (right-tailed)" if stats_d["skew"] > 0.3 else
                 "negatively skewed (left-tailed)" if stats_d["skew"] < -0.3 else "fairly symmetric")
    lines.append(f"The distribution is <b>{skew_word}</b> (skewness={stats_d['skew']:.2f}).")
    iqr_ratio = stats_d["iqr"] / stats_d["mean"] * 100 if stats_d["mean"] else 0
    variability = "high" if iqr_ratio > 60 else "moderate" if iqr_ratio > 25 else "low"
    lines.append(f"IQR of <b>{fmt(stats_d['iqr'])}</b> indicates <b>{variability} variability</b> around the median.")
    if group_extreme:
        g_name, g_std = group_extreme
        lines.append(f"<b>{g_name}</b> shows the highest variation among {group_by.lower()} groups (std={fmt(g_std)}).")
    lines.append(f"<b>{stats_d['outlier_pct']:.2f}%</b> of records ({stats_d['outlier_count']} rows) are statistical outliers (1.5×IQR rule).")
    lines.append(f"Most values fall between <b>{fmt(stats_d['q1'])}</b> and <b>{fmt(stats_d['q3'])}</b> (the middle 50%).")
    return lines


def _build_box_figure(df_in: pd.DataFrame, column: str, group_by: str | None,
                       show_only_outliers: bool, color_maps: dict) -> go.Figure:
    fig = go.Figure()
    color_map = color_maps.get(group_by, {}) if group_by else {}

    if group_by:
        counts = df_in.groupby(group_by)[column].count().sort_values(ascending=False)
        order = counts.head(15).index  # cap at 15 groups so the chart stays readable
        for i, g in enumerate(order):
            vals = pd.to_numeric(df_in.loc[df_in[group_by] == g, column], errors="coerce").dropna()
            if len(vals) == 0:
                continue
            clr = color_map.get(g, PAL[i % len(PAL)])
            fig.add_trace(go.Box(
                y=vals, name=str(g), marker_color=clr, line=dict(color=clr, width=1.5),
                boxpoints="outliers" if not show_only_outliers else "all",
                jitter=0.35, pointpos=0, marker=dict(size=4, opacity=0.75),
                whiskerwidth=0.6,
            ))
    else:
        vals = pd.to_numeric(df_in[column], errors="coerce").dropna()
        fig.add_trace(go.Box(
            y=vals, name=column, marker_color="#1D4DFF", line=dict(color="#1D4DFF", width=1.5),
            boxpoints="outliers" if not show_only_outliers else "all",
            jitter=0.35, pointpos=0, marker=dict(size=4, opacity=0.75), whiskerwidth=0.6,
        ))

    title = f"{column} Distribution" + (f" by {group_by}" if group_by else "")
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter", color="#9AA4B2", size=11),
        title=dict(text=title, font=dict(color="#F1F5F9", size=14)),
        height=440, margin=dict(l=10, r=10, t=50, b=10),
        yaxis=dict(gridcolor="rgba(255,255,255,.06)", linecolor="rgba(255,255,255,.09)"),
        xaxis=dict(gridcolor="rgba(255,255,255,.03)", linecolor="rgba(255,255,255,.09)"),
        showlegend=False,
    )
    return fig


def render_box_plot_analysis():
    """Box Plot Analysis page — reuses the globally filtered `df`."""
    _inject_boxplot_css()
    st.markdown('<div class="bp-section">', unsafe_allow_html=True)

    page_header("Box Plot Analysis", "Analyze data distribution, variability, and outliers")
    narrative(
        "<b>What this shows:</b> the spread, median, and outliers of any numeric metric — "
        "optionally broken down by city, category, product, or influencer status. "
        "<b>Why it matters:</b> outliers here often represent bulk orders, premium customers, "
        "or data-entry errors worth a closer look."
    )

    numeric_cols = _bp_numeric_columns(df)
    group_cols   = _bp_groupby_columns(df)

    if not numeric_cols:
        st.warning("No numeric columns available in the current (filtered) dataset.")
        st.markdown('</div>', unsafe_allow_html=True)
        return

    c1, c2, c3, c4 = st.columns([2, 2, 1.3, 1.5])
    with c1:
        column = st.selectbox("Numeric Column", numeric_cols, key="bp_numeric_col")
    with c2:
        group_choice = st.selectbox("Group By (Optional)", ["None"] + group_cols, key="bp_group_col")
        group_by = None if group_choice == "None" else group_choice
    with c3:
        st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
        show_only_outliers = st.checkbox("☑ Show Only Outliers", key="bp_show_outliers")
    with c4:
        st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
        download_slot = st.empty()

    # ── Validation ──────────────────────────────────────────────────────────
    if column not in df.columns or not pd.api.types.is_numeric_dtype(pd.to_numeric(df[column], errors="coerce")):
        st.error("⚠️ Selected column is not numeric.")
        st.markdown('</div>', unsafe_allow_html=True)
        return

    valid_n = pd.to_numeric(df[column], errors="coerce").dropna().shape[0]
    if valid_n < 5:
        st.warning("⚠️ Not enough data to generate a Box Plot (minimum 5 observations required).")
        st.markdown('</div>', unsafe_allow_html=True)
        return

    bp_stats = compute_boxplot_stats(df[column])

    group_extreme = None
    if group_by:
        g_std = df.groupby(group_by)[column].std(ddof=1).dropna()
        if len(g_std):
            top_g = g_std.idxmax()
            group_extreme = (top_g, float(g_std.loc[top_g]))

    color_maps = {"City": CITY_CLR, "Category": CAT_CLR}
    outlier_df = df.loc[df.index.intersection(bp_stats["outlier_index"])].copy()

    left, right = st.columns([7, 3])

    with left:
        st.markdown('<div class="bp-card">', unsafe_allow_html=True)
        fig = _build_box_figure(df, column, group_by, show_only_outliers, color_maps)
        st.plotly_chart(fig, use_container_width=True, key="bp_main_chart")
        st.markdown('</div>', unsafe_allow_html=True)

    with right:
        st.markdown(f"""
        <div class="bp-card">
          <div class="bp-title">📈 Distribution Summary <span class="bp-badge">{column}</span></div>
          <div class="bp-subtitle">Based on {bp_stats['n']:,} valid records</div>
        """, unsafe_allow_html=True)

        rows = [
            ("bp-green", "Minimum",   fmt(bp_stats["min"])),
            ("bp-green", "Q1 (25%)",  fmt(bp_stats["q1"])),
            ("bp-blue",  "Median (50%)", fmt(bp_stats["median"])),
            ("bp-green", "Q3 (75%)",  fmt(bp_stats["q3"])),
            ("bp-green", "Maximum",   fmt(bp_stats["max"])),
            ("bp-green", "Mean",      fmt(bp_stats["mean"])),
            ("bp-green", "Std Deviation", fmt(bp_stats["std"])),
            ("bp-green", "Variance",  fmt(bp_stats["variance"])),
            ("bp-green", "IQR (Q3−Q1)", fmt(bp_stats["iqr"])),
        ]
        for dot, label, val in rows:
            clr = "#1D4DFF" if dot == "bp-blue" else "#F1F5F9"
            st.markdown(
                f'<div class="bp-stat-row"><span class="bp-stat-label"><span class="bp-dot {dot}"></span>{label}</span>'
                f'<span class="bp-stat-value" style="color:{clr}">{val}</span></div>',
                unsafe_allow_html=True,
            )

        st.markdown(
            f'<div class="bp-stat-row" style="background:rgba(239,68,68,.08)">'
            f'<span class="bp-stat-label"><span class="bp-dot bp-red"></span>Outliers Detected</span>'
            f'<span class="bp-stat-value" style="color:#EF4444">{bp_stats["outlier_count"]}</span></div>'
            f'<div class="bp-stat-row" style="background:rgba(239,68,68,.08)">'
            f'<span class="bp-stat-label"><span class="bp-dot bp-red"></span>Outliers (%)</span>'
            f'<span class="bp-stat-value" style="color:#EF4444">{bp_stats["outlier_pct"]:.2f}%</span></div>',
            unsafe_allow_html=True,
        )
        st.markdown("</div>", unsafe_allow_html=True)

    csv_bytes = outlier_df.to_csv(index=False) if len(outlier_df) else "No outliers detected\n"
    with download_slot:
        st.download_button(
            "⬇ Download Outliers (CSV)", csv_bytes,
            file_name=f"novams_outliers_{column.replace(' ', '_').lower()}.csv",
            mime="text/csv", use_container_width=True, disabled=len(outlier_df) == 0,
        )

    st.markdown("<br>", unsafe_allow_html=True)

    ic1, ic2 = st.columns([1, 1])
    with ic1:
        insight_lines = _generate_boxplot_insights(bp_stats, column, group_by, group_extreme)
        st.markdown('<div class="bp-card">', unsafe_allow_html=True)
        st.markdown('<div class="bp-title">✨ AI Insights</div><br>', unsafe_allow_html=True)
        for line in insight_lines:
            st.markdown(f'<div class="bp-insight-line">{line}</div>', unsafe_allow_html=True)
        reco_subject = "high-value orders" if "Revenue" in column or "Profit" in column else f"unusual {column.lower()} values"
        st.markdown(
            f'<div class="bp-reco"><b>💡 Recommendation:</b> Investigate {reco_subject} for '
            f'{"upselling opportunities" if "Revenue" in column or "Profit" in column else "data quality or process review"} — '
            f'these {bp_stats["outlier_count"]} records sit outside the normal 1.5×IQR range.</div>',
            unsafe_allow_html=True,
        )
        st.markdown("</div>", unsafe_allow_html=True)

    with ic2:
        st.markdown('<div class="bp-card">', unsafe_allow_html=True)
        st.markdown(f'<div class="bp-title">🔎 Outlier Records <span class="bp-badge">{len(outlier_df)} total</span></div><br>',
                    unsafe_allow_html=True)
        if len(outlier_df) == 0:
            st.markdown('<div style="font-size:12px;color:#64748B;text-align:center;padding:24px">No outliers detected in this view.</div>', unsafe_allow_html=True)
        else:
            preferred_cols = ["Product Name", "City", column, "Category", "Date"]
            show_cols = [c for c in preferred_cols if c in outlier_df.columns]
            if column not in show_cols:
                show_cols.append(column)
            preview = outlier_df[show_cols].sort_values(column, ascending=False).head(5).reset_index(drop=True)
            preview.index = preview.index + 1
            st.dataframe(preview, use_container_width=True, height=210)

            if st.session_state.get("bp_view_all_outliers"):
                st.markdown("**All outliers:**")
                full = outlier_df[show_cols].sort_values(column, ascending=False).reset_index(drop=True)
                st.dataframe(full, use_container_width=True, height=320)
                if st.button("↑ Collapse", key="bp_collapse_outliers"):
                    st.session_state["bp_view_all_outliers"] = False
                    st.rerun()
            else:
                if st.button("View All Outliers →", key="bp_view_all_btn"):
                    st.session_state["bp_view_all_outliers"] = True
                    st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)  # close .bp-section


NAV_PAGES = [
    "Executive Overview",
    "Sales Analytics",
    "Box Plot Analysis",
    "Delivery Analytics",
    "Inventory Intelligence",
    "Operations",
    "Customer Analytics",
    "Finance",
    "AI Analyst",
    "Data Explorer",
    "Sales by Location",
    "Product Analytics",
    "Data Engine",
]


# ══════════════════════════════════════════════════════════════════════════════════
# ── SIDEBAR: BRAND · NAVIGATION · DATA SOURCE · FILTERS · SETTINGS · AI MODE
# ══════════════════════════════════════════════════════════════════════════════════

with st.sidebar:
    st.markdown("""
    <div class="nav-brand">
      <div class="logo">N</div>
      <div class="name">NovaMS</div>
      <div class="tag">Nova Management Solutions</div>
      <div class="caption">Enterprise Analytics Platform</div>
    </div>
    """, unsafe_allow_html=True)

    active_page = st.radio("Go to", NAV_PAGES, label_visibility="collapsed", key="nav_page")

    st.markdown("---")
    st.markdown("#### 📂 Data Source")

    _active_meta = st.session_state.get("_active_dataset_meta")
    _status_clr  = {"Excellent": "#22C55E", "Good": "#22C55E", "Needs Review": "#D97706", "Poor Quality": "#EF4444"}
    if _active_meta:
        st.markdown(f"""
        <div style="background:#14171C;border:1px solid #262B33;border-radius:10px;padding:12px 14px;margin-bottom:10px">
          <div style="font-size:9px;font-weight:700;color:#6B7688;text-transform:uppercase;letter-spacing:.08em;margin-bottom:6px">Active Dataset</div>
          <div style="font-size:13px;font-weight:700;color:#F1F5F9">{_active_meta['name']}</div>
          <div style="font-size:10.5px;color:#9AA4B2;margin-top:2px">Source: {_active_meta['source']} · {_active_meta['rows']:,} rows</div>
          <div style="margin-top:6px;font-size:10px;font-weight:700;color:{_status_clr.get(_active_meta['status'],'#9AA4B2')}">Trust Score: {_active_meta['trust_score']}/100 — {_active_meta['status']}</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("↩ Revert to Demo Dataset", use_container_width=True, key="revert_demo_btn"):
            st.session_state["_active_df_raw"] = None
            st.session_state["_active_dataset_meta"] = None
            record_dataset_version("Reverted to Demo Dataset", len(load_default()), "Manual revert")
            st.rerun()
    else:
        st.markdown("""
        <div style="background:#14171C;border:1px solid #262B33;border-radius:10px;padding:12px 14px;margin-bottom:10px">
          <div style="font-size:9px;font-weight:700;color:#6B7688;text-transform:uppercase;letter-spacing:.08em;margin-bottom:6px">Active Dataset</div>
          <div style="font-size:13px;font-weight:700;color:#F1F5F9">Demo Dataset</div>
          <div style="font-size:10.5px;color:#9AA4B2;margin-top:2px">Source: Built-in sample · no file uploaded yet</div>
        </div>
        """, unsafe_allow_html=True)

    uploaded = st.file_uploader(
        "Drag and drop CSV or Excel here",
        type=["csv", "xlsx"],
        help="Full preview, validation, and a Data Trust Score are shown before anything "
             "is imported — nothing changes until you confirm.",
        key="uploader_main",
    )

    if uploaded is not None:
        _sig = f"{uploaded.name}:{uploaded.size}"
        if st.session_state.get("_staged_upload_sig") != _sig:
            try:
                _raw = _read_uploaded_dataframe(uploaded)
                _raw.columns = [str(c).strip() for c in _raw.columns]
                if _raw.empty:
                    st.error("❌ The uploaded file is empty.")
                else:
                    st.session_state["_staged_raw_df"]     = _raw
                    st.session_state["_staged_filename"]   = uploaded.name
                    st.session_state["_staged_upload_sig"] = _sig
                    st.session_state["_show_trust_center"] = True
                    st.rerun()
            except ValueError as e:
                st.error(f"❌ {e}")
            except Exception:
                st.error("❌ This file does not contain readable data, or the format is not supported.")

    if st.session_state.get("_dataset_versions"):
        with st.expander(f"Dataset History ({len(st.session_state['_dataset_versions'])})"):
            for i, v in enumerate(st.session_state["_dataset_versions"], 1):
                note = f" · {v['note']}" if v.get("note") else ""
                st.markdown(
                    f"<div style='font-size:11px;color:#F1F5F9;font-weight:600;margin-top:4px'>Version {i} — {v['label']}</div>"
                    f"<div style='font-size:10px;color:#6B7688'>{v['rows']:,} rows{note}</div>",
                    unsafe_allow_html=True,
                )

    with st.expander("🗄️ Database (PostgreSQL)"):
        _db_conn = get_db_connection()
        if _db_conn is None:
            st.caption(
                "Not connected. Add a `[connections.postgresql]` block to "
                "`.streamlit/secrets.toml` to save datasets permanently across sessions."
            )
        else:
            st.markdown(
                '<span style="font-size:10px;font-weight:700;color:#22C55E">● Connected</span>',
                unsafe_allow_html=True,
            )
            _saved = list_saved_datasets(_db_conn)
            if _saved.empty:
                st.caption("No datasets saved yet. Import a file, then use "
                           "\"Save to Database\" in the Trust Center to persist it here.")
            else:
                for _, row in _saved.iterrows():
                    st.markdown(
                        f"<div style='font-size:11px;font-weight:600;color:#F1F5F9;margin-top:6px'>{row['name']}</div>"
                        f"<div style='font-size:10px;color:#6B7688'>{row['rows']:,} rows · Trust {row['trust_score']}/100 · "
                        f"saved {pd.to_datetime(row['saved_at']).strftime('%b %d, %H:%M')}</div>",
                        unsafe_allow_html=True,
                    )
                    lc1, lc2 = st.columns(2)
                    with lc1:
                        if st.button("Load", key=f"db_load_{row['id']}", use_container_width=True):
                            loaded = load_dataset_from_db(_db_conn, row["id"])
                            if loaded is not None:
                                st.session_state["_active_df_raw"] = clean(loaded)
                                st.session_state["_active_dataset_meta"] = dict(
                                    name=row["name"], source=row["source"], rows=int(row["rows"]),
                                    trust_score=int(row["trust_score"]) if pd.notna(row["trust_score"]) else 0,
                                    status=row["status"],
                                )
                                record_dataset_version(f"Loaded from database: {row['name']}", int(row["rows"]))
                                st.rerun()
                    with lc2:
                        if st.button("Delete", key=f"db_del_{row['id']}", use_container_width=True):
                            delete_dataset_from_db(_db_conn, row["id"])
                            st.rerun()
            if st.session_state.get("_db_last_error"):
                st.caption(f"⚠️ Last DB error: {st.session_state['_db_last_error']}")

    st.markdown("---")

    df_raw = st.session_state.get("_active_df_raw")
    if df_raw is None:
        df_raw = load_default()

    st.markdown("#### 🔍 Filters")

    # Any pending clear/reset must happen BEFORE the widgets below are
    # instantiated this run — Streamlit won't allow changing a widget's
    # session_state value after it's already been created in the same
    # script pass, so both the "reset all" and "clear one" actions defer
    # their actual work to the top of the NEXT run via a flag + rerun.
    if st.session_state.pop("_reset_filters_trigger", False):
        for _fk in ["filter_city", "filter_cat", "filter_inf", "filter_prod", "filter_search"]:
            st.session_state.pop(_fk, None)
    _pending_clear = st.session_state.pop("_clear_single_filter", None)
    if _pending_clear:
        st.session_state.pop(_pending_clear, None)

    cities     = ["All"] + sorted(df_raw["City"].unique())
    categories = ["All"] + sorted(df_raw["Category"].unique())
    products   = ["All"] + sorted(df_raw["Product Name"].unique())

    sel_city = st.selectbox("City / Region", cities, key="filter_city")
    sel_cat  = st.selectbox("Category",      categories, key="filter_cat")
    sel_inf  = st.selectbox("Influencer",    ["All", "Yes", "No"], key="filter_inf")
    sel_prod = st.selectbox("Product",       products, key="filter_prod")
    search   = st.text_input("Search product", placeholder="e.g. Maggi...", key="filter_search")

    # Each active filter (City/Region included) gets its own small "✕" clear
    # option shown as a chip, right below the filters — so the user can drop
    # a single filter without touching the others or re-selecting "All".
    _active_filters = []
    if sel_city != "All":            _active_filters.append(("📍 City/Region", sel_city, "filter_city"))
    if sel_cat  != "All":            _active_filters.append(("🏷️ Category",    sel_cat,  "filter_cat"))
    if sel_inf  != "All":            _active_filters.append(("⚡ Influencer",  sel_inf,  "filter_inf"))
    if sel_prod != "All":            _active_filters.append(("📦 Product",     sel_prod, "filter_prod"))
    if search and search.strip():    _active_filters.append(("🔎 Search",      search.strip(), "filter_search"))

    if _active_filters:
        st.markdown(
            f'<div style="font-size:9.5px;font-weight:700;color:#6B7688;text-transform:uppercase;'
            f'letter-spacing:.08em;margin:12px 0 6px">{len(_active_filters)} Active Filter(s)</div>',
            unsafe_allow_html=True,
        )
        for label, val, fkey in _active_filters:
            cc1, cc2 = st.columns([5, 1])
            with cc1:
                st.markdown(f"""
                <div style="background:rgba(29,77,255,.1);border:1px solid rgba(29,77,255,.25);
                            border-radius:8px;padding:6px 10px;font-size:11px;color:#F1F5F9;
                            overflow:hidden;white-space:nowrap;text-overflow:ellipsis;margin-bottom:6px">
                  <span style="color:#9AA4B2">{label}:</span> <b>{val}</b>
                </div>
                """, unsafe_allow_html=True)
            with cc2:
                if st.button("✕", key=f"clear_{fkey}", use_container_width=True, help=f"Clear {label} filter"):
                    st.session_state["_clear_single_filter"] = fkey
                    st.rerun()
        if st.button("↺ Reset All Filters", use_container_width=True, key="reset_filters_btn"):
            st.session_state["_reset_filters_trigger"] = True
            st.rerun()

    st.markdown("---")
    st.markdown("#### ⚙️ Settings")
    show_raw     = st.checkbox("Show Raw Data Table (Executive Overview)", value=False)
    show_stats   = st.checkbox("Show Statistical Analysis (Sales Analytics)", value=True)

    st.markdown("---")
    with st.expander("🎨 Customize Dashboard"):
        # Reset must happen BEFORE the theme widgets below are instantiated
        # this run — same safe flag+rerun pattern used for filter resets.
        if st.session_state.pop("_reset_theme_trigger", False):
            st.session_state["_theme_name"] = "Nova Blue"
            for _tk in ["_tc_primary", "_tc_bg", "_tc_card", "_tc_sidebar", "_tc_text",
                        "_tc_muted", "_tc_success", "_tc_warning", "_tc_danger"]:
                st.session_state.pop(_tk, None)
            st.session_state.pop("_theme_custom_colors", None)

        _theme_choice = st.selectbox(
            "Theme", list(THEME_PRESETS.keys()) + ["Custom"], key="_theme_name",
            help="Presets recolor cards, buttons, badges, and the sidebar. "
                 "A few page-specific summary cards keep their original colors for now.",
        )

        if _theme_choice == "Custom":
            st.caption("Pick any color below — the whole dashboard updates immediately.")
            _base = THEME_PRESETS["Nova Blue"]
            cc1, cc2 = st.columns(2)
            with cc1:
                _c_primary = st.color_picker("Primary / Accent", _base["primary"], key="_tc_primary")
                _c_bg      = st.color_picker("Background",       _base["bg"],      key="_tc_bg")
                _c_card    = st.color_picker("Card",             _base["card"],    key="_tc_card")
                _c_sidebar = st.color_picker("Sidebar",          _base["sidebar"], key="_tc_sidebar")
            with cc2:
                _c_text    = st.color_picker("Text",             _base["text"],    key="_tc_text")
                _c_muted   = st.color_picker("Muted Text",       _base["muted"],   key="_tc_muted")
                _c_success = st.color_picker("Success",          _base["success"], key="_tc_success")
                _c_warning = st.color_picker("Warning",          _base["warning"], key="_tc_warning")
            _c_danger = st.color_picker("Danger", _base["danger"], key="_tc_danger")

            _ratio = _contrast_ratio(_c_text, _c_bg)
            if _ratio < 4.5:
                st.warning(f"⚠️ Low contrast between Text and Background ({_ratio:.1f}:1) may reduce readability.")

            if st.button("💾 Save Theme", use_container_width=True, key="_save_theme_btn"):
                st.session_state["_theme_custom_colors"] = dict(
                    primary=_c_primary, bg=_c_bg, card=_c_card, sidebar=_c_sidebar,
                    text=_c_text, muted=_c_muted, success=_c_success, warning=_c_warning, danger=_c_danger,
                    border=_hex_to_rgba(_c_muted, .3), sidebar2=_lighten_hex(_c_sidebar, 12),
                )
                st.success("Saved for this session.")
        else:
            st.caption(f"Using the **{_theme_choice}** preset.")

        if st.button("↺ Reset to Default Theme", use_container_width=True, key="_reset_theme_btn"):
            st.session_state["_reset_theme_trigger"] = True
            st.rerun()

    st.markdown("---")
    st.markdown("#### 🤖 BlinkBot AI Mode")
    use_ai_mode = st.toggle("Enable LLM Mode", value=False, help="Use Claude (Anthropic) for natural-language answers")

    if use_ai_mode:
        secret_key = st.secrets.get("ANTHROPIC_API_KEY", "") if hasattr(st, "secrets") else ""
        if secret_key:
            api_key = secret_key.strip().strip('"').strip("'")
            st.markdown("""
            <div style="background:rgba(16,185,129,.1);border:1px solid rgba(16,185,129,.25);
                        border-radius:8px;padding:8px 10px;font-size:10px;color:#22C55E">
              ✅ Claude key loaded from secrets
            </div>""", unsafe_allow_html=True)
        else:
            _raw_key = st.text_input(
                "Anthropic (Claude) API Key",
                type="password",
                placeholder="sk-ant-api03-...",
                help="Get a key at console.anthropic.com → API Keys",
            )
            api_key = _raw_key.strip().strip('"').strip("'").strip() if _raw_key else ""
            _is_placeholder = api_key and (
                "your-key"    in api_key.lower()
                or "your_key" in api_key.lower()
                or "api-key"  in api_key.lower()
                or len(api_key) < 10
            )
            if api_key and not _is_placeholder:
                st.markdown("""
                <div style="background:rgba(16,185,129,.1);border:1px solid rgba(16,185,129,.25);
                            border-radius:8px;padding:8px 10px;font-size:10px;color:#22C55E">
                  ✅ Claude key set — LLM mode active
                </div>""", unsafe_allow_html=True)
            elif _is_placeholder:
                st.markdown("""
                <div style="background:rgba(239,68,68,.1);border:1px solid rgba(239,68,68,.3);
                            border-radius:8px;padding:8px 10px;font-size:10px;color:#EF4444">
                  ❌ Key looks invalid.<br><br>
                  Go to <strong>console.anthropic.com</strong> → API Keys.<br>
                  Paste your key directly — no quotes, no spaces.
                </div>""", unsafe_allow_html=True)
                api_key = ""
            else:
                st.markdown("""
                <div style="background:rgba(245,158,11,.08);border:1px solid rgba(245,158,11,.25);
                            border-radius:8px;padding:8px 10px;font-size:10px;color:#f59e0b">
                  ⚠️ Paste your Anthropic API key above.<br>
                  Get one at console.anthropic.com
                </div>""", unsafe_allow_html=True)
                api_key = ""
        st.markdown(f"""
        <div style="font-size:9px;color:#64748B;margin-top:6px">
          Model: <span style="color:#1D4DFF;font-family:monospace">{_CLAUDE_MODEL}</span><br>
          Claude AI Analyst · History: last {_LLM_HISTORY_LIMIT} turns
        </div>""", unsafe_allow_html=True)
    else:
        api_key = ""
        st.markdown("""
        <div style="background:rgba(255,255,255,.05);border:1px solid #262B33;
                    border-radius:8px;padding:8px 10px;font-size:10px;color:#9AA4B2">
          🔧 Rule-based mode — fast &amp; offline.<br>Toggle above to enable LLM responses.
        </div>""", unsafe_allow_html=True)

    st.markdown("---")

    # ── Workspace status card (reflects real, already-computed state —
    # no new logic: reuses _active_meta and _db_conn from above) ──────────
    _ws_dataset_label = _active_meta["name"] if _active_meta else "Demo Dataset"
    _ws_mode_label    = "Custom Dataset" if _active_meta else "Demo Mode"
    _ws_db_connected  = get_db_connection() is not None
    st.markdown(f"""
    <div class="nova-workspace-card">
      <div class="ws-label">Workspace</div>
      <div class="ws-row"><span><span class="ws-dot"></span>{_ws_mode_label}</span><span style="color:#64748B;font-size:10.5px">{_ws_dataset_label}</span></div>
      <div class="ws-row"><span><span class="ws-dot" style="background:{'#22C55E' if _ws_db_connected else '#64748B'};box-shadow:0 0 6px {'rgba(34,197,94,.8)' if _ws_db_connected else 'transparent'}"></span>{'Connected' if _ws_db_connected else 'Local Session'}</span><span style="color:#64748B;font-size:10.5px">Database</span></div>
      <div class="ws-row"><span><span class="ws-dot"></span>Live Status</span><span style="color:#22C55E;font-size:10.5px;font-weight:700">Active</span></div>
    </div>
    """, unsafe_allow_html=True)

    # ── User profile + logout (same auth/session logic as before, just
    # moved to the bottom of the sidebar and restyled) ─────────────────────
    _profile_user  = st.session_state.get("_auth_user", "user")
    _profile_initials = "".join([p[0] for p in _profile_user.replace(".", " ").replace("_", " ").split()][:2]).upper() or "U"
    st.markdown(f"""
    <div class="nova-profile-card">
      <div class="nova-profile-avatar">{_profile_initials}<span class="dot"></span></div>
      <div>
        <div class="nova-profile-name">{_profile_user}</div>
        <div class="nova-profile-role">Administrator</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div style="font-size:9.5px;color:#475569;text-align:center;margin-top:12px">
      Developed by <strong style="color:#3B82F6">Ayush Mishra</strong><br>
      FastAPI · Pandas · SciPy · Streamlit
    </div>
    """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════════
# ── DATA IMPORT & TRUST CENTER GATE
# While a freshly uploaded file is staged for review, show only the review
# panel — the rest of the dashboard keeps running on the previously active
# (or demo) dataset in the background, untouched, until the user imports.
# ══════════════════════════════════════════════════════════════════════════════════

if st.session_state.get("_show_trust_center") and st.session_state.get("_staged_raw_df") is not None:
    render_data_trust_center()
    st.stop()


# ══════════════════════════════════════════════════════════════════════════════════
# ── FILTERS
# ══════════════════════════════════════════════════════════════════════════════════

df = df_raw.copy()
if sel_city != "All": df = df[df["City"]              == sel_city]
if sel_cat  != "All": df = df[df["Category"]          == sel_cat]
if sel_inf  != "All": df = df[df["Influencer Active"] == sel_inf]
if sel_prod != "All": df = df[df["Product Name"]      == sel_prod]
if search:            df = df[df["Product Name"].str.contains(search, case=False, na=False)]

if df.empty:
    page_header("NovaMS", "Nova Management Solutions")
    st.warning("⚠️ No data matches your filters. Please adjust the filters in the sidebar.")
    st.stop()

# ══════════════════════════════════════════════════════════════════════════════════
# ── PRE-COMPUTE EVERYTHING ONCE  (shared across every page)
# ══════════════════════════════════════════════════════════════════════════════════

kpis       = compute_kpis(df)
inf_stats  = compute_influencer_stats(df)
stats_data = compute_statistics(df) if show_stats and len(df) >= 5 else None
forecast   = compute_forecast(df)
delivery   = compute_delivery_stats(len(df))
unit_econ  = compute_unit_economics(float(df["Total Revenue"].mean()) if len(df) > 0 else 500)
inventory  = compute_inventory(df)
defects    = compute_order_defects(int(kpis["total_orders"]))
wow        = compute_wow_metrics(kpis)
insights   = compute_ai_insights(df, kpis, inf_stats if inf_stats["available"] else {"rev_lift":0,"p_value":1,"significant":False})

_present_delivery_cols   = [c for c in OPTIONAL_DELIVERY_COLS if c in df.columns]
_missing_delivery_cols   = [c for c in OPTIONAL_DELIVERY_COLS if c not in df.columns]
_present_operations_cols = [c for c in OPTIONAL_OPERATIONS_COLS if c in df.columns]
_missing_operations_cols = [c for c in OPTIONAL_OPERATIONS_COLS if c not in df.columns]


# ══════════════════════════════════════════════════════════════════════════════════
# ── PAGE 1 — EXECUTIVE OVERVIEW
# ══════════════════════════════════════════════════════════════════════════════════

def render_executive_overview():
    page_header("Executive Overview", "Real-Time Business Snapshot · Developed by Ayush Mishra")

    st.markdown('<div class="section-head">Executive Summary</div>', unsafe_allow_html=True)
    narrative(f"<b>Business Summary:</b> {compute_executive_summary(df, kpis)}")

    st.markdown('<div class="section-head">Key Performance Indicators</div>', unsafe_allow_html=True)
    avg_delivery = delivery["avg"]

    # Delivery health status — reuses the exact 95% / 85% breakpoints already
    # defined in compute_delivery_stats(), not new thresholds.
    if delivery["otd_pct"] >= 95:
        _d_kind, _d_label = "up", "Healthy"
    elif delivery["otd_pct"] >= 85:
        _d_kind, _d_label = "neutral", "Watch"
    else:
        _d_kind, _d_label = "down", "Critical"

    _rev_badge, _rev_up   = wow["badges"]["total_rev"]
    _prof_badge, _prof_up = wow["badges"]["total_profit"]
    _ord_badge, _ord_up   = wow["badges"]["total_orders"]
    _mgn_badge, _mgn_up   = wow["badges"]["margin"]

    _top_city_pct = (kpis["city_rev"].iloc[0] / kpis["total_rev"] * 100) if kpis["total_rev"] and len(kpis["city_rev"]) else 0
    _top_cat_pct  = (kpis["cat_rev"].iloc[0]  / kpis["total_rev"] * 100) if kpis["total_rev"] and len(kpis["cat_rev"])  else 0

    c1,c2,c3,c4,c5,c6 = st.columns(6)
    with c1:
        kpi_card_v2("Total Revenue", fmt(kpis["total_rev"]), "trending-up",
                    [f"σ = {fmt(kpis['rev_std'])}"], _rev_badge, "up" if _rev_up else "down",
                    accent="blue", spark_values=df["Total Revenue"].values, delay=0.00)
    with c2:
        kpi_card_v2("Total Profit", fmt(kpis["total_profit"]), "activity",
                    ["Net margin earnings"], _prof_badge, "up" if _prof_up else "down",
                    accent="green", spark_values=df["Profit"].values, delay=0.06)
    with c3:
        kpi_card_v2("Total Orders", f"{int(kpis['total_orders']):,}", "shopping-bag",
                    ["Units sold"], _ord_badge, "up" if _ord_up else "down",
                    accent="violet", spark_values=df["Orders"].values, delay=0.12)
    with c4:
        kpi_card_v2("Profit Margin", f"{kpis['margin']:.1f}%", "percent",
                    ["Revenue to profit ratio"], _mgn_badge, "up" if _mgn_up else "down",
                    accent="amber", spark_values=df["Profit Margin"].values, delay=0.18)
    with c5:
        kpi_card_v2("Avg Delivery Time", f"{avg_delivery:.1f} min", "clock",
                    [f"OTD {delivery['otd_pct']:.0f}%"], f"● {_d_label}", _d_kind,
                    accent="red", delay=0.24)
    with c6:
        kpi_card_v2("Top Region", kpis["city_rev"].index[0] if len(kpis["city_rev"]) else "—", "map-pin",
                    [fmt(kpis["city_rev"].iloc[0]) if len(kpis["city_rev"]) else "—",
                     f"{_top_city_pct:.1f}% of Total" if len(kpis["city_rev"]) else ""],
                    accent="blue", delay=0.30)

    c7,c8,c9 = st.columns(3)
    with c7:
        kpi_card_v2("Top Category", kpis["cat_rev"].index[0] if len(kpis["cat_rev"]) else "—", "tag",
                    [fmt(kpis["cat_rev"].iloc[0]) if len(kpis["cat_rev"]) else "—"],
                    accent="blue", ring_pct=_top_cat_pct, delay=0.36)
    with c8:
        _aov_spark = (df["Total Revenue"] / df["Orders"].replace(0, np.nan)).dropna().values
        kpi_card_v2("Avg Order Value", fmt(kpis["aov"]), "receipt", ["Revenue per order"],
                    accent="violet", spark_values=_aov_spark, delay=0.42)
    with c9:
        kpi_card_v2("On-Time Delivery", f"{delivery['otd_pct']:.1f}%", "truck",
                    [f"● {_d_label}"], accent="green", ring_pct=delivery["otd_pct"], delay=0.48)

    st.markdown("<br>", unsafe_allow_html=True)
    narrative(
        f"<b>What's happening:</b> Revenue stands at <b>{fmt(kpis['total_rev'])}</b> across "
        f"<b>{int(kpis['total_orders']):,}</b> orders, led by <b>{kpis['cat_rev'].index[0]}</b> in "
        f"<b>{kpis['city_rev'].index[0]}</b>. <b>What to do:</b> protect the leading category/city combo "
        f"while running targeted promotions in <b>{kpis['city_rev'].index[-1]}</b>, your weakest region."
    )

    _anomaly = detect_top_anomaly(df)
    if _anomaly:
        st.markdown(
            f'<div class="missing-box">⚠ <b>Anomaly Detected:</b> {_anomaly["product"]} in '
            f'{_anomaly["city"]} ({_anomaly["category"]}) shows an unusual revenue {_anomaly["direction"]} — '
            f'{fmt(_anomaly["revenue"])} (Z-score {_anomaly["z"]:.1f} vs the rest of the current view). '
            f'Worth a quick data-quality or demand check.</div>',
            unsafe_allow_html=True,
        )

    with st.expander("🔍 Why did this happen? — dimension breakdown"):
        _why_ctx = _bb_context(df)
        _why_dim = st.selectbox("Explain a specific:", ["City", "Category", "Product"], key="why_dim_choice")
        _why_bullets, _why_name = [], None
        if _why_dim == "City" and kpis["city_rev"] is not None and len(kpis["city_rev"]):
            _why_name = st.selectbox("Choose:", kpis["city_rev"].index.tolist(), key="why_city_choice")
            _why_bullets = _dimension_evidence("city", _why_name, _why_ctx, df)
        elif _why_dim == "Category" and kpis["cat_rev"] is not None and len(kpis["cat_rev"]):
            _why_name = st.selectbox("Choose:", kpis["cat_rev"].index.tolist(), key="why_cat_choice")
            _why_bullets = _dimension_evidence("category", _why_name, _why_ctx, df)
        elif _why_dim == "Product":
            _prod_options = df["Product Name"].unique().tolist()
            if _prod_options:
                _why_name = st.selectbox("Choose:", _prod_options, key="why_prod_choice")
                _why_bullets = _dimension_evidence("product", _why_name, _why_ctx, df)
        if _why_bullets:
            for _b in _why_bullets:
                st.markdown(f"- {_b}")
        else:
            st.caption("Not enough data to explain this selection.")

    st.markdown('<div class="section-head">SALES SNAPSHOT</div>', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        city_data = df.groupby("City")["Total Revenue"].sum().sort_values(ascending=False).reset_index()
        city_data["Share %"] = city_data["Total Revenue"] / city_data["Total Revenue"].sum() * 100
        fig = px.bar(city_data, x="City", y="Total Revenue", color="City",
                     color_discrete_map=CITY_CLR, title="Revenue by City", labels={"Total Revenue":"Revenue (₹)"},
                     custom_data=["Share %"])
        fig.update_layout(**PLOTLY_LAYOUT, title_font_color="#F1F5F9", showlegend=False)
        fig.update_traces(marker_line_width=0, opacity=0.85,
                           hovertemplate="<b>%{x}</b><br>Revenue: ₹%{y:,.0f}<br>Share of total: %{customdata[0]:.1f}%<extra></extra>")
        fig.add_hline(y=city_data["Total Revenue"].mean(), line_dash="dot", line_color="rgba(255,255,255,.35)",
                      line_width=1, annotation_text="avg", annotation_font=dict(size=9, color="#9AA4B2"))
        fig.update_yaxes(tickformat=",.0f", tickprefix="₹")
        st.plotly_chart(fig, use_container_width=True)
    with col2:
        cat_data = df.groupby("Category")["Total Revenue"].sum().reset_index()
        fig = px.pie(cat_data, values="Total Revenue", names="Category",
                     color="Category", color_discrete_map=CAT_CLR, title="Category Distribution", hole=0.55)
        fig.update_layout(**PLOTLY_LAYOUT, title_font_color="#F1F5F9")
        fig.update_traces(textinfo="label+percent", textfont_size=10)
        st.plotly_chart(fig, use_container_width=True)

    st.markdown('<div class="section-head">CITY × CATEGORY HEATMAP</div>', unsafe_allow_html=True)
    pivot = df.pivot_table(index="Category", columns="City", values="Total Revenue", aggfunc="sum", fill_value=0)
    fig = go.Figure(data=go.Heatmap(
        z=pivot.values, x=pivot.columns.tolist(), y=pivot.index.tolist(),
        colorscale=[[0,"#161A21"],[0.35,"#26305C"],[0.7,"#3D52C4"],[1,"#1D4DFF"]],
        text=[[fmt(v) for v in row] for row in pivot.values],
        texttemplate="%{text}", hovertemplate="<b>%{y}</b><br>%{x}: %{text}<extra></extra>",
    ))
    fig.update_layout(**PLOTLY_LAYOUT, title="Revenue Intensity (City × Category)", title_font_color="#F1F5F9", height=280)
    st.plotly_chart(fig, use_container_width=True)

    st.markdown('<div class="section-head">AI BUSINESS INSIGHTS</div>', unsafe_allow_html=True)
    cols = st.columns(3)
    for i, (emoji, title, body) in enumerate(insights):
        with cols[i % 3]:
            st.markdown(f'<div class="insight-card"><div class="insight-title">{title}</div><div class="insight-body">{body}</div></div><br>', unsafe_allow_html=True)

    st.markdown('<div class="section-head">Week-over-Week Comparison</div>', unsafe_allow_html=True)
    w1,w2,w3,w4 = st.columns(4)
    wow_rows = [
        (w1,"Revenue This Week",  kpis["total_rev"],    wow["previous"]["total_rev"],    False),
        (w2,"Orders This Week",   kpis["total_orders"], wow["previous"]["total_orders"], False),
        (w3,"Profit This Week",   kpis["total_profit"], wow["previous"]["total_profit"], False),
        (w4,"Margin This Week",   kpis["margin"],       wow["previous"]["margin"],       True),
    ]
    for col, label, curr, prev, is_pct in wow_rows:
        badge, up = pct_change_label(curr, prev)
        val      = fmt(curr) if not is_pct else f"{curr:.1f}%"
        prev_val = fmt(prev) if not is_pct else f"{prev:.1f}%"
        with col:
            kpi_card(label, val, f"Last week: {prev_val}", badge, up)

    if show_raw:
        st.markdown('<div class="section-head">RAW DATA TABLE</div>', unsafe_allow_html=True)
        display_cols = ["Product Name","Category","City","Original Price","Current Price",
                        "Discount","Orders","Total Revenue","Profit","Profit Margin","Influencer Active"]
        show_df = df[[c for c in display_cols if c in df.columns]].copy()
        show_df["Profit Margin"] = show_df["Profit Margin"].round(1).astype(str) + "%"
        st.dataframe(show_df, use_container_width=True, height=350)
        st.download_button("⬇ Download Filtered CSV", df.to_csv(index=False), "novams_filtered.csv", "text/csv")


# ══════════════════════════════════════════════════════════════════════════════════
# ── PAGE 2 — SALES ANALYTICS
# ══════════════════════════════════════════════════════════════════════════════════

def render_sales_analytics():
    page_header("Sales Analytics", "Revenue Trends · Product & City Performance · Statistical Analysis")

    narrative(
        f"<b>What's happening:</b> {len(df):,} transactions generated <b>{fmt(kpis['total_rev'])}</b> "
        f"at an average order value of <b>{fmt(kpis['aov'])}</b>. "
        f"<b>Why:</b> performance is concentrated in a handful of top SKUs and cities (see Pareto below). "
        f"<b>What to do:</b> protect top performers, and use the discount curve to avoid over-discounting."
    )

    # ── Category Performance — smart metric selector instead of one fixed chart ──
    st.markdown('<div class="section-head">Category Performance</div>', unsafe_allow_html=True)
    st.caption("Switch metric to see which category leads on each measure.")
    _cat_metric = st.radio(
        "Performance Metric", ["Revenue", "Profit", "Orders", "Margin"],
        horizontal=True, key="cat_perf_metric", label_visibility="collapsed",
    )
    _cat_agg = df.groupby("Category").agg(
        Revenue=("Total Revenue", "sum"), Profit=("Profit", "sum"), Orders=("Orders", "sum"),
    )
    _cat_agg["Margin"] = np.where(_cat_agg["Revenue"] > 0, _cat_agg["Profit"] / _cat_agg["Revenue"] * 100, 0)
    _cat_sorted = _cat_agg.sort_values(_cat_metric, ascending=False)
    _cat_is_pct = _cat_metric == "Margin"
    _cat_text = [f"{v:.1f}%" for v in _cat_sorted[_cat_metric]] if _cat_is_pct else [fmt(v) for v in _cat_sorted[_cat_metric]]
    fig = go.Figure(go.Bar(
        x=_cat_sorted.index.tolist(), y=_cat_sorted[_cat_metric],
        marker_color=[CAT_CLR.get(c, "#6366f1") for c in _cat_sorted.index],
        marker_line_width=0, opacity=0.85, text=_cat_text, textposition="outside",
        textfont=dict(color="#F1F5F9", size=10),
    ))
    fig.update_layout(**PLOTLY_BASE,
        title=dict(text=f"Category {_cat_metric}", font=dict(color="#F1F5F9", size=13)),
        height=280, showlegend=False,
        yaxis=dict(ticksuffix="%" if _cat_is_pct else "", tickprefix="" if _cat_is_pct else "₹", **_AXIS_DEFAULTS))
    st.plotly_chart(fig, use_container_width=True)
    _cat_best, _cat_worst = _cat_sorted.index[0], _cat_sorted.index[-1]
    st.caption(
        f"**{_cat_best}** leads on {_cat_metric.lower()}; **{_cat_worst}** is weakest on this measure — "
        f"{'raise pricing or trim discounting there' if _cat_metric == 'Margin' else 'review pricing or promotion mix for it'}."
    )

    col1, col2 = st.columns(2)
    with col1:
        top_prod = df.groupby("Product Name")["Total Revenue"].sum().sort_values(ascending=False).head(10).reset_index()
        fig = px.bar(top_prod, x="Total Revenue", y="Product Name", orientation="h",
                     title="Top 10 Products by Revenue", color="Total Revenue",
                     color_continuous_scale=["#6366f1","#06b6d4","#10b981"])
        fig.update_layout(**PLOTLY_LAYOUT, title_font_color="#F1F5F9", coloraxis_showscale=False)
        fig.update_yaxes(autorange="reversed", gridcolor="rgba(255,255,255,.05)")
        fig.update_xaxes(tickformat=",.0f", tickprefix="₹")
        st.plotly_chart(fig, use_container_width=True)
    with col2:
        fig = px.scatter(df, x="Orders", y="Total Revenue", color="Category",
                         color_discrete_map=CAT_CLR, hover_name="Product Name",
                         hover_data={"City":True,"Discount":True},
                         title="Orders vs Revenue (Scatter)", labels={"Total Revenue":"Revenue (₹)"})
        fig.update_layout(**PLOTLY_LAYOUT, title_font_color="#F1F5F9")
        fig.update_traces(marker=dict(size=7, opacity=0.7))
        fig.update_yaxes(tickformat=",.0f", tickprefix="₹")
        st.plotly_chart(fig, use_container_width=True)

    col1, col2 = st.columns(2)
    with col1:
        inf_data = df.groupby(["Category","Influencer Active"])["Total Revenue"].mean().reset_index() if "Influencer Active" in df.columns else None
        if inf_data is not None:
            inf_data.columns = ["Category","Influencer","Avg Revenue"]
            fig = px.bar(inf_data, x="Category", y="Avg Revenue", color="Influencer",
                         barmode="group", title="Influencer Impact by Category",
                         color_discrete_map={"Yes":"#6366f1","No":"#64748B"})
            fig.update_layout(**PLOTLY_LAYOUT, title_font_color="#F1F5F9")
            fig.update_yaxes(tickformat=",.0f", tickprefix="₹")
            st.plotly_chart(fig, use_container_width=True)
        else:
            missing_data_notice(["Influencer Active"], "Influencer Impact")
    with col2:
        disc_data = df.groupby("Discount").agg(
            Avg_Revenue=("Total Revenue","mean"), Avg_Orders=("Orders","mean"), Count=("Orders","count")
        ).reset_index()
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        fig.add_trace(go.Bar(x=disc_data["Discount"].astype(str)+"%", y=disc_data["Avg_Revenue"],
                             name="Avg Revenue", marker_color="#6366f1", opacity=0.85), secondary_y=False)
        fig.add_trace(go.Scatter(x=disc_data["Discount"].astype(str)+"%", y=disc_data["Avg_Orders"],
                                 name="Avg Orders", mode="lines+markers",
                                 line=dict(color="#06b6d4", width=2)), secondary_y=True)
        fig.update_layout(**PLOTLY_LAYOUT, title="Discount vs Revenue & Orders", title_font_color="#F1F5F9")
        fig.update_yaxes(tickprefix="₹", secondary_y=False)
        st.plotly_chart(fig, use_container_width=True)

    if "Influencer Active" in df.columns:
        st.markdown('<div class="section-head">Marketing / Influencer Performance Ranking</div>', unsafe_allow_html=True)
        _mk = df.groupby("Influencer Active").agg(
            Orders=("Orders", "sum"), Revenue=("Total Revenue", "sum"),
        ).reindex(["Yes", "No"]).dropna(how="all")
        _mk["AOV"] = np.where(_mk["Orders"] > 0, _mk["Revenue"] / _mk["Orders"], 0)
        _mk_display = pd.DataFrame({
            "Marketing Status": ["Influencer-Active" if i == "Yes" else "Organic (No Influencer)" for i in _mk.index],
            "Orders": _mk["Orders"].map(lambda v: f"{int(v):,}"),
            "Revenue": _mk["Revenue"].map(fmt),
            "AOV": _mk["AOV"].map(fmt),
        })
        st.dataframe(_mk_display, use_container_width=True, hide_index=True)
        st.caption(
            "Ranked by revenue contribution. **ROI is not shown** — the dataset has no marketing-spend/cost "
            "column, so a true return-on-spend figure can't be calculated reliably from what's available."
        )

    price_data = df.groupby("Price Tier", observed=True)["Total Revenue"].sum().reset_index()
    price_data["Price Tier"] = price_data["Price Tier"].astype(str)
    fig = px.bar(price_data, x="Price Tier", y="Total Revenue", color="Price Tier",
                 color_discrete_sequence=PAL, title="Revenue by Price Tier", labels={"Total Revenue":"Revenue (₹)"})
    fig.update_layout(**PLOTLY_LAYOUT, title_font_color="#F1F5F9", showlegend=False)
    fig.update_yaxes(tickformat=",.0f", tickprefix="₹")
    fig.update_traces(marker_line_width=0, opacity=0.85)
    st.plotly_chart(fig, use_container_width=True)

    if stats_data:
        sd = stats_data
        st.markdown('<div class="section-head">STATISTICAL ANALYSIS</div>', unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown('<div style="background:#14171C;border:1px solid #262B33;box-shadow:0 1px 2px rgba(0,0,0,.35);border-radius:12px;padding:16px"><div style="font-size:11px;font-weight:600;color:#1D4DFF;margin-bottom:10px">📊 Descriptive Statistics</div>', unsafe_allow_html=True)
            for label, val in [
                ("Mean Revenue",   fmt(sd["mean"])), ("Median Revenue", fmt(sd["median"])),
                ("Std Deviation",  fmt(sd["std"])),  ("Skewness",       f"{sd['skewness']:.3f}"),
                ("Kurtosis",       f"{sd['kurtosis']:.3f}"), ("Normality p", f"{sd['p_norm']:.4f}"),
            ]:
                st.markdown(f'<div class="stat-row"><span class="stat-label">{label}</span><span class="stat-value">{val}</span></div>', unsafe_allow_html=True)
            normal_txt = "✓ Normally distributed" if sd["is_normal"] else "⚠ Not normally distributed"
            normal_clr = "#22C55E" if sd["is_normal"] else "#D97706"
            st.markdown(f'<div style="margin-top:10px;font-size:10px;color:{normal_clr};background:rgba(255,255,255,.05);padding:7px 10px;border-radius:7px">{normal_txt}</div></div>', unsafe_allow_html=True)
        with c2:
            outliers = sd["outliers"]
            st.markdown(f'<div style="background:#14171C;border:1px solid #262B33;box-shadow:0 1px 2px rgba(0,0,0,.35);border-radius:12px;padding:16px"><div style="font-size:11px;font-weight:600;color:#1D4DFF;margin-bottom:10px">⚠ Outlier Detection ({len(outliers)} outliers)</div>', unsafe_allow_html=True)
            if len(outliers) > 0:
                for _, row in outliers.head(6).iterrows():
                    st.markdown(f'<div style="background:rgba(239,68,68,.06);border:1px solid rgba(239,68,68,.15);border-radius:7px;padding:8px 10px;margin-bottom:5px"><div style="font-size:11px;font-weight:600;color:#F1F5F9">{row["Product Name"]}</div><div style="font-size:9px;color:#9AA4B2">{row["City"]} · {row["Category"]}</div><div style="display:flex;justify-content:space-between;margin-top:3px"><span style="font-size:10px;color:#1D4DFF">{fmt(row["Total Revenue"])}</span><span style="font-size:10px;color:#EF4444;font-family:monospace">Z={row["Z-Score"]}</span></div></div>', unsafe_allow_html=True)
            else:
                st.markdown('<div style="font-size:11px;color:#64748B;text-align:center;padding:20px">No significant outliers</div>', unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)
        with c3:
            r_disc, p_disc = sd["r_disc"], sd["p_disc"]
            r_rev,  p_rev  = sd["r_rev"],  sd["p_rev"]
            st.markdown('<div style="background:#14171C;border:1px solid #262B33;box-shadow:0 1px 2px rgba(0,0,0,.35);border-radius:12px;padding:16px"><div style="font-size:11px;font-weight:600;color:#1D4DFF;margin-bottom:10px">🔗 Correlation Analysis</div>', unsafe_allow_html=True)
            for label, val in [
                ("Discount → Orders (r)", f"{r_disc:.3f}"), ("Discount → Orders (p)", f"{p_disc:.4f}"),
                ("Revenue → Profit (r)",  f"{r_rev:.3f}"),  ("Revenue → Profit (p)",  f"{p_rev:.4f}"),
            ]:
                st.markdown(f'<div class="stat-row"><span class="stat-label">{label}</span><span class="stat-value">{val}</span></div>', unsafe_allow_html=True)
            for pair, r, p in [("Discount ↔ Orders", r_disc, p_disc), ("Revenue ↔ Profit", r_rev, p_rev)]:
                sig = p < 0.05; direction = "positive" if r > 0 else "negative"
                txt = f"{'Strong' if abs(r) > 0.5 else 'Weak'} {direction} — {'significant ✓' if sig else 'not significant'}"
                clr = "#22C55E" if sig else "#D97706"
                st.markdown(f'<div style="background:rgba(99,102,241,.07);border-radius:6px;padding:7px 10px;margin-top:6px"><div style="font-size:10px;font-weight:600;color:#1D4DFF">{pair}</div><div style="font-size:10px;color:{clr};margin-top:2px">{txt}</div></div>', unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

        fig = px.imshow(sd["corr_matrix"], text_auto=True,
                        color_continuous_scale=["#EF4444","#1A1E24","#1D4DFF"],
                        zmin=-1, zmax=1, title="Full Correlation Matrix")
        fig.update_layout(**PLOTLY_LAYOUT, title_font_color="#F1F5F9", height=350)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Enable 'Show Statistical Analysis' in the sidebar (needs ≥5 rows in the current filter).")

    st.markdown('<div class="section-head">SALES FORECASTING — LINEAR REGRESSION</div>', unsafe_allow_html=True)
    if forecast:
        fc = forecast
        col1, col2 = st.columns([2, 1])
        with col1:
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=fc["xs"], y=fc["upper"], fill=None, mode="lines", line=dict(width=0), showlegend=False))
            fig.add_trace(go.Scatter(x=fc["xs"], y=fc["lower"], fill="tonexty", mode="lines", line=dict(width=0), fillcolor="rgba(99,102,241,.08)", name="95% CI"))
            fig.add_trace(go.Scatter(x=fc["xs"], y=fc["actual_vals"], mode="lines+markers", name="Actual", line=dict(color="#6366f1", width=2), marker=dict(size=4)))
            fig.add_trace(go.Scatter(x=fc["xs"], y=fc["trend_vals"], mode="lines", name="Trend", line=dict(color="#06b6d4", width=2, dash="dash")))
            fig.add_trace(go.Scatter(x=[fc["n"]+1], y=[fc["next_val"]], mode="markers", name="Forecast", marker=dict(color="#10b981", size=12, symbol="star")))
            fig.update_layout(**PLOTLY_LAYOUT, title="Revenue Forecast with Confidence Interval", title_font_color="#F1F5F9", height=280)
            fig.update_yaxes(tickformat=",.0f", tickprefix="₹")
            st.plotly_chart(fig, use_container_width=True)
        with col2:
            growth_clr = "#22C55E" if fc["growth_pct"] >= 0 else "#EF4444"
            st.markdown(f"""
            <div style="background:#14171C;border:1px solid #262B33;box-shadow:0 1px 2px rgba(0,0,0,.35);border-radius:12px;padding:20px">
              <div style="font-size:10px;color:#64748B;text-transform:uppercase;letter-spacing:.08em;margin-bottom:8px">Forecast Value</div>
              <div style="font-size:28px;font-weight:700;font-family:monospace;background:linear-gradient(90deg,#1D4DFF,#1D4DFF);-webkit-background-clip:text;-webkit-text-fill-color:transparent">{fmt(fc['next_val'])}</div>
              <div style="display:inline-block;font-size:11px;font-weight:600;padding:3px 9px;border-radius:5px;margin:8px 0;background:{'rgba(16,185,129,.12)' if fc['growth_pct']>=0 else 'rgba(239,68,68,.12)'};color:{growth_clr}">
                {'↑' if fc['growth_pct']>=0 else '↓'} {abs(fc['growth_pct']):.1f}% vs avg
              </div>
            """, unsafe_allow_html=True)
            for label, val in [("R² Score", f"{fc['r2']:.4f}"), ("Slope β₁", f"{fc['slope']:.3f}"), ("CI Band", fmt(fc["ci"]))]:
                st.markdown(f'<div class="stat-row"><span class="stat-label">{label}</span><span class="stat-value">{val}</span></div>', unsafe_allow_html=True)
            quality = "✓ Good fit" if fc["r2"] > 0.6 else "⚠ Low R² — noisy data"
            q_clr   = "#22C55E" if fc["r2"] > 0.6 else "#D97706"
            st.markdown(f'<div style="margin-top:10px;font-size:10px;color:{q_clr};background:rgba(255,255,255,.05);padding:7px 10px;border-radius:7px">{quality}</div></div>', unsafe_allow_html=True)
    else:
        st.info("Need at least 5 distinct products in the current filter to fit a forecast.")

    st.markdown('<div class="section-head">PARETO ANALYSIS — 80/20 REVENUE RULE</div>', unsafe_allow_html=True)
    prod_rev_sorted = df.groupby("Product Name")["Total Revenue"].sum().sort_values(ascending=False)
    cumulative_pct  = (prod_rev_sorted.cumsum() / prod_rev_sorted.sum() * 100).values
    pareto_x        = list(range(1, len(prod_rev_sorted) + 1))
    cutoff_idx      = next((i for i, v in enumerate(cumulative_pct) if v >= 80), len(pareto_x)-1)
    cutoff_products = cutoff_idx + 1

    col1, col2 = st.columns([3, 1])
    with col1:
        fig = go.Figure()
        fig.add_trace(go.Bar(x=prod_rev_sorted.index.tolist(), y=prod_rev_sorted.values,
            name="Revenue", marker_color="#6366f1", marker_line_width=0, opacity=0.75, yaxis="y"))
        fig.add_trace(go.Scatter(x=prod_rev_sorted.index.tolist(), y=cumulative_pct,
            name="Cumulative %", mode="lines+markers", line=dict(color="#06b6d4", width=2), marker=dict(size=5), yaxis="y2"))
        fig.add_hline(y=80, line_dash="dash", line_color="#f59e0b",
                      annotation_text="80% Revenue Threshold", annotation_font_color="#f59e0b", annotation_position="top right")
        fig.add_vrect(x0=-0.5, x1=cutoff_idx + 0.5, fillcolor="rgba(99,102,241,.06)", line_width=0,
            annotation_text=f"Top {cutoff_products} products", annotation_position="top left", annotation_font_color="#1D4DFF")
        fig.update_layout(**PLOTLY_BASE,
            title=dict(text=f"Pareto Chart — Top {cutoff_products} of {len(prod_rev_sorted)} products drive 80% of revenue", font=dict(color="#F1F5F9", size=12)),
            height=300, yaxis=dict(title="Revenue (₹)", tickprefix="₹", gridcolor="rgba(255,255,255,.05)"),
            yaxis2=dict(title="Cumulative %", overlaying="y", side="right", range=[0,105], ticksuffix="%", showgrid=False),
            legend=dict(orientation="h", y=1.1))
        st.plotly_chart(fig, use_container_width=True)
    with col2:
        pareto_pct = cutoff_products / len(prod_rev_sorted) * 100
        rev_80     = prod_rev_sorted.iloc[:cutoff_products].sum()
        st.markdown(f"""
        <div style="background:#14171C;border:1px solid #262B33;box-shadow:0 1px 2px rgba(0,0,0,.35);border-radius:12px;padding:18px;text-align:center">
          <div style="font-size:10px;color:#64748B;text-transform:uppercase;letter-spacing:.08em;margin-bottom:10px">80/20 Rule</div>
          <div style="font-size:36px;font-weight:700;background:linear-gradient(90deg,#1D4DFF,#1D4DFF);-webkit-background-clip:text;-webkit-text-fill-color:transparent">{pareto_pct:.0f}%</div>
          <div style="font-size:11px;color:#9AA4B2;margin-top:4px">of products drive</div>
          <div style="font-size:22px;font-weight:700;color:#10b981;margin:6px 0">80%</div>
          <div style="font-size:11px;color:#9AA4B2">of revenue</div>
          <div style="margin-top:14px;padding-top:12px;border-top:1px solid rgba(255,255,255,.09)">
            <div class="stat-row"><span class="stat-label">Key SKUs</span><span class="stat-value">{cutoff_products}</span></div>
            <div class="stat-row"><span class="stat-label">Their revenue</span><span class="stat-value">{fmt(rev_80)}</span></div>
            <div class="stat-row"><span class="stat-label">Total SKUs</span><span class="stat-value">{len(prod_rev_sorted)}</span></div>
          </div>
        </div>
        """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════════
# ── PAGE 3 — DELIVERY ANALYTICS
# ══════════════════════════════════════════════════════════════════════════════════

def render_delivery_analytics():
    page_header("Delivery Analytics", "On-Time Performance · Speed · Order Quality")

    if _present_delivery_cols:
        narrative(
            f"Your file includes real delivery fields: {', '.join(f'<b>{c}</b>' for c in _present_delivery_cols)}. "
            f"Charts below that depend on these use your actual data; anything else falls back to the "
            f"simulated delivery model (labelled clearly)."
        )
    else:
        missing_data_notice(OPTIONAL_DELIVERY_COLS, "Delivery Analytics")
        narrative(
            "No raw delivery-timing columns were found, so KPIs and charts below use a <b>simulated delivery "
            "time model</b> (calibrated to a 10-minute promise) so the page still demonstrates the analytics "
            "NovaMS would run once real rider/order-timing data is connected."
        )

    dl = delivery
    st.markdown('<div class="section-head">DELIVERY PERFORMANCE</div>', unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    with col1:
        fig = go.Figure(go.Indicator(
            mode="gauge+number", value=dl["otd_pct"],
            title={"text":"On-Time Delivery %","font":{"color":"#9AA4B2","size":13}},
            number={"suffix":"%","font":{"color":dl["status_color"],"size":28}},
            gauge={"axis":{"range":[0,100],"tickcolor":"#64748B"},
                   "bar":{"color":dl["status_color"]}, "bgcolor":"#14171C",
                   "steps":[{"range":[0,85],"color":"rgba(239,68,68,.15)"},
                             {"range":[85,95],"color":"rgba(245,158,11,.15)"},
                             {"range":[95,100],"color":"rgba(16,185,129,.15)"}],
                   "threshold":{"line":{"color":"#fff","width":2},"thickness":0.75,"value":95}},
        ))
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", font_color="#9AA4B2", height=220, margin=dict(l=20,r=20,t=40,b=10))
        st.plotly_chart(fig, use_container_width=True)
        st.markdown(f'<div style="text-align:center;font-size:12px;font-weight:600;color:{dl["status_color"]}">{dl["status"]}</div>', unsafe_allow_html=True)
    with col2:
        fig = go.Figure(go.Bar(
            x=[dl["p50"],dl["avg"],dl["p90"],dl["promise"]],
            y=["P50","Avg","P90","Promise"], orientation="h",
            marker_color=["#10b981","#6366f1","#ef4444","#f59e0b"], marker_line_width=0,
        ))
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="#9AA4B2", height=220,
                          title=dict(text="Delivery Time (minutes)", font=dict(color="#F1F5F9",size=13)),
                          margin=dict(l=10,r=40,t=40,b=10),
                          xaxis=dict(title="Minutes",gridcolor="rgba(99,130,255,.05)"),
                          yaxis=dict(gridcolor="rgba(0,0,0,0)"))
        st.plotly_chart(fig, use_container_width=True)
    with col3:
        bar_colors = ["#ef4444" if x > dl["promise"]+2 else "#10b981" for x in dl["hist_centers"]]
        fig = go.Figure(go.Bar(x=dl["hist_centers"], y=dl["hist_counts"], marker_color=bar_colors, marker_line_width=0))
        fig.add_vline(x=dl["promise"], line_dash="dash", line_color="#f59e0b",
                      annotation_text="10-min promise", annotation_font_color="#f59e0b")
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="#9AA4B2", height=220,
                          title=dict(text="Order Distribution by Time", font=dict(color="#F1F5F9",size=13)),
                          margin=dict(l=10,r=10,t=40,b=10),
                          xaxis=dict(title="Minutes",gridcolor="rgba(99,130,255,.05)"),
                          yaxis=dict(gridcolor="rgba(99,130,255,.05)"))
        st.plotly_chart(fig, use_container_width=True)

    st.markdown('<div class="section-head">ORDER QUALITY — DEFECT RATE</div>', unsafe_allow_html=True)
    df_d = defects
    col1, col2 = st.columns(2)
    with col1:
        fig = go.Figure(go.Funnel(
            y=df_d["funnel_labels"], x=df_d["funnel_y"], textinfo="value+percent initial",
            marker=dict(color=["#6366f1","#8b5cf6","#f59e0b","#ef4444","#10b981"]),
            connector=dict(line=dict(color="#CBD5E1", width=1)),
        ))
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="#9AA4B2", height=300,
                          title=dict(text=f"Order Quality Funnel | ODR: {df_d['odr_pct']:.1f}%", font=dict(color="#F1F5F9",size=13)),
                          margin=dict(l=10,r=10,t=50,b=10))
        st.plotly_chart(fig, use_container_width=True)
    with col2:
        fig = go.Figure(go.Bar(
            x=["Expired/Damaged","Missing Items","Cancelled (OOS)"],
            y=[df_d["expired"],df_d["missing"],df_d["cancelled_oos"]],
            marker_color=["#ef4444","#f59e0b","#8b5cf6"], marker_line_width=0,
            text=[df_d["expired"],df_d["missing"],df_d["cancelled_oos"]],
            textposition="outside", textfont=dict(color="#F1F5F9"),
        ))
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="#9AA4B2", height=300,
                          title=dict(text="Defect Breakdown by Category", font=dict(color="#F1F5F9",size=13)),
                          margin=dict(l=10,r=10,t=50,b=10),
                          yaxis=dict(gridcolor="rgba(99,130,255,.05)"), xaxis=dict(gridcolor="rgba(0,0,0,0)"))
        st.plotly_chart(fig, use_container_width=True)

    st.markdown('<div class="section-head">DETAILED DELIVERY TABLE</div>', unsafe_allow_html=True)
    if _present_delivery_cols:
        show_cols = [c for c in OPTIONAL_DELIVERY_COLS if c in df.columns]
        st.dataframe(df[show_cols], use_container_width=True, height=320)
    else:
        st.markdown("""
        <div class="missing-box">
          📋 A per-order delivery table (Order ID, Delivery Partner, Pickup/Packing/Waiting Time, Distance,
          Delivery Cost, Delay Reason, SLA Target/Achieved, Customer Rating) will appear here automatically
          once your uploaded file includes any of those columns. No fabricated rows are shown.
        </div>
        """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════════
# ── PAGE 4 — INVENTORY INTELLIGENCE
# ══════════════════════════════════════════════════════════════════════════════════

def render_inventory_intelligence():
    page_header("Inventory Intelligence", "Stock Risk · Reorder Alerts · Fast/Slow Movers")

    narrative(
        f"<b>What's happening:</b> stock-cover is simulated from each product's order velocity "
        f"(no live warehouse feed is connected yet). <b>Why it matters:</b> "
        f"{(inventory['Risk'].str.contains('CRITICAL')).sum()} of your top {len(inventory)} SKUs are at "
        f"critical cover. <b>What to do:</b> action the reorder list below before those SKUs go out of stock."
    )

    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown('<div style="font-size:11px;font-weight:600;color:#1D4DFF;margin-bottom:10px">⚡ Top 10 High-Risk Inventory Items</div>', unsafe_allow_html=True)
        for _, row in inventory.iterrows():
            st.markdown(
                f'<div style="background:{row["_bg"]};border:1px solid {row["_border"]};border-radius:8px;padding:10px 14px;margin-bottom:6px;display:flex;align-items:center;justify-content:space-between">'
                f'<div><div style="font-size:12px;font-weight:600;color:#F1F5F9">{row["Product"]}</div>'
                f'<div style="font-size:10px;color:#9AA4B2;margin-top:2px">Stock: {row["Stock_Left"]} · Daily: {row["Daily_Sales"]} · Covers: {row["Days_Cover"]} days</div></div>'
                f'<div style="text-align:right"><div style="font-size:11px;font-weight:700;color:{row["_color"]}">{row["Risk"]}</div>'
                f'<div style="font-size:10px;color:{row["_color"]};margin-top:2px">{row["Action"]}</div></div></div>',
                unsafe_allow_html=True,
            )
    with col2:
        critical_count = inventory["Risk"].str.contains("CRITICAL").sum()
        low_count      = inventory["Risk"].str.contains("LOW").sum()
        ok_count       = inventory["Risk"].str.contains("OK").sum()
        fig = go.Figure(go.Pie(
            labels=["Critical 🔴","Low Stock 🟡","OK 🟢"], values=[critical_count, low_count, ok_count],
            hole=0.65, marker=dict(colors=["#ef4444","#f59e0b","#10b981"]), textinfo="label+value", textfont=dict(size=11),
        ))
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", font_color="#9AA4B2", height=280,
                          title=dict(text="Stock Risk Distribution", font=dict(color="#F1F5F9",size=13)),
                          margin=dict(l=10,r=10,t=50,b=10), legend=dict(font=dict(size=10)))
        st.plotly_chart(fig, use_container_width=True)
        st.markdown(f'<div style="background:rgba(239,68,68,.08);border:1px solid rgba(239,68,68,.25);border-radius:8px;padding:12px;text-align:center;margin-top:8px"><div style="font-size:22px;font-weight:700;color:#ef4444">{critical_count}</div><div style="font-size:10px;color:#9AA4B2">Products need immediate reorder</div></div>', unsafe_allow_html=True)

    st.markdown('<div class="section-head">FAST vs SLOW MOVERS</div>', unsafe_allow_html=True)
    prod_velocity = df.groupby("Product Name")["Orders"].sum().sort_values(ascending=False)
    col1, col2 = st.columns(2)
    with col1:
        fast = prod_velocity.head(8)
        fig = go.Figure(go.Bar(x=fast.values, y=fast.index.tolist(), orientation="h",
            marker_color="#10b981", marker_line_width=0, text=fast.values, textposition="outside"))
        fig.update_layout(**PLOTLY_BASE, title=dict(text="🟢 Fast-Moving Products (by Orders)", font=dict(color="#F1F5F9", size=13)),
                          height=280, yaxis=dict(autorange="reversed", gridcolor="rgba(0,0,0,0)"), showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
    with col2:
        slow = prod_velocity.tail(8).sort_values()
        fig = go.Figure(go.Bar(x=slow.values, y=slow.index.tolist(), orientation="h",
            marker_color="#f59e0b", marker_line_width=0, text=slow.values, textposition="outside"))
        fig.update_layout(**PLOTLY_BASE, title=dict(text="🟡 Slow-Moving Products (by Orders)", font=dict(color="#F1F5F9", size=13)),
                          height=280, yaxis=dict(gridcolor="rgba(0,0,0,0)"), showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

    st.markdown('<div class="section-head">INVENTORY SUMMARY</div>', unsafe_allow_html=True)
    i1, i2, i3, i4 = st.columns(4)
    for col, icon, label, val in [
        (i1,"📦","Total Products", f"{df['Product Name'].nunique():,}"),
        (i2,"🔴","Critical (Top 10)", f"{critical_count}"),
        (i3,"🟡","Low Stock (Top 10)", f"{low_count}"),
        (i4,"🟢","Healthy (Top 10)", f"{ok_count}"),
    ]:
        with col:
            kpi_card(label, val)
    st.caption("Stock levels and days-of-cover are simulated from order velocity — connect a warehouse/stock feed for live figures.")


# ══════════════════════════════════════════════════════════════════════════════════
# ── PAGE 5 — OPERATIONS
# ══════════════════════════════════════════════════════════════════════════════════

def render_operations():
    page_header("Operations", "Order Processing · Store Performance · Bottlenecks")

    if _present_operations_cols:
        narrative(f"Operational columns found in your data: {', '.join(f'<b>{c}</b>' for c in _present_operations_cols)}.")
    else:
        missing_data_notice(OPTIONAL_OPERATIONS_COLS, "Operations")

    st.markdown('<div class="section-head">ORDER VOLUME BY CITY (STORE PROXY)</div>', unsafe_allow_html=True)
    st.caption("Your dataset doesn't include a dedicated store/warehouse ID, so city is used as the closest available proxy for a fulfillment location.")
    city_ops = df.groupby("City").agg(Orders=("Orders","sum"), Revenue=("Total Revenue","sum")).sort_values("Orders", ascending=False).reset_index()
    fig = px.bar(city_ops, x="City", y="Orders", color="City", color_discrete_map=CITY_CLR,
                 title="Order Volume by City", labels={"Orders":"Total Orders"})
    fig.update_layout(**PLOTLY_LAYOUT, title_font_color="#F1F5F9", showlegend=False)
    fig.update_traces(marker_line_width=0, opacity=0.85)
    st.plotly_chart(fig, use_container_width=True)

    st.markdown('<div class="section-head">PROCESSING TIME BREAKDOWN</div>', unsafe_allow_html=True)
    if _present_operations_cols:
        for col in _present_operations_cols:
            if pd.api.types.is_numeric_dtype(df[col]):
                fig = px.histogram(df, x=col, nbins=20, title=f"Distribution of {col}", color_discrete_sequence=["#6366f1"])
                fig.update_layout(**PLOTLY_LAYOUT, title_font_color="#F1F5F9", height=260)
                st.plotly_chart(fig, use_container_width=True)
    else:
        st.markdown("""
        <div class="missing-box">
          ⚙️ Order processing time, picking time, and packing time are not present in your current dataset,
          so this section can't compute real operational-bottleneck charts. Upload a file with those columns
          (or an <code>Order ID</code> + timestamp trail) to unlock this analysis — nothing is being simulated
          here to avoid misleading operational decisions.
        </div>
        """, unsafe_allow_html=True)

    st.markdown('<div class="section-head">OPERATIONAL SUMMARY</div>', unsafe_allow_html=True)
    o1, o2, o3 = st.columns(3)
    for col, icon, label, val in [
        (o1,"🏙️","Active Locations (Cities)", f"{df['City'].nunique()}"),
        (o2,"🧾","Order Lines Processed", f"{len(df):,}"),
        (o3,"📦","SKUs in Circulation", f"{df['Product Name'].nunique()}"),
    ]:
        with col:
            kpi_card(label, val)


# ══════════════════════════════════════════════════════════════════════════════════
# ── PAGE 6 — CUSTOMER ANALYTICS
# ══════════════════════════════════════════════════════════════════════════════════

def render_customer_analytics():
    page_header("Customer Analytics", "New vs Repeat · Retention · Ratings · Segments")

    st.caption("Your dataset doesn't include a customer ID, so new-vs-repeat and cohort retention below use an illustrative weekly model — clearly separated from your real revenue/order figures elsewhere in NovaMS.")

    st.markdown('<div class="section-head">CUSTOMER RETENTION — NEW vs REPEAT</div>', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        weeks    = ["Week 1","Week 2","Week 3","Week 4","Week 5","Week 6"]
        new_c    = [1200,980,1100,870,1050,920]
        repeat_c = [800,920,1050,1100,1200,1280]
        fig = go.Figure()
        fig.add_trace(go.Bar(name="New Customers",    x=weeks, y=new_c,    marker_color="#6366f1", marker_line_width=0))
        fig.add_trace(go.Bar(name="Repeat Customers", x=weeks, y=repeat_c, marker_color="#10b981", marker_line_width=0))
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="#9AA4B2", height=280,
                          barmode="group", title=dict(text="New vs Repeat Customers (Weekly, illustrative)", font=dict(color="#F1F5F9",size=13)),
                          margin=dict(l=10,r=10,t=50,b=10), legend=dict(font=dict(size=10)),
                          yaxis=dict(gridcolor="rgba(99,130,255,.05)"), xaxis=dict(gridcolor="rgba(0,0,0,0)"))
        st.plotly_chart(fig, use_container_width=True)
    with col2:
        retention_matrix = [[100,68,52,41],[100,71,55,43],[100,65,48,38],[100,73,58,46]]
        fig = go.Figure(go.Heatmap(
            z=retention_matrix, x=["W+0","W+1","W+2","W+3"], y=["Week 1","Week 2","Week 3","Week 4"],
            colorscale=[[0,"#161A21"],[0.4,"#26305C"],[0.7,"#3D52C4"],[1,"#1D4DFF"]],
            text=[[f"{v}%" for v in row] for row in retention_matrix], texttemplate="%{text}",
            hovertemplate="Cohort: %{y}<br>Week: %{x}<br>Retention: %{text}<extra></extra>",
        ))
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", font_color="#9AA4B2", height=280,
                          title=dict(text="Cohort Retention Table (%, illustrative)", font=dict(color="#F1F5F9",size=13)),
                          margin=dict(l=10,r=10,t=50,b=10))
        st.plotly_chart(fig, use_container_width=True)

    st.markdown('<div class="section-head">CITY COMPETITIVE RADAR — MULTI-KPI</div>', unsafe_allow_html=True)
    radar_metrics = ["Revenue", "Orders", "Avg Price", "Discount%", "Profit Margin"]
    cities_present = df["City"].unique().tolist()
    city_radar_data = {}
    for city in cities_present:
        cdf = df[df["City"] == city]
        city_radar_data[city] = {
            "Revenue": cdf["Total Revenue"].sum(), "Orders": cdf["Orders"].sum(),
            "Avg Price": cdf["Current Price"].mean(), "Discount%": cdf["Discount"].mean(),
            "Profit Margin": cdf["Profit Margin"].mean() if "Profit Margin" in cdf.columns else 0,
        }
    radar_df = pd.DataFrame(city_radar_data).T
    radar_norm = radar_df.copy()
    for col in radar_norm.columns:
        col_range = radar_norm[col].max() - radar_norm[col].min()
        radar_norm[col] = (radar_norm[col] - radar_norm[col].min()) / col_range if col_range > 0 else 0.5

    col1, col2 = st.columns([2, 1])
    with col1:
        fig = go.Figure()
        for i, city in enumerate(cities_present):
            vals = radar_norm.loc[city].tolist(); vals += [vals[0]]
            cats  = radar_metrics + [radar_metrics[0]]
            clr   = CITY_CLR.get(city, PAL[i % len(PAL)])
            fig.add_trace(go.Scatterpolar(r=vals, theta=cats, name=city, fill="toself",
                fillcolor=_hex_to_rgba(clr, 0.08), line=dict(color=clr, width=2), marker=dict(size=5)))
        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            polar=dict(bgcolor="rgba(0,0,0,0)",
                radialaxis=dict(visible=True, range=[0,1], gridcolor="rgba(255,255,255,.09)", tickfont=dict(size=8, color="#64748B")),
                angularaxis=dict(gridcolor="rgba(255,255,255,.09)", tickfont=dict(size=10, color="#9AA4B2"))),
            font=dict(family="Inter", color="#9AA4B2", size=11),
            title=dict(text="City Competitive Radar (normalized per KPI)", font=dict(color="#F1F5F9", size=12)),
            legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(size=10)),
            margin=dict(l=30, r=30, t=50, b=30), height=360,
        )
        st.plotly_chart(fig, use_container_width=True)
    with col2:
        radar_norm["Score"] = radar_norm.mean(axis=1) * 100
        ranked = radar_norm[["Score"]].sort_values("Score", ascending=False)
        st.markdown("""
        <div style="background:#14171C;border:1px solid #262B33;box-shadow:0 1px 2px rgba(0,0,0,.35);border-radius:12px;padding:16px">
          <div style="font-size:10px;font-weight:600;color:#1D4DFF;text-transform:uppercase;letter-spacing:.08em;margin-bottom:12px">
            🏆 Composite City Score
          </div>
        """, unsafe_allow_html=True)
        medals_r = ["🥇","🥈","🥉"] + ["▫️"]*(len(ranked)-3)
        for i, (city, row) in enumerate(ranked.iterrows()):
            score = row["Score"]; bar_w = int(score); clr = CITY_CLR.get(city, PAL[i % len(PAL)])
            st.markdown(f"""
            <div style="margin-bottom:10px">
              <div style="display:flex;justify-content:space-between;margin-bottom:3px">
                <span style="font-size:11px;color:#F1F5F9">{medals_r[i]} {city}</span>
                <span style="font-size:10px;font-weight:600;color:{clr};font-family:monospace">{score:.0f}/100</span>
              </div>
              <div style="background:rgba(99,130,255,.08);border-radius:4px;height:5px">
                <div style="width:{bar_w}%;background:{clr};height:5px;border-radius:4px"></div>
              </div>
            </div>
            """, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    if "Influencer Active" in df.columns:
        st.markdown('<div class="section-head">INFLUENCER-DRIVEN CUSTOMER LIFT</div>', unsafe_allow_html=True)
        st.plotly_chart(_chart_influencer_lift(_bb_context(df), df), use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════════
# ── PAGE 7 — FINANCE
# ══════════════════════════════════════════════════════════════════════════════════

def render_finance():
    page_header("Finance", "Unit Economics · Cost Structure · Profitability by Category & City")

    ue = unit_econ
    narrative(
        f"<b>What's happening:</b> average order revenue is <b>{fmt(ue['avg_rev'])}</b> with a contribution "
        f"margin of <b>{ue['cm_pct']:.1f}%</b> after COGS, rider pay, packaging, gateway fees and promos. "
        f"<b>What to do:</b> COGS is the biggest lever — renegotiate supplier terms or shift mix toward "
        f"higher-margin categories below."
    )

    st.markdown('<div class="section-head">UNIT ECONOMICS — CONTRIBUTION MARGIN</div>', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        labels = ["Revenue","COGS","Rider Pay","Packaging","Gateway Fee","Promos","Net Profit"]
        values = [ue["avg_rev"],-ue["cogs"],-ue["rider"],-ue["packaging"],-ue["gateway"],-ue["promos"],ue["net_profit"]]
        fig = go.Figure(go.Waterfall(
            name="Unit Economics", orientation="v",
            measure=["absolute","relative","relative","relative","relative","relative","total"],
            x=labels, y=values, text=[fmt(abs(v)) for v in values], textposition="outside",
            connector={"line":{"color":"#94A3B8"}},
            decreasing={"marker":{"color":"#ef4444"}}, increasing={"marker":{"color":"#10b981"}},
            totals={"marker":{"color":"#6366f1"}},
        ))
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="#9AA4B2", height=320,
                          title=dict(text=f"Revenue → Net Profit | CM: {ue['cm_pct']:.1f}%", font=dict(color="#F1F5F9",size=12)),
                          margin=dict(l=10,r=10,t=50,b=10), yaxis=dict(gridcolor="rgba(99,130,255,.05)"), showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
    with col2:
        fig = go.Figure(go.Pie(
            labels=["COGS (52%)","Rider Pay (12%)","Packaging (3%)","Gateway (2%)","Promos (5%)","Net Profit (26%)"],
            values=[ue["cogs"],ue["rider"],ue["packaging"],ue["gateway"],ue["promos"],max(0,ue["net_profit"])],
            hole=0.6, marker=dict(colors=["#6366f1","#06b6d4","#f59e0b","#8b5cf6","#ec4899","#10b981"]),
            textinfo="label+percent", textfont=dict(size=10),
        ))
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", font_color="#9AA4B2", height=320,
                          title=dict(text="Cost Structure Breakdown", font=dict(color="#F1F5F9",size=13)),
                          margin=dict(l=10,r=10,t=50,b=10), legend=dict(font=dict(size=9)))
        st.plotly_chart(fig, use_container_width=True)

    st.markdown('<div class="section-head">PROFITABILITY BY CATEGORY & CITY</div>', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        cat_profit = df.groupby("Category").agg(Revenue=("Total Revenue","sum"), Profit=("Profit","sum")).reset_index()
        cat_profit["Margin %"] = np.where(cat_profit["Revenue"]>0, cat_profit["Profit"]/cat_profit["Revenue"]*100, 0)
        fig = go.Figure(go.Bar(
            x=cat_profit["Category"], y=cat_profit["Margin %"],
            marker_color=[CAT_CLR.get(c,"#6366f1") for c in cat_profit["Category"]], marker_line_width=0,
            text=[f"{v:.1f}%" for v in cat_profit["Margin %"]], textposition="outside",
        ))
        fig.update_layout(**PLOTLY_BASE, title=dict(text="Profit Margin by Category", font=dict(color="#F1F5F9", size=13)),
                          yaxis=dict(ticksuffix="%", gridcolor="rgba(255,255,255,.05)"), showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
    with col2:
        city_profit = df.groupby("City").agg(Revenue=("Total Revenue","sum"), Profit=("Profit","sum")).reset_index()
        city_profit["Margin %"] = np.where(city_profit["Revenue"]>0, city_profit["Profit"]/city_profit["Revenue"]*100, 0)
        fig = go.Figure(go.Bar(
            x=city_profit["City"], y=city_profit["Margin %"],
            marker_color=[CITY_CLR.get(c,"#6366f1") for c in city_profit["City"]], marker_line_width=0,
            text=[f"{v:.1f}%" for v in city_profit["Margin %"]], textposition="outside",
        ))
        fig.update_layout(**PLOTLY_BASE, title=dict(text="Profit Margin by City", font=dict(color="#F1F5F9", size=13)),
                          yaxis=dict(ticksuffix="%", gridcolor="rgba(255,255,255,.05)"), showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

    st.markdown('<div class="section-head">DELIVERY COST IMPACT</div>', unsafe_allow_html=True)
    dcol1, dcol2, dcol3 = st.columns(3)
    delivery_cost_per_order = ue["rider"] + ue["packaging"]
    total_delivery_cost = delivery_cost_per_order * kpis["total_orders"]
    for col, icon, label, val in [
        (dcol1,"🚴","Delivery Cost / Order", fmt(delivery_cost_per_order)),
        (dcol2,"📦","Total Delivery Cost",    fmt(total_delivery_cost)),
        (dcol3,"📊","% of Revenue",           f"{(total_delivery_cost/kpis['total_rev']*100 if kpis['total_rev'] else 0):.1f}%"),
    ]:
        with col:
            kpi_card(label, val)


# ══════════════════════════════════════════════════════════════════════════════════
# ── PAGE 8 — AI ANALYST (BlinkBot)
# ══════════════════════════════════════════════════════════════════════════════════

def render_ai_analyst():
    page_header("AI Analyst — BlinkBot", "Ask about revenue, delivery, inventory, or customers in plain English")

    _bb_ctx_live = _bb_context(df)
    _ui_mem = _get_memory()

    mode_badge = (
        '<span style="background:rgba(16,185,129,.2);border:1px solid rgba(16,185,129,.4);'
        'border-radius:20px;padding:3px 10px;font-size:10px;color:#22C55E;margin-left:8px">✨ Claude AI Analyst</span>'
        if (use_ai_mode and api_key) else
        '<span style="background:rgba(99,130,255,.08);border:1px solid #262B33;'
        'border-radius:20px;padding:3px 10px;font-size:10px;color:#64748B;margin-left:8px">🔧 Rule-based</span>'
    )

    bb_head_col, bb_mem_col = st.columns([3, 2])
    with bb_head_col:
        st.markdown(f"""
        <div class="blinkbot-header">
          <div style="width:42px;height:42px;background:linear-gradient(135deg,#6366f1,#06b6d4);border-radius:12px;
                      display:flex;align-items:center;justify-content:center;font-size:20px;">🤖</div>
          <div>
            <div style="font-size:15px;font-weight:700;color:#F1F5F9">BlinkBot {mode_badge}</div>
            <div style="font-size:11px;color:#1D4DFF">Senior AI Business Analyst • Always Online</div>
          </div>
          <div style="margin-left:auto;background:rgba(16,185,129,.15);border:1px solid rgba(16,185,129,.3);
                      border-radius:20px;padding:4px 10px;font-size:10px;color:#22C55E">● Live</div>
        </div>
        """, unsafe_allow_html=True)
    with bb_mem_col:
        mem_items = [
            ("💬 Turns",         str(_ui_mem.turn_count)),
            ("🧠 Last Topic",    _ui_mem.last_intent    or "—"),
            ("📍 Last City",     _ui_mem.last_city       or "—"),
            ("⭐ Last Product",  _ui_mem.last_product    or "—"),
            ("🏷️ Last Category", _ui_mem.last_category  or "—"),
        ]
        rows_html = "".join([
            f'<div style="display:flex;justify-content:space-between;padding:5px 0;'
            f'border-bottom:1px solid rgba(255,255,255,.05)">'
            f'<span style="font-size:10px;color:#64748B">{lbl}</span>'
            f'<span style="font-size:10px;font-weight:600;color:#1D4DFF;font-family:monospace">{val}</span>'
            f'</div>' for lbl, val in mem_items
        ])
        topic_stack = " → ".join(_ui_mem.intent_stack) if _ui_mem.intent_stack else "—"
        st.markdown(f"""
        <div style="background:#14171C;border:1px solid #262B33;box-shadow:0 1px 2px rgba(0,0,0,.35);border-radius:12px;padding:14px 16px;">
          <div style="font-size:10px;font-weight:600;color:#1D4DFF;text-transform:uppercase;
                      letter-spacing:.08em;margin-bottom:8px">🧠 Conversation Memory</div>
          {rows_html}
          <div style="margin-top:8px;padding:6px 8px;background:rgba(99,102,241,.07);border-radius:6px;">
            <div style="font-size:9px;color:#64748B;margin-bottom:2px">TOPIC TRAIL</div>
            <div style="font-size:10px;color:#1D4DFF">{topic_stack}</div>
          </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    if "blinkbot_history" not in st.session_state:
        welcome = (
            f"👋 **Hi! I'm BlinkBot** — now powered by **Claude** (Anthropic ✨).\n\n"
            f"I've analyzed **{len(df):,} records** and I have full conversational memory. "
            f"Ask me anything in plain English — I'll answer with data, a chart, and a recommendation.\n\n"
            f"Try: *'Give me a full summary'* · *'Which city should we focus on?'* · *'Why is Grocery underperforming?'*"
            if (use_ai_mode and api_key) else
            f"👋 **Hi! I'm BlinkBot** — your AI Business Analyst with memory.\n\n"
            f"I've analyzed **{len(df):,} records**. Every answer comes with an inline chart.\n\n"
            f"💡 *Enable **LLM Mode** in the sidebar → paste your **Claude API key** from console.anthropic.com*\n\n"
            f"Try: *'Give me a summary'* · *'Which city is worst?'* · *'Best product?'*"
        )
        st.session_state.blinkbot_history  = [{"role":"bot","msg":welcome,"fig_json":None}]

    if "bb_messages_llm" not in st.session_state:
        st.session_state.bb_messages_llm = []

    for _msg_idx, msg in enumerate(st.session_state.blinkbot_history):
        css_class = "chat-message-bot" if msg["role"] == "bot" else "chat-message-user"
        prefix    = "" if msg["role"] == "bot" else "💬 "
        st.markdown(f'<div class="{css_class}">{prefix}{msg["msg"]}</div>', unsafe_allow_html=True)
        if msg["role"] == "bot" and msg.get("fig_json"):
            restored = _fig_from_json(msg["fig_json"])
            if restored:
                st.plotly_chart(restored, use_container_width=True, key=f"bb_fig_{_msg_idx}")

    st.markdown("**💡 Quick Questions:**")
    QUICK_BASE = [
        ("📊 Summary",       "Give me a full business summary"),
        ("🏆 Best Product",  "Which product is performing best?"),
        ("📍 City Analysis", "Which city is performing worst?"),
        ("⚡ Influencers",   "How is influencer marketing performing?"),
    ]
    QUICK_FOLLOWUP: list[tuple[str, str]] = []
    if _ui_mem.last_intent == "city" and _ui_mem.last_city:
        QUICK_FOLLOWUP.append(("⚖️ Compare Cities",   "Compare best vs worst city"))
    if _ui_mem.last_intent in ("revenue","summary") and _ui_mem.last_category:
        QUICK_FOLLOWUP.append(("🏷️ Category Drill",   f"Tell me more about {_ui_mem.last_category}"))
    if _ui_mem.last_product:
        QUICK_FOLLOWUP.append(("📦 Reorder Risk",      f"Inventory risk for {_ui_mem.last_product}"))
    if _ui_mem.turn_count > 0:
        QUICK_FOLLOWUP.append(("🔄 Tell Me More",      "Tell me more"))

    display_items = (QUICK_FOLLOWUP + QUICK_BASE)[:4]
    quick_cols    = st.columns(len(display_items))
    clicked_quick = None
    for i, (btn_label, q_text) in enumerate(display_items):
        with quick_cols[i]:
            if st.button(btn_label, key=f"bb_q{i}", use_container_width=True):
                clicked_quick = q_text

    with st.form(key="bb_main_form", clear_on_submit=True):
        fc1, fc2 = st.columns([5, 1])
        with fc1:
            ph = (
                "Ask anything — I'll answer with data and a chart..."
                if (use_ai_mode and api_key)
                else "e.g. What is my total profit? Which city is weakest?"
            )
            user_input = st.text_input("Ask BlinkBot...", placeholder=ph, label_visibility="collapsed")
        with fc2:
            submitted = st.form_submit_button("Ask 🤖", use_container_width=True)

    question_to_answer = None
    if submitted and user_input.strip():
        question_to_answer = user_input.strip()
    elif clicked_quick:
        question_to_answer = clicked_quick

    if question_to_answer:
        st.session_state.blinkbot_history.append({"role":"user","msg":question_to_answer,"fig_json":None})
        st.session_state.bb_messages_llm.append({"role":"user","content":question_to_answer})

        response_fig     = _detect_chart_for_question(question_to_answer, _bb_ctx_live, df)
        response_fig_json = _fig_to_json(response_fig)

        if use_ai_mode and api_key:
            system_prompt = _build_llm_system_prompt(df, kpis)
            clean_messages = _sanitise_messages(st.session_state.bb_messages_llm)

            st.markdown(f'<div class="chat-message-user">💬 {question_to_answer}</div>', unsafe_allow_html=True)
            stream_placeholder = st.empty()
            full_response      = ""
            error_occurred     = False

            for chunk in _call_claude_stream(clean_messages, system_prompt, api_key):
                full_response += chunk
                if "⚠️" in chunk:
                    error_occurred = True
                stream_placeholder.markdown(f'<div class="chat-message-bot">{full_response}▊</div>', unsafe_allow_html=True)

            stream_placeholder.markdown(f'<div class="chat-message-bot">{full_response}</div>', unsafe_allow_html=True)

            if response_fig and not error_occurred:
                st.plotly_chart(response_fig, use_container_width=True, key="bb_stream_chart")

            if not error_occurred:
                st.session_state.bb_messages_llm.append({"role": "assistant", "content": full_response})
            else:
                st.session_state.bb_messages_llm = []

            if len(st.session_state.bb_messages_llm) > _LLM_HISTORY_LIMIT * 2:
                st.session_state.bb_messages_llm = st.session_state.bb_messages_llm[-_LLM_HISTORY_LIMIT:]

            st.session_state.blinkbot_history.append({
                "role": "bot", "msg": full_response,
                "fig_json": response_fig_json if not error_occurred else None,
            })
            st.rerun()
        else:
            response_text, response_fig_rb = blinkbot_analyze(question_to_answer, df)
            final_fig = response_fig_rb or response_fig
            st.session_state.blinkbot_history.append({
                "role": "bot", "msg": response_text, "fig_json": _fig_to_json(final_fig),
            })
            st.rerun()

    if len(st.session_state.blinkbot_history) > 1:
        cl1, cl2 = st.columns([1, 5])
        with cl1:
            if st.button("🗑️ Clear Chat & Memory", type="secondary", key="clear_chat", use_container_width=True):
                st.session_state.blinkbot_history  = []
                st.session_state.bb_messages_llm   = []
                st.session_state.bb_memory         = ConversationMemory().to_dict()
                st.rerun()


# ══════════════════════════════════════════════════════════════════════════════════
# ── PAGE 9 — DATA EXPLORER
# ══════════════════════════════════════════════════════════════════════════════════

def render_data_explorer():
    page_header("Data Explorer", "Search · Filter · Data Quality & Trust")

    dq = data_quality_report(df)
    q1, q2, q3, q4 = st.columns(4)
    for col, icon, label, val in [
        (q1,"🧾","Total Rows",    f"{dq['total_rows']:,}"),
        (q2,"📊","Total Columns", f"{dq['total_cols']}"),
        (q3,"❓","Missing Values",f"{dq['missing_total']:,}"),
        (q4,"🔁","Duplicate Rows",f"{dq['dup_rows']:,}"),
    ]:
        with col:
            kpi_card(label, val)

    validation_ok = dq["missing_total"] == 0 and dq["dup_rows"] == 0
    status_txt = "✅ No missing values or duplicates detected in the current (filtered) view" if validation_ok else "⚠️ Data quality issues detected below"
    status_clr = "#22C55E" if validation_ok else "#f59e0b"
    st.markdown(f'<div style="margin:10px 0 20px;font-size:12px;font-weight:600;color:{status_clr};background:rgba(255,255,255,.05);padding:10px 14px;border-radius:8px">{status_txt}</div>', unsafe_allow_html=True)

    if dq["city_map"]:
        st.markdown('<div class="section-head">CITY NAME STANDARDIZATION APPLIED</div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="narrative-box">The following city aliases were detected in your upload and merged '
            'into one canonical name so they are not double-counted:<br>' +
            "<br>".join(f"<b>{k}</b> → {v}" for k, v in dq["city_map"].items()) + "</div>",
            unsafe_allow_html=True,
        )

    if len(dq["missing_by_col"]) > 0:
        st.markdown('<div class="section-head">MISSING VALUES BY COLUMN</div>', unsafe_allow_html=True)
        miss_df = dq["missing_by_col"].reset_index()
        miss_df.columns = ["Column", "Missing Count"]
        st.dataframe(miss_df, use_container_width=True, height=min(300, 40 + 32*len(miss_df)))

    st.markdown('<div class="section-head">SEARCH & FILTER RECORDS</div>', unsafe_allow_html=True)
    search_term = st.text_input("Search across all text columns", placeholder="Type to search product, city, category...")
    view_df = df.copy()
    if search_term:
        text_cols = view_df.select_dtypes(include="object").columns
        mask = pd.Series(False, index=view_df.index)
        for c in text_cols:
            mask |= view_df[c].astype(str).str.contains(search_term, case=False, na=False)
        view_df = view_df[mask]
        st.caption(f"{len(view_df):,} rows match '{search_term}'")

    st.dataframe(view_df, use_container_width=True, height=400)
    st.download_button("⬇ Download Current View (CSV)", view_df.to_csv(index=False), "novams_explorer.csv", "text/csv")

    st.markdown('<div class="section-head">COLUMN TYPES</div>', unsafe_allow_html=True)
    dtype_df = dq["dtypes"].reset_index()
    dtype_df.columns = ["Column", "Type"]
    st.dataframe(dtype_df, use_container_width=True, height=min(350, 40 + 32*len(dtype_df)))

def render_data_engine():
    """
    Data Engine — schema-agnostic profiling for the currently active
    dataset. Reuses page_header()/narrative()/kpi_card() for visual
    consistency and the already-filtered `df`, so it stays in sync with
    the sidebar filters. Does not touch any existing calculation.
    """
    page_header("Data Engine", "Automatic profiling · quality · relationships · domain detection")

    narrative(
        "<b>What this does:</b> runs the dataset through a schema-agnostic engine that profiles "
        "every column, scores data quality, discovers table relationships, detects the likely "
        "business domain, and calculates whichever metrics the columns actually support — "
        "without sending any raw rows to an LLM."
    )

    if st.button("🔍 Run Data Engine on current dataset", type="primary"):
        with st.spinner("Profiling, validating, and analyzing..."):
            engine = DataEngine()
            st.session_state["_data_engine_output"] = engine.run(dataframes={"active_dataset": df})

    output = st.session_state.get("_data_engine_output")
    if not output:
        st.info("Click the button above to profile the current (filtered) dataset.")
        return

    m1, m2, m3, m4 = st.columns(4)
    with m1: kpi_card("Detected Domain", output["domain"].replace("_", " ").title())
    with m2: kpi_card("Domain Confidence", f"{output['domain_confidence']*100:.0f}%")
    with m3: kpi_card("Data Quality Score", f"{output['data_quality_score']}/100")
    with m4: kpi_card("Rows Profiled", f"{output['rows']:,}")

    st.markdown('<div class="section-head">Calculated Metrics</div>', unsafe_allow_html=True)
    if output["metrics"]:
        met_df = pd.DataFrame([
            {"Metric": k.replace("_", " ").title(), "Value": round(v["value"], 2), "Formula": v["formula"]}
            for k, v in output["metrics"].items()
        ])
        st.dataframe(met_df, use_container_width=True, hide_index=True)
    else:
        st.caption("No metrics could be computed from the available columns.")

    st.markdown('<div class="section-head">Data Quality Issues</div>', unsafe_allow_html=True)
    for table_name, q in output["quality"].items():
        if q["issues"]:
            with st.expander(f"{table_name} — {q['score']}/100 ({q['status']})"):
                for issue in q["issues"]:
                    st.markdown(f"- **[{issue['severity']}]** {issue['issue']}" +
                                (f" — `{issue['column']}`" if issue.get("column") else ""))
        else:
            st.success(f"{table_name} — {q['score']}/100, no issues detected.")

    if output["relationships"]:
        st.markdown('<div class="section-head">Discovered Relationships</div>', unsafe_allow_html=True)
        rel_df = pd.DataFrame(output["relationships"])
        st.dataframe(rel_df, use_container_width=True, hide_index=True)

    st.markdown('<div class="section-head">Recommended Dashboard Sections</div>', unsafe_allow_html=True)
    st.write(" · ".join(output["dashboard_recommendations"]["recommended_sections"]))

    st.markdown('<div class="section-head">AI Interpretation (optional)</div>', unsafe_allow_html=True)
    st.caption("Uses the same Claude key as BlinkBot's LLM Mode, if enabled in the sidebar. "
               "Only the compact summary below is sent — never raw rows.")
    context = build_llm_context(output)
    with st.expander("View the exact context sent to Claude"):
        st.json(context)
    if st.button("🧠 Interpret with Claude"):
        with st.spinner("Interpreting..."):
            st.markdown(interpret_with_claude(context, api_key=api_key if use_ai_mode else None))

    with st.expander("Full structured JSON output"):
        st.json(output)
# ══════════════════════════════════════════════════════════════════════════════════
# ── MAIN — DISPATCH TO ACTIVE PAGE
# ══════════════════════════════════════════════════════════════════════════════════

_PAGE_RENDERERS = {
    "Executive Overview":      render_executive_overview,
    "Sales Analytics":         render_sales_analytics,
    "Box Plot Analysis":       render_box_plot_analysis,
    "Delivery Analytics":      render_delivery_analytics,
    "Inventory Intelligence":  render_inventory_intelligence,
    "Operations":              render_operations,
    "Customer Analytics":      render_customer_analytics,
    "Finance":                 render_finance,
    "AI Analyst":              render_ai_analyst,
    "Data Explorer":           render_data_explorer,
    "Sales by Location":       render_sales_by_location,
    "Product Analytics":       render_product_analytics,
    "Data Engine":             render_data_engine,
}

_PAGE_RENDERERS.get(active_page, render_executive_overview)()

# ── FOOTER ────────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="footer">
  NovaMS — Nova Management Solutions &nbsp;·&nbsp;
  Developed by <span class="dev">Ayush Mishra</span> &nbsp;·&nbsp;
  Pandas · SciPy · scikit-learn · Streamlit · Plotly
</div>
""", unsafe_allow_html=True)
