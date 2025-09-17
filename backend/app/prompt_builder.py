# backend/app/prompt_builder.py
import logging
from typing import List, Dict, Any, Optional
import time
from datetime import datetime

logger = logging.getLogger(__name__)

def format_memory(memory: Dict[str, Any]) -> str:
    """
    Format a memory for inclusion in the prompt
    
    Args:
        memory: Memory object with text and metadata
        
    Returns:
        str: Formatted memory string
    """
    text = memory.get("text", "")
    metadata = memory.get("metadata", {})
    
    # Format timestamp if available
    timestamp_str = ""
    if "timestamp" in metadata:
        try:
            timestamp = metadata["timestamp"]
            dt = datetime.fromtimestamp(timestamp)
            timestamp_str = dt.strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            timestamp_str = "unknown time"
    
    # Format role if available
    role = metadata.get("role", "unknown")
    
    return f"[{timestamp_str}] ({role}): {text}"

def build_prompt(retrieved_memories: List[Dict[str, Any]], user_message: str, recent_history: Optional[List[Dict[str, Any]]] = None) -> str:
    """
    Build a prompt for Gemini that includes user memories and the current message
    
    Args:
        retrieved_memories: List of memory objects from mem0
        user_message: The current user message
        recent_history: Optional list of recent conversation messages
        
    Returns:
        str: The formatted prompt
    """
    # System instruction
    system = (
        "You are \"MemoryBot\", an assistant that converses politely and concisely. "
        "When provided with the \"User memory\" section, treat it as reliable past facts about the user — "
        "use it to personalize answers. If memory conflicts with current input, prioritize the user's "
        "explicit current statement and mention the discrepancy briefly."
    )
    
    # Format memories
    memory_block = ""
    if retrieved_memories:
        memory_lines = [format_memory(memory) for memory in retrieved_memories]
        memory_block = "\n".join(memory_lines)
    else:
        memory_block = "None"
    
    # Format recent history if provided
    history_block = ""
    if recent_history and len(recent_history) > 0:
        history_lines = []
        for msg in recent_history:
            role = "User" if msg.get("role") == "user" else "Assistant"
            text = msg.get("text", "")
            history_lines.append(f"{role}: {text}")
        history_block = "\n".join(history_lines) + "\n"
    
    # Build the final prompt
    prompt = f"{system}\n\nUser memory:\n{memory_block}\n\nConversation:\n{history_block}User: {user_message}\nAssistant:"
    
    logger.debug(f"Built prompt with {len(retrieved_memories)} memories")
    return prompt
