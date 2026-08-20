"""
report_charts.py — Chart Factory
===================================
Builds report-quality matplotlib charts and returns them as in-memory PNG
buffers ready to drop into a ReportLab flowable. Chart-type selection follows
the spec's rules (time series -> line, ranking -> horizontal bar, contribution
-> donut only for few categories, etc.) and every chart carries a real title,
axis labels, and number formatting — no unlabeled or decorative charts.
"""

from __future__ import annotations
import io
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np

from . import report_layout as _layout


def _pal() -> list:
    """Always reads the CURRENT chart palette (theme-aware) rather than a
    value frozen at import time — see report_layout.set_theme()."""
    return _layout.CHART_PALETTE

plt.rcParams.update({
    "font.family": "sans-serif",
    "font.size": 8.5,
    "axes.edgecolor": "#CBD5E1",
    "axes.labelcolor": "#475569",
    "text.color": "#0F172A",
    "xtick.color": "#475569",
    "ytick.color": "#475569",
    "axes.grid": True,
    "grid.color": "#E2E8F0",
    "grid.linewidth": 0.6,
    "axes.axisbelow": True,
    "figure.facecolor": "white",
    "axes.facecolor": "white",
})


def _finish(fig, tight=True) -> io.BytesIO:
    buf = io.BytesIO()
    if tight:
        fig.tight_layout()
    fig.savefig(buf, format="png", dpi=200, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return buf


def _short_num(v, is_currency=True):
    try:
        v = float(v)
    except Exception:
        return ""
    sym = "\u20b9" if is_currency else ""
    a = abs(v)
    if a >= 1e7: return f"{sym}{v/1e7:.1f}Cr"
    if a >= 1e5: return f"{sym}{v/1e5:.1f}L"
    if a >= 1e3: return f"{sym}{v/1e3:.0f}K"
    return f"{sym}{v:,.0f}"


def line_trend_chart(labels, values, title: str, y_label: str = "Revenue",
                       forecast_labels=None, forecast_values=None, ci=None,
                       width=6.4, height=2.6):
    """Time-series -> line chart, per spec. Optionally appends a dashed
    forecast segment with a shaded confidence band."""
    fig, ax = plt.subplots(figsize=(width, height))
    x = list(range(len(labels)))
    ax.plot(x, values, color=_pal()[0], linewidth=2, marker="o", markersize=3.5, label="Actual")
    ax.fill_between(x, values, min(values) * 0.0 if min(values) >= 0 else min(values),
                     color=_pal()[0], alpha=0.08)

    if forecast_labels and forecast_values:
        fx = list(range(len(labels) - 1, len(labels) + len(forecast_labels)))
        fy = [values[-1]] + list(forecast_values)
        ax.plot(fx, fy, color=_pal()[3], linewidth=2, linestyle="--", marker="o",
                markersize=3.5, label="Forecast")
        if ci:
            upper = [v + ci for v in fy]
            lower = [max(0, v - ci) for v in fy]
            ax.fill_between(fx, lower, upper, color=_pal()[3], alpha=0.12)
        all_labels = list(labels) + list(forecast_labels)
        ax.set_xticks(list(range(len(all_labels))))
        ax.set_xticklabels(all_labels, rotation=30, ha="right", fontsize=7)
        ax.legend(frameon=False, fontsize=7.5, loc="upper left")
    else:
        step = max(1, len(labels) // 10)
        ax.set_xticks(x[::step])
        ax.set_xticklabels([labels[i] for i in x[::step]], rotation=30, ha="right", fontsize=7)

    ax.set_title(title, fontsize=10, fontweight="bold", color="#0F172A", loc="left", pad=8)
    ax.set_ylabel(y_label, fontsize=8)
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, p: _short_num(v)))
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    return _finish(fig)


def horizontal_ranking_chart(labels, values, title: str, x_label: str = "Revenue",
                               highlight_best_worst=True, width=6.4, height=None,
                               is_currency=True):
    """Ranking/comparison -> horizontal bar chart, per spec."""
    n = len(labels)
    height = height or max(1.8, 0.42 * n + 0.6)
    fig, ax = plt.subplots(figsize=(width, height))
    y = np.arange(n)
    colors_list = [_pal()[0]] * n
    if highlight_best_worst and n > 1:
        colors_list[0] = "#16A34A"
        colors_list[-1] = "#DC2626"
    ax.barh(y, values, color=colors_list, height=0.6)
    ax.set_yticks(y)
    ax.set_yticklabels(labels, fontsize=8)
    ax.invert_yaxis()
    for i, v in enumerate(values):
        ax.text(v, i, f"  {_short_num(v, is_currency)}", va="center", fontsize=7.5, color="#0F172A")
    ax.set_title(title, fontsize=10, fontweight="bold", color="#0F172A", loc="left", pad=8)
    ax.set_xlabel(x_label, fontsize=8)
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda v, p: _short_num(v, is_currency)))
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    ax.grid(axis="y", visible=False)
    return _finish(fig)


