from __future__ import annotations

import html
import io
import re
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path
from datetime import date, datetime
from typing import Iterable

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import streamlit.components.v1 as components
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
.block-container {{max-width: 1920px; min-width: 1500px; padding: 0.35rem 0.75rem 0.85rem;}}
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
.kpi {{display:flex;align-items:center;min-height:122px;padding:12px 15px;border-right:1px solid #D7DEE8;min-width:0;}}
.kpi:last-child {{border-right:0;}}
.kpi > div:last-child {{min-width:0;flex:1;}}
.kpi-icon {{width:60px;height:60px;min-width:60px;border-radius:50%;display:flex;align-items:center;justify-content:center;background:{NAVY};color:white;font-size:28px;margin-right:13px;box-shadow:inset 0 0 0 2px rgba(255,255,255,.13);}}
.kpi-label {{font-size:12px;font-weight:900;color:#101828;letter-spacing:.15px;white-space:normal;line-height:1.15;margin-bottom:5px;}}
.kpi-value {{font-size:clamp(24px,2vw,34px);font-weight:900;line-height:1.08;margin-top:2px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:100%;}}
.kpi.top-vendor .kpi-value, .kpi.top-item .kpi-value {{font-size:clamp(17px,1.35vw,22px);line-height:1.16;white-space:normal;overflow:visible;text-overflow:clip;max-width:100%;overflow-wrap:break-word;word-break:normal;}}
.kpi.top-vendor, .kpi.top-item {{padding-left:12px;padding-right:12px;}}
.kpi-unit {{font-size:11px;color:#17243A;font-weight:700;margin-top:5px;line-height:1.2;white-space:normal;}}

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
.insights {{display:grid;grid-template-columns:1.05fr repeat(4,minmax(0,1fr));background:linear-gradient(90deg,#FFF8D9,#FFF0B5);border:1.5px solid #E9B92E;border-radius:12px;margin:10px 0;padding:15px 16px;box-shadow:0 3px 10px rgba(120,90,0,.10);min-height:142px;align-items:stretch;}}
.insight-head {{display:flex;align-items:center;font-size:20px;font-weight:900;color:#102A56;padding-right:14px;line-height:1.2;}}
.insight-bulb {{width:54px;height:54px;min-width:54px;border-radius:50%;display:flex;align-items:center;justify-content:center;background:{ORANGE};color:white;font-size:28px;margin-right:12px;box-shadow:0 2px 6px rgba(120,80,0,.18);}}
.insight-item {{border-left:1px dashed #9A8B5F;padding:10px 16px;color:#17233D;display:flex;align-items:center;justify-content:center;min-width:0;}}
.insight-copy {{width:100%;display:flex;flex-direction:column;justify-content:center;align-items:flex-start;gap:6px;font-size:14px;font-weight:700;line-height:1.32;overflow-wrap:break-word;word-break:normal;min-width:0;}}
.insight-copy .insight-label {{font-size:13px;font-weight:900;color:#102A56;text-transform:uppercase;letter-spacing:.15px;}}
.insight-copy b {{color:{RED};font-size:16px;font-weight:900;line-height:1.2;}}
.insight-copy .insight-note {{font-size:14px;font-weight:700;color:#27364F;}}

/* ---------- Bottom summary ---------- */
.summary-strip {{display:grid;grid-template-columns:repeat(7,1fr);background:linear-gradient(100deg,{NAVY_DARK},{NAVY});color:white;border-radius:12px;padding:10px 6px;margin-top:5px;box-shadow:0 5px 14px rgba(4,30,72,.18);}}
.summary-item {{display:flex;align-items:center;justify-content:center;border-right:1px solid rgba(255,255,255,.35);min-height:82px;padding:5px 10px;}}
.summary-item:last-child {{border-right:0;}}
.summary-icon {{width:50px;height:50px;min-width:50px;border-radius:50%;display:flex;align-items:center;justify-content:center;background:white;color:{NAVY};font-size:24px;margin-right:11px;}}
.summary-label {{font-size:12px;font-weight:850;color:#E5EEFC;white-space:nowrap;}}
.summary-value {{font-size:27px;font-weight:900;line-height:1.05;margin-top:3px;white-space:nowrap;}}
.summary-value.accepted {{color:#63D65E;}}
.summary-value.rejected {{color:#FF4B3E;}}
.summary-value.special {{color:#FFB000;}}
.summary-value.rate {{color:#FFD21F;}}
.summary-unit {{font-size:11.5px;color:#D8E5F8;margin-top:2px;}}
.source-note {{text-align:center;font-size:10px;color:#667085;margin-top:4px;}}

/* ---------- Data table ---------- */
div[data-testid="stExpander"] details {{background:white;border:1px solid {BORDER};border-radius:8px;}}


/* ---------- Screenshot export mode ---------- */
.export-mode .kpi-row {{padding:12px 8px;}}
.export-mode .kpi {{min-height:140px;padding:14px 16px;align-items:center;}}
.export-mode .kpi-icon {{width:58px;height:58px;min-width:58px;font-size:27px;margin-right:12px;}}
.export-mode .kpi-label {{font-size:12px;line-height:1.18;margin-bottom:7px;}}
.export-mode .kpi-value {{font-size:30px;line-height:1.12;margin-top:0;}}
.export-mode .kpi.top-vendor .kpi-value, .export-mode .kpi.top-item .kpi-value {{font-size:17px;line-height:1.12;max-width:100%;white-space:normal!important;overflow-wrap:anywhere!important;word-break:break-word!important;hyphens:auto;}}
.export-mode .kpi-unit {{font-size:11px;line-height:1.25;margin-top:7px;}}
.export-mode .insights {{min-height:165px;padding:18px 18px;}}
.export-mode .insight-head {{font-size:18px;line-height:1.25;}}
.export-mode .insight-item {{padding:12px 18px;}}
.export-mode .insight-copy {{font-size:14px;line-height:1.35;gap:7px;}}
.export-mode .insight-copy .insight-label {{font-size:12px;line-height:1.2;}}
.export-mode .insight-copy b {{font-size:15px;line-height:1.25;}}
.export-mode .insight-copy .insight-note {{font-size:13px;line-height:1.3;}}
.export-mode .chart-title {{font-size:15px;}}
/* Compact only the areas that tend to overlap in html2canvas export */
.export-mode .kpi:nth-child(3) .kpi-label {{font-size:10px;line-height:1.1;}}
.export-mode .kpi:nth-child(3) .kpi-value {{font-size:25px;line-height:1.05;}}
.export-mode .kpi:nth-child(3) .kpi-unit {{font-size:9px;line-height:1.15;margin-top:5px;}}
.export-mode .kpi:nth-child(5) .kpi-label {{font-size:9.5px;line-height:1.08;}}
.export-mode .kpi:nth-child(5) .kpi-value {{font-size:17px;line-height:1.12;}}
.export-mode .kpi:nth-child(5) .kpi-unit {{font-size:9px;line-height:1.12;margin-top:5px;}}
.export-mode .insights .insight-item:last-child .insight-label {{font-size:10px;line-height:1.1;}}
.export-mode .insights .insight-item:last-child b {{font-size:13px;line-height:1.15;}}
.export-mode .insights .insight-item:last-child .insight-note {{font-size:11px;line-height:1.2;}}

/* Stable wrapping for long vendor/item names and rate cards during export */
.kpi.defect-rate > div:last-child,
.kpi.top-vendor > div:last-child,
.kpi.top-item > div:last-child,
.summary-item.defect-rate-summary > div:last-child {{min-width:0;}}
.kpi.top-vendor .kpi-value,
.kpi.top-item .kpi-value {{white-space:normal;overflow-wrap:anywhere;word-break:break-word;}}
.export-mode .kpi.defect-rate {{padding-top:12px;padding-bottom:12px;}}
.export-mode .kpi.defect-rate .kpi-label {{font-size:10px;line-height:1.05;margin-bottom:4px;}}
.export-mode .kpi.defect-rate .kpi-value {{font-size:23px;line-height:1.0;margin:0;white-space:nowrap;}}
.export-mode .kpi.defect-rate .kpi-unit {{font-size:8.5px;line-height:1.05;margin-top:4px;white-space:normal;}}
.export-mode .summary-item.defect-rate-summary {{padding-left:6px;padding-right:6px;}}
.export-mode .summary-item.defect-rate-summary .summary-label {{font-size:8.5px;line-height:1.0;white-space:normal;text-align:left;}}
.export-mode .summary-item.defect-rate-summary .summary-value {{font-size:20px;line-height:1.0;white-space:nowrap;}}
.export-mode .summary-item.defect-rate-summary .summary-unit {{font-size:7.5px;line-height:1.05;white-space:normal;max-width:105px;}}

/* Improve text readability in html2canvas export */
.export-mode .kpi-label,
.export-mode .kpi-unit,
.export-mode .insight-label,
.export-mode .insight-note,
.export-mode .summary-label,
.export-mode .summary-unit {{
    font-family: Arial, Helvetica, sans-serif !important;
    font-weight: 700 !important;
    letter-spacing: .35px !important;
    word-spacing: 1.4px !important;
    text-rendering: geometricPrecision;
}}
.export-mode .kpi-label {{line-height:1.28!important;margin-bottom:7px!important;}}
.export-mode .kpi-unit {{line-height:1.32!important;margin-top:7px!important;}}
.export-mode .insight-copy {{gap:10px!important;}}
.export-mode .insight-copy .insight-label {{line-height:1.3!important;letter-spacing:.45px!important;}}
.export-mode .insight-copy b {{
    font-family: Arial, Helvetica, sans-serif !important;
    font-weight: 800 !important;
    line-height:1.3!important;
    letter-spacing:.20px!important;
    word-spacing:1.2px!important;
    overflow-wrap:anywhere!important;
}}
.export-mode .insight-copy .insight-note {{line-height:1.38!important;}}
.export-mode .summary-label {{line-height:1.28!important;letter-spacing:.45px!important;}}
.export-mode .summary-unit {{line-height:1.35!important;word-spacing:1.6px!important;}}
.export-mode .summary-value {{line-height:1.12!important;margin-top:5px!important;margin-bottom:3px!important;}}


/* Final export tuning: vendor name and defect-rate typography */
.export-mode .kpi.top-vendor .kpi-value {{
    font-family: Arial, Helvetica, sans-serif !important;
    font-size: 15px !important;
    font-weight: 700 !important;
    line-height: 1.32 !important;
    letter-spacing: .45px !important;
    word-spacing: 2px !important;
    white-space: normal !important;
    overflow-wrap: normal !important;
    word-break: normal !important;
    margin-top: 1px !important;
}}
.export-mode .kpi.top-vendor .kpi-unit {{
    font-size: 8.5px !important;
    line-height: 1.3 !important;
    margin-top: 7px !important;
    letter-spacing: .25px !important;
    word-spacing: 1.5px !important;
}}
.export-mode .kpi.defect-rate .kpi-value {{
    font-family: Arial, Helvetica, sans-serif !important;
    font-size: 25px !important;
    font-weight: 700 !important;
    line-height: 1.12 !important;
    letter-spacing: .65px !important;
    margin-top: 2px !important;
}}
.export-mode .kpi.defect-rate .kpi-unit {{
    font-family: Arial, Helvetica, sans-serif !important;
    font-size: 8.5px !important;
    font-weight: 600 !important;
    line-height: 1.3 !important;
    letter-spacing: .25px !important;
    margin-top: 7px !important;
}}
.export-mode .summary-item.defect-rate-summary .summary-label {{
    font-family: Arial, Helvetica, sans-serif !important;
    font-size: 8.5px !important;
    font-weight: 700 !important;
    line-height: 1.25 !important;
    letter-spacing: .4px !important;
    margin-bottom: 3px !important;
}}
.export-mode .summary-item.defect-rate-summary .summary-value {{
    font-family: Arial, Helvetica, sans-serif !important;
    font-size: 23px !important;
    font-weight: 700 !important;
    line-height: 1.12 !important;
    letter-spacing: .65px !important;
    margin-top: 2px !important;
    margin-bottom: 4px !important;
}}
.export-mode .summary-item.defect-rate-summary .summary-unit {{
    font-family: Arial, Helvetica, sans-serif !important;
    font-size: 7.5px !important;
    font-weight: 600 !important;
    line-height: 1.3 !important;
    letter-spacing: .2px !important;
    white-space: normal !important;
    max-width: 115px !important;
}}



/* Final export tuning: add clear spacing to dashboard headings */
.export-mode .dash-title {{
    font-family: Arial, Helvetica, sans-serif !important;
    font-weight: 800 !important;
    letter-spacing: 1.25px !important;
    word-spacing: 4px !important;
    line-height: 1.15 !important;
    text-rendering: geometricPrecision;
}}
.export-mode .dash-subtitle {{
    font-family: Arial, Helvetica, sans-serif !important;
    font-weight: 600 !important;
    letter-spacing: .45px !important;
    word-spacing: 1.8px !important;
    line-height: 1.35 !important;
}}
.export-mode .chart-title {{
    font-family: Arial, Helvetica, sans-serif !important;
    font-weight: 800 !important;
    letter-spacing: .75px !important;
    word-spacing: 2.4px !important;
    line-height: 1.25 !important;
    text-rendering: geometricPrecision;
}}
.export-mode .insight-head {{
    font-family: Arial, Helvetica, sans-serif !important;
    font-weight: 800 !important;
    letter-spacing: .75px !important;
    word-spacing: 2.4px !important;
    line-height: 1.35 !important;
    text-rendering: geometricPrecision;
}}

/* ---------- Landscape dashboard / export ---------- */
@media (min-width: 1200px) {{
  .block-container {{max-width:1920px!important; min-width:1500px!important;}}
  .chart-card {{padding:8px 10px 5px;}}
  .insights {{margin:7px 0;padding:11px 13px;min-height:116px;}}
  .summary-strip {{margin-top:4px;padding:7px 5px;}}
  .summary-item {{min-height:70px;padding:4px 7px;}}
}}
.export-mode {{
  width:1920px!important;
  max-width:1920px!important;
  min-width:1920px!important;
  padding:8px 14px 12px!important;
  box-sizing:border-box!important;
}}
.export-mode .chart-card {{padding:7px 9px 5px!important;}}
.export-mode .insights {{margin:6px 0!important;min-height:112px!important;padding:10px 12px!important;}}
.export-mode .summary-strip {{padding:7px 4px!important;margin-top:4px!important;}}
.export-mode .summary-item {{min-height:68px!important;padding:3px 6px!important;}}

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
    "year_month": ["Year-Month", "Year Month", "Month-Year", "Month Year"],
    "date_created": ["Date Created", "Created Date", "Created On"],
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



def parse_date_series(series: pd.Series, *, month_first: bool = False) -> pd.Series:
    """Parse Excel/CSV dates safely.

    When ``month_first=True``, text dates are interpreted using the US format
    M/D/YYYY (or M/D/YYYY HH:MM:SS). Existing datetime values and Excel serial
    numbers are preserved.
    """
    result = pd.Series(pd.NaT, index=series.index, dtype="datetime64[ns]")

    is_dt = series.map(lambda value: isinstance(value, (pd.Timestamp, datetime, date)))
    if is_dt.any():
        result.loc[is_dt] = pd.to_datetime(series.loc[is_dt], errors="coerce")

    remaining = result.isna() & series.notna()
    if not remaining.any():
        return result

    numeric = pd.to_numeric(series.loc[remaining], errors="coerce")
    serial_mask = numeric.between(1, 100000, inclusive="both")
    if serial_mask.any():
        serial_index = numeric.index[serial_mask]
        result.loc[serial_index] = pd.to_datetime(
            numeric.loc[serial_index], unit="D", origin="1899-12-30", errors="coerce"
        )

    remaining = result.isna() & series.notna()
    if remaining.any():
        values = series.loc[remaining].astype(str).str.strip()

        iso_mask = values.str.match(r"^\d{4}[-/]\d{1,2}[-/]\d{1,2}")
        if iso_mask.any():
            idx = values.index[iso_mask]
            result.loc[idx] = pd.to_datetime(
                values.loc[idx], errors="coerce", yearfirst=True
            )

        other_idx = values.index[~iso_mask]
        if len(other_idx):
            # Date Created is exported as M/D/YYYY, optionally with time.
            # month_first=True guarantees 6/5/2026 = June 5, not 6 May.
            result.loc[other_idx] = pd.to_datetime(
                values.loc[other_idx],
                errors="coerce",
                dayfirst=not month_first,
                format="mixed",
            )

    return result

def normalize_year_month(series: pd.Series) -> pd.Series:
    """Normalize an existing Year-Month column to yyyy-mm."""
    raw = series.astype(str).str.strip()
    extracted = raw.str.extract(r"(?P<year>20\d{2})\D*(?P<month>\d{1,2})")
    month_num = pd.to_numeric(extracted["month"], errors="coerce")
    valid = extracted["year"].notna() & month_num.between(1, 12)
    result = pd.Series(pd.NA, index=series.index, dtype="string")
    result.loc[valid] = (
        extracted.loc[valid, "year"].astype(str)
        + "-"
        + month_num.loc[valid].astype(int).astype(str).str.zfill(2)
    )
    return result

def prepare(source: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, str]]:
    cols = {key: find_col(source, aliases) for key, aliases in ALIASES.items()}
    missing = [key for key in ("date", "received", "rejected", "item") if not cols[key]]
    if missing:
        raise ValueError("Thiếu cột bắt buộc: " + ", ".join(missing))

    df = source.copy()
    date_col = cols["date"]
    assert date_col is not None

    # Use Date Created as the reporting date whenever available. The NetSuite
    # export uses the US format M/D/YYYY, so parse it explicitly month-first.
    created_col = cols.get("date_created")
    if created_col and created_col in df.columns:
        df[created_col] = parse_date_series(df[created_col], month_first=True)
        df[date_col] = df[created_col]
    else:
        # Fallback only when Date Created is absent.
        df[date_col] = parse_date_series(df[date_col], month_first=False)

    # Rebuild the reporting month solely from the parsed reporting date.
    # Any pre-existing Year-Month helper is intentionally ignored.
    df["Year-Month"] = df[date_col].dt.strftime("%Y-%m")
    iso_calendar = df[date_col].dt.isocalendar()
    df["Year-Week"] = (
        iso_calendar["year"].astype("Int64").astype(str)
        + "-W"
        + iso_calendar["week"].astype("Int64").astype(str).str.zfill(2)
    )

    # Keep rows with a valid reporting month. A valid date is still needed for
    # daily calculations, but an existing Year-Month column can preserve rows
    # whose raw date text is blank or malformed.
    df = df[df["Year-Month"].notna()].copy()

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


def _wrap_chart_label(text: object, max_chars: int = 22, max_lines: int = 2) -> str:
    """Wrap long chart labels without cutting important vendor/item text."""
    raw = str(text).strip()
    if len(raw) <= max_chars:
        return raw

    # Add sensible break opportunities around punctuation first.
    prepared = re.sub(r"\s+", " ", raw)
    prepared = re.sub(r"(?<=[,./&-])(?=[A-Za-z0-9])", " ", prepared)
    words = prepared.split()

    lines: list[str] = []
    current = ""
    for word in words:
        trial = f"{current} {word}".strip()
        if len(trial) <= max_chars or not current:
            current = trial
        else:
            lines.append(current)
            current = word
            if len(lines) >= max_lines - 1:
                break
    if current and len(lines) < max_lines:
        lines.append(current)

    # A single unbroken company name still needs a safe split.
    if len(lines) == 1 and len(lines[0]) > max_chars:
        value = lines[0]
        lines = [value[:max_chars], value[max_chars:max_chars * 2]]

    return "<br>".join(lines[:max_lines])


def bar_chart(
    series: pd.Series,
    color: str,
    total: float,
    empty_text: str = "No rejected quantity",
    *,
    wrap_labels: bool = False,
) -> go.Figure:
    s = series.head(5).sort_values(ascending=True)
    if s.empty:
        return empty_chart(empty_text, 430)
    labels = [f"{value:,.0f} ({value / total:.2%})" if total else f"{value:,.0f}" for value in s.values]
    original_labels = [str(x) for x in s.index]
    display_labels = [
        _wrap_chart_label(x, max_chars=20, max_lines=2) if wrap_labels else str(x)
        for x in s.index
    ]
    fig = go.Figure(
        go.Bar(
            x=s.values,
            y=original_labels,
            customdata=original_labels,
            orientation="h",
            marker=dict(color=color, line=dict(color="rgba(0,0,0,0.12)", width=1.0)),
            text=labels,
            textposition="outside",
            cliponaxis=False,
            textfont=dict(size=16, color=TEXT, family="Arial Black"),
            hovertemplate="%{customdata}<br>%{x:,.0f} pcs<extra></extra>",
        )
    )
    max_label = max((len(str(x)) for x in original_labels), default=10)
    left_margin = min(340, max(155, (20 if wrap_labels else max_label) * 8 + 35))
    layout(fig, 470, dict(l=left_margin, r=125, t=20, b=64))
    fig.update_layout(showlegend=False, paper_bgcolor="white", plot_bgcolor="white")
    fig.update_xaxes(title=dict(text="PCS", font=dict(size=17, color=TEXT, family="Arial Black")), rangemode="tozero", tickfont=dict(size=14, color=TEXT, family="Arial Black"))
    fig.update_yaxes(
        automargin=True,
        tickfont=dict(size=15 if wrap_labels else 16, color=TEXT, family="Arial Black"),
        showgrid=False,
        tickmode="array" if wrap_labels else "auto",
        tickvals=original_labels if wrap_labels else None,
        ticktext=display_labels if wrap_labels else None,
    )
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
        ticktext = _safe_list(getattr(getattr(fig.layout, "yaxis", None), "ticktext", None))
        labels = [str(x).replace("<br>", "\n") for x in (ticktext if ticktext else horizontal.y)]
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


def _safe_list(value) -> list:
    """Convert Plotly/Pandas/NumPy sequences without boolean evaluation."""
    if value is None:
        return []
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, (pd.Series, pd.Index)):
        return value.tolist()
    try:
        return list(value)
    except TypeError:
        return [value]


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
        labels = [str(x) for x in _safe_list(getattr(pie, "labels", None))]
        values = np.asarray(_safe_list(getattr(pie, "values", None)), dtype=float)
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
        annotations = _safe_list(getattr(fig.layout, "annotations", None))
        if len(annotations) > 0:
            center = _strip_html(annotations[0].text).replace("Total Defect", "\nTotal Defect")
        ax.text(0, 0, center, ha="center", va="center", fontsize=28, fontweight="bold", color=TEXT)
        ax.legend(wedges, labels, loc="center left", bbox_to_anchor=(1.0, 0.5), frameon=False,
                  fontsize=19, handlelength=1.2, labelspacing=1.0)
        ax.axis("equal")
        ax.axis("off")
        mpl_fig.subplots_adjust(left=0.03, right=0.72, top=0.96, bottom=0.04)

    elif horizontal is not None:
        ticktext = _safe_list(getattr(getattr(fig.layout, "yaxis", None), "ticktext", None))
        labels = [str(x).replace("<br>", "\n") for x in (ticktext if ticktext else horizontal.y)]
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
        txt_source = _safe_list(getattr(horizontal, "text", None))
        txt = txt_source if len(txt_source) > 0 else [f"{v:,.0f}" for v in values]
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
        draw.text((M+55, 82), title, font=_dashboard_font(82, True), fill="white")
        draw.text((W-M-55, 105), subtitle, font=_dashboard_font(44, True), fill="#D7E7FF", anchor="ra")
        draw.text((W-M-55, 175), page_no, font=_dashboard_font(38, True), fill="#AFC8EF", anchor="ra")

    # PAGE 1 — Executive summary
    p1, d1 = page()
    add_header(d1, "IQC QUALITY DASHBOARD", f"Reporting month: {report_month}  |  Source: {source}", "PAGE 1 / 2")

    # KPI cards
    kpi_top, kpi_bottom = 285, 690
    gap = 26
    card_w = (W - 2*M - gap*4) // 5
    fill_map = ["#EAF3FF", "#EAF8EE", "#FDECEC", "#FFF3E0", "#F3ECFF"]
    icon_chars = ["R", "A", "X", "%", "V"]
    for i, (label, value, accent) in enumerate(metrics[:5]):
        x1 = M + i*(card_w+gap); x2 = x1+card_w
        _rounded_card(d1, (x1, kpi_top, x2, kpi_bottom), radius=28, fill="white")
        d1.ellipse((x1+25, kpi_top+115, x1+155, kpi_top+245), fill=fill_map[i])
        d1.text((x1+90, kpi_top+180), icon_chars[i], font=_dashboard_font(58, True), fill=accent, anchor="mm")
        d1.text((x1+178, kpi_top+78), label.upper(), font=_dashboard_font(44, True), fill=TEXT)
        vf = _fit_text(d1, value, card_w-205, 76, 38, True)
        d1.text((x1+178, kpi_top+158), str(value), font=vf, fill=accent)

    # Main charts
    y1, y2 = 735, 1745
    left = (M, y1, 2280, y2)
    right = (2310, y1, W-M, y2)
    for box, title in ((left, figures[0][0]), (right, figures[1][0])):
        _rounded_card(d1, box, radius=28, fill="white")
        bar_w = min(850, box[2]-box[0]-50)
        d1.rounded_rectangle((box[0]+24, box[1]+22, box[0]+bar_w, box[1]+92), radius=13, fill=NAVY)
        d1.text((box[0]+48, box[1]+39), title.upper(), font=_dashboard_font(38, True), fill="white")
    _paste_chart(p1, figures[0][1], (left[0]+30, left[1]+115, left[2]-30, left[3]-30))
    _paste_chart(p1, figures[1][1], (right[0]+30, right[1]+115, right[2]-30, right[3]-30))

    # Insights as four readable cards
    insight_top, insight_bottom = 1795, 2395
    d1.rounded_rectangle((M, insight_top, W-M, insight_bottom), radius=30, fill="#FFF4C8", outline="#EDBE34", width=3)
    title_w = 510
    d1.rounded_rectangle((M, insight_top, M+title_w, insight_bottom), radius=30, fill="#FFBF1A")
    d1.text((M+70, insight_top+155), "KEY QUALITY", font=_dashboard_font(44, True), fill=NAVY_DARK)
    d1.text((M+70, insight_top+220), "INSIGHTS", font=_dashboard_font(58, True), fill=NAVY_DARK)
    d1.text((M+255, insight_top+370), "!", font=_dashboard_font(90, True), fill="white", anchor="mm")
    available = W-M-(M+title_w)-40
    iw = available // 4
    for i, insight in enumerate(insights[:4]):
        x1 = M+title_w+20+i*iw
        if i:
            d1.line((x1, insight_top+45, x1, insight_bottom-45), fill="#D2B45D", width=3)
        font = _dashboard_font(34, True)
        lines = _wrap_lines(d1, insight, font, iw-50, max_lines=7)
        d1.multiline_text((x1+24, insight_top+95), "\n".join(lines), font=font, fill=TEXT, spacing=22)

    # PAGE 2 — Detailed rankings
    p2, d2 = page()
    add_header(d2, "IQC QUALITY DASHBOARD — TOP 5 ANALYSIS", f"Reporting month: {report_month}", "PAGE 2 / 2")
    row_boxes = [(M, 300, W-M, 930), (M, 970, W-M, 1600), (M, 1640, W-M, 2270)]
    for (title, fig), box in zip(figures[2:5], row_boxes):
        _rounded_card(d2, box, radius=28, fill="white")
        d2.rounded_rectangle((box[0]+24, box[1]+22, box[0]+910, box[1]+92), radius=13, fill=NAVY)
        d2.text((box[0]+48, box[1]+39), title.upper(), font=_dashboard_font(38, True), fill="white")
        _paste_chart(p2, fig, (box[0]+35, box[1]+115, box[2]-35, box[3]-30))

    # Summary footer on page 2
    fy1, fy2 = 2310, 2425
    d2.rounded_rectangle((M, fy1, W-M, fy2), radius=22, fill=NAVY_DARK)
    sw = (W-2*M) // max(1, len(footer_metrics))
    for i, (label, value, accent) in enumerate(footer_metrics):
        x1=M+i*sw; x2=x1+sw
        if i:
            d2.line((x1, fy1+18, x1, fy2-18), fill="#4B6994", width=2)
        d2.text(((x1+x2)//2, fy1+22), label.upper(), font=_dashboard_font(27, True), fill="#EAF1FF", anchor="ma")
        vf=_fit_text(d2, value, sw-28, 42, 28, True)
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
st.markdown('<div id="dashboard-capture-start"></div>', unsafe_allow_html=True)

with st.container(key="topbar"):
    title_col, month_col, week_col, vendor_col, item_col = st.columns([3.35, .72, .72, .72, .72], gap="small")
    with title_col:
        st.markdown(
            '<div class="dash-title"><span class="dash-title-icon">📋</span>IQC QUALITY DASHBOARD</div>'
            '<div class="dash-subtitle">Incoming Quality Control · Interactive management report</div>',
            unsafe_allow_html=True,
        )

    # Data is loaded before filters below. Placeholders are created here and filled later.
    month_placeholder = month_col.empty()
    week_placeholder = week_col.empty()
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
    month = st.selectbox("Month", month_options, index=1 if months else 0, key="month_filter")

month_df = df.copy() if month == "All" else df[df["Year-Month"] == month].copy()

weeks = sorted(month_df["Year-Week"].dropna().unique(), reverse=True)
week_options = ["(All)"] + weeks
with week_placeholder.container():
    week = st.selectbox("Week", week_options, key="week_filter")

week_df = month_df.copy() if week == "(All)" else month_df[month_df["Year-Week"] == week].copy()

vendor_options = ["(All)"] + sorted(x for x in week_df[c["vendor"]].unique() if x != "(Blank)")
with vendor_placeholder.container():
    vendor = st.selectbox("Vendor", vendor_options, key="vendor_filter")

item_options = ["(All)"] + sorted(x for x in week_df[c["item"]].unique() if x != "(Blank)")
with item_placeholder.container():
    item = st.selectbox("Item", item_options, key="item_filter")

filtered = week_df.copy()
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

vendor_rej = filtered[filtered[c["vendor"]] != "(Blank)"].groupby(c["vendor"], dropna=False)[c["rejected"]].sum().sort_values(ascending=False)
vendor_rej = vendor_rej[vendor_rej > 0].head(5)
item_rej = filtered[filtered[c["item"]] != "(Blank)"].groupby(c["item"], dropna=False)[c["rejected"]].sum().sort_values(ascending=False)
item_rej = item_rej[item_rej > 0].head(5)
defect_rej = filtered[filtered[c["defect"]] != "(Blank)"].groupby(c["defect"], dropna=False)[c["rejected"]].sum().sort_values(ascending=False)
defect_rej = defect_rej[defect_rej > 0].head(5)
line_rej = filtered[filtered[c["location"]] != "(Blank)"].groupby(c["location"], dropna=False)[c["rejected"]].sum().sort_values(ascending=False)
line_rej = line_rej[line_rej > 0]
daily_rej = filtered.groupby(filtered[c["date"]].dt.date)[c["rejected"]].sum().sort_index()

top_line = str(line_rej.index[0]) if len(line_rej) else "-"
top_line_qty = float(line_rej.iloc[0]) if len(line_rej) else 0.0
top_vendor = str(vendor_rej.index[0]) if len(vendor_rej) else "0"
top_vendor_qty = float(vendor_rej.iloc[0]) if len(vendor_rej) else 0.0
top_item = str(item_rej.index[0]) if len(item_rej) else "0"
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
def beautify_company_name(name: str) -> str:
    """Make compact supplier names easier to read in KPI/export images."""
    text = str(name).strip()
    if not text or text in {"-", "(Blank)"}:
        return "0"

    # Normalize punctuation spacing.
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"\s*,\s*", ", ", text)
    text = re.sub(r"\s*\.\s*", ". ", text)
    text = re.sub(r"\bCO\.?,?\s*LTD\.?\b", "CO., LTD", text, flags=re.I)

    # Common supplier name in the current IQC data source.
    compact = re.sub(r"[^A-Z0-9]", "", text.upper())
    if compact.startswith("VANDONGPHAT"):
        suffix = "CO., LTD" if "COLTD" in compact else ""
        text = "VAN DONG PHAT" + (f" {suffix}" if suffix else "")

    return text.strip()


def display_wrapped_name(name: str, line_chars: int = 14, max_lines: int = 2) -> str:
    """Wrap long vendor/item values into at most two readable HTML lines."""
    text = beautify_company_name(name)
    if text == "0":
        return "0"

    escaped = safe(text)
    words = escaped.split()
    lines: list[str] = []
    current = ""

    for word in words:
        candidate = f"{current} {word}".strip()
        if current and len(candidate) > line_chars:
            lines.append(current)
            current = word
        else:
            current = candidate
        if len(lines) >= max_lines - 1:
            break

    if current and len(lines) < max_lines:
        lines.append(current)

    # Put company suffix on the second line when possible.
    if len(lines) == 1 and " CO., LTD" in escaped:
        base, suffix = escaped.split(" CO., LTD", 1)
        lines = [base, "CO., LTD"]

    shown = "<br>".join(lines[:max_lines])
    visible = " ".join(lines[:max_lines])
    if len(visible.replace(" ", "")) < len(escaped.replace(" ", "")):
        shown += "…"
    return shown

kpis = [
    ("📋", "TOTAL DEFECT", number(rejected), "PCS", RED),
    ("📦", "OUTPUT", number(received), "PCS", NAVY),
    ("✓", "DEFECT RATE", pct(reject_rate), "Rejected / Output", RED),
    ("🏢", "TOP VENDOR", display_wrapped_name(top_vendor), f"{number(top_vendor_qty)} rejected pcs", NAVY),
    ("📦", "TOP DEFECTIVE ITEM", display_wrapped_name(top_item), f"{number(top_item_qty)} rejected pcs", NAVY),
]
kpi_html = '<div class="kpi-row">'
for icon, label, value, unit, color in kpis:
    class_map = {
        "DEFECT RATE": " defect-rate",
        "TOP VENDOR": " top-vendor",
        "TOP DEFECTIVE ITEM": " top-item",
    }
    extra_class = class_map.get(label, "")
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
    # The trend chart changes granularity with the selected filters:
    # All months -> monthly; one month -> weekly; one week -> daily.
    trend_source = df.copy()
    if vendor != "(All)":
        trend_source = trend_source[trend_source[c["vendor"]] == vendor]
    if item != "(All)":
        trend_source = trend_source[trend_source[c["item"]] == item]

    if week != "(All)":
        trend_source = trend_source[trend_source["Year-Week"] == week]
        trend = (
            trend_source.groupby(trend_source[c["date"]].dt.date)
            .agg(Output=(c["received"], "sum"), Defect=(c["rejected"], "sum"))
            .sort_index()
        )
        trend["Label"] = [pd.Timestamp(x).strftime("%d %b") for x in trend.index]
        trend_title = f"DAILY PERFORMANCE — {week}"
        x_axis_title = "Day"
    elif month != "All":
        trend_source = trend_source[trend_source["Year-Month"] == month]
        trend = (
            trend_source.groupby("Year-Week")
            .agg(Output=(c["received"], "sum"), Defect=(c["rejected"], "sum"))
            .sort_index()
        )
        trend["Label"] = trend.index.astype(str)
        trend_title = f"WEEKLY PERFORMANCE — {pd.Period(month, freq='M').strftime('%b %Y')}"
        x_axis_title = "Week"
    else:
        trend = (
            trend_source.groupby("Year-Month")
            .agg(Output=(c["received"], "sum"), Defect=(c["rejected"], "sum"))
            .sort_index()
        )
        trend = trend.tail(7)
        trend["Label"] = [pd.Period(x, freq="M").strftime("%b %Y") for x in trend.index]
        trend_title = "MONTH-OVER-MONTH PERFORMANCE"
        x_axis_title = "Month"

    trend = trend[(trend["Output"] > 0) | (trend["Defect"] > 0)].copy()
    trend["Defect Rate"] = (trend["Defect"] / trend["Output"].replace(0, pd.NA) * 100).fillna(0)

    st.markdown(f'<div class="chart-card"><div class="chart-title">{trend_title}</div>', unsafe_allow_html=True)
    monthly = trend
    month_fig = go.Figure()
    month_fig.add_bar(
        x=monthly["Label"],
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
        x=monthly["Label"],
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
            x=monthly["Label"],
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
    month_fig.update_xaxes(type="category", categoryorder="array", categoryarray=list(monthly["Label"]), tickfont=dict(size=17, color=TEXT, family="Arial Black"), tickangle=0, title=dict(text=x_axis_title, font=dict(size=18, color=TEXT, family="Arial Black")))
    st.plotly_chart(month_fig, use_container_width=True, config={"displayModeBar": False, "displaylogo": False, "responsive": True})
    st.markdown('</div>', unsafe_allow_html=True)

# Top item details shown inside the Disposition card.
def _top_item_by_quantity(data: pd.DataFrame, quantity_col: str) -> tuple[str, float]:
    ranked = (
        data[data[c["item"]] != "(Blank)"]
        .groupby(c["item"], dropna=False)[quantity_col]
        .sum()
        .sort_values(ascending=False)
    )
    ranked = ranked[ranked > 0]
    if ranked.empty:
        return "0", 0.0
    return str(ranked.index[0]), float(ranked.iloc[0])


top_accepted_item, top_accepted_item_qty = _top_item_by_quantity(filtered, c["approved"])
top_rejected_item, top_rejected_item_qty = _top_item_by_quantity(filtered, c["rejected"])
top_special_item, top_special_item_qty = _top_item_by_quantity(filtered, c["special"])


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
            x=.34, y=.50, showarrow=False, font=dict(size=26, color=TEXT, family="Arial Black")
        )

        detail_rows = [
            ("TOP ACCEPTED ITEM", top_accepted_item, top_accepted_item_qty, GREEN, .70),
            ("TOP REJECTED ITEM", top_rejected_item, top_rejected_item_qty, RED, .46),
            ("TOP SPECIAL RELEASE", top_special_item, top_special_item_qty, ORANGE, .22),
        ]
        for detail_label, detail_item, detail_qty, detail_color, detail_y in detail_rows:
            item_display = _wrap_chart_label(detail_item, max_chars=20, max_lines=2)
            donut.add_annotation(
                x=.735, y=detail_y, xref="paper", yref="paper",
                xanchor="left", yanchor="middle", align="left", showarrow=False,
                text=(
                    f"<span style='font-size:11px'><b>{detail_label}</b></span><br>"
                    f"<span style='color:{detail_color};font-size:14px'><b>{item_display}</b></span><br>"
                    f"<span style='font-size:11px'>{detail_qty:,.0f} pcs</span>"
                ),
                font=dict(size=12, color=TEXT, family="Arial"),
            )

        layout(donut, 500, dict(l=18, r=20, t=45, b=35))
        donut.update_layout(
            legend=dict(
                orientation="h", y=1.02, x=.02, xanchor="left",
                font=dict(size=11, color=TEXT, family="Arial Black"),
            ),
            margin=dict(l=18, r=18, t=65, b=35),
        )
        donut.update_traces(domain=dict(x=[.01, .66], y=[.03, .92]))
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
# RANKED CHARTS — INDEPENDENT MONTH / WEEK FILTERS
# ============================================================
# These two filters only control the three Top-5 charts below. They do not
# change the KPI cards, Daily Performance chart, Disposition, or Insights.
rank_filter_left, rank_filter_month_col, rank_filter_week_col = st.columns(
    [3.2, 1.0, 1.0], gap="small"
)
with rank_filter_left:
    st.markdown(
        '<div style="height:100%;display:flex;align-items:end;padding:0 0 8px 3px;'
        'font-size:14px;font-weight:800;color:#073B7A;letter-spacing:.25px">'
        'TOP 5 CHART FILTER</div>',
        unsafe_allow_html=True,
    )

rank_month_options = ["All"] + months
rank_month_default = month if month in rank_month_options else "All"
with rank_filter_month_col:
    rank_month = st.selectbox(
        "Month",
        rank_month_options,
        index=rank_month_options.index(rank_month_default),
        key="rank_month_filter",
    )

rank_month_df = df.copy() if rank_month == "All" else df[df["Year-Month"] == rank_month].copy()
rank_week_values = sorted(rank_month_df["Year-Week"].dropna().unique(), reverse=True)
rank_week_options = ["(All)"] + rank_week_values
rank_week_default = week if week in rank_week_options else "(All)"
with rank_filter_week_col:
    rank_week = st.selectbox(
        "Week",
        rank_week_options,
        index=rank_week_options.index(rank_week_default),
        key="rank_week_filter",
    )

rank_filtered = (
    rank_month_df.copy()
    if rank_week == "(All)"
    else rank_month_df[rank_month_df["Year-Week"] == rank_week].copy()
)

# Keep the existing Vendor and Item selections active, while Month and Week
# are independently controlled by the two filters immediately above.
if vendor != "(All)":
    rank_filtered = rank_filtered[rank_filtered[c["vendor"]] == vendor]
if item != "(All)":
    rank_filtered = rank_filtered[rank_filtered[c["item"]] == item]

rank_rejected = float(rank_filtered[c["rejected"]].sum())
rank_vendor_rej = (
    rank_filtered[rank_filtered[c["vendor"]] != "(Blank)"]
    .groupby(c["vendor"], dropna=False)[c["rejected"]]
    .sum()
    .sort_values(ascending=False)
)
rank_item_rej = (
    rank_filtered[rank_filtered[c["item"]] != "(Blank)"]
    .groupby(c["item"], dropna=False)[c["rejected"]]
    .sum()
    .sort_values(ascending=False)
)
rank_defect_rej = (
    rank_filtered[rank_filtered[c["defect"]] != "(Blank)"]
    .groupby(c["defect"], dropna=False)[c["rejected"]]
    .sum()
    .sort_values(ascending=False)
)

# Top items by Special Released quantity, controlled by the same Month/Week
# filters as the three rejected-quantity charts.
rank_special_total = float(rank_filtered[c["special"]].sum())
rank_item_special = (
    rank_filtered[rank_filtered[c["item"]] != "(Blank)"]
    .groupby(c["item"], dropna=False)[c["special"]]
    .sum()
    .sort_values(ascending=False)
)

# Do not display zero-quantity categories. Empty charts keep their title and
# show a clean white body with a short no-data message.
rank_vendor_rej = rank_vendor_rej[rank_vendor_rej > 0].head(5)
rank_item_rej = rank_item_rej[rank_item_rej > 0].head(5)
rank_defect_rej = rank_defect_rej[rank_defect_rej > 0].head(5)
rank_item_special = rank_item_special[rank_item_special > 0].head(5)

rank_cols = st.columns(4, gap="small")
rank_specs = [
    (rank_cols[0], "TOP VENDORS BY REJECTED QTY", rank_vendor_rej, "#1457B8", rank_rejected, "No rejected quantity"),
    (rank_cols[1], "TOP ITEMS BY REJECTED QTY", rank_item_rej, "#2474D8", rank_rejected, "No rejected quantity"),
    (rank_cols[2], "TOP DEFECTS BY REJECTED QTY", rank_defect_rej, RED, rank_rejected, "No rejected quantity"),
    (rank_cols[3], "TOP ITEMS BY SPECIAL RELEASE", rank_item_special, ORANGE, rank_special_total, "No special released quantity"),
]
rank_figures: list[tuple[str, go.Figure]] = []
for rank_index, (column, title, series, color, chart_total, empty_text) in enumerate(rank_specs):
    rank_fig = bar_chart(
        series,
        color,
        chart_total,
        empty_text,
        wrap_labels=(title == "TOP VENDORS BY REJECTED QTY"),
    )
    rank_figures.append((title, rank_fig))
    with column:
        st.markdown(f'<div class="chart-card"><div class="chart-title">{title}</div>', unsafe_allow_html=True)
        st.plotly_chart(
            rank_fig,
            use_container_width=True,
            config={"displayModeBar": False, "displaylogo": False, "responsive": True},
            key=f"rank_chart_{rank_index}",
        )
        st.markdown('</div>', unsafe_allow_html=True)

# ============================================================
# FOOTER SUMMARY — FOLLOWS THE TOP-5 MONTH / WEEK FILTERS
# ============================================================
# The seven footer KPIs use exactly the same filtered dataset as the four
# ranking charts above, including Month, Week, Vendor and Item selections.
footer_received = float(rank_filtered[c["received"]].sum())
footer_approved = float(rank_filtered[c["approved"]].sum())
footer_rejected = float(rank_filtered[c["rejected"]].sum())
footer_special = float(rank_filtered[c["special"]].sum())
footer_reject_rate = footer_rejected / footer_received if footer_received else 0.0
footer_accepted_rate = footer_approved / footer_received if footer_received else 0.0

footer_counter_count = rank_filtered[c["counter"]].replace("(Blank)", pd.NA).nunique()
if footer_counter_count == 0:
    footer_counter_count = rank_filtered[c["vendor"]].replace("(Blank)", pd.NA).nunique()

footer_supplier_ppm = (footer_rejected / footer_received * 1_000_000) if footer_received else 0.0

summary = [
    ("📦", "TOTAL RECEIVED", number(footer_received), "PCS", ""),
    ("✓", "TOTAL ACCEPTED", number(footer_approved), pct(footer_accepted_rate), "accepted"),
    ("✕", "TOTAL REJECTED", number(footer_rejected), pct(footer_reject_rate), "rejected"),
    ("SR", "TOTAL SPECIAL RELEASED", number(footer_special), "PCS", "special"),
    ("%", "DEFECT RATE", pct(footer_reject_rate), "Rejected / Received", "rate"),
    ("👤", "TOTAL COUNTER", number(footer_counter_count), "People / Suppliers", ""),
    ("PPM", "SUPPLIER PPM", number(round(footer_supplier_ppm)), "Rejected / Received × 1,000,000", "rate"),
]
footer_html = '<div class="summary-strip">'
for icon, label, value, unit, value_class in summary:
    summary_extra_class = " defect-rate-summary" if label == "DEFECT RATE" else ""
    footer_html += (
        f'<div class="summary-item{summary_extra_class}">'
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
# EXPORT DATA
# ============================================================
export_data_col, export_note_col = st.columns([1.1, 4.9], gap="small")
with export_data_col:
    st.download_button(
        "⬇️ EXPORT DATA",
        filtered.to_csv(index=False).encode("utf-8-sig"),
        file_name=f"IQC_filtered_{month}_{week}.csv",
        mime="text/csv",
        use_container_width=True,
        key="export_data_main",
    )
with export_note_col:
    st.markdown(
        '<div style="height:42px;display:flex;align-items:center;padding:0 14px;'
        'background:#FFFFFF;border:1px solid #C8D3E1;border-radius:8px;'
        'font-size:13px;font-weight:700;color:#425466">'
        'Xuất toàn bộ dữ liệu đang được lọc trên dashboard.</div>',
        unsafe_allow_html=True,
    )

# ============================================================
# ONE-BUTTON FULL DASHBOARD SCREENSHOT EXPORT
# ============================================================
# Capture the actual browser-rendered dashboard so the exported image keeps
# exactly the same fonts, colors, spacing and chart layout as the web page.
st.markdown('<div id="dashboard-capture-end"></div>', unsafe_allow_html=True)

st.markdown(
    '<div style="margin-top:18px;padding:14px 18px;border:1px solid #C8D3E1;border-radius:12px;'
    'background:#FFFFFF;box-shadow:0 4px 14px rgba(15,40,80,.08)">'
    '<div style="font-size:20px;font-weight:900;color:#062B63;margin-bottom:4px">⬇️ EXPORT FULL REPORT</div>'
    '<div style="font-size:13px;font-weight:700;color:#425466">Xuất dashboard thành ảnh PNG khổ ngang Full HD 1920 × 1080, giữ đúng tỷ lệ chữ và biểu đồ.</div>'
    '</div>',
    unsafe_allow_html=True,
)

components.html(
    """
    <script src="https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js"></script>
    <style>
      html, body { margin:0; padding:0; background:transparent; font-family:Arial,Helvetica,sans-serif; }
      .export-wrap { padding:8px 0 2px; }
      .export-btn {
        width:100%; height:48px; border:0; border-radius:8px;
        background:#073B7A; color:#fff; font-size:16px; font-weight:900;
        cursor:pointer; box-shadow:0 3px 10px rgba(7,59,122,.22);
      }
      .export-btn:hover { background:#0A56B5; }
      .export-btn:disabled { opacity:.65; cursor:wait; }
      #status { margin-top:7px; color:#425466; font-size:12px; font-weight:700; text-align:center; }
    </style>
    <div class="export-wrap">
      <button id="exportBtn" class="export-btn">⬇️ TẢI TOÀN BỘ DASHBOARD DẠNG HÌNH ẢNH</button>
      <div id="status">Ảnh sẽ được xuất theo khổ ngang Full HD 1920 × 1080 và không làm nén chữ.</div>
    </div>
    <script>
    const btn = document.getElementById('exportBtn');
    const status = document.getElementById('status');

    function safeName() {
      const now = new Date();
      const p = n => String(n).padStart(2,'0');
      return `IQC_Quality_Dashboard_${now.getFullYear()}${p(now.getMonth()+1)}${p(now.getDate())}_${p(now.getHours())}${p(now.getMinutes())}.png`;
    }

    btn.addEventListener('click', async () => {
      btn.disabled = true;
      btn.textContent = '⏳ ĐANG CHỤP DASHBOARD...';
      status.textContent = 'Vui lòng chờ vài giây, hệ thống đang tạo ảnh chất lượng cao.';
      try {
        const doc = window.parent.document;
        const start = doc.getElementById('dashboard-capture-start');
        const end = doc.getElementById('dashboard-capture-end');
        if (!start || !end) throw new Error('Không tìm thấy vùng dashboard cần chụp.');

        const container = start.closest('.block-container') || doc.querySelector('.block-container');
        if (!container) throw new Error('Không tìm thấy vùng nội dung Streamlit.');

        container.classList.add('export-mode');
        if (doc.fonts && doc.fonts.ready) {
          await doc.fonts.ready;
        }
        await new Promise(resolve => setTimeout(resolve, 1200));

        const containerRect = container.getBoundingClientRect();
        const startRect = start.getBoundingClientRect();
        const endRect = end.getBoundingClientRect();
        const startY = Math.max(0, startRect.top - containerRect.top);
        const endY = Math.max(startY + 100, endRect.top - containerRect.top);

        const scale = 2;
        const exportWidth = 1920;
        const exportHeight = 1080;
        const fullCanvas = await html2canvas(container, {
          scale: scale,
          useCORS: true,
          allowTaint: true,
          backgroundColor: '#F2F5FA',
          logging: false,
          scrollX: 0,
          scrollY: -window.parent.scrollY,
          windowWidth: 1920,
          windowHeight: Math.ceil(doc.documentElement.scrollHeight)
        });

        const cropY = Math.round(startY * scale);
        const cropH = Math.round((endY - startY) * scale);
        const cropped = document.createElement('canvas');
        cropped.width = fullCanvas.width;
        cropped.height = cropH;
        const cropCtx = cropped.getContext('2d');
        cropCtx.fillStyle = '#F2F5FA';
        cropCtx.fillRect(0, 0, cropped.width, cropped.height);
        cropCtx.drawImage(fullCanvas, 0, cropY, fullCanvas.width, cropH, 0, 0, fullCanvas.width, cropH);

        // Export to a 1920 x 1080 landscape canvas WITHOUT stretching text.
        // Keep one uniform scale for both width and height, then center the
        // dashboard. This prevents letters, icons and charts from becoming
        // horizontally or vertically compressed.
        const output = document.createElement('canvas');
        output.width = exportWidth * scale;
        output.height = exportHeight * scale;
        const ctx = output.getContext('2d');
        ctx.fillStyle = '#F2F5FA';
        ctx.fillRect(0, 0, output.width, output.height);
        ctx.imageSmoothingEnabled = true;
        ctx.imageSmoothingQuality = 'high';

        const fitScale = Math.min(
          output.width / cropped.width,
          output.height / cropped.height
        );
        const drawWidth = Math.round(cropped.width * fitScale);
        const drawHeight = Math.round(cropped.height * fitScale);
        const drawX = Math.round((output.width - drawWidth) / 2);
        const drawY = Math.round((output.height - drawHeight) / 2);

        ctx.drawImage(
          cropped,
          0, 0, cropped.width, cropped.height,
          drawX, drawY, drawWidth, drawHeight
        );

        output.toBlob(blob => {
          const url = URL.createObjectURL(blob);
          const a = doc.createElement('a');
          a.href = url;
          a.download = safeName();
          doc.body.appendChild(a);
          a.click();
          a.remove();
          setTimeout(() => URL.revokeObjectURL(url), 2000);
          container.classList.remove('export-mode');
          status.textContent = 'Đã tạo ảnh. File đang được tải về máy.';
          btn.disabled = false;
          btn.textContent = '⬇️ TẢI TOÀN BỘ DASHBOARD DẠNG HÌNH ẢNH';
        }, 'image/png', 1.0);
      } catch (err) {
        try {
          const doc = window.parent.document;
          const container = doc.querySelector('.block-container');
          if (container) container.classList.remove('export-mode');
        } catch (_) {}
        status.textContent = 'Không thể tạo ảnh: ' + err.message;
        btn.disabled = false;
        btn.textContent = '⬇️ THỬ XUẤT LẠI DASHBOARD';
      }
    });
    </script>
    """,
    height=88,
    scrolling=False,
)

st.markdown(
    f'<div class="source-note">Source: {safe(source_name)} · Defect Rate = Rejected Qty / Received Qty × 100%</div>',
    unsafe_allow_html=True,
)

with st.expander("🔎 View filtered data"):
    st.dataframe(filtered, use_container_width=True, hide_index=True, height=390)
    st.download_button(
        "Download filtered CSV",
        filtered.to_csv(index=False).encode("utf-8-sig"),
        file_name=f"IQC_filtered_{month}_{week}.csv",
        mime="text/csv",
    )
