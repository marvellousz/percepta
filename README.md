# perceptra

A full-stack AI chat platform with FastAPI backend and Next.js frontend, featuring LiveKit integration and multi-agent AI capabilities.

**Repository**: [https://github.com/marvellousz/percepta](https://github.com/marvellousz/percepta)

## Quick Start

### Prerequisites
- Python 3.8+
- Node.js 18+
- Docker (optional)

### Environment Setup
```bash
# Clone repository
git clone https://github.com/marvellousz/percepta.git
cd percepta/attack-capital

# Create environment file
cp .env.example .env
# Edit .env with your API keys
```

### Running the Application

#### Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Choose one method:
python -m app.main
# or
python3 simple_server_groq.py
```

#### Frontend
```bash
cd frontend/app
npm install
npm run dev
```

**Access Points:**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

### Docker (Alternative)
```bash
docker-compose up --build
```

## Project Structure
```
attack-capital/
├── backend/                    # FastAPI backend application
│   ├── app/                   # Main application code
│   │   ├── __init__.py       # Python package marker
│   │   ├── main.py           # FastAPI application entry point
│   │   ├── api/              # REST API routes and endpoints
│   │   ├── livekit_integration/  # LiveKit real-time communication
│   │   ├── llm/              # Language model clients (Gemini, Groq)
│   │   ├── memory/           # Memory management and storage
│   │   └── multi_agent/      # Multi-agent system management
│   ├── data/                 # Data storage directory
│   ├── llm/                  # Additional LLM utilities
│   ├── memory/               # Memory system components
│   ├── requirements.txt      # Python dependencies
│   ├── Dockerfile           # Backend container configuration
│   ├── simple_server_groq.py # Standalone Groq-based server
│   ├── simple_server_langchain_groq.py # LangChain-based server
│   └── users.db             # SQLite database for user data
├── frontend/                 # Next.js frontend application
│   └── app/                 # Next.js app directory
│       ├── src/             # Source code
│       ├── public/          # Static assets
│       ├── package.json     # Node.js dependencies and scripts
│       ├── package-lock.json # Dependency lock file
│       ├── next.config.js   # Next.js configuration
│       ├── tailwind.config.js # Tailwind CSS configuration
│       ├── tsconfig.json    # TypeScript configuration
│       ├── postcss.config.js # PostCSS configuration
│       ├── next-env.d.ts    # Next.js TypeScript declarations
│       ├── Dockerfile       # Frontend container configuration
│       └── node_modules/    # Node.js dependencies (auto-generated)
├── docker-compose.yml       # Multi-container orchestration
├── livekit.yaml            # LiveKit server configuration
├── .env.example            # Environment variables template
├── .gitignore              # Git ignore rules
└── README.md               # This documentation
```

### File Descriptions

#### Backend Files
- **`app/main.py`**: Main FastAPI application with WebSocket support and API endpoints
- **`app/api/`**: REST API routes and request handlers
- **`app/livekit_integration/`**: Real-time communication with LiveKit rooms
- **`app/llm/`**: AI language model clients (Gemini, Groq) for generating responses
- **`app/memory/`**: User memory and conversation storage using Mem0
- **`app/multi_agent/`**: Multi-agent system for different AI personalities
- **`simple_server_groq.py`**: Standalone server implementation using Groq API
- **`simple_server_langchain_groq.py`**: LangChain-based server with Groq integration
- **`requirements.txt`**: Python package dependencies
- **`users.db`**: SQLite database storing user data and conversations
- **`Dockerfile`**: Container configuration for backend deployment

#### Frontend Files
- **`src/`**: React components, pages, and application logic
- **`public/`**: Static assets (images, icons, etc.)
- **`package.json`**: Node.js dependencies, scripts, and project metadata
- **`next.config.js`**: Next.js framework configuration
- **`tailwind.config.js`**: Tailwind CSS styling configuration
- **`tsconfig.json`**: TypeScript compiler configuration
- **`postcss.config.js`**: PostCSS processing configuration
- **`Dockerfile`**: Container configuration for frontend deployment

#### Configuration Files
- **`docker-compose.yml`**: Orchestrates backend and frontend containers
- **`livekit.yaml`**: LiveKit server configuration for real-time communication
- **`.env.example`**: Template for environment variables
- **`.gitignore`**: Specifies files to ignore in version control

## Environment Variables
```env
# Required
LIVEKIT_URL=wss://your-livekit-server.com
LIVEKIT_API_KEY=your_api_key
LIVEKIT_API_SECRET=your_secret
GEMINI_API_KEY=your_gemini_key
GROQ_API_KEY=your_groq_key
MEM0_API_KEY=your_mem0_key
```

## Key Features
- Real-time chat with LiveKit
- Multi-agent AI system
- Memory management with Mem0
- WebSocket support
- Docker containerization

## API Endpoints
- `GET /` - Health check
- `GET /agents` - List AI agents
- `POST /agent-response` - Get AI response
- `POST /create-room` - Create chat room
- `WebSocket /ws/{username}/{room_name}` - Real-time chat

## Contributing
1. Fork the repository
2. Create feature branch: `git checkout -b feature/name`
3. Make changes and test
4. Submit pull request

## License
MIT License
