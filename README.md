# IQC Quality Dashboard V5

Streamlit dashboard for IQC reporting.

## Improvements in V5
- KPI `TOP VENDOR` replaces `TOP LINE`.
- Month-over-Month chart uses clear month labels such as `Apr 2026`, `May 2026`.
- Top 5 Vendor / Item / Defect labels and values use larger bold fonts.
- Each Plotly chart includes a camera button for high-resolution PNG export.
- Export section provides a PDF report and ZIP package of PNG charts.

## Deploy
1. Replace `app.py`, `requirements.txt`, and `.streamlit/config.toml` in GitHub.
2. Commit changes.
3. Streamlit Community Cloud will redeploy automatically.

## Default shared data
Place the shared Excel file at:

`data/IQC_Data.xlsx`

Do not upload confidential data to a public repository.
