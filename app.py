"""
EnergiX AI – Smart Energy Analytics Platform
Main entry point: Supabase Auth login + sidebar navigation + page routing
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import streamlit as st
from pathlib import Path

# ── Page config (must be first Streamlit call) ───────
st.set_page_config(
    page_title="EnergiX AI – Smart Energy Analytics",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Inject Global CSS ────────────────────────────────
css_path = Path(__file__).parent / "styles" / "main.css"
if css_path.exists():
    with open(css_path, encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Hide Streamlit's auto-generated pages/ sidebar navigation
st.markdown("""
<style>
[data-testid="stSidebarNav"],
[data-testid="stSidebarNavItems"],
[data-testid="stSidebarNavSeparator"] { display: none !important; }
section[data-testid="stSidebar"] > div:first-child > div:first-child > div:first-child
    > div[data-testid="stSidebarNav"] { display: none !important; }
</style>
""", unsafe_allow_html=True)

from config import APP_TITLE


# ── Session state defaults ───────────────────────────
def _init_state():
    defaults = {
        "logged_in":    False,
        "user_email":   "",
        "user_name":    "",
        "user_role":    "",
        "dark_mode":    False,
        "notifications": [
            {"type": "danger",  "msg": "⚠️ Meter Tampering detected – CON-1007"},
            {"type": "warning", "msg": "⚡ Peak load alert – New York grid at 91%"},
            {"type": "info",    "msg": "✅ AI Forecast updated for next 24 hours"},
            {"type": "success", "msg": "🌱 Green energy contribution up to 38%"},
        ],
        "active_page": "Dashboard",
        "sb_ready":    None,   # None = not checked yet
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


_init_state()


# ════════════════════════════════════════════════════
# SUPABASE SETUP GUIDE  (shown if tables not ready)
# ════════════════════════════════════════════════════
def show_setup_guide():
    setup_sql_path = Path(__file__).parent / "database" / "supabase_setup.sql"
    sql_content = ""
    if setup_sql_path.exists():
        with open(setup_sql_path, encoding="utf-8") as f:
            sql_content = f.read()

    st.markdown("""
    <div class="page-title-banner animate-fade-up">
        <span style="font-size:2rem;">⚙️</span>
        <div>
            <h1>One-Time Supabase Setup</h1>
            <p>Run the SQL below in your Supabase dashboard to create the database tables.</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="alert-info">
        <strong>📋 Instructions:</strong><br>
        1. Open <a href="https://supabase.com/dashboard/project/shxqfepnfhawqrgxkyow/sql/new"
           target="_blank" style="color:#0066FF;">Supabase SQL Editor ↗</a><br>
        2. Paste the SQL below into a new query and click <strong>Run</strong><br>
        3. Once it says <em>"Success"</em>, click <strong>✅ Tables are ready – Continue</strong> below
    </div>
    """, unsafe_allow_html=True)

    # ── Button at the TOP so it's always visible ──────
    col_btn1, col_btn2, _ = st.columns([1.5, 1.5, 2])
    with col_btn1:
        if st.button("✅ Tables are ready – Continue", key="tables_ready_top",
                     use_container_width=True, type="primary"):
            st.session_state.sb_ready = True   # force login
            st.rerun()
    with col_btn2:
        if st.button("⏩ Skip Check & Login", key="force_skip",
                     use_container_width=True):
            st.session_state.sb_ready = True
            st.rerun()

    # Show connection error details if available
    if st.session_state.get("sb_error"):
        st.markdown(f"""
        <div class="alert-danger">
            ⚠️ <strong>Connection error:</strong> {st.session_state.sb_error}
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("#### 📄 SQL Setup Script (copy & paste into Supabase SQL Editor)")
    st.code(sql_content, language="sql")

    # Button also at the BOTTOM for convenience
    col_btn3, _ = st.columns([1, 3])
    with col_btn3:
        if st.button("✅ Tables are ready – Continue", key="tables_ready_bottom",
                     use_container_width=True):
            st.session_state.sb_ready = True
            st.rerun()



