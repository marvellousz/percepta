#!/usr/bin/env python
# backend/tests/test_prompt_builder.py
import sys
import os
import logging
import time

# Add the parent directory to the path so we can import app modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import prompt_builder

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_prompt_builder():
    """Test the prompt builder functionality"""
    
    # Create some test memories
    memories = [
        {
            "text": "My favorite hobby is photography",
            "metadata": {
                "username": "test_user",
                "role": "user",
                "timestamp": time.time() - 3600  # 1 hour ago
            },
            "score": 0.95
        },
        {
            "text": "I live in San Francisco",
            "metadata": {
                "username": "test_user",
                "role": "user",
                "timestamp": time.time() - 7200  # 2 hours ago
            },
            "score": 0.85
        }
    ]
    
    # Create some test history
    history = [
        {"role": "user", "text": "Hello, how are you?"},
        {"role": "assistant", "text": "I'm doing well, thank you for asking!"}
    ]
    
    # Build a prompt with memories and history
    user_message = "What was my hobby again?"
    prompt = prompt_builder.build_prompt(memories, user_message, history)
    
    # Log the prompt
    logger.info("Generated prompt:")
    logger.info(prompt)
    
    # Build a prompt with just memories
    prompt_no_history = prompt_builder.build_prompt(memories, user_message)
    
    # Log the prompt
    logger.info("Generated prompt without history:")
    logger.info(prompt_no_history)
    
    # Build a prompt with no memories
    prompt_no_memories = prompt_builder.build_prompt([], user_message, history)
    
    # Log the prompt
    logger.info("Generated prompt without memories:")
    logger.info(prompt_no_memories)
    
    logger.info("Test completed successfully")

if __name__ == "__main__":
    test_prompt_builder()
