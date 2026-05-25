"""
EnergiX AI – Anomaly Detection Page
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import random

from database.supabase_manager import query_df
from utils.data_generator import generate_anomaly_scores, generate_hourly_series
from utils.ml_models import AnomalyDetector
from utils.charts import scatter_anomaly_chart, heatmap_chart
from config import CITIES


def _risk_badge(score):
    if score > 0.75:
        return '<span class="risk-badge risk-high">HIGH RISK</span>'
    elif score > 0.5:
        return '<span class="risk-badge risk-medium">MEDIUM</span>'
    return '<span class="risk-badge risk-low">NORMAL</span>'


def show():
    st.markdown("""
    <div class="page-title-banner animate-fade-up">
        <span style="font-size:2rem;">🚨</span>
        <div>
            <h1>Anomaly Detection Engine</h1>
            <p>Isolation Forest ML · Real-time electricity theft detection & abnormal usage monitoring</p>
        </div>
        <div style="margin-left:auto;">
            <span class="ai-badge">🔍 AI Powered</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Live Alerts ────────────────────────────────────
    st.markdown("""
    <div class="alert-danger animate-fade-up">
        <strong>🚨 CRITICAL ALERT:</strong> Potential Meter Tampering Detected – Consumer CON-1004
        in Chicago. Abnormal bypass signature found. Risk Score: <strong>0.94</strong>
        <span class="risk-badge risk-high" style="float:right;">INVESTIGATING</span>
    </div>
    <div class="alert-danger animate-fade-up">
        <strong>⚡ HIGH ALERT:</strong> Sudden Usage Spike Found – CON-1011 (Houston).
        Usage jumped 287% above baseline in last 2 hours.
        <span class="risk-badge risk-high" style="float:right;">OPEN</span>
    </div>
    <div class="alert-warning animate-fade-up">
        <strong>⚠️ WARNING:</strong> Off-Hours Activity Detected – CON-1023 (Seattle).
        High consumption at 2:45 AM during non-operational hours.
        <span class="risk-badge risk-medium" style="float:right;">OPEN</span>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Summary KPIs ──────────────────────────────────
    df_anom = generate_anomaly_scores(n=50)
    n_high    = len(df_anom[df_anom["risk_score"] > 0.75])
    n_medium  = len(df_anom[(df_anom["risk_score"] > 0.5) & (df_anom["risk_score"] <= 0.75)])
    n_normal  = len(df_anom[df_anom["risk_score"] <= 0.5])
    avg_risk  = df_anom["risk_score"].mean()

    col_k1, col_k2, col_k3, col_k4 = st.columns(4)
    stats = [
        ("🔴", "High Risk Cases",   str(n_high),             "kpi-card-red"),
        ("🟠", "Medium Risk",       str(n_medium),            "kpi-card-orange"),
        ("🟢", "Normal",            str(n_normal),            "kpi-card-green"),
        ("📊", "Avg Risk Score",    f"{avg_risk:.3f}",        "kpi-card-blue"),
    ]
    for col, (icon, label, value, cls) in zip([col_k1, col_k2, col_k3, col_k4], stats):
        with col:
            st.markdown(f"""
            <div class="kpi-card {cls} animate-fade-up">
                <span class="kpi-icon">{icon}</span>
                <div class="kpi-label">{label}</div>
                <div class="kpi-value">{value}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Suspicious Consumers Table + Scatter ──────────
    col_table, col_scatter = st.columns([1.2, 1])

    with col_table:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown("""
        <div class="section-header">
            <div class="icon">⚠️</div>
            <h3>Suspicious Consumer Rankings</h3>
            <span class="badge">TOP 20</span>
        </div>
        """, unsafe_allow_html=True)

        # Filter controls
        risk_filter = st.selectbox("Filter by Risk",
                                   ["All", "High Risk (>0.75)", "Medium (0.5–0.75)", "Normal (<0.5)"],
                                   key="anom_risk_filter")
        city_filter = st.multiselect("Filter by City", CITIES, default=[], key="anom_city")

        df_display = df_anom.copy()
        if risk_filter == "High Risk (>0.75)":
            df_display = df_display[df_display["risk_score"] > 0.75]
        elif risk_filter == "Medium (0.5–0.75)":
            df_display = df_display[(df_display["risk_score"] > 0.5) & (df_display["risk_score"] <= 0.75)]
        elif risk_filter == "Normal (<0.5)":
            df_display = df_display[df_display["risk_score"] <= 0.5]
        if city_filter:
            df_display = df_display[df_display["city"].isin(city_filter)]

        # Render as HTML table with badges
        table_rows = ""
        for _, row in df_display.head(15).iterrows():
            badge = _risk_badge(row["risk_score"])
            table_rows += f"""
            <tr>
                <td><strong>{row['consumer_id']}</strong></td>
                <td>{row['city']}</td>
                <td><span style="font-weight:700;color:#FF3366;">{row['risk_score']:.3f}</span></td>
                <td>{row['usage_deviation_pct']:.1f}%</td>
                <td>{badge}</td>
                <td style="font-size:0.78rem;">{row['anomaly_type']}</td>
            </tr>"""

        st.markdown(f"""
        <div style="overflow-x:auto;max-height:380px;overflow-y:auto;">
        <table style="width:100%;border-collapse:collapse;font-size:0.82rem;">
            <thead>
                <tr style="background:linear-gradient(135deg,#0066FF,#00D4FF);color:white;">
                    <th style="padding:0.6rem 0.8rem;text-align:left;">Consumer</th>
                    <th style="padding:0.6rem 0.8rem;text-align:left;">City</th>
                    <th style="padding:0.6rem 0.8rem;text-align:left;">Risk Score</th>
                    <th style="padding:0.6rem 0.8rem;text-align:left;">Deviation</th>
                    <th style="padding:0.6rem 0.8rem;text-align:left;">Status</th>
                    <th style="padding:0.6rem 0.8rem;text-align:left;">Type</th>
                </tr>
            </thead>
            <tbody>{table_rows}</tbody>
        </table>
        </div>
        """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with col_scatter:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown("""
        <div class="section-header">
            <div class="icon">🎯</div>
            <h3>Anomaly Risk Map</h3>
        </div>
        """, unsafe_allow_html=True)
        fig_scatter = scatter_anomaly_chart(df_anom)
        st.plotly_chart(fig_scatter, use_container_width=True, config={"displayModeBar": False})
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── AI Anomaly Detection on Time Series ───────────
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown("""
    <div class="section-header">
        <div class="icon">🔬</div>
        <h3>ML Anomaly Detection – Time Series Analysis</h3>
        <span class="badge">ISOLATION FOREST</span>
    </div>
    """, unsafe_allow_html=True)

    with st.spinner("Running Isolation Forest anomaly detection..."):
        df_ts = generate_hourly_series(days=7)
        # Add required columns for detector
        df_ts["voltage"] = np.random.normal(230, 5, len(df_ts))
        df_ts["power_factor"] = np.random.uniform(0.85, 0.99, len(df_ts))
        detector = AnomalyDetector(contamination=0.05)
        detector.train(df_ts)
        df_result = detector.predict(df_ts)

    import plotly.graph_objects as go
    anomaly_pts = df_result[df_result["anomaly_flag"] == 1]
    normal_pts  = df_result[df_result["anomaly_flag"] == 0]

    fig_ts = go.Figure()
    fig_ts.add_trace(go.Scatter(
        x=normal_pts["timestamp"], y=normal_pts["energy_kwh"],
        mode="lines", name="Normal", line=dict(color="#0066FF", width=1.5),
    ))
    fig_ts.add_trace(go.Scatter(
        x=anomaly_pts["timestamp"], y=anomaly_pts["energy_kwh"],
        mode="markers", name="⚠️ Anomaly",
        marker=dict(color="#FF3366", size=8, symbol="x",
                    line=dict(color="white", width=1.5)),
    ))
    fig_ts.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, sans-serif", size=12, color="#1e293b"),
        margin=dict(l=20, r=20, t=20, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        xaxis=dict(showgrid=True, gridcolor="rgba(0,102,255,0.08)"),
        yaxis=dict(showgrid=True, gridcolor="rgba(0,102,255,0.08)"),
    )
    st.plotly_chart(fig_ts, use_container_width=True, config={"displayModeBar": False})
    st.markdown(
        f'<div class="alert-info">ℹ️ Isolation Forest detected '
        f'<strong>{len(anomaly_pts)}</strong> anomalies out of '
        f'<strong>{len(df_result)}</strong> readings '
        f'({len(anomaly_pts)/len(df_result)*100:.1f}% contamination rate)</div>',
        unsafe_allow_html=True,
    )
    st.markdown('</div>', unsafe_allow_html=True)

    # ── City Risk Heatmap ─────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown("""
    <div class="section-header">
        <div class="icon">🗺️</div>
        <h3>High-Risk Area Heatmap – City × Anomaly Type</h3>
    </div>
    """, unsafe_allow_html=True)

    anom_types = ["Meter Tampering", "Usage Spike", "Off-Hours Activity",
                  "Voltage Irregularity", "Power Factor Drop"]
    records = []
    for city in CITIES:
        for atype in anom_types:
            records.append({
                "city": city, "anomaly_type": atype,
                "count": random.randint(0, 8),
            })
    df_city_anom = pd.DataFrame(records)
    fig_heat = heatmap_chart(df_city_anom, "anomaly_type", "city", "count",
                             title="Anomaly Count by City & Type")
    st.plotly_chart(fig_heat, use_container_width=True, config={"displayModeBar": False})
    st.markdown('</div>', unsafe_allow_html=True)

    # ── DB Anomalies Table ────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    with st.expander("🗄️ View Database Anomaly Logs"):
        df_db = query_df("SELECT * FROM anomalies ORDER BY detected_at DESC LIMIT 50")
        if not df_db.empty:
            status_filter = st.selectbox("Filter Status", ["All", "Open", "Investigating", "Resolved"],
                                         key="db_anom_status")
            if status_filter != "All":
                df_db = df_db[df_db["status"] == status_filter]
            st.dataframe(df_db, use_container_width=True, height=300)
            csv = df_db.to_csv(index=False).encode()
            st.download_button("⬇️ Export Anomaly CSV", csv, "anomalies.csv", "text/csv")
