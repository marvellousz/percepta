import os
import logging
import uvicorn
import sqlite3
import numpy as np
import json
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, List, Optional
from groq import Groq
from langchain_groq import ChatGroq
from dotenv import load_dotenv
from mem0 import MemoryClient

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
    
# Initialize Groq client
groq_api_key = os.getenv("GROQ_API_KEY")
if not groq_api_key:
    raise ValueError("GROQ_API_KEY environment variable not set")
print(f"DEBUG: GROQ_API_KEY (first 6 chars): {groq_api_key[:6]}...")  # Debug print
# Check for path environment variable
print(f"DEBUG: Current working directory: {os.getcwd()}")
print(f"DEBUG: .env file exists in current dir: {os.path.exists('.env')}")
print(f"DEBUG: .env file exists in parent dir: {os.path.exists('../.env')}")
groq_client = Groq(api_key=groq_api_key)

# Initialize Mem0 client
mem0_api_key = os.getenv("MEM0_API_KEY", "m0-BIIaaD4yTCeKto4g3R9piQHwUvbWkvYAixCaCj2k")
if not mem0_api_key:
    raise ValueError("MEM0_API_KEY environment variable not set")
mem0_client = MemoryClient(api_key=mem0_api_key)
logger.info("Mem0 client initialized")

# Initialize FastAPI
app = FastAPI(title="Attack Capital AI Chat")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Store active connections by user and by room
active_connections: Dict[str, WebSocket] = {}
# Store room memberships - users in each room
room_members: Dict[str, List[str]] = {}

