from __future__ import annotations

import html
import io
import re
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Iterable

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import FuncFormatter
from PIL import Image, ImageDraw, ImageFont
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import Image as RLImage, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

st.set_page_config(
    page_title="IQC Quality Dashboard",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ============================================================
# THEME
# ============================================================
NAVY = "#073B7A"
NAVY_DARK = "#031D46"
NAVY_MID = "#0A56B5"
BLUE = "#176FDB"
GREEN = "#45A52C"
RED = "#E6332A"
ORANGE = "#F5A000"
PURPLE = "#7B2CBF"
CYAN = "#19A6BE"
TEXT = "#0A2147"
MUTED = "#425466"
GRID = "#E3E9F1"
BG = "#F2F5FA"
BORDER = "#C8D3E1"

st.markdown(
    f"""
<style>
/* ---------- Page ---------- */
html, body, [class*="css"] {{font-family: Arial, Helvetica, sans-serif;}}
.stApp {{background:{BG};}}
.block-container {{max-width: 1720px; padding: 0.45rem 1.05rem 1.25rem;}}
header[data-testid="stHeader"] {{height:0; background:transparent;}}
#MainMenu, footer, div[data-testid="stToolbar"] {{visibility:hidden;}}
[data-testid="stDecoration"] {{display:none;}}

/* ---------- Top navigation ---------- */
.st-key-topbar {{
    background:linear-gradient(105deg,{NAVY_DARK} 0%,{NAVY} 63%,#082E6A 100%);
    border-radius:12px;
    padding:12px 18px 16px;
    min-height:88px;
    overflow:visible;
    box-shadow:0 5px 16px rgba(4,30,72,.22);
    margin-bottom:8px;
}}
.st-key-topbar div[data-testid="stHorizontalBlock"] {{align-items:flex-start; gap:.65rem;}}
.dash-title {{color:white; font-weight:900; font-size:clamp(28px,2.6vw,42px); line-height:1.08; letter-spacing:.2px; white-space:nowrap;}}
.dash-title-icon {{display:inline-flex;width:56px;height:56px;border-radius:50%;align-items:center;justify-content:center;background:white;color:{NAVY};font-size:30px;margin-right:12px;vertical-align:middle;}}
.dash-subtitle {{font-size:12px;color:#D7E5FB;margin:5px 0 0 70px;letter-spacing:.2px;line-height:1.35;min-height:18px;display:block;}}
.st-key-topbar label {{color:white!important;font-weight:800!important;font-size:12px!important;margin-bottom:0!important;}}
.st-key-topbar div[data-baseweb="select"] > div {{
    min-height:38px!important;height:38px!important;border:0!important;border-radius:6px!important;background:white!important;
    font-size:13px!important;box-shadow:none!important;
}}
.st-key-topbar div[data-testid="stSelectbox"] {{margin-top:1px;}}

/* ---------- Uploader ---------- */
.st-key-upload_panel {{margin:0 0 4px;}}
.st-key-upload_panel details {{background:#fff;border:1px solid {BORDER};border-radius:8px;}}
.st-key-upload_panel summary {{font-size:11px;font-weight:800;color:{NAVY};}}
div[data-testid="stFileUploader"] section {{border:1px dashed #9AAAC0;border-radius:8px;background:#FAFCFF;min-height:70px;padding:8px;}}

/* ---------- KPI cards ---------- */
.kpi-row {{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:0;background:white;border:1px solid {BORDER};border-radius:12px;padding:10px 6px;box-shadow:0 2px 8px rgba(15,40,80,.06);margin-bottom:5px;}}
.kpi {{display:flex;align-items:center;min-height:112px;padding:10px 18px;border-right:1px solid #D7DEE8;}}
.kpi:last-child {{border-right:0;}}
.kpi-icon {{width:64px;height:64px;min-width:64px;border-radius:50%;display:flex;align-items:center;justify-content:center;background:{NAVY};color:white;font-size:30px;margin-right:16px;box-shadow:inset 0 0 0 2px rgba(255,255,255,.13);}}
.kpi-label {{font-size:13px;font-weight:900;color:#101828;letter-spacing:.2px;white-space:nowrap;}}
.kpi-value {{font-size:clamp(26px,2.3vw,38px);font-weight:900;line-height:1.08;margin-top:5px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:190px;}}
.kpi.top-vendor .kpi-value, .kpi.top-item .kpi-value {{font-size:clamp(18px,1.55vw,25px);line-height:1.12;white-space:normal;overflow:visible;text-overflow:clip;max-width:220px;overflow-wrap:anywhere;word-break:normal;}}
.kpi.top-vendor {{padding-left:14px;padding-right:14px;}}
.kpi-unit {{font-size:12px;color:#17243A;font-weight:700;margin-top:3px;}}

/* ---------- Chart cards ---------- */
.chart-card {{background:white;border:1.2px solid {BORDER};border-radius:12px;padding:10px 12px 7px;box-shadow:0 4px 14px rgba(15,40,80,.09);}}
.chart-title {{display:inline-block;background:linear-gradient(90deg,{NAVY_DARK},{NAVY_MID});color:white;padding:7px 20px;border-radius:7px;font-size:16px;font-weight:900;letter-spacing:.25px;margin:0 0 5px 10px;min-width:220px;text-align:center;}}
div[data-testid="stPlotlyChart"] {{margin-top:-3px;margin-bottom:-3px;background:#FFFFFF;border-radius:0 0 10px 10px;padding:0 4px 2px;}}


/* ---------- Plotly chart typography ---------- */
div[data-testid="stPlotlyChart"] .main-svg text {{
    font-family: Arial Black, Arial, Helvetica, sans-serif !important;
    font-weight: 800 !important;
    fill: #0A2147 !important;
}}

/* ---------- Insight strip ---------- */
.insights {{display:grid;grid-template-columns:1.05fr repeat(4,1fr);background:linear-gradient(90deg,#FFF8D9,#FFF0B5);border:1.5px solid #E9B92E;border-radius:12px;margin:10px 0;padding:14px 16px;box-shadow:0 3px 10px rgba(120,90,0,.10);min-height:122px;align-items:stretch;}}
.insight-head {{display:flex;align-items:center;font-size:20px;font-weight:900;color:#102A56;padding-right:14px;line-height:1.2;}}
.insight-bulb {{width:54px;height:54px;min-width:54px;border-radius:50%;display:flex;align-items:center;justify-content:center;background:{ORANGE};color:white;font-size:28px;margin-right:12px;box-shadow:0 2px 6px rgba(120,80,0,.18);}}
.insight-item {{border-left:1px dashed #9A8B5F;padding:10px 16px;color:#17233D;display:flex;align-items:center;justify-content:center;min-width:0;}}
.insight-copy {{width:100%;display:flex;flex-direction:column;justify-content:center;align-items:flex-start;gap:5px;font-size:15px;font-weight:700;line-height:1.28;overflow-wrap:anywhere;}}
.insight-copy .insight-label {{font-size:13px;font-weight:900;color:#102A56;text-transform:uppercase;letter-spacing:.15px;}}
.insight-copy b {{color:{RED};font-size:16px;font-weight:900;line-height:1.2;}}
.insight-copy .insight-note {{font-size:14px;font-weight:700;color:#27364F;}}

/* ---------- Bottom summary ---------- */
.summary-strip {{display:grid;grid-template-columns:repeat(6,1fr);background:linear-gradient(100deg,{NAVY_DARK},{NAVY});color:white;border-radius:12px;padding:10px 6px;margin-top:5px;box-shadow:0 5px 14px rgba(4,30,72,.18);}}
.summary-item {{display:flex;align-items:center;justify-content:center;border-right:1px solid rgba(255,255,255,.35);min-height:82px;padding:5px 10px;}}
.summary-item:last-child {{border-right:0;}}
.summary-icon {{width:50px;height:50px;min-width:50px;border-radius:50%;display:flex;align-items:center;justify-content:center;background:white;color:{NAVY};font-size:24px;margin-right:11px;}}
.summary-label {{font-size:12px;font-weight:850;color:#E5EEFC;white-space:nowrap;}}
.summary-value {{font-size:27px;font-weight:900;line-height:1.05;margin-top:3px;white-space:nowrap;}}
.summary-value.accepted {{color:#63D65E;}}
.summary-value.rejected {{color:#FF4B3E;}}
.summary-value.rate {{color:#FFD21F;}}
.summary-unit {{font-size:11.5px;color:#D8E5F8;margin-top:2px;}}
.source-note {{text-align:center;font-size:10px;color:#667085;margin-top:4px;}}

/* ---------- Data table ---------- */
div[data-testid="stExpander"] details {{background:white;border:1px solid {BORDER};border-radius:8px;}}

@media (max-width:1150px) {{
  .kpi-row {{grid-template-columns:repeat(2,1fr);}}
  .kpi {{border-bottom:1px solid #E0E5EC;}}
  .insights {{grid-template-columns:1fr 1fr;}}
  .insight-item {{border-top:1px dashed #8D98A7;}}
  .summary-strip {{grid-template-columns:repeat(2,1fr);}}
}}
</style>
""",
    unsafe_allow_html=True,
)

# ============================================================
# DATA LOADING
# ============================================================
ALIASES = {
    "date": ["Item Receipt Date", "Receipt Date", "Date", "Inspection Date"],
    "received": ["Quantity Received", "Received Qty", "Total Received", "Received", "Output"],
    "approved": ["Quantity Approved (Actual)", "Quantity Approved", "Approved Qty", "Accepted Qty", "Approved", "Accepted"],
    "rejected": ["Quantity Rejected", "Rejected Qty", "Reject Qty", "Rejected", "Defect Qty", "Total Defect"],
    "reworked": ["Quantity Reworked", "Reworked Qty", "Rework Qty", "Reworked"],
    "special": ["Quantity Special Released", "Special Released Qty", "Special Released"],
    "quarantine": ["Quantity In Quarantine", "Quarantine Qty", "Quarantine"],
    "to_inspect": ["Quantity To Inspect", "Inspection Qty", "Qty To Inspect", "Total Inspection"],
    "item": ["Item", "Part Number", "Part No", "Item Code"],
    "vendor": ["Vendor", "Supplier", "Vendor Name", "Supplier Name"],
    "defect": ["Defect", "Defect Type", "Defect Description"],
    "location": ["Location", "Production Line", "Line"],
    "receipt": ["Item Receipt", "Document Number", "Receipt Number"],
    "counter": ["Counter", "Inspector", "Created By", "Employee"],
    "inspection_time": ["Inspection Time", "Duration", "Total Inspection Time"],
}


def norm(value: object) -> str:
    return re.sub(r"[^a-z0-9]+", "", str(value).strip().lower())


def find_col(df: pd.DataFrame, names: Iterable[str]) -> str | None:
    mapping = {norm(c): c for c in df.columns}
    for name in names:
        if norm(name) in mapping:
            return mapping[norm(name)]
    return None


def parse_excel_xml(raw: bytes) -> pd.DataFrame:
    root = ET.fromstring(raw.decode("utf-8", errors="ignore"))
    ns = {"ss": "urn:schemas-microsoft-com:office:spreadsheet"}
    worksheet = root.find("ss:Worksheet", ns)
    if worksheet is None:
        raise ValueError("Không tìm thấy worksheet trong file Excel XML.")
    table = worksheet.find("ss:Table", ns)
    if table is None:
        raise ValueError("Không tìm thấy bảng dữ liệu trong file Excel XML.")

    rows: list[dict[int, str | None]] = []
    for row in table.findall("ss:Row", ns):
        values: dict[int, str | None] = {}
        col_index = 1
        for cell in row.findall("ss:Cell", ns):
            explicit_index = cell.attrib.get("{urn:schemas-microsoft-com:office:spreadsheet}Index")
            if explicit_index:
                col_index = int(explicit_index)
            data = cell.find("ss:Data", ns)
            values[col_index] = data.text if data is not None else None
            col_index += 1
        rows.append(values)

    if not rows:
        return pd.DataFrame()
    max_col = max(max(row.keys(), default=0) for row in rows)
    headers = [rows[0].get(i) or f"Column_{i}" for i in range(1, max_col + 1)]
    return pd.DataFrame(
        [{headers[i - 1]: row.get(i) for i in range(1, max_col + 1)} for row in rows[1:]]
    )


@st.cache_data(show_spinner=False)
def read_file(raw: bytes, filename: str) -> pd.DataFrame:
    suffix = Path(filename).suffix.lower()
    if suffix == ".csv":
        for encoding in ("utf-8-sig", "utf-8", "latin-1"):
            try:
                return pd.read_csv(io.BytesIO(raw), encoding=encoding)
            except UnicodeDecodeError:
                continue
        raise ValueError("Không đọc được file CSV.")

    if raw.lstrip().startswith(b"<?xml"):
        return parse_excel_xml(raw)

    excel = pd.ExcelFile(io.BytesIO(raw))
    preferred = ["DuLieuGoc", "Data_Input", "Input Data", "Data"]
    sheet = next((name for name in preferred if name in excel.sheet_names), excel.sheet_names[0])
    return pd.read_excel(io.BytesIO(raw), sheet_name=sheet)


def default_data() -> tuple[pd.DataFrame | None, str | None]:
    for name in ("IQC_Data.xlsx", "IQC_Data.xlsm", "IQC_Data.xls", "IQC_Data.csv"):
        path = Path("data") / name
        if path.exists():
            return read_file(path.read_bytes(), path.name), path.name
    return None, None


def prepare(source: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, str]]:
    cols = {key: find_col(source, aliases) for key, aliases in ALIASES.items()}
    missing = [key for key in ("date", "received", "rejected", "item") if not cols[key]]
    if missing:
        raise ValueError("Thiếu cột bắt buộc: " + ", ".join(missing))

    df = source.copy()
    date_col = cols["date"]
    assert date_col is not None
    # IQC exports commonly use Vietnamese day/month/year dates.
    # dayfirst=True prevents 05/06/2026 from being misread as May 6.
    df[date_col] = pd.to_datetime(df[date_col], errors="coerce", dayfirst=True)
    df = df[df[date_col].notna()].copy()
    df["Year-Month"] = df[date_col].dt.strftime("%Y-%m")

    numeric_keys = ["received", "approved", "rejected", "reworked", "special", "quarantine", "to_inspect"]
    for key in numeric_keys:
        col = cols[key]
        if col:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
        else:
            col = f"__{key}"
            df[col] = 0.0
            cols[key] = col

    text_keys = ["item", "vendor", "defect", "location", "receipt", "counter"]
    for key in text_keys:
        col = cols[key]
        if col:
            df[col] = df[col].fillna("(Blank)").astype(str).str.strip().replace("", "(Blank)")
        else:
            col = f"__{key}"
            df[col] = "(Blank)"
            cols[key] = col

    # Optional inspection time as timedelta.
    time_col = cols.get("inspection_time")
    if time_col:
        df[time_col] = pd.to_timedelta(df[time_col], errors="coerce")

    return df, {key: str(value) for key, value in cols.items()}


