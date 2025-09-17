#!/usr/bin/env python3
"""
Script to initialize the memory store with example data
Run this script to test the memory store functionality
"""

import asyncio
import os
import sys
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add the parent directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.memory_store import get_memory_store

async def main():
    """Initialize the memory store with example data"""
    logger.info("Initializing memory store with example data")
    
    # Get memory store instance
    memory_store = get_memory_store()
    
    # Add some example data
    test_user = "test_user"
    memory_store.add_message(test_user, "Hi, my name is Test User", is_user=True)
    memory_store.add_message(test_user, "Hello Test User! How can I help you today?", is_user=False)
    memory_store.add_message(test_user, "I'm interested in learning about AI", is_user=True)
    memory_store.add_message(test_user, "That's great! AI is a fascinating field. What specific aspects are you interested in?", is_user=False)
    
    # Save to file
    memory_store.save_to_file("memory_store.pkl")
    
    # Test querying
    context = memory_store.get_context_for_user(test_user, "What's my name?")
    logger.info(f"Context for 'What's my name?': {context}")
    
    logger.info("Memory store initialized successfully")

if __name__ == "__main__":
    asyncio.run(main())
