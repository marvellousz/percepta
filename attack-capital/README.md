# Attack Capital AI Chat

A real-time AI chat application with memory persistence and multi-agent capabilities for the Attack Capital technical assignment.

## Features

- **Real-Time LiveKit Integration**: Chat with AI agents in real-time using LiveKit
- **Contextual Memory with Mem0**: AI remembers previous conversations using Mem0's powerful memory system
- **Memory Persistence Across Sessions**: Conversations are stored in Mem0 and retrieved when users return
- **Multi-Agent Extension**: Switch between different AI agents (Support, Sales, Financial Advisor)
- **Google Gemini Integration**: Advanced AI capabilities using Google's Gemini API
- **Clean Next.js Frontend**: Modern UI with Tailwind CSS
- **Dockerized Application**: Easy setup with Docker Compose

## Architecture

![Architecture](https://i.imgur.com/PLACEHOLDER.png)

The application consists of three main components:

1. **Python Backend**:
   - FastAPI for the REST API
   - LiveKit integration for real-time communication
   - Mem0 for memory management and contextual retrieval
   - SQLite as fallback storage
   - Google Gemini API for LLM responses

2. **Next.js Frontend**:
   - React with TypeScript
   - Tailwind CSS for styling
   - WebSockets for real-time communication

3. **LiveKit Server**:
   - Handles real-time communication between users and AI agents

## Setup Instructions

### Prerequisites

- Docker and Docker Compose
- Google Gemini API key (Get it from [Google AI Studio](https://aistudio.google.com/))
- Mem0 API key

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/attack-capital.git
   cd attack-capital
   ```

2. Create a `.env` file from the example:
   ```bash
   cp env.example .env
   ```

3. Add your API keys to the `.env` file:
   ```
   GEMINI_API_KEY=your_gemini_api_key
   MEM0_API_KEY=your_mem0_api_key
   ```

4. Start the application with Docker Compose:
   ```bash
   docker-compose up -d
   ```

5. Access the application at [http://localhost:3000](http://localhost:3000)

## Usage

1. Enter your username and room name on the home page
2. Start chatting with the AI agent
3. Switch between different agents using the agent selector
4. Close the browser and return later - the AI will remember your previous conversations

## Development

### Backend

The backend is built with FastAPI and uses the following components:

- `simple_server.py`: Main FastAPI application with Mem0 integration
- `app/livekit_integration/agent.py`: LiveKit agent integration
- `app/memory/memory_store.py`: Legacy memory store (replaced by Mem0)
- `app/llm/gemini_client.py`: Gemini API integration
- `app/multi_agent/agent_manager.py`: Multi-agent management

To run the backend locally:

```bash
cd backend
pip install -r requirements.txt
pip install mem0ai  # Install Mem0 package
GEMINI_API_KEY=your_gemini_api_key python simple_server.py
```

### Frontend

The frontend is built with Next.js and uses the following components:

- `src/app/page.tsx`: Home page with login form
- `src/app/chat/page.tsx`: Chat page with messages and agent selector
- `src/components/`: React components for the UI

To run the frontend locally:

```bash
cd frontend/app
npm install
npm run dev
```

## Memory System

The application uses Mem0 for memory management, which provides:

- **Persistent Memory**: Conversations are stored in Mem0's cloud database
- **Contextual Retrieval**: Relevant context is retrieved based on the current conversation
- **User-Specific Memory**: Each user has their own memory space
- **Seamless Integration**: Mem0's API handles all the complexity of memory management

### Mem0 API Integration

- **API Version**: We use Mem0 API v2 for all operations (v1 is deprecated)
- **Memory Storage**: Messages are stored with user_id for proper retrieval
- **Search Capabilities**: Semantic search with filters for relevant context
- **Error Handling**: Fallback to SQLite when Mem0 API is unavailable
- **Documentation**: See `MEM0_INTEGRATION.md` for detailed implementation

The memory system allows the AI to:
- Remember user preferences and previous conversations
- Provide personalized responses based on conversation history
- Maintain context across different sessions

### Mem0 API Key

To get a Mem0 API key:
1. Visit [Mem0 Dashboard](https://dashboard.mem0.ai/)
2. Sign up or sign in to your account
3. Navigate to API Keys section
4. Create a new API key
5. Copy the key to your `.env` file as `MEM0_API_KEY`

## AI System

The application uses Google's Gemini API for AI capabilities, which provides:

- **Free Tier Models**: Using Gemini 2.5 Flash-Lite, a free model suitable for this application
- **Advanced Language Understanding**: Gemini models offer sophisticated natural language understanding
- **Contextual Responses**: Responses are generated based on conversation history and agent profiles
- **Multiple Personalities**: Different agent personas with specialized knowledge and tone

### Gemini API Key

To get a free Gemini API key:
1. Visit [Google AI Studio](https://aistudio.google.com/)
2. Sign in with your Google account
3. Click on "Get API Key" and then "Create API Key"
4. Copy the generated key to your `.env` file

Free tier usage limits:
- 10 requests per minute
- 500 requests per day
- 250,000 tokens per minute

## Future Improvements

- Add authentication and user accounts
- Implement more sophisticated Mem0 memory management
- Add support for voice and video interactions
- Improve the multi-agent handoff mechanism
- Add analytics and conversation insights
- Implement Mem0's advanced memory features like memory summarization
- Explore more advanced Gemini API capabilities

## License

This project is licensed under the MIT License - see the LICENSE file for details.