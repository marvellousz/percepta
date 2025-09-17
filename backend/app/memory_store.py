"""
Custom memory store implementation based on FAISS and SentenceTransformer
Used as a fallback when mem0ai is not available
"""

import os
import logging
import numpy as np
from typing import Dict, List, Optional
from datetime import datetime
import json
import pickle
import uuid

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MemoryStore:
    """In-memory FAISS-based vector store for conversation memory"""
    
    def __init__(self):
        self.memories = {}  # username -> list of memories
        logger.info("Initialized in-memory store")
        
        # Try to import necessary libraries
        self.faiss_available = False
        self.sentence_transformer_available = False
        
        try:
            import faiss
            self.faiss = faiss
            self.faiss_available = True
            logger.info("FAISS library available")
        except ImportError:
            logger.warning("FAISS library not available. Vector search will be disabled.")
        
        try:
            from sentence_transformers import SentenceTransformer
            self.SentenceTransformer = SentenceTransformer
            # Initialize the embedding model
            self.model = SentenceTransformer('all-MiniLM-L6-v2')
            self.vector_dim = self.model.get_sentence_embedding_dimension()
            self.sentence_transformer_available = True
            logger.info(f"SentenceTransformer available with dimension {self.vector_dim}")
        except ImportError:
            logger.warning("SentenceTransformer not available. Using text-based fallback.")

        # Initialize indices if both libraries are available
        self.indices = {}
        if self.faiss_available and self.sentence_transformer_available:
            logger.info("Vector search enabled with FAISS and SentenceTransformer")

    def _create_index_for_user(self, username):
        """Create a new FAISS index for a user"""
        if not self.faiss_available or not self.sentence_transformer_available:
            return None
            
        try:
            index = self.faiss.IndexFlatL2(self.vector_dim)
            self.indices[username] = index
            return index
        except Exception as e:
            logger.error(f"Error creating index for user {username}: {e}")
            return None

    def _get_embedding(self, text):
        """Get embedding for text"""
        if not self.sentence_transformer_available:
            return None
            
        try:
            return self.model.encode(text, convert_to_numpy=True).astype(np.float32)
        except Exception as e:
            logger.error(f"Error getting embedding: {e}")
            return None

    def add_message(self, username: str, message: str, is_user: bool = True):
        """Add a message to memory"""
        # Create user entry if it doesn't exist
        if username not in self.memories:
            self.memories[username] = []
            if self.faiss_available and self.sentence_transformer_available:
                self._create_index_for_user(username)
        
        # Create memory entry
        memory = {
            "id": str(uuid.uuid4()),
            "text": message,
            "is_user": is_user,
            "role": "user" if is_user else "assistant",
            "timestamp": datetime.now().isoformat()
        }
        
        # Get embedding if possible
        embedding = self._get_embedding(message)
        if embedding is not None:
            # Add to index
            if username in self.indices:
                self.indices[username].add(np.array([embedding]))
                # Store the index position
                memory["index_pos"] = self.indices[username].ntotal - 1
        
        # Add to memories
        self.memories[username].append(memory)
        logger.info(f"Added message to memory for user: {username}")
        return memory

    def get_context_for_user(self, username: str, query: str = None, k: int = 5) -> str:
        """Get context string for user"""
        if username not in self.memories:
            return ""
        
        if not self.memories[username]:
            return ""
        
        # If we have vector search capability and a query is provided
        relevant_messages = []
        if query and self.faiss_available and self.sentence_transformer_available and username in self.indices:
            # Get embedding for query
            query_embedding = self._get_embedding(query)
            if query_embedding is not None:
                try:
                    # Search for similar messages
                    distances, indices = self.indices[username].search(
                        np.array([query_embedding]), k
                    )
                    
                    # Get the relevant messages
                    for i in indices[0]:
                        if i < 0 or i >= len(self.memories[username]):
                            continue
                        for msg in self.memories[username]:
                            if msg.get("index_pos") == i:
                                relevant_messages.append(msg)
                                break
                except Exception as e:
                    logger.error(f"Error searching for similar messages: {e}")
        
        # If vector search failed or is not available, use most recent messages
        if not relevant_messages:
            relevant_messages = self.memories[username][-k:]
        
        # Format the context
        context = ""
        for msg in relevant_messages:
            speaker = "User" if msg["is_user"] else "Assistant"
            context += f"{speaker}: {msg['text']}\n"
        
        return context
    
    def get_all_messages(self, username: str) -> List[Dict]:
        """Get all messages for a user"""
        if username not in self.memories:
            return []
        
        return self.memories[username]
    
    def save_to_file(self, file_path: str):
        """Save memory store to a file"""
        try:
            with open(file_path, 'wb') as f:
                pickle.dump(self.memories, f)
            logger.info(f"Memory store saved to {file_path}")
            return True
        except Exception as e:
            logger.error(f"Error saving memory store: {e}")
            return False
    
    def load_from_file(self, file_path: str):
        """Load memory store from a file"""
        if not os.path.exists(file_path):
            logger.warning(f"Memory file {file_path} does not exist")
            return False
            
        try:
            with open(file_path, 'rb') as f:
                self.memories = pickle.load(f)
            
            # Recreate indices if needed
            if self.faiss_available and self.sentence_transformer_available:
                for username in self.memories:
                    self._create_index_for_user(username)
                    
                    # Re-add all messages to the index
                    for i, memory in enumerate(self.memories[username]):
                        if "text" in memory:
                            embedding = self._get_embedding(memory["text"])
                            if embedding is not None:
                                self.indices[username].add(np.array([embedding]))
                                memory["index_pos"] = i
            
            logger.info(f"Memory store loaded from {file_path}")
            return True
        except Exception as e:
            logger.error(f"Error loading memory store: {e}")
            return False

# Global instance
memory_store = MemoryStore()

def get_memory_store() -> MemoryStore:
    """Get the global memory store instance"""
    global memory_store
    return memory_store
