# Notebook 01 — Setup Schema & Tables (Unity Catalog)

Create a new notebook in Databricks called `01_Setup_Schema` and paste each cell below.

---

## Cell 1 — Create Schema

```python
# Cell 1: Create schema (Unity Catalog compatible — no LOCATION needed)
spark.sql("USE CATALOG workspace")
spark.sql("""
    CREATE SCHEMA IF NOT EXISTS time_tracker
    COMMENT 'Game Changer Time Entry App'
""")
spark.sql("USE SCHEMA time_tracker")
print("✅ Schema ready: workspace.time_tracker")
spark.sql("SHOW SCHEMAS IN workspace").show()
```

---

## Cell 2 — Create Users Table

```python
# Cell 2: Users table
spark.sql("""
    CREATE TABLE IF NOT EXISTS workspace.time_tracker.users (
        user_id     STRING      COMMENT 'Unique user ID',
        name        STRING      COMMENT 'Full name',
        email       STRING      COMMENT 'Email address',
        role        STRING      COMMENT 'employee | manager | admin',
        manager_id  STRING      COMMENT 'FK to users.user_id',
        department  STRING      COMMENT 'Department name',
        is_active   BOOLEAN     COMMENT 'Active flag',
        created_at  TIMESTAMP   COMMENT 'Row creation time'
    )
    USING DELTA
    COMMENT 'App users'
""")
print("✅ users table created")
```

---

## Cell 3 — Create Projects Table

```python
# Cell 3: Projects table
spark.sql("""
    CREATE TABLE IF NOT EXISTS workspace.time_tracker.projects (
        project_id    STRING    COMMENT 'Unique project ID',
        project_name  STRING    COMMENT 'Full project name',
        project_code  STRING    COMMENT 'Short code e.g. PROJ-001',
        description   STRING    COMMENT 'Project description',
        budget_hours  DOUBLE    COMMENT 'Total approved hours budget',
        status        STRING    COMMENT 'active | completed | on_hold',
        created_at    TIMESTAMP COMMENT 'Row creation time',
        updated_at    TIMESTAMP COMMENT 'Last update time'
    )
    USING DELTA
    COMMENT 'Projects being tracked'
""")
print("✅ projects table created")
```

---

## Cell 4 — Create Time Entries Table

```python
# Cell 4: Time entries table
spark.sql("""
    CREATE TABLE IF NOT EXISTS workspace.time_tracker.time_entries (
        entry_id      STRING    COMMENT 'Unique entry ID',
        user_id       STRING    COMMENT 'FK to users.user_id',
        project_id    STRING    COMMENT 'FK to projects.project_id',
        entry_date    DATE      COMMENT 'Date work was done',
        hours         DOUBLE    COMMENT 'Hours logged',
        description   STRING    COMMENT 'Work description',
        status        STRING    COMMENT 'draft | submitted | approved | rejected',
        week_start    DATE      COMMENT 'Monday of the work week',
        is_flagged    BOOLEAN   COMMENT 'AI anomaly flag',
        flag_reason   STRING    COMMENT 'Why it was flagged',
        submitted_at  TIMESTAMP COMMENT 'When submitted',
        created_at    TIMESTAMP COMMENT 'Row creation time',
        updated_at    TIMESTAMP COMMENT 'Last update time'
    )
    USING DELTA
    COMMENT 'Employee time entries'
""")
print("✅ time_entries table created")
```

---

## Cell 5 — Create Approvals Table

```python
# Cell 5: Approvals audit table
spark.sql("""
    CREATE TABLE IF NOT EXISTS workspace.time_tracker.approvals (
        approval_id  STRING    COMMENT 'Unique approval ID',
        entry_id     STRING    COMMENT 'FK to time_entries.entry_id',
        manager_id   STRING    COMMENT 'FK to users.user_id (manager)',
        action       STRING    COMMENT 'approved | rejected',
        comments     STRING    COMMENT 'Manager comment',
        actioned_at  TIMESTAMP COMMENT 'When action was taken'
    )
    USING DELTA
    COMMENT 'Approval audit trail'
""")
print("✅ approvals table created")
```

---

## Cell 6 — Verify All Tables

```python
# Cell 6: Check all 4 tables exist
spark.sql("SHOW TABLES IN workspace.time_tracker").show()
```

**Expected output:**
```
+-----------+------------+-----------+
|  database |   tableName|isTemporary|
+-----------+------------+-----------+
|time_tracker|   approvals|      false|
|time_tracker|   projects |      false|
|time_tracker|time_entries|      false|
|time_tracker|      users |      false|
+-----------+------------+-----------+
```
