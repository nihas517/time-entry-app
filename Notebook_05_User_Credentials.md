# Notebook 05 — User Credentials & Login Setup

Create a new notebook called `05_User_Credentials` and run each cell in order.
Run this AFTER notebooks 01–04.

---

## How Role-Based Access Works

The login credential determines what the user sees:

| Who logs in | What they see |
|-------------|--------------|
| **Admin** | All users, all projects, full report, can add/manage users with passwords |
| **Manager** | Only their own employees' timesheets, approval queue, team charts |
| **Employee** | Only their own timesheet — cannot see managers or admin at all |

There is **only one admin**. There can be multiple managers and multiple employees.
Each person has their own unique username and password.

---

## Cell 1 — Create user_credentials Table

```python
# Cell 1: Create login credentials table
spark.sql("""
    CREATE TABLE IF NOT EXISTS workspace.time_tracker.user_credentials (
        user_id       STRING    COMMENT 'FK to users.user_id',
        username      STRING    COMMENT 'Login username (unique)',
        password_hash STRING    COMMENT 'SHA-256 hashed password',
        created_at    TIMESTAMP COMMENT 'When credential was created',
        updated_at    TIMESTAMP COMMENT 'Last updated'
    )
    USING DELTA
    COMMENT 'Login credentials for app users'
""")
print("✅ user_credentials table created")
spark.sql("SHOW TABLES IN workspace.time_tracker").show()
```

---

## Cell 2 — Seed Unique Credentials for All Existing Users

Each user gets a **different password** based on their role and name.

```python
# Cell 2: Seed unique credentials per user
import hashlib
from datetime import datetime
from pyspark.sql.types import StructType, StructField, StringType, TimestampType

def hash_pw(pw):
    return hashlib.sha256(pw.encode()).hexdigest()

now = datetime.now()

# Fetch all existing users with their roles
users = spark.sql("""
    SELECT user_id, name, role FROM workspace.time_tracker.users ORDER BY role, name
""").collect()

# Assign unique username and password per user
# Username = first name lowercase
# Password = role-based prefix + name + number (all different)
creds = []
for u in users:
    first = u['name'].split()[0].lower()
    role  = u['role']
    if role == 'admin':
        password = f"Admin@{first.capitalize()}2024"
    elif role == 'manager':
        password = f"Mgr#{first.capitalize()}01"
    else:
        password = f"Emp#{first.capitalize()}01"

    creds.append((u['user_id'], first, hash_pw(password), now, now))

schema = StructType([
    StructField("user_id",       StringType(),    True),
    StructField("username",      StringType(),    True),
    StructField("password_hash", StringType(),    True),
    StructField("created_at",    TimestampType(), True),
    StructField("updated_at",    TimestampType(), True),
])

creds_df = spark.createDataFrame(creds, schema)
creds_df.write.mode("overwrite").saveAsTable("workspace.time_tracker.user_credentials")
print(f"✅ Created unique credentials for {len(creds)} users")
```

---

## Cell 3 — Print All Login Credentials (Save This!)

```python
# Cell 3: Show all usernames and passwords in plain text (run once, save the output)
import hashlib

def hash_pw(pw):
    return hashlib.sha256(pw.encode()).hexdigest()

users = spark.sql("""
    SELECT user_id, name, role FROM workspace.time_tracker.users ORDER BY role, name
""").collect()

print("=" * 55)
print("  GAME CHANGER APP — LOGIN CREDENTIALS")
print("=" * 55)
print(f"{'Name':<18} {'Role':<10} {'Username':<12} {'Password'}")
print("-" * 55)
for u in users:
    first = u['name'].split()[0].lower()
    role  = u['role']
    if role == 'admin':
        password = f"Admin@{first.capitalize()}2024"
    elif role == 'manager':
        password = f"Mgr#{first.capitalize()}01"
    else:
        password = f"Emp#{first.capitalize()}01"
    print(f"{u['name']:<18} {role:<10} {first:<12} {password}")
print("=" * 55)
print("\n⚠️  Save this output! Passwords are hashed in the DB.")
print("    Admin can reset any password from the app's Admin Panel.")
```

---

## Cell 4 — Verify No Duplicate Usernames

```python
# Cell 4: Make sure all usernames are unique
dupes = spark.sql("""
    SELECT username, COUNT(*) as cnt
    FROM workspace.time_tracker.user_credentials
    GROUP BY username
    HAVING COUNT(*) > 1
""").collect()

if dupes:
    print("⚠️  Duplicate usernames found — fix before going live:")
    for d in dupes:
        print(f"  '{d['username']}' appears {d['cnt']} times")
else:
    count = spark.sql("SELECT COUNT(*) as n FROM workspace.time_tracker.user_credentials").collect()[0]['n']
    print(f"✅ All {count} usernames are unique — ready to go!")

# Show final credential list (no passwords)
spark.sql("""
    SELECT u.role, u.name, uc.username
    FROM workspace.time_tracker.user_credentials uc
    JOIN workspace.time_tracker.users u ON uc.user_id = u.user_id
    ORDER BY u.role, u.name
""").show(truncate=False)
```

---

## Expected Credentials Table

| Name | Role | Username | Password |
|------|------|----------|----------|
| Niha Admin | admin | `niha` | `Admin@Niha2024` |
| Sarah Johnson | manager | `sarah` | `Mgr#Sarah01` |
| Tom Williams | manager | `tom` | `Mgr#Tom01` |
| Alice Smith | employee | `alice` | `Emp#Alice01` |
| Bob Patel | employee | `bob` | `Emp#Bob01` |
| Carol Nguyen | employee | `carol` | `Emp#Carol01` |
| David Chen | employee | `david` | `Emp#David01` |

> **Note:** The admin can reset any password from the Admin Panel inside the app
> at any time — no need to re-run this notebook.

---

## What Each Role Sees After Login

**Admin (`niha`):**
- Manage Users tab — see ALL users (employees, managers, admin) with their usernames
- Add new user and auto-generate their login credentials
- Reset any user's password
- Manage Projects
- Full company-wide time entry report

**Manager (`sarah` or `tom`):**
- See ONLY the employees assigned to them
- Approve or reject their team's timesheets
- View their team's hours and charts
- Cannot see other managers, admin, or unrelated employees

**Employee (`alice`, `bob`, `carol`, `david`):**
- Log their own time entries
- View their own entries and stats
- Cannot see any manager or admin information
- Cannot see other employees
