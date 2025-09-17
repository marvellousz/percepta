#!/usr/bin/env python3
"""
Script to test the LiveKit agent functionality directly
This script connects the agent to a room and allows you to send test messages
"""

import asyncio
import os
import sys
import logging
import json
import time
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add the parent directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.livekit_agent import LiveKitAgent
from app.config import settings

async def test_livekit_agent():
    """Test the LiveKit agent by connecting to a room and sending messages"""
    logger.info("Starting LiveKit agent test")
    
    # Create and connect agent
    agent = LiveKitAgent()
    await agent.connect()
    logger.info("Agent connected")
    
    # Give the agent time to fully connect
    await asyncio.sleep(2)
    
    # Create a test message
    test_message = {
        "type": "chat",
        "text": "Hello, this is a test message from the test script.",
        "timestamp": time.time(),
        "sender": "test_user"
    }
    
    # Send the test message to the agent
    logger.info("Simulating message received")
    await agent._handle_chat_message(test_message, "test_user")
    
    # Wait for response
    await asyncio.sleep(5)
    
    logger.info("Test completed - check logs for response")
    await asyncio.sleep(1)
    
    # Test memory functionality
    another_test_message = {
        "type": "chat",
        "text": "What was my previous message?",
        "timestamp": time.time(),
        "sender": "test_user"
    }
    
    # Send another test message to test memory
    logger.info("Testing memory functionality")
    await agent._handle_chat_message(another_test_message, "test_user")
    
    # Wait for response
    await asyncio.sleep(5)
    
    logger.info("Memory test completed - check logs for response")
    
    # Wait for a while before disconnecting
    await asyncio.sleep(2)

if __name__ == "__main__":
    try:
        asyncio.run(test_livekit_agent())
    except KeyboardInterrupt:
        logger.info("Test interrupted")
    except Exception as e:
        logger.error(f"Error during test: {e}")
