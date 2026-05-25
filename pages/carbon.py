"""
EnergiX AI – Carbon Emission Analytics Page
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px

from utils.data_generator import generate_carbon_data
from utils.ml_models import compute_carbon_intensity
from utils.charts import gauge_chart, pie_chart, area_chart_multi


def show():
    st.markdown("""
    <div class="page-title-banner animate-fade-up">
        <span style="font-size:2rem;">🌿</span>
        <div>
            <h1>Carbon Emission Analytics</h1>
            <p>Carbon footprint tracking · Sustainability scoring · Green energy contribution analysis</p>
        </div>
        <div style="margin-left:auto;">
            <span class="ai-badge">🌱 ESG Certified</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Data ──────────────────────────────────────────
    df_carbon = generate_carbon_data(days=90)
    carbon_metrics = compute_carbon_intensity(df_carbon)

    total_co2     = carbon_metrics["total_co2_tonnes"]
    renewable_pct = carbon_metrics["renewable_pct"]
    intensity     = carbon_metrics["carbon_intensity_kg_mwh"]
    sust_score    = carbon_metrics["sustainability_score"]

    # ── KPI Row ───────────────────────────────────────
    col1, col2, col3, col4, col5 = st.columns(5)
    kpis = [
        ("💨", "Total CO₂ Emitted",    f"{total_co2:,.1f} t",    "kpi-card-red"),
        ("🌱", "Renewable Share",       f"{renewable_pct:.1f}%",  "kpi-card-green"),
        ("⚡", "Carbon Intensity",      f"{intensity:.1f} kg/MWh","kpi-card-orange"),
        ("🏆", "Sustainability Score",  f"{sust_score:.1f}/100",  "kpi-card-blue"),
        ("🌍", "Trees Equivalent",      f"{int(total_co2*45):,}", "kpi-card-green"),
    ]
    for col, (icon, label, value, cls) in zip([col1, col2, col3, col4, col5], kpis):
        with col:
            st.markdown(f"""
            <div class="kpi-card {cls} animate-fade-up">
                <span class="kpi-icon">{icon}</span>
                <div class="kpi-label">{label}</div>
                <div class="kpi-value">{value}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Sustainability Score + Goal ────────────────────
    if sust_score >= 70:
        st.markdown("""
        <div class="alert-success animate-fade-up">
            🌿 <strong>On Track:</strong> Sustainability score exceeds 70. You're meeting the 2030 clean energy targets.
            Continue expanding renewable capacity to reach 100% green by 2035.
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="alert-warning animate-fade-up">
            ⚠️ <strong>Below Target:</strong> Sustainability score is below 70. Increase renewable energy
            contribution to meet ESG commitments. Consider solar + wind expansion.
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Row: CO2 Trend + Sustainability Gauge ──────────
    col_trend, col_gauge = st.columns([3, 1])

    with col_trend:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown("""
        <div class="section-header">
            <div class="icon">📈</div>
            <h3>CO₂ Emission Trend – 90 Days</h3>
        </div>
        """, unsafe_allow_html=True)

        df_daily_co2 = df_carbon.groupby("date")["co2_tonnes"].sum().reset_index()
        df_daily_co2["date"] = pd.to_datetime(df_daily_co2["date"])

        # Add 7-day rolling average
        df_daily_co2["rolling_avg"] = df_daily_co2["co2_tonnes"].rolling(7, min_periods=1).mean()

        fig_co2 = go.Figure()
        fig_co2.add_trace(go.Scatter(
            x=df_daily_co2["date"], y=df_daily_co2["co2_tonnes"],
            name="Daily CO₂", mode="lines",
            line=dict(color="rgba(255,51,102,0.4)", width=1.5),
            fill="tozeroy", fillcolor="rgba(255,51,102,0.06)",
        ))
        fig_co2.add_trace(go.Scatter(
            x=df_daily_co2["date"], y=df_daily_co2["rolling_avg"],
            name="7-Day Avg", mode="lines",
            line=dict(color="#FF3366", width=2.5),
        ))
        fig_co2.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font=dict(family="Inter, sans-serif", size=12, color="#1e293b"),
            margin=dict(l=20, r=20, t=20, b=20),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            xaxis=dict(showgrid=True, gridcolor="rgba(0,102,255,0.08)"),
            yaxis=dict(showgrid=True, gridcolor="rgba(0,102,255,0.08)", title="CO₂ Tonnes"),
        )
        st.plotly_chart(fig_co2, use_container_width=True, config={"displayModeBar": False})
        st.markdown('</div>', unsafe_allow_html=True)

    with col_gauge:
        st.markdown('<div class="glass-card" style="margin-bottom:1rem;">', unsafe_allow_html=True)
        st.markdown("""
        <div class="section-header">
            <div class="icon">🏆</div>
            <h3>Sustainability Score</h3>
        </div>
        """, unsafe_allow_html=True)
        fig_g = gauge_chart(sust_score, "Sustainability Index", 0, 100, 70)
        st.plotly_chart(fig_g, use_container_width=True, config={"displayModeBar": False})
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown("""
        <div class="kpi-label">🌿 Green Rating</div>
        """, unsafe_allow_html=True)
        rating = "🌟 Excellent" if sust_score >= 80 else ("✅ Good" if sust_score >= 65 else "⚠️ Needs Work")
        color  = "#00C853" if sust_score >= 80 else ("#FF6B35" if sust_score >= 65 else "#FF3366")
        st.markdown(f"""
        <div style="font-size:1.4rem;font-weight:800;color:{color};margin:0.5rem 0;">
            {rating}
        </div>
        <div style="font-size:0.8rem;color:#475569;">
            Renewable: <strong>{renewable_pct:.1f}%</strong><br>
            Intensity: <strong>{intensity:.1f} kg/MWh</strong>
        </div>
        """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # ── Row: Renewable vs Non-Renewable ───────────────
    st.markdown("<br>", unsafe_allow_html=True)
    col_area, col_pie = st.columns([2, 1])

    with col_area:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown("""
        <div class="section-header">
            <div class="icon">⚡</div>
            <h3>Renewable vs Non-Renewable Energy Mix</h3>
        </div>
        """, unsafe_allow_html=True)

        df_daily_src = df_carbon.copy()
        df_daily_src["date"] = pd.to_datetime(df_daily_src["date"])
        df_renew = df_daily_src.groupby(["date","is_renewable"])["energy_mwh"].sum().reset_index()
        df_ren   = df_renew[df_renew["is_renewable"] == True].rename(columns={"energy_mwh":"renewable"})
        df_non   = df_renew[df_renew["is_renewable"] == False].rename(columns={"energy_mwh":"non_renewable"})
        df_mix   = df_ren[["date","renewable"]].merge(df_non[["date","non_renewable"]], on="date", how="outer").fillna(0)

        fig_mix = go.Figure()
        fig_mix.add_trace(go.Scatter(
            x=df_mix["date"], y=df_mix["renewable"],
            name="🌱 Renewable", mode="lines",
            line=dict(color="#00C853", width=2),
            fill="tozeroy", fillcolor="rgba(0,200,83,0.1)",
        ))
        fig_mix.add_trace(go.Scatter(
            x=df_mix["date"], y=df_mix["non_renewable"],
            name="⛽ Non-Renewable", mode="lines",
            line=dict(color="#FF3366", width=2),
            fill="tonexty", fillcolor="rgba(255,51,102,0.08)",
        ))
        fig_mix.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font=dict(family="Inter, sans-serif", size=12, color="#1e293b"),
            margin=dict(l=20, r=20, t=20, b=20),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            xaxis=dict(showgrid=True, gridcolor="rgba(0,102,255,0.08)"),
            yaxis=dict(showgrid=True, gridcolor="rgba(0,102,255,0.08)", title="Energy (MWh)"),
        )
        st.plotly_chart(fig_mix, use_container_width=True, config={"displayModeBar": False})
        st.markdown('</div>', unsafe_allow_html=True)

    with col_pie:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown("""
        <div class="section-header">
            <div class="icon">🥧</div>
            <h3>Energy Source Breakdown</h3>
        </div>
        """, unsafe_allow_html=True)
        df_src_agg = df_carbon.groupby("source")["energy_mwh"].sum().reset_index()
        colors_src = ["#FF3366","#FF6B35","#FFD700","#00C853","#0066FF","#00D4FF"]
        fig_src = go.Figure(go.Pie(
            labels=df_src_agg["source"],
            values=df_src_agg["energy_mwh"],
            hole=0.4,
            marker=dict(colors=colors_src, line=dict(color="white", width=2)),
            textinfo="label+percent",
        ))
        fig_src.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(family="Inter, sans-serif"),
            margin=dict(l=10, r=10, t=10, b=10),
            legend=dict(orientation="v", font=dict(size=11)),
        )
        st.plotly_chart(fig_src, use_container_width=True, config={"displayModeBar": False})
        st.markdown('</div>', unsafe_allow_html=True)

    # ── CO2 by Source Stack ───────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown("""
    <div class="section-header">
        <div class="icon">📊</div>
        <h3>CO₂ Emission by Energy Source – 90 Days</h3>
        <span class="badge">STACKED VIEW</span>
    </div>
    """, unsafe_allow_html=True)

    df_pivot = df_carbon.pivot_table(
        index="date", columns="source", values="co2_tonnes", aggfunc="sum"
    ).reset_index()
    df_pivot["date"] = pd.to_datetime(df_pivot["date"])

    sources = ["Coal", "Natural Gas", "Solar", "Wind", "Hydro", "Nuclear"]
    src_colors = {"Coal":"#FF3366","Natural Gas":"#FF6B35","Solar":"#FFD700",
                  "Wind":"#00C853","Hydro":"#0066FF","Nuclear":"#A855F7"}

    fig_stack = go.Figure()
    for src in sources:
        if src in df_pivot.columns:
            fig_stack.add_trace(go.Bar(
                x=df_pivot["date"], y=df_pivot[src],
                name=src, marker_color=src_colors.get(src, "#888"),
            ))
    fig_stack.update_layout(
        barmode="stack",
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, sans-serif", size=12, color="#1e293b"),
        margin=dict(l=20, r=20, t=20, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        xaxis=dict(showgrid=True, gridcolor="rgba(0,102,255,0.08)"),
        yaxis=dict(showgrid=True, gridcolor="rgba(0,102,255,0.08)", title="CO₂ Tonnes"),
    )
    st.plotly_chart(fig_stack, use_container_width=True, config={"displayModeBar": False})
    st.markdown('</div>', unsafe_allow_html=True)

    # ── Environmental Impact Summary ──────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown("""
    <div class="section-header">
        <div class="icon">🌍</div>
        <h3>Environmental Impact Summary</h3>
    </div>
    """, unsafe_allow_html=True)

    col_e1, col_e2, col_e3, col_e4 = st.columns(4)
    impacts = [
        ("🌳", "Trees Needed to Offset",  f"{int(total_co2 * 45):,}", "trees/year"),
        ("🚗", "Car Equivalent Emissions", f"{int(total_co2 / 0.21):,}", "km driven"),
        ("✈️", "Flight Equivalent",        f"{int(total_co2 / 0.255):,}", "passenger km"),
        ("🏠", "Homes Powered (clean)",    f"{int(df_carbon[df_carbon.is_renewable]['energy_mwh'].sum() / 10.5):,}", "homes/year"),
    ]
    for col, (icon, label, val, unit) in zip([col_e1, col_e2, col_e3, col_e4], impacts):
        with col:
            st.markdown(f"""
            <div class="glass-card" style="text-align:center;padding:1.25rem 0.75rem;">
                <div style="font-size:2rem;">{icon}</div>
                <div class="kpi-label" style="margin:0.35rem 0;">{label}</div>
                <div style="font-size:1.5rem;font-weight:800;color:#0066FF;">{val}</div>
                <div style="font-size:0.75rem;color:#94a3b8;">{unit}</div>
            </div>
            """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
