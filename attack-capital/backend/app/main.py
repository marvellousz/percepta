import os
import logging
import pathlib
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, List, Optional
from dotenv import load_dotenv

# Explicitly load .env file from project root
project_root = pathlib.Path(__file__).parent.parent.parent
dotenv_path = project_root / ".env"
load_dotenv(dotenv_path=dotenv_path)
print(f"Loading environment from: {dotenv_path}")
print(f"GEMINI_API_KEY available: {'Yes' if os.getenv('GEMINI_API_KEY') else 'No'}")

from .livekit_integration.agent import LiveKitAgent
from .memory.memory_store import MemoryStore
from .llm.gemini_client import GeminiClient
from .multi_agent.agent_manager import AgentManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Attack Capital AI Chat")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
memory_store = MemoryStore()
llm_client = GeminiClient()
agent_manager = AgentManager(memory_store, llm_client)

# Store active connections
active_connections: Dict[str, WebSocket] = {}
active_agents: Dict[str, LiveKitAgent] = {}

class RoomRequest(BaseModel):
    username: str
    room_name: str
    
class AgentRequest(BaseModel):
    username: str
    message: str
    
class HandoffRequest(BaseModel):
    username: str
    from_agent: str
    to_agent: str
    reason: str

@app.get("/")
async def root():
    return {"message": "Attack Capital AI Chat Backend"}

@app.get("/agents")
async def list_agents():
    """List all available agents"""
    agents = agent_manager.list_agents()
    return {"agents": [agent.dict() for agent in agents]}

@app.post("/agent-response")
async def get_agent_response(request: AgentRequest, agent_name: str = "support-agent"):
    """Get a response from a specific agent"""
    try:
        # Use the agent name from the query param or default to support-agent
        
        # Initialize memory for this user if it doesn't exist
        if not memory_store.user_exists(request.username):
            memory_store.initialize_user(request.username)
        
        # Get context from memory
        context = memory_store.get_context_for_user(request.username)
        
        # Generate response using the agent
        response = await agent_manager.generate_agent_response(
            agent_name=agent_name,
            message=request.message,
            username=request.username,
            context=context
        )
        
        # Store the message and response in memory
        memory_store.add_message(request.username, request.message, is_user=True)
        memory_store.add_message(request.username, response, is_user=False)
        
        return {"response": response, "agent": agent_name}
    except Exception as e:
        logger.error(f"Error generating agent response: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/handoff")
async def handoff_conversation(request: HandoffRequest):
    """Handoff a conversation from one agent to another"""
    try:
        # Generate handoff message
        handoff_message = await agent_manager.handoff_conversation(
            from_agent=request.from_agent,
            to_agent=request.to_agent,
            username=request.username,
            reason=request.reason
        )
        
        return {
            "success": True, 
            "message": handoff_message,
            "from_agent": request.from_agent,
            "to_agent": request.to_agent
        }
    except Exception as e:
        logger.error(f"Error in conversation handoff: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/create-room")
async def create_room(request: RoomRequest):
    try:
        # Create a LiveKit token for the user
        room_name = request.room_name
        username = request.username
        
        # Initialize memory for this user if it doesn't exist
        if not memory_store.user_exists(username):
            memory_store.initialize_user(username)
        
        # Create a LiveKit token
        token = LiveKitAgent.create_token(room_name, username)
        
        return {"token": token}
    except Exception as e:
        logger.error(f"Error creating room: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.websocket("/ws/{username}/{room_name}")
async def websocket_endpoint(websocket: WebSocket, username: str, room_name: str):
    await websocket.accept()
    active_connections[username] = websocket
    
    try:
        # Create and connect the AI agent to the room
        if room_name not in active_agents:
            agent = LiveKitAgent(room_name, "ai-assistant", memory_store, llm_client)
            await agent.connect()
            active_agents[room_name] = agent
            logger.info(f"AI agent joined room: {room_name}")
        
        # Send welcome message
        context = memory_store.get_context_for_user(username)
        welcome_message = await llm_client.generate_response(
            f"Generate a welcome message for {username}. " + 
            (f"Context from previous conversations: {context}" if context else "This is a new user."),
            username
        )
        
        await websocket.send_json({
            "type": "message",
            "sender": "ai-assistant",
            "content": welcome_message
        })
        
        # Main message loop
        while True:
            data = await websocket.receive_json()
            message = data.get("message", "")
            
            # Store the message in memory
            memory_store.add_message(username, message, is_user=True)
            
            # Get context from memory
            context = memory_store.get_context_for_user(username)
            
            # Generate response using LLM
            response = await llm_client.generate_response(message, username, context)
            
            # Store the AI response in memory
            memory_store.add_message(username, response, is_user=False)
            
            # Send response back to user
            await websocket.send_json({
                "type": "message",
                "sender": "ai-assistant",
                "content": response
            })
            
            # Broadcast to LiveKit room
            await active_agents[room_name].send_message(response)
            
    except WebSocketDisconnect:
        logger.info(f"User {username} disconnected from room {room_name}")
        if username in active_connections:
            del active_connections[username]
    except Exception as e:
        logger.error(f"Error in websocket connection: {str(e)}")
        if username in active_connections:
            del active_connections[username]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
