# YB-Task-Management
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