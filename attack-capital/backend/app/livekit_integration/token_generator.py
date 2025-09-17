"""
Token Generator for LiveKit rooms
Provides functions to create tokens for users and agents to join LiveKit rooms
"""

import os
import logging
from typing import Optional
from livekit import rtc

logger = logging.getLogger(__name__)

def create_token(room_name: str, identity: str, is_agent: bool = False) -> str:
    """
    Create a LiveKit token for a participant
    
    Args:
        room_name: The name of the room to join
        identity: The identity of the participant
        is_agent: Whether this token is for an agent or a regular user
        
    Returns:
        str: The JWT token
    """
    api_key = os.environ.get("LIVEKIT_API_KEY")
    api_secret = os.environ.get("LIVEKIT_API_SECRET")
    
    if not api_key or not api_secret:
        raise ValueError("LIVEKIT_API_KEY and LIVEKIT_API_SECRET must be set")
    
    # Create a token with permissions
    token = rtc.AccessToken(api_key, api_secret)
    token.identity = identity
    
    # Add grants with different permissions based on participant type
    if is_agent:
        token.add_grant(
            room_join=True,
            room=room_name,
            can_publish=True,
            can_subscribe=True,
            can_publish_data=True
        )
    else:
        # Regular user can send data but not audio/video
        token.add_grant(
            room_join=True,
            room=room_name,
            can_publish=False,
            can_subscribe=True,
            can_publish_data=True
        )
    
    return token.to_jwt()

def create_user_token(room_name: str, username: str) -> str:
    """Create a token for a regular user"""
    return create_token(room_name, username, is_agent=False)

def create_agent_token(room_name: str, agent_name: str) -> str:
    """Create a token for an agent"""
    return create_token(room_name, agent_name, is_agent=True)
