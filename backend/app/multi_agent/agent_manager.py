import logging
from typing import Dict, List, Optional
from pydantic import BaseModel

from ..memory.memory_store import MemoryStore
from ..llm.gemini_client import GeminiClient

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AgentProfile(BaseModel):
    """Agent profile with specific characteristics"""
    name: str
    role: str
    description: str
    system_prompt: str

class AgentManager:
    """Manages multiple AI agents with different roles"""
    
    def __init__(self, memory_store: MemoryStore, llm_client: GeminiClient):
        self.memory_store = memory_store
        self.llm_client = llm_client
        self.agents: Dict[str, AgentProfile] = {}
        
        # Initialize with default agents
        self._initialize_default_agents()
    
    def _initialize_default_agents(self):
        """Initialize default agent profiles"""
        # General Assistant
        self.register_agent(
            name="general-assistant",
            role="General Assistant",
            description="A helpful, concise assistant providing clear answers",
            system_prompt="""
            You are a helpful, concise assistant. 
            Provide clear answers, step-by-step instructions when useful, and ask one clarifying question if the request is ambiguous. 
            Keep responses under ~300 words unless the user asks for more.
            """
        )
        
        # Technical Assistant
        self.register_agent(
            name="technical-assistant",
            role="Developer Assistant",
            description="Expert developer assistant providing code examples and technical advice",
            system_prompt="""
            You are an expert developer assistant. 
            Prioritize correct code examples, minimal reproducible snippets, and explain trade-offs. 
            When giving commands, mark them in code blocks. 
            Ask for environment details (OS, language version, frameworks) if missing.
            """
        )
        
        # Creative Writer
        self.register_agent(
            name="creative-writer",
            role="Creative Writer",
            description="Creative writing assistant producing vivid, original text",
            system_prompt="""
            You are a creative writing assistant. 
            Produce vivid, original text in the requested tone and length. 
            If the user does not specify tone or POV, ask which they prefer. 
            Avoid clichés and keep language fresh.
            """
        )
        
        # Fact Checker
        self.register_agent(
            name="fact-checker",
            role="Research Assistant",
            description="Careful fact-checker verifying claims with sources",
            system_prompt="""
            You are a careful fact-checker. 
            Verify claims, list the confidence level, and provide 2–3 concise sources or suggestions where to look. 
            If unsure, say so explicitly and propose next steps to verify.
            """
        )
        
        # Tutor
        self.register_agent(
            name="tutor",
            role="Educational Assistant",
            description="Patient tutor explaining concepts with examples",
            system_prompt="""
            You are a patient tutor. 
            Explain concepts step-by-step, use simple analogies, give a single short example, 
            and then offer a small practice problem the user can try. 
            Ask if they'd like a deeper dive.
            """
        )
    
    def register_agent(self, name: str, role: str, description: str, system_prompt: str):
        """Register a new agent profile"""
        self.agents[name] = AgentProfile(
            name=name,
            role=role,
            description=description,
            system_prompt=system_prompt
        )
        logger.info(f"Registered agent: {name} ({role})")
    
    def get_agent(self, name: str) -> Optional[AgentProfile]:
        """Get an agent profile by name"""
        return self.agents.get(name)
    
    def list_agents(self) -> List[AgentProfile]:
        """List all available agents"""
        return list(self.agents.values())
    
    async def generate_agent_response(
        self,
        agent_name: str,
        message: str,
        username: str,
        context: Optional[str] = None
    ) -> str:
        """Generate a response from a specific agent"""
        agent = self.get_agent(agent_name)
        if not agent:
            return f"Agent '{agent_name}' not found."
        
        # Create a prompt with the agent's system prompt
        prompt = f"{agent.system_prompt}\n\n"
        
        if context:
            prompt += f"Previous conversation context:\n{context}\n\n"
        
        prompt += f"User ({username}): {message}\n\n{agent.role}:"
        
        # Generate response using the LLM
        response = await self.llm_client.generate_response(
            message=message,
            username=username,
            context=prompt
        )
        
        return response
    
    async def handoff_conversation(
        self,
        from_agent: str,
        to_agent: str,
        username: str,
        reason: str
    ) -> str:
        """Handoff a conversation from one agent to another"""
        source_agent = self.get_agent(from_agent)
        target_agent = self.get_agent(to_agent)
        
        if not source_agent or not target_agent:
            return "Handoff failed. One or both agents not found."
        
        # Get context from memory
        context = self.memory_store.get_context_for_user(username)
        
        # Generate handoff message
        handoff_message = f"I'm transferring you to our {target_agent.role} who can better assist you with this. {reason}"
        
        # Store the handoff message
        self.memory_store.add_message(username, handoff_message, is_user=False)
        
        # Generate welcome message from the new agent
        welcome_prompt = f"""
        {target_agent.system_prompt}
        
        Previous conversation context:
        {context}
        
        Generate a welcome message as {target_agent.role} who is taking over the conversation.
        Acknowledge that you're taking over from {source_agent.role} and briefly mention why you can help.
        Keep it concise and friendly.
        """
        
        welcome_message = await self.llm_client.generate_response(
            message=welcome_prompt,
            username=username
        )
        
        return welcome_message