def pareto_chart(labels, values, title: str, threshold=80, width=6.4, height=2.8):
    """Contribution/ranking across many items -> Pareto (bar + cumulative
    line), used for Product/Category pages instead of an unreadable pie."""
    n = len(labels)
    cum = np.cumsum(values) / max(1e-9, sum(values)) * 100
    fig, ax1 = plt.subplots(figsize=(width, height))
    x = np.arange(n)
    ax1.bar(x, values, color=_pal()[0], alpha=0.85, width=0.6)
    ax1.set_xticks(x)
    ax1.set_xticklabels(labels, rotation=30, ha="right", fontsize=7)
    ax1.set_ylabel("Revenue", fontsize=8)
    ax1.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, p: _short_num(v)))
    ax2 = ax1.twinx()
    ax2.plot(x, cum, color=_pal()[3], marker="o", markersize=3.5, linewidth=1.8)
    ax2.axhline(threshold, color=_pal()[4], linestyle="--", linewidth=1)
    ax2.set_ylim(0, 110)
    ax2.set_ylabel("Cumulative %", fontsize=8)
    ax2.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, p: f"{v:.0f}%"))
    ax1.set_title(title, fontsize=10, fontweight="bold", color="#0F172A", loc="left", pad=8)
    for spine in ("top",):
        ax1.spines[spine].set_visible(False)
        ax2.spines[spine].set_visible(False)
    return _finish(fig)


def donut_chart(labels, values, title: str, width=4.6, height=3.0):
    """Contribution -> donut, only for a SMALL number of categories, per spec."""
    fig, ax = plt.subplots(figsize=(width, height))
    colors_list = _pal()[: len(labels)]
    wedges, _ = ax.pie(values, colors=colors_list, startangle=90, wedgeprops=dict(width=0.42, edgecolor="white"))
    total = sum(values)
    pcts = [v / total * 100 if total else 0 for v in values]
    legend_labels = [f"{l} \u2014 {p:.0f}%" for l, p in zip(labels, pcts)]
    ax.legend(wedges, legend_labels, loc="center left", bbox_to_anchor=(1.0, 0.5),
              frameon=False, fontsize=7.5)
    ax.set_title(title, fontsize=10, fontweight="bold", color="#0F172A", loc="left", pad=8)
    ax.axis("equal")
    ax.grid(False)
    return _finish(fig, tight=False)


def waterfall_chart(labels, values, title: str, width=6.4, height=2.8):
    """Profit composition -> waterfall, per spec. `values` are signed deltas
    except the first (absolute starting value) and last (absolute total)."""
    fig, ax = plt.subplots(figsize=(width, height))
    n = len(labels)
    running = 0.0
    for i, (label, v) in enumerate(zip(labels, values)):
        is_edge = i == 0 or i == n - 1
        if is_edge:
            bottom = 0
            height_v = v
            running = v
        else:
            bottom = running if v >= 0 else running + v
            height_v = abs(v)
            running += v
        color = "#1D4DFF" if is_edge else ("#16A34A" if v >= 0 else "#DC2626")
        ax.bar(i, height_v, bottom=bottom, color=color, width=0.6)
        label_y = bottom + height_v + (max(values, key=abs) * 0.02 if values else 0)
        ax.text(i, label_y, _short_num(v if not is_edge else running), ha="center", fontsize=7.5)
    ax.set_xticks(range(n))
    ax.set_xticklabels(labels, rotation=20, ha="right", fontsize=7.5)
    ax.set_title(title, fontsize=10, fontweight="bold", color="#0F172A", loc="left", pad=8)
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, p: _short_num(v)))
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    return _finish(fig)


def bar_chart(labels, values, title: str, y_label: str = "Count", colors_list=None,
              width=6.0, height=3.4):
    """Simple vertical bar chart — matches the "Customer Satisfaction" /
    target-distribution style chart in academic EDA reports."""
    fig, ax = plt.subplots(figsize=(width, height))
    x = np.arange(len(labels))
    colors_list = colors_list or _pal()[: len(labels)]
    ax.bar(x, values, color=colors_list, width=0.55)
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=15, ha="right" if len(str(labels[0])) > 6 else "center", fontsize=8)
    for i, v in enumerate(values):
        ax.text(i, v, f" {_short_num(v, is_currency=False)}", ha="center", va="bottom", fontsize=8)
    ax.set_title(title, fontsize=10, fontweight="bold", color="#0F172A", loc="left", pad=8)
    ax.set_ylabel(y_label, fontsize=8)
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    return _finish(fig)


