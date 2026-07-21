from __future__ import annotations

import io
import os
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Iterable

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(
    page_title="IQC Quality Dashboard",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ----------------------------
# Visual theme
# ----------------------------
NAVY = "#062B63"
NAVY_2 = "#0B4EA2"
BLUE = "#1769D2"
GREEN = "#5DA83B"
RED = "#E43D2F"
ORANGE = "#F59E0B"
YELLOW = "#F7C948"
PURPLE = "#7E3BB2"
TEAL = "#21A6B8"
TEXT = "#102A56"
MUTED = "#637083"
GRID = "#DCE3EC"
BG = "#F5F7FB"

st.markdown(
    f"""
<style>
    .stApp {{background:{BG};}}
    .block-container {{max-width: 1600px; padding: .7rem 1rem 1.5rem;}}
    header[data-testid="stHeader"] {{height:0; background:transparent;}}
    #MainMenu, footer {{visibility:hidden;}}

    .hero {{
        background: linear-gradient(100deg, #041D48 0%, {NAVY} 58%, #0B4EA2 100%);
        color:white; border-radius:13px; padding:15px 22px; margin-bottom:7px;
        display:flex; align-items:center; justify-content:space-between;
        box-shadow:0 7px 22px rgba(5,35,80,.18);
    }}
    .hero-title {{font-size:clamp(22px,2.3vw,38px); font-weight:850; line-height:1.05; letter-spacing:.2px;}}
    .hero-sub {{font-size:13px; color:#D6E6FF; margin-top:5px;}}
    .hero-badge {{font-size:12px; color:#E9F2FF; border:1px solid rgba(255,255,255,.27); border-radius:9px; padding:7px 11px;}}

    .filter-label {{font-size:11px; font-weight:800; color:{TEXT}; margin:0 0 2px;}}
    div[data-testid="stSelectbox"] > div > div {{border-radius:8px; min-height:36px;}}
    div[data-testid="stFileUploader"] section {{border:1px dashed #94A9C4; border-radius:12px; background:white;}}

    .card {{
        background:#fff; border:1px solid #D9E1EB; border-radius:12px; min-height:115px;
        padding:13px 16px; box-shadow:0 3px 10px rgba(18,42,86,.07);
        display:flex; align-items:center; gap:13px;
    }}
    .icon-circle {{
        flex:0 0 58px; width:58px; height:58px; border-radius:50%;
        display:flex; align-items:center; justify-content:center; font-size:27px;
        background:#EEF4FF; color:{NAVY}; border:1px solid #D6E5FF;
    }}
    .k-label {{font-size:11px; font-weight:850; letter-spacing:.25px; color:#17233D;}}
    .k-value {{font-size:clamp(25px,2.2vw,38px); font-weight:900; line-height:1.05; margin-top:6px;}}
    .k-foot {{font-size:11px; font-weight:650; color:{MUTED}; margin-top:4px;}}

    .section {{background:#fff; border:1px solid #D9E1EB; border-radius:13px; padding:9px 11px 5px; box-shadow:0 3px 10px rgba(18,42,86,.055);}}
    .section-title {{display:inline-block; background:{NAVY}; color:#fff; border-radius:7px; padding:6px 18px; font-size:12px; font-weight:850; letter-spacing:.15px; margin:0 0 3px;}}

    .insight-wrap {{background:linear-gradient(90deg,#FFF8DA,#FFF2BB); border:1px solid #F2DA7C; border-radius:12px; padding:10px 12px; margin:7px 0;}}
    .insight-grid {{display:grid; grid-template-columns:1.1fr repeat(4, 1fr); align-items:stretch;}}
    .insight-title {{display:flex; align-items:center; gap:10px; font-size:17px; font-weight:900; color:#17233D; padding:4px 15px 4px 4px;}}
    .bulb {{background:{ORANGE}; color:white; height:45px; width:45px; border-radius:50%; display:flex; align-items:center; justify-content:center; font-size:24px;}}
    .insight {{border-left:1px dashed #98A1AD; padding:4px 13px; font-size:12px; line-height:1.38; color:#1D2636; display:flex; align-items:center;}}
    .insight b {{color:{NAVY};}}

    .footer-strip {{
        margin-top:8px; background:linear-gradient(100deg,#041D48,#073574); color:#fff;
        border-radius:12px; display:grid; grid-template-columns:repeat(6,1fr); padding:9px 5px;
        box-shadow:0 5px 15px rgba(5,35,80,.15);
    }}
    .footer-kpi {{text-align:center; border-right:1px solid rgba(255,255,255,.35); padding:6px 7px;}}
    .footer-kpi:last-child {{border-right:0;}}
    .footer-label {{font-size:10px; font-weight:800; color:#E4EEFF;}}
    .footer-value {{font-size:22px; font-weight:900; margin-top:4px;}}
    .footer-unit {{font-size:10px; color:#D3E2FA;}}

    .empty {{background:#fff; border:1px dashed #AAB8C8; border-radius:14px; padding:38px; text-align:center; color:{MUTED};}}
    .small-note {{font-size:11px; color:{MUTED}; text-align:center; margin-top:5px;}}

    @media (max-width: 950px) {{
        .insight-grid {{grid-template-columns:1fr;}}
        .insight {{border-left:0; border-top:1px dashed #98A1AD;}}
        .footer-strip {{grid-template-columns:repeat(2,1fr);}}
        .footer-kpi {{border-bottom:1px solid rgba(255,255,255,.25);}}
    }}
</style>
""",
    unsafe_allow_html=True,
)

# ----------------------------
# Data loading
# ----------------------------
ALIASES = {
    "date": ["Item Receipt Date", "Receipt Date", "Date", "Inspection Date"],
    "received": ["Quantity Received", "Received Qty", "Total Received", "Received"],
    "approved": ["Quantity Approved (Actual)", "Quantity Approved", "Approved Qty", "Accepted Qty", "Approved"],
    "rejected": ["Quantity Rejected", "Rejected Qty", "Reject Qty", "Rejected", "Defect Qty"],
    "reworked": ["Quantity Reworked", "Reworked Qty", "Rework Qty", "Reworked"],
    "special": ["Quantity Special Released", "Special Released Qty", "Special Released"],
    "quarantine": ["Quantity In Quarantine", "Quarantine Qty", "Quarantine"],
    "to_inspect": ["Quantity To Inspect", "Inspection Qty", "Qty To Inspect"],
    "item": ["Item", "Part Number", "Part No", "Item Code"],
    "vendor": ["Vendor", "Supplier", "Vendor Name", "Supplier Name"],
    "defect": ["Defect", "Defect Type", "Defect Description"],
    "location": ["Location", "Production Line", "Line"],
    "receipt": ["Item Receipt", "Document Number", "Receipt Number"],
}


def _norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", str(s).strip().lower())


def find_col(df: pd.DataFrame, names: Iterable[str]) -> str | None:
    norm_map = {_norm(c): c for c in df.columns}
    for name in names:
        if _norm(name) in norm_map:
            return norm_map[_norm(name)]
    return None


def parse_excel_xml(raw: bytes) -> pd.DataFrame:
    root = ET.fromstring(raw.decode("utf-8", errors="ignore"))
    ns = {"ss": "urn:schemas-microsoft-com:office:spreadsheet"}
    ws = root.find("ss:Worksheet", ns)
    if ws is None:
        raise ValueError("Không tìm thấy Worksheet trong file XML Excel.")
    table = ws.find("ss:Table", ns)
    if table is None:
        raise ValueError("Không tìm thấy Table trong file XML Excel.")
    rows = []
    for row in table.findall("ss:Row", ns):
        values: dict[int, str | None] = {}
        col = 1
        for cell in row.findall("ss:Cell", ns):
            index = cell.attrib.get("{urn:schemas-microsoft-com:office:spreadsheet}Index")
            if index:
                col = int(index)
            data = cell.find("ss:Data", ns)
            values[col] = data.text if data is not None else None
            col += 1
        rows.append(values)
    if not rows:
        return pd.DataFrame()
    max_col = max(max(r.keys(), default=0) for r in rows)
    headers = [rows[0].get(i) or f"Column_{i}" for i in range(1, max_col + 1)]
    return pd.DataFrame([{headers[i - 1]: r.get(i) for i in range(1, max_col + 1)} for r in rows[1:]])


@st.cache_data(show_spinner=False)
def read_uploaded_file(raw: bytes, filename: str) -> pd.DataFrame:
    suffix = Path(filename).suffix.lower()
    if suffix == ".csv":
        for enc in ("utf-8-sig", "utf-8", "latin-1"):
            try:
                return pd.read_csv(io.BytesIO(raw), encoding=enc)
            except UnicodeDecodeError:
                continue
        raise ValueError("Không đọc được mã hóa CSV.")

    if raw.lstrip().startswith(b"<?xml"):
        return parse_excel_xml(raw)

    book = pd.ExcelFile(io.BytesIO(raw))
    preferred = ["DuLieuGoc", "Data_Input", "Input Data", "Data"]
    sheet = next((x for x in preferred if x in book.sheet_names), book.sheet_names[0])
    return pd.read_excel(io.BytesIO(raw), sheet_name=sheet)


def load_default_file() -> tuple[pd.DataFrame | None, str | None]:
    candidates = [
        Path("data/IQC_Data.xlsx"),
        Path("data/IQC_Data.xlsm"),
        Path("data/IQC_Data.xls"),
        Path("data/IQC_Data.csv"),
    ]
    for p in candidates:
        if p.exists():
            return read_uploaded_file(p.read_bytes(), p.name), p.name
    return None, None


def prepare(df: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, str | None]]:
    cols = {k: find_col(df, v) for k, v in ALIASES.items()}
    required = ["date", "received", "rejected", "item"]
    missing = [k for k in required if not cols[k]]
    if missing:
        raise ValueError("Thiếu cột bắt buộc: " + ", ".join(missing))

    out = df.copy()
    out[cols["date"]] = pd.to_datetime(out[cols["date"]], errors="coerce")
    out = out[out[cols["date"]].notna()].copy()
    out["Year-Month"] = out[cols["date"]].dt.strftime("%Y-%m")

    for key in ["received", "approved", "rejected", "reworked", "special", "quarantine", "to_inspect"]:
        c = cols.get(key)
        if c:
            out[c] = pd.to_numeric(out[c], errors="coerce").fillna(0)
        else:
            generated = f"__{key}"
            out[generated] = 0.0
            cols[key] = generated

    for key in ["item", "vendor", "defect", "location", "receipt"]:
        c = cols.get(key)
        if c:
            out[c] = out[c].fillna("(Blank)").astype(str).str.strip().replace("", "(Blank)")
        else:
            generated = f"__{key}"
            out[generated] = "(Blank)"
            cols[key] = generated
    return out, cols


