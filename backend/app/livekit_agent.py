# backend/app/livekit_agent.py
import asyncio
import logging
import json
from typing import Dict, Optional, Any, Union
import time
import os

from livekit import rtc
from livekit import api
from .config import settings
from .utils import async_retry, RateLimiter
from .memory_store import get_memory_store

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
        def on_data_received(data, **kwargs):
            # Extract participant and kind from kwargs with defaults
            participant = kwargs.get('participant')
            kind = kwargs.get('kind')
            
            # Log more information for debugging
            logger.debug(f"Received data packet type: {type(data)}")
            logger.debug(f"Data packet kwargs: {kwargs}")
            
            try:
                # Extract the bytes data from the packet
                bytes_data = None
                
                # Handle different LiveKit SDK versions
                try:
                    # First try directly as DataPacket (newer SDK)
                    bytes_data = data.payload
                except AttributeError:
                    try:
                        # Then try as rtc.DataPacket
                        if isinstance(data, rtc.DataPacket):
                            bytes_data = data.data
                        # Or maybe it has a direct payload attribute
                        elif hasattr(data, 'payload'):
                            bytes_data = data.payload
                        # Or maybe it has a data attribute
                        elif hasattr(data, 'data'):
                            bytes_data = data.data
                        # As a last resort, try to get bytes directly
                        else:
                            bytes_data = bytes(data)
                    except Exception as inner_e:
                        logger.error(f"Error extracting data from packet: {inner_e}")
                        return
                
                if bytes_data is None:
                    logger.error("Could not extract bytes data from packet")
                    return
                
                # Log the bytes for debugging (first 20 bytes only)
                try:
                    logger.debug(f"Data bytes (first 20): {bytes_data[:20]}")
                except Exception:
                    logger.debug("Could not log data bytes")
                
                # Decode the bytes to string
                message_str = bytes_data.decode('utf-8')
                message_data = json.loads(message_str)
                
                # Log decoded message
                logger.debug(f"Decoded message: {message_data}")
                
                # Check if it's a chat message
                if message_data.get("type") == "chat":
                    # Extract sender info - either from participant or from message
                    sender_identity = participant.identity if participant else message_data.get("sender", "unknown")
                    
                    # Ignore messages from self to prevent loops
                    if sender_identity == settings.AGENT_IDENTITY:
                        return
                    
                    # Log the message
                    logger.info(f"Received chat message from {sender_identity}: {message_data.get('text', '')}")
                    
                    # Create a task to handle the message asynchronously
                    text = message_data.get('text', '')
                    if text:
                        # Send immediate acknowledgment
                        asyncio.create_task(self._send_chat_message(
                            f"I received your message. Processing..."
                        ))
                        
                        # Process the message fully
                        asyncio.create_task(self._handle_chat_message(message_data, sender_identity))
            except Exception as e:
                logger.error(f"Error handling data packet: {e}", exc_info=True)
                # Try to send a response about the error
                if participant:
                    asyncio.create_task(self._send_chat_message(
                        "Sorry, I had trouble processing your message. Please try again."
                    ))
                
    async def _handle_chat_message(self, message_data: Dict[str, Any], sender_identity: str):
        """Handle a chat message from a participant"""
        # Log the full message data for debugging
        logger.debug(f"Full message data: {message_data}")
        
        # Check rate limiting for this user
        if self.rate_limiter.is_rate_limited(sender_identity):
            logger.info(f"Rate limiting message from {sender_identity}")
            await self._send_chat_message(f"Please wait a moment before sending another message.")
            return
            
        # Update last response time
        self.rate_limiter.update_last_operation_time(sender_identity)
        
        # Extract the text from the message
        text = message_data.get("text", "")
        if not text:
            logger.warning("Received message with empty text")
            await self._send_chat_message("I received an empty message. Please try again with some text.")
            return
            
        logger.info(f"Processing message from {sender_identity}: {text}")
        
        try:
            # Check if API keys are configured before proceeding
            if not settings.GEMINI_API_KEY:
                logger.error("Missing API key: Please configure GEMINI_API_KEY in .env file")
                await self._send_chat_message("Hello! I'm MemoryBot. I need a Gemini API key to work properly. Please add GEMINI_API_KEY to your .env file.")
                return

            # Step 1: Try to retrieve memories for this user
            memories = []
            context = ""
            
            # Try using mem0_client if available, otherwise use local memory store
            mem0_available = False
            try:
                from . import mem0_client
                mem0_available = True
                logger.info("Using mem0_client for memory management")
            except ImportError as e:
                logger.warning(f"mem0_client not available, using fallback memory store: {e}")
                # Using fallback memory store
            
            # Retrieve memories based on available implementation
            if mem0_available:
                try:
                    @async_retry(retries=2, delay=0.5, backoff=2.0)
                    async def retrieve_memories():
                        return await mem0_client.query_memory(
                            username=sender_identity, 
                            query_text=text,
                            top_k=5
                        )
                    
                    memories = await retrieve_memories()
                    logger.info(f"Retrieved {len(memories)} memories from mem0 for user {sender_identity}")
                except Exception as e:
                    logger.error(f"Error retrieving memories from mem0 after retries: {e}")
                    mem0_available = False
                    # Fall back to local memory store
            
            # If mem0 failed or is not available, use local memory store
            if not mem0_available:
                memory_store = get_memory_store()
                context = memory_store.get_context_for_user(sender_identity, text)
                logger.info(f"Retrieved context from local memory store for user {sender_identity}")
            
            # Step 2: Build prompt with memories/context and user message
            try:
                from . import prompt_builder
                
                if mem0_available:
                    # Use mem0 memories with prompt builder
                    prompt = prompt_builder.build_prompt(
                        retrieved_memories=memories,
                        user_message=text
                    )
                else:
                    # Use context directly
                    prompt = prompt_builder.build_prompt(
                        retrieved_memories=[],  # Empty list since context is used directly
                        user_message=text,
                        recent_history=[{"role": "system", "text": context}] if context else None
                    )
                
                # Step 3: Generate response with Gemini
                try:
                    from . import gemini_client
                    
                    @async_retry(retries=2, delay=1.0, backoff=2.0)
                    async def generate_ai_response():
                        return await gemini_client.generate_response(prompt)
                    
                    response = await generate_ai_response()
                except ImportError:
                    logger.error("Could not import gemini_client module")
                    response = "Hello! I'm MemoryBot. I'm missing the Gemini AI module. Please make sure the gemini module is installed and your API key is set."
                except Exception as e:
                    logger.error(f"Failed to generate AI response: {e}")
                    response = "Hello! I'm MemoryBot. I'm having some configuration issues at the moment. Please make sure your API key for Gemini is properly set in your .env file."
            except ImportError:
                logger.error("Could not import prompt_builder module")
                response = "Hello! I'm MemoryBot. I need to respond to your message but I'm having trouble with my prompt builder module."
            except Exception as e:
                logger.error(f"Failed to build prompt: {e}")
                response = "Hello! I'm MemoryBot. I received your message but I'm having trouble processing it right now."
            
            # Step 4: Send the response back to the user
            await self._send_chat_message(response)
            
            # Step 5: Store the conversation in memory
            if mem0_available:
                try:
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
                    
                    await index_conversation()
                    logger.info(f"Indexed conversation in mem0 for user {sender_identity}")
                except Exception as e:
                    logger.error(f"Error indexing conversation in mem0 after retries: {e}")
                    # Fall back to local memory store
                    memory_store = get_memory_store()
                    memory_store.add_message(sender_identity, text, is_user=True)
                    memory_store.add_message(sender_identity, response, is_user=False)
                    logger.info(f"Stored conversation in local memory store as fallback for user {sender_identity}")
            else:
                # Use local memory store
                memory_store = get_memory_store()
                memory_store.add_message(sender_identity, text, is_user=True)
                memory_store.add_message(sender_identity, response, is_user=False)
                logger.info(f"Stored conversation in local memory store for user {sender_identity}")
                
                # Try to save to file periodically (every 10th message)
                if len(memory_store.get_all_messages(sender_identity)) % 10 == 0:
                    memory_store.save_to_file(os.path.join(os.path.dirname(__file__), "memory_store.pkl"))
                
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
        try:
            # Try with just the data parameter (newer API version)
            await self.room.local_participant.publish_data(message_bytes)
            logger.info(f"Sent message: {text}")
        except TypeError:
            try:
                # Fallback to older API version syntax
                await self.room.local_participant.publish_data(
                    message_bytes, 
                    reliability=rtc.DataPacketKind.KIND_RELIABLE
                )
                logger.info(f"Sent message: {text}")
            except Exception as e:
                logger.error(f"Failed to send message: {e}", exc_info=True)

# Global agent instance
agent: Optional[LiveKitAgent] = None

async def initialize_agent():
    """Initialize and connect the LiveKit agent"""
    global agent
    agent = LiveKitAgent()
    await agent.connect()
    return agent
