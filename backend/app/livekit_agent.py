# backend/app/livekit_agent.py
import asyncio
import logging
import json
from typing import Dict, Optional, Any
import time

from livekit import rtc
from livekit import api
from .config import settings

logger = logging.getLogger(__name__)

class LiveKitAgent:
    def __init__(self):
        self.room = rtc.Room()
        self.connected = False
        self.last_response_ts_by_user: Dict[str, float] = {}  # For rate limiting
        self.rate_limit_seconds = 1.5  # Minimum seconds between responses to the same user
        
    async def connect(self):
        """Connect to the LiveKit room as the agent"""
        if self.connected:
            logger.info("Agent already connected")
            return
            
        # Create token for agent
        token = api.AccessToken(settings.LIVEKIT_API_KEY, settings.LIVEKIT_API_SECRET)
        token.with_identity(settings.AGENT_IDENTITY)
        token.with_name(settings.AGENT_IDENTITY)
        token.with_grants(api.VideoGrants(
            room_join=True,
            room=settings.DEMO_ROOM
        ))
        
        # Set up event handlers before connecting
        self._setup_event_handlers()
        
        # Connect to the room
        try:
            await self.room.connect(settings.LIVEKIT_URL, token.to_jwt())
            self.connected = True
            logger.info(f"Agent '{settings.AGENT_IDENTITY}' connected to room '{settings.DEMO_ROOM}'")
        except Exception as e:
            logger.error(f"Failed to connect agent to room: {e}")
            raise
            
    def _setup_event_handlers(self):
        """Set up event handlers for the room"""
        
        @self.room.on("participant_connected")
        def on_participant_connected(participant: rtc.RemoteParticipant):
            logger.info(f"Participant connected: {participant.identity}")
            
        @self.room.on("participant_disconnected")
        def on_participant_disconnected(participant: rtc.RemoteParticipant):
            logger.info(f"Participant disconnected: {participant.identity}")
            
        @self.room.on("data_received")
        def on_data_received(data: bytes, participant: rtc.RemoteParticipant, kind: rtc.DataPacketKind):
            if participant.identity == settings.AGENT_IDENTITY:
                # Ignore messages from self to prevent loops
                return
                
            try:
                # Decode the message
                message_str = data.decode("utf-8")
                message_data = json.loads(message_str)
                
                # Check if it's a chat message
                if message_data.get("type") == "chat":
                    # Create a task to handle the message asynchronously
                    asyncio.create_task(self._handle_chat_message(message_data, participant.identity))
            except Exception as e:
                logger.error(f"Error handling message: {e}")
                
    async def _handle_chat_message(self, message_data: Dict[str, Any], sender_identity: str):
        """Handle a chat message from a participant"""
        # Check rate limiting for this user
        current_time = time.time()
        last_response_time = self.last_response_ts_by_user.get(sender_identity, 0)
        
        if current_time - last_response_time < self.rate_limit_seconds:
            logger.info(f"Rate limiting message from {sender_identity}")
            return
            
        # Update last response time
        self.last_response_ts_by_user[sender_identity] = current_time
        
        # Extract the text from the message
        text = message_data.get("text", "")
        if not text:
            return
            
        logger.info(f"Received message from {sender_identity}: {text}")
        
        # TODO: In Task 3-5, we'll add:
        # 1. Memory retrieval from mem0_client
        # 2. Prompt building with prompt_builder
        # 3. Response generation with gemini_client
        
        # For now, just send a simple acknowledgment
        response = f"Received your message: {text}"
        await self._send_chat_message(response)
        
    async def _send_chat_message(self, text: str):
        """Send a chat message to the room"""
        if not self.connected:
            logger.error("Cannot send message: Agent not connected")
            return
            
        message = {
            "type": "chat",
            "text": text,
            "timestamp": time.time()
        }
        
        message_bytes = json.dumps(message).encode("utf-8")
        await self.room.local_participant.publish_data(message_bytes, rtc.DataPacketKind.KIND_RELIABLE)
        logger.info(f"Sent message: {text}")

# Global agent instance
agent: Optional[LiveKitAgent] = None

async def initialize_agent():
    """Initialize and connect the LiveKit agent"""
    global agent
    agent = LiveKitAgent()
    await agent.connect()
    return agent