def fmt_num(x: float) -> str:
    return f"{x:,.0f}"


def kpi_card(icon: str, label: str, value: str, foot: str, color: str) -> str:
    return f"""
    <div class="card">
      <div class="icon-circle">{icon}</div>
      <div><div class="k-label">{label}</div><div class="k-value" style="color:{color}">{value}</div><div class="k-foot">{foot}</div></div>
    </div>"""


def blank_chart(message: str) -> go.Figure:
    fig = go.Figure()
    fig.add_annotation(text=message, x=.5, y=.5, showarrow=False, font=dict(size=14, color=MUTED))
    fig.update_xaxes(visible=False); fig.update_yaxes(visible=False)
    fig.update_layout(height=300, margin=dict(l=10,r=10,t=10,b=10), paper_bgcolor="white", plot_bgcolor="white")
    return fig


def common_layout(fig: go.Figure, height: int = 300, margin: dict | None = None) -> go.Figure:
    fig.update_layout(
        height=height,
        margin=margin or dict(l=34, r=18, t=25, b=35),
        paper_bgcolor="white", plot_bgcolor="white",
        font=dict(family="Arial", color=TEXT, size=11),
        hoverlabel=dict(bgcolor="white", font_size=12),
        legend=dict(orientation="h", yanchor="bottom", y=1.01, xanchor="left", x=0),
    )
    fig.update_xaxes(showgrid=False, zeroline=False, linecolor="#BCC8D8")
    fig.update_yaxes(gridcolor=GRID, zeroline=False)
    return fig


