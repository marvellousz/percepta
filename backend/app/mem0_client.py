# backend/app/mem0_client.py
import asyncio
import logging
import time
from typing import List, Dict, Any, Optional
import json

import mem0ai
from .config import settings
from .gemini_client import embed_text

logger = logging.getLogger(__name__)

class Mem0Client:
    def __init__(self):
        """Initialize the mem0 client with API key from settings"""
        self.client = mem0ai.Mem0Client(api_key=settings.MEM0_API_KEY)
        
    async def index_memory(self, username: str, text: str, role: str = "user") -> bool:
        """
        Index a memory for a specific user
        
        Args:
            username: The username to associate with this memory
            text: The text content to index
            role: Either "user" or "agent"
            
        Returns:
            bool: True if indexing was successful
        """
        try:
            # Get embedding for the text
            embedding = await embed_text(text)
            
            # Create metadata with username to ensure isolation
            metadata = {
                "username": username,
                "role": role,
                "timestamp": time.time(),
            }
            
            # Index the memory in mem0
            await self.client.index(
                embedding=embedding,
                text=text,
                metadata=metadata
            )
            
            logger.info(f"Indexed memory for user {username}: {text[:50]}...")
            return True
        except Exception as e:
            logger.error(f"Failed to index memory: {e}")
            return False
            
    async def query_memory(self, username: str, query_text: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Query memories for a specific user based on semantic similarity
        
        Args:
            username: The username to filter memories by
            query_text: The query text to find similar memories
            top_k: Maximum number of memories to return
            
        Returns:
            List[Dict]: List of memory objects with text and metadata
        """
        try:
            # Get embedding for the query text
            query_embedding = await embed_text(query_text)
            
            # Query mem0 with username filter to ensure isolation
            results = await self.client.query(
                embedding=query_embedding,
                filter={"username": username},
                top_k=top_k
            )
            
            # Format the results
            memories = []
            for result in results:
                memory = {
                    "text": result.text,
                    "metadata": result.metadata,
                    "score": result.score,
                }
                memories.append(memory)
                
            logger.info(f"Retrieved {len(memories)} memories for user {username}")
            return memories
        except Exception as e:
            logger.error(f"Failed to query memories: {e}")
            return []
            
    async def delete_memories(self, username: str) -> bool:
        """
        Delete all memories for a specific user
        
        Args:
            username: The username whose memories to delete
            
        Returns:
            bool: True if deletion was successful
        """
        try:
            # Delete memories with the username filter
            await self.client.delete(filter={"username": username})
            logger.info(f"Deleted all memories for user {username}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete memories: {e}")
            return False

# Global client instance
client: Optional[Mem0Client] = None

async def get_client() -> Mem0Client:
    """Get or create the mem0 client instance"""
    global client
    if client is None:
        client = Mem0Client()
    return client

async def index_memory(username: str, text: str, role: str = "user") -> bool:
    """Index a memory for a specific user"""
    client = await get_client()
    return await client.index_memory(username, text, role)

async def query_memory(username: str, query_text: str, top_k: int = 5) -> List[Dict[str, Any]]:
    """Query memories for a specific user"""
    client = await get_client()
    return await client.query_memory(username, query_text, top_k)

async def delete_memories(username: str) -> bool:
    """Delete all memories for a specific user"""
    client = await get_client()
    return await client.delete_memories(username)
