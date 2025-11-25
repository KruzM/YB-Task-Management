# Quick Start Guide

## Backend (FastAPI)

### Option 1: Using venv Python directly (Recommended)
```bash
# In Git Bash:
venv/bin/python -m uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000

# Or in PowerShell:
.\venv\bin\python.exe -m uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
```

### Option 2: Activate venv first
```bash
# In Git Bash:
source venv/bin/activate
uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000

# In PowerShell (if venv has Scripts folder):
.\venv\Scripts\Activate.ps1
uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
```

## Frontend (Next.js)

### First, make sure Node.js is installed:
```bash
# Check if Node.js is installed:
node --version
npm --version
```

### If Node.js is not installed:
1. Download from: https://nodejs.org/
2. Install it
3. Restart your terminal

### Then run:
```bash
# Make sure you're in the project root directory
npm install  # First time only, to install dependencies
npm run dev
```

## Important Notes:

1. **Run migration first** (if not done):
   ```bash
   venv/bin/python -m alembic upgrade head
   ```

2. **Install python-multipart** (for file uploads):
   ```bash
   venv/bin/python -m pip install python-multipart
   ```

3. **Backend runs on**: http://localhost:8000 (or http://0.0.0.0:8000)
4. **Frontend runs on**: http://localhost:3000

## Troubleshooting:

- If `uvicorn` not found: Use `venv/bin/python -m uvicorn` instead
- If `npm` not found: Install Node.js from nodejs.org
- If port 8000 is busy: Change port with `--port 8001`
- If migration errors: Check that `alembic.ini` is in the project root

