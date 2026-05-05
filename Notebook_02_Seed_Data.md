# Notebook 02 — Seed Data & Business Logic (Unity Catalog)

Create a new notebook called `02_Seed_Data` and run each cell in order.

---

## Cell 1 — Seed Users

```python
# Cell 1: Insert sample users (managers + employees)
from datetime import datetime
import uuid

def new_id():
    return str(uuid.uuid4())[:8]

now = datetime.now()

# Generate IDs upfront so we can cross-reference manager_id
mgr1_id = new_id()
mgr2_id = new_id()
emp1_id = new_id()
emp2_id = new_id()
emp3_id = new_id()
emp4_id = new_id()

users_data = [
    (mgr1_id, "Sarah Johnson",  "sarah@company.com",  "manager",  None,    "Engineering",  True, now),
    (mgr2_id, "Tom Williams",   "tom@company.com",    "manager",  None,    "Marketing",    True, now),
    (emp1_id, "Alice Smith",    "alice@company.com",  "employee", mgr1_id, "Engineering",  True, now),
    (emp2_id, "Bob Patel",      "bob@company.com",    "employee", mgr1_id, "Engineering",  True, now),
    (emp3_id, "Carol Nguyen",   "carol@company.com",  "employee", mgr2_id, "Marketing",    True, now),
    (emp4_id, "David Chen",     "david@company.com",  "employee", mgr2_id, "Marketing",    True, now),
]

schema = ["user_id","name","email","role","manager_id","department","is_active","created_at"]
users_df = spark.createDataFrame(users_data, schema)
users_df.write.mode("overwrite").saveAsTable("workspace.time_tracker.users")
print(f"✅ Inserted {users_df.count()} users")
spark.sql("SELECT user_id, name, role, department FROM workspace.time_tracker.users ORDER BY role, name").show()
```

---

## Cell 2 — Seed Projects

```python
# Cell 2: Insert sample projects
from datetime import datetime
import uuid

def new_id():
    return str(uuid.uuid4())[:8]

now = datetime.now()

projects_data = [
    (new_id(), "Customer Portal Redesign",    "PROJ-001", "Full redesign of customer-facing portal",         400.0, "active",    now, now),
    (new_id(), "Mobile App v2.0",             "PROJ-002", "New mobile application release",                  300.0, "active",    now, now),
    (new_id(), "Q3 Marketing Campaign",       "PROJ-003", "Multi-channel Q3 campaign execution",             150.0, "active",    now, now),
    (new_id(), "Staff Onboarding Revamp",     "PROJ-004", "Improve onboarding experience",                   80.0,  "active",    now, now),
    (new_id(), "Legacy System Migration",     "PROJ-005", "Migrate from legacy ERP to cloud platform",       500.0, "active",    now, now),
]

schema = ["project_id","project_name","project_code","description","budget_hours","status","created_at","updated_at"]
projects_df = spark.createDataFrame(projects_data, schema)
projects_df.write.mode("overwrite").saveAsTable("workspace.time_tracker.projects")
print(f"✅ Inserted {projects_df.count()} projects")
spark.sql("SELECT project_code, project_name, budget_hours, status FROM workspace.time_tracker.projects ORDER BY project_code").show()
```

---

## Cell 3 — Seed Time Entries (4 weeks of data)

