import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
from config import DB_PATH, CITIES, DEVICE_TYPES


def get_connection():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS consumers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            consumer_id TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            city TEXT NOT NULL,
            device_type TEXT NOT NULL,
            contract_kw REAL NOT NULL,
            tariff_rate REAL NOT NULL,
            latitude REAL,
            longitude REAL,
            registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS energy_readings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            consumer_id TEXT NOT NULL,
            timestamp TIMESTAMP NOT NULL,
            energy_kwh REAL NOT NULL,
            voltage REAL NOT NULL,
            current_a REAL NOT NULL,
            power_factor REAL NOT NULL,
            temperature REAL NOT NULL,
            city TEXT NOT NULL,
            device_type TEXT NOT NULL,
            cost_usd REAL NOT NULL
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS predictions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            prediction_date DATE NOT NULL,
            hour INTEGER NOT NULL,
            predicted_kwh REAL NOT NULL,
            confidence REAL NOT NULL,
            model_version TEXT DEFAULT 'v2.1',
            city TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS anomalies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            consumer_id TEXT NOT NULL,
            detected_at TIMESTAMP NOT NULL,
            anomaly_type TEXT NOT NULL,
            risk_score REAL NOT NULL,
            description TEXT,
            status TEXT DEFAULT 'Open',
            city TEXT NOT NULL
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            role TEXT NOT NULL,
            last_login TIMESTAMP,
            is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS smart_meters (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            meter_id TEXT UNIQUE NOT NULL,
            consumer_id TEXT NOT NULL,
            city TEXT NOT NULL,
            status TEXT DEFAULT 'Active',
            firmware_version TEXT DEFAULT 'v3.2.1',
            last_ping TIMESTAMP,
            battery_pct REAL DEFAULT 100.0
        )
    """)

    conn.commit()
    conn.close()


def seed_data_if_empty():
    conn = get_connection()
    c = conn.cursor()
    count = c.execute("SELECT COUNT(*) FROM consumers").fetchone()[0]
    if count > 0:
        conn.close()
        return

    np.random.seed(42)
    random.seed(42)

    # --- Consumers ---
    consumers = []
    city_coords = {
        "New York": (40.71, -74.01), "Los Angeles": (34.05, -118.24),
        "Chicago": (41.88, -87.63), "Houston": (29.76, -95.37),
        "Phoenix": (33.45, -112.07), "San Francisco": (37.77, -122.42),
        "Seattle": (47.61, -122.33), "Boston": (42.36, -71.06),
        "Dallas": (32.78, -96.80), "Miami": (25.77, -80.19),
    }
    names = [
        "Alpha Corp", "Beta Industries", "Gamma Ltd", "Delta Systems",
        "Epsilon Tech", "Zeta Power", "Eta Grid", "Theta Energy",
        "Iota Smart", "Kappa Networks", "Lambda City", "Mu Solutions",
        "Nu Dynamics", "Xi Analytics", "Omicron Hub", "Pi Ventures",
        "Rho Utilities", "Sigma Plants", "Tau Logistics", "Upsilon AI",
    ]
    for i in range(50):
        city = random.choice(CITIES)
        lat, lon = city_coords.get(city, (0, 0))
        consumers.append((
            f"CON-{1000+i}",
            names[i % len(names)] + f" {i+1}",
            city,
            random.choice(DEVICE_TYPES),
            round(random.uniform(10, 500), 1),
            round(random.uniform(0.08, 0.25), 3),
            round(lat + random.uniform(-0.1, 0.1), 4),
            round(lon + random.uniform(-0.1, 0.1), 4),
        ))
    c.executemany(
        "INSERT OR IGNORE INTO consumers (consumer_id,name,city,device_type,contract_kw,tariff_rate,latitude,longitude) VALUES (?,?,?,?,?,?,?,?)",
        consumers
    )

    # --- Energy Readings (last 30 days, hourly) ---
    readings = []
    end_dt = datetime.now()
    start_dt = end_dt - timedelta(days=30)
    sample_consumers = [f"CON-{1000+i}" for i in range(10)]
    t = start_dt
    while t <= end_dt:
        for con in sample_consumers:
            city = random.choice(CITIES)
            dev = random.choice(DEVICE_TYPES)
            hour = t.hour
            base = 80 + 40 * np.sin(np.pi * hour / 12) + random.gauss(0, 10)
            base = max(10, base)
            voltage = round(random.gauss(230, 5), 2)
            current = round(base / voltage * 1000, 2)
            pf = round(random.uniform(0.85, 0.99), 3)
            temp = round(random.gauss(22, 4), 1)
            tariff = random.uniform(0.08, 0.25)
            cost = round(base * tariff, 4)
            readings.append((con, t.strftime("%Y-%m-%d %H:%M:%S"),
                             round(base, 2), voltage, current, pf, temp, city, dev, cost))
        t += timedelta(hours=1)
    c.executemany(
        "INSERT INTO energy_readings (consumer_id,timestamp,energy_kwh,voltage,current_a,power_factor,temperature,city,device_type,cost_usd) VALUES (?,?,?,?,?,?,?,?,?,?)",
        readings
    )

    # --- Predictions (next 24 hrs) ---
    preds = []
    today = datetime.now().date()
    for city in CITIES[:5]:
        for hour in range(24):
            base = 120 + 50 * np.sin(np.pi * hour / 12)
            conf = round(random.uniform(0.82, 0.98), 3)
            preds.append((str(today), hour, round(base + random.gauss(0, 8), 2), conf, city))
    c.executemany(
        "INSERT INTO predictions (prediction_date,hour,predicted_kwh,confidence,city) VALUES (?,?,?,?,?)",
        preds
    )

    # --- Anomalies ---
    anomaly_types = [
        ("Meter Tampering", "Potential meter tampering detected – unusual bypass signature"),
        ("Usage Spike", "Sudden energy usage spike of >200% baseline"),
        ("Off-Hours Activity", "High consumption detected during non-operational hours"),
        ("Voltage Irregularity", "Abnormal voltage fluctuation pattern"),
        ("Power Factor Drop", "Power factor dropped below 0.75 threshold"),
    ]
    anomalies = []
    for i in range(20):
        con = f"CON-{1000 + random.randint(0, 49)}"
        atype, desc = random.choice(anomaly_types)
        detected = datetime.now() - timedelta(hours=random.randint(1, 240))
        risk = round(random.uniform(0.4, 0.99), 3)
        status = random.choice(["Open", "Investigating", "Resolved"])
        city = random.choice(CITIES)
        anomalies.append((con, detected.strftime("%Y-%m-%d %H:%M:%S"), atype, risk, desc, status, city))
    c.executemany(
        "INSERT INTO anomalies (consumer_id,detected_at,anomaly_type,risk_score,description,status,city) VALUES (?,?,?,?,?,?,?)",
        anomalies
    )

    # --- Users ---
    users = [
        ("admin@energix.ai", "Alex Reynolds", "Admin"),
        ("analyst@energix.ai", "Priya Sharma", "Analyst"),
        ("demo@energix.ai", "Guest User", "Viewer"),
        ("ops@energix.ai", "Marcus Webb", "Operator"),
        ("eng@energix.ai", "Lena Fischer", "Engineer"),
    ]
    c.executemany(
        "INSERT OR IGNORE INTO users (email,name,role) VALUES (?,?,?)",
        users
    )

    # --- Smart Meters ---
    meters = []
    for i in range(30):
        con = f"CON-{1000 + i}"
        city = random.choice(CITIES)
        last_ping = datetime.now() - timedelta(minutes=random.randint(1, 60))
        status = random.choice(["Active", "Active", "Active", "Offline", "Maintenance"])
        batt = round(random.uniform(60, 100), 1)
        meters.append((f"MTR-{5000+i}", con, city, status,
                       last_ping.strftime("%Y-%m-%d %H:%M:%S"), batt))
    c.executemany(
        "INSERT OR IGNORE INTO smart_meters (meter_id,consumer_id,city,status,last_ping,battery_pct) VALUES (?,?,?,?,?,?)",
        meters
    )

    conn.commit()
    conn.close()


def query_df(sql, params=()):
    conn = get_connection()
    df = pd.read_sql_query(sql, conn, params=params)
    conn.close()
    return df


def execute_sql(sql):
    conn = get_connection()
    try:
        df = pd.read_sql_query(sql, conn)
        conn.close()
        return df, None
    except Exception as e:
        try:
            conn.execute(sql)
            conn.commit()
            conn.close()
            return pd.DataFrame(), None
        except Exception as e2:
            conn.close()
            return None, str(e2)


def get_kpi_summary():
    df = query_df("""
        SELECT
            SUM(energy_kwh) as total_kwh,
            AVG(energy_kwh) as avg_kwh,
            MAX(energy_kwh) as peak_kwh,
            SUM(cost_usd) as total_cost,
            COUNT(DISTINCT consumer_id) as active_consumers,
            AVG(power_factor) as avg_pf
        FROM energy_readings
        WHERE timestamp >= datetime('now','-24 hours')
    """)
    return df.iloc[0] if len(df) > 0 else {}
