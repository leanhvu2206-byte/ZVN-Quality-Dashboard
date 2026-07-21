from __future__ import annotations

import io
import math
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Iterable

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


APP_TITLE = "ZVN Assembly Defects Dashboard"
REQUIRED_COLUMNS = {
    "Date",
    "Document Number",
    "Production Line",
    "Item",
    "Work Order Group",
    "Total Quantity (Including Rejects)",
    "Defect Type",
    "Quantity",
    "Cost Value (AUD)",
}

PALETTE = {
    "navy": "#062B63",
    "blue": "#1261C9",
    "green": "#178A3A",
    "red": "#D92D20",
    "orange": "#F97316",
    "purple": "#7E22CE",
    "yellow": "#F4B400",
    "cyan": "#0EA5E9",
    "bg": "#F4F7FB",
    "text": "#102A56",
    "muted": "#607089",
}


def parse_spreadsheetml_xls(data: bytes) -> pd.DataFrame:
    """Parse NetSuite/Excel SpreadsheetML XML saved with an .xls extension."""
    root = ET.fromstring(data)
    ns = {"ss": "urn:schemas-microsoft-com:office:spreadsheet"}
    table = root.find(".//ss:Worksheet/ss:Table", ns)
    if table is None:
        raise ValueError("No SpreadsheetML worksheet table was found.")

    parsed_rows: list[dict[int, object]] = []
    max_col = 0
    index_key = "{urn:schemas-microsoft-com:office:spreadsheet}Index"

    for row in table.findall("ss:Row", ns):
        values: dict[int, object] = {}
        col_index = 1
        for cell in row.findall("ss:Cell", ns):
            explicit_index = cell.attrib.get(index_key)
            if explicit_index:
                col_index = int(explicit_index)
            node = cell.find("ss:Data", ns)
            values[col_index] = node.text if node is not None else None
            max_col = max(max_col, col_index)
            col_index += 1
        parsed_rows.append(values)

    if not parsed_rows:
        return pd.DataFrame()

    headers = [parsed_rows[0].get(i) for i in range(1, max_col + 1)]
    records = [
        {headers[i - 1]: row.get(i) for i in range(1, max_col + 1) if headers[i - 1]}
        for row in parsed_rows[1:]
    ]
    return pd.DataFrame(records)


def read_uploaded_file(uploaded_file) -> pd.DataFrame:
    filename = uploaded_file.name.lower()
    raw = uploaded_file.getvalue()

    if filename.endswith(".csv"):
        return pd.read_csv(io.BytesIO(raw))
    if filename.endswith(".xlsx") or filename.endswith(".xlsm"):
        return pd.read_excel(io.BytesIO(raw))
    if filename.endswith(".xls"):
        # NetSuite exports are often XML Spreadsheet 2003 files renamed to .xls.
        if raw.lstrip().startswith(b"<?xml") or b"urn:schemas-microsoft-com:office:spreadsheet" in raw[:5000]:
            return parse_spreadsheetml_xls(raw)
        return pd.read_excel(io.BytesIO(raw))
    raise ValueError("Supported file types: CSV, XLSX, XLSM, and XLS.")


def load_sample() -> pd.DataFrame:
    path = Path(__file__).with_name("sample_input.xls")
    return parse_spreadsheetml_xls(path.read_bytes())


