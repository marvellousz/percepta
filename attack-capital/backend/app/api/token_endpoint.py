"""
Token endpoint for LiveKit rooms
Provides an API endpoint to generate tokens for LiveKit rooms
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import os
from dotenv import load_dotenv
from ..livekit_integration.token_generator import create_user_token

# Initialize router
router = APIRouter()

class TokenRequest(BaseModel):
    username: str
    room_name: Optional[str] = "default-room"

@router.post("/token")
async def get_token(request: TokenRequest):
    """
    Generate a LiveKit token for a user to join a room
    """
    if not request.username or not request.username.strip():
        raise HTTPException(status_code=400, detail="Username is required")
    
    try:
        # Generate token using our token generator
        token = create_user_token(request.room_name, request.username)
        
        # Return token and LiveKit URL
        return {
            "url": os.environ.get("LIVEKIT_URL", "ws://localhost:7880"),
            "token": token,
            "room": request.room_name
        }
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate token: {str(e)}")
