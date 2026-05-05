# Notebook 03 — AI Anomaly Detection (Unity Catalog)

Create a new notebook called `03_Anomaly_Detection` and run each cell in order.

---

## Cell 1 — Flag Excessive Hours (>10h in one day)

```python
# Cell 1: Flag entries where a single day exceeds 10 hours
spark.sql("""
    UPDATE workspace.time_tracker.time_entries
    SET
        is_flagged  = true,
        flag_reason = 'Excessive hours: more than 10h in a single day',
        updated_at  = current_timestamp()
    WHERE hours > 10
      AND is_flagged = false
""")

count = spark.sql("""
    SELECT COUNT(*) as n FROM workspace.time_tracker.time_entries
    WHERE flag_reason = 'Excessive hours: more than 10h in a single day'
""").collect()[0]['n']
print(f"✅ Flagged {count} excessive-hours entries")
```

---

## Cell 2 — Flag Weekend Submissions

```python
# Cell 2: Flag time entries logged on Saturday (7) or Sunday (1)
spark.sql("""
    UPDATE workspace.time_tracker.time_entries
    SET
        is_flagged  = true,
        flag_reason = COALESCE(flag_reason || ' | ', '') || 'Weekend entry',
        updated_at  = current_timestamp()
    WHERE dayofweek(entry_date) IN (1, 7)
      AND status = 'submitted'
""")

count = spark.sql("""
    SELECT COUNT(*) as n FROM workspace.time_tracker.time_entries
    WHERE flag_reason LIKE '%Weekend%'
""").collect()[0]['n']
print(f"✅ Flagged {count} weekend entries")
```

---

## Cell 3 — Flag High Daily Totals (>12h per day per person)

```python
# Cell 3: Flag employees who logged more than 12 hours on the same day
spark.sql("""
    UPDATE workspace.time_tracker.time_entries te
    SET
        is_flagged  = true,
        flag_reason = COALESCE(te.flag_reason || ' | ', '') || 'High daily total: over 12h',
        updated_at  = current_timestamp()
    WHERE te.entry_id IN (
        SELECT entry_id
        FROM (
            SELECT
                entry_id,
                SUM(hours) OVER (PARTITION BY user_id, entry_date) AS daily_total
            FROM workspace.time_tracker.time_entries
        ) t
        WHERE daily_total > 12
    )
    AND is_flagged = false
""")
print("✅ High daily total check complete")
```

---

## Cell 4 — Find Missing Submissions

```python
# Cell 4: Show employees who haven't submitted anything this week
from datetime import date, timedelta

today = date.today()
week_start = str(today - timedelta(days=today.weekday()))

missing = spark.sql(f"""
    SELECT
        u.name,
        u.department,
        u.email,
        m.name AS manager
    FROM workspace.time_tracker.users u
    LEFT JOIN workspace.time_tracker.users m ON u.manager_id = m.user_id
    LEFT JOIN workspace.time_tracker.time_entries te
        ON u.user_id = te.user_id AND te.week_start = '{week_start}'
    WHERE u.role = 'employee'
      AND u.is_active = true
    GROUP BY u.name, u.department, u.email, m.name
    HAVING COUNT(te.entry_id) = 0
    ORDER BY u.department, u.name
""")

print(f"Employees with NO time submitted for week starting {week_start}:")
missing.show(truncate=False)
```

---

## Cell 5 — Show All Flagged Entries

```python
# Cell 5: Summary of all anomalies detected
spark.sql("""
    SELECT
        u.name       AS employee,
        p.project_code,
        te.entry_date,
        te.hours,
        te.status,
        te.flag_reason
    FROM workspace.time_tracker.time_entries te
    JOIN workspace.time_tracker.users u    ON te.user_id    = u.user_id
    JOIN workspace.time_tracker.projects p ON te.project_id = p.project_id
    WHERE te.is_flagged = true
    ORDER BY te.entry_date DESC
""").show(truncate=False)

total = spark.sql("SELECT COUNT(*) as n FROM workspace.time_tracker.time_entries WHERE is_flagged=true").collect()[0]['n']
print(f"✅ Total flagged entries: {total}")
```
