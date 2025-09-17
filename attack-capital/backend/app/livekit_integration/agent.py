import os
import asyncio
import logging
from typing import Optional
from livekit import rtc
from livekit.agents import ChatAgent, ChatAgentConfig
from dotenv import load_dotenv

from ..memory.memory_store import MemoryStore
from ..llm.gemini_client import GeminiClient

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LiveKitAgent:
    def __init__(
        self, 
        room_name: str, 
        agent_name: str, 
        memory_store: MemoryStore,
        llm_client: GeminiClient
    ):
        self.room_name = room_name
        self.agent_name = agent_name
        self.memory_store = memory_store
        self.llm_client = llm_client
        
        # Initialize the LiveKit agent
        config = ChatAgentConfig(
            name=agent_name,
            token=self._get_agent_token(),
            url=os.getenv("LIVEKIT_URL", "ws://localhost:7880")
        )
        self.agent = ChatAgent(config)
        
        # Set up message handler
        self.agent.on_message(self._handle_message)
        
    async def connect(self):
        """Connect the agent to the LiveKit room"""
        await self.agent.connect()
        logger.info(f"Agent {self.agent_name} connected to room {self.room_name}")
    
    async def disconnect(self):
        """Disconnect the agent from the LiveKit room"""
        await self.agent.disconnect()
        logger.info(f"Agent {self.agent_name} disconnected from room {self.room_name}")
    
    async def send_message(self, message: str):
        """Send a message to the LiveKit room"""
        await self.agent.send_message(message)
    
    async def _handle_message(self, sender_id: str, sender_name: str, message: str):
        """Handle incoming messages from the LiveKit room"""
        # Skip messages from self
        if sender_name == self.agent_name:
            return
            
        logger.info(f"Received message from {sender_name}: {message}")
        
        # Store the message in memory
        self.memory_store.add_message(sender_name, message, is_user=True)
        
        # Get context from memory
        context = self.memory_store.get_context_for_user(sender_name)
        
        # Generate response using LLM
        response = await self.llm_client.generate_response(message, sender_name, context)
        
        # Store the AI response in memory
        self.memory_store.add_message(sender_name, response, is_user=False)
        
        # Send response back to the room
        await self.send_message(response)
    
    def _get_agent_token(self) -> str:
        """Get a token for the agent"""
        return self.create_token(self.room_name, self.agent_name)
    
    @staticmethod
    def create_token(room_name: str, identity: str) -> str:
        """Create a LiveKit token for a participant"""
        api_key = os.getenv("LIVEKIT_API_KEY")
        api_secret = os.getenv("LIVEKIT_API_SECRET")
        
        if not api_key or not api_secret:
            raise ValueError("LIVEKIT_API_KEY and LIVEKIT_API_SECRET must be set")
        
        # Create a token with permissions
        token = rtc.AccessToken(api_key, api_secret)
        token.identity = identity
        token.add_grant(
            room_join=True,
            room=room_name,
            can_publish=True,
            can_subscribe=True
        )
        
        return token.to_jwt()
