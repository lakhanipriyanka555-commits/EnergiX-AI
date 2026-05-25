"""
EnergiX AI – AI Forecasting Page
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random

from utils.data_generator import generate_hourly_series, generate_forecast_data
from utils.ml_models import EnergyForecaster
from utils.charts import forecast_chart, line_chart, bar_chart
from config import CITIES


def show():
    st.markdown("""
    <div class="page-title-banner animate-fade-up">
        <span style="font-size:2rem;">🤖</span>
        <div>
            <h1>AI Demand Forecasting</h1>
            <p>Gradient-Boosting ML model · 24-hour ahead prediction with confidence intervals</p>
        </div>
        <div style="margin-left:auto;">
            <span class="ai-badge">⚡ GBR Model v2.1</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Filters ───────────────────────────────────────
    col_f1, col_f2, col_f3, col_f4 = st.columns(4)
    with col_f1:
        selected_city = st.selectbox("🏙️ Select City", CITIES, key="fc_city")
    with col_f2:
        forecast_hours = st.slider("⏱️ Forecast Window (hrs)", 6, 48, 24, key="fc_hours")
    with col_f3:
        forecast_date = st.date_input("📅 Start Date", datetime.now().date(), key="fc_date")
    with col_f4:
        confidence_threshold = st.slider("🎯 Confidence Threshold %", 70, 99, 85, key="fc_conf")

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Train model ───────────────────────────────────
    with st.spinner("🤖 Training AI Forecasting Model..."):
        df_raw = generate_hourly_series(days=30)
        forecaster = EnergyForecaster()
        forecaster.train(df_raw)
        r2 = forecaster.score(df_raw)

    # ── Model Stats Banner ────────────────────────────
    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
    stats = [
        ("🎯", "Model Accuracy (R²)", f"{r2:.4f}", "#0066FF"),
        ("📊", "Training Samples",   f"{len(df_raw):,}", "#00D4FF"),
        ("⚡", "Forecast Horizon",   f"{forecast_hours}h", "#00FF88"),
        ("🏙️", "City",             selected_city, "#A855F7"),
    ]
    for col, (icon, label, val, color) in zip([col_m1, col_m2, col_m3, col_m4], stats):
        with col:
            st.markdown(f"""
            <div class="glass-card" style="text-align:center;padding:1rem;">
                <div style="font-size:1.5rem;">{icon}</div>
                <div class="kpi-label" style="margin-top:0.25rem;">{label}</div>
                <div style="font-size:1.4rem;font-weight:800;color:{color};">{val}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Forecast Chart ────────────────────────────────
    hist_df, pred_df = generate_forecast_data(hours=forecast_hours)
    # Filter by confidence threshold
    pred_df_filtered = pred_df[pred_df["confidence"] >= confidence_threshold].copy()

    col_chart, col_info = st.columns([3, 1])

    with col_chart:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown(f"""
        <div class="section-header">
            <div class="icon">📈</div>
            <h3>24-Hour AI Demand Forecast – {selected_city}</h3>
            <span class="badge">LIVE MODEL</span>
        </div>
        """, unsafe_allow_html=True)

        fig_fc = forecast_chart(hist_df, pred_df)
        st.plotly_chart(fig_fc, use_container_width=True, config={"displayModeBar": False})
        st.markdown('</div>', unsafe_allow_html=True)

    with col_info:
        # Peak hour prediction
        peak_idx  = pred_df["energy_kwh"].idxmax()
        peak_time = pred_df.loc[peak_idx, "timestamp"]
        peak_val  = pred_df.loc[peak_idx, "energy_kwh"]
        avg_conf  = pred_df["confidence"].mean()
        valley_idx  = pred_df["energy_kwh"].idxmin()
        valley_time = pred_df.loc[valley_idx, "timestamp"]

        st.markdown(f"""
        <div class="glass-card" style="margin-bottom:1rem;">
            <div class="kpi-label">⚡ Peak Hour</div>
            <div style="font-size:1.6rem;font-weight:800;color:#FF6B35;">
                {peak_time.strftime('%H:%M')}
            </div>
            <div style="font-size:0.85rem;color:#475569;">{peak_val:.1f} kWh predicted</div>
        </div>

        <div class="glass-card" style="margin-bottom:1rem;">
            <div class="kpi-label">🌙 Valley Hour</div>
            <div style="font-size:1.6rem;font-weight:800;color:#00D4FF;">
                {valley_time.strftime('%H:%M')}
            </div>
            <div style="font-size:0.85rem;color:#475569;">Lowest demand expected</div>
        </div>

        <div class="glass-card" style="margin-bottom:1rem;">
            <div class="kpi-label">🎯 Avg Confidence</div>
            <div style="font-size:1.6rem;font-weight:800;color:#00C853;">
                {avg_conf:.1f}%
            </div>
        </div>

        <div class="glass-card">
            <div class="kpi-label">📋 Points Above Threshold</div>
            <div style="font-size:1.6rem;font-weight:800;color:#A855F7;">
                {len(pred_df_filtered)}/{len(pred_df)}
            </div>
            <div style="font-size:0.8rem;color:#475569;">≥ {confidence_threshold}% confidence</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Historical vs Predicted Comparison ────────────
    col_hist, col_hour = st.columns(2)

    with col_hist:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown("""
        <div class="section-header">
            <div class="icon">📉</div>
            <h3>Historical vs Predicted Comparison</h3>
        </div>
        """, unsafe_allow_html=True)
        import plotly.graph_objects as go
        fig_comp = go.Figure()
        fig_comp.add_trace(go.Scatter(
            x=hist_df["timestamp"].tail(24), y=hist_df["energy_kwh"].tail(24),
            name="Historical", line=dict(color="#0066FF", width=2),
            mode="lines+markers", marker=dict(size=4),
        ))
        fig_comp.add_trace(go.Scatter(
            x=pred_df["timestamp"], y=pred_df["energy_kwh"],
            name="AI Forecast", line=dict(color="#00D4FF", width=2, dash="dot"),
            mode="lines+markers", marker=dict(size=4),
        ))
        fig_comp.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font=dict(family="Inter, sans-serif", size=12, color="#1e293b"),
            margin=dict(l=20, r=20, t=20, b=20),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            xaxis=dict(showgrid=True, gridcolor="rgba(0,102,255,0.08)"),
            yaxis=dict(showgrid=True, gridcolor="rgba(0,102,255,0.08)"),
        )
        st.plotly_chart(fig_comp, use_container_width=True, config={"displayModeBar": False})
        st.markdown('</div>', unsafe_allow_html=True)

    with col_hour:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown("""
        <div class="section-header">
            <div class="icon">⏰</div>
            <h3>Hourly Forecast Confidence</h3>
        </div>
        """, unsafe_allow_html=True)
        import plotly.graph_objects as go
        colors = ["#00C853" if c >= confidence_threshold else "#FF6B35"
                  for c in pred_df["confidence"]]
        fig_conf = go.Figure(go.Bar(
            x=pred_df["timestamp"].dt.strftime("%H:%M"),
            y=pred_df["confidence"],
            marker_color=colors,
            hovertemplate="Hour: %{x}<br>Confidence: %{y:.1f}%<extra></extra>",
        ))
        fig_conf.add_hline(y=confidence_threshold, line_dash="dash",
                           line_color="#FF3366", annotation_text=f"Threshold {confidence_threshold}%")
        fig_conf.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font=dict(family="Inter, sans-serif", size=11, color="#1e293b"),
            margin=dict(l=20, r=20, t=20, b=40),
            yaxis=dict(range=[50, 100], showgrid=True, gridcolor="rgba(0,102,255,0.08)"),
            xaxis=dict(showgrid=False, tickangle=-45),
        )
        st.plotly_chart(fig_conf, use_container_width=True, config={"displayModeBar": False})
        st.markdown('</div>', unsafe_allow_html=True)

    # ── AI Recommendation Engine ──────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown("""
    <div class="section-header">
        <div class="icon">🤖</div>
        <h3>AI Recommendation Engine</h3>
        <span class="badge">GPT-ENHANCED</span>
    </div>
    """, unsafe_allow_html=True)

    recs = [
        ("🏭", "Load Shift Industrial Units",
         f"Schedule heavy industrial loads away from peak at {peak_time.strftime('%H:%M')}. "
         f"Estimated grid relief: 12–18%."),
        ("❄️", "Pre-cool HVAC Systems",
         f"Pre-cool buildings 2 hours before peak demand. Reduces peak HVAC load by ~22%."),
        ("🔋", "Activate Battery Storage",
         f"Discharge storage batteries during {peak_time.strftime('%H:%M')}–{(peak_time + timedelta(hours=2)).strftime('%H:%M')} "
         f"to avoid grid stress."),
        ("⚡", "Enable Demand Response",
         f"Send demand response signals to {random.randint(8, 20)} enrolled consumers "
         f"for voluntary load reduction."),
    ]
    cols_rec = st.columns(2)
    for i, (icon, title, desc) in enumerate(recs):
        with cols_rec[i % 2]:
            st.markdown(f"""
            <div class="rec-card" style="margin-bottom:0.75rem;">
                <div class="rec-icon rec-icon-{'blue' if i%2==0 else 'green'}">
                    {icon}
                </div>
                <div>
                    <div class="rec-title">{title}</div>
                    <div class="rec-desc">{desc}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

    # ── Forecast Data Table ───────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    with st.expander("📋 View Raw Forecast Data"):
        display_df = pred_df[["timestamp", "energy_kwh", "upper", "lower", "confidence"]].copy()
        display_df.columns = ["Timestamp", "Predicted kWh", "Upper Bound", "Lower Bound", "Confidence %"]
        display_df["Timestamp"] = display_df["Timestamp"].dt.strftime("%Y-%m-%d %H:%M")
        st.dataframe(display_df, use_container_width=True, height=300)

        csv = display_df.to_csv(index=False).encode()
        st.download_button("⬇️ Export Forecast CSV", csv, "forecast_data.csv", "text/csv")
