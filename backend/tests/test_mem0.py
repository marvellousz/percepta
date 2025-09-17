#!/usr/bin/env python
# backend/tests/test_mem0.py
import asyncio
import sys
import os
import logging

# Add the parent directory to the path so we can import app modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import mem0_client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_mem0():
    """Test the mem0 client functionality"""
    username = "test_user"
    
    # Delete any existing memories for this test user
    logger.info("Deleting existing memories for test user")
    await mem0_client.delete_memories(username)
    
    # Index some test memories
    logger.info("Indexing test memories")
    await mem0_client.index_memory(username, "My favorite hobby is photography", "user")
    await mem0_client.index_memory(username, "I live in San Francisco", "user")
    await mem0_client.index_memory(username, "I have a dog named Max", "user")
    
    # Query for similar memories
    logger.info("Querying memories about hobbies")
    hobby_memories = await mem0_client.query_memory(username, "What do I like to do in my free time?", top_k=1)
    
    if hobby_memories:
        logger.info(f"Found memory: {hobby_memories[0]['text']}")
    else:
        logger.error("No memories found")
    
    # Query for memories about pets
    logger.info("Querying memories about pets")
    pet_memories = await mem0_client.query_memory(username, "Do I have any pets?", top_k=1)
    
    if pet_memories:
        logger.info(f"Found memory: {pet_memories[0]['text']}")
    else:
        logger.error("No memories found")
    
    # Test isolation - create a different user
    other_username = "other_user"
    await mem0_client.index_memory(other_username, "I prefer playing video games", "user")
    
    # Query for hobbies again - should still return photography for original user
    logger.info("Querying memories about hobbies for original user")
    hobby_memories = await mem0_client.query_memory(username, "What do I like to do in my free time?", top_k=1)
    
    if hobby_memories:
        logger.info(f"Found memory: {hobby_memories[0]['text']}")
    else:
        logger.error("No memories found")
    
    # Clean up
    logger.info("Cleaning up test data")
    await mem0_client.delete_memories(username)
    await mem0_client.delete_memories(other_username)
    
    logger.info("Test completed successfully")

if __name__ == "__main__":
    asyncio.run(test_mem0())

