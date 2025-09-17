# backend/app/main.py
from fastapi import FastAPI

app = FastAPI(title="MemoryBot Backend")

@app.get("/health")
def health_check():
    return {"status": "healthy"}
