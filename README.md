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


## Deployment

You can deploy EnergiX-AI to cloud environments easily. Since it is a Python Streamlit app, we recommend either **Streamlit Community Cloud** or **Render**.

### 1. Deploying on Render (Web Service)
Render allows you to run Streamlit as a persistent web service (supporting WebSockets).

- **Service Type**: Web Service
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `streamlit run app.py --server.port $PORT --server.address 0.0.0.0`
- **Environment Variables**:
  Add your Supabase credentials in the **Environment** section of your Render dashboard:
  - `supabase__url` = `<your-supabase-url>`
  - `supabase__anon_key` = `<your-supabase-anon-key>`
  - `supabase__service_key` = `<your-supabase-service-key>`
  *(Note: Double underscores `__` represent nested fields in Streamlit secrets management when mapped from environment variables).*

### 2. Deploying on Streamlit Community Cloud (Recommended)
This is the easiest and free way to host Streamlit apps:
1. Push your code to GitHub.
2. Go to [share.streamlit.io](https://share.streamlit.io/) and log in with GitHub.
3. Click **New App**, select your repo `lakhanipriyanka555-commits/EnergiX-AI`, branch `main`, and main file path `app.py`.
4. Open **Advanced Settings** -> **Secrets** and paste the contents of your `.streamlit/secrets.toml`:
   ```toml
   [supabase]
   url = "https://your-project.supabase.co"
   anon_key = "sb_publishable_..."
   service_key = "sb_secret_..."
   ```
5. Click **Deploy**.

## License
- MIT

