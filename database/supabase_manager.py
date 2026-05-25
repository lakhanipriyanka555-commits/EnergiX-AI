"""
EnergiX AI – Supabase Manager (httpx-based)
Calls Supabase REST + Auth APIs directly via httpx.
Compatible with BOTH key formats:
  - Legacy JWT keys:  eyJhbGciOi...
  - New Supabase keys: sb_publishable_ / sb_secret_
"""

import streamlit as st
import pandas as pd
import numpy as np
import random
import httpx
from datetime import datetime, timedelta
from typing import Optional, Tuple

from config import CITIES, DEVICE_TYPES

_TIMEOUT = 15.0
_LONG_TIMEOUT = 60.0


# ══════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════

def _url() -> str:
    return st.secrets["supabase"]["url"]

def _anon_key() -> str:
    return st.secrets["supabase"]["anon_key"]

def _service_key() -> str:
    return st.secrets["supabase"]["service_key"]

def _anon_headers() -> dict:
    k = _anon_key()
    return {
        "apikey":        k,
        "Authorization": f"Bearer {k}",
        "Content-Type":  "application/json",
    }

def _admin_headers() -> dict:
    k = _service_key()
    return {
        "apikey":        k,
        "Authorization": f"Bearer {k}",
        "Content-Type":  "application/json",
    }


# ══════════════════════════════════════════════════════
# CONNECTIVITY CHECK
# ══════════════════════════════════════════════════════

def is_tables_ready() -> bool:
    """Ping the consumers table via REST to confirm setup is complete."""
    try:
        r = httpx.get(
            f"{_url()}/rest/v1/consumers",
            params={"select": "id", "limit": "1"},
            headers=_admin_headers(),
            timeout=_TIMEOUT,
        )
        return r.status_code == 200
    except Exception:
        return False


# ══════════════════════════════════════════════════════
# SUPABASE AUTH  (GoTrue /auth/v1/)
# ══════════════════════════════════════════════════════

def sign_in(email: str, password: str) -> Optional[dict]:
    """
    Sign in via Supabase Auth password flow.
    Returns user dict on success or None on failure.
    Works with both legacy JWT keys and new sb_publishable_ keys.
    """
    try:
        r = httpx.post(
            f"{_url()}/auth/v1/token",
            params={"grant_type": "password"},
            headers=_anon_headers(),
            json={"email": email, "password": password},
            timeout=_TIMEOUT,
        )
        if r.status_code == 200:
            data      = r.json()
            user_data = data.get("user", {})
            meta      = user_data.get("user_metadata") or {}
            return {
                "email":        user_data.get("email", email),
                "name":         meta.get("name", email.split("@")[0].title()),
                "role":         meta.get("role", "Admin"),
                "id":           user_data.get("id", ""),
                "access_token": data.get("access_token", ""),
            }
        else:
            body = r.json()
            st.session_state["auth_error"] = (
                body.get("error_description")
                or body.get("msg")
                or body.get("message")
                or r.text
            )
    except Exception as exc:
        st.session_state["auth_error"] = str(exc)
    return None


def sign_out():
    """Clear auth state."""
    st.session_state.pop("access_token", None)
    st.session_state.pop("auth_error", None)


def ensure_demo_users():
    """
    Create the three demo accounts in Supabase Auth (idempotent).
    Uses the Admin API with the service key.
    Silently ignores 'already exists' errors.
    """
    from config import DEMO_USERS
    for email, info in DEMO_USERS.items():
        try:
            httpx.post(
                f"{_url()}/auth/v1/admin/users",
                headers=_admin_headers(),
                json={
                    "email":         email,
                    "password":      info["password"],
                    "email_confirm": True,
                    "user_metadata": {
                        "name": info["name"],
                        "role": info["role"],
                    },
                },
                timeout=_TIMEOUT,
            )
        except Exception:
            pass  # Already exists — fine


# ══════════════════════════════════════════════════════
# SQL EXECUTION  (via run_sql RPC)
# ══════════════════════════════════════════════════════