# ============================================================
# HELPERS
# ============================================================
def safe(value: object) -> str:
    return html.escape(str(value))


def number(value: float) -> str:
    return f"{value:,.0f}"


def pct(value: float) -> str:
    return f"{value:.2%}"


def layout(fig: go.Figure, height: int, margins: dict | None = None) -> go.Figure:
    fig.update_layout(
        height=height,
        margin=margins or dict(l=32, r=18, t=22, b=30),
        paper_bgcolor="white",
        plot_bgcolor="white",
        font=dict(family="Arial Black", color=TEXT, size=16),
        hoverlabel=dict(bgcolor="white", font_size=16, font_family="Arial Black"),
        legend=dict(orientation="h", yanchor="bottom", y=1.04, xanchor="left", x=0, font=dict(size=15, color=TEXT, family="Arial Black")),
        bargap=0.32,
    )
    fig.update_xaxes(showgrid=False, zeroline=False, linecolor="#AEBBCD", linewidth=1.2, tickfont=dict(size=15, color=TEXT, family="Arial Black"), title_font=dict(size=16, color=TEXT, family="Arial Black"))
    fig.update_yaxes(gridcolor=GRID, gridwidth=1, zeroline=False, tickfont=dict(size=15, color=TEXT, family="Arial Black"), title_font=dict(size=16, color=TEXT, family="Arial Black"))
    return fig