# Initialize SQLite database for legacy support
def init_db():
    conn = sqlite3.connect("data/memory.db")
    cursor = conn.cursor()
    
    # Create tables if they don't exist
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        username TEXT PRIMARY KEY,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        message TEXT,
        is_user BOOLEAN,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (username) REFERENCES users (username)
    )
    ''')
    
    conn.commit()
    conn.close()

# Initialize database
init_db()

class RoomRequest(BaseModel):
    username: str
    room_name: str

class MessageRequest(BaseModel):
    username: str
    message: str
    agent: str = "support-agent"
    
class HandoffRequest(BaseModel):
    username: str
    from_agent: str
    to_agent: str
    reason: str = ""

# Agent profiles
AGENTS = {
    "support-agent": {
        "name": "Support Agent",
        "role": "Customer Support",
        "description": "Helps users with technical issues and questions",
        "prompt": "You are a Customer Support agent for Attack Capital. Your goal is to help users with technical issues and questions. Be friendly, helpful, and provide clear instructions."
    },
    "sales-agent": {
        "name": "Sales Agent",
        "role": "Sales Representative",
        "description": "Helps users with product information and purchases",
        "prompt": "You are a Sales Representative for Attack Capital. Your goal is to help users understand our products and make informed decisions. Be persuasive but honest, highlighting the benefits of our offerings."
    },
    "advisor-agent": {
        "name": "Financial Advisor",
        "role": "Financial Advisor",
        "description": "Provides financial advice and investment strategies",
        "prompt": "You are a Financial Advisor for Attack Capital. Your goal is to help users with financial planning and investment strategies. Provide thoughtful, personalized advice based on user goals and risk tolerance."
    }
}

# Helper functions using Mem0
def user_exists(username: str) -> bool:
    """Check if a user exists in Mem0"""
    try:
        # According to Mem0 API docs, we need to use proper filters
        # Using v2 search API with user_id filter
        filters = {"user_id": username}
        
        # Search for any memories for this user
        results = mem0_client.search(
            query="user check",  # Non-empty query required
            version="v2",        # Using v2 API as recommended
            filters=filters,
            limit=1
        )
        
        return len(results) > 0
    except Exception as e:
        logger.error(f"Error checking if user exists in Mem0: {str(e)}")
        # Fall back to SQLite
        conn = sqlite3.connect("data/memory.db")
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM users WHERE username = ?", (username,))
        exists = cursor.fetchone() is not None
        conn.close()
        return exists

def initialize_user(username: str):
    """Initialize a user in Mem0"""
    if not user_exists(username):
        try:
            # Add an initial memory for the user to establish their existence
            # Following the format in Mem0 API docs
            welcome_message = [
                {"role": "assistant", "content": f"User {username} initialized in Mem0 memory system."}
            ]
            
            # Add memory with proper user_id
            mem0_client.add(
                messages=welcome_message,
                user_id=username,
                version="v2"  # Using v2 API as recommended
            )
            
            logger.info(f"User {username} initialized in Mem0")
        except Exception as e:
            logger.error(f"Error initializing user in Mem0: {str(e)}")
            # Fall back to SQLite
            conn = sqlite3.connect("data/memory.db")
            cursor = conn.cursor()
            cursor.execute("INSERT INTO users (username) VALUES (?)", (username,))
            conn.commit()
            conn.close()

def add_message(username: str, message: str, is_user: bool):
    """Add a message to Mem0"""
    try:
        # Format the message for Mem0 according to API docs
        role = "user" if is_user else "assistant"
        messages = [{"role": role, "content": message}]
        
        # Add to Mem0 with proper parameters
        mem0_client.add(
            messages=messages,
            user_id=username,
            version="v2"  # Using v2 API as recommended
        )
        
        logger.info(f"Message added to Mem0 for user {username}")
    except Exception as e:
        logger.error(f"Error adding message to Mem0: {str(e)}")
        # Fall back to SQLite
        conn = sqlite3.connect("data/memory.db")
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO messages (username, message, is_user) VALUES (?, ?, ?)",
            (username, message, is_user)
        )
        conn.commit()
        conn.close()

def get_all_messages_for_user(username: str) -> list:
    """Get all messages for a user from Mem0"""
    try:
        # Using v2 API to get all memories for a user
        filters = {"user_id": username}
        
        # Get all memories using get_all method
        # This is more appropriate than search when we want all messages
        results = mem0_client.get_all(
            filters=filters,
            version="v2",
            limit=100
        )
        
        # Check if we have any results
        if results:
            return results
        else:
            return []
    except Exception as e:
        logger.error(f"Error getting messages from Mem0: {str(e)}")
        # Fall back to SQLite
        conn = sqlite3.connect("data/memory.db")
        cursor = conn.cursor()
        cursor.execute(
            "SELECT message, is_user, timestamp FROM messages WHERE username = ? ORDER BY timestamp",
            (username,)
        )
        messages = cursor.fetchall()
        conn.close()
        
        return messages

def get_context_for_user(username: str, limit: int = 10) -> str:
    """Get context for a user from Mem0"""
    try:
        # Using v2 search API to get relevant context
        filters = {"user_id": username}
        
        # Search for relevant memories
        # We use a generic query to get recent memories
        results = mem0_client.search(
            query="recent conversation",
            version="v2",
            filters=filters,
            limit=limit
        )
        
        # Format the context
        context = ""
        if results:
            for item in results:
                # Extract memory content
                if isinstance(item, dict) and "memory" in item:
                    memory_content = item["memory"]
                    
                    # Try to parse the memory to extract role and content
                    try:
                        memory_data = json.loads(memory_content)
                        if isinstance(memory_data, dict):
                            role = memory_data.get("role", "unknown")
                            content = memory_data.get("content", memory_content)
                            speaker = "User" if role == "user" else "Assistant"
                            context += f"{speaker}: {content}\n"
                        else:
                            context += f"{memory_content}\n"
                    except:
                        # If parsing fails, just use the raw memory
                        context += f"{memory_content}\n"
        
        return context
    except Exception as e:
        logger.error(f"Error getting context from Mem0: {str(e)}")
        # Fall back to SQLite
        conn = sqlite3.connect("data/memory.db")
        cursor = conn.cursor()
        cursor.execute(
            "SELECT message, is_user FROM messages WHERE username = ? ORDER BY timestamp DESC LIMIT ?",
            (username, limit)
        )
        messages = cursor.fetchall()
        conn.close()
        
        # Format the context
        context = ""
        for message, is_user in reversed(messages):
            speaker = "User" if is_user else "Assistant"
            context += f"{speaker}: {message}\n"
        
        return context

async def generate_response(message: str, username: str, agent_name: str = "support-agent", context: Optional[str] = None) -> str:
    try:
        # Get agent profile
        agent = AGENTS.get(agent_name, AGENTS["support-agent"])
        
        # Prepare the user message
        user_message = f"User: {message}"
        
        # Get recent conversation history from Mem0 for this user
        # We'll prepare messages directly in the format Groq expects
        messages = [
            {"role": "system", "content": agent['prompt']}
        ]
        
        # Only add context if explicitly needed
        # This is where we'd use the context flag if we wanted to control it
        use_context = True  # You can make this a parameter or dynamic based on needs
        
        if use_context:
            try:
                # Get memories for this user to build conversation history
                filters = {"user_id": username}
                recent_messages = mem0_client.search(
                    query="recent conversation",
                    version="v2",
                    filters=filters,
                    limit=10  # Limit to recent messages
                )
                
                # Format messages for Groq
                if recent_messages:
                    for item in recent_messages:
                        # Extract memory content
                        if isinstance(item, dict) and "memory" in item:
                            memory_content = item["memory"]
                            
                            # Try to parse the memory
                            try:
                                memory_data = json.loads(memory_content)
                                if isinstance(memory_data, dict):
                                    role = memory_data.get("role", "")
                                    content = memory_data.get("content", "")
                                    
                                    # Only add valid roles (user or assistant)
                                    if role in ["user", "assistant"] and content:
                                        messages.append({"role": role, "content": content})
                            except:
                                # Skip invalid memories
                                pass
            except Exception as mem_err:
                logger.warning(f"Error retrieving memory context: {str(mem_err)}")
        
        # Always add the current message at the end
        messages.append({"role": "user", "content": message})
        
        # Generate response using Groq
        # Using llama-3.1-8b-instant model for faster responses
        response = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",  # Using llama-3.1-8b-instant model
            messages=messages,
            max_tokens=1024,
            temperature=0.7,
        )
        
        # Extract the response text
        response_text = response.choices[0].message.content
        
        return response_text
    except Exception as e:
        logger.error(f"Error generating response: {str(e)}")
        # Check if this is a rate limit error
        if "429" in str(e) and "quota" in str(e).lower():
            return "I'm sorry, the AI service is currently experiencing high demand. Please try again in a moment."
        return "I'm sorry, I encountered an error processing your request."

@app.get("/")
async def root():
    return {"message": "Attack Capital AI Chat Backend"}

@app.get("/agents")
async def list_agents():
    """List all available agents"""
    return {"agents": [
        {
            "name": agent_id,
            "role": data["role"],
            "description": data["description"]
        }
        for agent_id, data in AGENTS.items()
    ]}

@app.post("/create-room")
async def create_room(request: RoomRequest):
    try:
        username = request.username
        room_name = request.room_name
        
        # Initialize user if they don't exist
        initialize_user(username)
        
        # In a real LiveKit implementation, we would create a token here
        # For this simplified version, we'll just return a dummy token
        token = f"dummy_token_{username}_{room_name}"
        
        return {"token": token}
    except Exception as e:
        logger.error(f"Error creating room: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/agent-response")
async def get_agent_response(request: MessageRequest):
    try:
        username = request.username
        message = request.message
        agent_name = request.agent
        
        # Initialize user if they don't exist
        initialize_user(username)
        
        # Get context from memory
        context = get_context_for_user(username)
        
        # Generate response
        response = await generate_response(message, username, agent_name, context)
        
        # Store the message and response
        add_message(username, message, True)
        add_message(username, response, False)
        
        return {"response": response, "agent": agent_name}
    except Exception as e:
        logger.error(f"Error generating agent response: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/handoff")
async def handoff_conversation(request: HandoffRequest):
    """Handoff a conversation from one agent to another"""
    try:
        logger.info(f"Handoff request received: {request}")
        username = request.username
        from_agent = request.from_agent
        to_agent = request.to_agent
        
        # Get agent profile
        agent = AGENTS.get(to_agent, AGENTS["support-agent"])
        logger.info(f"Agent found: {agent}")
        
        # Generate simple handoff message
        handoff_message = f"I'm now switching to {agent['role']} mode to better assist you."
        logger.info(f"Handoff message: {handoff_message}")
        
        # Store the handoff message
        add_message(username, handoff_message, False)
        
        return {
            "success": True, 
            "message": handoff_message,
            "from_agent": from_agent,
            "to_agent": to_agent
        }
    except Exception as e:
        logger.error(f"Error in conversation handoff: {str(e)}")
        # Return a 200 response with an error message instead of raising an exception
        return {
            "success": False,
            "message": f"I'm having trouble switching agents right now. Please try again later.",
            "error": str(e)
        }

async def broadcast_to_room(room_name: str, message: dict, exclude_user: Optional[str] = None):
    """Broadcast a message to all users in a room"""
    if room_name in room_members:
        for username in room_members[room_name]:
            # Skip the excluded user (usually the sender)
            if exclude_user and username == exclude_user:
                continue
            
            # Make a copy of the message for this specific recipient
            user_specific_message = message.copy()
            
            # Always include isUser flag, whether it's a user message, AI message, or system message
            if "username" in message:
                # For user messages: set isUser=true only if this user is the sender
                if message.get("sender") == "user":
                    user_specific_message["isUser"] = (username == message["username"])
                # For AI messages: set isUser=false for everyone
                else:
                    user_specific_message["isUser"] = False
            # For system messages with no username
            else:
                user_specific_message["isUser"] = False
                
            # Send to this room member if they're connected
            if username in active_connections:
                try:
                    await active_connections[username].send_json(user_specific_message)
                    logger.debug(f"Message broadcast to {username} in room {room_name}")
                except Exception as e:
                    logger.error(f"Error broadcasting to {username}: {str(e)}")

@app.websocket("/ws/{username}/{room_name}")
async def websocket_endpoint(websocket: WebSocket, username: str, room_name: str):
    logger.debug(f"WebSocket connection attempt from {username} for room {room_name}")
    try:
        await websocket.accept()
        logger.debug(f"WebSocket connection accepted for {username}")
        
        # Store connection
        active_connections[username] = websocket
        
        # Add user to room
        if room_name not in room_members:
            room_members[room_name] = []
        if username not in room_members[room_name]:
            room_members[room_name].append(username)
            
        logger.debug(f"Added {username} to room {room_name}. Room members: {room_members[room_name]}")
        
        # Initialize user if they don't exist
        initialize_user(username)
        logger.debug(f"User {username} initialized")
        
        # Check if this is a returning user
        user_messages = get_all_messages_for_user(username)
        is_returning_user = len(user_messages) > 0
        
        # Use a simple welcome message that doesn't reference previous conversations
        if is_returning_user:
            welcome_message = f"Hello {username}! Welcome back to Attack Capital Chat. How can I assist you today?"
        else:
            welcome_message = f"Hello {username}! Welcome to Attack Capital Chat. I'm your AI assistant. How can I help you today?"
            
        # Also broadcast that a new user has joined the room
        join_message = {
            "type": "system",
            "content": f"{username} has joined the room.",
            "sender": "system"
        }
        await broadcast_to_room(room_name, join_message, exclude_user=None)
        
        # Create welcome message
        welcome_message_obj = {
            "type": "message",
            "sender": "ai-assistant",
            "content": welcome_message,
            "username": username  # Include the username of who this welcome is for
        }
        
        # Broadcast welcome message to all users in the room
        await broadcast_to_room(room_name, welcome_message_obj, exclude_user=None)
        
        # Add welcome message to memory
        add_message(username, welcome_message, False)
        
        # Main message loop
        while True:
            data = await websocket.receive_json()
            message = data.get("message", "")
            agent_name = data.get("agent", "support-agent")
            
            # Broadcast user's message to everyone in the room including the sender
            user_message_obj = {
                "type": "message",
                "sender": "user",
                "content": message,
                "username": username
            }
            # Don't exclude the sender - everyone should see the message
            await broadcast_to_room(room_name, user_message_obj, exclude_user=None)
            
            # Store the message in memory
            add_message(username, message, True)
            
            # Generate response (context handling is now done inside generate_response)
            response = await generate_response(message, username, agent_name)
            
            # Store the AI response in memory
            add_message(username, response, False)
            
            # Prepare message object
            response_message = {
                "type": "message",
                "sender": "ai-assistant",
                "content": response,
                "username": username  # Include sender's username
            }
            
            # Send response to all users in the room (including the sender)
            await broadcast_to_room(room_name, response_message, exclude_user=None)
            
    except WebSocketDisconnect:
        logger.info(f"User {username} disconnected from room {room_name}")
        # Remove from active connections
        if username in active_connections:
            del active_connections[username]
        
        # Remove from room
        if room_name in room_members and username in room_members[room_name]:
            room_members[room_name].remove(username)
            logger.debug(f"Removed {username} from room {room_name}")
            
            # Notify other users in the room that this user left
            leave_message = {
                "type": "system",
                "content": f"{username} has left the room.",
                "sender": "system"
            }
            await broadcast_to_room(room_name, leave_message)
            
    except Exception as e:
        logger.error(f"Error in websocket connection for {username} in room {room_name}: {str(e)}")
        logger.error(f"Error type: {type(e)}")
        import traceback
        logger.error(f"Stack trace: {traceback.format_exc()}")
        
        # Clean up connections
        if username in active_connections:
            del active_connections[username]
        if room_name in room_members and username in room_members[room_name]:
            room_members[room_name].remove(username)

if __name__ == "__main__":
    # Ensure the data directory exists
    os.makedirs("data", exist_ok=True)
    
    # Run the server
    uvicorn.run("simple_server_groq:app", host="0.0.0.0", port=8000, reload=True)
