from __future__ import annotations

import base64
import secrets
import time
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

from auth import (
    authenticate_user,
    create_employee_user,
    find_user_by_email,
    is_valid_email,
    is_valid_employee_id,
    public_user,
    validate_password_strength,
)
from model import (
    ATTENDANCE_HISTORY_COLUMNS,
    DATA_FILE,
    WEIGHTS,
    build_reward_analysis,
    export_powerbi_results,
)


LOGIN_ROUTE = "/login"
SIGNUP_ROUTE = "/employee/signup"
MANAGER_DASHBOARD_ROUTE = "/manager/dashboard"
EMPLOYEE_DASHBOARD_ROUTE = "/employee/dashboard"
SESSION_TTL_SECONDS = 45 * 60


st.set_page_config(
    page_title="AI HR Reward System",
    layout="wide",
)


@st.cache_data
def get_analysis(data_mtime: float) -> tuple[pd.DataFrame, pd.DataFrame]:
    return build_reward_analysis(DATA_FILE)


def apply_theme() -> None:
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');
        
        html, body, [data-testid="stAppViewContainer"] {
            font-family: 'Plus Jakarta Sans', sans-serif !important;
            background: 
              radial-gradient(ellipse 700px 500px at 8% 8%, rgba(45,212,191,0.16), transparent 60%),
              radial-gradient(ellipse 600px 500px at 95% 12%, rgba(167,139,250,0.18), transparent 60%),
              radial-gradient(ellipse 700px 600px at 50% 100%, rgba(251,113,133,0.13), transparent 60%),
              linear-gradient(180deg, #161226, #1E1934 40%, #241D3D) !important;
            color: #f8fafc !important;
        }

        header[data-testid="stHeader"] {
            background: rgba(2, 6, 23, 0.5) !important;
            backdrop-filter: blur(10px);
            border-bottom: 1px solid rgba(255, 255, 255, 0.05);
        }
        
        footer {visibility: hidden;}

        .block-container {
            max-width: 1400px;
            padding-top: 3rem;
            padding-bottom: 2rem;
        }

        /* Enhanced Headers */
        h1 {
            background: linear-gradient(to right, #2dd4bf, #3b82f6);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-weight: 800 !important;
            font-size: 3rem !important;
            margin-bottom: 1rem !important;
            text-align: center;
        }
        h2, h3 {
            color: #38bdf8 !important;
            font-weight: 600 !important;
            letter-spacing: 0.02em;
        }
        
        /* Premium Metric Cards */
        div[data-testid="stMetric"], .premium-card {
            background: linear-gradient(135deg, rgba(30, 41, 59, 0.6) 0%, rgba(15, 23, 42, 0.9) 100%);
            border: 1px solid rgba(148, 163, 184, 0.15);
            border-radius: 20px;
            padding: 1.5rem;
            backdrop-filter: blur(12px);
            box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3);
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            position: relative;
            overflow: hidden;
        }
        div[data-testid="stMetric"]::before, .premium-card::before {
            content: "";
            position: absolute;
            top: 0; left: 0; right: 0; height: 1px;
            background: linear-gradient(90deg, transparent, rgba(45, 212, 191, 0.5), transparent);
        }
        div[data-testid="stMetric"]:hover, .premium-card:hover {
            border-color: rgba(45, 212, 191, 0.4);
            transform: translateY(-5px);
            box-shadow: 0 12px 40px 0 rgba(45, 212, 191, 0.2);
        }

        .metric-label {
            font-size: 0.9rem !important;
            color: #94a3b8 !important;
            font-weight: 400 !important;
            text-transform: uppercase;
            letter-spacing: 0.1em;
            margin-bottom: 0.5rem;
        }
        .metric-value-large {
            font-size: 2.5rem !important;
            font-weight: 800 !important;
            background: linear-gradient(to right, #f8fafc, #cbd5e1);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .metric-value-highlight {
            font-size: 2.5rem !important;
            font-weight: 800 !important;
            background: linear-gradient(to right, #34d399, #3b82f6);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        /* Container Styling */
        .badge-container {
            background: linear-gradient(135deg, rgba(45, 212, 191, 0.05), rgba(59, 130, 246, 0.05));
            border: 1px solid rgba(45, 212, 191, 0.2);
            border-radius: 20px;
            padding: 2rem;
            margin-top: 1.5rem;
            text-align: center;
        }

        .certificate-container {
            background: #020617;
            border-radius: 24px;
            overflow: hidden;
            border: 1px solid rgba(255, 255, 255, 0.08);
            box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.6);
            padding: 1rem;
        }

        /* Sidebar Refinement */
        div[data-testid="stSidebar"] {
            background: rgba(2, 6, 23, 0.7) !important;
            backdrop-filter: blur(15px);
            border-right: 1px solid rgba(255, 255, 255, 0.05);
        }
        
        /* Auth Screens Visibility */
        .auth-title {
            font-size: 3rem;
            font-weight: 800;
            background: linear-gradient(to right, #2dd4bf, #3b82f6);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 0.5rem;
            text-align: center;
        }
        .auth-subtitle {
            color: #94a3b8;
            font-size: 1.2rem;
            margin-bottom: 2rem;
            text-align: center;
        }

        .glass-logo-box {
            background: rgba(255, 255, 255, 0.02);
            backdrop-filter: blur(20px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 24px;
            padding: 20px;
            margin: 0 auto 2rem auto;
            max-width: 450px;
            width: 100%;
            box-shadow: 0 10px 40px -10px rgba(0,0,0,0.5);
            display: flex;
            justify-content: center;
            align-items: center;
            transition: all 0.4s ease;
        }
        
        .glass-logo-box:hover {
            border-color: rgba(45, 212, 191, 0.4);
            transform: translateY(-3px);
            box-shadow: 0 20px 40px -10px rgba(45, 212, 191, 0.2);
        }
        
        /* Buttons */
        div.stButton > button {
            background: linear-gradient(to right, #0ea5e9, #3b82f6);
            color: white;
            border: none;
            border-radius: 12px;
            padding: 0.5rem 1rem;
            font-weight: 600;
            transition: all 0.3s;
        }
        div.stButton > button:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 20px rgba(59, 130, 246, 0.4);
            color: white;
        }
        
        div[data-testid="stForm"] {
            background: rgba(15, 23, 42, 0.6);
            backdrop-filter: blur(16px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 24px;
            padding: 2.5rem;
            box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
            max-width: 450px;
            margin: 0 auto;
        }
        
        div[data-testid="stTextInput"] input, div[data-testid="stSelectbox"] div {
            background: rgba(255, 255, 255, 0.05) !important;
            border: 1px solid rgba(255, 255, 255, 0.1) !important;
            color: #f8fafc !important;
            border-radius: 12px;
        }

        /* Scrollbar */
        ::-webkit-scrollbar {
            width: 8px;
        }
        ::-webkit-scrollbar-track {
            background: #020617;
        }
        ::-webkit-scrollbar-thumb {
            background: #334155;
            border-radius: 4px;
        }
        ::-webkit-scrollbar-thumb:hover {
            background: #475569;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def format_score(value: float) -> str:
    return f"{value:.2f}"


def get_route() -> str:
    route = st.query_params.get("route", LOGIN_ROUTE)
    if isinstance(route, list):
        return route[0] if route else LOGIN_ROUTE
    return route or LOGIN_ROUTE


def set_route(route: str) -> None:
    st.query_params["route"] = route
    st.session_state["route"] = route
    st.rerun()


def queue_toast(message: str) -> None:
    st.session_state["toast_message"] = message


def show_queued_toast() -> None:
    message = st.session_state.pop("toast_message", None)
    if message:
        st.toast(message)


def start_session(user: dict[str, object]) -> None:
    st.session_state["auth_session"] = {
        "token": secrets.token_urlsafe(32),
        "user": user,
        "expires_at": time.time() + SESSION_TTL_SECONDS,
    }
    # Persist email in URL to survive refresh
    st.query_params["session_user"] = user["email"]


def get_current_user() -> dict[str, object] | None:
    session = st.session_state.get("auth_session")
    
    # Try to restore from query params if session state is empty (happens on refresh)
    if not session:
        stored_email = st.query_params.get("session_user")
        if stored_email:
            user = find_user_by_email(stored_email)
            if user:
                # Restore the session safely
                start_session(public_user(user))
                return public_user(user)

    if not session:
        return None

    if time.time() > session.get("expires_at", 0):
        # Clear query params if expired
        st.query_params.clear()
        st.session_state.pop("auth_session", None)
        queue_toast("Session expired. Please sign in again.")
        return None

    session["expires_at"] = time.time() + SESSION_TTL_SECONDS
    return session["user"]


def logout() -> None:
    st.session_state.pop("auth_session", None)
    st.query_params.clear()
    queue_toast("Signed out successfully.")
    set_route(LOGIN_ROUTE)


def get_base64_image(path: str) -> str:
    try:
        if not Path(path).exists():
            return ""
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    except Exception:
        return ""


def show_auth_header(subtitle: str) -> None:
    # Glass Logo Box
    logo_path = "assets/logo.png"
    logo_b64 = get_base64_image(logo_path)
    
    if logo_b64:
        st.markdown(
            f"""
            <div class="glass-logo-box">
                <img src="data:image/png;base64,{logo_b64}" style="max-width: 400px; width: 100%; height: 200px; mix-blend-mode: screen; filter: brightness(1.1) contrast(1.1);">
            </div>
            """,
            unsafe_allow_html=True
        )
    else:
        st.markdown('<div class="auth-title" style="text-align: center;">SmartRewardX</div>', unsafe_allow_html=True)
    
    st.markdown(f'<div class="auth-subtitle">{subtitle}</div>', unsafe_allow_html=True)


def close_auth_header() -> None:
    pass


def show_login_page() -> None:
    show_auth_header("Secure login for managers and employees")

    st.markdown('<div style="max-width: 450px; margin: 0 auto;">', unsafe_allow_html=True)
    show_password = st.toggle("Show password", key="login_show_pwd")
    st.markdown('</div>', unsafe_allow_html=True)
    
    with st.form("login_form", border=False):
        st.markdown('<h3 style="text-align:center; margin-bottom: 1.5rem;">Sign In</h3>', unsafe_allow_html=True)
        
        email = st.text_input(
            "Email",
            value=st.session_state.pop("prefill_email", ""),
            placeholder="name@company.com",
        )
        password = st.text_input(
            "Password",
            type="default" if show_password else "password",
            placeholder="Enter password",
        )

        submitted = st.form_submit_button("Sign in", type="primary", use_container_width=True)

        if submitted:
            email_ok = is_valid_email(email)
            password_ok = bool(password)
            login_ready = email_ok and password_ok

            if not login_ready:
                if not email_ok:
                    st.error("Use a valid company email format.")
                if not password_ok:
                    st.error("Password is required.")
            else:
                with st.spinner("Signing in..."):
                    user = authenticate_user(email, password)
                    time.sleep(0.35)

                if not user:
                    st.toast("Login failed. Check your email and password.")
                    st.error("Invalid email or password.")
                else:
                    start_session(user)
                    route = (
                        MANAGER_DASHBOARD_ROUTE
                        if user["role"] == "manager"
                        else EMPLOYEE_DASHBOARD_ROUTE
                    )
                    queue_toast("Login successful.")
                    set_route(route)

    st.divider()
    if st.button("New employee sign up", use_container_width=True):
        set_route(SIGNUP_ROUTE)

    with st.expander("Demo accounts"):
        st.write("Manager: manager@company.com / Manager@123")
        st.write("Employee: aarav.sharma@gmail.com / Employee@123")
        
    close_auth_header()


def show_signup_page() -> None:
    show_auth_header("New employee account setup")

    st.markdown('<div style="max-width: 450px; margin: 0 auto;">', unsafe_allow_html=True)
    show_password = st.toggle("Show password", key="signup_show_pwd")
    st.markdown('</div>', unsafe_allow_html=True)
    
    with st.form("signup_form", border=False):
        st.markdown('<h3 style="text-align:center; margin-bottom: 1.5rem;">Create Account</h3>', unsafe_allow_html=True)
        full_name = st.text_input("Full Name", placeholder="Aditi Sharma")
        employee_id = st.text_input("Employee ID", placeholder="EMP031")
        email = st.text_input("Email", placeholder="employee@company.com")
        department = st.selectbox(
            "Department",
            [
                "Select department",
                "Engineering",
                "Sales",
                "HR",
                "Operations",
                "Finance",
                "Marketing",
                "Customer Success",
            ],
        )
        
        pwd_type = "default" if show_password else "password"
        password = st.text_input("Password", type=pwd_type, placeholder="Minimum 8 characters")
        confirm_password = st.text_input("Confirm Password", type=pwd_type, placeholder="Re-enter password")

        submitted = st.form_submit_button("Create employee account", type="primary", use_container_width=True)

        if submitted:
            password_issues = validate_password_strength(password) if password else []
            full_name_ok = len(full_name.strip()) >= 2
            employee_id_ok = is_valid_employee_id(employee_id)
            email_ok = is_valid_email(email)
            department_ok = department != "Select department"
            password_ok = bool(password) and not password_issues
            passwords_match = password == confirm_password

            signup_ready = (
                full_name_ok
                and employee_id_ok
                and email_ok
                and department_ok
                and password_ok
                and passwords_match
            )

            if not signup_ready:
                if not full_name_ok:
                    st.error("Full name must be at least 2 characters.")
                if not employee_id_ok:
                    st.error("Employee ID must be 3-20 letters, numbers, or hyphens.")
                if not email_ok:
                    st.error("Use a valid email address.")
                if not department_ok:
                    st.error("Please select a department.")
                if password_issues:
                    st.error("Password needs " + ", ".join(password_issues) + ".")
                elif not password_ok:
                    st.error("Password is required.")
                if not passwords_match:
                    st.error("Passwords do not match.")
            else:
                with st.spinner("Creating secure account..."):
                    ok, message, _ = create_employee_user(
                        full_name=full_name,
                        employee_id=employee_id,
                        email=email,
                        department=department,
                        password=password,
                    )
                    time.sleep(0.35)

                if ok:
                    st.session_state["prefill_email"] = email
                    queue_toast(message)
                    set_route(LOGIN_ROUTE)
                else:
                    st.toast(message)
                    st.error(message)

    st.divider()
    if st.button("Already have an account? Back to login", use_container_width=True):
        set_route(LOGIN_ROUTE)

    st.caption("Manager accounts are admin-created only and cannot be made here.")
    
    close_auth_header()


def render_sidebar(user: dict[str, object]) -> None:
    st.sidebar.markdown(
        """
        <div style="font-family: 'Fraunces', serif; font-weight: 700; font-size: 26px; letter-spacing: -0.01em; margin-bottom: 8px; line-height: 1.1;">
            SmartReward<span style="color:#FFC857; font-style:italic; font-weight:600;">X</span>
        </div>
        """,
        unsafe_allow_html=True
    )
    st.sidebar.write(f"**{user['full_name']}**")
    st.sidebar.caption(f"{str(user['role']).title()} | {user['email']}")
    st.sidebar.divider()

    if user["role"] == "manager":
        if st.sidebar.button("Manager Dashboard", use_container_width=True):
            set_route(MANAGER_DASHBOARD_ROUTE)
    else:
        if st.sidebar.button("Employee Dashboard", use_container_width=True):
            set_route(EMPLOYEE_DASHBOARD_ROUTE)

    st.sidebar.divider()
    st.sidebar.caption("Scoring weights")
    st.sidebar.write(f"Attendance: {WEIGHTS['attendance_percent']:.0%}")
    st.sidebar.write(f"Performance: {WEIGHTS['project_completion_rate']:.0%}")
    st.sidebar.write(f"Peer feedback: {WEIGHTS['peer_feedback_score']:.0%}")
    st.sidebar.divider()

    if st.sidebar.button("Sign out", use_container_width=True):
        logout()


def employee_dashboard(df: pd.DataFrame, user: dict[str, object]) -> None:
    employee_id = str(user["employee_id"]).upper()
    matched = df[df["employee_id"].str.upper() == employee_id]

    if matched.empty:
        st.title("Employee Dashboard")
        st.subheader(str(user["full_name"]))
        st.info("Your account is active. Reward data will appear after HR imports your first performance cycle.")
        st.dataframe(
            pd.DataFrame(
                [
                    {
                        "Full Name": user["full_name"],
                        "Employee ID": user["employee_id"],
                        "Email": user["email"],
                        "Department": user["department"],
                        "Role": user["role"],
                    }
                ]
            ),
            use_container_width=True,
            hide_index=True,
        )
        return

    employee = matched.iloc[0].copy()
    
    import streamlit.components.v1 as components
    from datetime import datetime
    
    with open("employee_template.html", "r", encoding="utf-8") as f:
        template = f.read()

    def map_y(val):
        val = max(min(val, 100), 40)
        return int(190 - (val - 40) * 2.5)

    att_cols = ["attendance_jan", "attendance_feb", "attendance_mar", "attendance_apr"]
    att_vals = [employee.get(c, employee["attendance_percent"]) for c in att_cols]
    xs = [40, 166, 292, 418]
    ys = [map_y(v) for v in att_vals]
    
    line_path = f"M{xs[0]},{ys[0]} L{xs[1]},{ys[1]} L{xs[2]},{ys[2]} L{xs[3]},{ys[3]}"
    area_path = f"{line_path} L{xs[3]},190 L{xs[0]},190 Z"
    
    dots_html = f'<circle cx="{xs[0]}" cy="{ys[0]}" r="5" fill="#161226" stroke="#2DD4BF" stroke-width="2.5"/>'
    dots_html += f'<circle cx="{xs[1]}" cy="{ys[1]}" r="5" fill="#161226" stroke="#2DD4BF" stroke-width="2.5"/>'
    dots_html += f'<circle cx="{xs[2]}" cy="{ys[2]}" r="5" fill="#161226" stroke="#2DD4BF" stroke-width="2.5"/>'
    dots_html += f'<circle cx="{xs[3]}" cy="{ys[3]}" r="6.5" fill="#2DD4BF" stroke="#161226" stroke-width="2"/>'
    
    anomaly_flag = not employee.get("needs_manager_review", False)
    anomaly_icon = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none"><path d="M4 12.5l5 5L20 7" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/></svg>' if anomaly_flag else '<svg width="16" height="16" viewBox="0 0 24 24" fill="none"><path d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/></svg>'
    anomaly_text = "No anomaly flags for this record" if anomaly_flag else str(employee.get("anomaly_flags", ""))
    anomaly_class = "anomaly-ok" if anomaly_flag else "anomaly-warn"
    
    diff = employee.get("score_vs_peer_group", 0)
    diff_class = "up" if diff >= 0 else "down"

    name = str(employee["employee_name"])
    initials = "".join([n[0] for n in name.split()[:2]]).upper() if name else "U"

    html = template
    replacements = {
        "{employee_name}": name,
        "{avatar_initials}": initials,
        "{role}": str(employee["role"]),
        "{email}": str(user["email"]),
        "{current_date}": datetime.now().strftime("%d %b %Y"),
        "{reward_action}": str(employee.get("reward_action", "Reward")),
        "{score_vs_peer_group_str}": f"{diff:+.2f}",
        "{badge_earned}": str(employee.get("badge_earned", "Badge")),
        "{attendance_percent}": str(employee.get("attendance_percent", 0)),
        "{project_completion_rate}": str(employee.get("project_completion_rate", 0)),
        "{peer_feedback_score}": str(employee.get("peer_feedback_score", 0)),
        "{motivation_trigger}": str(employee.get("motivation_trigger", "Keep up the good work!")),
        "{area_path}": area_path,
        "{line_path}": line_path,
        "{dots_html}": dots_html,
        "{attendance_component}": f"{employee.get('attendance_component', 0):.1f}",
        "{performance_component}": f"{employee.get('performance_component', 0):.1f}",
        "{feedback_component}": f"{employee.get('feedback_component', 0):.1f}",
        "{total_score}": f"{employee.get('total_score', 0):.1f}",
        "{fairness_note}": str(employee.get("fairness_note", "")),
        "{cluster_average_score}": f"{employee.get('cluster_average_score', 0):.2f}",
        "{fairness_group}": str(employee.get("fairness_group", "Team")),
        "{diff_class}": diff_class,
        "{anomaly_icon}": anomaly_icon,
        "{anomaly_text}": anomaly_text,
        "{anomaly_class}": anomaly_class,
    }
    
    for k, v in replacements.items():
        html = html.replace(k, str(v))
        
    components.html(html, height=1000, scrolling=True)


def managerial_view(df: pd.DataFrame, cluster_summary: pd.DataFrame) -> None:
    st.markdown(
        """
        <div style="margin-top: -1.5rem; padding-bottom: 2rem;">
            <div style="font-size: 11.5px; letter-spacing: .16em; text-transform: uppercase; color: #2DD4BF; font-weight: 700; margin-bottom: 8px;">
                Reward Engine · Admin
            </div>
            <h1 style="font-family: 'Fraunces', serif; font-weight: 600; font-size: 36px; margin:0; line-height: 1.2; text-align: left; background: none; -webkit-text-fill-color: #F3F0FA;">
                Executive <em style="color:#FFC857; font-style:italic;">Overview</em>.
            </h1>
        </div>
        """, unsafe_allow_html=True
    )

    average_score = df["total_score"].mean()
    gold_count = (df["badge_earned"] == "Gold Performance Badge").sum()
    review_count = df["needs_manager_review"].sum()
    average_points = df["reward_points"].mean()

    metric_cols = st.columns(4)
    with metric_cols[0]:
        st.markdown(
            f"""
            <div data-testid="stMetric">
                <div class="metric-label">Average Score</div>
                <div class="metric-value-large">{average_score:.2f}</div>
            </div>
            """, unsafe_allow_html=True
        )
    with metric_cols[1]:
        st.markdown(
            f"""
            <div data-testid="stMetric">
                <div class="metric-label">Avg Reward Points</div>
                <div class="metric-value-large">{average_points:.0f}</div>
            </div>
            """, unsafe_allow_html=True
        )
    with metric_cols[2]:
        st.markdown(
            f"""
            <div data-testid="stMetric">
                <div class="metric-label">Gold Badges</div>
                <div class="metric-value-large">{int(gold_count)}</div>
            </div>
            """, unsafe_allow_html=True
        )
    with metric_cols[3]:
        st.markdown(
            f"""
            <div data-testid="stMetric">
                <div class="metric-label">Review Cases</div>
                <div class="metric-value-large">{int(review_count)}</div>
            </div>
            """, unsafe_allow_html=True
        )

    st.markdown("<br/>", unsafe_allow_html=True)
    
    chart_col1, chart_col2 = st.columns(2)
    with chart_col1:
        st.subheader("Department Performance")
        dept_chart = alt.Chart(df).mark_bar(cornerRadiusTopLeft=8, cornerRadiusTopRight=8).encode(
            x=alt.X('department:N', title='Department', sort='-y'),
            y=alt.Y('mean(total_score):Q', title='Average Score'),
            color=alt.Color('department:N', legend=None)
        ).properties(height=300)
        st.altair_chart(dept_chart, use_container_width=True)
        
    with chart_col2:
        st.subheader("Badge Distribution")
        badge_counts = df['badge_earned'].value_counts().reset_index()
        badge_counts.columns = ['Badge', 'Count']
        badge_chart = alt.Chart(badge_counts).mark_arc(innerRadius=50).encode(
            theta=alt.Theta(field="Count", type="quantitative"),
            color=alt.Color(field="Badge", type="nominal", scale=alt.Scale(scheme='category20b')),
            tooltip=['Badge', 'Count']
        ).properties(height=300)
        st.altair_chart(badge_chart, use_container_width=True)

    st.subheader("AI Productivity Clusters")
    scatter = (
        alt.Chart(df)
        .mark_circle(size=120, opacity=0.78)
        .encode(
            x=alt.X("attendance_percent:Q", title="Attendance %"),
            y=alt.Y("project_completion_rate:Q", title="Project Completion %"),
            color=alt.Color("fairness_group:N", title="Fairness Group"),
            size=alt.Size("peer_feedback_score:Q", title="Peer Feedback"),
            tooltip=[
                "employee_id",
                "employee_name",
                "department",
                "total_score",
                "badge_earned",
                "fairness_group",
                "anomaly_flags",
            ],
        )
        .properties(height=380)
        .interactive()
    )
    st.altair_chart(scatter, use_container_width=True)

    st.subheader("Cluster Summary")
    st.dataframe(cluster_summary, use_container_width=True, hide_index=True)

    st.subheader("Reward Decisions")
    st.dataframe(
        df[
            [
                "employee_id",
                "employee_name",
                "department",
                "total_score",
                "reward_points",
                "badge_earned",
                "bonus_amount",
                "fairness_group",
                "needs_manager_review",
                "fairness_note",
            ]
        ].sort_values("total_score", ascending=False),
        use_container_width=True,
        hide_index=True,
    )

    st.subheader("Challenge Review: Technical Issues and Outliers")
    review_cases = df[df["needs_manager_review"]][
        [
            "employee_id",
            "employee_name",
            "department",
            "attendance_percent",
            "project_completion_rate",
            "peer_feedback_score",
            "anomaly_flags",
            "fairness_note",
        ]
    ]
    if review_cases.empty:
        st.success("No technical issues or outliers detected.")
    else:
        st.warning("Automatic rewards are paused for these records until a manager reviews them.")
        st.dataframe(review_cases, use_container_width=True, hide_index=True)

    st.subheader("Department Transparency")
    department_summary = (
        df.groupby("department")
        .agg(
            employees=("employee_id", "count"),
            average_score=("total_score", "mean"),
            average_points=("reward_points", "mean"),
            review_cases=("needs_manager_review", "sum"),
        )
        .reset_index()
    )
    department_summary[["average_score", "average_points"]] = department_summary[
        ["average_score", "average_points"]
    ].round(2)
    st.dataframe(department_summary, use_container_width=True, hide_index=True)


def export_and_assets_view(df: pd.DataFrame) -> None:
    st.title("Power BI Export and Canva AI Assets")

    output_path = Path(__file__).with_name("powerbi_reward_export.csv")
    if st.button("Create Power BI Export", type="primary"):
        export_powerbi_results(df, output_path)
        st.toast("Power BI export created.")
        st.success(f"Export created: {output_path}")

    csv_bytes = df.to_csv(index=False).encode("utf-8")
    st.download_button(
        "Download Current Analysis CSV",
        data=csv_bytes,
        file_name="powerbi_reward_export.csv",
        mime="text/csv",
    )

    st.subheader("Power BI Ready Columns")
    export_preview = df[
        [
            "employee_id",
            "employee_name",
            "department",
            "total_score",
            "reward_points",
            "badge_earned",
            "bonus_amount",
            "fairness_group",
            "needs_manager_review",
            "anomaly_flags",
            "motivation_trigger",
        ]
    ]
    st.dataframe(export_preview, use_container_width=True, hide_index=True)



def show_manager_dashboard() -> None:
    df, cluster_summary = get_analysis(DATA_FILE.stat().st_mtime)
    dashboard_tab, export_tab = st.tabs(["Dashboard", "Power BI and Canva Assets"])
    with dashboard_tab:
        managerial_view(df, cluster_summary)
    with export_tab:
        export_and_assets_view(df)


def show_employee_dashboard(user: dict[str, object]) -> None:
    df, _ = get_analysis(DATA_FILE.stat().st_mtime)
    employee_dashboard(df, user)


def protect_route(route: str, user: dict[str, object] | None) -> None:
    if route in {LOGIN_ROUTE, SIGNUP_ROUTE}:
        return

    if not user:
        queue_toast("Please sign in to continue.")
        set_route(LOGIN_ROUTE)

    if route == MANAGER_DASHBOARD_ROUTE and user["role"] != "manager":
        queue_toast("Manager access is restricted.")
        set_route(EMPLOYEE_DASHBOARD_ROUTE)

    if route == EMPLOYEE_DASHBOARD_ROUTE and user["role"] != "employee":
        queue_toast("Employee dashboard is restricted to employee accounts.")
        set_route(MANAGER_DASHBOARD_ROUTE)


def main() -> None:
    apply_theme()
    show_queued_toast()

    route = get_route()
    user = get_current_user()
    
    if route == "logout":
        logout()
        return
        
    protect_route(route, user)

    if route == LOGIN_ROUTE:
        if user:
            target = (
                MANAGER_DASHBOARD_ROUTE
                if user["role"] == "manager"
                else EMPLOYEE_DASHBOARD_ROUTE
            )
            set_route(target)
        show_login_page()
        return

    if route == SIGNUP_ROUTE:
        if user:
            logout()
        show_signup_page()
        return

    if not user:
        show_login_page()
        return

    if route == MANAGER_DASHBOARD_ROUTE:
        render_sidebar(user)
        show_manager_dashboard()
    elif route == EMPLOYEE_DASHBOARD_ROUTE:
        st.markdown(
            """
            <style>
            [data-testid="stSidebar"] { display: none !important; }
            .block-container { padding: 0 !important; max-width: 100% !important; }
            header[data-testid="stHeader"] { display: none !important; }
            
            /* Floating Logout Button */
            div[data-testid="stButton"] {
                position: fixed;
                bottom: 40px;
                right: 48px;
                z-index: 9999999;
            }
            div[data-testid="stButton"] button {
                background: rgba(251,113,133,0.12) !important;
                border: 1px solid rgba(251,113,133,0.4) !important;
                color: #fb7185 !important;
                padding: 10px 24px !important;
                border-radius: 12px !important;
                font-weight: 600 !important;
                transition: all 0.2s ease !important;
                font-family: 'Plus Jakarta Sans', sans-serif !important;
            }
            div[data-testid="stButton"] button:hover {
                background: rgba(251,113,133,0.25) !important;
                border-color: #fb7185 !important;
                color: #fff !important;
                transform: translateY(-2px) !important;
                box-shadow: 0 10px 20px rgba(251,113,133,0.2) !important;
            }
            </style>
            """, unsafe_allow_html=True
        )
        if st.button("Log out securely"):
            logout()
        show_employee_dashboard(user)
    else:
        target = (
            MANAGER_DASHBOARD_ROUTE
            if user["role"] == "manager"
            else EMPLOYEE_DASHBOARD_ROUTE
        )
        set_route(target)


if __name__ == "__main__":
    main()