def normalize_data(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [str(c).strip() for c in df.columns]
    missing = sorted(REQUIRED_COLUMNS - set(df.columns))
    if missing:
        raise ValueError("Missing required columns: " + ", ".join(missing))

    date_columns = ["Date", "Date Created"]
    numeric_columns = [
        "Total Quantity (Including Rejects)",
        "Quantity",
        "Cost Value (AUD)",
        "% Defects",
    ]
    text_columns = [
        "Document Number",
        "Production Line",
        "Item",
        "Work Order Group",
        "Defect Type",
    ]

    for col in date_columns:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")
    for col in numeric_columns:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
    for col in text_columns:
        df[col] = df[col].fillna("(Blank)").astype(str).str.strip()

    df = df[df["Date"].notna()].copy()
    df["Year-Month"] = df["Date"].dt.strftime("%Y-%m")
    df["Defect Group"] = df["Defect Type"].str.split(":", n=1).str[0].str.strip()
    return df


def apply_filters(
    df: pd.DataFrame,
    months: list[str],
    lines: list[str],
    groups: list[str],
    items: list[str],
) -> pd.DataFrame:
    filtered = df.copy()
    if months:
        filtered = filtered[filtered["Year-Month"].isin(months)]
    if lines:
        filtered = filtered[filtered["Production Line"].isin(lines)]
    if groups:
        filtered = filtered[filtered["Work Order Group"].isin(groups)]
    if items:
        filtered = filtered[filtered["Item"].isin(items)]
    return filtered


def output_quantity(df: pd.DataFrame) -> float:
    # Output is repeated when one document/item has multiple defect types.
    unique_rows = df.drop_duplicates(["Document Number", "Item"])
    return float(unique_rows["Total Quantity (Including Rejects)"].sum())


def fmt_number(value: float) -> str:
    return f"{value:,.0f}"


def kpi_card(icon: str, label: str, value: str, accent: str, subtitle: str = "") -> str:
    return f"""
    <div class="kpi-card" style="border-top:4px solid {accent}">
      <div class="kpi-icon" style="color:{accent}">{icon}</div>
      <div class="kpi-content">
        <div class="kpi-label">{label}</div>
        <div class="kpi-value" style="color:{accent}">{value}</div>
        <div class="kpi-subtitle">{subtitle}</div>
      </div>
    </div>
    """


def style_chart(fig: go.Figure, height: int = 370) -> go.Figure:
    fig.update_layout(
        height=height,
        margin=dict(l=20, r=20, t=55, b=30),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, Segoe UI, Arial", color=PALETTE["text"]),
        title_font=dict(size=18, color=PALETTE["navy"]),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        hoverlabel=dict(bgcolor="white", font_size=13),
    )
    fig.update_xaxes(showgrid=False, zeroline=False)
    fig.update_yaxes(gridcolor="#E5EAF1", zeroline=False)
    return fig


def horizontal_bar(data: pd.Series, title: str, color: str, height: int = 360) -> go.Figure:
    frame = data.sort_values(ascending=True).reset_index()
    frame.columns = ["Category", "Quantity"]
    fig = px.bar(
        frame,
        x="Quantity",
        y="Category",
        orientation="h",
        text="Quantity",
        color_discrete_sequence=[color],
        title=title,
    )
    fig.update_traces(texttemplate="%{text:,.0f}", textposition="outside", cliponaxis=False)
    fig.update_yaxes(title=None, tickfont=dict(size=11))
    fig.update_xaxes(title="Defect quantity")
    return style_chart(fig, height)


st.set_page_config(page_title=APP_TITLE, page_icon="📊", layout="wide")
st.markdown(
    f"""
    <style>
      .stApp {{ background: {PALETTE['bg']}; }}
      .block-container {{ max-width: 1650px; padding-top: 1.1rem; padding-bottom: 2rem; }}
      .hero {{
        background: linear-gradient(135deg, {PALETTE['navy']} 0%, #0A438C 100%);
        border-radius: 18px; padding: 24px 30px; color: white; margin-bottom: 18px;
        box-shadow: 0 10px 28px rgba(6,43,99,.20);
      }}
      .hero h1 {{ margin: 0; font-size: 34px; letter-spacing: .4px; }}
      .hero p {{ margin: 6px 0 0; color: #DCEAFF; font-size: 15px; }}
      .kpi-card {{
        background:white; border-radius:16px; padding:18px; min-height:128px;
        display:flex; align-items:center; gap:14px; box-shadow:0 5px 18px rgba(15,42,86,.08);
        border:1px solid #E4EAF2;
      }}
      .kpi-icon {{ font-size:36px; width:48px; text-align:center; }}
      .kpi-label {{ color:#607089; font-size:12px; font-weight:800; letter-spacing:.5px; }}
      .kpi-value {{ font-size:31px; font-weight:850; margin-top:3px; line-height:1.1; }}
      .kpi-subtitle {{ color:#7A879A; font-size:11px; margin-top:5px; }}
      .insight-box {{
        background:linear-gradient(90deg,#FFF7D8,#FFFDF4); border:1px solid #F2D479;
        border-radius:16px; padding:16px 18px; color:#253858; min-height:90px;
        box-shadow:0 4px 12px rgba(100,78,0,.05);
      }}
      .insight-title {{ font-size:12px; color:#9A6D00; font-weight:800; }}
      .insight-value {{ font-size:15px; font-weight:750; margin-top:7px; }}
      div[data-testid="stPlotlyChart"] {{
        background:white; border:1px solid #E4EAF2; border-radius:16px;
        box-shadow:0 5px 18px rgba(15,42,86,.07); padding:6px;
      }}
      section[data-testid="stSidebar"] {{ background:#EFF4FA; }}
      .section-label {{ color:{PALETTE['navy']}; font-size:18px; font-weight:800; margin:10px 0 8px; }}
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="hero">
      <h1>🛡️ ZVN Assembly Defects Dashboard</h1>
      <p>Upload an Excel or CSV file to explore defects, production output, cost impact, lines, items, and defect trends.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.header("📁 Data source")
    uploaded = st.file_uploader("Upload data", type=["csv", "xlsx", "xlsm", "xls"])
    use_sample = st.toggle("Use bundled sample data", value=uploaded is None)
    st.caption("NetSuite XML .xls exports are supported.")

try:
    if uploaded is not None:
        raw_df = read_uploaded_file(uploaded)
        source_name = uploaded.name
    elif use_sample:
        raw_df = load_sample()
        source_name = "sample_input.xls"
    else:
        st.info("Upload a file or enable sample data to begin.")
        st.stop()
    df = normalize_data(raw_df)
except Exception as exc:
    st.error(f"Could not load the file: {exc}")
    st.stop()

with st.sidebar:
    st.header("🔎 Filters")
    all_months = sorted(df["Year-Month"].dropna().unique(), reverse=True)
    selected_months = st.multiselect("Month", all_months, default=all_months[:1])

    scoped = df[df["Year-Month"].isin(selected_months)] if selected_months else df
    all_lines = sorted(scoped["Production Line"].unique())
    selected_lines = st.multiselect("Production line", all_lines)
    all_groups = sorted(scoped["Work Order Group"].unique())
    selected_groups = st.multiselect("Work order group", all_groups)
    all_items = sorted(scoped["Item"].unique())
    selected_items = st.multiselect("Item", all_items)

    top_n = st.slider("Top N", 3, 15, 5)
    st.divider()
    st.caption(f"Source: {source_name}")
    st.caption(f"Rows loaded: {len(df):,}")

filtered = apply_filters(df, selected_months, selected_lines, selected_groups, selected_items)
if filtered.empty:
    st.warning("No data matches the selected filters.")
    st.stop()

# KPIs
quantity = float(filtered["Quantity"].sum())
output = output_quantity(filtered)
defect_rate = quantity / output if output else 0
line_count = filtered["Production Line"].nunique()
item_count = filtered["Item"].nunique()
doc_count = filtered["Document Number"].nunique()
defect_type_count = filtered["Defect Type"].nunique()
cost = float(filtered["Cost Value (AUD)"].sum())

kpi_cols = st.columns(5)
kpis = [
    ("📋", "TOTAL DEFECT QTY", fmt_number(quantity), PALETTE["blue"], "Rejected / defect pieces"),
    ("🏭", "TOTAL OUTPUT QTY", fmt_number(output), PALETTE["green"], "Unique document + item output"),
    ("%", "DEFECT RATE", f"{defect_rate:.2%}", PALETTE["red"], "Defect qty ÷ output qty"),
    ("⚙️", "PRODUCTION LINES", fmt_number(line_count), PALETTE["purple"], "Lines in current selection"),
    ("📦", "AFFECTED ITEMS", fmt_number(item_count), PALETTE["orange"], "Unique affected part numbers"),
]
for col, values in zip(kpi_cols, kpis):
    col.markdown(kpi_card(*values), unsafe_allow_html=True)

st.write("")

# Primary charts
left, right = st.columns([1.55, 1])
with left:
    daily = filtered.groupby(filtered["Date"].dt.date)["Quantity"].sum().reset_index()
    daily.columns = ["Date", "Defect Qty"]
    fig_daily = px.line(
        daily,
        x="Date",
        y="Defect Qty",
        markers=True,
        text="Defect Qty",
        title="Daily Defect Trend",
        color_discrete_sequence=[PALETTE["blue"]],
    )
    fig_daily.update_traces(textposition="top center", line=dict(width=3), marker=dict(size=8))
    fig_daily.update_xaxes(title=None)
    fig_daily.update_yaxes(title="Defect quantity")
    st.plotly_chart(style_chart(fig_daily, 420), use_container_width=True, config={"displayModeBar": False})

with right:
    group_data = filtered.groupby("Defect Group")["Quantity"].sum().sort_values(ascending=False).reset_index()
    fig_group = px.pie(
        group_data,
        names="Defect Group",
        values="Quantity",
        hole=0.58,
        title="Defect Group Distribution",
        color_discrete_sequence=[PALETTE["blue"], PALETTE["red"], PALETTE["orange"], PALETTE["green"], PALETTE["purple"], PALETTE["cyan"]],
    )
    fig_group.update_traces(textinfo="percent", textfont_size=13)
    fig_group.add_annotation(text=f"<b>{quantity:,.0f}</b><br>Total defects", showarrow=False, font_size=18)
    st.plotly_chart(style_chart(fig_group, 420), use_container_width=True, config={"displayModeBar": False})

# Insights
line_sum = filtered.groupby("Production Line")["Quantity"].sum().sort_values(ascending=False)
item_sum = filtered.groupby("Item")["Quantity"].sum().sort_values(ascending=False)
defect_sum = filtered.groupby("Defect Type")["Quantity"].sum().sort_values(ascending=False)
group_sum = filtered.groupby("Defect Group")["Quantity"].sum().sort_values(ascending=False)
top_day = filtered.groupby(filtered["Date"].dt.date)["Quantity"].sum().idxmax()
top_day_qty = filtered.groupby(filtered["Date"].dt.date)["Quantity"].sum().max()

st.markdown('<div class="section-label">💡 Key Quality Insights</div>', unsafe_allow_html=True)
insight_cols = st.columns(4)
insight_texts = [
    ("DOMINANT GROUP", f"{group_sum.index[0]} accounts for {group_sum.iloc[0] / quantity:.1%} of selected defects."),
    ("HIGHEST-IMPACT LINE", f"{line_sum.index[0]} recorded {line_sum.iloc[0]:,.0f} defects."),
    ("TOP ITEM", f"{item_sum.index[0]} recorded {item_sum.iloc[0]:,.0f} defects."),
    ("TOP INSPECTION DAY", f"{top_day:%d %b %Y}: {top_day_qty:,.0f} defects."),
]
for col, (title, body) in zip(insight_cols, insight_texts):
    col.markdown(
        f'<div class="insight-box"><div class="insight-title">{title}</div><div class="insight-value">{body}</div></div>',
        unsafe_allow_html=True,
    )

st.write("")

# Ranking charts
c1, c2, c3 = st.columns(3)
with c1:
    st.plotly_chart(horizontal_bar(line_sum.head(top_n), "Top Production Lines by Defect Qty", PALETTE["blue"]), use_container_width=True, config={"displayModeBar": False})
with c2:
    st.plotly_chart(horizontal_bar(item_sum.head(top_n), "Top Items by Defect Qty", PALETTE["green"]), use_container_width=True, config={"displayModeBar": False})
with c3:
    st.plotly_chart(horizontal_bar(defect_sum.head(top_n), "Top Defect Types by Qty", PALETTE["red"]), use_container_width=True, config={"displayModeBar": False})

# Monthly performance and cost impact
m1, m2 = st.columns([1.4, 1])
with m1:
    monthly_defect = filtered.groupby("Year-Month")["Quantity"].sum()
    unique_output = (
        filtered.drop_duplicates(["Year-Month", "Document Number", "Item"])
        .groupby("Year-Month")["Total Quantity (Including Rejects)"]
        .sum()
    )
    monthly = pd.concat([monthly_defect.rename("Defect Qty"), unique_output.rename("Output Qty")], axis=1).fillna(0).reset_index()
    monthly["Defect Rate"] = monthly["Defect Qty"] / monthly["Output Qty"].replace(0, math.nan) * 100
    fig_month = go.Figure()
    fig_month.add_bar(x=monthly["Year-Month"], y=monthly["Output Qty"], name="Output Qty", marker_color=PALETTE["navy"])
    fig_month.add_bar(x=monthly["Year-Month"], y=monthly["Defect Qty"], name="Defect Qty", marker_color=PALETTE["red"])
    fig_month.add_trace(go.Scatter(x=monthly["Year-Month"], y=monthly["Defect Rate"], name="Defect Rate %", mode="lines+markers", yaxis="y2", line=dict(color=PALETTE["yellow"], width=3)))
    fig_month.update_layout(
        title="Month-over-Month Performance",
        barmode="group",
        yaxis=dict(title="Quantity"),
        yaxis2=dict(title="Defect rate (%)", overlaying="y", side="right", showgrid=False),
    )
    st.plotly_chart(style_chart(fig_month, 390), use_container_width=True, config={"displayModeBar": False})

with m2:
    cost_by_defect = filtered.groupby("Defect Type")["Cost Value (AUD)"].sum().sort_values(ascending=False).head(top_n)
    fig_cost = horizontal_bar(cost_by_defect, "Top Defects by Cost Impact (AUD)", PALETTE["purple"], 390)
    fig_cost.update_xaxes(title="Cost value (AUD)", tickprefix="$", tickformat=",")
    st.plotly_chart(fig_cost, use_container_width=True, config={"displayModeBar": False})

# Footer metrics
st.markdown('<div class="section-label">📌 Current Selection Summary</div>', unsafe_allow_html=True)
footer_cols = st.columns(4)
footer_values = [
    ("Documents", fmt_number(doc_count)),
    ("Defect types", fmt_number(defect_type_count)),
    ("Highest-impact line", line_sum.index[0]),
    ("Total cost value (AUD)", f"${cost:,.0f}"),
]
for col, (label, value) in zip(footer_cols, footer_values):
    col.metric(label, value)

with st.expander("Preview filtered data"):
    st.dataframe(filtered, use_container_width=True, hide_index=True)
    csv = filtered.to_csv(index=False).encode("utf-8-sig")
    st.download_button("Download filtered CSV", csv, "filtered_defect_data.csv", "text/csv")