# ----------------------------
# Header and data source
# ----------------------------
st.markdown(
    """<div class="hero"><div><div class="hero-title">📋 IQC QUALITY DASHBOARD</div>
    <div class="hero-sub">Incoming Quality Control · Interactive Management Report</div></div>
    <div class="hero-badge">Upload Excel / CSV · Auto Analysis</div></div>""",
    unsafe_allow_html=True,
)

with st.expander("📤 Upload / change data file", expanded=False):
    uploaded = st.file_uploader("Upload IQC file", type=["xlsx", "xlsm", "xls", "csv"], label_visibility="collapsed")
    st.caption("Ưu tiên sheet `DuLieuGoc` hoặc `Data_Input`. File mặc định có thể đặt tại `data/IQC_Data.xlsx` trong GitHub.")

try:
    if uploaded is not None:
        source_df = read_uploaded_file(uploaded.getvalue(), uploaded.name)
        source_name = uploaded.name
    else:
        source_df, source_name = load_default_file()
except Exception as exc:
    st.error(f"Không thể đọc file: {exc}")
    st.stop()

if source_df is None:
    st.markdown("<div class='empty'><h3>Chưa có dữ liệu mặc định</h3><p>Upload file IQC phía trên, hoặc thêm file <b>data/IQC_Data.xlsx</b> vào GitHub để mọi người cùng xem một dữ liệu.</p></div>", unsafe_allow_html=True)
    st.stop()

