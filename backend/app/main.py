# backend/app/main.py
import asyncio
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import contextlib
from .config import settings
from .token_endpoint import router as token_router
from . import livekit_agent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

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

# Global variable to store the agent background task
agent_task = None

@app.get("/health")
def health_check():
    agent_status = "connected" if livekit_agent.agent and livekit_agent.agent.connected else "disconnected"
    return {
        "status": "healthy", 
        "agent_identity": settings.AGENT_IDENTITY,
        "agent_status": agent_status,
        "room": settings.DEMO_ROOM
    }

@app.get("/")
def root():
    return {"message": "MemoryBot Backend API", "version": "1.0.0"}

@app.on_event("startup")
async def startup_event():
    """Start the LiveKit agent when the application starts"""
    global agent_task
    
    # Create a background task to initialize and run the agent
    try:
        logger.info(f"Starting LiveKit agent '{settings.AGENT_IDENTITY}' for room '{settings.DEMO_ROOM}'")
        await livekit_agent.initialize_agent()
        logger.info("LiveKit agent started successfully")
    except Exception as e:
        logger.error(f"Failed to start LiveKit agent: {e}")

@app.on_event("shutdown")
async def shutdown_event():
    """Disconnect the LiveKit agent when the application shuts down"""
    if livekit_agent.agent and livekit_agent.agent.connected:
        with contextlib.suppress(Exception):
            await livekit_agent.agent.room.disconnect()
            logger.info("LiveKit agent disconnected")