def execute_sql(sql: str) -> Tuple[Optional[pd.DataFrame], Optional[str]]:
    """Execute arbitrary SQL via the run_sql() PostgreSQL RPC function."""
    try:
        r = httpx.post(
            f"{_url()}/rest/v1/rpc/run_sql",
            headers=_admin_headers(),
            json={"query": sql},
            timeout=_LONG_TIMEOUT,
        )
        if r.status_code in (200, 201):
            data = r.json()
            if isinstance(data, dict) and "error" in data:
                return None, data["error"]
            if isinstance(data, list):
                return (pd.DataFrame(data) if data else pd.DataFrame()), None
            return pd.DataFrame(), None
        else:
            body = r.json() if r.headers.get("content-type","").startswith("application/json") else {}
            err  = body.get("message") or body.get("hint") or r.text
            return None, f"HTTP {r.status_code}: {err}"
    except Exception as exc:
        return None, str(exc)


def query_df(sql: str, params=()) -> pd.DataFrame:
    """Execute SQL and return a DataFrame (same interface as db_manager.query_df)."""
    df, err = execute_sql(sql)
    if err:
        st.warning(f"⚠️ Query error: {err}")
    return df if df is not None else pd.DataFrame()


# ══════════════════════════════════════════════════════
# KPI SUMMARY
# ══════════════════════════════════════════════════════

def get_kpi_summary() -> dict:
    """Get 24-hour energy KPI aggregates from Supabase."""
    df, _ = execute_sql("""
        SELECT
            SUM(energy_kwh)             AS total_kwh,
            AVG(energy_kwh)             AS avg_kwh,
            MAX(energy_kwh)             AS peak_kwh,
            SUM(cost_usd)               AS total_cost,
            COUNT(DISTINCT consumer_id) AS active_consumers,
            AVG(power_factor)           AS avg_pf
        FROM energy_readings
        WHERE timestamp >= NOW() - INTERVAL '24 hours'
    """)
    if df is not None and not df.empty:
        return df.iloc[0].to_dict()
    return {}


# ══════════════════════════════════════════════════════
# TABLE OPERATIONS  (PostgREST REST API)
# ══════════════════════════════════════════════════════

def get_table(
    table: str,
    limit: int = 200,
    order_col: Optional[str] = None,
    desc: bool = True,
) -> pd.DataFrame:
    """Fetch rows from a Supabase table via REST API."""
    try:
        params: dict = {"select": "*", "limit": str(limit)}
        if order_col:
            params["order"] = f"{order_col}.{'desc' if desc else 'asc'}"
        r = httpx.get(
            f"{_url()}/rest/v1/{table}",
            params=params,
            headers=_admin_headers(),
            timeout=_TIMEOUT,
        )
        if r.status_code == 200:
            data = r.json()
            return pd.DataFrame(data) if data else pd.DataFrame()
        return pd.DataFrame()
    except Exception as exc:
        st.warning(f"⚠️ Table fetch error ({table}): {exc}")
        return pd.DataFrame()


def get_table_count(table: str) -> int:
    """Return exact row count of a table via Content-Range header."""
    try:
        r = httpx.get(
            f"{_url()}/rest/v1/{table}",
            params={"select": "id"},
            headers={
                **_admin_headers(),
                "Prefer": "count=exact",
                "Range":  "0-0",
            },
            timeout=_TIMEOUT,
        )
        # Content-Range: 0-0/TOTAL
        cr    = r.headers.get("content-range", "0-0/0")
        total = cr.split("/")[-1]
        return int(total) if total.isdigit() else 0
    except Exception:
        return 0


def insert_row(table: str, data: dict) -> bool:
    """Insert a single row into a Supabase table."""
    try:
        r = httpx.post(
            f"{_url()}/rest/v1/{table}",
            headers={**_admin_headers(), "Prefer": "return=minimal"},
            json=data,
            timeout=_TIMEOUT,
        )
        return r.status_code in (200, 201)
    except Exception as exc:
        st.error(f"❌ Insert error ({table}): {exc}")
        return False


def _batch_insert(table: str, records: list, batch_size: int = 400):
    """Batch-insert records to stay within Supabase payload limits."""
    for i in range(0, len(records), batch_size):
        batch = records[i : i + batch_size]
        try:
            httpx.post(
                f"{_url()}/rest/v1/{table}",
                headers={**_admin_headers(), "Prefer": "return=minimal"},
                json=batch,
                timeout=_LONG_TIMEOUT,
            )
        except Exception:
            pass


# ══════════════════════════════════════════════════════
# ADMIN CLIENT SHIM  (for admin.py compatibility)
# ══════════════════════════════════════════════════════

