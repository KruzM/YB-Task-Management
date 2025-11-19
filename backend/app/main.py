from fastapi import FastAPI
from backend.app import auth
from dotenv import load_dotenv
load_dotenv()
app = FastAPI()

app.include_router(auth.router)

@app.get("/")
def root():
    return {"message": "YB Task Management API is running"}