def empty_chart(text: str, height: int = 220) -> go.Figure:
    fig = go.Figure()
    fig.add_annotation(text=text, x=.5, y=.5, showarrow=False, font=dict(size=14, color=MUTED, family="Arial"))
    fig.update_xaxes(visible=False)
    fig.update_yaxes(visible=False)
    return layout(fig, height, dict(l=5, r=5, t=5, b=5))


def bar_chart(series: pd.Series, color: str, total: float) -> go.Figure:
    s = series.head(5).sort_values(ascending=True)
    if s.empty:
        return empty_chart("No rejected quantity", 430)
    labels = [f"{value:,.0f} ({value / total:.2%})" if total else f"{value:,.0f}" for value in s.values]
    fig = go.Figure(
        go.Bar(
            x=s.values,
            y=s.index,
            orientation="h",
            marker=dict(color=color, line=dict(color="rgba(0,0,0,0.12)", width=1.0)),
            text=labels,
            textposition="outside",
            cliponaxis=False,
            textfont=dict(size=16, color=TEXT, family="Arial Black"),
            hovertemplate="%{y}<br>%{x:,.0f} pcs<extra></extra>",
        )
    )
    max_label = max((len(str(x)) for x in s.index), default=10)
    left_margin = min(300, max(145, max_label * 8 + 28))
    layout(fig, 470, dict(l=left_margin, r=125, t=20, b=64))
    fig.update_layout(showlegend=False, paper_bgcolor="white", plot_bgcolor="white")
    fig.update_xaxes(title=dict(text="PCS", font=dict(size=17, color=TEXT, family="Arial Black")), rangemode="tozero", tickfont=dict(size=14, color=TEXT, family="Arial Black"))
    fig.update_yaxes(automargin=True, tickfont=dict(size=16, color=TEXT, family="Arial Black"), showgrid=False)
    return fig


def _strip_html(text: str) -> str:
    return re.sub(r"<[^>]+>", " ", str(text)).replace("  ", " ").strip()


def figure_png(fig: go.Figure, width: int = 1500, height: int = 850) -> bytes:
    """Render the dashboard charts without Kaleido/Chrome.

    This Matplotlib renderer supports the chart types used in this app:
    grouped bar + rate line, horizontal ranking bars, and doughnut charts.
    """
    dpi = 180
    # Scale export typography with the requested image size so full-dashboard
    # PNG/PDF remains readable when rendered at high resolution.
    scale = max(1.0, min(2.2, width / 1200.0))
    mpl_fig, ax = plt.subplots(figsize=(width / dpi, height / dpi), dpi=dpi)
    mpl_fig.patch.set_facecolor("white")
    ax.set_facecolor("white")
    traces = list(fig.data)

    pie = next((t for t in traces if getattr(t, "type", "") == "pie"), None)
    horizontal = next((t for t in traces if getattr(t, "type", "") == "bar" and getattr(t, "orientation", None) == "h"), None)

    if pie is not None:
        labels = [] if pie.labels is None else list(pie.labels)
        values = np.asarray([] if pie.values is None else list(pie.values), dtype=float)
        pie_colors = getattr(getattr(pie, "marker", None), "colors", None)
        colors_list = [GREEN, RED, ORANGE, PURPLE, BLUE] if pie_colors is None else list(pie_colors)
        wedges, _ = ax.pie(
            values,
            startangle=90,
            counterclock=False,
            colors=colors_list[:len(values)],
            wedgeprops=dict(width=0.38, edgecolor="white", linewidth=2),
        )
        total = values.sum()
        for wedge, value in zip(wedges, values):
            share = value / total if total else 0
            if share >= 0.025:
                angle = (wedge.theta1 + wedge.theta2) / 2
                x, y = 0.81 * np.cos(np.deg2rad(angle)), 0.81 * np.sin(np.deg2rad(angle))
                ax.text(x, y, f"{share:.1%}", ha="center", va="center", color="white", fontsize=13 * scale, fontweight="bold")
        center_text = f"{total:,.0f}\nTotal"
        if getattr(fig.layout, "annotations", None):
            center_text = _strip_html(fig.layout.annotations[0].text).replace("Total Defect", "\nTotal Defect")
        ax.text(0, 0, center_text, ha="center", va="center", fontsize=19 * scale, fontweight="bold", color=TEXT)
        ax.legend(wedges, labels, loc="center left", bbox_to_anchor=(1.0, 0.5), frameon=False, fontsize=12 * scale)
        ax.axis("equal")
        ax.axis("off")

    elif horizontal is not None:
        labels = [str(x) for x in horizontal.y]
        values = np.asarray(list(horizontal.x), dtype=float)
        color = getattr(getattr(horizontal, "marker", None), "color", NAVY_MID)
        positions = np.arange(len(labels))
        ax.barh(positions, values, color=color, height=0.62)
        ax.set_yticks(positions)
        ax.set_yticklabels(labels, fontsize=13 * scale, fontweight="bold", color=TEXT)
        ax.tick_params(axis="x", labelsize=12 * scale, colors=TEXT)
        ax.grid(axis="x", color=GRID, linewidth=0.8)
        ax.set_axisbelow(True)
        ax.set_xlabel("PCS", fontsize=13 * scale, fontweight="bold", color=TEXT)
        max_value = float(values.max()) if len(values) else 1.0
        horizontal_text = getattr(horizontal, "text", None)
        text_values = [f"{v:,.0f}" for v in values] if horizontal_text is None else list(horizontal_text)
        for y, value, label_text in zip(positions, values, text_values):
            ax.text(value + max_value * 0.025, y, str(label_text), va="center", ha="left", fontsize=12.5 * scale, fontweight="bold", color=TEXT)
        ax.set_xlim(0, max_value * 1.34 if max_value else 1)
        for spine in ("top", "right", "left"):
            ax.spines[spine].set_visible(False)
        ax.spines["bottom"].set_color("#AEBBCD")

    else:
        bar_traces = [t for t in traces if getattr(t, "type", "") == "bar"]
        line_trace = next((t for t in traces if getattr(t, "type", "") == "scatter"), None)
        categories = [str(x) for x in (bar_traces[0].x if bar_traces else (line_trace.x if line_trace is not None else []))]
        pos = np.arange(len(categories))
        bar_width = 0.34
        for idx, trace in enumerate(bar_traces):
            vals = np.asarray(list(trace.y), dtype=float)
            offset = (idx - (len(bar_traces)-1)/2) * bar_width
            color = getattr(getattr(trace, "marker", None), "color", NAVY)
            bars = ax.bar(pos + offset, vals, width=bar_width, color=color, label=str(trace.name))
            for rect, value in zip(bars, vals):
                ax.text(rect.get_x()+rect.get_width()/2, rect.get_height(), f"{value:,.0f}", ha="center", va="bottom", fontsize=10.5 * scale, fontweight="bold", color=TEXT)
        ax.set_xticks(pos)
        ax.set_xticklabels(categories, fontsize=12 * scale, fontweight="bold", color=TEXT)
        ax.set_ylabel("PCS", fontsize=13 * scale, fontweight="bold", color=TEXT)
        ax.tick_params(axis="y", labelsize=11, colors=TEXT)
        ax.grid(axis="y", color=GRID, linewidth=0.8)
        ax.set_axisbelow(True)
        handles, labels_legend = ax.get_legend_handles_labels()
        if line_trace is not None:
            ax2 = ax.twinx()
            rate = np.asarray(list(line_trace.y), dtype=float)
            line_color = getattr(getattr(line_trace, "line", None), "color", ORANGE)
            ax2.plot(pos, rate, color=line_color, marker="o", linewidth=2.6 * scale, markersize=6.5 * scale, label=str(line_trace.name))
            for x, value in zip(pos, rate):
                ax2.text(x, value, f"{value:.2f}%", ha="center", va="bottom", fontsize=10.5, fontweight="bold", color=RED)
            ax2.set_ylabel("%", fontsize=13 * scale, fontweight="bold", color=TEXT)
            ax2.tick_params(axis="y", labelsize=11, colors=TEXT)
            ax2.yaxis.set_major_formatter(FuncFormatter(lambda x, _: f"{x:.1f}%"))
            h2, l2 = ax2.get_legend_handles_labels()
            handles += h2; labels_legend += l2
        ax.legend(handles, labels_legend, loc="upper left", bbox_to_anchor=(0, 1.12), ncol=3, frameon=False, fontsize=11 * scale)
        for spine in ("top", "right"):
            ax.spines[spine].set_visible(False)

    mpl_fig.tight_layout(pad=1.8)
    buffer = io.BytesIO()
    mpl_fig.savefig(buffer, format="png", dpi=dpi, facecolor="white", bbox_inches="tight")
    plt.close(mpl_fig)
    return buffer.getvalue()


