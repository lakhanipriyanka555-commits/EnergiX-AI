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

License
- MIT (add your preferred license file)