# ════════════════════════════════════════════════════
# LOGIN PAGE
# ════════════════════════════════════════════════════
def show_login():
    from database.supabase_manager import sign_in, ensure_demo_users, seed_data_if_empty

    # Particle background
    st.markdown("""
    <div class="particle-bg">
        <div class="particle p1"></div><div class="particle p2"></div>
        <div class="particle p3"></div><div class="particle p4"></div>
        <div class="particle p5"></div>
    </div>
    """, unsafe_allow_html=True)

    _, col, _ = st.columns([1, 1.1, 1])
    with col:
        st.markdown("""
        <div class="login-container">
          <div class="login-card">
            <div class="login-logo">
              <span class="logo-icon">⚡</span>
              <h1>EnergiX AI</h1>
              <p>Smart Energy Analytics Platform · Powered by Supabase</p>
            </div>
          </div>
        </div>
        """, unsafe_allow_html=True)

        # Supabase badge
        st.markdown("""
        <div style="text-align:center;margin-bottom:0.75rem;">
            <span style="background:linear-gradient(135deg,rgba(62,207,142,0.15),rgba(62,207,142,0.05));
                  border:1px solid rgba(62,207,142,0.4);border-radius:100px;
                  padding:0.25rem 0.85rem;font-size:0.75rem;font-weight:700;
                  color:#3ECF8E;letter-spacing:0.05em;">
                🟢 SUPABASE AUTH ENABLED
            </span>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("#### 🔐 Login to Smart Grid System")

        with st.form("login_form"):
            email    = st.text_input("📧 Email Address", placeholder="admin@energix.ai")
            password = st.text_input("🔑 Password", type="password", placeholder="••••••••")
            submitted = st.form_submit_button("⚡ Sign In to EnergiX", use_container_width=True)

        if submitted:
            if not email or not password:
                st.warning("Please enter email and password.")
            else:
                st.session_state.pop("auth_error", None)
                with st.spinner("🔐 Authenticating via Supabase..."):
                    # Try to create demo users (silently ignore any key/permission errors)
                    try:
                        ensure_demo_users()
                    except Exception:
                        pass
                    user = sign_in(email, password)

                if user:
                    st.session_state.logged_in  = True
                    st.session_state.user_email = user["email"]
                    st.session_state.user_name  = user["name"]
                    st.session_state.user_role  = user["role"]
                    st.session_state.pop("auth_error", None)
                    # Seed DB on first login (async-safe, returns quickly if already seeded)
                    try:
                        seed_data_if_empty()
                    except Exception:
                        pass
                    st.success(f"✅ Welcome, {user['name']}!")
                    st.rerun()
                else:
                    err = st.session_state.get("auth_error", "Invalid email or password.")
                    st.error(f"❌ {err}")

        st.markdown("""
        <div class="demo-creds">
            <strong>🔑 Demo Credentials</strong><br>
            Admin &nbsp;→ <code>admin@energix.ai</code> / <code>admin123</code><br>
            Analyst → <code>analyst@energix.ai</code> / <code>analyst123</code><br>
            Viewer &nbsp;→ <code>demo@energix.ai</code> / <code>demo123</code>
        </div>
        """, unsafe_allow_html=True)

        # Supabase status
        st.markdown("""
        <div style="text-align:center;margin-top:1rem;font-size:0.72rem;color:#94a3b8;">
            🔒 Secured by Supabase Auth · JWT Sessions · bcrypt passwords
        </div>
        """, unsafe_allow_html=True)


# ════════════════════════════════════════════════════
# SIDEBAR
# ════════════════════════════════════════════════════
def show_sidebar():
    with st.sidebar:
        # Logo
        st.markdown("""
        <div class="sidebar-logo">
            <span style="font-size:2rem;">⚡</span>
            <div class="logo-text">EnergiX AI</div>
            <div style="font-size:0.68rem;opacity:0.5;letter-spacing:0.1em;margin-top:2px;">
                SMART ENERGY ANALYTICS
            </div>
        </div>
        """, unsafe_allow_html=True)

        # User card with Supabase badge
        initials = "".join(w[0] for w in st.session_state.user_name.split()[:2]).upper()
        st.markdown(f"""
        <div class="sidebar-user-card">
            <div class="sidebar-avatar">{initials}</div>
            <div>
                <div class="sidebar-user-name">{st.session_state.user_name}</div>
                <div class="sidebar-user-role">
                    <span class="status-dot status-online"></span>
                    {st.session_state.user_role} · Supabase Auth
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # Navigation
        pages = [
            ("📊", "Dashboard"),
            ("🤖", "AI Forecasting"),
            ("🚨", "Anomaly Detection"),
            ("⚡", "Smart Optimization"),
            ("🌿", "Carbon Analytics"),
            ("🗄️", "SQL Database"),
            ("📡", "Real-Time Monitor"),
            ("🛡️", "Admin Panel"),
        ]

        for icon, label in pages:
            is_active = st.session_state.active_page == label
            btn_style = (
                "background:linear-gradient(90deg,rgba(0,102,255,0.25),rgba(0,212,255,0.1));"
                "border-left:3px solid #0066FF;"
            ) if is_active else ""
            st.markdown(f'<div style="{btn_style} border-radius:8px; padding:0.1rem 0;">',
                        unsafe_allow_html=True)
            if st.button(f"{icon}  {label}", key=f"nav_{label}", use_container_width=True):
                st.session_state.active_page = label
                st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("---")

        # Notifications
        n_count = len(st.session_state.notifications)
        with st.expander(f"🔔 Notifications  ({n_count})"):
            for notif in st.session_state.notifications[:4]:
                color_map = {"danger":"#FF3366","warning":"#FF6B35",
                             "info":"#0066FF","success":"#00C853"}
                c = color_map.get(notif["type"], "#0066FF")
                st.markdown(
                    f'<div style="border-left:3px solid {c};padding:0.4rem 0.75rem;'
                    f'background:rgba(255,255,255,0.05);border-radius:4px;margin-bottom:6px;'
                    f'font-size:0.78rem;">{notif["msg"]}</div>',
                    unsafe_allow_html=True,
                )

        st.markdown("---")

        # Supabase status badge
        st.markdown("""
        <div style="text-align:center;margin-bottom:0.5rem;">
            <span style="background:rgba(62,207,142,0.15);border:1px solid rgba(62,207,142,0.35);
                  border-radius:100px;padding:0.2rem 0.75rem;font-size:0.68rem;font-weight:700;
                  color:#3ECF8E;letter-spacing:0.04em;">
                🟢 Supabase Connected
            </span>
        </div>
        """, unsafe_allow_html=True)

        col1, col2 = st.columns(2)
        with col1:
            dm = st.toggle("🌙 Dark", value=st.session_state.dark_mode, key="dm_toggle")
            if dm != st.session_state.dark_mode:
                st.session_state.dark_mode = dm
                st.rerun()
        with col2:
            if st.button("🚪 Logout", key="logout_btn"):
                try:
                    from database.supabase_manager import sign_out
                    sign_out()
                except Exception:
                    pass
                st.session_state.logged_in = False
                st.rerun()

        st.markdown(
            '<div style="text-align:center;font-size:0.68rem;opacity:0.35;padding-top:0.5rem;">'
            'EnergiX AI v2.1.0 · © 2025</div>',
            unsafe_allow_html=True,
        )


# ════════════════════════════════════════════════════
# PAGE ROUTER
# ════════════════════════════════════════════════════
def route_page():
    page = st.session_state.active_page
    if   page == "Dashboard":        from pages.dashboard     import show
    elif page == "AI Forecasting":   from pages.forecasting   import show
    elif page == "Anomaly Detection":from pages.anomaly       import show
    elif page == "Smart Optimization":from pages.optimization import show
    elif page == "Carbon Analytics": from pages.carbon        import show
    elif page == "SQL Database":     from pages.database_view import show
    elif page == "Real-Time Monitor":from pages.realtime      import show
    elif page == "Admin Panel":      from pages.admin         import show
    else:                            from pages.dashboard     import show
    show()


# ════════════════════════════════════════════════════
# MAIN FLOW
# ════════════════════════════════════════════════════
if not st.session_state.logged_in:
    # ── Check if Supabase tables are ready (cached per session) ──
    if st.session_state.sb_ready is None:
        try:
            from database.supabase_manager import is_tables_ready
            st.session_state.sb_ready = is_tables_ready()
        except Exception:
            st.session_state.sb_ready = False

    if not st.session_state.sb_ready:
        show_setup_guide()
    else:
        show_login()
else:
    show_sidebar()
    route_page()