try:
    df, c = prepare(source_df)
except Exception as exc:
    st.error(str(exc))
    st.write("Các cột hiện có:", list(source_df.columns))
    st.stop()

# ----------------------------
# Filters
# ----------------------------
months = sorted(df["Year-Month"].dropna().unique(), reverse=True)
f1, f2, f3, f4 = st.columns([1.1, 1.1, 1.1, 1.25], gap="small")
with f1:
    month = st.selectbox("Month (Year-Month)", months, index=0)
month_df = df[df["Year-Month"] == month].copy()
with f2:
    vendors = ["(All)"] + sorted(x for x in month_df[c["vendor"]].unique() if x != "(Blank)")
    vendor = st.selectbox("Vendor", vendors)
with f3:
    items = ["(All)"] + sorted(x for x in month_df[c["item"]].unique() if x != "(Blank)")
    item = st.selectbox("Item", items)
with f4:
    locations = ["(All)"] + sorted(x for x in month_df[c["location"]].unique() if x != "(Blank)")
    location = st.selectbox("Location / Line", locations)

filtered = month_df.copy()
if vendor != "(All)": filtered = filtered[filtered[c["vendor"]] == vendor]
if item != "(All)": filtered = filtered[filtered[c["item"]] == item]
if location != "(All)": filtered = filtered[filtered[c["location"]] == location]

# Metrics
received = filtered[c["received"]].sum()
approved = filtered[c["approved"]].sum()
rejected = filtered[c["rejected"]].sum()
reworked = filtered[c["reworked"]].sum()
special = filtered[c["special"]].sum()
quarantine = filtered[c["quarantine"]].sum()
to_inspect = filtered[c["to_inspect"]].sum()
reject_rate = rejected / received if received else 0

vendor_rej = filtered.groupby(c["vendor"], dropna=False)[c["rejected"]].sum().sort_values(ascending=False)
vendor_rej = vendor_rej[vendor_rej > 0]
item_rej = filtered.groupby(c["item"], dropna=False)[c["rejected"]].sum().sort_values(ascending=False)
item_rej = item_rej[item_rej > 0]
defect_rej = filtered.groupby(c["defect"], dropna=False)[c["rejected"]].sum().sort_values(ascending=False)
defect_rej = defect_rej[defect_rej > 0]
daily_rej = filtered.groupby(filtered[c["date"]].dt.date)[c["rejected"]].sum().sort_index()

