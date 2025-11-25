# Database Migration Fix

## Problem
The database is missing the `user_sessions` and `documents` tables, causing errors when the application tries to use them.

## Solution

### Step 1: Run Database Migrations

On your Raspberry Pi (or wherever the backend is running), execute:

```bash
cd /home/kruzer04/YB-Task-Management
source venv/bin/activate  # or: . venv/bin/activate
alembic upgrade head
```

This will:
- Apply all pending migrations
- Create the `user_sessions` table
- Create the `documents` table
- Update any other missing schema elements

### Step 2: Verify Migration

Check that the migration was applied:

```bash
alembic current
```

You should see the latest revision ID.

### Step 3: Restart the Backend

After running migrations, restart your FastAPI server:

```bash
# Stop the current server (Ctrl+C)
# Then restart:
uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
```

## What Was Fixed

1. **Migration File**: Fixed the `down_revision` in `add_document_management_and_session_tracking.py` to correctly reference the previous migration
2. **Graceful Degradation**: Updated `backend/app/utils/security.py` to handle missing tables gracefully (won't crash if tables don't exist, but will log warnings)

## If Migrations Still Fail

If you encounter issues, you can check the migration status:

```bash
# See current database state
alembic current

# See migration history
alembic history

# Check what migrations are pending
alembic heads
```

If there are conflicts, you may need to:
1. Check the `alembic_version` table in your database
2. Manually set the version if needed: `alembic stamp <revision_id>`
3. Then run `alembic upgrade head`

## Alternative: Create Tables Manually (Not Recommended)

If migrations continue to fail, you can manually create the tables using SQL, but this is not recommended as it bypasses the migration system.