def pie_chart(labels, values, title: str, width=5.0, height=3.6):
    """Full pie (not donut) — matches "Customer Type Distribution" style."""
    fig, ax = plt.subplots(figsize=(width, height))
    colors_list = _pal()[: len(labels)]
    ax.pie(values, labels=labels, autopct="%1.1f%%", colors=colors_list,
           startangle=90, textprops=dict(fontsize=8))
    ax.set_title(title, fontsize=10, fontweight="bold", color="#0F172A", loc="left", pad=8)
    ax.axis("equal")
    ax.grid(False)
    return _finish(fig, tight=False)


def grouped_bar_chart(categories, series: dict, title: str, x_label: str = "",
                        y_label: str = "Count", width=6.4, height=3.2):
    """Grouped bars — e.g. Satisfaction split by Class. `series` is
    {series_name: [values aligned to categories]}."""
    fig, ax = plt.subplots(figsize=(width, height))
    n_groups = len(series)
    x = np.arange(len(categories))
    bar_w = 0.8 / max(1, n_groups)
    for i, (name, values) in enumerate(series.items()):
        ax.bar(x + i * bar_w, values, width=bar_w, label=str(name),
               color=_pal()[i % len(_pal())])
    ax.set_xticks(x + bar_w * (n_groups - 1) / 2)
    ax.set_xticklabels(categories, rotation=15, ha="right", fontsize=8)
    ax.set_title(title, fontsize=10, fontweight="bold", color="#0F172A", loc="left", pad=8)
    ax.set_xlabel(x_label, fontsize=8)
    ax.set_ylabel(y_label, fontsize=8)
    ax.legend(frameon=False, fontsize=7.5)
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    return _finish(fig)


def scatter_chart(x_vals, y_vals, title: str, x_label: str, y_label: str,
                    width=6.0, height=3.4):
    fig, ax = plt.subplots(figsize=(width, height))
    ax.scatter(x_vals, y_vals, color=_pal()[2], alpha=0.45, s=14, edgecolors="none")
    ax.set_title(title, fontsize=10, fontweight="bold", color="#0F172A", loc="left", pad=8)
    ax.set_xlabel(x_label, fontsize=8)
    ax.set_ylabel(y_label, fontsize=8)
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    return _finish(fig)


def box_chart(values, title: str, y_label: str = "Value", width=4.6, height=3.4):
    fig, ax = plt.subplots(figsize=(width, height))
    bp = ax.boxplot(values, patch_artist=True, widths=0.4)
    for box in bp["boxes"]:
        box.set(facecolor=_pal()[2], alpha=0.6)
    ax.set_title(title, fontsize=10, fontweight="bold", color="#0F172A", loc="left", pad=8)
    ax.set_ylabel(y_label, fontsize=8)
    ax.set_xticks([])
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    return _finish(fig)


def correlation_heatmap_chart(corr_df, title: str, width=6.6, height=6.0):
    fig, ax = plt.subplots(figsize=(width, height))
    im = ax.imshow(corr_df.values, cmap="coolwarm", vmin=-1, vmax=1)
    ax.set_xticks(range(len(corr_df.columns)))
    ax.set_xticklabels(corr_df.columns, rotation=75, ha="right", fontsize=6.5)
    ax.set_yticks(range(len(corr_df.index)))
    ax.set_yticklabels(corr_df.index, fontsize=6.5)
    fig.colorbar(im, ax=ax, fraction=0.046, pad=0.03)
    ax.set_title(title, fontsize=10, fontweight="bold", color="#0F172A", loc="left", pad=10)
    ax.grid(False)
    return _finish(fig)


def histogram_chart(values, title: str, x_label: str = "Value", width=6.4, height=2.6, bins=14):
    """Distribution -> histogram, per spec."""
    fig, ax = plt.subplots(figsize=(width, height))
    ax.hist(values, bins=bins, color=_pal()[0], alpha=0.85, edgecolor="white")
    ax.set_title(title, fontsize=10, fontweight="bold", color="#0F172A", loc="left", pad=8)
    ax.set_xlabel(x_label, fontsize=8)
    ax.set_ylabel("Frequency", fontsize=8)
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    return _finish(fig)
