# backend/app/gemini_client.py
import logging
import os
import asyncio
from typing import List, Optional, Dict, Any

from .config import settings

logger = logging.getLogger(__name__)

# Try to import google.generativeai if it's available
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    logger.warning("google.generativeai module not available")
    GEMINI_AVAILABLE = False

# Configure the Gemini API
try:
    if not settings.GEMINI_API_KEY:
        logger.error("GEMINI_API_KEY is not set in environment variables")
        raise ValueError("GEMINI_API_KEY is not set")
    
    if GEMINI_AVAILABLE:
        if settings.GEMINI_API_KEY == "dummy_gemini_api_key":
            logger.warning("Using dummy Gemini API key - will return mock responses")
        else:
            genai.configure(api_key=settings.GEMINI_API_KEY)
            logger.info("Gemini API configured successfully")
    else:
        logger.warning("Skipping Gemini API configuration as the module is not available")
except Exception as e:
    logger.error(f"Failed to configure Gemini API: {e}")

async def embed_text(text: str) -> List[float]:
    """
    Generate embeddings for text using Gemini's embedding model
    
    Args:
        text: The text to embed
        
    Returns:
        List[float]: The embedding vector
    """
    # Check if using dummy key or Gemini is not available
    if not GEMINI_AVAILABLE or settings.GEMINI_API_KEY == "dummy_gemini_api_key":
        logger.warning("Using mock embeddings")
        import hashlib
        import struct
        
        # Generate a deterministic but unique embedding for each text
        hash_obj = hashlib.md5(text.encode())
        hash_bytes = hash_obj.digest()
        
        # Convert to floats - repeat the hash to get to 768 dimensions
        floats = []
        for i in range(96):  # 96 * 8 = 768
            idx = i % 16  # 16 bytes in MD5 hash
            val = struct.unpack('d', hash_bytes[idx:idx+1] * 8)[0]
            floats.append(val)
            
        return floats
        
    try:
        # Use a thread pool to run the synchronous embedding API call
        loop = asyncio.get_event_loop()
        embedding_result = await loop.run_in_executor(
            None, 
            lambda: genai.embed_content(
                model="models/embedding-002",  # Using the latest embedding model
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

async def generate_response(prompt: str) -> str:
    """
    Generate a response from Gemini based on the given prompt
    
    Args:
        prompt: The prompt to send to Gemini
        
    Returns:
        str: The generated response
    """
    # Check if using dummy key or Gemini is not available
    if not GEMINI_AVAILABLE or settings.GEMINI_API_KEY == "dummy_gemini_api_key":
        logger.warning("Using mock response generator")
        await asyncio.sleep(1)  # Simulate API latency
        return "Hello! I'm MemoryBot running in development mode. Since you're using a dummy API key, I'm providing a mock response. I would normally use Google's Gemini API to generate a proper response to your query."
        
    try:
        # Configure the generation model
        generation_config = {
            "temperature": 0.7,
            "top_p": 0.95,
            "top_k": 40,
            "max_output_tokens": 1024,
        }
        
        safety_settings = [
            {
                "category": "HARM_CATEGORY_HARASSMENT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
            {
                "category": "HARM_CATEGORY_HATE_SPEECH",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
            {
                "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
            {
                "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            }
        ]
        
        # Initialize the model - use the latest available model
        try:
            # Try Gemini 2.5 Pro first (newer, better model)
            model = genai.GenerativeModel(
                model_name="gemini-2.5-pro",
                generation_config=generation_config,
                safety_settings=safety_settings
            )
            logger.info("Using Gemini 2.5 Pro model")
        except Exception as e:
            logger.warning(f"Failed to initialize Gemini 2.5 Pro, falling back to 1.5 Pro: {e}")
            # Fall back to Gemini 1.5 Pro
            model = genai.GenerativeModel(
                model_name="gemini-1.5-pro",
                generation_config=generation_config,
                safety_settings=safety_settings
            )
            logger.info("Using Gemini 1.5 Pro model")
        
        # Use a thread pool to run the synchronous API call
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: model.generate_content(prompt)
        )
        
        # Extract the text from the response
        response_text = response.text
        logger.info(f"Generated response: {response_text[:100]}...")
        return response_text
    except Exception as e:
        logger.error(f"Failed to generate response: {e}")
        return f"I apologize, but I encountered an error while processing your request. Please try again later."
