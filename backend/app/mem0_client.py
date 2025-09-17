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
        try:
            if not settings.MEM0_API_KEY:
                logger.error("MEM0_API_KEY is not set in environment variables")
                raise ValueError("MEM0_API_KEY is not set")
                
            self.client = mem0ai.Mem0Client(api_key=settings.MEM0_API_KEY)
            logger.info("mem0 client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize mem0 client: {e}")
            raise
        
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
            
            # Add memory using the correct mem0 API (add_memories)
            # https://docs.mem0.ai/api-reference/memory/add-memories
            memory = {
                "embedding": embedding,
                "text": text,
                "metadata": metadata
            }
            
            await self.client.add_memories([memory])
            
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
            
            # Use search_memories v2 API
            # https://docs.mem0.ai/api-reference/memory/v2-search-memories
            search_params = {
                "query_embedding": query_embedding,
                "filter": {"metadata": {"username": username}},
                "limit": top_k,
                "include_metadata": True
            }
            
            results = await self.client.search_memories_v2(**search_params)
            
            # Format the results
            memories = []
            if hasattr(results, 'memories'):
                for memory in results.memories:
                    mem_dict = {
                        "text": memory.text,
                        "metadata": memory.metadata,
                        "score": memory.score if hasattr(memory, 'score') else 0.0,
                        "id": memory.id if hasattr(memory, 'id') else None
                    }
                    memories.append(mem_dict)
            else:
                # Fallback for different return format
                for memory in results:
                    mem_dict = {
                        "text": memory.text if hasattr(memory, 'text') else "",
                        "metadata": memory.metadata if hasattr(memory, 'metadata') else {},
                        "score": memory.score if hasattr(memory, 'score') else 0.0,
                        "id": memory.id if hasattr(memory, 'id') else None
                    }
                    memories.append(mem_dict)
                
            logger.info(f"Retrieved {len(memories)} memories for user {username}")
            return memories
        except Exception as e:
            logger.error(f"Failed to query memories: {e}", exc_info=True)
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
            # Use the delete_memories API
            # https://docs.mem0.ai/api-reference/memory/delete-memories
            await self.client.delete_memories(filter={"metadata": {"username": username}})
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
