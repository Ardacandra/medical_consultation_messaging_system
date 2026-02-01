from fastapi import FastAPI
from app.db.database import engine, Base

app = FastAPI(title="Nightingale API", version="0.1.0")

@app.get("/")
def read_root():
    return {"message": "Welcome to Nightingale API"}

@app.get("/health")
def health_check():
    return {"status": "ok"}