top_vendor = vendor_rej.index[0] if len(vendor_rej) else "-"
top_item = item_rej.index[0] if len(item_rej) else "-"
top_defect = defect_rej.index[0] if len(defect_rej) else "-"
top_day = daily_rej.idxmax().strftime("%Y-%m-%d") if len(daily_rej) and daily_rej.max() > 0 else "-"

# Top KPI cards
kcols = st.columns(5, gap="small")
contents = [
    ("📦","TOTAL RECEIVED",fmt_num(received),"PCS",BLUE),
    ("✅","APPROVED",fmt_num(approved),"PCS",GREEN),
    ("❌","REJECTED",fmt_num(rejected),"PCS",RED),
    ("%","REJECT RATE",f"{reject_rate:.2%}","Rejected / Received",RED),
    ("🏢","TOP VENDOR",top_vendor,"By rejected qty",NAVY_2),
]
for col, args in zip(kcols, contents):
    col.markdown(kpi_card(*args), unsafe_allow_html=True)

# ----------------------------
# Main charts
# ----------------------------
left, right = st.columns([1.62, 1], gap="small")
with left:
    st.markdown("<div class='section'><div class='section-title'>MONTH-OVER-MONTH PERFORMANCE</div>", unsafe_allow_html=True)
    monthly = df.groupby("Year-Month").agg(
        Received=(c["received"], "sum"), Rejected=(c["rejected"], "sum")
    ).sort_index()
    monthly["Reject Rate"] = (monthly["Rejected"] / monthly["Received"].replace(0, pd.NA) * 100).fillna(0)
    fig = go.Figure()
    fig.add_bar(x=monthly.index, y=monthly["Received"], name="Received", marker_color=NAVY, text=monthly["Received"].map(lambda x:f"{x:,.0f}"), textposition="outside")
    fig.add_bar(x=monthly.index, y=monthly["Rejected"], name="Rejected", marker_color=RED, text=monthly["Rejected"].map(lambda x:f"{x:,.0f}"), textposition="outside")
    fig.add_trace(go.Scatter(x=monthly.index, y=monthly["Reject Rate"], name="Reject Rate", mode="lines+markers+text", text=monthly["Reject Rate"].map(lambda x:f"{x:.2f}%"), textposition="top center", yaxis="y2", line=dict(color=ORANGE,width=2), marker=dict(size=7)))
    common_layout(fig, 320, dict(l=48,r=50,t=35,b=40))
    fig.update_layout(barmode="group", yaxis=dict(title="Quantity", gridcolor=GRID), yaxis2=dict(title="%", overlaying="y", side="right", ticksuffix="%", showgrid=False))
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar":False})
    st.markdown("</div>", unsafe_allow_html=True)

with right:
    st.markdown("<div class='section'><div class='section-title'>DISPOSITION</div>", unsafe_allow_html=True)
    disposition = pd.Series({"Approved":approved,"Rejected":rejected,"Reworked":reworked,"Special Released":special,"Quarantine":quarantine})
    disposition = disposition[disposition > 0]
    if disposition.empty:
        dfig = blank_chart("No disposition data")
    else:
        palette = {"Approved":GREEN,"Rejected":RED,"Reworked":BLUE,"Special Released":ORANGE,"Quarantine":PURPLE}
        dfig = go.Figure(go.Pie(labels=disposition.index, values=disposition.values, hole=.60, marker_colors=[palette[x] for x in disposition.index], textinfo="percent", hovertemplate="%{label}<br>%{value:,.0f} pcs<br>%{percent}<extra></extra>"))
        dfig.add_annotation(text=f"<b>{received:,.0f}</b><br><span style='font-size:11px'>Total Received</span>",x=.5,y=.5,showarrow=False,font=dict(size=20,color=TEXT))
        common_layout(dfig, 320, dict(l=5,r=5,t=30,b=10))
        dfig.update_layout(legend=dict(orientation="v", y=.5, x=1.0, xanchor="right"))
    st.plotly_chart(dfig, use_container_width=True, config={"displayModeBar":False})
    st.markdown("</div>", unsafe_allow_html=True)

