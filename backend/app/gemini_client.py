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

async def generate_response(prompt: str) -> str:
    """
    Generate a response from Gemini based on the given prompt
    
    Args:
        prompt: The prompt to send to Gemini
        
    Returns:
        str: The generated response
    """
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
        
        # Initialize the model
        model = genai.GenerativeModel(
            model_name="gemini-1.5-pro",
            generation_config=generation_config,
            safety_settings=safety_settings
        )
        
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
