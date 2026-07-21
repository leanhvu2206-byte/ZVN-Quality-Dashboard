# ZVN Assembly Defects Web Dashboard

A polished browser-based quality dashboard built with **Python, Streamlit, Pandas, and Plotly**.

## Features

- Upload CSV, XLSX, XLSM, or XLS files.
- Supports NetSuite SpreadsheetML XML files saved with an `.xls` extension.
- Filters by month, production line, work order group, and item.
- Automatic KPI calculation.
- Interactive line, donut, bar, monthly performance, and cost-impact charts.
- Download filtered data as CSV.
- Includes the supplied data file as sample data.

## Run on Windows

1. Install Python 3.10 or newer.
2. Open Command Prompt in this folder.
3. Run:

```bat
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

The dashboard opens automatically in your browser, normally at:

```text
http://localhost:8501
```

## Update data

Open the web page and use **Upload data** in the left sidebar. No code change is required.

## Expected columns

- Date
- Document Number
- Production Line
- Item
- Work Order Group
- Total Quantity (Including Rejects)
- Defect Type
- Quantity
- Cost Value (AUD)

The columns `% Defects` and `Date Created` are optional.
