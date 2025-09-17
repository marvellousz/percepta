import os
import logging
import numpy as np
import faiss
import json
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from sentence_transformers import SentenceTransformer
import sqlite3

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MemoryStore:
    def __init__(self, db_path: str = "memory.db", vector_dim: int = 384):
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self.vector_dim = vector_dim
        self.db_path = db_path
        self.user_indices: Dict[str, faiss.IndexFlatL2] = {}
        self.user_messages: Dict[str, List[Dict]] = {}
        
        # Initialize database
        self._initialize_db()
        
        # Load existing users from database
        self._load_existing_users()
    
    def _initialize_db(self):
        """Initialize the SQLite database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create tables if they don't exist
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            message TEXT,
            is_user BOOLEAN,
            embedding BLOB,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (username) REFERENCES users (username)
        )
        ''')
        
        conn.commit()
        conn.close()
    
    def _load_existing_users(self):
        """Load existing users from the database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get all users
        cursor.execute("SELECT username FROM users")
        users = cursor.fetchall()
        
        for (username,) in users:
            # Initialize index for this user
            self.user_indices[username] = faiss.IndexFlatL2(self.vector_dim)
            self.user_messages[username] = []
            
            # Load messages for this user
            cursor.execute(
                "SELECT message, is_user, embedding, timestamp FROM messages WHERE username = ? ORDER BY timestamp",
                (username,)
            )
            
            for message, is_user, embedding_blob, timestamp in cursor.fetchall():
                # Convert blob to numpy array
                embedding = np.frombuffer(embedding_blob, dtype=np.float32)
                
                # Add to in-memory storage
                self.user_messages[username].append({
                    "message": message,
                    "is_user": bool(is_user),
                    "timestamp": timestamp
                })
                
                # Add to FAISS index
                self.user_indices[username].add(np.array([embedding]))
        
        conn.close()
        logger.info(f"Loaded {len(users)} existing users from database")
    
    def user_exists(self, username: str) -> bool:
        """Check if a user exists in the memory store"""
        return username in self.user_indices
    
    def initialize_user(self, username: str):
        """Initialize memory for a new user"""
        if username in self.user_indices:
            return
        
        # Create FAISS index for this user
        self.user_indices[username] = faiss.IndexFlatL2(self.vector_dim)
        self.user_messages[username] = []
        
        # Add user to database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("INSERT OR IGNORE INTO users (username) VALUES (?)", (username,))
        conn.commit()
        conn.close()
        
        logger.info(f"Initialized memory for user: {username}")
    
    def add_message(self, username: str, message: str, is_user: bool):
        """Add a message to the user's memory"""
        if username not in self.user_indices:
            self.initialize_user(username)
        
        # Generate embedding
        embedding = self.model.encode(message, convert_to_numpy=True).astype(np.float32)
        
        # Add to in-memory storage
        timestamp = datetime.now().isoformat()
        self.user_messages[username].append({
            "message": message,
            "is_user": is_user,
            "timestamp": timestamp
        })
        
        # Add to FAISS index
        self.user_indices[username].add(np.array([embedding]))
        
        # Add to database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO messages (username, message, is_user, embedding) VALUES (?, ?, ?, ?)",
            (username, message, is_user, embedding.tobytes())
        )
        conn.commit()
        conn.close()
        
        logger.info(f"Added message to memory for user: {username}")
    
    def get_context_for_user(self, username: str, query: str = None, k: int = 5) -> str:
        """Get relevant context for a user based on query or recent messages"""
        if username not in self.user_indices:
            return ""
        
        if not self.user_messages[username]:
            return ""
        
        if query:
            # Search for relevant messages using the query
            query_embedding = self.model.encode(query, convert_to_numpy=True).astype(np.float32)
            distances, indices = self.user_indices[username].search(
                np.array([query_embedding]), k
            )
            
            # Get the relevant messages
            relevant_messages = [
                self.user_messages[username][i] for i in indices[0] if i < len(self.user_messages[username])
            ]
        else:
            # Get the most recent messages
            relevant_messages = self.user_messages[username][-k:]
        
        # Format the context
        context = ""
        for msg in relevant_messages:
            speaker = "User" if msg["is_user"] else "Assistant"
            context += f"{speaker}: {msg['message']}\n"
        
        return context
    
    def get_all_messages_for_user(self, username: str) -> List[Dict]:
        """Get all messages for a user"""
        if username not in self.user_messages:
            return []
        
        return self.user_messages[username]
