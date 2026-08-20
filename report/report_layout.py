"""
report_layout.py — Visual System for the PDF
===============================================
Centralizes color, typography, spacing, and the header/footer chrome so
every page template looks like it came from the same design system —
restrained, corporate, no gradients, no emoji, no decorative noise.
"""

from __future__ import annotations
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.platypus import BaseDocTemplate, PageTemplate, Frame

# ── Brand palette (matches NovaMS's --nova-* CSS variables) ────────────────
NAVY       = colors.HexColor("#0F172A")
INK        = colors.HexColor("#0F172A")
INK_SOFT   = colors.HexColor("#475569")
MUTED      = colors.HexColor("#94A3B8")
BORDER     = colors.HexColor("#E2E8F0")
CARD_BG    = colors.HexColor("#F8FAFC")
GREEN      = colors.HexColor("#16A34A")
GREEN_TINT = colors.HexColor("#F0FDF4")
RED        = colors.HexColor("#DC2626")
RED_TINT   = colors.HexColor("#FEF2F2")
AMBER      = colors.HexColor("#D97706")
AMBER_TINT = colors.HexColor("#FFFBEB")
WHITE      = colors.white

# ── Theme-able accent + chart colors ────────────────────────────────────────
# PRIMARY / PRIMARY_TINT / CHART_PALETTE are the only colors that change with
# the active NovaMS dashboard theme (report_engine.py calls set_theme() once
# per generate() call, passing through whichever theme the person has
# selected in the sidebar's "Customize Dashboard" panel). Everything else
# (ink, borders, card backgrounds, success/warning/danger) stays fixed so the
# PDF always stays print-safe and legible regardless of how dark or unusual
# the dashboard's own theme is — only the accent/brand color and the chart
# palette follow the dashboard, the same way NovaMS's own charts do.
_DEFAULT_PRIMARY_HEX = "#1D4DFF"
_DEFAULT_CHART_PALETTE = ["#1D4DFF", "#0EA5E9", "#16A34A", "#D97706", "#DC2626",
                           "#7C3AED", "#0F172A", "#64748B"]


def _hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    hex_color = hex_color.lstrip("#")
    if len(hex_color) != 6:
        return (29, 77, 255)  # fallback to default primary if malformed
    return tuple(int(hex_color[i:i + 2], 16) for i in (0, 2, 4))


def _tint_toward_white(hex_color: str, white_ratio: float = 0.88) -> str:
    """Blends `hex_color` toward white for a light card-background tint —
    same idea as NovaMS's own `_hex_to_rgba(color, .14)` used against a dark
    background, just recomputed for a light/print PDF background instead."""
    r, g, b = _hex_to_rgb(hex_color)
    r2 = round(r * (1 - white_ratio) + 255 * white_ratio)
    g2 = round(g * (1 - white_ratio) + 255 * white_ratio)
    b2 = round(b * (1 - white_ratio) + 255 * white_ratio)
    return f"#{r2:02X}{g2:02X}{b2:02X}"


def _is_valid_hex(hex_color) -> bool:
    if not isinstance(hex_color, str) or not hex_color.startswith("#") or len(hex_color) != 7:
        return False
    try:
        int(hex_color[1:], 16)
        return True
    except ValueError:
        return False


PRIMARY = colors.HexColor(_DEFAULT_PRIMARY_HEX)
PRIMARY_TINT = colors.HexColor(_tint_toward_white(_DEFAULT_PRIMARY_HEX))
CHART_PALETTE = list(_DEFAULT_CHART_PALETTE)


def set_theme(primary_hex: str | None = None, chart_palette: list | None = None):
    """Updates the report's accent color and chart palette to match the
    currently active NovaMS dashboard theme. Called once per
    `ReportEngine.generate()` call — pass nothing (or invalid values) to
    reset to NovaMS's default Nova Blue look, so one report's theme never
    silently leaks into the next report generated in the same session.

    Only the accent color and chart palette are themed (see note above) —
    the PDF's background, text, and border colors stay fixed for print
    legibility even when the dashboard itself uses a dark or unusual theme.
    """
    global PRIMARY, PRIMARY_TINT, CHART_PALETTE
    hex_val = primary_hex if _is_valid_hex(primary_hex) else _DEFAULT_PRIMARY_HEX
    PRIMARY = colors.HexColor(hex_val)
    PRIMARY_TINT = colors.HexColor(_tint_toward_white(hex_val))
    valid_palette = [c for c in (chart_palette or []) if _is_valid_hex(c)]
    CHART_PALETTE = valid_palette if valid_palette else list(_DEFAULT_CHART_PALETTE)


class _LazyStyles:
    """Dict-like proxy that rebuilds the stylesheet on every lookup, so
    style colors (e.g. the Cover page's kicker text, which uses PRIMARY)
    always reflect the theme active at report-generation time — rather than
    whatever theme happened to be active the first time this module was
    imported, which would otherwise freeze forever (Python only runs a
    module's top-level code once per process, and Streamlit keeps the same
    process alive across reruns)."""

    def __getitem__(self, key):
        return get_styles()[key]


