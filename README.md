# EnergiX-AI

Energy analytics dashboard and forecasting tools built with Python.

## Description

EnergiX-AI is a modular energy analytics platform that helps teams and researchers explore, forecast, and optimize energy usage. It provides:

- Interactive dashboards for visualizing time series energy data and KPIs.
- Forecasting tools using ML models to predict demand and generation.
- Anomaly detection to flag unusual consumption or sensor readings.
- Real-time data views for streaming/near-real-time metrics.
- Optimization components for scenario analysis and cost/consumption minimization.

The codebase is organized to separate data ingestion, modeling, visualization, and persistence. It includes utilities for synthetic data generation, charting helpers, and integrations with Supabase for storage and simple auth.

Use cases: building operational dashboards, prototyping forecasting models, conducting energy optimization experiments, and monitoring deployments in pilot projects.


Contents
- `app.py` — Streamlit/Dash/FastAPI entry (project root)
- `pages/` — web pages (dashboard, forecasting, realtime, etc.)
- `utils/` — helpers for charts, data generation, ML models
- `database/` — DB and Supabase helpers

Setup
1. Create a Python virtual environment:

```bash
python -m venv .venv
```

2. Activate the environment (Windows PowerShell):

```powershell
.venv\Scripts\Activate.ps1
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

Run
- Run the app (example):

```bash
python app.py
```

Notes
- Add a `.gitignore` if you want to exclude virtualenv files and secrets.
- Update this README with architecture details and deployment instructions.

## Deployment — Streamlit Community Cloud

EnergiX-AI is a Streamlit app and can be deployed directly to Streamlit Community Cloud (share.streamlit.io). Steps:

1. Ensure `requirements.txt` includes `streamlit` and any other dependencies. Install locally to verify.

2. Make sure `app.py` is at the repository root (it is). Commit and push your branch (already pushed to GitHub).

3. Create a Streamlit Community Cloud app:
	- Visit https://share.streamlit.io and sign in with GitHub.
	- Click **New app**, select your repository, branch `main`, and the `app.py` file.
	- Click **Deploy**.

4. Set secrets (environment variables) in the Streamlit app settings for Supabase and any API keys, for example:

```
SUPABASE_URL=<your-supabase-url>
SUPABASE_KEY=<your-supabase-service-role-or-api-key>
```

5. If your app needs additional system packages, add a `packages.txt` file in the repo root listing them.

Notes & troubleshooting:
- The app uses Supabase; ensure your database is provisioned and run the SQL in `database/supabase_setup.sql` if needed.
- Streamlit Cloud runs a persistent container; if you need larger resources or private networking, consider Render, Fly.io, or a Docker-based host.

License
- MIT (add your preferred license file)
