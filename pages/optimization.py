"""
EnergiX AI – Smart Optimization Page
"""

import streamlit as st
import pandas as pd
import numpy as np
import random

from utils.data_generator import generate_optimization_data
from utils.ml_models import compute_efficiency_score
from utils.charts import optimization_bar, gauge_chart


def show():
    st.markdown("""
    <div class="page-title-banner animate-fade-up">
        <span style="font-size:2rem;">⚡</span>
        <div>
            <h1>Smart Optimization Engine</h1>
            <p>AI-driven energy saving recommendations · Cost reduction analytics · Peak-hour optimization</p>
        </div>
        <div style="margin-left:auto;">
            <span class="ai-badge">💡 AI Advisor</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Data ──────────────────────────────────────────
    df_opt = generate_optimization_data()
    total_before  = df_opt["before_kwh"].sum()
    total_after   = df_opt["after_kwh"].sum()
    total_saved   = total_before - total_after
    total_cost_saved = df_opt["cost_saved_usd"].sum()
    avg_savings_pct  = df_opt["savings_pct"].mean()

    # ── KPI Row ───────────────────────────────────────
    col1, col2, col3, col4 = st.columns(4)
    kpis = [
        ("💡", "Total Energy Saved",   f"{total_saved:.1f} kWh",  "kpi-card-green"),
        ("💰", "Cost Reduction",       f"${total_cost_saved:.2f}", "kpi-card-blue"),
        ("📉", "Avg Savings Rate",     f"{avg_savings_pct:.1f}%",  "kpi-card-cyan"),
        ("🌿", "CO₂ Avoided",         f"{total_saved*0.45:.1f} kg","kpi-card-green"),
    ]
    for col, (icon, label, value, cls) in zip([col1, col2, col3, col4], kpis):
        with col:
            st.markdown(f"""
            <div class="kpi-card {cls} animate-fade-up">
                <span class="kpi-icon">{icon}</span>
                <div class="kpi-label">{label}</div>
                <div class="kpi-value">{value}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── AI Recommendations ────────────────────────────
    col_rec, col_gauge = st.columns([2, 1])

    with col_rec:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown("""
        <div class="section-header">
            <div class="icon">🤖</div>
            <h3>AI Energy Saving Recommendations</h3>
            <span class="badge">PRIORITY SORTED</span>
        </div>
        """, unsafe_allow_html=True)

        recommendations = [
            ("💨", "rec-icon-green",  "Optimize HVAC Scheduling",
             "Shift HVAC operations to off-peak hours (10PM–6AM). Use smart thermostats for 2°C pre-cooling.",
             "~$420/month savings", "High Impact"),
            ("💡", "rec-icon-blue",   "Smart Lighting Control",
             "Install occupancy sensors in low-traffic zones. Dim non-critical lighting by 40% after 8PM.",
             "~$180/month savings", "Medium Impact"),
            ("🔋", "rec-icon-purple", "Battery Storage Optimization",
             "Charge storage batteries during valley hours (2–5AM). Discharge during peak (5–8PM) to avoid demand charges.",
             "~$650/month savings", "High Impact"),
            ("🏭", "rec-icon-orange", "Industrial Load Curtailment",
             "Enroll top 5 industrial consumers in demand response program. Reduce load by 15% during peaks.",
             "~$890/month savings", "Critical Impact"),
            ("☀️", "rec-icon-green",  "Solar Self-Consumption Boost",
             "Shift flexible loads (EV charging, water heating) to solar peak hours (10AM–2PM).",
             "~$310/month savings", "Medium Impact"),
            ("⚙️", "rec-icon-blue",   "Power Factor Correction",
             "Install capacitor banks at 3 industrial sites with PF < 0.88. Reduces reactive power charges.",
             "~$220/month savings", "Low Impact"),
        ]

        for icon, icon_cls, title, desc, saving, impact in recommendations:
            impact_color = {"Critical Impact":"#FF3366","High Impact":"#FF6B35",
                            "Medium Impact":"#0066FF","Low Impact":"#00C853"}.get(impact, "#0066FF")
            st.markdown(f"""
            <div class="rec-card" style="margin-bottom:0.75rem;">
                <div class="rec-icon {icon_cls}">{icon}</div>
                <div style="flex:1;">
                    <div style="display:flex;align-items:center;gap:0.5rem;margin-bottom:0.3rem;">
                        <div class="rec-title">{title}</div>
                        <span style="font-size:0.68rem;font-weight:700;padding:0.15rem 0.5rem;
                              border-radius:100px;background:rgba(0,0,0,0.05);color:{impact_color};">
                            {impact}
                        </span>
                    </div>
                    <div class="rec-desc">{desc}</div>
                    <div class="rec-saving" style="margin-top:0.3rem;">💰 {saving}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with col_gauge:
        # Efficiency Score Gauge
        eff_score = round(compute_efficiency_score(
            pd.DataFrame({"energy_kwh": np.random.normal(100, 15, 100),
                          "power_factor": np.random.uniform(0.88, 0.99, 100)})
        ), 1)

        st.markdown('<div class="glass-card" style="margin-bottom:1rem;">', unsafe_allow_html=True)
        st.markdown("""
        <div class="section-header">
            <div class="icon">⚡</div>
            <h3>Efficiency Score</h3>
        </div>
        """, unsafe_allow_html=True)
        fig_gauge = gauge_chart(eff_score, "Energy Efficiency", 0, 100, 75)
        st.plotly_chart(fig_gauge, use_container_width=True, config={"displayModeBar": False})
        st.markdown(f"""
        <div class="alert-{'success' if eff_score >= 75 else 'warning'}">
            {'✅ Good efficiency! Implement recommendations to reach 90+.' if eff_score >= 75
             else '⚠️ Below target. Critical optimizations needed.'}
        </div>
        """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        # Savings Calculator
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown("""
        <div class="section-header">
            <div class="icon">🧮</div>
            <h3>Savings Calculator</h3>
        </div>
        """, unsafe_allow_html=True)
        monthly_kwh  = st.number_input("Monthly kWh", value=50000, step=1000, key="calc_kwh")
        tariff_rate  = st.number_input("Tariff ($/kWh)", value=0.15, step=0.01, key="calc_tariff")
        reduction_pct = st.slider("Reduction Target %", 5, 40, 20, key="calc_pct")

        kwh_saved     = monthly_kwh * reduction_pct / 100
        dollar_saved  = kwh_saved * tariff_rate
        co2_avoided   = kwh_saved * 0.45

        st.markdown(f"""
        <div style="margin-top:0.75rem;">
            <div style="display:flex;justify-content:space-between;padding:0.4rem 0;
                 border-bottom:1px solid rgba(0,102,255,0.1);">
                <span style="font-size:0.82rem;color:#475569;">kWh Saved/Month</span>
                <strong style="color:#00C853;">{kwh_saved:,.0f} kWh</strong>
            </div>
            <div style="display:flex;justify-content:space-between;padding:0.4rem 0;
                 border-bottom:1px solid rgba(0,102,255,0.1);">
                <span style="font-size:0.82rem;color:#475569;">Cost Saved/Month</span>
                <strong style="color:#0066FF;">${dollar_saved:,.2f}</strong>
            </div>
            <div style="display:flex;justify-content:space-between;padding:0.4rem 0;
                 border-bottom:1px solid rgba(0,102,255,0.1);">
                <span style="font-size:0.82rem;color:#475569;">Annual Savings</span>
                <strong style="color:#A855F7;">${dollar_saved*12:,.2f}</strong>
            </div>
            <div style="display:flex;justify-content:space-between;padding:0.4rem 0;">
                <span style="font-size:0.82rem;color:#475569;">CO₂ Avoided/Month</span>
                <strong style="color:#00FF88;">{co2_avoided:,.1f} kg</strong>
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # ── Before vs After Chart ─────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown("""
    <div class="section-header">
        <div class="icon">📊</div>
        <h3>Energy Optimization – Before vs After Comparison</h3>
        <span class="badge">AI MODELED</span>
    </div>
    """, unsafe_allow_html=True)
    fig_opt = optimization_bar(df_opt)
    st.plotly_chart(fig_opt, use_container_width=True, config={"displayModeBar": False})
    st.markdown('</div>', unsafe_allow_html=True)

    # ── Smart Appliance Scheduling ────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown("""
    <div class="section-header">
        <div class="icon">📅</div>
        <h3>Smart Appliance Scheduling Suggestions</h3>
    </div>
    """, unsafe_allow_html=True)

    schedule_data = {
        "Appliance": ["Industrial Compressors", "EV Charging Stations", "Water Heaters",
                      "HVAC Pre-cooling", "Data Center Backup", "Irrigation Pumps"],
        "Current Schedule": ["08:00–18:00", "17:00–22:00", "06:00–09:00",
                              "As needed", "Always on", "06:00–12:00"],
        "Recommended": ["22:00–06:00", "00:00–05:00", "00:00–05:00",
                        "08:00–10:00", "02:00–06:00", "22:00–04:00"],
        "Est. Savings/Month": ["$1,240", "$380", "$165", "$290", "$510", "$95"],
        "Priority": ["🔴 Critical", "🟠 High", "🟡 Medium", "🟠 High", "🟡 Medium", "🟢 Low"],
    }
    df_sched = pd.DataFrame(schedule_data)
    st.dataframe(df_sched, use_container_width=True, hide_index=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # ── Peak Hour Optimization ────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    col_peak1, col_peak2 = st.columns(2)
    with col_peak1:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown("""
        <div class="section-header">
            <div class="icon">⏰</div>
            <h3>Peak-Hour Optimization Map</h3>
        </div>
        """, unsafe_allow_html=True)
        hours = list(range(24))
        load = [40,35,30,28,27,30,45,65,80,88,90,92,88,82,80,85,91,95,90,80,70,60,50,44]
        import plotly.graph_objects as go
        colors = ["#FF3366" if l >= 88 else ("#FF6B35" if l >= 75 else "#00C853") for l in load]
        fig_peak = go.Figure(go.Bar(
            x=[f"{h:02d}:00" for h in hours], y=load,
            marker_color=colors,
            hovertemplate="Hour: %{x}<br>Load: %{y}%<extra></extra>",
        ))
        fig_peak.add_hline(y=85, line_dash="dash", line_color="#FF3366",
                           annotation_text="Peak Threshold 85%")
        fig_peak.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font=dict(family="Inter, sans-serif", size=11, color="#1e293b"),
            margin=dict(l=20, r=20, t=20, b=40),
            yaxis=dict(title="Grid Load %", range=[0,110],
                       showgrid=True, gridcolor="rgba(0,102,255,0.08)"),
            xaxis=dict(tickangle=-45, showgrid=False),
        )
        st.plotly_chart(fig_peak, use_container_width=True, config={"displayModeBar": False})
        st.markdown('</div>', unsafe_allow_html=True)

    with col_peak2:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown("""
        <div class="section-header">
            <div class="icon">💹</div>
            <h3>Savings by Category</h3>
        </div>
        """, unsafe_allow_html=True)
        fig_sav = go.Figure(go.Bar(
            x=df_opt["savings_pct"], y=df_opt["category"],
            orientation="h",
            marker=dict(
                color=df_opt["savings_pct"],
                colorscale=[[0,"#00D4FF"],[0.5,"#0066FF"],[1,"#00FF88"]],
                showscale=False,
            ),
            text=[f"{v:.1f}%" for v in df_opt["savings_pct"]],
            textposition="outside",
            hovertemplate="%{y}: %{x:.1f}% saved<extra></extra>",
        ))
        fig_sav.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font=dict(family="Inter, sans-serif", size=12, color="#1e293b"),
            margin=dict(l=20, r=60, t=20, b=20),
            xaxis=dict(range=[0,50], title="Savings %",
                       showgrid=True, gridcolor="rgba(0,102,255,0.08)"),
            yaxis=dict(showgrid=False),
        )
        st.plotly_chart(fig_sav, use_container_width=True, config={"displayModeBar": False})

        # Savings table
        st.markdown("<br>", unsafe_allow_html=True)
        st.dataframe(
            df_opt[["category","before_kwh","after_kwh","savings_pct","cost_saved_usd"]].rename(columns={
                "category":"Category","before_kwh":"Before (kWh)","after_kwh":"After (kWh)",
                "savings_pct":"Savings %","cost_saved_usd":"Cost Saved ($)"
            }),
            use_container_width=True, hide_index=True,
        )
        st.markdown('</div>', unsafe_allow_html=True)