LAZY_STYLES = _LazyStyles()

PAGE_SIZE = A4
MARGIN = 18 * mm

# ── Font registration ───────────────────────────────────────────────────────
# The built-in Helvetica/Courier base-14 fonts have NO glyph for the Rupee
# sign (U+20B9) or other non-Latin-1 characters — they render as a black box
# ("tofu"). DejaVu Sans (bundled with matplotlib, so always present in this
# environment) does support it, so we register it and use it everywhere
# instead of Helvetica. Falls back to Helvetica/Courier if registration
# fails for any reason (e.g. font files unavailable in a different
# deployment), so the report still generates either way.
FONT_REGULAR = "Helvetica"
FONT_BOLD    = "Helvetica-Bold"
FONT_MONO    = "Courier"

try:
    import os
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    import matplotlib as _mpl

    _dejavu_dir = os.path.join(_mpl.get_data_path(), "fonts", "ttf")
    _regular_path = os.path.join(_dejavu_dir, "DejaVuSans.ttf")
    _bold_path = os.path.join(_dejavu_dir, "DejaVuSans-Bold.ttf")
    if os.path.exists(_regular_path) and os.path.exists(_bold_path):
        pdfmetrics.registerFont(TTFont("NovaSans", _regular_path))
        pdfmetrics.registerFont(TTFont("NovaSans-Bold", _bold_path))
        FONT_REGULAR = "NovaSans"
        FONT_BOLD = "NovaSans-Bold"
except Exception:
    pass  # keep the Helvetica fallback — currency will show as "Rs" via fmt_currency's ASCII-safe path


def get_styles() -> dict:
    base = getSampleStyleSheet()
    styles = {}
    styles["CoverTitle"] = ParagraphStyle(
        "CoverTitle", parent=base["Title"], fontName=FONT_BOLD, fontSize=28,
        leading=34, textColor=INK, alignment=TA_LEFT, spaceAfter=6,
    )
    styles["CoverSub"] = ParagraphStyle(
        "CoverSub", parent=base["Normal"], fontName=FONT_REGULAR, fontSize=12,
        leading=16, textColor=INK_SOFT, alignment=TA_LEFT,
    )
    styles["CoverKicker"] = ParagraphStyle(
        "CoverKicker", parent=base["Normal"], fontName=FONT_BOLD, fontSize=9,
        leading=11, textColor=PRIMARY, alignment=TA_LEFT, spaceAfter=10,
    )
    styles["SectionHeading"] = ParagraphStyle(
        "SectionHeading", parent=base["Heading1"], fontName=FONT_BOLD, fontSize=14,
        leading=18, textColor=INK, spaceBefore=4, spaceAfter=8,
        borderColor=PRIMARY, borderWidth=0,
    )
    styles["SubHeading"] = ParagraphStyle(
        "SubHeading", parent=base["Heading2"], fontName=FONT_BOLD, fontSize=11,
        leading=14, textColor=INK, spaceBefore=10, spaceAfter=6,
    )
    styles["Body"] = ParagraphStyle(
        "Body", parent=base["Normal"], fontName=FONT_REGULAR, fontSize=9.5,
        leading=14, textColor=INK_SOFT,
    )
    styles["BodyBold"] = ParagraphStyle(
        "BodyBold", parent=base["Normal"], fontName=FONT_BOLD, fontSize=9.5,
        leading=14, textColor=INK,
    )
    styles["Caption"] = ParagraphStyle(
        "Caption", parent=base["Normal"], fontName=FONT_REGULAR, fontSize=8,
        leading=11, textColor=MUTED,
    )
    styles["KPILabel"] = ParagraphStyle(
        "KPILabel", parent=base["Normal"], fontName=FONT_BOLD, fontSize=7.5,
        leading=9, textColor=MUTED, alignment=TA_LEFT,
    )
    styles["KPIValue"] = ParagraphStyle(
        "KPIValue", parent=base["Normal"], fontName=FONT_BOLD, fontSize=13,
        leading=15, textColor=INK, alignment=TA_LEFT,
    )
    styles["KPIDelta"] = ParagraphStyle(
        "KPIDelta", parent=base["Normal"], fontName=FONT_BOLD, fontSize=8,
        leading=10, alignment=TA_LEFT,
    )
    styles["Bullet"] = ParagraphStyle(
        "Bullet", parent=base["Normal"], fontName=FONT_REGULAR, fontSize=9.5,
        leading=15, textColor=INK_SOFT, leftIndent=10, bulletIndent=0,
    )
    styles["TableHeader"] = ParagraphStyle(
        "TableHeader", parent=base["Normal"], fontName=FONT_BOLD, fontSize=8,
        leading=10, textColor=WHITE,
    )
    styles["TableCell"] = ParagraphStyle(
        "TableCell", parent=base["Normal"], fontName=FONT_REGULAR, fontSize=8.5,
        leading=11, textColor=INK,
    )
    styles["ConclusionBig"] = ParagraphStyle(
        "ConclusionBig", parent=base["Normal"], fontName=FONT_BOLD, fontSize=13,
        leading=18, textColor=INK,
    )
    return styles