class _AdminUsersProxy:
    def create_user(self, payload: dict):
        r = httpx.post(
            f"{_url()}/auth/v1/admin/users",
            headers=_admin_headers(),
            json=payload,
            timeout=_TIMEOUT,
        )
        if r.status_code not in (200, 201):
            body = r.json()
            raise Exception(body.get("msg") or body.get("message") or r.text)
        return r.json()


class _AdminAuthProxy:
    def __init__(self):
        self.admin = _AdminUsersProxy()


class _TableProxy:
    """Minimal PostgREST-style table proxy for legacy code compatibility."""
    def __init__(self, table: str):
        self._table   = table
        self._params  = {}
        self._headers = {}
        self._mode    = "select"
        self._payload = None

    def select(self, cols: str = "*", **kwargs):
        self._params["select"] = cols
        if "count" in kwargs:
            self._headers["Prefer"] = f"count={kwargs['count']}"
        return self

    def insert(self, data):
        self._mode    = "insert"
        self._payload = data
        return self

    def update(self, data):
        self._mode    = "update"
        self._payload = data
        return self

    def eq(self, col: str, val):
        self._params[col] = f"eq.{val}"
        return self

    def order(self, col: str, desc: bool = True):
        self._params["order"] = f"{col}.{'desc' if desc else 'asc'}"
        return self

    def limit(self, n: int):
        self._params["limit"] = str(n)
        return self

    def execute(self):
        url     = f"{_url()}/rest/v1/{self._table}"
        headers = {**_admin_headers(), **self._headers}

        if self._mode == "insert":
            httpx.post(url, headers={**headers, "Prefer": "return=minimal"},
                       json=self._payload, timeout=_TIMEOUT)
            class _R:
                data  = []
                count = None
            return _R()

        r = httpx.get(url, params=self._params, headers=headers, timeout=_TIMEOUT)

        class _R:
            pass
        resp       = _R()
        resp.data  = r.json() if r.status_code == 200 else []
        if "Prefer" in self._headers:
            cr         = r.headers.get("content-range", "0-0/0")
            total      = cr.split("/")[-1]
            resp.count = int(total) if total.isdigit() else 0
        else:
            resp.count = None
        return resp


class _AdminClientShim:
    """Drop-in replacement for supabase_client for admin.py."""
    def __init__(self):
        self.auth = _AdminAuthProxy()

    def table(self, name: str) -> _TableProxy:
        return _TableProxy(name)


def _admin_client() -> _AdminClientShim:
    return _AdminClientShim()


# ══════════════════════════════════════════════════════
# DATA SEEDING
# ══════════════════════════════════════════════════════