def build_png_zip(figures: list[tuple[str, go.Figure]]) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for filename, fig in figures:
            archive.writestr(filename, figure_png(fig))
    return buffer.getvalue()


def build_pdf_report(
    report_month: str,
    source: str,
    metrics: list[tuple[str, str]],
    insights: list[str],
    figures: list[tuple[str, go.Figure]],
) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        rightMargin=12 * mm,
        leftMargin=12 * mm,
        topMargin=10 * mm,
        bottomMargin=10 * mm,
        title=f"IQC Quality Dashboard {report_month}",
    )
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "DashboardTitle", parent=styles["Title"], fontName="Helvetica-Bold",
        fontSize=22, leading=26, textColor=colors.HexColor(NAVY_DARK), spaceAfter=8
    )
    small = ParagraphStyle(
        "Small", parent=styles["BodyText"], fontName="Helvetica", fontSize=9,
        leading=12, textColor=colors.HexColor(TEXT)
    )
    insight_style = ParagraphStyle(
        "Insight", parent=styles["BodyText"], fontName="Helvetica-Bold", fontSize=10,
        leading=13, textColor=colors.HexColor(TEXT)
    )
    story = [Paragraph("IQC QUALITY DASHBOARD", title_style), Paragraph(f"Month: {report_month} &nbsp;&nbsp; Source: {safe(source)}", small), Spacer(1, 4 * mm)]

    metric_cells = []
    for label, value in metrics:
        metric_cells.append(Paragraph(f"<b>{safe(label)}</b><br/><font size='16'>{safe(value)}</font>", small))
    metric_table = Table([metric_cells], colWidths=[52 * mm] * len(metric_cells))
    metric_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.white),
        ("BOX", (0, 0), (-1, -1), 0.8, colors.HexColor(BORDER)),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor(BORDER)),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.extend([metric_table, Spacer(1, 4 * mm)])

    insight_cells = [Paragraph(f"• {safe(text)}", insight_style) for text in insights]
    insight_table = Table([insight_cells], colWidths=[65 * mm] * len(insight_cells))
    insight_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#FFF4C8")),
        ("BOX", (0, 0), (-1, -1), 0.8, colors.HexColor("#E8C85D")),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E8C85D")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
    ]))
    story.extend([insight_table, Spacer(1, 5 * mm)])

    # Two charts per landscape page.
    chart_cells = []
    for chart_name, fig in figures:
        image_bytes = io.BytesIO(figure_png(fig, 1300, 720))
        chart = RLImage(image_bytes, width=128 * mm, height=70 * mm)
        chart_cells.append([Paragraph(f"<b>{safe(chart_name)}</b>", small), chart])

    for index in range(0, len(chart_cells), 2):
        pair = chart_cells[index:index + 2]
        titles = [cell[0] for cell in pair]
        images = [cell[1] for cell in pair]
        if len(pair) == 1:
            titles.append(Paragraph("", small)); images.append(Spacer(1, 1))
        table = Table([titles, images], colWidths=[135 * mm, 135 * mm])
        table.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor(BORDER)),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor(BORDER)),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ]))
        story.append(table)
        if index + 2 < len(chart_cells):
            story.append(PageBreak())

    doc.build(story)
    return buffer.getvalue()




def _dashboard_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    """Load a reliable font on Streamlit Cloud."""
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
    ]
    for candidate in candidates:
        try:
            return ImageFont.truetype(candidate, size=size)
        except (OSError, IOError):
            continue
    return ImageFont.load_default()


def _rounded_card(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], radius: int = 26,
                  fill: str = "#FFFFFF", outline: str = BORDER, width: int = 3) -> None:
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def _fit_text(draw: ImageDraw.ImageDraw, text: str, max_width: int, font_size: int,
              min_size: int = 22, bold: bool = True) -> ImageFont.ImageFont:
    size = font_size
    while size > min_size:
        font = _dashboard_font(size, bold)
        if draw.textbbox((0, 0), str(text), font=font)[2] <= max_width:
            return font
        size -= 1
    return _dashboard_font(min_size, bold)


def _wrap_lines(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont,
                max_width: int, max_lines: int = 5) -> list[str]:
    words = str(text).split()
    lines: list[str] = []
    current = ""
    for word in words:
        trial = f"{current} {word}".strip()
        if draw.textbbox((0, 0), trial, font=font)[2] <= max_width:
            current = trial
        else:
            if current:
                lines.append(current)
            current = word
            if len(lines) >= max_lines - 1:
                break
    if current and len(lines) < max_lines:
        lines.append(current)
    return lines[:max_lines]


def _export_chart_png(fig: go.Figure, width: int, height: int) -> bytes:
    """Dedicated print renderer with exact aspect ratio and large typography."""
    dpi = 160
    mpl_fig, ax = plt.subplots(figsize=(width / dpi, height / dpi), dpi=dpi)
    mpl_fig.patch.set_facecolor("white")
    ax.set_facecolor("white")
    traces = list(fig.data)
    pie = next((t for t in traces if getattr(t, "type", "") == "pie"), None)
    horizontal = next((t for t in traces if getattr(t, "type", "") == "bar" and getattr(t, "orientation", None) == "h"), None)

    if pie is not None:
        labels = list(pie.labels or [])
        values = np.asarray(list(pie.values or []), dtype=float)
        pie_colors = getattr(getattr(pie, "marker", None), "colors", None)
        colors_list = list(pie_colors) if pie_colors is not None else [GREEN, RED, ORANGE, PURPLE, BLUE]
        wedges, _ = ax.pie(
            values, startangle=90, counterclock=False, colors=colors_list[:len(values)],
            wedgeprops=dict(width=0.40, edgecolor="white", linewidth=3),
        )
        total = values.sum()
        for wedge, value in zip(wedges, values):
            share = value / total if total else 0
            if share >= 0.025:
                angle = (wedge.theta1 + wedge.theta2) / 2
                x, y = 0.80 * np.cos(np.deg2rad(angle)), 0.80 * np.sin(np.deg2rad(angle))
                ax.text(x, y, f"{share:.1%}", ha="center", va="center", color="white", fontsize=22, fontweight="bold")
        center = f"{total:,.0f}\nTotal"
        if getattr(fig.layout, "annotations", None):
            center = _strip_html(fig.layout.annotations[0].text).replace("Total Defect", "\nTotal Defect")
        ax.text(0, 0, center, ha="center", va="center", fontsize=28, fontweight="bold", color=TEXT)
        ax.legend(wedges, labels, loc="center left", bbox_to_anchor=(1.0, 0.5), frameon=False,
                  fontsize=19, handlelength=1.2, labelspacing=1.0)
        ax.axis("equal")
        ax.axis("off")
        mpl_fig.subplots_adjust(left=0.03, right=0.72, top=0.96, bottom=0.04)

    elif horizontal is not None:
        labels = [str(x) for x in horizontal.y]
        values = np.asarray(list(horizontal.x), dtype=float)
        color = getattr(getattr(horizontal, "marker", None), "color", NAVY_MID)
        positions = np.arange(len(labels))
        ax.barh(positions, values, color=color, height=0.60)
        ax.set_yticks(positions)
        ax.set_yticklabels(labels, fontsize=22, fontweight="bold", color=TEXT)
        ax.tick_params(axis="x", labelsize=18, colors=TEXT, width=1.4)
        ax.grid(axis="x", color=GRID, linewidth=1.2)
        ax.set_axisbelow(True)
        ax.set_xlabel("PCS", fontsize=21, fontweight="bold", color=TEXT, labelpad=10)
        max_value = float(values.max()) if len(values) else 1.0
        txt = list(getattr(horizontal, "text", None) or [f"{v:,.0f}" for v in values])
        for y, value, label_text in zip(positions, values, txt):
            ax.text(value + max_value * 0.025, y, str(label_text), va="center", ha="left",
                    fontsize=20, fontweight="bold", color=TEXT)
        ax.set_xlim(0, max_value * 1.40 if max_value else 1)
        for spine in ("top", "right", "left"):
            ax.spines[spine].set_visible(False)
        ax.spines["bottom"].set_color("#AEBBCD")
        mpl_fig.subplots_adjust(left=0.31, right=0.93, top=0.94, bottom=0.16)

    else:
        bar_traces = [t for t in traces if getattr(t, "type", "") == "bar"]
        line_trace = next((t for t in traces if getattr(t, "type", "") == "scatter"), None)
        categories = [str(x) for x in (bar_traces[0].x if bar_traces else (line_trace.x if line_trace is not None else []))]
        pos = np.arange(len(categories))
        bar_width = 0.34
        handles, legend_labels = [], []
        for idx, trace in enumerate(bar_traces):
            vals = np.asarray(list(trace.y), dtype=float)
            offset = (idx - (len(bar_traces) - 1) / 2) * bar_width
            color = getattr(getattr(trace, "marker", None), "color", NAVY)
            bars = ax.bar(pos + offset, vals, width=bar_width, color=color, label=str(trace.name))
            for rect, value in zip(bars, vals):
                ax.text(rect.get_x() + rect.get_width()/2, rect.get_height(), f"{value:,.0f}",
                        ha="center", va="bottom", fontsize=19, fontweight="bold", color=TEXT)
        ax.set_xticks(pos)
        ax.set_xticklabels(categories, fontsize=21, fontweight="bold", color=TEXT)
        ax.set_ylabel("PCS", fontsize=22, fontweight="bold", color=TEXT)
        ax.tick_params(axis="y", labelsize=18, colors=TEXT)
        ax.grid(axis="y", color=GRID, linewidth=1.1)
        ax.set_axisbelow(True)
        handles, legend_labels = ax.get_legend_handles_labels()
        if line_trace is not None:
            ax2 = ax.twinx()
            rate = np.asarray(list(line_trace.y), dtype=float)
            line_color = getattr(getattr(line_trace, "line", None), "color", ORANGE)
            line, = ax2.plot(pos, rate, color=line_color, marker="o", linewidth=4.0, markersize=9, label=str(line_trace.name))
            for x, value in zip(pos, rate):
                ax2.text(x, value, f"{value:.2f}%", ha="center", va="bottom",
                         fontsize=19, fontweight="bold", color=RED)
            ax2.set_ylabel("%", fontsize=22, fontweight="bold", color=TEXT)
            ax2.tick_params(axis="y", labelsize=18, colors=TEXT)
            ax2.yaxis.set_major_formatter(FuncFormatter(lambda x, _: f"{x:.1f}%"))
            handles.append(line); legend_labels.append(str(line_trace.name))
        ax.legend(handles, legend_labels, loc="upper left", bbox_to_anchor=(0, 1.14), ncol=3,
                  frameon=False, fontsize=20)
        for spine in ("top", "right"):
            ax.spines[spine].set_visible(False)
        mpl_fig.subplots_adjust(left=0.10, right=0.89, top=0.82, bottom=0.18)

    buffer = io.BytesIO()
    mpl_fig.savefig(buffer, format="png", dpi=dpi, facecolor="white")
    plt.close(mpl_fig)
    return buffer.getvalue()


