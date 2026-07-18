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
        @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&display=swap');
        
        html, body, [data-testid="stAppViewContainer"] {
            font-family: 'Outfit', sans-serif;
            background: radial-gradient(circle at 15% 50%, #0f172a, #020617 100%);
            color: #f8fafc;
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

    with st.container(border=True):
        st.subheader("Login")
        
        show_password = st.toggle("Show password", key="login_show_pwd")
        
        with st.form("login_form", border=False):
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
            st.write("Employee: aarav.sharma@company.com / Employee@123")

    close_auth_header()


def show_signup_page() -> None:
    show_auth_header("New employee account setup")

    with st.container(border=True):
        st.subheader("Employee Sign-Up")
        
        show_password = st.toggle("Show password", key="signup_show_pwd")
        
        with st.form("signup_form", border=False):
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
    st.sidebar.title("SmartRewardX")
    st.sidebar.write(user["full_name"])
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
    st.title("Employee Dashboard")

    employee_id = str(user["employee_id"]).upper()
    matched = df[df["employee_id"].str.upper() == employee_id]

    if matched.empty:
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
    
    # Map legacy placeholders from CSV to actual asset paths
    asset_map = {
        "canva_badge_gold_placeholder": "assets/badge_gold.png",
        "canva_badge_silver_placeholder": "assets/badge_silver.png",
        "canva_badge_bronze_placeholder": "assets/badge_bronze.png",
        "canva_badge_progress_placeholder": "assets/badge_progress.png",
        "canva_badge_support_placeholder": "assets/badge_support.png",
        "canva_certificate_gold_placeholder": "assets/certificate_gold.png",
        "canva_certificate_silver_placeholder": "assets/certificate_silver.png",
        "canva_certificate_bronze_placeholder": "assets/certificate_bronze.png",
        "canva_certificate_progress_placeholder": "assets/certificate_progress.png",
        "canva_certificate_support_placeholder": "assets/certificate_support.png",
    }
    
    if employee["canva_badge_placeholder"] in asset_map:
        employee["canva_badge_placeholder"] = asset_map[employee["canva_badge_placeholder"]]
    if employee["canva_certificate_placeholder"] in asset_map:
        employee["canva_certificate_placeholder"] = asset_map[employee["canva_certificate_placeholder"]]

    st.subheader(f"{employee['employee_name']} | {employee['role']}")
    st.caption(f"Department: {employee['department']} | Employee ID: {employee['employee_id']}")

    score_col, points_col, badge_col, cluster_col = st.columns(4)
    
    with score_col:
        st.markdown(
            f"""
            <div data-testid="stMetric">
                <div class="metric-label">Total Score</div>
                <div class="metric-value-large">{format_score(employee["total_score"])}</div>
            </div>
            """,
            unsafe_allow_html=True
        )
    
    with points_col:
        st.markdown(
            f"""
            <div data-testid="stMetric">
                <div class="metric-label">Reward Points</div>
                <div class="metric-value-large">{int(employee["reward_points"])}</div>
            </div>
            """,
            unsafe_allow_html=True
        )
    
    with badge_col:
        with st.container(border=True):
            st.markdown('<div class="metric-label" style="text-align:center">Badge Tier</div>', unsafe_allow_html=True)
            st.markdown('<div class="metric-container-inner">', unsafe_allow_html=True)
            c1, c2, c3 = st.columns([1, 2, 1])
            with c2:
                try:
                    st.image(employee["canva_badge_placeholder"], width=80)
                except:
                    st.markdown(f'<div class="metric-value-large" style="font-size:1.2rem !important; text-align:center;">{employee["badge_earned"]}</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
    
    with cluster_col:
        with st.container(border=True):
            st.markdown('<div class="metric-label" style="text-align:center">Fairness Group</div>', unsafe_allow_html=True)
            st.markdown('<div class="metric-container-inner">', unsafe_allow_html=True)
            fairness_img = {
                "High productivity peer group": "assets/fairness_high.png",
                "Consistent productivity peer group": "assets/fairness_consistent.png",
                "Growth support peer group": "assets/fairness_growth.png"
            }.get(employee["fairness_group"], "")
            
            c1, c2, c3 = st.columns([1, 2, 1])
            with c2:
                try:
                    if fairness_img:
                        st.image(fairness_img, width=80)
                    else:
                        st.markdown(f'<div class="metric-value-large" style="font-size:1.1rem !important; text-align:center;">{employee["fairness_group"]}</div>', unsafe_allow_html=True)
                except:
                    st.markdown(f'<div class="metric-value-large" style="font-size:1.1rem !important; text-align:center;">{employee["fairness_group"]}</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div style="margin-top: 1rem;"></div>', unsafe_allow_html=True)
    st.markdown('<div class="badge-container">', unsafe_allow_html=True)
    st.markdown(f"### {employee['badge_earned']}")
    st.write(f"**Reward:** {employee['reward_action']}")
    st.markdown('</div>', unsafe_allow_html=True)

    st.divider()

    chart_col, logic_col = st.columns([1.1, 0.9])

    with chart_col:
        st.subheader("Historical Attendance")
        attendance_history = pd.DataFrame(
            {
                "month": ["Jan", "Feb", "Mar", "Apr"],
                "attendance_percent": [
                    employee[column] for column in ATTENDANCE_HISTORY_COLUMNS
                ],
            }
        )
        st.line_chart(
            attendance_history,
            x="month",
            y="attendance_percent",
            height=260,
        )

        st.subheader("Current Reward Decision")
        st.write(employee["reward_action"])
        st.info(employee["motivation_trigger"])

    with logic_col:
        st.subheader("Reward Logic")
        st.write(
            "Total Score = "
            f"({WEIGHTS['attendance_percent']} x Attendance) + "
            f"({WEIGHTS['project_completion_rate']} x Performance) + "
            f"({WEIGHTS['peer_feedback_score']} x Feedback)"
        )

        components = pd.DataFrame(
            [
                {
                    "Metric": "Attendance",
                    "Raw Score": employee["attendance_percent"],
                    "Weight": WEIGHTS["attendance_percent"],
                    "Weighted Points": employee["attendance_component"],
                },
                {
                    "Metric": "Performance",
                    "Raw Score": employee["project_completion_rate"],
                    "Weight": WEIGHTS["project_completion_rate"],
                    "Weighted Points": employee["performance_component"],
                },
                {
                    "Metric": "Peer Feedback",
                    "Raw Score": employee["peer_feedback_score"],
                    "Weight": WEIGHTS["peer_feedback_score"],
                    "Weighted Points": employee["feedback_component"],
                },
            ]
        )
        st.dataframe(components, use_container_width=True, hide_index=True)

        st.subheader("Fairness Check")
        st.write(employee["fairness_note"])
        st.write(f"Peer-group average score: {employee['cluster_average_score']:.2f}")
        st.write(f"Difference from peer group: {employee['score_vs_peer_group']:+.2f}")

        if employee["needs_manager_review"]:
            st.warning(employee["anomaly_flags"])
        else:
            st.success("No anomaly flags for this record.")

    st.divider()
    st.subheader("Your Achievement Certificate")
    
    st.markdown('<div class="certificate-container">', unsafe_allow_html=True)
    try:
        st.image(employee["canva_certificate_placeholder"], use_container_width=True)
        
        # Add a download button for the certificate
        with open(employee["canva_certificate_placeholder"], "rb") as f:
            st.download_button(
                label="Download Certificate",
                data=f,
                file_name=f"Certificate_{employee['employee_id']}.png",
                mime="image/png",
                use_container_width=True
            )
    except:
        st.info("Certificate asset is being generated or was not found in the assets folder.")
    st.markdown('</div>', unsafe_allow_html=True)


def managerial_view(df: pd.DataFrame, cluster_summary: pd.DataFrame) -> None:
    st.title("Managerial View")

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

    render_sidebar(user)

    if route == MANAGER_DASHBOARD_ROUTE:
        show_manager_dashboard()
    elif route == EMPLOYEE_DASHBOARD_ROUTE:
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
