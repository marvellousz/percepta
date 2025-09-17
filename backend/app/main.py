# backend/app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .config import settings
from .token_endpoint import router as token_router

app = FastAPI(title="MemoryBot Backend", version="1.0.0")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL, "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(token_router, prefix="/api")

@app.get("/health")
def health_check():
    return {"status": "healthy", "agent_identity": settings.AGENT_IDENTITY}

@app.get("/")
def root():
    return {"message": "MemoryBot Backend API", "version": "1.0.0"}
