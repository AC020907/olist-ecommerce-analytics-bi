# Deploying the web demo (Streamlit Community Cloud)

The demo reads only `demo/data/*.parquet` (< 1 MB) and needs no database or secrets,
so it runs on Streamlit Community Cloud's free tier.

## Steps (one time, ~5 minutes)

1. Sign in at <https://share.streamlit.io> with the GitHub account that owns the repository.
2. **Create app → Deploy a public app from GitHub**.
3. Repository `AC020907/olist-ecommerce-analytics-bi`, branch `main`, main file path `demo/app.py`.
4. **Advanced settings → Python version 3.13**. Dependencies are read from
   `demo/requirements.txt` (the file next to the app takes precedence over the root one).
5. Optional: choose a custom subdomain, e.g. `olist-bi-demo`.
6. Deploy, then open the URL and check: the five tabs render, the month slider and region
   filter update the KPIs, and "How the numbers are built" shows identical SQL and demo values.
7. Add the URL to the top of `README.md` (the `Demo:` line).

Theme settings are in `.streamlit/config.toml` at the repository root.

## Updating the data

```bash
python -m olist_bi build
python -m olist_bi export        # rewrites demo/data/*.parquet and export_metadata.json
pytest tests/test_demo_data.py tests/test_kpi_reconciliation.py
```

Commit and push `demo/data/`; Streamlit Cloud redeploys automatically on push.

## Licensing note

The aggregates derive from the Olist dataset (CC BY-NC-SA 4.0). The public demo is a
non-commercial portfolio piece; do not put it behind a paywall or use it as a paid product.
