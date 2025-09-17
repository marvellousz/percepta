# LiveKit Integration for Attack Capital

This integration allows multiple users to join a room and chat with the AI assistant. The agent remembers context according to the username.

## Features

- Multiple users can join chat rooms
- Real-time messaging via LiveKit WebRTC
- Persistent memory per user
- AI responses from Groq/Gemini

## Backend Setup

The backend includes:

1. A token endpoint (`/api/token`) for generating LiveKit tokens
2. LiveKit Agent integration with the memory store
3. WebSocket handling for real-time chat

### Configuration

Add the following to your `.env` file:

```
LIVEKIT_URL=ws://localhost:7880
LIVEKIT_API_KEY=your_livekit_api_key
LIVEKIT_API_SECRET=your_livekit_api_secret
```

## Frontend Setup

The frontend includes:

1. A LiveKit chat component
2. Room pages for joining chats
3. LiveKit client utilities

### Usage

1. Users can navigate to `/rooms/[roomId]` to join a specific room
2. The chat component connects to LiveKit and displays messages
3. The AI agent responds to messages and remembers context per user

## Implementation Details

### Token Generation

The token endpoint generates LiveKit tokens with appropriate permissions for users.

### LiveKit Agent

The LiveKit agent connects to rooms, listens for messages, and responds using the memory store and LLM client.

### Memory Store

The memory store maintains separate memories for each user, allowing the AI to remember context per user.

### Chat Component

The chat component handles the UI for sending and receiving messages, as well as connecting to LiveKit rooms.

## Usage Example

```typescript
import LiveKitChat from '@/components/LiveKitChat';

// In a React component
<LiveKitChat username="john_doe" roomName="demo-room" />
```
