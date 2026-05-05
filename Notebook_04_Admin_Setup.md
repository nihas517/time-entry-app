# Notebook 04 — Admin User & Final Verification (Unity Catalog)

Create a new notebook called `04_Admin_Setup` and run each cell in order.
Run this AFTER notebooks 01, 02, and 03.

---

## Cell 1 — Add Admin User

```python
# Cell 1: Insert admin user (run once)
from datetime import datetime
import uuid

def new_id():
    return str(uuid.uuid4())[:8]

now = datetime.now()

admin_data = [
    (new_id(), "Niha Admin", "nihasai92@gmail.com", "admin", None, "All", True, now)
]

schema = ["user_id","name","email","role","manager_id","department","is_active","created_at"]
admin_df = spark.createDataFrame(admin_data, schema)
admin_df.write.mode("append").saveAsTable("workspace.time_tracker.users")
print("✅ Admin user added!")
spark.sql("SELECT user_id, name, role FROM workspace.time_tracker.users WHERE role='admin'").show()
```

---

## Cell 2 — Verify All Roles

```python
# Cell 2: Confirm all roles exist
spark.sql("""
    SELECT role, COUNT(*) as count
    FROM workspace.time_tracker.users
    GROUP BY role
    ORDER BY role
""").show()
```

Expected:
```
+--------+-----+
|    role|count|
+--------+-----+
|   admin|    1|
|employee|    4|
| manager|    2|
+--------+-----+
```

---

## Cell 3 — Budget Verification

```python
# Cell 3: Check budget vs logged hours
spark.sql("""
    SELECT
        p.project_code,
        p.project_name,
        p.budget_hours,
        ROUND(COALESCE(SUM(te.hours), 0), 1)                                    AS logged_hours,
        ROUND(COALESCE(SUM(te.hours),0) / NULLIF(p.budget_hours,0) * 100, 1)   AS pct_used
    FROM workspace.time_tracker.projects p
    LEFT JOIN workspace.time_tracker.time_entries te
        ON p.project_id = te.project_id
       AND te.status IN ('submitted','approved')
    WHERE p.status = 'active'
    GROUP BY p.project_code, p.project_name, p.budget_hours
    ORDER BY pct_used DESC
""").show()
```

---

## Cell 4 — Final Health Check

```python
# Cell 4: Full system check — all tables and counts
print("=" * 50)
print("GAME CHANGER TIME ENTRY APP — DATA SUMMARY")
print("=" * 50)

tables = ["users", "projects", "time_entries", "approvals"]
for t in tables:
    count = spark.sql(f"SELECT COUNT(*) as n FROM workspace.time_tracker.{t}").collect()[0]['n']
    print(f"  workspace.time_tracker.{t}: {count} rows")

print()
print("Time entries by status:")
spark.sql("""
    SELECT status, COUNT(*) as entries, ROUND(SUM(hours),1) as hours
    FROM workspace.time_tracker.time_entries
    GROUP BY status ORDER BY status
""").show()

print("Flagged entries:")
spark.sql("""
    SELECT COUNT(*) as flagged FROM workspace.time_tracker.time_entries WHERE is_flagged = true
""").show()

print("✅ All done! Ready to deploy Streamlit app.")
```
