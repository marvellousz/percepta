# percepta

A real-time AI chat platform with multi-agent personalities, persistent memory, and WebSocket communication. Chat with different AI assistants that remember your conversations.

## Table of Contents

- [Overview](#overview)
- [Tech Stack](#tech-stack)
- [Features](#features)
- [Installation](#installation)
- [Usage](#usage)
- [Deployment](#deployment)
- [Contributing](#contributing)
- [License](#license)
- [Contact](#contact)

## Overview

Percepta solves the problem of having meaningful, persistent conversations with AI assistants. Unlike traditional chatbots that forget context, Percepta maintains conversation history and offers multiple AI personalities for different use cases.

**Who it's for:** Developers, researchers, students, and anyone who wants to have ongoing conversations with AI assistants that remember context and can adapt to different roles.

## Tech Stack

- **Backend**: FastAPI, Python 3.8+, WebSocket support
- **Frontend**: Next.js 14, React, TypeScript, Tailwind CSS
- **AI Models**: Groq (Llama 3.1), Google Gemini
- **Memory**: Mem0 for persistent conversation storage
- **Real-time**: LiveKit for WebRTC communication
- **Database**: SQLite for user data
- **Deployment**: Docker, Docker Compose

## Features

- **Multi-Agent System**: Choose from 5 different AI personalities (Helpful, Developer, Creative, Research, Educational)
- **Persistent Memory**: AI remembers your conversations across sessions
- **Real-time Chat**: WebSocket-based instant messaging
- **LiveKit Integration**: Professional-grade real-time communication
- **Context Awareness**: AI maintains conversation context and user preferences
- **Multiple Server Options**: Direct Groq API or LangChain integration
- **Docker Support**: Easy deployment and development setup

## Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/marvellousz/percepta.git
   cd percepta
   ```

2. **Set up environment variables**
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` with your API keys:
   ```env
   GROQ_API_KEY=your_groq_api_key
   MEMO_API_KEY=your_mem0_api_key
   LIVEKIT_URL=wss://your-livekit-server.com
   LIVEKIT_API_KEY=your_livekit_key
   LIVEKIT_API_SECRET=your_livekit_secret
   GEMINI_API_KEY=your_gemini_key
   PORT=8000
   FRONTEND_URL=http://localhost:3000
   ```

3. **Backend Setup**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

4. **Frontend Setup**
   ```bash
   cd frontend/app
   npm install
   ```

5. **Run the application**
   
   **Option 1: Direct Groq Server (Recommended)**
   ```bash
   # Terminal 1 - Backend
   cd backend
   python3 simple_server_groq.py
   
   # Terminal 2 - Frontend
   cd frontend/app
   npm run dev
   ```
   
   **Option 2: LangChain Server**
   ```bash
   # Terminal 1 - Backend
   cd backend
   python3 simple_server_langchain_groq.py
   
   # Terminal 2 - Frontend
   cd frontend/app
   npm run dev
   ```
   
   **Option 3: Docker**
   ```bash
   docker-compose up --build
   ```

**Access Points:**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

## Usage

### Starting a Chat Session

1. **Open the application** at http://localhost:3000
2. **Enter your username** and room name
3. **Select an AI agent** from the available personalities:
   - **Helpful Assistant**: General-purpose AI helper
   - **Developer Assistant**: Coding and technical support
   - **Creative Assistant**: Writing and creative tasks
   - **Research Assistant**: Academic and research help
   - **Educational Assistant**: Learning and teaching support
4. **Start chatting** - the AI will remember your conversation

### API Endpoints

- `GET /` - Health check
- `GET /agents` - List available AI agents
- `POST /agent-response` - Get AI response
- `POST /create-room` - Create chat room
- `WebSocket /ws/{username}/{room_name}` - Real-time chat

### Example API Request

```bash
curl -X POST "http://localhost:8000/agent-response" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "user123",
    "message": "Hello, can you help me with Python?",
    "agent": "developer-assistant"
  }'
```

## Deployment

### Docker Deployment (Recommended)

1. **Build and run with Docker Compose**
   ```bash
   docker-compose up --build
   ```

2. **Set production environment variables**
   ```bash
   # Update docker-compose.yml with production values
   # Or use environment file: docker-compose --env-file .env up
   ```

### Manual Deployment

1. **Backend deployment**
   ```bash
   cd backend
   pip install -r requirements.txt
   python3 simple_server_groq.py
   ```

2. **Frontend deployment**
   ```bash
   cd frontend/app
   npm run build
   npm start
   ```

### Environment Variables for Production

Ensure all required environment variables are set:
- `GROQ_API_KEY` (Required for AI responses)
- `MEMO_API_KEY` (Required for memory storage)
- `LIVEKIT_URL` (Required for real-time features)
- `LIVEKIT_API_KEY` (Required for LiveKit)
- `LIVEKIT_API_SECRET` (Required for LiveKit)
- `GEMINI_API_KEY` (Optional, for Gemini integration)

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contact

- **Email**: pranavmurali024@gmail.com
- **GitHub**: [https://github.com/marvellousz/percepta](https://github.com/marvellousz/percepta)

---

Built with ❤️ for AI conversations
