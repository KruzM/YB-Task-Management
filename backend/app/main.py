from fastapi import FastAPI
from backend.app import auth
from dotenv import load_dotenv
from backend.app.routers import tasks_router
from .routers import clients_router, auth_router, audit
from backend.app.routers import admin_permissions_router
from backend.app.routers.recurrence_router import router as recurrence_router
from backend.app.routers.documents_router import router as documents_router
from fastapi.security import APIKeyHeader
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from backend.app.routers.users_router import router as users_router
from backend.app.startup import seed_data
from .database import Base, engine, SessionLocal
from backend.app import models
from backend.app.services.recurrence.evaluator import evaluate_task_for_recurrence


import asyncio
from datetime import datetime
from sqlalchemy.orm import Session
import os

load_dotenv()

app = FastAPI()

origins = [
    "http://localhost:3000",
    "http://10.0.0.237:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------
#   RECURRENCE BACKGROUND TASK 
# ---------------------------------------------------------
async def recurrence_background_task():
    await asyncio.sleep(5)  # wait for app to fully start
    while True:
        try:
            now = datetime.utcnow()
            db: Session = SessionLocal()

            # Find completed recurring tasks
            tasks = db.query(models.Task).filter(
                models.Task.is_recurring == True,
                models.Task.status == "completed"
            ).all()

            created_ids = []

            # Run evaluator for each
            for task in tasks:
                new_task = evaluate_task_for_recurrence(
                    db=db,
                    task_model=models.Task,
                    subtask_model=models.Subtask,
                    task_instance=task,
                    commit=True,
                    notification_hook=None,
                )
                if new_task:
                    created_ids.append(new_task.id)

            if created_ids:
                print(f"[recurrence] created {len(created_ids)} tasks at {now.isoformat()}")

            db.close()
        except Exception as e:
            print("recurrence background error:", e)

        await asyncio.sleep(300)  # run every 5 minutes


# ---------------------------------------------------------
#   DOCUMENT PURGE BACKGROUND TASK
# ---------------------------------------------------------
async def document_purge_background_task():
    await asyncio.sleep(10)  # wait for app to fully start
    while True:
        try:
            now = datetime.utcnow()
            db: Session = SessionLocal()

            # Execute approved document purges
            from backend.app.crud_utils.documents import execute_purge_approved_documents
            purged_count = execute_purge_approved_documents(db, performed_by=None)  # System action

            if purged_count > 0:
                print(f"[document_purge] purged {purged_count} documents at {now.isoformat()}")

            db.close()
        except Exception as e:
            print("document purge background error:", e)

        await asyncio.sleep(86400)  # run once per day


# ---------------------------------------------------------
#   STARTUP EVENT
# ---------------------------------------------------------
@app.on_event("startup")
async def startup_event():
    # Base.metadata.create_all(bind=engine)
    seed_data()
    asyncio.create_task(recurrence_background_task())
    asyncio.create_task(document_purge_background_task())


# ---------------------------------------------------------
#   ROUTERS
# ---------------------------------------------------------
app.include_router(tasks_router.router)
app.include_router(recurrence_router)
# app.include_router(recurrence_router.router)
app.include_router(auth.router)
app.include_router(clients_router.router)
app.include_router(audit.router)
app.include_router(admin_permissions_router.router, prefix="/admin", tags=["Admin Permissions"])
app.include_router(users_router)
app.include_router(documents_router)


# ---------------------------------------------------------
#   OPENAPI CONFIG
# ---------------------------------------------------------
api_key_scheme = APIKeyHeader(name="Authorization")

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title="FastAPI",
        version="1.0.0",
        routes=app.routes,
    )

    openapi_schema["components"]["securitySchemes"] = {
        "AuthHeader": {
            "type": "apiKey",
            "in": "header",
            "name": "Authorization"
        }
    }

    openapi_schema["security"] = [{"AuthHeader": []}]
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi


# ---------------------------------------------------------
#   ROOT ENDPOINT
# ---------------------------------------------------------
@app.get("/")
def root():
    return {"message": "YB Task Management API is running"}
