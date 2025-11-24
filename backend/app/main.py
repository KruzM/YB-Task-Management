from fastapi import FastAPI
from backend.app import auth
from dotenv import load_dotenv
from backend.app.routers import tasks_router
from .routers import clients_router, auth_router, audit
from backend.app.routers import admin_permissions_router
from backend.app.routers.recurrence_router import router as recurrence_router
from fastapi.security import APIKeyHeader
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from backend.app.routers.users_router import router as users_router
from backend.app.startup import seed_data
from .database import Base, engine, SessionLocal

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
            from backend.app.services.recurrence.generator import run_recurrence_pass

            created = run_recurrence_pass(db)
            if created:
                print(f"[recurrence] created {len(created)} tasks at {now.isoformat()}")

            db.close()
        except Exception as e:
            print("recurrence background error:", e)

        await asyncio.sleep(300)  # run every 5 minutes


# ---------------------------------------------------------
#   STARTUP EVENT
# ---------------------------------------------------------
@app.on_event("startup")
async def startup_event():
    # Base.metadata.create_all(bind=engine)
    seed_data()
    asyncio.create_task(recurrence_background_task())


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