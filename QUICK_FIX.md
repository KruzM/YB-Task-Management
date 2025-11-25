# Quick Fix for Database Issues

## The Problem
Your database is missing:
1. `clients.status` column (causing 500 errors)
2. `user_sessions` table (causing warnings)
3. `documents` table (causing background task errors)

## The Solution - Run This Command

**On your Raspberry Pi**, run:

```bash
cd /home/kruzer04/YB-Task-Management/YB-Task-Management
source venv/bin/activate
alembic upgrade head
```

This will apply all pending migrations and fix all the database issues.

## After Running Migrations

1. **Restart your backend server** (Ctrl+C, then restart uvicorn)
2. The warnings about `user_sessions` will stop
3. The 500 errors on `/clients` will be fixed
4. All features will work properly

## If Migrations Fail

If you get errors about migration conflicts, you can check the current state:

```bash
alembic current
alembic history
```

If needed, you can manually stamp the database to a specific revision, but this should not be necessary with the fixed migration chain.

