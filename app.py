import streamlit as st
from databricks import sql
import pandas as pd
import plotly.express as px
import uuid
import hashlib
import secrets
from datetime import datetime, date, timedelta

st.set_page_config(page_title="Game Changer Time Entry", layout="wide")

# ── Helpers ────────────────────────────────────────────────────────────────────
def get_conn():
    return sql.connect(
        server_hostname=st.secrets["DATABRICKS_HOST"],
        http_path=st.secrets["DATABRICKS_HTTP_PATH"],
        access_token=st.secrets["DATABRICKS_TOKEN"]
    )

def run_query(q, params=None):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(q, params or [])
            cols = [d[0] for d in cur.description]
            return pd.DataFrame(cur.fetchall(), columns=cols)

def run_update(q):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(q)

def new_id():
    return str(uuid.uuid4())[:8]

def safe(s):
    return str(s).replace("'", "''") if s else ""

def week_start(d=None):
    d = d or date.today()
    return d - timedelta(days=d.weekday())

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def generate_password():
    return secrets.token_urlsafe(8)

# ── Session State Init ─────────────────────────────────────────────────────────
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_id   = None
    st.session_state.user_name = None
    st.session_state.role      = None

# ════════════════════════════════════════════════════════════════════════════════
#  LOGIN PAGE
# ════════════════════════════════════════════════════════════════════════════════
if not st.session_state.logged_in:
    st.markdown("""
        <h1 style='text-align:center; margin-top: 80px;'>🕐 Game Changer Time Entry</h1>
        <p style='text-align:center; color:gray;'>Please log in to continue</p>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        with st.form("login_form"):
            st.markdown("### Login")
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            login_btn = st.form_submit_button("Login", use_container_width=True)

        if login_btn:
            if not username.strip() or not password.strip():
                st.error("Please enter both username and password.")
            else:
                ph = hash_password(password)
                result = run_query(f"""
                    SELECT u.user_id, u.name, u.role, u.is_active
                    FROM workspace.time_tracker.user_credentials uc
                    JOIN workspace.time_tracker.users u ON uc.user_id = u.user_id
                    WHERE uc.username = '{safe(username.strip())}' AND uc.password_hash = '{ph}'
                """)
                if result.empty:
                    st.error("Invalid username or password.")
                elif not bool(result.iloc[0]["is_active"]):
                    st.error("Your account has been deactivated. Please contact your admin.")
                else:
                    st.session_state.logged_in = True
                    st.session_state.user_id   = result.iloc[0]["user_id"]
                    st.session_state.user_name = result.iloc[0]["name"]
                    st.session_state.role      = result.iloc[0]["role"]
                    st.rerun()
    st.stop()

# ── Logged-in vars ─────────────────────────────────────────────────────────────
user_id   = st.session_state.user_id
user_name = st.session_state.user_name
role      = st.session_state.role

# ── Sidebar ────────────────────────────────────────────────────────────────────
st.sidebar.title("Game Changer Time Entry")
st.sidebar.markdown(f"**👤 {user_name}**")
st.sidebar.markdown(f"Role: `{role.title()}`")
st.sidebar.markdown("---")
if st.sidebar.button("🚪 Logout"):
    st.session_state.logged_in = False
    st.session_state.user_id   = None
    st.session_state.user_name = None
    st.session_state.role      = None
    st.rerun()

# ════════════════════════════════════════════════════════════════════════════════
#  EMPLOYEE VIEW
# ════════════════════════════════════════════════════════════════════════════════
if role == "employee":
    st.title(f"My Time Entries — {user_name}")
    tab1, tab2, tab3 = st.tabs(["Log Time", "My Entries", "My Stats"])

    # ── Log Time ──────────────────────────────────────────────────────────────
    with tab1:
        st.subheader("Log New Time Entry")
        projects = run_query("SELECT project_id, project_name, project_code FROM workspace.time_tracker.projects WHERE status='active' ORDER BY project_code")
        proj_options = {f"{r['project_code']} - {r['project_name']}": r['project_id'] for _, r in projects.iterrows()}

        with st.form("log_time"):
            selected_proj = st.selectbox("Project:", list(proj_options.keys()))
            entry_date    = st.date_input("Date:", value=date.today())
            hours         = st.number_input("Hours:", min_value=0.5, max_value=24.0, step=0.5, value=8.0)
            description   = st.text_area("What did you work on?", height=100)
            submit_now    = st.checkbox("Submit for approval now", value=True)
            submitted     = st.form_submit_button("Save Entry")

        if submitted:
            if not description.strip():
                st.error("Please add a description.")
            else:
                proj_id    = proj_options[selected_proj]
                status     = "submitted" if submit_now else "draft"
                ws         = str(week_start(entry_date))
                entry_id   = new_id()
                now_ts     = datetime.now().isoformat()
                flag        = False
                flag_reason = ""

                if hours > 10:
                    flag        = True
                    flag_reason = "Excessive hours: more than 10h in a single day"
                if entry_date.weekday() >= 5:
                    flag        = True
                    flag_reason = (flag_reason + " | " if flag_reason else "") + "Weekend entry"

                run_update(f"""
                    INSERT INTO workspace.time_tracker.time_entries
                    (entry_id, user_id, project_id, entry_date, hours, description,
                     status, week_start, is_flagged, flag_reason,
                     submitted_at, created_at, updated_at)
                    VALUES ('{entry_id}', '{user_id}', '{proj_id}', '{entry_date}',
                            {hours}, '{safe(description)}', '{status}', '{ws}',
                            {flag}, '{flag_reason}', '{now_ts}', '{now_ts}', '{now_ts}')
                """)

                if flag:
                    st.warning(f"Entry saved but flagged: {flag_reason}")
                else:
                    st.success(f"Entry saved! Status: {status.upper()}")
                st.rerun()

    # ── My Entries ────────────────────────────────────────────────────────────
    with tab2:
        st.subheader("My Time Entries")
        df = run_query(f"""
            SELECT te.entry_date, p.project_code, te.hours, te.description,
                   te.status, te.is_flagged, te.flag_reason
            FROM workspace.time_tracker.time_entries te
            JOIN workspace.time_tracker.projects p ON te.project_id = p.project_id
            WHERE te.user_id = '{user_id}'
            ORDER BY te.entry_date DESC
        """)
        if df.empty:
            st.info("No entries yet. Use the Log Time tab to add your first entry.")
        else:
            colour_map = {"approved": "green", "submitted": "orange", "rejected": "red", "draft": "gray"}
            for _, row in df.iterrows():
                flag_txt = f"  🚩 {row['flag_reason']}" if row["is_flagged"] else ""
                c = colour_map.get(row["status"], "black")
                st.markdown(f"**{row['entry_date']}** | {row['project_code']} | {row['hours']}h | :{c}[{str(row['status']).upper()}]{flag_txt}")
                st.caption(row["description"])
                st.divider()

    # ── My Stats ──────────────────────────────────────────────────────────────
    with tab3:
        st.subheader("My Hours by Project — Last 4 Weeks")
        df = run_query(f"""
            SELECT p.project_code, ROUND(SUM(te.hours), 1) AS hours
            FROM workspace.time_tracker.time_entries te
            JOIN workspace.time_tracker.projects p ON te.project_id = p.project_id
            WHERE te.user_id = '{user_id}'
              AND te.status IN ('submitted', 'approved')
              AND te.entry_date >= date_sub(current_date(), 28)
            GROUP BY p.project_code
            ORDER BY hours DESC
        """)
        if df.empty:
            st.info("No approved or submitted entries in the last 4 weeks.")
        else:
            fig = px.pie(df, values="hours", names="project_code",
                         title="My Hours by Project (Last 4 Weeks)")
            st.plotly_chart(fig, use_container_width=True)

# ════════════════════════════════════════════════════════════════════════════════
#  MANAGER VIEW
# ════════════════════════════════════════════════════════════════════════════════
elif role == "manager":
    st.title(f"Manager Dashboard — {user_name}")
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "Pending Approvals", "Bulk Approve", "Team Summary", "Charts", "Budget Status"
    ])

    # ── Pending Approvals ─────────────────────────────────────────────────────
    with tab1:
        st.subheader("Entries Awaiting Your Approval")
        df = run_query(f"""
            SELECT te.entry_id, u.name AS employee, p.project_code,
                   te.entry_date, te.hours, te.description,
                   te.is_flagged, te.flag_reason
            FROM workspace.time_tracker.time_entries te
            JOIN workspace.time_tracker.users u ON te.user_id = u.user_id
            JOIN workspace.time_tracker.projects p ON te.project_id = p.project_id
            WHERE te.status = 'submitted' AND u.manager_id = '{user_id}'
            ORDER BY te.submitted_at ASC
        """)
        if df.empty:
            st.success("No pending approvals!")
        else:
            for _, row in df.iterrows():
                label = f"{row['employee']} | {row['project_code']} | {row['entry_date']} | {row['hours']}h"
                if row["is_flagged"]:
                    label += "  🚩"
                with st.expander(label):
                    st.write(f"**Description:** {row['description']}")
                    if row["is_flagged"]:
                        st.warning(f"Flagged: {row['flag_reason']}")
                    comment = st.text_input("Comment (optional):", key=f"c_{row['entry_id']}")
                    col1, col2 = st.columns(2)
                    if col1.button("✅ Approve", key=f"a_{row['entry_id']}"):
                        run_update(f"UPDATE workspace.time_tracker.time_entries SET status='approved', updated_at=current_timestamp() WHERE entry_id='{row['entry_id']}'")
                        run_update(f"INSERT INTO workspace.time_tracker.approvals VALUES ('{new_id()}', '{row['entry_id']}', '{user_id}', 'approved', '{safe(comment)}', current_timestamp())")
                        st.success("Approved!")
                        st.rerun()
                    if col2.button("❌ Reject", key=f"r_{row['entry_id']}"):
                        run_update(f"UPDATE workspace.time_tracker.time_entries SET status='rejected', updated_at=current_timestamp() WHERE entry_id='{row['entry_id']}'")
                        run_update(f"INSERT INTO workspace.time_tracker.approvals VALUES ('{new_id()}', '{row['entry_id']}', '{user_id}', 'rejected', '{safe(comment)}', current_timestamp())")
                        st.error("Rejected.")
                        st.rerun()

    # ── Bulk Approve ──────────────────────────────────────────────────────────
    with tab2:
        st.subheader("Bulk Approve / Reject")
        df = run_query(f"""
            SELECT te.entry_id, u.name AS employee, p.project_code,
                   te.entry_date, te.hours, te.is_flagged
            FROM workspace.time_tracker.time_entries te
            JOIN workspace.time_tracker.users u ON te.user_id = u.user_id
            JOIN workspace.time_tracker.projects p ON te.project_id = p.project_id
            WHERE te.status = 'submitted' AND u.manager_id = '{user_id}'
        """)
        if df.empty:
            st.success("Nothing pending.")
        else:
            df.insert(0, "Select", False)
            edited = st.data_editor(df[["Select", "employee", "project_code", "entry_date", "hours", "is_flagged"]],
                                    use_container_width=True, hide_index=True)
            selected_ids = df[edited["Select"]]["entry_id"].tolist()
            col1, col2 = st.columns(2)
            if col1.button(f"✅ Approve Selected ({len(selected_ids)})"):
                for eid in selected_ids:
                    run_update(f"UPDATE workspace.time_tracker.time_entries SET status='approved', updated_at=current_timestamp() WHERE entry_id='{eid}'")
                    run_update(f"INSERT INTO workspace.time_tracker.approvals VALUES ('{new_id()}', '{eid}', '{user_id}', 'approved', 'Bulk approved', current_timestamp())")
                st.success(f"Approved {len(selected_ids)} entries!")
                st.rerun()
            if col2.button(f"❌ Reject Selected ({len(selected_ids)})"):
                for eid in selected_ids:
                    run_update(f"UPDATE workspace.time_tracker.time_entries SET status='rejected', updated_at=current_timestamp() WHERE entry_id='{eid}'")
                    run_update(f"INSERT INTO workspace.time_tracker.approvals VALUES ('{new_id()}', '{eid}', '{user_id}', 'rejected', 'Bulk rejected', current_timestamp())")
                st.error(f"Rejected {len(selected_ids)} entries.")
                st.rerun()

    # ── Team Summary ──────────────────────────────────────────────────────────
    with tab3:
        st.subheader("Team Summary — This Week")
        ws = str(week_start())
        df = run_query(f"""
            SELECT u.name, u.department,
                   COALESCE(SUM(te.hours), 0) AS total_hours,
                   SUM(CASE WHEN te.status='approved'  THEN te.hours ELSE 0 END) AS approved_h,
                   SUM(CASE WHEN te.status='submitted' THEN te.hours ELSE 0 END) AS pending_h
            FROM workspace.time_tracker.users u
            LEFT JOIN workspace.time_tracker.time_entries te
                ON u.user_id = te.user_id AND te.week_start = '{ws}'
            WHERE u.role = 'employee' AND u.manager_id = '{user_id}' AND u.is_active = true
            GROUP BY u.name, u.department
            ORDER BY total_hours DESC
        """)
        st.dataframe(df, use_container_width=True)
        no_time = df[df["total_hours"] == 0]["name"].tolist()
        if no_time:
            st.warning(f"No time logged this week: {', '.join(no_time)}")

    # ── Charts ────────────────────────────────────────────────────────────────
    with tab4:
        st.subheader("Team Hours — Last 4 Weeks")
        df = run_query(f"""
            SELECT CAST(te.week_start AS STRING) AS week_start,
                   p.project_code,
                   ROUND(SUM(te.hours), 1) AS hours
            FROM workspace.time_tracker.time_entries te
            JOIN workspace.time_tracker.users u ON te.user_id = u.user_id
            JOIN workspace.time_tracker.projects p ON te.project_id = p.project_id
            WHERE u.manager_id = '{user_id}'
              AND te.status IN ('submitted', 'approved')
              AND te.entry_date >= date_sub(current_date(), 28)
            GROUP BY te.week_start, p.project_code
            ORDER BY te.week_start
        """)
        if not df.empty:
            fig = px.bar(df, x="week_start", y="hours", color="project_code",
                         title="Weekly Hours by Project", barmode="stack")
            st.plotly_chart(fig, use_container_width=True)
            weekly = df.groupby("week_start")["hours"].sum().reset_index()
            fig2 = px.line(weekly, x="week_start", y="hours",
                           title="Total Team Hours per Week", markers=True)
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("No data yet for charts.")

    # ── Budget Status ─────────────────────────────────────────────────────────
    with tab5:
        st.subheader("Project Budget Status")
        df = run_query("""
            SELECT p.project_code, p.project_name, p.budget_hours,
                   ROUND(COALESCE(SUM(te.hours), 0), 1) AS logged,
                   ROUND(COALESCE(SUM(te.hours), 0) / NULLIF(p.budget_hours, 0) * 100, 1) AS pct
            FROM workspace.time_tracker.projects p
            LEFT JOIN workspace.time_tracker.time_entries te
                ON p.project_id = te.project_id AND te.status IN ('submitted', 'approved')
            WHERE p.status = 'active'
            GROUP BY p.project_code, p.project_name, p.budget_hours
            ORDER BY pct DESC
        """)
        for _, row in df.iterrows():
            pct    = float(row["pct"]) if row["pct"] else 0.0
            colour = "red" if pct >= 100 else "orange" if pct >= 80 else "green"
            st.markdown(f"**{row['project_code']}** — {row['project_name']}")
            st.progress(min(pct / 100, 1.0))
            st.markdown(f":{colour}[{row['logged']}h / {row['budget_hours']}h ({pct:.1f}%)]")
            st.divider()
        if not df.empty:
            fig = px.bar(df, x="pct", y="project_code", orientation="h",
                         title="Budget Burn-down (%)", color="pct",
                         color_continuous_scale=["green", "orange", "red"],
                         range_color=[0, 120])
            fig.add_vline(x=80,  line_dash="dash", line_color="orange", annotation_text="80%")
            fig.add_vline(x=100, line_dash="dash", line_color="red",    annotation_text="100%")
            st.plotly_chart(fig, use_container_width=True)

# ════════════════════════════════════════════════════════════════════════════════
#  ADMIN VIEW
# ════════════════════════════════════════════════════════════════════════════════
elif role == "admin":
    st.title(f"Admin Panel — {user_name}")
    tab1, tab2, tab3 = st.tabs(["Manage Users", "Manage Projects", "Full Report"])

    # ── Manage Users ──────────────────────────────────────────────────────────
    with tab1:
        st.subheader("All Users")
        df = run_query("""
            SELECT u.user_id, u.name, u.email, u.role, u.department, u.is_active, uc.username
            FROM workspace.time_tracker.users u
            LEFT JOIN workspace.time_tracker.user_credentials uc ON u.user_id = uc.user_id
            ORDER BY u.role, u.name
        """)
        st.dataframe(df[["name", "email", "role", "department", "is_active", "username"]], use_container_width=True)

        st.subheader("Add New User")
        with st.form("add_user"):
            n_name     = st.text_input("Full Name")
            n_email    = st.text_input("Email")
            n_role     = st.selectbox("Role", ["employee", "manager", "admin"])
            n_dept     = st.text_input("Department")
            mgrs       = run_query("SELECT user_id, name FROM workspace.time_tracker.users WHERE role='manager' AND is_active=true")
            mgr_map    = {"None": ""} | {r["name"]: r["user_id"] for _, r in mgrs.iterrows()}
            n_mgr      = st.selectbox("Manager (for employees):", list(mgr_map.keys()))
            st.markdown("**Login Credentials**")
            n_username = st.text_input("Username (e.g. alice.smith)")
            n_password = st.text_input("Password", value=generate_password(),
                                       help="Auto-generated — you can change it before saving")
            if st.form_submit_button("Add User & Create Login"):
                if not n_name.strip() or not n_username.strip() or not n_password.strip():
                    st.error("Name, username, and password are all required.")
                else:
                    # Check if username already exists
                    existing = run_query(f"SELECT username FROM workspace.time_tracker.user_credentials WHERE username = '{safe(n_username.strip())}'")
                    if not existing.empty:
                        st.error(f"Username '{n_username}' is already taken. Please choose another.")
                    else:
                        mgr_val = f"'{mgr_map[n_mgr]}'" if mgr_map[n_mgr] else "NULL"
                        uid     = new_id()
                        ph      = hash_password(n_password)
                        run_update(f"INSERT INTO workspace.time_tracker.users VALUES ('{uid}', '{safe(n_name)}', '{safe(n_email)}', '{n_role}', {mgr_val}, '{safe(n_dept)}', true, current_timestamp())")
                        run_update(f"INSERT INTO workspace.time_tracker.user_credentials VALUES ('{uid}', '{safe(n_username.strip())}', '{ph}', current_timestamp(), current_timestamp())")
                        st.success(f"✅ User **{n_name}** added!")
                        st.info(f"Share these login details with them:\n\n**Username:** `{n_username.strip()}`\n\n**Password:** `{n_password}`")
                        st.rerun()

        st.subheader("Reset User Password")
        with st.form("reset_pw"):
            all_users  = run_query("SELECT u.name, uc.username FROM workspace.time_tracker.users u JOIN workspace.time_tracker.user_credentials uc ON u.user_id = uc.user_id WHERE u.is_active=true ORDER BY u.name")
            user_names = all_users["name"].tolist()
            reset_user = st.selectbox("Select user:", user_names)
            new_pw     = st.text_input("New Password", value=generate_password())
            if st.form_submit_button("Reset Password"):
                uid_row = run_query(f"SELECT u.user_id FROM workspace.time_tracker.users u WHERE u.name = '{safe(reset_user)}'")
                if not uid_row.empty:
                    ph = hash_password(new_pw)
                    run_update(f"UPDATE workspace.time_tracker.user_credentials SET password_hash = '{ph}', updated_at = current_timestamp() WHERE user_id = '{uid_row.iloc[0]['user_id']}'")
                    st.success(f"Password reset for **{reset_user}**")
                    st.info(f"New password: `{new_pw}`")

        st.subheader("Deactivate User")
        active_users = df[df["is_active"] == True]["name"].tolist()
        if active_users:
            deact = st.selectbox("Select user to deactivate:", active_users)
            if st.button("Deactivate"):
                uid = df[df["name"] == deact]["user_id"].iloc[0]
                run_update(f"UPDATE workspace.time_tracker.users SET is_active=false WHERE user_id='{uid}'")
                st.warning(f"{deact} has been deactivated.")
                st.rerun()

    # ── Manage Projects ───────────────────────────────────────────────────────
    with tab2:
        st.subheader("All Projects")
        df = run_query("SELECT project_code, project_name, budget_hours, status FROM workspace.time_tracker.projects ORDER BY project_code")
        st.dataframe(df, use_container_width=True)

        st.subheader("Add New Project")
        with st.form("add_proj"):
            p_name   = st.text_input("Project Name")
            p_code   = st.text_input("Project Code (e.g. PROJ-006)")
            p_desc   = st.text_area("Description")
            p_budget = st.number_input("Budget Hours", min_value=1.0, value=100.0, step=10.0)
            if st.form_submit_button("Add Project"):
                pid = new_id()
                run_update(f"INSERT INTO workspace.time_tracker.projects VALUES ('{pid}', '{safe(p_name)}', '{safe(p_code)}', '{safe(p_desc)}', {p_budget}, 'active', current_timestamp(), current_timestamp())")
                st.success(f"Project {p_code} added!")
                st.rerun()

        st.subheader("Close a Project")
        active_projs = df[df["status"] == "active"]["project_code"].tolist()
        if active_projs:
            close_proj = st.selectbox("Select project to close:", active_projs)
            if st.button("Close Project"):
                run_update(f"UPDATE workspace.time_tracker.projects SET status='completed', updated_at=current_timestamp() WHERE project_code='{close_proj}'")
                st.warning(f"{close_proj} marked as completed.")
                st.rerun()

    # ── Full Report ───────────────────────────────────────────────────────────
    with tab3:
        st.subheader("Company-Wide Time Entry Report")
        df = run_query("""
            SELECT u.name AS employee, u.department, p.project_code,
                   te.entry_date, te.hours, te.status, te.is_flagged, te.flag_reason
            FROM workspace.time_tracker.time_entries te
            JOIN workspace.time_tracker.users u ON te.user_id = u.user_id
            JOIN workspace.time_tracker.projects p ON te.project_id = p.project_id
            ORDER BY te.entry_date DESC
        """)
        st.dataframe(df, use_container_width=True)
        csv = df.to_csv(index=False)
        st.download_button("Download CSV", csv, "time_entries_report.csv", "text/csv")
