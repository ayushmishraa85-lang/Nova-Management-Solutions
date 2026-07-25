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

/* ── Sidebar — dark, disciplined, single accent ── */
section[data-testid="stSidebar"] {
  background: var(--nova-sidebar);
  border-right: 1px solid rgba(255,255,255,.06);
}
section[data-testid="stSidebar"] * { color: #CBD5E1; }
section[data-testid="stSidebar"] h1, section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3, section[data-testid="stSidebar"] h4 { color: #F8FAFC; }
section[data-testid="stSidebar"] .stMarkdown p { color: #94A3B8; }
section[data-testid="stSidebar"] hr { border-color: rgba(255,255,255,.08); }
section[data-testid="stSidebar"] input[type="radio"] { accent-color: var(--nova-blue); }
section[data-testid="stSidebar"] [data-testid="stWidgetLabel"] p {
  font-size: 10.5px; font-weight: 700; color: #64748B; text-transform: uppercase; letter-spacing: .08em;
}
section[data-testid="stSidebar"] [role="radiogroup"] label {
  padding: 7px 10px; border-radius: 6px; margin-bottom: 1px;
}
section[data-testid="stSidebar"] [role="radiogroup"] label:hover { background: var(--nova-sidebar-2); }
section[data-testid="stSidebar"] .stTextInput input,
section[data-testid="stSidebar"] .stSelectbox div[data-baseweb="select"] > div {
  background: var(--nova-sidebar-2); border-color: rgba(255,255,255,.1); color: #F1F5F9;
}

.nav-brand { text-align:center; padding:10px 0 20px; }
.nav-brand .logo {
  width:38px;height:38px;background:var(--nova-blue);
  border-radius:9px;display:inline-flex;align-items:center;justify-content:center;
  font-size:18px;font-weight:700;color:#fff;margin-bottom:10px;
}
.nav-brand .name { font-size:15px;font-weight:700;color:#F8FAFC;letter-spacing:-.01em; }
.nav-brand .tag { font-size:10px;color:#64748B;margin-top:2px; letter-spacing:.06em; text-transform:uppercase; }

/* ── Global Streamlit primary accent (buttons, tabs, focus rings) ── */
.stButton>button, [data-testid="stFormSubmitButton"] button, [data-testid="stBaseButton-primary"] {
  border-radius: 7px; font-weight: 600;
}
</style>
""", unsafe_allow_html=True)

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


def resolve_references(question: str, mem: ConversationMemory) -> str:
    q = question.lower().strip()
    city_refs = ["that city", "that region", "that location", "there", "that place"]
    if any(ref in q for ref in city_refs) and mem.last_city:
        q = q.replace("that city", mem.last_city) \
              .replace("that region", mem.last_city) \
              .replace("that location", mem.last_city) \
              .replace("there", mem.last_city) \
              .replace("that place", mem.last_city)
    prod_refs = ["that product", "it", "that item", "the same product", "that one"]
    if any(ref in q for ref in prod_refs) and mem.last_product:
        for ref in prod_refs:
            q = q.replace(ref, mem.last_product)
    cat_refs = ["that category", "that segment", "that section"]
    if any(ref in q for ref in cat_refs) and mem.last_category:
        for ref in cat_refs:
            q = q.replace(ref, mem.last_category)
    more_refs = ["tell me more", "more details", "expand", "elaborate", "explain more", "go deeper"]
    if any(ref in q for ref in more_refs) and mem.last_intent:
        q = mem.last_intent
    if q.strip() in ("why", "why?", "how come") and mem.last_intent:
        q = f"explain {mem.last_intent}"
    return q


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
    return dict(total_r=total_r, total_o=total_o, total_p=total_p, mgn=mgn,
                cat_r=cat_r, city_r=city_r, prod_r=prod_r, best_m=best_m,
                inf_y_rev=inf_y_rev, inf_n_rev=inf_n_rev, inf_lift=inf_lift,
                ord_lift=ord_lift, disc_grp=disc_grp,
                n_inf_y=len(df[df["Influencer Active"]=="Yes"]) if "Influencer Active" in df.columns else 0)


# ── Chart Factories — used by BlinkBot + Sales/Delivery/etc pages ───────────────

def _chart_revenue_by_category(ctx: dict) -> go.Figure:
    cat_r = ctx["cat_r"]
    fig = go.Figure(go.Bar(
        x=cat_r.index.tolist(), y=cat_r.values,
        marker_color=[CAT_CLR.get(c, "#6366f1") for c in cat_r.index],
        marker_line_width=0, opacity=0.85,
        text=[fmt(v) for v in cat_r.values], textposition="outside",
        textfont=dict(color="#F1F5F9", size=10),
    ))
    fig.update_layout(**PLOTLY_BASE,
        title=dict(text="💬 Revenue by Category", font=dict(color="#1D4DFF", size=12)),
        height=240, yaxis=dict(tickprefix="₹", **_AXIS_DEFAULTS), showlegend=False)
    return fig


def _chart_city_ranking(ctx: dict) -> go.Figure:
    cr = ctx["city_r"]
    colors = ["#10b981" if i == 0 else "#ef4444" if i == len(cr)-1 else "#6366f1"
              for i in range(len(cr))]
    fig = go.Figure(go.Bar(
        x=cr.values, y=cr.index.tolist(), orientation="h",
        marker_color=colors, marker_line_width=0, opacity=0.85,
        text=[fmt(v) for v in cr.values], textposition="outside",
        textfont=dict(color="#F1F5F9", size=10),
    ))
    fig.update_layout(**PLOTLY_BASE,
        title=dict(text="💬 City Revenue Ranking", font=dict(color="#1D4DFF", size=12)),
        height=240, xaxis=dict(tickprefix="₹", **_AXIS_DEFAULTS),
        yaxis=dict(autorange="reversed", **_AXIS_DEFAULTS), showlegend=False)
    return fig


def _chart_top_products(ctx: dict, n: int = 8) -> go.Figure:
    pr = ctx["prod_r"].head(n)
    fig = go.Figure(go.Bar(
        x=pr.values, y=pr.index.tolist(), orientation="h",
        marker=dict(color=pr.values, colorscale=[[0,"#312e81"],[0.5,"#6366f1"],[1,"#06b6d4"]], showscale=False),
        marker_line_width=0,
        text=[fmt(v) for v in pr.values], textposition="outside",
        textfont=dict(color="#F1F5F9", size=10),
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


# ── BlinkBot intent handlers (rule-based fallback) ────────────────────────────────

def _bb_greeting(q: str, ctx: dict, df: pd.DataFrame, mem: ConversationMemory) -> BotReply | None:
    if not any(w in q for w in ["hello","hi","hey","namaste","hii"]): return None
    c         = ctx
    returning = mem.turn_count > 0
    opener    = (f"Welcome back! You've asked **{mem.turn_count}** question(s) so far."
                 if returning else f"I've analyzed **{len(df):,} records** and I'm ready to help.")
    mem.update("greeting")
    text = (
        ResponseBuilder("👋", "Hi! I'm BlinkBot — your AI Business Analyst")
        .answer(opener)
        .metric("Total Revenue", fmt(c["total_r"]), "💰")
        .metric("Top Category",  c["cat_r"].index[0]  if c["cat_r"]  is not None else "N/A", "🏆")
        .metric("Top City",      c["city_r"].index[0] if c["city_r"] is not None else "N/A", "📍")
        .metric("Total Orders",  f"{int(c['total_o']):,}", "🛒")
        .followup("'Give me a full summary' · 'Which city is weakest?' · 'Best product?'")
        .build()
    )
    return text, _chart_revenue_by_category(ctx)


def _bb_summary(q: str, ctx: dict, df: pd.DataFrame, mem: ConversationMemory) -> BotReply | None:
    if not any(w in q for w in ["summary","overview","analyze","brief","insights","tell me"]): return None
    c       = ctx
    aov     = c["total_r"] / c["total_o"] if c["total_o"] else 0
    weakest = c["city_r"].index[-1] if c["city_r"] is not None else "N/A"
    mem.update("summary",
               city     = c["city_r"].index[0] if c["city_r"] is not None else None,
               product  = c["prod_r"].index[0] if c["prod_r"] is not None else None,
               category = c["cat_r"].index[0]  if c["cat_r"]  is not None else None)
    text = (
        ResponseBuilder("📋", "Executive Summary")
        .answer(f"Here's everything at a glance across **{len(df):,} records**.")
        .metric("Total Revenue",  fmt(c["total_r"]), "💰")
        .metric("Total Profit",   f"{fmt(c['total_p'])} ({c['mgn']:.1f}% margin)", "📈")
        .metric("Total Orders",   f"{int(c['total_o']):,} | AOV: {fmt(aov)}", "🛒")
        .metric("Best Category",  f"{c['cat_r'].index[0] if c['cat_r'] is not None else 'N/A'} "
                                  f"({c['cat_r'].iloc[0]/c['total_r']*100:.1f}% of rev)", "🏆")
        .metric("Best City",      f"{c['city_r'].index[0] if c['city_r'] is not None else 'N/A'} "
                                  f"— {fmt(c['city_r'].iloc[0]) if c['city_r'] is not None else 'N/A'}", "📍")
        .metric("Best Product",   c["prod_r"].index[0] if c["prod_r"] is not None else "N/A", "⭐")
        .context(f"⚠️ **{weakest}** is your weakest region — investigate and run targeted promotions.")
        .tip(f"Focus on {c['cat_r'].index[0] if c['cat_r'] is not None else 'top category'} "
             f"in {c['city_r'].index[0] if c['city_r'] is not None else 'top city'} — this is your growth engine.")
        .followup(f"'Tell me about {weakest}' · 'Breakdown by category' · 'Best product?'")
        .build()
    )
    return text, _chart_summary_snapshot(ctx)


def _bb_revenue(q: str, ctx: dict, df: pd.DataFrame, mem: ConversationMemory) -> BotReply | None:
    if not any(w in q for w in ["revenue","how much","earnings","sales total"]): return None
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
    rb = (
        ResponseBuilder("📊", "Revenue Analysis")
        .answer(f"Total revenue is **{fmt(c['total_r'])}** across **{len(df):,} transactions**.")
        .metric("Best category",   f"{top_cat} ({c['cat_r'].iloc[0]/c['total_r']*100:.1f}%)" if c["cat_r"] is not None else "N/A", "🏆")
        .metric("Top city",        top_city, "📍")
        .metric("Net profit",      f"{fmt(c['total_p'])} ({c['mgn']:.1f}% margin)", "💰")
        .metric("Avg order value", fmt(c["total_r"]/c["total_o"] if c["total_o"] else 0), "🛒")
    )
    if extra_ctx: rb = rb.context(extra_ctx)
    rb = rb.tip(f"Double down on **{top_cat}** in **{top_city}** — allocate 30% more marketing budget here.")
    rb = rb.followup("'Break down by category' · 'Which product earns most?' · 'Compare cities'")
    return rb.build(), _chart_revenue_by_category(ctx)


def _bb_profit(q: str, ctx: dict, df: pd.DataFrame, mem: ConversationMemory) -> BotReply | None:
    if not any(w in q for w in ["profit","margin","net"]): return None
    c          = ctx
    bm         = c["best_m"]
    prev_topic = mem.last_intent
    mem.update("profit", category=bm.index[0] if bm is not None else None)
    rb = (
        ResponseBuilder("💰", "Profit & Margin Analysis")
        .answer(f"Total profit is **{fmt(c['total_p'])}** on revenue of **{fmt(c['total_r'])}**.")
        .metric("Profit margin",      f"{c['mgn']:.1f}%", "📈")
        .metric("Highest-margin cat", f"{bm.index[0] if bm is not None else 'N/A'} ({bm.iloc[0]:.1f}%)" if bm is not None else "N/A", "🏆")
        .metric("Lowest-margin cat",  f"{bm.index[-1] if bm is not None else 'N/A'} — needs review"     if bm is not None else "N/A", "⚠️")
        .metric("Keep per ₹100",      f"₹{c['mgn']:.0f}", "🪙")
    )
    if prev_topic == "revenue":
        rb = rb.context("You were just looking at revenue — margin tells you how much you actually keep.")
    rb = rb.tip(f"Grow **{bm.index[0] if bm is not None else 'top category'}** volume — best return per rupee sold.")
    rb = rb.followup("'Which product has best margin?' · 'Revenue breakdown' · 'Discount impact on margin?'")
    return rb.build(), _chart_profit_margin_by_category(ctx, df)


def _bb_best_product(q: str, ctx: dict, df: pd.DataFrame, mem: ConversationMemory) -> BotReply | None:
    if not any(w in q for w in ["best product","top product","number one","highest selling"]): return None
    pr = ctx["prod_r"]
    if pr is None: return "Product data not available.", None
    top3   = pr.head(3)
    medals = ["🥇","🥈","🥉"]
    lines  = "\n".join([f"{medals[i]} **{top3.index[i]}** — {fmt(top3.iloc[i])}" for i in range(len(top3))])
    mem.update("best_product", product=top3.index[0])
    text = (
        ResponseBuilder("🏆", "Top Products by Revenue")
        .answer(f"Your #1 product is **{top3.index[0]}** generating **{fmt(top3.iloc[0])}**.\n\n{lines}")
        .metric("Share of total", f"{top3.iloc[0]/ctx['total_r']*100:.1f}%", "📊")
        .metric("Runner-up gap",  fmt(top3.iloc[0]-top3.iloc[1]) if len(top3)>1 else "—", "↔️")
        .tip(f"Keep **{top3.index[0]}** always in stock. Bundle with **{top3.index[1] if len(top3)>1 else '#2'}** to boost AOV.")
        .followup(f"'Worst products?' · 'Which city sells {top3.index[0]} most?' · 'Inventory alert?'")
        .build()
    )
    return text, _chart_top_products(ctx)


def _bb_worst_product(q: str, ctx: dict, df: pd.DataFrame, mem: ConversationMemory) -> BotReply | None:
    if not any(w in q for w in ["worst product","lowest","weakest product"]): return None
    pr = ctx["prod_r"]
    if pr is None: return "Product data not available.", None
    worst = pr.tail(3).sort_values()
    lines = "\n".join([f"{['🔴','🟡','🟡'][i]} **{worst.index[i]}** — {fmt(worst.iloc[i])}" for i in range(len(worst))])
    mem.update("worst_product", product=worst.index[0])
    text = (
        ResponseBuilder("⚠️", "Underperforming Products")
        .answer(f"Lowest revenue: **{worst.index[0]}** at only **{fmt(worst.iloc[0])}**.\n\n{lines}")
        .metric("Gap to #1", fmt(ctx["prod_r"].iloc[0] - worst.iloc[0]), "↕️")
        .tip("Run a 30-day promotion on these. If no improvement, discontinue the lowest performer.")
        .followup(f"'Best product?' · 'Category for {worst.index[0]}?' · 'Discount to boost it?'")
        .build()
    )
    return text, _chart_top_products(ctx, n=8)


def _bb_city(q: str, ctx: dict, df: pd.DataFrame, mem: ConversationMemory) -> BotReply | None:
    if not any(w in q for w in ["city","region","location","where"]): return None
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
    if gap_pct > 50:
        rb = rb.context(f"⚠️ {weakest} underperforms by **{gap_pct:.0f}%** — big opportunity here.")
    rb = rb.tip(f"Replicate {best}'s success in {weakest} — start with influencer campaigns for top 3 products.")
    rb = rb.followup(f"'Revenue in {weakest}' · 'Best product in {best}' · 'Compare cities'")
    return rb.build(), _chart_city_ranking(ctx)


def _bb_category(q: str, ctx: dict, df: pd.DataFrame, mem: ConversationMemory) -> BotReply | None:
    if not any(w in q for w in ["category","segment","best category"]): return None
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
        .followup(f"'Products in {cat_r.index[0]}' · 'Which city buys most?' · 'Margin by category'")
        .build()
    )
    return text, _chart_revenue_by_category(ctx)


def _bb_influencer(q: str, ctx: dict, df: pd.DataFrame, mem: ConversationMemory) -> BotReply | None:
    if not any(w in q for w in ["influencer","marketing","campaign"]): return None
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
        .followup("'Which category benefits most?' · 'Top cities for campaigns?' · 'Influencer ROI?'")
        .build()
    )
    return text, _chart_influencer_lift(ctx, df)


def _bb_orders(q: str, ctx: dict, df: pd.DataFrame, mem: ConversationMemory) -> BotReply | None:
    if not any(w in q for w in ["orders","order count","volume","how many orders"]): return None
    c      = ctx
    aov    = c["total_r"] / c["total_o"] if c["total_o"] else 0
    top_co = df.groupby("City")["Orders"].sum().sort_values(ascending=False) if "City" in df.columns else None
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


def _bb_discount(q: str, ctx: dict, df: pd.DataFrame, mem: ConversationMemory) -> BotReply | None:
    if not any(w in q for w in ["discount","offer","deal","promo"]): return None
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
        .followup("'Discount vs profit margin?' · 'Which category discounts best?' · 'Order volume vs discount'")
        .build()
    )
    return text, _chart_discount_curve(ctx)


def _bb_inventory(q: str, ctx: dict, df: pd.DataFrame, mem: ConversationMemory) -> BotReply | None:
    if not any(w in q for w in ["stock","inventory","reorder","shortage"]): return None
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


def _bb_compare(q: str, ctx: dict, df: pd.DataFrame, mem: ConversationMemory) -> BotReply | None:
    if not any(w in q for w in ["compare","vs","versus","against","difference between"]): return None
    cr = ctx["city_r"]
    if cr is not None and len(cr) >= 2:
        c1, c2 = cr.index[0], cr.index[-1]
        diff   = cr.iloc[0] - cr.iloc[-1]
        gap    = diff / cr.iloc[-1] * 100 if cr.iloc[-1] else 0
        mem.update("compare", city=c1)
        text = (
            ResponseBuilder("⚖️", f"Comparison: {c1} vs {c2}")
            .answer(f"**{c1}** outperforms **{c2}** by **{gap:.0f}%**.")
            .metric(c1, fmt(cr.iloc[0]), "🟢")
            .metric(c2, fmt(cr.iloc[-1]), "🔴")
            .metric("Revenue gap", fmt(diff), "↕️")
            .tip(f"Investigate what makes {c1} strong — replicate those tactics in {c2}.")
            .followup(f"'Products in {c2}' · 'Influencer coverage in {c2}' · 'Category split in {c1}'")
            .build()
        )
        return text, _chart_city_ranking(ctx)
    return None


def _bb_fallback(q: str, ctx: dict, df: pd.DataFrame, mem: ConversationMemory) -> BotReply:
    hint    = f"\n\n💬 *Last topic: **{mem.last_intent}** — say 'tell me more' to expand.*" if mem.last_intent else ""
    cols_av = ", ".join(df.columns.tolist())
    text = (
        ResponseBuilder("🤔", "I didn't quite catch that")
        .answer(
            "I can help you with:\n"
            "- 💰 Revenue & Profit\n- 🏆 Best / worst products\n- 📍 City performance\n"
            "- 🏷️ Category breakdown\n- ⚡ Influencer impact\n- 🛒 Orders & volume\n"
            "- 🏷️ Discount analysis\n- 📦 Inventory alerts\n- ⚖️ Compare cities" + hint
        )
        .context(f"Available columns: {cols_av}")
        .followup("'Give me a summary' · 'Which city is worst?' · 'Best product?'")
        .build()
    )
    return text, None


_BB_HANDLERS = [
    _bb_greeting, _bb_compare, _bb_summary, _bb_revenue, _bb_profit,
    _bb_best_product, _bb_worst_product, _bb_city, _bb_category,
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
    q   = resolve_references(q_raw, mem)
    ctx = _bb_context(df)
    for handler in _BB_HANDLERS:
        result = handler(q, ctx, df, mem)
        if result is not None:
            _save_memory(mem)
            return result
    _save_memory(mem)
    return _bb_fallback(q, ctx, df, mem)


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
    if any(w in q for w in ["compare","vs","versus","against","city","region","where","location"]):
        return _chart_city_ranking(ctx)
    if any(w in q for w in ["category","segment"]):
        return _chart_revenue_by_category(ctx)
    if any(w in q for w in ["best product","top product","worst","lowest","product","sku","item"]):
        return _chart_top_products(ctx)
    if any(w in q for w in ["profit","margin","net"]):
        return _chart_profit_margin_by_category(ctx, df)
    if any(w in q for w in ["influencer","marketing","campaign"]):
        return _chart_influencer_lift(ctx, df)
    if any(w in q for w in ["orders","volume","order count"]):
        return _chart_orders_by_city(df)
    if any(w in q for w in ["discount","promo","offer","deal"]):
        return _chart_discount_curve(ctx)
    if any(w in q for w in ["summary","overview","revenue","earnings","how much"]):
        return _chart_summary_snapshot(ctx)
    if any(w in q for w in ["hello","hi","hey"]):
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


def missing_data_notice(missing_cols: list[str], context: str):
    st.markdown(f"""
    <div class="missing-box">
      ⚠️ <b>Limited data for {context}.</b> Your uploaded file doesn't include: {", ".join(f"<code>{c}</code>" for c in missing_cols)}.
      This section only shows analytics that can be computed honestly from the columns you do have —
      nothing below is simulated to fill the gap.
    </div>
    """, unsafe_allow_html=True)


NAV_PAGES = [
    "Executive Overview",
    "Sales Analytics",
    "Delivery Analytics",
    "Inventory Intelligence",
    "Operations",
    "Customer Analytics",
    "Finance",
    "AI Analyst",
    "Data Explorer",
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
    </div>
    """, unsafe_allow_html=True)

    st.markdown("#### 🧭 Navigation")
    active_page = st.radio("Go to", NAV_PAGES, label_visibility="collapsed", key="nav_page")

    st.markdown("---")
    st.markdown("#### 📂 Data Source")
    uploaded = st.file_uploader(
        "Upload your CSV or Excel file",
        type=["csv", "xlsx"],
        help="Replace the default dataset. Accepts .csv or .xlsx exports "
             "from Zepto, Blinkit, Swiggy Instamart, or similar platforms.",
    )
    st.markdown("---")

    df_raw = load_default()
    if uploaded is not None:
        try:
            df_raw = load_user_file(uploaded)
            file_kind = "Excel" if uploaded.name.lower().endswith(".xlsx") else "CSV"
            st.success(f"✅ Loaded {len(df_raw):,} rows from **{uploaded.name}** ({file_kind})")
            city_map = st.session_state.get("_city_standardization", {})
            if city_map:
                st.info("🏙️ Standardized city names: " + ", ".join(f"{k}→{v}" for k, v in city_map.items()))
        except ValueError as e:
            st.error(f"❌ {e}")
            st.info("↩️ Falling back to the default sample dataset until a valid file is uploaded.")
        except Exception as e:
            st.error(f"❌ Unexpected error while loading **{uploaded.name}**: {e}")
            st.info("↩️ Falling back to the default sample dataset.")

    st.markdown("#### 🔍 Filters")
    cities     = ["All"] + sorted(df_raw["City"].unique())
    categories = ["All"] + sorted(df_raw["Category"].unique())
    products   = ["All"] + sorted(df_raw["Product Name"].unique())

    sel_city = st.selectbox("City / Region", cities)
    sel_cat  = st.selectbox("Category",      categories)
    sel_inf  = st.selectbox("Influencer",    ["All", "Yes", "No"])
    sel_prod = st.selectbox("Product",       products)
    search   = st.text_input("Search product", placeholder="e.g. Maggi...")

    st.markdown("---")
    st.markdown("#### ⚙️ Settings")
    show_raw     = st.checkbox("Show Raw Data Table (Executive Overview)", value=False)
    show_stats   = st.checkbox("Show Statistical Analysis (Sales Analytics)", value=True)

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
    st.markdown("""
    <div style="font-size:10px;color:#64748B;text-align:center">
      Developed by <strong style="color:#1D4DFF">Ayush Mishra</strong><br>
      FastAPI · Pandas · SciPy · Streamlit
    </div>
    """, unsafe_allow_html=True)


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

    st.markdown('<div class="section-head">Key Performance Indicators</div>', unsafe_allow_html=True)
    c1,c2,c3,c4,c5,c6 = st.columns(6)
    avg_delivery = delivery["avg"]
    with c1: kpi_card("Total Revenue", fmt(kpis["total_rev"]), f"σ = {fmt(kpis['rev_std'])}", "+12.4% WoW", True)
    with c2: kpi_card("Total Profit", fmt(kpis["total_profit"]), "Net margin earnings", "+8.1% WoW", True)
    with c3: kpi_card("Total Orders", f"{int(kpis['total_orders']):,}", "Units sold", "+5.3% WoW", True)
    with c4: kpi_card("Profit Margin", f"{kpis['margin']:.1f}%", "Revenue to profit ratio", "+2.1 pts", True)
    with c5: kpi_card("Avg Delivery Time", f"{avg_delivery:.1f} min", delivery["status"], f"OTD {delivery['otd_pct']:.0f}%", delivery['otd_pct'] >= 85)
    with c6: kpi_card("Top Region", kpis["city_rev"].index[0] if len(kpis["city_rev"]) else "—", fmt(kpis["city_rev"].iloc[0]) if len(kpis["city_rev"]) else "—")

    c7,c8,c9 = st.columns(3)
    with c7: kpi_card("Top Category", kpis["cat_rev"].index[0] if len(kpis["cat_rev"]) else "—", fmt(kpis["cat_rev"].iloc[0]) if len(kpis["cat_rev"]) else "—")
    with c8: kpi_card("Avg Order Value", fmt(kpis["aov"]), "Revenue per order")
    with c9: kpi_card("On-Time Delivery", f"{delivery['otd_pct']:.1f}%", delivery["status"])

    st.markdown("<br>", unsafe_allow_html=True)
    narrative(
        f"<b>What's happening:</b> Revenue stands at <b>{fmt(kpis['total_rev'])}</b> across "
        f"<b>{int(kpis['total_orders']):,}</b> orders, led by <b>{kpis['cat_rev'].index[0]}</b> in "
        f"<b>{kpis['city_rev'].index[0]}</b>. <b>What to do:</b> protect the leading category/city combo "
        f"while running targeted promotions in <b>{kpis['city_rev'].index[-1]}</b>, your weakest region."
    )

    st.markdown('<div class="section-head">SALES SNAPSHOT</div>', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        city_data = df.groupby("City")["Total Revenue"].sum().sort_values(ascending=False).reset_index()
        fig = px.bar(city_data, x="City", y="Total Revenue", color="City",
                     color_discrete_map=CITY_CLR, title="Revenue by City", labels={"Total Revenue":"Revenue (₹)"})
        fig.update_layout(**PLOTLY_LAYOUT, title_font_color="#F1F5F9", showlegend=False)
        fig.update_traces(marker_line_width=0, opacity=0.85)
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

    for msg in st.session_state.blinkbot_history:
        css_class = "chat-message-bot" if msg["role"] == "bot" else "chat-message-user"
        prefix    = "" if msg["role"] == "bot" else "💬 "
        st.markdown(f'<div class="{css_class}">{prefix}{msg["msg"]}</div>', unsafe_allow_html=True)
        if msg["role"] == "bot" and msg.get("fig_json"):
            restored = _fig_from_json(msg["fig_json"])
            if restored:
                st.plotly_chart(restored, use_container_width=True, key=f"bb_fig_{id(msg)}")

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


# ══════════════════════════════════════════════════════════════════════════════════
# ── MAIN — DISPATCH TO ACTIVE PAGE
# ══════════════════════════════════════════════════════════════════════════════════

_PAGE_RENDERERS = {
    "Executive Overview":      render_executive_overview,
    "Sales Analytics":         render_sales_analytics,
    "Delivery Analytics":      render_delivery_analytics,
    "Inventory Intelligence":  render_inventory_intelligence,
    "Operations":              render_operations,
    "Customer Analytics":      render_customer_analytics,
    "Finance":                 render_finance,
    "AI Analyst":              render_ai_analyst,
    "Data Explorer":           render_data_explorer,
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
