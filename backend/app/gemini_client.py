# backend/app/gemini_client.py
import logging
import google.generativeai as genai
from typing import List, Optional, Dict, Any
import asyncio

from .config import settings

logger = logging.getLogger(__name__)

# Configure the Gemini API
genai.configure(api_key=settings.GEMINI_API_KEY)

async def embed_text(text: str) -> List[float]:
    """
    Generate embeddings for text using Gemini's embedding model
    
    Args:
        text: The text to embed
        
    Returns:
        List[float]: The embedding vector
    """
    try:
        # Use a thread pool to run the synchronous embedding API call
        loop = asyncio.get_event_loop()
        embedding_result = await loop.run_in_executor(
            None, 
            lambda: genai.embed_content(
                model="models/embedding-001",
                content=text,
                task_type="semantic_similarity",
            )
        )
        
        # Extract the embedding values
        embedding = embedding_result["embedding"]
        logger.debug(f"Generated embedding with {len(embedding)} dimensions")
        return embedding
    except Exception as e:
        logger.error(f"Failed to generate embedding: {e}")
        # Return a zero vector as fallback (not ideal but prevents crashes)
        return [0.0] * 768  # Common embedding dimension

# Full Gemini client implementation will be added in task 4