```python
# Cell 3: Generate 4 weeks of sample time entries
from datetime import datetime, date, timedelta
import uuid

def new_id():
    return str(uuid.uuid4())[:8]

now = datetime.now()

# Fetch IDs from the tables
users = {r['name']: r['user_id'] for r in spark.sql(
    "SELECT user_id, name FROM workspace.time_tracker.users WHERE role='employee'"
).collect()}

projs = {r['project_code']: r['project_id'] for r in spark.sql(
    "SELECT project_id, project_code FROM workspace.time_tracker.projects"
).collect()}

print("Users found:", list(users.keys()))
print("Projects found:", list(projs.keys()))

today = date.today()

# Each employee's typical weekly assignments
sample_assignments = [
    ("Alice Smith",  "PROJ-001", 6.0, "Backend API development"),
    ("Alice Smith",  "PROJ-002", 5.0, "Mobile app feature work"),
    ("Bob Patel",    "PROJ-001", 7.0, "Database optimisation"),
    ("Bob Patel",    "PROJ-005", 5.0, "Legacy system migration tasks"),
    ("Carol Nguyen", "PROJ-003", 6.0, "Campaign asset creation"),
    ("Carol Nguyen", "PROJ-004", 2.0, "Onboarding content writing"),
    ("David Chen",   "PROJ-003", 4.0, "Social media scheduling"),
    ("David Chen",   "PROJ-004", 3.0, "Onboarding training completion"),
]

entries = []
for week_offset in range(-3, 1):  # last 3 weeks + current week
    ws = today - timedelta(days=today.weekday()) + timedelta(weeks=week_offset)
    for name, proj_code, hrs, desc in sample_assignments:
        if name not in users or proj_code not in projs:
            continue
        entry_date = ws + timedelta(days=1)  # Tuesday of each week
        entries.append((
            new_id(),
            users[name],
            projs[proj_code],
            entry_date,
            hrs,
            desc,
            "approved",   # mark as approved so budget charts show data
            ws,
            False,
            None,
            now, now, now
        ))

schema = [
    "entry_id","user_id","project_id","entry_date","hours","description",
    "status","week_start","is_flagged","flag_reason",
    "submitted_at","created_at","updated_at"
]

entries_df = spark.createDataFrame(entries, schema)
entries_df.write.mode("overwrite").saveAsTable("workspace.time_tracker.time_entries")
print(f"✅ Inserted {entries_df.count()} time entries across 4 weeks")
```

---

## Cell 4 — Add a Few Pending Entries (for approval testing)

```python
# Cell 4: Add some submitted (pending) entries this week for managers to approve
from datetime import datetime, date, timedelta
import uuid

def new_id():
    return str(uuid.uuid4())[:8]

now = datetime.now()

users = {r['name']: r['user_id'] for r in spark.sql(
    "SELECT user_id, name FROM workspace.time_tracker.users WHERE role='employee'"
).collect()}

projs = {r['project_code']: r['project_id'] for r in spark.sql(
    "SELECT project_id, project_code FROM workspace.time_tracker.projects"
).collect()}

today = date.today()
ws = today - timedelta(days=today.weekday())  # this Monday

pending = [
    ("Alice Smith",  "PROJ-001", 8.0, "API endpoint development", today),
    ("Bob Patel",    "PROJ-005", 7.5, "Data migration scripting",  today),
    ("Carol Nguyen", "PROJ-003", 6.0, "Campaign copy review",      today),
    ("David Chen",   "PROJ-003", 11.5, "Social media blitz",       today),  # will be flagged >10h
]

entries = []
for name, proj_code, hrs, desc, edate in pending:
    if name not in users or proj_code not in projs:
        continue
    entries.append((
        new_id(), users[name], projs[proj_code],
        edate, hrs, desc,
        "submitted", ws,
        False, None,
        now, now, now
    ))

schema = [
    "entry_id","user_id","project_id","entry_date","hours","description",
    "status","week_start","is_flagged","flag_reason",
    "submitted_at","created_at","updated_at"
]
df = spark.createDataFrame(entries, schema)
df.write.mode("append").saveAsTable("workspace.time_tracker.time_entries")
print(f"✅ Inserted {df.count()} pending entries")
```

---

## Cell 5 — Verify Data

```python
# Cell 5: Verify all tables have data
print("=== USERS ===")
spark.sql("SELECT role, COUNT(*) as count FROM workspace.time_tracker.users GROUP BY role").show()

print("=== PROJECTS ===")
spark.sql("SELECT project_code, budget_hours, status FROM workspace.time_tracker.projects ORDER BY project_code").show()

print("=== TIME ENTRIES by status ===")
spark.sql("SELECT status, COUNT(*) as count, ROUND(SUM(hours),1) as total_hours FROM workspace.time_tracker.time_entries GROUP BY status").show()

print("=== BUDGET USAGE ===")
spark.sql("""
    SELECT
        p.project_code,
        p.budget_hours,
        ROUND(COALESCE(SUM(te.hours), 0), 1) AS logged_hours,
        ROUND(COALESCE(SUM(te.hours),0) / p.budget_hours * 100, 1) AS pct_used
    FROM workspace.time_tracker.projects p
    LEFT JOIN workspace.time_tracker.time_entries te
        ON p.project_id = te.project_id AND te.status IN ('submitted','approved')
    GROUP BY p.project_code, p.budget_hours
    ORDER BY pct_used DESC
""").show()
```
