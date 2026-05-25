"""
EnergiX AI – Real-Time Simulation Page
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import time
import random
from datetime import datetime

from utils.data_generator import generate_realtime_tick
from config import CITIES


_MAX_BUFFER = 60  # seconds of history


def _init_rt_state():
    if "rt_buffer" not in st.session_state:
        st.session_state.rt_buffer = []
    if "rt_running" not in st.session_state:
        st.session_state.rt_running = False
    if "rt_tick_count" not in st.session_state:
        st.session_state.rt_tick_count = 0
    if "rt_notifications" not in st.session_state:
        st.session_state.rt_notifications = []
    if "rt_last_val" not in st.session_state:
        st.session_state.rt_last_val = 110.0


def _maybe_add_notification(tick):
    notifs = st.session_state.rt_notifications
    if tick["grid_load_pct"] > 90:
        notifs.insert(0, {
            "type": "danger",
            "msg": f"🚨 Grid overload! Load at {tick['grid_load_pct']:.1f}%",
            "time": datetime.now().strftime("%H:%M:%S"),
        })
    elif tick["voltage"] < 225 or tick["voltage"] > 235:
        notifs.insert(0, {
            "type": "warning",
            "msg": f"⚡ Voltage anomaly: {tick['voltage']:.1f}V (normal: 230V)",
            "time": datetime.now().strftime("%H:%M:%S"),
        })
    elif tick["power_factor"] < 0.9:
        notifs.insert(0, {
            "type": "warning",
            "msg": f"⚠️ Low power factor: {tick['power_factor']:.3f}",
            "time": datetime.now().strftime("%H:%M:%S"),
        })
    # Keep last 20
    st.session_state.rt_notifications = notifs[:20]


def show():
    _init_rt_state()

    st.markdown("""
    <div class="page-title-banner animate-fade-up">
        <span style="font-size:2rem;">📡</span>
        <div>
            <h1>Real-Time Grid Monitor</h1>
            <p>Live smart meter simulation · Auto-refreshing sensor data · Dynamic grid analysis</p>
        </div>
        <div style="margin-left:auto;">
            <span class="ai-badge">⚡ LIVE</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Controls ──────────────────────────────────────
    col_ctrl1, col_ctrl2, col_ctrl3, col_ctrl4 = st.columns([1, 1, 1, 3])
    with col_ctrl1:
        if st.button("▶️ Start Live Feed", key="rt_start", use_container_width=True):
            st.session_state.rt_running = True
    with col_ctrl2:
        if st.button("⏹️ Stop", key="rt_stop", use_container_width=True):
            st.session_state.rt_running = False
    with col_ctrl3:
        if st.button("🗑️ Clear Data", key="rt_clear", use_container_width=True):
            st.session_state.rt_buffer = []
            st.session_state.rt_notifications = []
            st.session_state.rt_tick_count = 0
    with col_ctrl4:
        city_sim = st.selectbox("Simulating City", CITIES, key="rt_city",
                                label_visibility="collapsed")

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Generate a new tick if running ────────────────
    if st.session_state.rt_running:
        tick = generate_realtime_tick(
            prev_val=st.session_state.rt_last_val, base=110
        )
        st.session_state.rt_last_val = tick["energy_kwh"]
        st.session_state.rt_buffer.append(tick)
        st.session_state.rt_buffer = st.session_state.rt_buffer[-_MAX_BUFFER:]
        st.session_state.rt_tick_count += 1
        _maybe_add_notification(tick)

    # Use latest tick for sensor display
    if st.session_state.rt_buffer:
        latest = st.session_state.rt_buffer[-1]
    else:
        latest = generate_realtime_tick(base=110)

    # ── Sensor Cards ──────────────────────────────────
    cols_sensor = st.columns(5)
    sensors = [
        ("⚡", "Energy", f"{latest['energy_kwh']:.1f}", "kWh", ""),
        ("🔌", "Voltage", f"{latest['voltage']:.1f}", "V",
         "🔴" if abs(latest["voltage"] - 230) > 5 else "🟢"),
        ("〜", "Frequency", f"{latest['frequency']:.3f}", "Hz",
         "🔴" if abs(latest["frequency"] - 50) > 0.1 else "🟢"),
        ("💫", "Power Factor", f"{latest['power_factor']:.3f}", "PF",
         "🟠" if latest["power_factor"] < 0.9 else "🟢"),
        ("📊", "Grid Load", f"{latest['grid_load_pct']:.1f}", "%",
         "🔴" if latest["grid_load_pct"] > 90 else ("🟠" if latest["grid_load_pct"] > 75 else "🟢")),
    ]
    for col, (icon, label, value, unit, status) in zip(cols_sensor, sensors):
        with col:
            st.markdown(f"""
            <div class="sensor-card animate-fade-up">
                <div style="font-size:1.5rem;margin-bottom:0.25rem;">{icon} {status}</div>
                <div class="sensor-value">{value}</div>
                <div class="sensor-unit">{unit}</div>
                <div class="sensor-label">{label}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Live Chart + Notifications ────────────────────
    col_chart, col_notif = st.columns([3, 1])

    with col_chart:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown(f"""
        <div class="section-header">
            <div class="icon">📈</div>
            <h3>Live Energy Feed – {city_sim}</h3>
            <span class="badge">{'STREAMING' if st.session_state.rt_running else 'PAUSED'}</span>
        </div>
        """, unsafe_allow_html=True)

        if len(st.session_state.rt_buffer) > 1:
            df_rt = pd.DataFrame(st.session_state.rt_buffer)
            df_rt["time"] = [t.strftime("%H:%M:%S") for t in df_rt["timestamp"]]

            fig_rt = go.Figure()
            fig_rt.add_trace(go.Scatter(
                x=df_rt["time"], y=df_rt["energy_kwh"],
                mode="lines+markers",
                name="Energy kWh",
                line=dict(color="#00D4FF", width=2.5),
                marker=dict(size=5, color="#0066FF"),
                fill="tozeroy",
                fillcolor="rgba(0,212,255,0.08)",
            ))
            # Grid load overlay
            fig_rt.add_trace(go.Scatter(
                x=df_rt["time"], y=df_rt["grid_load_pct"],
                mode="lines", name="Grid Load %",
                line=dict(color="#FF6B35", width=2, dash="dot"),
                yaxis="y2",
            ))
            fig_rt.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,20,60,0.9)",
                font=dict(family="Inter, sans-serif", size=11, color="#e2eaf8"),
                margin=dict(l=20, r=60, t=20, b=40),
                legend=dict(orientation="h", yanchor="bottom", y=1.02,
                            xanchor="right", x=1, font=dict(color="#e2eaf8")),
                xaxis=dict(showgrid=True, gridcolor="rgba(0,212,255,0.1)",
                           tickangle=-45, tickfont=dict(color="#94a3b8")),
                yaxis=dict(showgrid=True, gridcolor="rgba(0,212,255,0.1)",
                           title="Energy (kWh)", titlefont=dict(color="#00D4FF"),
                           tickfont=dict(color="#94a3b8")),
                yaxis2=dict(title="Grid Load %", overlaying="y", side="right",
                            range=[0, 120], showgrid=False,
                            titlefont=dict(color="#FF6B35"),
                            tickfont=dict(color="#94a3b8")),
                hovermode="x unified",
            )
            if latest["grid_load_pct"] > 85:
                fig_rt.add_hline(y=85, line_dash="dash", line_color="#FF3366",
                                 yref="y2", annotation_text="Peak Threshold")
            st.plotly_chart(fig_rt, use_container_width=True, config={"displayModeBar": False})
        else:
            st.info("▶️ Click **Start Live Feed** to begin real-time monitoring.")

        st.markdown('</div>', unsafe_allow_html=True)

        # Voltage / PF trend
        if len(st.session_state.rt_buffer) > 1:
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            st.markdown("""
            <div class="section-header">
                <div class="icon">🔌</div>
                <h3>Voltage & Power Factor Trend</h3>
            </div>
            """, unsafe_allow_html=True)
            df_rt2 = pd.DataFrame(st.session_state.rt_buffer)
            df_rt2["time"] = [t.strftime("%H:%M:%S") for t in df_rt2["timestamp"]]
            fig_vf = go.Figure()
            fig_vf.add_trace(go.Scatter(
                x=df_rt2["time"], y=df_rt2["voltage"],
                mode="lines", name="Voltage (V)",
                line=dict(color="#0066FF", width=2),
                yaxis="y",
            ))
            fig_vf.add_trace(go.Scatter(
                x=df_rt2["time"], y=df_rt2["power_factor"] * 100,
                mode="lines", name="PF × 100",
                line=dict(color="#00C853", width=2, dash="dot"),
                yaxis="y2",
            ))
            fig_vf.update_layout(
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font=dict(family="Inter, sans-serif", size=11, color="#1e293b"),
                margin=dict(l=20, r=60, t=10, b=40),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                xaxis=dict(showgrid=True, gridcolor="rgba(0,102,255,0.08)", tickangle=-45),
                yaxis=dict(title="Voltage (V)", showgrid=True, gridcolor="rgba(0,102,255,0.08)"),
                yaxis2=dict(title="PF × 100", overlaying="y", side="right", showgrid=False),
            )
            st.plotly_chart(fig_vf, use_container_width=True, config={"displayModeBar": False})
            st.markdown('</div>', unsafe_allow_html=True)

    with col_notif:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown(f"""
        <div class="section-header">
            <div class="icon">🔔</div>
            <h3>Live Alerts</h3>
            <span class="badge">{len(st.session_state.rt_notifications)}</span>
        </div>
        """, unsafe_allow_html=True)

        if st.session_state.rt_notifications:
            for notif in st.session_state.rt_notifications[:12]:
                color_map = {"danger":"#FF3366","warning":"#FF6B35","info":"#0066FF","success":"#00C853"}
                c = color_map.get(notif["type"], "#0066FF")
                st.markdown(
                    f'<div style="border-left:3px solid {c};padding:0.5rem 0.75rem;'
                    f'background:rgba(255,255,255,0.6);border-radius:4px;margin-bottom:6px;">'
                    f'<div style="font-size:0.77rem;">{notif["msg"]}</div>'
                    f'<div style="font-size:0.68rem;color:#94a3b8;margin-top:2px;">{notif["time"]}</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
        else:
            st.markdown('<div style="font-size:0.82rem;color:#94a3b8;text-align:center;padding:1rem;">No alerts yet.<br>Start live feed to monitor.</div>',
                        unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        # Sensor status panel
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown("""
        <div class="section-header">
            <div class="icon">📡</div>
            <h3>Sensor Status</h3>
        </div>
        """, unsafe_allow_html=True)
        sensors_status = [
            ("SM-001", "Active",      "New York"),
            ("SM-002", "Active",      "Chicago"),
            ("SM-003", "Offline",     "Houston"),
            ("SM-004", "Active",      "Miami"),
            ("SM-005", "Maintenance", "Seattle"),
        ]
        for sid, status, city in sensors_status:
            dot = {"Active":"status-online","Offline":"status-offline","Maintenance":"status-warn"}.get(status,"")
            st.markdown(
                f'<div style="display:flex;align-items:center;justify-content:space-between;'
                f'padding:0.35rem 0;border-bottom:1px solid rgba(0,102,255,0.08);">'
                f'<div><span class="status-dot {dot}"></span>'
                f'<span style="font-size:0.82rem;font-weight:600;">{sid}</span>'
                f'<div style="font-size:0.7rem;color:#94a3b8;margin-left:14px;">{city}</div></div>'
                f'<span style="font-size:0.72rem;color:#475569;">{status}</span>'
                f'</div>',
                unsafe_allow_html=True,
            )
        st.markdown('</div>', unsafe_allow_html=True)

    # ── Stats summary ─────────────────────────────────
    if len(st.session_state.rt_buffer) > 5:
        st.markdown("<br>", unsafe_allow_html=True)
        df_buf = pd.DataFrame(st.session_state.rt_buffer)
        col_s1, col_s2, col_s3, col_s4 = st.columns(4)
        stats = [
            ("📊", "Total Ticks",   f"{st.session_state.rt_tick_count}",   "kpi-card-blue"),
            ("⬆️", "Max kWh",       f"{df_buf['energy_kwh'].max():.1f}",   "kpi-card-orange"),
            ("⬇️", "Min kWh",       f"{df_buf['energy_kwh'].min():.1f}",   "kpi-card-cyan"),
            ("〰️", "Avg kWh",       f"{df_buf['energy_kwh'].mean():.1f}",  "kpi-card-green"),
        ]
        for col, (icon, label, value, cls) in zip([col_s1, col_s2, col_s3, col_s4], stats):
            with col:
                st.markdown(f"""
                <div class="kpi-card {cls}">
                    <span class="kpi-icon">{icon}</span>
                    <div class="kpi-label">{label}</div>
                    <div class="kpi-value">{value}</div>
                </div>
                """, unsafe_allow_html=True)

    # ── Auto-refresh ──────────────────────────────────
    if st.session_state.rt_running:
        time.sleep(1.5)
        st.rerun()
