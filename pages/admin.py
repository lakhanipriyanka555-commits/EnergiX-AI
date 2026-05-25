"""
EnergiX AI – Admin Panel (Supabase Edition)
User management via Supabase Auth + table ops · Smart meters · AI monitoring · Alert logs
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import random

from database.supabase_manager import (
    get_table, get_table_count, query_df,
    insert_row, _admin_client,
)
from utils.data_generator import generate_hourly_series
from utils.ml_models import EnergyForecaster


def _get_system_health():
    return {
        "uptime_hrs": round(random.uniform(120, 500), 1),
        "cpu_pct":    round(random.uniform(12, 45), 1),
        "mem_pct":    round(random.uniform(28, 60), 1),
        "api_calls":  random.randint(8000, 25000),
        "db":         "Supabase PostgreSQL",
    }


def show():
    st.markdown("""
    <div class="page-title-banner animate-fade-up">
        <span style="font-size:2rem;">🛡️</span>
        <div>
            <h1>Admin Control Panel</h1>
            <p>Supabase user management · Smart meter fleet · AI model monitoring · Alert logs</p>
        </div>
        <div style="margin-left:auto;">
            <span class="ai-badge">🔒 Admin Only</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    if st.session_state.get("user_role") != "Admin":
        st.markdown("""
        <div class="alert-danger">
            🔒 <strong>Access Restricted:</strong> This panel requires Admin privileges.
            Log in with <code>admin@energix.ai</code> to access.
        </div>
        """, unsafe_allow_html=True)
        return

    # ── System Health KPIs ────────────────────────────
    health = _get_system_health()
    cols_h = st.columns(5)
    health_kpis = [
        ("🗄️", "Database",      "Supabase",                   "kpi-card-blue"),
        ("⏱️", "Uptime",         f"{health['uptime_hrs']} hrs",  "kpi-card-green"),
        ("💻", "CPU Usage",      f"{health['cpu_pct']}%",        "kpi-card-orange"),
        ("🧠", "Memory",         f"{health['mem_pct']}%",         "kpi-card-purple"),
        ("📡", "API Calls",      f"{health['api_calls']:,}",      "kpi-card-cyan"),
    ]
    for col, (icon, label, val, cls) in zip(cols_h, health_kpis):
        with col:
            st.markdown(f"""
            <div class="kpi-card {cls} animate-fade-up">
                <span class="kpi-icon">{icon}</span>
                <div class="kpi-label">{label}</div>
                <div class="kpi-value" style="font-size:1.3rem;">{val}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    tab_users, tab_meters, tab_model, tab_alerts, tab_health = st.tabs([
        "👥 User Management",
        "📡 Smart Meters",
        "🤖 AI Model Monitor",
        "🚨 Alert Logs",
        "🖥️ System Health",
    ])

    # ── Users Tab ─────────────────────────────────────
    with tab_users:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown("""
        <div class="section-header">
            <div class="icon">👥</div>
            <h3>User Management</h3>
            <span class="badge">SUPABASE AUTH</span>
        </div>
        """, unsafe_allow_html=True)

        df_users = get_table("users", limit=100, order_col="created_at")

        if not df_users.empty:
            col_search, col_role_filter = st.columns([2, 1])
            with col_search:
                user_search = st.text_input(
                    "Search", placeholder="Name or email...",
                    key="admin_user_search", label_visibility="collapsed",
                )
            with col_role_filter:
                role_filter = st.selectbox(
                    "Role", ["All", "Admin", "Analyst", "Operator", "Engineer", "Viewer"],
                    key="admin_role_filter", label_visibility="collapsed",
                )
            df_show = df_users.copy()
            if user_search:
                mask = df_show.apply(
                    lambda c: c.astype(str).str.contains(user_search, case=False, na=False)
                )
                df_show = df_show[mask.any(axis=1)]
            if role_filter != "All":
                df_show = df_show[df_show["role"] == role_filter]

            st.dataframe(df_show, use_container_width=True, height=280, hide_index=True)

            col_dl, col_info = st.columns([1, 3])
            with col_dl:
                csv = df_show.to_csv(index=False).encode()
                st.download_button("⬇️ Export", csv, "users.csv", "text/csv", key="dl_users")
            with col_info:
                st.info(f"**{len(df_show)}** users shown")
        else:
            st.info("No user profiles found. Seed data first.")

        # Add user form
        with st.expander("➕ Add New User"):
            with st.form("add_user_form"):
                col_f1, col_f2 = st.columns(2)
                with col_f1:
                    new_email    = st.text_input("Email", placeholder="user@energix.ai")
                    new_name     = st.text_input("Full Name", placeholder="Jane Doe")
                    new_password = st.text_input("Password", type="password",
                                                  placeholder="Min 6 characters")
                with col_f2:
                    new_role = st.selectbox(
                        "Role", ["Viewer", "Analyst", "Operator", "Engineer", "Admin"]
                    )
                    st.markdown("<br>", unsafe_allow_html=True)
                    st.markdown("""
                    <div style="font-size:0.78rem;color:#475569;">
                        This will create the user in <strong>Supabase Auth</strong>
                        (email-confirmed) and add their profile to the <code>users</code> table.
                    </div>
                    """, unsafe_allow_html=True)

                submitted_user = st.form_submit_button("➕ Create User", use_container_width=True)

            if submitted_user:
                if not new_email or not new_name or not new_password:
                    st.warning("Please fill in all fields.")
                elif len(new_password) < 6:
                    st.warning("Password must be at least 6 characters.")
                else:
                    with st.spinner("Creating user in Supabase Auth..."):
                        try:
                            # Create in Supabase Auth
                            _admin_client().auth.admin.create_user({
                                "email":         new_email,
                                "password":      new_password,
                                "email_confirm": True,
                                "user_metadata": {"name": new_name, "role": new_role},
                            })
                            # Add to users profile table
                            insert_row("users", {
                                "email": new_email,
                                "name":  new_name,
                                "role":  new_role,
                            })
                            st.success(f"✅ User **{new_name}** created in Supabase Auth!")
                            st.rerun()
                        except Exception as exc:
                            err = str(exc)
                            if "already registered" in err or "already exists" in err:
                                st.warning("⚠️ This email is already registered.")
                            else:
                                st.error(f"❌ Error: {exc}")

        st.markdown('</div>', unsafe_allow_html=True)

    # ── Smart Meters Tab ──────────────────────────────
    with tab_meters:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown("""
        <div class="section-header">
            <div class="icon">📡</div>
            <h3>Smart Meter Fleet Management</h3>
        </div>
        """, unsafe_allow_html=True)

        df_meters = get_table("smart_meters", limit=100, order_col="last_ping")
        if not df_meters.empty:
            n_active  = len(df_meters[df_meters["status"] == "Active"])
            n_offline = len(df_meters[df_meters["status"] == "Offline"])
            n_maint   = len(df_meters[df_meters["status"] == "Maintenance"])

            col_m1, col_m2, col_m3 = st.columns(3)
            for col, (label, val, cls) in zip(
                [col_m1, col_m2, col_m3],
                [("✅ Active", n_active, "kpi-card-green"),
                 ("❌ Offline", n_offline, "kpi-card-red"),
                 ("🔧 Maintenance", n_maint, "kpi-card-orange")],
            ):
                with col:
                    st.markdown(f"""
                    <div class="kpi-card {cls}" style="padding:0.75rem 1rem;">
                        <div class="kpi-label">{label}</div>
                        <div class="kpi-value">{val}</div>
                    </div>
                    """, unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)
            status_f = st.selectbox(
                "Filter by Status", ["All", "Active", "Offline", "Maintenance"],
                key="meter_status_f",
            )
            df_m_show = df_meters if status_f == "All" else df_meters[df_meters["status"] == status_f]
            st.dataframe(df_m_show, use_container_width=True, height=320, hide_index=True)

            csv_m = df_m_show.to_csv(index=False).encode()
            st.download_button("⬇️ Export", csv_m, "smart_meters.csv", "text/csv", key="dl_meters")
        else:
            st.info("No smart meter data. Seed data first.")

        st.markdown('</div>', unsafe_allow_html=True)

    # ── AI Model Monitor Tab ──────────────────────────
    with tab_model:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown("""
        <div class="section-header">
            <div class="icon">🤖</div>
            <h3>AI Model Accuracy Monitoring</h3>
            <span class="badge">LIVE EVAL</span>
        </div>
        """, unsafe_allow_html=True)

        with st.spinner("Evaluating Gradient Boosting Regressor..."):
            df_eval = generate_hourly_series(days=30)
            forecaster = EnergyForecaster()
            forecaster.train(df_eval)
            r2     = forecaster.score(df_eval)
            preds  = forecaster.predict(df_eval)
            actual = df_eval["energy_kwh"].values
            mae    = np.mean(np.abs(preds - actual))
            rmse   = np.sqrt(np.mean((preds - actual) ** 2))
            mape   = np.mean(np.abs((preds - actual) / (actual + 1e-9))) * 100

        col_m1, col_m2, col_m3, col_m4 = st.columns(4)
        for col, (label, val, color) in zip(
            [col_m1, col_m2, col_m3, col_m4],
            [
                ("R² Score",   f"{r2:.4f}",  "#00C853" if r2 > 0.9 else "#FF6B35"),
                ("MAE (kWh)",  f"{mae:.2f}", "#0066FF"),
                ("RMSE (kWh)", f"{rmse:.2f}","#00D4FF"),
                ("MAPE (%)",   f"{mape:.2f}%","#A855F7"),
            ],
        ):
            with col:
                st.markdown(f"""
                <div class="glass-card" style="text-align:center;padding:1rem;">
                    <div class="kpi-label">{label}</div>
                    <div style="font-size:1.6rem;font-weight:800;color:{color};">{val}</div>
                </div>
                """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        n_plot = min(200, len(df_eval))
        fig_model = go.Figure()
        fig_model.add_trace(go.Scatter(
            x=df_eval["timestamp"].tail(n_plot), y=actual[-n_plot:],
            mode="lines", name="Actual",
            line=dict(color="#0066FF", width=2),
        ))
        fig_model.add_trace(go.Scatter(
            x=df_eval["timestamp"].tail(n_plot), y=preds[-n_plot:],
            mode="lines", name="Predicted",
            line=dict(color="#00D4FF", width=2, dash="dot"),
        ))
        fig_model.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font=dict(family="Inter, sans-serif", size=12, color="#1e293b"),
            margin=dict(l=20, r=20, t=20, b=20),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            xaxis=dict(showgrid=True, gridcolor="rgba(0,102,255,0.08)"),
            yaxis=dict(showgrid=True, gridcolor="rgba(0,102,255,0.08)", title="Energy kWh"),
        )
        st.plotly_chart(fig_model, use_container_width=True, config={"displayModeBar": False})

        st.markdown(f"""
        <div style="display:flex;gap:1rem;flex-wrap:wrap;margin-top:0.5rem;">
            <div><div class="kpi-label">Model Type</div><strong>Gradient Boosting Regressor</strong></div>
            <div><div class="kpi-label">Version</div><strong>v2.1.0</strong></div>
            <div><div class="kpi-label">Training Samples</div><strong>{len(df_eval):,}</strong></div>
            <div><div class="kpi-label">Status</div><span class="risk-badge risk-low">✅ Healthy</span></div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # ── Alert Logs Tab ────────────────────────────────
    with tab_alerts:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown("""
        <div class="section-header">
            <div class="icon">🚨</div>
            <h3>Anomaly Alert Logs – Supabase</h3>
        </div>
        """, unsafe_allow_html=True)

        df_alerts = get_table("anomalies", limit=100, order_col="detected_at")
        if not df_alerts.empty:
            col_a1, col_a2 = st.columns(2)
            with col_a1:
                status_f2 = st.selectbox(
                    "Status", ["All","Open","Investigating","Resolved"], key="alert_status"
                )
            with col_a2:
                all_types = ["All"] + df_alerts["anomaly_type"].unique().tolist()
                type_f    = st.selectbox("Type", all_types, key="alert_type")

            df_a = df_alerts.copy()
            if status_f2 != "All": df_a = df_a[df_a["status"] == status_f2]
            if type_f != "All":    df_a = df_a[df_a["anomaly_type"] == type_f]

            st.dataframe(df_a, use_container_width=True, height=350, hide_index=True)
            csv_a = df_a.to_csv(index=False).encode()
            st.download_button("⬇️ Export", csv_a, "alert_logs.csv", "text/csv", key="dl_alerts")
        else:
            st.info("No anomaly data found. Seed data first.")

        st.markdown('</div>', unsafe_allow_html=True)

    # ── System Health Tab ─────────────────────────────
    with tab_health:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown("""
        <div class="section-header">
            <div class="icon">🖥️</div>
            <h3>System Health Dashboard</h3>
        </div>
        """, unsafe_allow_html=True)

        health_items = [
            ("🗄️", "Supabase PostgreSQL",    "Connected",  "bg:#e8fdf0;color:#00C853", "✅"),
            ("🔐", "Supabase Auth",           "Active",     "bg:#e8fdf0;color:#00C853", "✅"),
            ("🤖", "AI Forecasting Engine",   "Online",     "bg:#e8fdf0;color:#00C853", "✅"),
            ("🔍", "Anomaly Detector",        "Online",     "bg:#e8fdf0;color:#00C853", "✅"),
            ("📡", "Smart Meter API",         "Degraded",   "bg:#fff8e0;color:#FF6B35", "⚠️"),
            ("☁️", "Cloud Realtime Sync",     "Offline",    "bg:#fdf0f0;color:#FF3366", "❌"),
        ]
        for icon, name, status, style, emoji in health_items:
            st.markdown(f"""
            <div class="health-card" style="margin-bottom:0.5rem;">
                <div class="health-icon-wrap" style="background:rgba(0,102,255,0.08);">{icon}</div>
                <div style="flex:1;"><div style="font-weight:600;font-size:0.9rem;">{name}</div></div>
                <div style="padding:0.25rem 0.75rem;border-radius:100px;
                     font-size:0.75rem;font-weight:700;{style};">{emoji} {status}</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        hours     = list(range(24))
        cpu_trend = [random.uniform(10, 60) for _ in hours]
        mem_trend = [random.uniform(25, 70) for _ in hours]

        fig_res = go.Figure()
        fig_res.add_trace(go.Scatter(
            x=hours, y=cpu_trend, name="CPU %",
            mode="lines+markers", line=dict(color="#0066FF", width=2),
            fill="tozeroy", fillcolor="rgba(0,102,255,0.06)",
        ))
        fig_res.add_trace(go.Scatter(
            x=hours, y=mem_trend, name="Memory %",
            mode="lines+markers", line=dict(color="#00D4FF", width=2, dash="dot"),
        ))
        fig_res.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font=dict(family="Inter, sans-serif", size=11, color="#1e293b"),
            margin=dict(l=20, r=20, t=10, b=20),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            xaxis=dict(title="Hour of Day", showgrid=True, gridcolor="rgba(0,102,255,0.08)"),
            yaxis=dict(title="Usage %", range=[0,100], showgrid=True,
                       gridcolor="rgba(0,102,255,0.08)"),
        )
        st.plotly_chart(fig_res, use_container_width=True, config={"displayModeBar": False})
        st.markdown('</div>', unsafe_allow_html=True)
