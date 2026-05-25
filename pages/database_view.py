"""
EnergiX AI – SQL Database Integration Page (Supabase Edition)
Table browser via REST API + SQL Explorer via run_sql() RPC
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

from database.supabase_manager import (
    get_table, get_table_count, execute_sql
)


_TABLES = {
    "consumers": {
        "icon": "👥",
        "desc": "Smart meter consumers registered in the system",
        "order": "registered_at",
    },
    "energy_readings": {
        "icon": "⚡",
        "desc": "Hourly smart meter energy readings",
        "order": "timestamp",
    },
    "predictions": {
        "icon": "🤖",
        "desc": "AI-generated demand predictions per city",
        "order": "created_at",
    },
    "anomalies": {
        "icon": "🚨",
        "desc": "Detected anomalies and electricity theft cases",
        "order": "detected_at",
    },
    "smart_meters": {
        "icon": "📡",
        "desc": "Smart meter devices and their status",
        "order": "last_ping",
    },
    "users": {
        "icon": "🔐",
        "desc": "System user profiles",
        "order": "created_at",
    },
}

_SAMPLE_QUERIES = [
    ("Top 10 consumers by energy usage",
     "SELECT consumer_id, ROUND(SUM(energy_kwh)::numeric, 2) AS total_kwh,\n"
     "       COUNT(*) AS readings\n"
     "FROM energy_readings\n"
     "GROUP BY consumer_id\n"
     "ORDER BY total_kwh DESC\n"
     "LIMIT 10"),

    ("City-wise average consumption",
     "SELECT city,\n"
     "       ROUND(AVG(energy_kwh)::numeric, 2) AS avg_kwh,\n"
     "       ROUND(SUM(cost_usd)::numeric, 2)   AS total_cost\n"
     "FROM energy_readings\n"
     "GROUP BY city\n"
     "ORDER BY avg_kwh DESC"),

    ("High-risk anomalies (open)",
     "SELECT consumer_id, anomaly_type, risk_score, city, status\n"
     "FROM anomalies\n"
     "WHERE risk_score > 0.75\n"
     "  AND status != 'Resolved'\n"
     "ORDER BY risk_score DESC"),

    ("Hourly energy profile (all data)",
     "SELECT EXTRACT(HOUR FROM timestamp)::int AS hour,\n"
     "       ROUND(AVG(energy_kwh)::numeric, 2) AS avg_kwh,\n"
     "       COUNT(*) AS readings\n"
     "FROM energy_readings\n"
     "GROUP BY hour\n"
     "ORDER BY hour"),

    ("Device type energy breakdown",
     "SELECT device_type,\n"
     "       ROUND(SUM(energy_kwh)::numeric, 2) AS total_kwh,\n"
     "       ROUND(AVG(energy_kwh)::numeric, 2) AS avg_kwh,\n"
     "       COUNT(*) AS readings\n"
     "FROM energy_readings\n"
     "GROUP BY device_type\n"
     "ORDER BY total_kwh DESC"),

    ("Offline / maintenance meters",
     "SELECT meter_id, consumer_id, city, status, battery_pct, last_ping\n"
     "FROM smart_meters\n"
     "WHERE status != 'Active'\n"
     "ORDER BY last_ping DESC"),

    ("Consumers in high-risk cities",
     "SELECT c.consumer_id, c.name, c.city, c.device_type,\n"
     "       COUNT(a.id) AS anomaly_count\n"
     "FROM consumers c\n"
     "LEFT JOIN anomalies a ON c.consumer_id = a.consumer_id\n"
     "GROUP BY c.consumer_id, c.name, c.city, c.device_type\n"
     "HAVING COUNT(a.id) > 0\n"
     "ORDER BY anomaly_count DESC"),
]


def show():
    st.markdown("""
    <div class="page-title-banner animate-fade-up">
        <span style="font-size:2rem;">🗄️</span>
        <div>
            <h1>SQL Database Explorer</h1>
            <p>Supabase PostgreSQL · REST API table browser · Live SQL query executor</p>
        </div>
        <div style="margin-left:auto;">
            <span style="background:rgba(62,207,142,0.15);border:1px solid rgba(62,207,142,0.35);
                  border-radius:100px;padding:0.25rem 0.85rem;font-size:0.75rem;font-weight:700;
                  color:#3ECF8E;letter-spacing:0.04em;">🟢 Supabase PostgreSQL</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Schema Overview Cards ─────────────────────────
    st.markdown("### 📋 Database Schema")
    cols = st.columns(3)
    for i, (tbl, meta) in enumerate(_TABLES.items()):
        with cols[i % 3]:
            cnt = get_table_count(tbl)
            st.markdown(f"""
            <div class="glass-card" style="padding:1rem;margin-bottom:0.75rem;">
                <div style="display:flex;align-items:center;gap:0.5rem;margin-bottom:0.35rem;">
                    <span style="font-size:1.3rem;">{meta['icon']}</span>
                    <strong style="font-size:0.9rem;">{tbl}</strong>
                    <span style="margin-left:auto;background:rgba(0,102,255,0.1);
                          color:#0066FF;font-size:0.7rem;font-weight:700;
                          padding:0.15rem 0.5rem;border-radius:100px;">{cnt:,} rows</span>
                </div>
                <div style="font-size:0.78rem;color:#475569;">{meta['desc']}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Table Browser ─────────────────────────────────
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown("""
    <div class="section-header">
        <div class="icon">🗂️</div>
        <h3>Table Browser</h3>
        <span class="badge">SUPABASE REST</span>
    </div>
    """, unsafe_allow_html=True)

    tab_names = [f"{meta['icon']} {tbl}" for tbl, meta in _TABLES.items()]
    tabs = st.tabs(tab_names)

    for tab, (tbl, meta) in zip(tabs, _TABLES.items()):
        with tab:
            col_search, col_rows = st.columns([3, 1])
            with col_search:
                search = st.text_input(
                    f"Search {tbl}", placeholder="Filter any column...",
                    key=f"search_{tbl}", label_visibility="collapsed",
                )
            with col_rows:
                n_rows = st.selectbox("Rows", [25, 50, 100, 200],
                                      key=f"rows_{tbl}", label_visibility="collapsed")

            df = get_table(tbl, limit=n_rows, order_col=meta.get("order"))

            if search and not df.empty:
                mask = df.apply(
                    lambda c: c.astype(str).str.contains(search, case=False, na=False)
                )
                df = df[mask.any(axis=1)]

            if df.empty:
                st.info("No data found. Run the setup SQL and seed data first.")
            else:
                st.dataframe(df, use_container_width=True, height=340, hide_index=True)
                col_dl, col_info = st.columns([1, 3])
                with col_dl:
                    csv = df.to_csv(index=False).encode()
                    st.download_button(
                        "⬇️ Export CSV", csv, f"{tbl}.csv", "text/csv",
                        key=f"dl_{tbl}",
                    )
                with col_info:
                    st.info(f"**{len(df)}** rows displayed")

    st.markdown('</div>', unsafe_allow_html=True)

    # ── SQL Query Executor ────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown("""
    <div class="section-header">
        <div class="icon">💻</div>
        <h3>SQL Query Executor</h3>
        <span class="badge">run_sql() RPC</span>
    </div>
    <div class="alert-info" style="margin-bottom:0.75rem;">
        ℹ️ Powered by the <code>run_sql()</code> PostgreSQL function created during setup.
        Supports any <strong>SELECT</strong> statement against your Supabase schema.
    </div>
    """, unsafe_allow_html=True)

    sample_labels = [q[0] for q in _SAMPLE_QUERIES]
    picked = st.selectbox(
        "💡 Load Sample Query", ["── Select a template ──"] + sample_labels,
        key="sample_query_picker",
    )

    default_sql = "SELECT * FROM energy_readings ORDER BY timestamp DESC LIMIT 20"
    for label, sql in _SAMPLE_QUERIES:
        if picked == label:
            default_sql = sql
            break

    sql_input = st.text_area(
        "📝 Enter SQL Query",
        value=default_sql,
        height=160,
        key="sql_editor",
        help="Write any SELECT query against the Supabase PostgreSQL database.",
    )

    col_run, _ = st.columns([1, 5])
    with col_run:
        run_clicked = st.button("▶️ Execute", key="run_sql", use_container_width=True)

    if run_clicked:
        with st.spinner("Running query on Supabase..."):
            result_df, error = execute_sql(sql_input)

        if error:
            st.markdown(f"""
            <div class="alert-danger">
                ❌ <strong>Error:</strong> {error}
            </div>
            """, unsafe_allow_html=True)
        else:
            if result_df is not None and not result_df.empty:
                st.success(
                    f"✅ Returned **{len(result_df)}** rows · "
                    f"**{len(result_df.columns)}** columns"
                )
                st.dataframe(result_df, use_container_width=True, height=350)

                col_ex1, _ = st.columns([1, 5])
                with col_ex1:
                    csv = result_df.to_csv(index=False).encode()
                    st.download_button(
                        "⬇️ Export CSV", csv,
                        "query_results.csv", "text/csv", key="dl_query",
                    )

                # Auto-visualize if numeric columns exist
                numeric_cols = result_df.select_dtypes(include="number").columns.tolist()
                if len(numeric_cols) >= 1 and len(result_df) > 1:
                    with st.expander("📊 Auto-Visualize Results"):
                        x_col     = result_df.columns[0]
                        y_col     = st.selectbox("Y Axis", numeric_cols, key="auto_y")
                        chart_type = st.radio(
                            "Chart", ["Bar", "Line", "Scatter"],
                            horizontal=True, key="auto_chart",
                        )
                        if chart_type == "Bar":
                            fig = px.bar(result_df, x=x_col, y=y_col)
                        elif chart_type == "Line":
                            fig = px.line(result_df, x=x_col, y=y_col)
                        else:
                            fig = px.scatter(result_df, x=x_col, y=y_col)
                        fig.update_layout(
                            paper_bgcolor="rgba(0,0,0,0)",
                            plot_bgcolor="rgba(0,0,0,0)",
                            font=dict(family="Inter, sans-serif"),
                            margin=dict(l=20, r=20, t=20, b=20),
                        )
                        st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("✅ Query executed. No rows returned.")

    st.markdown('</div>', unsafe_allow_html=True)

    # ── DB Stats ──────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown("""
    <div class="section-header">
        <div class="icon">📊</div>
        <h3>Table Row Counts</h3>
    </div>
    """, unsafe_allow_html=True)

    col_chart, col_info = st.columns([2, 1])
    with col_chart:
        counts = {tbl: get_table_count(tbl) for tbl in _TABLES}
        df_counts = pd.DataFrame(
            {"table": list(counts.keys()), "rows": list(counts.values())}
        )
        fig_bar = go.Figure(go.Bar(
            x=df_counts["rows"], y=df_counts["table"],
            orientation="h",
            marker_color=["#0066FF","#00D4FF","#00C853","#FF3366","#FF6B35","#A855F7"],
            text=[f"{v:,}" for v in df_counts["rows"]],
            textposition="outside",
        ))
        fig_bar.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font=dict(family="Inter, sans-serif", size=12, color="#1e293b"),
            margin=dict(l=20, r=60, t=10, b=10),
            xaxis=dict(showgrid=True, gridcolor="rgba(0,102,255,0.08)"),
            yaxis=dict(showgrid=False),
            height=220,
        )
        st.plotly_chart(fig_bar, use_container_width=True, config={"displayModeBar": False})

    with col_info:
        st.markdown(f"""
        <div style="padding:0.5rem 0;">
            <div style="display:flex;justify-content:space-between;padding:0.4rem 0;
                 border-bottom:1px solid rgba(0,102,255,0.1);">
                <span style="color:#475569;">Database</span><strong>Supabase PostgreSQL</strong>
            </div>
            <div style="display:flex;justify-content:space-between;padding:0.4rem 0;
                 border-bottom:1px solid rgba(0,102,255,0.1);">
                <span style="color:#475569;">Project ID</span>
                <strong style="font-size:0.78rem;">shxqfepnfhawqrgxkyow</strong>
            </div>
            <div style="display:flex;justify-content:space-between;padding:0.4rem 0;
                 border-bottom:1px solid rgba(0,102,255,0.1);">
                <span style="color:#475569;">Tables</span><strong>6</strong>
            </div>
            <div style="display:flex;justify-content:space-between;padding:0.4rem 0;
                 border-bottom:1px solid rgba(0,102,255,0.1);">
                <span style="color:#475569;">Auth</span><strong>Supabase Auth</strong>
            </div>
            <div style="display:flex;justify-content:space-between;padding:0.4rem 0;">
                <span style="color:#475569;">Status</span>
                <span class="risk-badge risk-low">🟢 Connected</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)
