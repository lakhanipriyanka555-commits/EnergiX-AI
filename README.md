# EnergiX-AI

Energy analytics dashboard and forecasting tools built with Python.

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
