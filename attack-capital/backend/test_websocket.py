import os
import logging
import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Initialize FastAPI
app = FastAPI(title="Simple WebSocket Test")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Simple WebSocket Test Server"}

@app.websocket("/ws/{username}/{room_name}")
async def websocket_endpoint(websocket: WebSocket, username: str, room_name: str):
    logger.debug(f"WebSocket connection attempt from {username} for room {room_name}")
    try:
        await websocket.accept()
        logger.debug(f"WebSocket connection accepted for {username}")
        
        # Simple welcome message
        welcome_message = f"Hello {username}! Welcome to the test chat. How can I help you today?"
        await websocket.send_json({
            "type": "message",
            "sender": "system",
            "content": welcome_message
        })
        logger.debug(f"Sent welcome message to {username}")
        
        # Main message loop
        while True:
            data = await websocket.receive_json()
            logger.debug(f"Received message from {username}: {data}")
            message = data.get("message", "")
            
            # Echo the message back
            response = f"You said: {message}"
            await websocket.send_json({
                "type": "message",
                "sender": "system",
                "content": response
            })
            logger.debug(f"Sent response to {username}: {response}")
            
    except WebSocketDisconnect:
        logger.info(f"User {username} disconnected from room {room_name}")
    except Exception as e:
        logger.error(f"Error in websocket connection for {username} in room {room_name}: {str(e)}")
        logger.error(f"Error type: {type(e)}")
        import traceback
        logger.error(f"Stack trace: {traceback.format_exc()}")

if __name__ == "__main__":
    uvicorn.run("test_websocket:app", host="0.0.0.0", port=8000, reload=True)
