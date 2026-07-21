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
    padding:12px 18px 8px;
    box-shadow:0 5px 16px rgba(4,30,72,.22);
    margin-bottom:5px;
}}
.st-key-topbar div[data-testid="stHorizontalBlock"] {{align-items:center; gap:.65rem;}}
.dash-title {{color:white; font-weight:900; font-size:clamp(28px,2.6vw,42px); line-height:1; letter-spacing:.2px; white-space:nowrap;}}
.dash-title-icon {{display:inline-flex;width:56px;height:56px;border-radius:50%;align-items:center;justify-content:center;background:white;color:{NAVY};font-size:30px;margin-right:12px;vertical-align:middle;}}
.dash-subtitle {{font-size:12px;color:#D7E5FB;margin:5px 0 0 70px;letter-spacing:.2px;}}
.st-key-topbar label {{color:white!important;font-weight:800!important;font-size:12px!important;margin-bottom:0!important;}}
.st-key-topbar div[data-baseweb="select"] > div {{
    min-height:38px!important;height:38px!important;border:0!important;border-radius:6px!important;background:white!important;
    font-size:13px!important;box-shadow:none!important;
}}
.st-key-topbar div[data-testid="stSelectbox"] {{margin-top:-3px;}}

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
.kpi-unit {{font-size:12px;color:#17243A;font-weight:700;margin-top:3px;}}

/* ---------- Chart cards ---------- */
.chart-card {{background:white;border:1.2px solid {BORDER};border-radius:12px;padding:10px 12px 7px;box-shadow:0 4px 14px rgba(15,40,80,.09);}}
.chart-title {{display:inline-block;background:linear-gradient(90deg,{NAVY_DARK},{NAVY_MID});color:white;padding:7px 20px;border-radius:7px;font-size:16px;font-weight:900;letter-spacing:.25px;margin:0 0 5px 10px;min-width:220px;text-align:center;}}
div[data-testid="stPlotlyChart"] {{margin-top:-3px;margin-bottom:-3px;}}


/* ---------- Plotly chart typography ---------- */
div[data-testid="stPlotlyChart"] .main-svg text {{
    font-family: Arial Black, Arial, Helvetica, sans-serif !important;
    font-weight: 800 !important;
    fill: #0A2147 !important;
}}

/* ---------- Insight strip ---------- */
.insights {{display:grid;grid-template-columns:1.05fr repeat(4,1fr);background:linear-gradient(90deg,#FFF7D7,#FFF1B9);border:1px solid #F0D77A;border-radius:12px;margin:8px 0;padding:12px 14px;box-shadow:0 2px 7px rgba(120,90,0,.06);}}
.insight-head {{display:flex;align-items:center;font-size:20px;font-weight:900;color:#17233D;padding-right:10px;}}
.insight-bulb {{width:52px;height:52px;border-radius:50%;display:flex;align-items:center;justify-content:center;background:{ORANGE};color:white;font-size:27px;margin-right:13px;}}
.insight-item {{border-left:1px dashed #8D98A7;padding:7px 16px;font-size:14px;line-height:1.48;color:#1F2937;display:flex;align-items:center;}}
.insight-item b {{color:{RED};font-weight:900;}}

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
    df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
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
        paper_bgcolor="rgba(0,0,0,0)",
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
        return empty_chart("No rejected quantity", 350)
    labels = [f"{value:,.0f} ({value / total:.2%})" if total else f"{value:,.0f}" for value in s.values]
    fig = go.Figure(
        go.Bar(
            x=s.values,
            y=s.index,
            orientation="h",
            marker=dict(color=color, line=dict(color="rgba(0,0,0,0.10)", width=1.0)),
            text=labels,
            textposition="outside",
            cliponaxis=False,
            textfont=dict(size=18, color=TEXT, family="Arial Black"),
            hovertemplate="%{y}<br>%{x:,.0f} pcs<extra></extra>",
        )
    )
    layout(fig, 470, dict(l=70, r=180, t=26, b=70))
    fig.update_layout(showlegend=False)
    fig.update_xaxes(title=dict(text="PCS", font=dict(size=18, color=TEXT, family="Arial Black")), rangemode="tozero", tickfont=dict(size=17, color=TEXT, family="Arial Black"))
    fig.update_yaxes(automargin=True, tickfont=dict(size=18, color=TEXT, family="Arial Black"))
    return fig


def figure_png(fig: go.Figure, width: int = 1500, height: int = 850) -> bytes:
    """Render a Plotly figure as a high-resolution PNG using Kaleido."""
    return fig.to_image(format="png", width=width, height=height, scale=2)


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
    """Load a clear font available on Streamlit Cloud, with a safe fallback."""
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


def _rounded_card(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], radius: int = 22,
                  fill: str = "#FFFFFF", outline: str = BORDER, width: int = 2) -> None:
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def _fit_text(draw: ImageDraw.ImageDraw, text: str, max_width: int, font_size: int,
              min_size: int = 18, bold: bool = True) -> ImageFont.ImageFont:
    size = font_size
    while size > min_size:
        font = _dashboard_font(size, bold)
        if draw.textbbox((0, 0), text, font=font)[2] <= max_width:
            return font
        size -= 1
    return _dashboard_font(min_size, bold)


def _paste_chart(canvas: Image.Image, fig: go.Figure, box: tuple[int, int, int, int]) -> None:
    x1, y1, x2, y2 = box
    width, height = x2 - x1, y2 - y1
    png = Image.open(io.BytesIO(figure_png(fig, width=max(width, 900), height=max(height, 520)))).convert("RGB")
    png.thumbnail((width, height), Image.Resampling.LANCZOS)
    px = x1 + (width - png.width) // 2
    py = y1 + (height - png.height) // 2
    canvas.paste(png, (px, py))


def build_full_dashboard_image(
    report_month: str,
    source: str,
    metrics: list[tuple[str, str, str]],
    insights: list[str],
    figures: list[tuple[str, go.Figure]],
    footer_metrics: list[tuple[str, str, str]],
) -> Image.Image:
    """Create one high-resolution image containing the complete dashboard."""
    W, H = 2200, 2450
    canvas = Image.new("RGB", (W, H), "#F3F6FB")
    draw = ImageDraw.Draw(canvas)

    # Header
    draw.rounded_rectangle((30, 24, W - 30, 150), radius=28, fill=NAVY_DARK)
    draw.text((70, 54), "IQC QUALITY DASHBOARD", font=_dashboard_font(50, True), fill="white")
    subtitle = f"Month: {report_month}   |   Source: {source}"
    draw.text((W - 70, 82), subtitle, font=_dashboard_font(24, True), fill="#D9E8FF", anchor="ra")

    # KPI cards
    card_gap = 20
    card_y1, card_y2 = 180, 390
    card_w = (W - 60 - card_gap * (len(metrics) - 1)) // len(metrics)
    accent_fills = ["#EAF3FF", "#EAF8EE", "#FDECEC", "#FFF4E5", "#F3EDFF"]
    for idx, (label, value, accent) in enumerate(metrics):
        x1 = 30 + idx * (card_w + card_gap)
        x2 = x1 + card_w
        _rounded_card(draw, (x1, card_y1, x2, card_y2), fill="white")
        draw.ellipse((x1 + 24, card_y1 + 46, x1 + 112, card_y1 + 134), fill=accent_fills[idx % len(accent_fills)])
        draw.text((x1 + 68, card_y1 + 90), str(idx + 1), font=_dashboard_font(34, True), fill=accent, anchor="mm")
        draw.text((x1 + 130, card_y1 + 50), label.upper(), font=_dashboard_font(23, True), fill=TEXT)
        value_font = _fit_text(draw, value, card_w - 155, 43, 25, True)
        draw.text((x1 + 130, card_y1 + 92), value, font=value_font, fill=accent)

    # Main chart row
    main_y1, main_y2 = 425, 1120
    left_box = (30, main_y1, 1390, main_y2)
    right_box = (1410, main_y1, W - 30, main_y2)
    for box, title in [(left_box, figures[0][0]), (right_box, figures[1][0])]:
        _rounded_card(draw, box, fill="white")
        draw.rounded_rectangle((box[0] + 18, box[1] + 16, box[0] + 520, box[1] + 65), radius=12, fill=NAVY)
        draw.text((box[0] + 36, box[1] + 27), title.upper(), font=_dashboard_font(24, True), fill="white")
    _paste_chart(canvas, figures[0][1], (left_box[0] + 20, left_box[1] + 75, left_box[2] - 20, left_box[3] - 20))
    _paste_chart(canvas, figures[1][1], (right_box[0] + 20, right_box[1] + 75, right_box[2] - 20, right_box[3] - 20))

    # Insight strip
    ins_y1, ins_y2 = 1150, 1365
    draw.rounded_rectangle((30, ins_y1, W - 30, ins_y2), radius=22, fill="#FFF3C4", outline="#F1BE32", width=2)
    draw.ellipse((55, ins_y1 + 50, 155, ins_y1 + 150), fill="#FDBB16")
    draw.text((105, ins_y1 + 100), "!", font=_dashboard_font(50, True), fill=NAVY_DARK, anchor="mm")
    draw.text((180, ins_y1 + 50), "KEY QUALITY\nINSIGHTS", font=_dashboard_font(28, True), fill=TEXT)
    start_x = 430
    insight_w = (W - start_x - 50) // max(len(insights), 1)
    for idx, text in enumerate(insights):
        x = start_x + idx * insight_w
        if idx:
            draw.line((x, ins_y1 + 30, x, ins_y2 - 30), fill="#D8B85F", width=2)
        # Basic line wrapping
        words, lines, current = text.split(), [], ""
        font = _dashboard_font(20, True)
        for word in words:
            trial = (current + " " + word).strip()
            if draw.textbbox((0, 0), trial, font=font)[2] <= insight_w - 34:
                current = trial
            else:
                if current:
                    lines.append(current)
                current = word
        if current:
            lines.append(current)
        draw.multiline_text((x + 18, ins_y1 + 45), "\n".join(lines[:5]), font=font, fill=TEXT, spacing=8)

    # Three ranked charts
    rank_y1, rank_y2 = 1395, 2115
    rank_gap = 18
    rank_w = (W - 60 - rank_gap * 2) // 3
    for idx, (title, fig) in enumerate(figures[2:5]):
        x1 = 30 + idx * (rank_w + rank_gap)
        x2 = x1 + rank_w
        _rounded_card(draw, (x1, rank_y1, x2, rank_y2), fill="white")
        draw.rounded_rectangle((x1 + 18, rank_y1 + 16, x2 - 18, rank_y1 + 68), radius=12, fill=NAVY)
        title_font = _fit_text(draw, title.upper(), rank_w - 70, 23, 17, True)
        draw.text((x1 + 35, rank_y1 + 29), title.upper(), font=title_font, fill="white")
        _paste_chart(canvas, fig, (x1 + 15, rank_y1 + 78, x2 - 15, rank_y2 - 15))

    # Footer summary
    foot_y1, foot_y2 = 2145, 2415
    draw.rounded_rectangle((30, foot_y1, W - 30, foot_y2), radius=24, fill=NAVY_DARK)
    footer_w = (W - 60) // max(len(footer_metrics), 1)
    for idx, (label, value, accent) in enumerate(footer_metrics):
        x1 = 30 + idx * footer_w
        x2 = x1 + footer_w
        if idx:
            draw.line((x1, foot_y1 + 30, x1, foot_y2 - 30), fill="#4F6D97", width=2)
        draw.text(((x1 + x2) // 2, foot_y1 + 48), label.upper(), font=_dashboard_font(20, True), fill="white", anchor="ma")
        val_font = _fit_text(draw, value, footer_w - 30, 34, 20, True)
        draw.text(((x1 + x2) // 2, foot_y1 + 112), value, font=val_font, fill=accent, anchor="ma")

    return canvas


def dashboard_image_bytes(image: Image.Image, output_format: str) -> tuple[bytes, str]:
    buffer = io.BytesIO()
    if output_format == "PDF":
        image.convert("RGB").save(buffer, format="PDF", resolution=150.0)
        return buffer.getvalue(), "application/pdf"
    image.save(buffer, format="PNG", optimize=True)
    return buffer.getvalue(), "image/png"

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
with month_placeholder.container():
    month = st.selectbox("Month (Year-Month)", months, index=0, key="month_filter")
month_df = df[df["Year-Month"] == month].copy()

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

# ============================================================
# KPI ROW
# ============================================================
kpis = [
    ("📋", "TOTAL DEFECT", number(rejected), "PCS", RED),
    ("📦", "OUTPUT", number(received), "PCS", NAVY),
    ("✓", "DEFECT RATE", pct(reject_rate), "Rejected / Output", RED),
    ("🏢", "TOP VENDOR", safe(top_vendor), f"{number(top_vendor_qty)} rejected pcs", NAVY),
    ("📅", "TOP INSPECTION DAY", safe(top_day), "Date", NAVY),
]
kpi_html = '<div class="kpi-row">'
for icon, label, value, unit, color in kpis:
    kpi_html += (
        '<div class="kpi">'
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
left, right = st.columns([1.42, 1], gap="small")

with left:
    st.markdown('<div class="chart-card"><div class="chart-title">MONTH-OVER-MONTH PERFORMANCE</div>', unsafe_allow_html=True)
    monthly = df.groupby("Year-Month").agg(Output=(c["received"], "sum"), Defect=(c["rejected"], "sum")).sort_index()
    monthly = monthly.tail(7)
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
        textfont=dict(size=17, color=TEXT, family="Arial Black"),
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
            textposition="top center",
            textfont=dict(size=17, color=RED, family="Arial Black"),
            hovertemplate="%{x}<br>Defect rate: %{y:.2f}%<extra></extra>",
        )
    )
    layout(month_fig, 500, dict(l=92, r=92, t=80, b=82))
    month_fig.update_layout(
        barmode="group",
        font=dict(family="Arial Black", size=18, color=TEXT),
        legend=dict(orientation="h", yanchor="bottom", y=1.05, xanchor="left", x=0, font=dict(size=17, color=TEXT, family="Arial Black")),
        yaxis=dict(title=dict(text="PCS", font=dict(size=18, color=TEXT, family="Arial Black")), gridcolor=GRID, tickfont=dict(size=17, color=TEXT, family="Arial Black")),
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
        donut = empty_chart("No disposition data", 390)
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
        layout(donut, 390, dict(l=8, r=28, t=30, b=12))
        donut.update_layout(legend=dict(orientation="v", y=.5, x=1.03, xanchor="left", font=dict(size=13, color=TEXT)))
    st.plotly_chart(donut, use_container_width=True, config={"displayModeBar": False, "displaylogo": False, "responsive": True})
    st.markdown('</div>', unsafe_allow_html=True)

# ============================================================
# INSIGHTS
# ============================================================
previous_month = None
previous_rate = None
if month in list(df["Year-Month"].unique()):
    ordered = sorted(df["Year-Month"].unique())
    idx = ordered.index(month)
    if idx > 0:
        previous_month = ordered[idx - 1]
        prev = df[df["Year-Month"] == previous_month]
        prev_received = float(prev[c["received"]].sum())
        previous_rate = float(prev[c["rejected"]].sum()) / prev_received if prev_received else 0

if previous_rate is None:
    trend_sentence = f"Defect rate in {month}: <b>{pct(reject_rate)}</b>."
else:
    delta = reject_rate - previous_rate
    direction = "increased" if delta > 0 else "decreased"
    trend_sentence = f"Defect rate <b>{direction} {abs(delta):.2%}</b> vs {previous_month} ({pct(previous_rate)})."

insight_html = f"""
<div class="insights">
  <div class="insight-head"><div class="insight-bulb">💡</div><div>KEY QUALITY<br>INSIGHTS</div></div>
  <div class="insight-item">{trend_sentence}</div>
  <div class="insight-item">Top inspection day:<br><b>{safe(top_day)}</b>&nbsp; with {number(top_day_qty)} pcs defects.</div>
  <div class="insight-item">Vendor <b>{safe(top_vendor)}</b> has the highest rejected quantity: {number(top_vendor_qty)} pcs.</div>
  <div class="insight-item">Top item: <b>{safe(top_item)}</b> · Top defect: <b>{safe(top_defect)}</b>.</div>
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

inspection_time_text = "N/A"
time_col = c.get("inspection_time")
if time_col and time_col in filtered.columns and pd.api.types.is_timedelta64_dtype(filtered[time_col]):
    total_seconds = int(filtered[time_col].dropna().dt.total_seconds().sum())
    hours, rem = divmod(total_seconds, 3600)
    minutes, seconds = divmod(rem, 60)
    inspection_time_text = f"{hours:02d}:{minutes:02d}:{seconds:02d}"

summary = [
    ("📋", "TOTAL INSPECTION", number(to_inspect if to_inspect > 0 else record_count), "Times / PCS", ""),
    ("✓", "TOTAL ACCEPTED", number(approved), pct(accepted_rate), "accepted"),
    ("✕", "TOTAL REJECTED", number(rejected), pct(reject_rate), "rejected"),
    ("%", "DEFECT RATE", pct(reject_rate), "Rejected / Output", "rate"),
    ("👤", "TOTAL COUNTER", number(counter_count), "People / Suppliers", ""),
    ("◷", "INSPECTION TIME", inspection_time_text, "HH:MM:SS", ""),
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
    ("Top Vendor", top_vendor, PURPLE),
]
full_insights = [
    f"Top vendor: {top_vendor} — {number(top_vendor_qty)} rejected pcs",
    f"Top inspection day: {top_day} — {number(top_day_qty)} rejected pcs",
    f"Top item: {top_item} — {number(top_item_qty)} rejected pcs",
    f"Top defect: {top_defect} — {number(top_defect_qty)} rejected pcs",
]
full_footer = [
    ("Total Inspection", number(to_inspect if to_inspect > 0 else record_count), "#FFFFFF"),
    ("Total Accepted", number(approved), "#42D67B"),
    ("Total Rejected", number(rejected), "#FF665C"),
    ("Defect Rate", pct(reject_rate), "#FFD33D"),
    ("Vendors", number(counter_count), "#FFFFFF"),
    ("Items", number(filtered[c["item"]].replace("(Blank)", pd.NA).nunique()), "#FFFFFF"),
]

try:
    dashboard_image = build_full_dashboard_image(
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
    export_bytes, export_mime = dashboard_image_bytes(dashboard_image, export_format)
    extension = export_format.lower()
    with export_button_col:
        st.download_button(
            "⬇️ EXPORT FULL DASHBOARD",
            data=export_bytes,
            file_name=f"IQC_Full_Dashboard_{month}.{extension}",
            mime=export_mime,
            use_container_width=True,
            type="primary",
        )
    st.caption("Xuất một file duy nhất bao gồm toàn bộ KPI, biểu đồ, insight và phần tổng kết của dashboard.")
except Exception as export_error:
    st.warning(f"Không thể tạo file dashboard: {export_error}. Kiểm tra kaleido trong requirements.txt.")

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