# ----------------------------
# Insights
# ----------------------------
top_vendor_qty = vendor_rej.iloc[0] if len(vendor_rej) else 0
top_item_qty = item_rej.iloc[0] if len(item_rej) else 0
top_defect_qty = defect_rej.iloc[0] if len(defect_rej) else 0
month_label = pd.Period(month).strftime("%b %Y")
insights_html = f"""
<div class="insight-wrap"><div class="insight-grid">
<div class="insight-title"><div class="bulb">💡</div><div>KEY QUALITY<br>INSIGHTS</div></div>
<div class="insight"><span><b>{month_label}</b><br>Reject rate: <b>{reject_rate:.2%}</b></span></div>
<div class="insight"><span>Top inspection day:<br><b>{top_day}</b></span></div>
<div class="insight"><span>Top vendor:<br><b>{top_vendor}</b> · {top_vendor_qty:,.0f} pcs</span></div>
<div class="insight"><span>Top item: <b>{top_item}</b><br>Top defect: <b>{top_defect}</b> · {top_defect_qty:,.0f} pcs</span></div>
</div></div>"""
st.markdown(insights_html, unsafe_allow_html=True)

# ----------------------------
# Ranked charts
# ----------------------------
def horizontal_bar(series: pd.Series, color: str, title: str) -> go.Figure:
    s = series.head(7).sort_values(ascending=True)
    if s.empty:
        return blank_chart("No rejected quantity")
    fig = go.Figure(go.Bar(x=s.values, y=s.index, orientation="h", marker_color=color, text=[f"{x:,.0f}" for x in s.values], textposition="outside", cliponaxis=False, hovertemplate="%{y}<br>%{x:,.0f} pcs<extra></extra>"))
    common_layout(fig, 285, dict(l=12,r=38,t=12,b=35))
    fig.update_layout(showlegend=False)
    fig.update_xaxes(title="PCS")
    fig.update_yaxes(tickfont=dict(size=10), automargin=True)
    return fig

r1, r2, r3 = st.columns(3, gap="small")
for col, title, series, color in [
    (r1,"TOP VENDORS BY REJECTED QTY",vendor_rej,NAVY_2),
    (r2,"TOP ITEMS BY REJECTED QTY",item_rej,BLUE),
    (r3,"TOP DEFECTS BY REJECTED QTY",defect_rej,RED),
]:
    with col:
        st.markdown(f"<div class='section'><div class='section-title'>{title}</div>", unsafe_allow_html=True)
        st.plotly_chart(horizontal_bar(series,color,title), use_container_width=True, config={"displayModeBar":False})
        st.markdown("</div>", unsafe_allow_html=True)

# Footer summary
record_count = len(filtered)
vendor_count = filtered[c["vendor"]].replace("(Blank)", pd.NA).nunique()
item_count = filtered[c["item"]].replace("(Blank)", pd.NA).nunique()
footer = [
    ("TOTAL RECORDS", fmt_num(record_count), "Rows"),
    ("TO INSPECT", fmt_num(to_inspect), "PCS"),
    ("APPROVED", fmt_num(approved), f"{approved/received:.2%}" if received else "0%"),
    ("REJECTED", fmt_num(rejected), f"{reject_rate:.2%}"),
    ("VENDORS", fmt_num(vendor_count), "Suppliers"),
    ("ITEMS", fmt_num(item_count), "Part numbers"),
]
footer_html = "<div class='footer-strip'>" + "".join(f"<div class='footer-kpi'><div class='footer-label'>{a}</div><div class='footer-value'>{b}</div><div class='footer-unit'>{d}</div></div>" for a,b,d in footer) + "</div>"
st.markdown(footer_html, unsafe_allow_html=True)
st.markdown(f"<div class='small-note'>Source: {source_name} · Defect Rate = Rejected Qty / Received Qty × 100%</div>", unsafe_allow_html=True)

with st.expander("🔎 View filtered data"):
    st.dataframe(filtered, use_container_width=True, hide_index=True, height=420)
    st.download_button("Download filtered CSV", filtered.to_csv(index=False).encode("utf-8-sig"), file_name=f"IQC_filtered_{month}.csv", mime="text/csv")