def _paste_chart(canvas: Image.Image, fig: go.Figure, box: tuple[int, int, int, int]) -> None:
    x1, y1, x2, y2 = box
    width, height = x2 - x1, y2 - y1
    chart = Image.open(io.BytesIO(_export_chart_png(fig, width, height))).convert("RGB")
    if chart.size != (width, height):
        chart = chart.resize((width, height), Image.Resampling.LANCZOS)
    canvas.paste(chart, (x1, y1))


def build_dashboard_pages(
    report_month: str,
    source: str,
    metrics: list[tuple[str, str, str]],
    insights: list[str],
    figures: list[tuple[str, go.Figure]],
    footer_metrics: list[tuple[str, str, str]],
) -> list[Image.Image]:
    """Create a dedicated print report, not a screenshot of the web page."""
    W, H = 3508, 2480  # A4 landscape at 300 dpi
    M = 70

    def page() -> tuple[Image.Image, ImageDraw.ImageDraw]:
        img = Image.new("RGB", (W, H), "#F3F6FB")
        return img, ImageDraw.Draw(img)

    def add_header(draw: ImageDraw.ImageDraw, title: str, subtitle: str, page_no: str) -> None:
        draw.rounded_rectangle((M, 55, W-M, 250), radius=34, fill=NAVY_DARK)
        draw.text((M+55, 98), title, font=_dashboard_font(58, True), fill="white")
        draw.text((W-M-55, 120), subtitle, font=_dashboard_font(28, True), fill="#D7E7FF", anchor="ra")
        draw.text((W-M-55, 185), page_no, font=_dashboard_font(23, True), fill="#AFC8EF", anchor="ra")

    # PAGE 1 — Executive summary
    p1, d1 = page()
    add_header(d1, "IQC QUALITY DASHBOARD", f"Reporting month: {report_month}  |  Source: {source}", "PAGE 1 / 2")

    # KPI cards
    kpi_top, kpi_bottom = 290, 645
    gap = 26
    card_w = (W - 2*M - gap*4) // 5
    fill_map = ["#EAF3FF", "#EAF8EE", "#FDECEC", "#FFF3E0", "#F3ECFF"]
    icon_chars = ["R", "A", "X", "%", "V"]
    for i, (label, value, accent) in enumerate(metrics[:5]):
        x1 = M + i*(card_w+gap); x2 = x1+card_w
        _rounded_card(d1, (x1, kpi_top, x2, kpi_bottom), radius=28, fill="white")
        d1.ellipse((x1+28, kpi_top+98, x1+142, kpi_top+212), fill=fill_map[i])
        d1.text((x1+85, kpi_top+155), icon_chars[i], font=_dashboard_font(40, True), fill=accent, anchor="mm")
        d1.text((x1+170, kpi_top+74), label.upper(), font=_dashboard_font(27, True), fill=TEXT)
        vf = _fit_text(d1, value, card_w-195, 54, 28, True)
        d1.text((x1+170, kpi_top+135), str(value), font=vf, fill=accent)

    # Main charts
    y1, y2 = 690, 1740
    left = (M, y1, 2280, y2)
    right = (2310, y1, W-M, y2)
    for box, title in ((left, figures[0][0]), (right, figures[1][0])):
        _rounded_card(d1, box, radius=28, fill="white")
        bar_w = min(850, box[2]-box[0]-50)
        d1.rounded_rectangle((box[0]+24, box[1]+22, box[0]+bar_w, box[1]+92), radius=13, fill=NAVY)
        d1.text((box[0]+48, box[1]+39), title.upper(), font=_dashboard_font(30, True), fill="white")
    _paste_chart(p1, figures[0][1], (left[0]+30, left[1]+115, left[2]-30, left[3]-30))
    _paste_chart(p1, figures[1][1], (right[0]+30, right[1]+115, right[2]-30, right[3]-30))

    # Insights as four readable cards
    insight_top, insight_bottom = 1790, 2380
    d1.rounded_rectangle((M, insight_top, W-M, insight_bottom), radius=30, fill="#FFF4C8", outline="#EDBE34", width=3)
    title_w = 510
    d1.rounded_rectangle((M, insight_top, M+title_w, insight_bottom), radius=30, fill="#FFBF1A")
    d1.text((M+70, insight_top+155), "KEY QUALITY", font=_dashboard_font(36, True), fill=NAVY_DARK)
    d1.text((M+70, insight_top+220), "INSIGHTS", font=_dashboard_font(48, True), fill=NAVY_DARK)
    d1.text((M+255, insight_top+370), "!", font=_dashboard_font(90, True), fill="white", anchor="mm")
    available = W-M-(M+title_w)-40
    iw = available // 4
    for i, insight in enumerate(insights[:4]):
        x1 = M+title_w+20+i*iw
        if i:
            d1.line((x1, insight_top+45, x1, insight_bottom-45), fill="#D2B45D", width=3)
        font = _dashboard_font(27, True)
        lines = _wrap_lines(d1, insight, font, iw-50, max_lines=7)
        d1.multiline_text((x1+24, insight_top+95), "\n".join(lines), font=font, fill=TEXT, spacing=17)

    # PAGE 2 — Detailed rankings
    p2, d2 = page()
    add_header(d2, "IQC QUALITY DASHBOARD — TOP 5 ANALYSIS", f"Reporting month: {report_month}", "PAGE 2 / 2")
    row_boxes = [(M, 300, W-M, 930), (M, 970, W-M, 1600), (M, 1640, W-M, 2270)]
    for (title, fig), box in zip(figures[2:5], row_boxes):
        _rounded_card(d2, box, radius=28, fill="white")
        d2.rounded_rectangle((box[0]+24, box[1]+22, box[0]+910, box[1]+92), radius=13, fill=NAVY)
        d2.text((box[0]+48, box[1]+39), title.upper(), font=_dashboard_font(30, True), fill="white")
        _paste_chart(p2, fig, (box[0]+35, box[1]+115, box[2]-35, box[3]-30))

    # Summary footer on page 2
    fy1, fy2 = 2310, 2425
    d2.rounded_rectangle((M, fy1, W-M, fy2), radius=22, fill=NAVY_DARK)
    sw = (W-2*M) // max(1, len(footer_metrics))
    for i, (label, value, accent) in enumerate(footer_metrics):
        x1=M+i*sw; x2=x1+sw
        if i:
            d2.line((x1, fy1+18, x1, fy2-18), fill="#4B6994", width=2)
        d2.text(((x1+x2)//2, fy1+22), label.upper(), font=_dashboard_font(18, True), fill="#EAF1FF", anchor="ma")
        vf=_fit_text(d2, value, sw-28, 31, 20, True)
        d2.text(((x1+x2)//2, fy1+65), str(value), font=vf, fill=accent, anchor="ma")

    return [p1, p2]


def dashboard_pages_bytes(images: list[Image.Image], output_format: str) -> tuple[bytes, str, str]:
    """Return a 2-page PDF or a ZIP with two print-quality PNG pages."""
    buffer = io.BytesIO()
    if output_format == "PDF":
        rgb = [img.convert("RGB") for img in images]
        rgb[0].save(buffer, format="PDF", save_all=True, append_images=rgb[1:], resolution=300.0)
        return buffer.getvalue(), "application/pdf", "pdf"
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for i, image in enumerate(images, 1):
            b = io.BytesIO(); image.save(b, format="PNG", optimize=True)
            archive.writestr(f"IQC_Dashboard_Print_Page_{i}.png", b.getvalue())
    return buffer.getvalue(), "application/zip", "zip"

# ============================================================
# DATA SOURCE
# ============================================================
with st.container(key="topbar"):
    title_col, month_col, vendor_col, item_col = st.columns([3.8, .8, .8, .8], gap="small")
    with title_col:
        st.markdown(
            '<div class="dash-title"><span class="dash-title-icon">📋</span>IQC QUALITY DASHBOARD</div>'
            '<div class="dash-subtitle">Incoming Quality Control · Interactive management report</div>',
            unsafe_allow_html=True,
        )

    # Data is loaded before filters below. Placeholders are created here and filled later.
    month_placeholder = month_col.empty()
    vendor_placeholder = vendor_col.empty()
    item_placeholder = item_col.empty()

with st.container(key="upload_panel"):
    with st.expander("📤 Upload / change data file", expanded=False):
        uploaded = st.file_uploader(
            "Upload IQC file",
            type=["xlsx", "xlsm", "xls", "csv"],
            label_visibility="collapsed",
        )
        st.caption("Đặt file mặc định tại `data/IQC_Data.xlsx` để mọi người xem chung một dữ liệu.")

try:
    if uploaded is not None:
        raw_df = read_file(uploaded.getvalue(), uploaded.name)
        source_name = uploaded.name
    else:
        raw_df, source_name = default_data()
except Exception as exc:
    st.error(f"Không thể đọc file: {exc}")
    st.stop()

if raw_df is None:
    st.info("Upload file IQC, hoặc thêm `data/IQC_Data.xlsx` vào GitHub.")
    st.stop()

try:
    df, c = prepare(raw_df)
except Exception as exc:
    st.error(str(exc))
    st.write("Các cột hiện có:", list(raw_df.columns))
    st.stop()

# ============================================================
# FILTERS (rendered inside the top bar placeholders)
# ============================================================
months = sorted(df["Year-Month"].dropna().unique(), reverse=True)
month_options = ["All"] + months
with month_placeholder.container():
    month = st.selectbox("Month (Year-Month)", month_options, index=1 if months else 0, key="month_filter")
month_df = df.copy() if month == "All" else df[df["Year-Month"] == month].copy()

vendor_options = ["(All)"] + sorted(x for x in month_df[c["vendor"]].unique() if x != "(Blank)")
with vendor_placeholder.container():
    vendor = st.selectbox("Vendor", vendor_options, key="vendor_filter")

item_options = ["(All)"] + sorted(x for x in month_df[c["item"]].unique() if x != "(Blank)")
with item_placeholder.container():
    item = st.selectbox("Item", item_options, key="item_filter")

filtered = month_df.copy()
if vendor != "(All)":
    filtered = filtered[filtered[c["vendor"]] == vendor]
if item != "(All)":
    filtered = filtered[filtered[c["item"]] == item]

# ============================================================
# METRICS
# ============================================================
received = float(filtered[c["received"]].sum())
approved = float(filtered[c["approved"]].sum())
rejected = float(filtered[c["rejected"]].sum())
reworked = float(filtered[c["reworked"]].sum())
special = float(filtered[c["special"]].sum())
quarantine = float(filtered[c["quarantine"]].sum())
to_inspect = float(filtered[c["to_inspect"]].sum())
reject_rate = rejected / received if received else 0.0

vendor_rej = filtered[filtered[c["vendor"]] != "(Blank)"].groupby(c["vendor"], dropna=False)[c["rejected"]].sum().sort_values(ascending=False).head(5)
item_rej = filtered[filtered[c["item"]] != "(Blank)"].groupby(c["item"], dropna=False)[c["rejected"]].sum().sort_values(ascending=False).head(5)
defect_rej = filtered[filtered[c["defect"]] != "(Blank)"].groupby(c["defect"], dropna=False)[c["rejected"]].sum().sort_values(ascending=False).head(5)
line_rej = filtered[filtered[c["location"]] != "(Blank)"].groupby(c["location"], dropna=False)[c["rejected"]].sum().sort_values(ascending=False)
line_rej = line_rej[line_rej > 0]
daily_rej = filtered.groupby(filtered[c["date"]].dt.date)[c["rejected"]].sum().sort_index()

top_line = str(line_rej.index[0]) if len(line_rej) else "-"
top_line_qty = float(line_rej.iloc[0]) if len(line_rej) else 0.0
top_vendor = str(vendor_rej.index[0]) if len(vendor_rej) else "-"
top_vendor_qty = float(vendor_rej.iloc[0]) if len(vendor_rej) else 0.0
top_item = str(item_rej.index[0]) if len(item_rej) else "-"
top_item_qty = float(item_rej.iloc[0]) if len(item_rej) else 0.0
top_defect = str(defect_rej.index[0]) if len(defect_rej) else "-"
top_defect_qty = float(defect_rej.iloc[0]) if len(defect_rej) else 0.0
top_day = daily_rej.idxmax().strftime("%Y-%m-%d") if len(daily_rej) and daily_rej.max() > 0 else "-"
top_day_qty = float(daily_rej.max()) if len(daily_rej) else 0.0

# Additional management insights that do not duplicate the KPI cards.
receipt_rej = (
    filtered[filtered[c["receipt"]] != "(Blank)"]
    .groupby(c["receipt"], dropna=False)[c["rejected"]]
    .sum()
    .sort_values(ascending=False)
)
top_po = str(receipt_rej.index[0]) if len(receipt_rej) and receipt_rej.iloc[0] > 0 else "-"
top_po_qty = float(receipt_rej.iloc[0]) if len(receipt_rej) else 0.0

defect_group_text = (
    filtered[c["defect"]]
    .fillna("(Blank)")
    .astype(str)
    .str.split(" - ", n=1).str[0]
    .str.split(":", n=1).str[0]
    .str.strip()
)
defect_group_rej = (
    filtered.assign(__defect_group=defect_group_text)
    .query('__defect_group != "(Blank)"')
    .groupby("__defect_group", dropna=False)[c["rejected"]]
    .sum()
    .sort_values(ascending=False)
)
top_defect_group = str(defect_group_rej.index[0]) if len(defect_group_rej) and defect_group_rej.iloc[0] > 0 else "-"
top_defect_group_qty = float(defect_group_rej.iloc[0]) if len(defect_group_rej) else 0.0
top1_vendor_qty = float(vendor_rej.iloc[0]) if len(vendor_rej) else 0.0
top1_vendor_share = top1_vendor_qty / rejected if rejected else 0.0

# ============================================================
# KPI ROW
# ============================================================
def display_vendor_name(name: str, max_chars: int = 30) -> str:
    text = safe(name).strip()
    if len(text) <= max_chars:
        return text
    words = text.split()
    lines = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if len(candidate) <= 17 or not current:
            current = candidate
        else:
            lines.append(current)
            current = word
        if len(lines) == 1:
            break
    if current and len(lines) < 2:
        lines.append(current)
    result = "<br>".join(lines[:2])
    if len(text) > sum(len(x) for x in lines[:2]) + max(0, len(lines[:2]) - 1):
        result += "…"
    return result

kpis = [
    ("📋", "TOTAL DEFECT", number(rejected), "PCS", RED),
    ("📦", "OUTPUT", number(received), "PCS", NAVY),
    ("✓", "DEFECT RATE", pct(reject_rate), "Rejected / Output", RED),
    ("🏢", "TOP VENDOR", display_vendor_name(top_vendor), f"{number(top_vendor_qty)} rejected pcs", NAVY),
    ("📦", "TOP DEFECTIVE ITEM", safe(top_item), f"{number(top_item_qty)} rejected pcs", NAVY),
]
kpi_html = '<div class="kpi-row">'
for icon, label, value, unit, color in kpis:
    extra_class = ' top-vendor' if label == 'TOP VENDOR' else (' top-item' if label == 'TOP DEFECTIVE ITEM' else '')
    kpi_html += (
        f'<div class="kpi{extra_class}">'
        f'<div class="kpi-icon">{icon}</div>'
        '<div>'
        f'<div class="kpi-label">{label}</div>'
        f'<div class="kpi-value" style="color:{color}">{value}</div>'
        f'<div class="kpi-unit">{unit}</div>'
        '</div></div>'
    )
kpi_html += '</div>'
st.markdown(kpi_html, unsafe_allow_html=True)

# ============================================================
# MAIN CHARTS
# ============================================================
left, right = st.columns([58, 42], gap="small")

with left:
    st.markdown('<div class="chart-card"><div class="chart-title">MONTH-OVER-MONTH PERFORMANCE</div>', unsafe_allow_html=True)
    monthly = df.groupby("Year-Month").agg(Output=(c["received"], "sum"), Defect=(c["rejected"], "sum")).sort_index()
    # Show only months that truly contain activity. This also prevents empty or
    # incorrectly parsed months from appearing on the chart.
    monthly = monthly[(monthly["Output"] > 0) | (monthly["Defect"] > 0)].tail(7)
    monthly["Defect Rate"] = (monthly["Defect"] / monthly["Output"].replace(0, pd.NA) * 100).fillna(0)
    monthly["Month Label"] = [pd.Period(x, freq="M").strftime("%b %Y") for x in monthly.index]

    month_fig = go.Figure()
    month_fig.add_bar(
        x=monthly["Month Label"],
        y=monthly["Output"],
        name="Output (pcs)",
        marker=dict(color=NAVY, line=dict(color=NAVY_DARK, width=1.1)),
        text=[f"{x:,.0f}" for x in monthly["Output"]],
        textposition="outside",
        cliponaxis=False,
        textfont=dict(size=16, color=TEXT, family="Arial Black"),
        hovertemplate="%{x}<br>Output: %{y:,.0f}<extra></extra>",
    )
    month_fig.add_bar(
        x=monthly["Month Label"],
        y=monthly["Defect"],
        name="Defect (pcs)",
        marker=dict(color=RED, line=dict(color="#B42318", width=1.1)),
        text=[f"{x:,.0f}" for x in monthly["Defect"]],
        textposition="outside",
        textfont=dict(size=17, color=RED, family="Arial Black"),
        hovertemplate="%{x}<br>Defect: %{y:,.0f}<extra></extra>",
    )
    month_fig.add_trace(
        go.Scatter(
            x=monthly["Month Label"],
            y=monthly["Defect Rate"],
            yaxis="y2",
            name="Defect Rate (%)",
            mode="lines+markers+text",
            line=dict(color=ORANGE, width=4),
            marker=dict(color=ORANGE, size=10, line=dict(color="white", width=1.5)),
            text=[f"{x:.2f}%" for x in monthly["Defect Rate"]],
            textposition="top left",
            textfont=dict(size=16, color=RED, family="Arial Black"),
            hovertemplate="%{x}<br>Defect rate: %{y:.2f}%<extra></extra>",
        )
    )
    layout(month_fig, 500, dict(l=92, r=92, t=80, b=82))
    month_fig.update_layout(
        barmode="group",
        font=dict(family="Arial Black", size=18, color=TEXT),
        legend=dict(orientation="h", yanchor="bottom", y=1.08, xanchor="left", x=0, font=dict(size=17, color=TEXT, family="Arial Black")),
        uniformtext_minsize=13,
        uniformtext_mode="show",
        yaxis=dict(title=dict(text="PCS", font=dict(size=18, color=TEXT, family="Arial Black")), gridcolor=GRID, tickfont=dict(size=17, color=TEXT, family="Arial Black"), range=[0, max(float(monthly["Output"].max()) * 1.20, 1)]),
        yaxis2=dict(title=dict(text="%", font=dict(size=18, color=TEXT, family="Arial Black")), overlaying="y", side="right", ticksuffix="%", showgrid=False, rangemode="tozero", tickfont=dict(size=17, color=TEXT, family="Arial Black")),
    )
    month_fig.update_xaxes(type="category", categoryorder="array", categoryarray=list(monthly["Month Label"]), tickfont=dict(size=17, color=TEXT, family="Arial Black"), tickangle=0, title=dict(text="Month", font=dict(size=18, color=TEXT, family="Arial Black")))
    st.plotly_chart(month_fig, use_container_width=True, config={"displayModeBar": False, "displaylogo": False, "responsive": True})
    st.markdown('</div>', unsafe_allow_html=True)

with right:
    st.markdown('<div class="chart-card"><div class="chart-title">DISPOSITION</div>', unsafe_allow_html=True)
    disposition = pd.Series({
        "Accepted": approved,
        "Rejected": rejected,
        "Reworked": reworked,
        "Special Released": special,
        "Quarantine": quarantine,
    })
    disposition = disposition[disposition > 0]
    if disposition.empty:
        donut = empty_chart("No disposition data", 500)
    else:
        colors = {
            "Accepted": GREEN,
            "Rejected": RED,
            "Reworked": BLUE,
            "Special Released": ORANGE,
            "Quarantine": PURPLE,
        }
        donut = go.Figure(
            go.Pie(
                labels=disposition.index,
                values=disposition.values,
                hole=.62,
                sort=False,
                marker=dict(colors=[colors[x] for x in disposition.index], line=dict(color="white", width=2)),
                textinfo="percent",
                textfont=dict(size=14, color="white", family="Arial Black"),
                hovertemplate="%{label}<br>%{value:,.0f} pcs<br>%{percent}<extra></extra>",
            )
        )
        donut.add_annotation(
            text=f"<b>{rejected:,.0f}</b><br><span style='font-size:12px'>Total Defect</span>",
            x=.5, y=.5, showarrow=False, font=dict(size=26, color=TEXT, family="Arial Black")
        )
        layout(donut, 500, dict(l=18, r=20, t=45, b=35))
        donut.update_layout(
            legend=dict(orientation="v", y=.5, x=.78, xanchor="left", font=dict(size=14, color=TEXT, family="Arial Black")),
            margin=dict(l=18, r=18, t=45, b=35),
        )
        donut.update_traces(domain=dict(x=[.02, .70], y=[.02, .98]))
    st.plotly_chart(donut, use_container_width=True, config={"displayModeBar": False, "displaylogo": False, "responsive": True})
    st.markdown('</div>', unsafe_allow_html=True)

# ============================================================
# INSIGHTS
# ============================================================
previous_month = None
previous_rate = None
if month != "All" and month in list(df["Year-Month"].unique()):
    ordered = sorted(df["Year-Month"].unique())
    idx = ordered.index(month)
    if idx > 0:
        previous_month = ordered[idx - 1]
        prev = df[df["Year-Month"] == previous_month]
        prev_received = float(prev[c["received"]].sum())
        previous_rate = float(prev[c["rejected"]].sum()) / prev_received if prev_received else 0

if month == "All":
    trend_label = "Overall defect rate"
    trend_value = pct(reject_rate)
    trend_note = f"Across {len(months)} month(s)"
elif previous_rate is None:
    trend_label = "Defect rate"
    trend_value = pct(reject_rate)
    trend_note = f"Period {month}"
else:
    delta = reject_rate - previous_rate
    direction = "increased" if delta > 0 else "decreased"
    trend_label = "Defect rate trend"
    trend_value = f"{direction} {abs(delta):.2%}"
    trend_note = f"vs {previous_month} ({pct(previous_rate)})"

insight_html = f"""
<div class="insights">
  <div class="insight-head"><div class="insight-bulb">💡</div><div>KEY QUALITY<br>INSIGHTS</div></div>
  <div class="insight-item"><div class="insight-copy"><span class="insight-label">Top PO reject</span><b>{safe(top_po)}</b><span class="insight-note">{number(top_po_qty)} rejected pcs</span></div></div>
  <div class="insight-item"><div class="insight-copy"><span class="insight-label">Top inspection day by reject</span><b>{safe(top_day)}</b><span class="insight-note">{number(top_day_qty)} rejected pcs</span></div></div>
  <div class="insight-item"><div class="insight-copy"><span class="insight-label">Top defect group</span><b>{safe(top_defect_group)}</b><span class="insight-note">{number(top_defect_group_qty)} rejected pcs</span></div></div>
  <div class="insight-item"><div class="insight-copy"><span class="insight-label">Top 1 vendor</span><b>{safe(top_vendor)}</b><span class="insight-note">{number(top1_vendor_qty)} rejected pcs · {pct(top1_vendor_share)} of total rejects</span></div></div>
</div>
"""
st.markdown(insight_html, unsafe_allow_html=True)

# ============================================================
# RANKED CHARTS
# ============================================================
rank_cols = st.columns(3, gap="small")
rank_specs = [
    (rank_cols[0], "TOP VENDORS BY REJECTED QTY", vendor_rej, "#1457B8"),
    (rank_cols[1], "TOP ITEMS BY REJECTED QTY", item_rej, "#2474D8"),
    (rank_cols[2], "TOP DEFECTS BY REJECTED QTY", defect_rej, RED),
]
rank_figures: list[tuple[str, go.Figure]] = []
for column, title, series, color in rank_specs:
    rank_fig = bar_chart(series, color, rejected)
    rank_figures.append((title, rank_fig))
    with column:
        st.markdown(f'<div class="chart-card"><div class="chart-title">{title}</div>', unsafe_allow_html=True)
        st.plotly_chart(rank_fig, use_container_width=True, config={"displayModeBar": False, "displaylogo": False, "responsive": True})
        st.markdown('</div>', unsafe_allow_html=True)

# ============================================================
# FOOTER SUMMARY
# ============================================================
record_count = len(filtered)
accepted_rate = approved / received if received else 0
counter_count = filtered[c["counter"]].replace("(Blank)", pd.NA).nunique()
if counter_count == 0:
    counter_count = filtered[c["vendor"]].replace("(Blank)", pd.NA).nunique()

supplier_ppm = (rejected / received * 1_000_000) if received else 0.0

summary = [
    ("📦", "TOTAL RECEIVED", number(received), "PCS", ""),
    ("✓", "TOTAL ACCEPTED", number(approved), pct(accepted_rate), "accepted"),
    ("✕", "TOTAL REJECTED", number(rejected), pct(reject_rate), "rejected"),
    ("%", "DEFECT RATE", pct(reject_rate), "Rejected / Received", "rate"),
    ("👤", "TOTAL COUNTER", number(counter_count), "People / Suppliers", ""),
    ("PPM", "SUPPLIER PPM", number(round(supplier_ppm)), "Rejected / Received × 1,000,000", "rate"),
]
footer_html = '<div class="summary-strip">'
for icon, label, value, unit, value_class in summary:
    footer_html += (
        '<div class="summary-item">'
        f'<div class="summary-icon">{icon}</div>'
        '<div>'
        f'<div class="summary-label">{label}</div>'
        f'<div class="summary-value {value_class}">{safe(value)}</div>'
        f'<div class="summary-unit">{safe(unit)}</div>'
        '</div></div>'
    )
footer_html += '</div>'
st.markdown(footer_html, unsafe_allow_html=True)

# ============================================================
# ONE-BUTTON FULL DASHBOARD EXPORT
# ============================================================
full_figures = [("Month-over-Month Performance", month_fig), ("Disposition", donut)] + rank_figures
full_metrics = [
    ("Total Received", number(received), NAVY_MID),
    ("Approved", number(approved), GREEN),
    ("Rejected", number(rejected), RED),
    ("Reject Rate", pct(reject_rate), ORANGE),
    ("Top Defective Item", top_item, PURPLE),
]
full_insights = [
    f"Top PO reject: {top_po} — {number(top_po_qty)} rejected pcs",
    f"Top inspection day by reject: {top_day} — {number(top_day_qty)} rejected pcs",
    f"Top defect group: {top_defect_group} — {number(top_defect_group_qty)} rejected pcs",
    f"Top 1 vendor: {top_vendor} — {number(top1_vendor_qty)} rejected pcs ({pct(top1_vendor_share)})",
]
full_footer = [
    ("Total Received", number(received), "#FFFFFF"),
    ("Total Accepted", number(approved), "#42D67B"),
    ("Total Rejected", number(rejected), "#FF665C"),
    ("Defect Rate", pct(reject_rate), "#FFD33D"),
    ("Vendors", number(counter_count), "#FFFFFF"),
    ("Supplier PPM", number(round(supplier_ppm)), "#FFD33D"),
]

st.markdown('<div style="margin-top:12px;font-size:18px;font-weight:900;color:#062B63">⬇️ EXPORT PROFESSIONAL REPORT</div>', unsafe_allow_html=True)
try:
    dashboard_pages = build_dashboard_pages(
        report_month=month,
        source=source_name or "Uploaded file",
        metrics=full_metrics,
        insights=full_insights,
        figures=full_figures,
        footer_metrics=full_footer,
    )
    export_format_col, export_button_col = st.columns([1, 2], gap="small")
    with export_format_col:
        export_format = st.selectbox("Export format", ["PDF", "PNG"], label_visibility="collapsed")
    export_bytes, export_mime, extension = dashboard_pages_bytes(dashboard_pages, export_format)
    with export_button_col:
        st.download_button(
            "⬇️ EXPORT PROFESSIONAL REPORT",
            data=export_bytes,
            file_name=f"IQC_Professional_Report_{month}.{extension}",
            mime=export_mime,
            use_container_width=True,
            type="primary",
        )
    st.caption("PDF gồm 2 trang A4 ngang được thiết kế riêng cho bản in. PNG được tải dưới dạng ZIP chứa 2 ảnh chất lượng cao.")
except Exception as export_error:
    st.error(f"Không thể tạo file dashboard: {export_error}")
    st.caption("Vui lòng kiểm tra lại dữ liệu hoặc tải lại trang. Bản Print Pro xuất PDF 2 trang hoặc ZIP gồm 2 ảnh PNG, không cần Chrome/Kaleido.")

st.markdown(
    f'<div class="source-note">Source: {safe(source_name)} · Defect Rate = Rejected Qty / Received Qty × 100%</div>',
    unsafe_allow_html=True,
)

with st.expander("🔎 View filtered data"):
    st.dataframe(filtered, use_container_width=True, hide_index=True, height=390)
    st.download_button(
        "Download filtered CSV",
        filtered.to_csv(index=False).encode("utf-8-sig"),
        file_name=f"IQC_filtered_{month}.csv",
        mime="text/csv",
    )
