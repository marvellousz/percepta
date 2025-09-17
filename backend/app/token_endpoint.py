# backend/app/token_endpoint.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from .config import settings
from livekit import api

router = APIRouter()

class TokenRequest(BaseModel):
    username: str
    room: str = settings.DEMO_ROOM  # will be overridden

@router.post("/token")
def create_token(req: TokenRequest):
    if not req.username or not req.username.strip():
        raise HTTPException(status_code=400, detail="username required")
    
    # Always override room to DEMO_ROOM for security
    room = settings.DEMO_ROOM
    
    # Create LiveKit access token
    token = api.AccessToken(settings.LIVEKIT_API_KEY, settings.LIVEKIT_API_SECRET)
    token.with_identity(req.username.strip())
    token.with_name(req.username.strip())
    # Add grants
    token.with_grants(api.VideoGrants(
        room_join=True,
        room=room
    ))
    
    return {
        "url": settings.LIVEKIT_URL,
        "token": token.to_jwt(),
        "room": room
    }
