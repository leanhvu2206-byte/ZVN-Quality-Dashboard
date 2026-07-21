# IQC Quality Web Dashboard

Streamlit dashboard designed for the IQC file structure with columns such as:

- Item Receipt Date
- Quantity Received
- Quantity Approved (Actual)
- Quantity Rejected
- Quantity Reworked
- Quantity Special Released
- Quantity In Quarantine
- Quantity To Inspect
- Item, Vendor, Defect, Location

## Deploy on Streamlit Community Cloud

1. Upload all project files to your GitHub repository.
2. Optional: add the shared data file as `data/IQC_Data.xlsx`.
3. Open https://share.streamlit.io and deploy `app.py`.
4. Repository: your GitHub repo, Branch: `main`, Main file: `app.py`.

## Important data-sharing note

A public GitHub repository exposes every committed data file. If the IQC data is confidential:

- do not commit the data file; users can upload it in the app, or
- make the repository/app private using an appropriate hosting plan, or
- later connect the app to a protected database/SharePoint/Google Drive.

## Run locally

```bash
python -m pip install -r requirements.txt
python -m streamlit run app.py
```
