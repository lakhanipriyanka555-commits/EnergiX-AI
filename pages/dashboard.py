"""
EnergiX AI – Dashboard Overview Page
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import random

from database.supabase_manager import get_kpi_summary, query_df
from utils.data_generator import (
    generate_hourly_series, generate_multi_city_daily,
    generate_device_usage, generate_weather_data
)
from utils.charts import (
    line_chart, area_chart_multi, pie_chart,
    bar_chart, heatmap_chart
)


def _kpi_card(icon, label, value, delta, delta_dir, color_cls):
    delta_cls = "up" if delta_dir == "up" else "down"
    arrow = "▲" if delta_dir == "up" else "▼"
    st.markdown(f"""
    <div class="kpi-card {color_cls} animate-fade-up">
        <span class="kpi-icon">{icon}</span>
        <div class="kpi-label">{label}</div>
        <div class="kpi-value">{value}</div>
        <div class="kpi-delta {delta_cls}">{arrow} {delta}</div>
    </div>
    """, unsafe_allow_html=True)


def show():
    # ── Page Header ───────────────────────────────────
    now = datetime.now()
    st.markdown(f"""
    <div class="page-title-banner animate-fade-up">
        <span style="font-size:2rem;">📊</span>
        <div>
            <h1>Dashboard Overview</h1>
            <p>Live Smart Grid Monitoring · Last updated {now.strftime('%H:%M:%S')} · {now.strftime('%d %b %Y')}</p>
        </div>
        <div style="margin-left:auto;">
            <span class="ai-badge">🤖 AI Powered</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── KPI Data ──────────────────────────────────────
    kpi = get_kpi_summary()
    total_kwh  = float(kpi.get("total_kwh", 0) or 0)
    avg_kwh    = float(kpi.get("avg_kwh", 0) or 0)
    peak_kwh   = float(kpi.get("peak_kwh", 0) or 0)
    total_cost = float(kpi.get("total_cost", 0) or 0)
    consumers  = int(kpi.get("active_consumers", 0) or 0)
    avg_pf     = float(kpi.get("avg_pf", 0.92) or 0.92)

    # Derived KPIs
    grid_load_pct  = round(min(100, avg_kwh / 3), 1)
    predicted_kwh  = round(avg_kwh * 1.08, 1)
    carbon_kg      = round(total_kwh * 0.45 / 1000, 1)

    # ── KPI Row ───────────────────────────────────────
    cols = st.columns(6)
    kpis = [
        ("⚡", "Total Energy (24h)", f"{total_kwh:,.0f} kWh", "+3.2% vs yesterday", "up",   "kpi-card-blue"),
        ("📈", "Grid Load",          f"{grid_load_pct}%",     "-1.5% vs avg",       "down",  "kpi-card-cyan"),
        ("👥", "Active Consumers",   f"{consumers:,}",         "+2 new today",       "up",   "kpi-card-green"),
        ("🤖", "Predicted Demand",   f"{predicted_kwh:.1f}",  "+8% next hour",      "up",   "kpi-card-orange"),
        ("🌿", "Carbon Emission",    f"{carbon_kg} t CO₂",    "-5% this week",      "down",  "kpi-card-green"),
        ("💰", "Energy Cost (24h)",  f"${total_cost:,.2f}",   "+1.8% vs yesterday", "up",   "kpi-card-purple"),
    ]
    for col, (icon, label, value, delta, delta_dir, color) in zip(cols, kpis):
        with col:
            _kpi_card(icon, label, value, delta, delta_dir, color)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Peak usage banner ─────────────────────────────
    peak_hour = random.randint(17, 20)
    st.markdown(f"""
    <div class="peak-banner animate-fade-up">
        <div class="icon">⚡</div>
        <div class="text">
            <h4>Peak Load Alert – {peak_hour}:00 Today</h4>
            <p>Grid load is expected to reach <strong>{grid_load_pct + random.uniform(8,15):.1f}%</strong>
            capacity during evening peak hours. AI recommends load balancing across zones.</p>
        </div>
        <div style="margin-left:auto;text-align:right">
            <span class="risk-badge risk-high">HIGH RISK</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Row 2: Energy Trend + Weather ─────────────────
    col_trend, col_weather = st.columns([3, 1])

    with col_trend:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown("""
        <div class="section-header">
            <div class="icon">📈</div>
            <h3>24-Hour Energy Consumption Trend</h3>
            <span class="badge">LIVE</span>
        </div>
        """, unsafe_allow_html=True)
        df_trend = generate_hourly_series(days=1)
        fig = line_chart(df_trend, "timestamp", "energy_kwh", title="")
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
        st.markdown('</div>', unsafe_allow_html=True)

    with col_weather:
        weather = generate_weather_data()
        st.markdown(f"""
        <div class="weather-card float-anim">
            <div style="font-size:0.72rem;opacity:0.8;text-transform:uppercase;letter-spacing:0.08em;">
                🌍 Current Weather
            </div>
            <div class="weather-temp">{weather['temperature']}°C</div>
            <div style="font-size:1.5rem;margin:0.5rem 0;">{weather['condition']}</div>
            <hr style="border-color:rgba(255,255,255,0.25)!important;margin:0.75rem 0!important;">
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:0.5rem;">
                <div><div class="weather-label">Humidity</div><strong>{weather['humidity']}%</strong></div>
                <div><div class="weather-label">Wind</div><strong>{weather['wind_speed']} km/h</strong></div>
                <div><div class="weather-label">Solar Irr.</div><strong>{weather['solar_irradiance']:.0f} W/m²</strong></div>
                <div><div class="weather-label">Power Factor</div><strong>{avg_pf:.3f}</strong></div>
            </div>
            <div style="margin-top:0.75rem;font-size:0.75rem;opacity:0.75;">
                ☀️ High solar irradiance → optimize renewable intake
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Quick stats below weather
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(f"""
        <div class="glass-card" style="padding:1rem;">
            <div class="kpi-label">Peak Load Today</div>
            <div style="font-size:1.5rem;font-weight:800;color:#FF6B35;">{peak_kwh:.1f} kWh</div>
            <div style="margin-top:0.5rem;">
                <div class="kpi-label">System Efficiency</div>
                <div style="font-size:1.5rem;font-weight:800;color:#00C853;">{round(avg_pf*100,1)}%</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # ── Row 3: Device Pie + City Bar ──────────────────
    col_pie, col_bar = st.columns(2)

    with col_pie:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown("""
        <div class="section-header">
            <div class="icon">🥧</div>
            <h3>Device-Wise Energy Usage</h3>
        </div>
        """, unsafe_allow_html=True)
        df_dev = generate_device_usage()
        fig_pie = pie_chart(df_dev, "device_type", "usage_kwh", title="")
        st.plotly_chart(fig_pie, use_container_width=True, config={"displayModeBar": False})
        st.markdown('</div>', unsafe_allow_html=True)

    with col_bar:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown("""
        <div class="section-header">
            <div class="icon">🏙️</div>
            <h3>City-Wise Energy Consumption</h3>
        </div>
        """, unsafe_allow_html=True)
        df_city = generate_multi_city_daily(days=1)
        df_city_agg = df_city.groupby("city")["energy_mwh"].sum().reset_index()
        fig_bar = bar_chart(df_city_agg, "city", "energy_mwh", title="")
        st.plotly_chart(fig_bar, use_container_width=True, config={"displayModeBar": False})
        st.markdown('</div>', unsafe_allow_html=True)

    # ── Row 4: Heatmap ────────────────────────────────
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown("""
    <div class="section-header">
        <div class="icon">🌡️</div>
        <h3>City × Hour Energy Heatmap</h3>
        <span class="badge">AI ENHANCED</span>
    </div>
    """, unsafe_allow_html=True)

    # Build city-hour data
    hours = list(range(24))
    from config import CITIES
    records = []
    for city in CITIES[:8]:
        for h in hours:
            base = 80 + 40 * np.sin(np.pi * h / 12)
            records.append({"city": city, "hour": h, "energy_kwh": round(base + random.gauss(0, 10), 1)})
    df_heat = pd.DataFrame(records)
    fig_heat = heatmap_chart(df_heat, "hour", "city", "energy_kwh",
                             title="Energy Consumption by City & Hour (kWh)")
    st.plotly_chart(fig_heat, use_container_width=True, config={"displayModeBar": False})
    st.markdown('</div>', unsafe_allow_html=True)

    # ── Row 5: 30-Day Multi-area trend ────────────────
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown("""
    <div class="section-header">
        <div class="icon">📉</div>
        <h3>30-Day Energy Trend – Multi-Source Breakdown</h3>
    </div>
    """, unsafe_allow_html=True)

    df_30 = generate_hourly_series(days=30)
    df_30["solar"]    = (df_30["energy_kwh"] * 0.22 + np.random.normal(0, 5, len(df_30))).clip(0)
    df_30["wind"]     = (df_30["energy_kwh"] * 0.15 + np.random.normal(0, 3, len(df_30))).clip(0)
    df_30["grid_net"] = df_30["energy_kwh"] - df_30["solar"] - df_30["wind"]
    # Downsample to daily for cleaner chart
    df_30["date"] = df_30["timestamp"].dt.date
    df_daily = df_30.groupby("date")[["energy_kwh", "solar", "wind", "grid_net"]].mean().reset_index()
    df_daily["date"] = pd.to_datetime(df_daily["date"])
    fig_area = area_chart_multi(df_daily, "date",
                                ["energy_kwh", "solar", "wind", "grid_net"],
                                title="")
    st.plotly_chart(fig_area, use_container_width=True, config={"displayModeBar": False})
    st.markdown('</div>', unsafe_allow_html=True)
