# backend/app/livekit_agent.py
import asyncio
import logging
import json
from typing import Dict, Optional, Any
import time

from livekit import rtc
from livekit import api
from .config import settings
from .utils import async_retry, RateLimiter

logger = logging.getLogger(__name__)

class LiveKitAgent:
    def __init__(self):
        self.room = rtc.Room()
        self.connected = False
        self.rate_limiter = RateLimiter(rate_limit_seconds=1.5)  # Rate limiter for user responses
        
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
        if self.rate_limiter.is_rate_limited(sender_identity):
            logger.info(f"Rate limiting message from {sender_identity}")
            return
            
        # Update last response time
        self.rate_limiter.update_last_operation_time(sender_identity)
        
        # Extract the text from the message
        text = message_data.get("text", "")
        if not text:
            return
            
        logger.info(f"Received message from {sender_identity}: {text}")
        
        try:
            # Step 1: Retrieve memories for this user
            from . import mem0_client
            memories = []
            
            @async_retry(retries=2, delay=0.5, backoff=2.0)
            async def retrieve_memories():
                return await mem0_client.query_memory(
                    username=sender_identity, 
                    query_text=text,
                    top_k=5
                )
                
            try:
                memories = await retrieve_memories()
                logger.info(f"Retrieved {len(memories)} memories for user {sender_identity}")
            except Exception as e:
                logger.error(f"Error retrieving memories after retries: {e}")
                # Continue with empty memories if retrieval fails
            
            # Step 2: Build prompt with memories and user message
            from . import prompt_builder
            prompt = prompt_builder.build_prompt(
                retrieved_memories=memories,
                user_message=text
            )
            
            # Step 3: Generate response with Gemini
            from . import gemini_client
            
            @async_retry(retries=2, delay=1.0, backoff=2.0)
            async def generate_ai_response():
                return await gemini_client.generate_response(prompt)
                
            response = await generate_ai_response()
            
            # Step 4: Send the response back to the user
            await self._send_chat_message(response)
            
            # Step 5: Index the conversation in memory
            @async_retry(retries=2, delay=0.5, backoff=2.0)
            async def index_conversation():
                # Index user message
                await mem0_client.index_memory(
                    username=sender_identity,
                    text=text,
                    role="user"
                )
                
                # Index agent response
                await mem0_client.index_memory(
                    username=sender_identity,
                    text=response,
                    role="agent"
                )
            
            try:
                await index_conversation()
                logger.info(f"Indexed conversation for user {sender_identity}")
            except Exception as e:
                logger.error(f"Error indexing conversation after retries: {e}")
                # Continue even if indexing fails
                
        except Exception as e:
            logger.error(f"Error handling message: {e}")
            # Send a fallback response in case of any error
            await self._send_chat_message(
                "I apologize, but I encountered an error while processing your message. Please try again."
            )
        
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
