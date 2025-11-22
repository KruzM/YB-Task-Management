from fastapi import FastAPI
from backend.app import auth
from dotenv import load_dotenv
from backend.app.routers import tasks_router
from backend.app.routers import admin_permissions_router
from fastapi.security import APIKeyHeader
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from backend.app.routers.users_router import router as users_router
from backend.app.startup import seed_data
load_dotenv()
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://10.0.0.237:3000"
],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup_event():
    seed_data()

app.include_router(tasks_router.router)
app.include_router(auth.router)
# Attach admin router with a single /admin prefix (router itself has no prefix)
app.include_router(admin_permissions_router.router, prefix="/admin", tags=["Admin Permissions"])
app.include_router(users_router)
api_key_scheme = APIKeyHeader(name="Authorization")  # not strictly required, but available if you use it in future

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title="FastAPI",
        version="1.0.0",
        routes=app.routes,
    )

    # Add API Key header auth
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

@app.get("/")
def root():
    return {"message": "YB Task Management API is running"}