def seed_data_if_empty():
    """
    Seed synthetic demo data into Supabase if tables are empty.
    Called once after the first successful login.
    """
    try:
        if get_table_count("consumers") > 0:
            return  # Already seeded
    except Exception:
        return

    np.random.seed(42)
    random.seed(42)

    city_coords = {
        "New York":      (40.71, -74.01), "Los Angeles":   (34.05, -118.24),
        "Chicago":       (41.88, -87.63), "Houston":       (29.76, -95.37),
        "Phoenix":       (33.45, -112.07),"San Francisco": (37.77, -122.42),
        "Seattle":       (47.61, -122.33),"Boston":        (42.36, -71.06),
        "Dallas":        (32.78, -96.80), "Miami":         (25.77, -80.19),
    }
    names = [
        "Alpha Corp","Beta Industries","Gamma Ltd","Delta Systems",
        "Epsilon Tech","Zeta Power","Eta Grid","Theta Energy",
        "Iota Smart","Kappa Networks","Lambda City","Mu Solutions",
        "Nu Dynamics","Xi Analytics","Omicron Hub","Pi Ventures",
        "Rho Utilities","Sigma Plants","Tau Logistics","Upsilon AI",
    ]

    # ── Consumers ──────────────────────────────────────
    consumers = []
    for i in range(50):
        city = random.choice(CITIES)
        lat, lon = city_coords.get(city, (0, 0))
        consumers.append({
            "consumer_id": f"CON-{1000 + i}",
            "name":        f"{names[i % len(names)]} {i + 1}",
            "city":        city,
            "device_type": random.choice(DEVICE_TYPES),
            "contract_kw": round(random.uniform(10, 500), 1),
            "tariff_rate": round(random.uniform(0.08, 0.25), 3),
            "latitude":    round(lat + random.uniform(-0.1, 0.1), 4),
            "longitude":   round(lon + random.uniform(-0.1, 0.1), 4),
        })
    _batch_insert("consumers", consumers)

    # ── Energy Readings (7 days) ───────────────────────
    readings   = []
    end_dt     = datetime.utcnow()
    start_dt   = end_dt - timedelta(days=7)
    sample_con = [f"CON-{1000 + i}" for i in range(10)]
    t = start_dt
    while t <= end_dt:
        for con in sample_con:
            h      = t.hour
            base   = max(10.0, 80 + 40 * np.sin(np.pi * h / 12) + random.gauss(0, 10))
            volt   = round(random.gauss(230, 5), 2)
            pf     = round(random.uniform(0.85, 0.99), 3)
            tariff = random.uniform(0.08, 0.25)
            readings.append({
                "consumer_id":  con,
                "timestamp":    t.isoformat() + "Z",
                "energy_kwh":   round(base, 2),
                "voltage":      volt,
                "current_a":    round(base / volt * 1000, 2),
                "power_factor": pf,
                "temperature":  round(random.gauss(22, 4), 1),
                "city":         random.choice(CITIES),
                "device_type":  random.choice(DEVICE_TYPES),
                "cost_usd":     round(base * tariff, 4),
            })
        t += timedelta(hours=1)
    _batch_insert("energy_readings", readings)

    # ── Predictions ────────────────────────────────────
    preds = []
    today = datetime.utcnow().date()
    for city in CITIES[:5]:
        for hour in range(24):
            base = 120 + 50 * np.sin(np.pi * hour / 12)
            preds.append({
                "prediction_date": str(today),
                "hour":            hour,
                "predicted_kwh":   round(base + random.gauss(0, 8), 2),
                "confidence":      round(random.uniform(0.82, 0.98), 3),
                "city":            city,
            })
    _batch_insert("predictions", preds)

    # ── Anomalies ──────────────────────────────────────
    anomaly_types = [
        ("Meter Tampering",      "Unusual bypass signature detected"),
        ("Usage Spike",          "Sudden >200% consumption spike"),
        ("Off-Hours Activity",   "High usage during non-operational hours"),
        ("Voltage Irregularity", "Abnormal voltage fluctuation pattern"),
        ("Power Factor Drop",    "PF dropped below 0.75 threshold"),
    ]
    anomalies = []
    for _ in range(20):
        atype, desc = random.choice(anomaly_types)
        detected    = datetime.utcnow() - timedelta(hours=random.randint(1, 240))
        anomalies.append({
            "consumer_id":  f"CON-{1000 + random.randint(0, 49)}",
            "detected_at":  detected.isoformat() + "Z",
            "anomaly_type": atype,
            "risk_score":   round(random.uniform(0.4, 0.99), 3),
            "description":  desc,
            "status":       random.choice(["Open", "Investigating", "Resolved"]),
            "city":         random.choice(CITIES),
        })
    _batch_insert("anomalies", anomalies)

    # ── Smart Meters ───────────────────────────────────
    meters = []
    for i in range(30):
        last_ping = datetime.utcnow() - timedelta(minutes=random.randint(1, 60))
        meters.append({
            "meter_id":    f"MTR-{5000 + i}",
            "consumer_id": f"CON-{1000 + i}",
            "city":        random.choice(CITIES),
            "status":      random.choice(["Active","Active","Active","Offline","Maintenance"]),
            "last_ping":   last_ping.isoformat() + "Z",
            "battery_pct": round(random.uniform(60, 100), 1),
        })
    _batch_insert("smart_meters", meters)

    # ── User Profiles ──────────────────────────────────
    profiles = [
        {"email": "admin@energix.ai",   "name": "Alex Reynolds", "role": "Admin"},
        {"email": "analyst@energix.ai", "name": "Priya Sharma",  "role": "Analyst"},
        {"email": "demo@energix.ai",    "name": "Guest User",    "role": "Viewer"},
        {"email": "ops@energix.ai",     "name": "Marcus Webb",   "role": "Operator"},
        {"email": "eng@energix.ai",     "name": "Lena Fischer",  "role": "Engineer"},
    ]
    _batch_insert("users", profiles)
