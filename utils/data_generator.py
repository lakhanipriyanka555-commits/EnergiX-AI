import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import random
from config import CITIES, DEVICE_TYPES


def generate_hourly_series(days=30, noise_std=12, seed=42):
    np.random.seed(seed)
    periods = days * 24
    t = np.arange(periods)
    # Daily sinusoidal pattern
    daily = 80 + 40 * np.sin(2 * np.pi * t / 24 - np.pi / 2)
    # Weekly seasonality
    weekly = 15 * np.sin(2 * np.pi * t / (24 * 7))
    # Long-term trend
    trend = 0.02 * t
    noise = np.random.normal(0, noise_std, periods)
    values = daily + weekly + trend + noise
    values = np.clip(values, 20, 300)

    start = datetime.now() - timedelta(days=days)
    timestamps = [start + timedelta(hours=i) for i in range(periods)]
    df = pd.DataFrame({"timestamp": timestamps, "energy_kwh": values.round(2)})
    return df


def generate_multi_city_daily(days=30):
    records = []
    for city in CITIES:
        base = random.uniform(500, 2000)
        for d in range(days):
            dt = datetime.now() - timedelta(days=days - d)
            val = base + random.gauss(0, 80) + 10 * d
            records.append({"city": city, "date": dt.date(), "energy_mwh": round(max(val, 100), 2)})
    return pd.DataFrame(records)


def generate_device_usage():
    data = {
        "device_type": DEVICE_TYPES,
        "usage_kwh": [round(random.uniform(50, 400), 1) for _ in DEVICE_TYPES],
    }
    return pd.DataFrame(data)


def generate_forecast_data(hours=24):
    np.random.seed(int(datetime.now().timestamp()) % 1000)
    t = np.arange(hours)
    historical_hours = 48
    hist_t = np.arange(-historical_hours, 0)

    base_val = 100 + 50 * np.sin(2 * np.pi * np.arange(-historical_hours, hours) / 24 - np.pi / 2)
    hist_vals = base_val[:historical_hours] + np.random.normal(0, 10, historical_hours)
    pred_vals = base_val[historical_hours:] + np.random.normal(0, 5, hours)
    confidence = np.clip(np.random.uniform(0.82, 0.97, hours), 0, 1)
    upper = pred_vals * (1 + (1 - confidence) * 0.5)
    lower = pred_vals * (1 - (1 - confidence) * 0.5)

    now = datetime.now().replace(minute=0, second=0, microsecond=0)
    hist_ts = [now - timedelta(hours=historical_hours - i) for i in range(historical_hours)]
    pred_ts = [now + timedelta(hours=i) for i in range(hours)]

    hist_df = pd.DataFrame({"timestamp": hist_ts, "energy_kwh": hist_vals.round(2), "type": "Historical"})
    pred_df = pd.DataFrame({
        "timestamp": pred_ts,
        "energy_kwh": pred_vals.round(2),
        "upper": upper.round(2),
        "lower": lower.round(2),
        "confidence": (confidence * 100).round(1),
        "type": "Forecast",
    })
    return hist_df, pred_df


def generate_anomaly_scores(n=50):
    np.random.seed(7)
    consumer_ids = [f"CON-{1000+i}" for i in range(n)]
    cities = [random.choice(CITIES) for _ in range(n)]
    risk_scores = np.random.beta(2, 5, n)
    risk_scores[:5] = np.random.uniform(0.75, 0.99, 5)  # inject high-risk
    usage_deviation = risk_scores * 200 + np.random.normal(0, 10, n)
    anomaly_types = np.where(
        risk_scores > 0.75,
        np.random.choice(["Meter Tampering", "Usage Spike"], n),
        "Normal",
    )
    df = pd.DataFrame({
        "consumer_id": consumer_ids,
        "city": cities,
        "risk_score": risk_scores.round(3),
        "usage_deviation_pct": usage_deviation.round(1),
        "anomaly_type": anomaly_types,
        "detected_at": [datetime.now() - timedelta(hours=random.randint(1, 72)) for _ in range(n)],
    })
    return df.sort_values("risk_score", ascending=False).reset_index(drop=True)


def generate_carbon_data(days=90):
    records = []
    sources = ["Coal", "Natural Gas", "Solar", "Wind", "Hydro", "Nuclear"]
    weights = [0.28, 0.24, 0.18, 0.14, 0.10, 0.06]
    for d in range(days):
        dt = datetime.now() - timedelta(days=days - d)
        total_mwh = random.uniform(800, 1600)
        for src, wt in zip(sources, weights):
            kwh = total_mwh * wt * 1000 * random.uniform(0.85, 1.15)
            ef = {"Coal": 0.82, "Natural Gas": 0.49, "Solar": 0.04,
                  "Wind": 0.01, "Hydro": 0.02, "Nuclear": 0.02}
            co2 = kwh * ef[src] / 1000  # tonnes
            records.append({
                "date": dt.date(), "source": src,
                "energy_mwh": round(kwh / 1000, 2), "co2_tonnes": round(co2, 2),
                "is_renewable": src in ["Solar", "Wind", "Hydro"],
            })
    return pd.DataFrame(records)


def generate_realtime_tick(prev_val=None, base=110):
    if prev_val is None:
        prev_val = base
    new_val = prev_val + random.gauss(0, 3)
    new_val = max(40, min(300, new_val))
    voltage = round(random.gauss(230, 3), 2)
    freq = round(random.gauss(50.0, 0.05), 3)
    pf = round(random.uniform(0.88, 0.99), 3)
    return {
        "timestamp": datetime.now(),
        "energy_kwh": round(new_val, 2),
        "voltage": voltage,
        "frequency": freq,
        "power_factor": pf,
        "grid_load_pct": round(min(100, new_val / 3), 1),
    }


def generate_optimization_data():
    categories = ["HVAC", "Lighting", "Industrial", "EV Charging", "Data Centers"]
    before = [round(random.uniform(150, 400), 1) for _ in categories]
    savings_pct = [round(random.uniform(10, 35), 1) for _ in categories]
    after = [round(b * (1 - s / 100), 1) for b, s in zip(before, savings_pct)]
    return pd.DataFrame({
        "category": categories,
        "before_kwh": before,
        "after_kwh": after,
        "savings_pct": savings_pct,
        "cost_saved_usd": [round((b - a) * 0.18, 2) for b, a in zip(before, after)],
    })


def generate_weather_data():
    return {
        "temperature": round(random.uniform(18, 38), 1),
        "humidity": round(random.uniform(30, 85), 1),
        "wind_speed": round(random.uniform(5, 45), 1),
        "condition": random.choice(["Sunny ☀️", "Partly Cloudy ⛅", "Cloudy ☁️", "Rainy 🌧️", "Windy 💨"]),
        "solar_irradiance": round(random.uniform(200, 900), 0),
    }
