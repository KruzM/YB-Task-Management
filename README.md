## Local dev (fast path)

1. Frontend env:
   - Create `.env.local` in the project root with:
     NEXT_PUBLIC_API_BASE_URL=http://10.0.0.237:8000

2. Backend env:
   - Create `backend/.env` with SECRET_KEY, FRONTEND_ORIGIN, etc.

3. Start backend:
   cd backend
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000

4. Start frontend:
   cd app
   npm install
   npm run dev

5. Visit: http://10.0.0.237:3000/auth/login# YB-Task-Management
Custom Task Management software for Yecny Bookkeeping

# YB Task Management — Backend (FastAPI + SQLite)

This repository contains the backend for YB Task Management.

## Quick start (local / dev)

1. Copy `.env.example` → `.env` and edit values (SECRET_KEY, ADMIN_PASSWORD).
2. Create a Python virtual env and install:
   ```bash
   python -m venv .venv
   source .venv/bin/activate      # Mac/Linux
   .venv\Scripts\activate         # Windows
   pip install -r requirements.txt
