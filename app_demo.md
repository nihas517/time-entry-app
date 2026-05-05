# 🕐 Game Changer Time Entry App — Live Demo

**App URL:** https://time-entry-app-4jqh7d5xzzp8wjg5p6wxd8.streamlit.app/

Built on **Databricks Unity Catalog** + **Streamlit Community Cloud**  
Delta Lake · AI Anomaly Detection · Role-Based Login · Real-Time Budget Tracking

---

## 🔐 Login Credentials

| Name | Role | Username | Password |
|------|------|----------|----------|
| Niha Admin | Admin | `niha` | `Admin@Niha2024` |
| Sarah Johnson | Manager | `sarah` | `Mgr#Sarah01` |
| Tom Williams | Manager | `tom` | `Mgr#Tom01` |
| Alice Smith | Employee | `alice` | `Emp#Alice01` |
| Bob Patel | Employee | `bob` | `Emp#Bob01` |
| Carol Nguyen | Employee | `carol` | `Emp#Carol01` |
| David Chen | Employee | `david` | `Emp#David01` |

---

## 1. Login Page

Every user starts here. The role and dashboard are determined automatically by the credentials — no role dropdown needed.

![Login Page](screenshots/01_login.png)

---

## 2. Employee View

### Log Time
Employees select a project, pick a date, enter hours, describe their work, and submit for approval. The AI automatically flags entries over 10 hours or on weekends.

![Employee - Log Time](screenshots/02_employee_log_time.png)

### My Entries
All past entries shown with colour-coded status: **APPROVED** (green), **SUBMITTED** (orange), **REJECTED** (red), **DRAFT** (grey). Flagged entries show a 🚩 with the reason.

![Employee - My Entries](screenshots/03_employee_my_entries.png)

### My Stats
A pie chart showing hours distribution across projects over the last 4 weeks — only approved and submitted entries count.

![Employee - My Stats](screenshots/04_employee_my_stats.png)

---

## 3. Manager View

Managers see **only their direct reports** — Sarah sees Alice & Bob (Engineering), Tom sees Carol & David (Marketing).

### Pending Approvals
Each submitted entry is an expandable card showing employee name, project, hours, and work description. Flagged entries show a warning. Managers can add a comment before approving or rejecting.

![Manager - Pending Approvals](screenshots/05_manager_pending_approvals.png)

### Team Summary
Weekly snapshot of each direct report's total hours, approved hours, and pending hours. Employees who logged zero hours this week are highlighted.

![Manager - Team Summary](screenshots/06_manager_team_summary.png)

### Budget Status
Live progress bars for every active project — green under 80%, orange 80–99%, red over 100%.

![Manager - Budget Status](screenshots/07_manager_budget_status.png)

### Charts
Stacked bar chart of weekly hours by project, plus a line chart showing total team hours trend over the last 4 weeks.

![Manager - Charts](screenshots/08_manager_charts.png)

---

## 4. Admin View

The admin (Niha) has full access to all users, projects, and data across the entire organisation.

### Manage Users
All users displayed with name, email, role, department, active status, and username. Admin can add new users, auto-generate their login credentials, reset passwords, and deactivate accounts.

![Admin - Manage Users](screenshots/09_admin_manage_users.png)

### Manage Projects
View all projects with budget hours and status. Add new projects or close completed ones.

![Admin - Manage Projects](screenshots/10_admin_manage_projects.png)

### Full Report
Company-wide time entry data across all employees and departments. Downloadable as CSV for payroll or external reporting.

![Admin - Full Report](screenshots/11_admin_full_report.png)

---

## 🤖 AI Anomaly Detection

The system auto-flags suspicious entries in real time when saved, and in bulk via Databricks Notebook 03.

| Rule | Condition | Flag |
|------|-----------|------|
| Excessive Hours | > 10h in a single day | ⚠️ Excessive hours |
| Weekend Entry | Logged on Saturday or Sunday | ⚠️ Weekend entry |
| High Daily Total | > 12h total across entries on same day | ⚠️ High daily total |

Flagged entries are visible to managers in Pending Approvals with a 🚩 and warning banner.

---

## 🏗️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Data Warehouse | Databricks Unity Catalog |
| Storage | Delta Lake (ACID transactions) |
| Frontend | Streamlit (Python) |
| Charts | Plotly Express |
| Hosting | Streamlit Community Cloud |
| Source Control | GitHub (nihas517/time-entry-app) |
| Auth | SHA-256 password hashing |
| Connector | databricks-sql-connector |

---

*Last updated: May 2026*
