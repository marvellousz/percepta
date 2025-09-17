# backend/app/config.py
import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    LIVEKIT_API_KEY: str
    LIVEKIT_API_SECRET: str
    LIVEKIT_URL: str
    GEMINI_API_KEY: str
    MEM0_API_KEY: str
    PORT: int = 8000
    FRONTEND_URL: str = "http://localhost:3000"
    DEMO_ROOM: str = "demo-room"
    AGENT_IDENTITY: str = "MemoryBot"

    class Config:
        env_file = "../.env"

settings = Settings()