def fmt_currency(v: float, symbol: str = "\u20b9") -> str:
    try:
        v = float(v)
    except Exception:
        return "N/A"
    if v != v or v in (float("inf"), float("-inf")):
        return "N/A"
    sign = "-" if v < 0 else ""
    v = abs(v)
    if v >= 1e7:
        return f"{sign}{symbol}{v/1e7:.2f}Cr"
    if v >= 1e5:
        return f"{sign}{symbol}{v/1e5:.2f}L"
    if v >= 1e3:
        return f"{sign}{symbol}{v/1e3:.1f}K"
    return f"{sign}{symbol}{v:,.0f}"


def fmt_number(v: float) -> str:
    try:
        v = float(v)
    except Exception:
        return "N/A"
    if v != v or v in (float("inf"), float("-inf")):
        return "N/A"
    if abs(v) >= 1e7:
        return f"{v/1e7:.2f}Cr"
    if abs(v) >= 1e5:
        return f"{v/1e5:.2f}L"
    if abs(v) >= 1e3:
        return f"{v/1e3:.1f}K"
    return f"{v:,.0f}"


def fmt_pct(v: float, signed: bool = False) -> str:
    try:
        v = float(v)
    except Exception:
        return "N/A"
    if v != v or v in (float("inf"), float("-inf")):
        return "N/A"
    sign = "+" if (signed and v >= 0) else ""
    return f"{sign}{v:.1f}%"


class _HeaderFooterDocTemplate(BaseDocTemplate):
    """DocTemplate that draws a consistent header/footer + page numbers on
    every page, and tracks section numbers via a simple counter the
    templates increment through `doc.section_no`."""

    def __init__(self, filename, report_title: str, dataset_name: str, **kw):
        super().__init__(filename, pagesize=PAGE_SIZE,
                          leftMargin=MARGIN, rightMargin=MARGIN,
                          topMargin=MARGIN + 4 * mm, bottomMargin=MARGIN, **kw)
        self.report_title = report_title
        self.dataset_name = dataset_name
        self.section_no = 0
        frame = Frame(self.leftMargin, self.bottomMargin, self.width, self.height, id="main")
        template = PageTemplate(id="main", frames=[frame], onPage=self._draw_chrome)
        self.addPageTemplates([template])

    def _draw_chrome(self, canvas, doc):
        canvas.saveState()
        # Header
        canvas.setFont(FONT_BOLD, 8)
        canvas.setFillColor(PRIMARY)
        canvas.drawString(MARGIN, PAGE_SIZE[1] - MARGIN + 6, "NOVAMS")
        canvas.setFont(FONT_REGULAR, 8)
        canvas.setFillColor(MUTED)
        header_right = _fit_text(canvas, doc.report_title, FONT_REGULAR, 8, max_width=380)
        canvas.drawRightString(PAGE_SIZE[0] - MARGIN, PAGE_SIZE[1] - MARGIN + 6, header_right)
        canvas.setStrokeColor(BORDER)
        canvas.setLineWidth(0.6)
        canvas.line(MARGIN, PAGE_SIZE[1] - MARGIN + 2, PAGE_SIZE[0] - MARGIN, PAGE_SIZE[1] - MARGIN + 2)
        # Footer
        canvas.setFont(FONT_REGULAR, 7.5)
        canvas.setFillColor(MUTED)
        footer_left = _fit_text(canvas, f"NovaMS \u00b7 {doc.dataset_name}", FONT_REGULAR, 7.5, max_width=130)
        canvas.drawString(MARGIN, MARGIN - 10, footer_left)
        canvas.drawCentredString(PAGE_SIZE[0] / 2, MARGIN - 10, "Business Intelligence \u00b7 Data Analytics \u00b7 AI-Assisted Insights")
        canvas.drawRightString(PAGE_SIZE[0] - MARGIN, MARGIN - 10, f"Page {doc.page}")
        canvas.restoreState()


def make_document(filepath: str, report_title: str, dataset_name: str) -> _HeaderFooterDocTemplate:
    return _HeaderFooterDocTemplate(filepath, report_title, dataset_name)


def _fit_text(canvas, text: str, font_name: str, font_size: float, max_width: float) -> str:
    """Truncates `text` with a trailing ellipsis so it fits within
    `max_width` points at the given font — used to keep footer/header text
    from ever overlapping neighboring elements, regardless of how long a
    dataset name is."""
    if canvas.stringWidth(text, font_name, font_size) <= max_width:
        return text
    ellipsis = "\u2026"
    lo, hi = 0, len(text)
    while lo < hi:
        mid = (lo + hi + 1) // 2
        candidate = text[:mid].rstrip() + ellipsis
        if canvas.stringWidth(candidate, font_name, font_size) <= max_width:
            lo = mid
        else:
            hi = mid - 1
    return text[:lo].rstrip() + ellipsis if lo > 0 else ellipsis
