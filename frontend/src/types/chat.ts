// frontend/src/types/chat.ts

import { RemoteParticipant } from 'livekit-client';

/**
 * Chat message structure
 */
export interface ChatMessage {
  id: string;
  text: string;
  sender: string;
  timestamp: number;
  isAgent: boolean;
}

/**
 * Message received from LiveKit data channel
 */
export interface ReceivedMessage {
  type: string;
  text: string;
  timestamp: number;
}

/**
 * Props for the Chat component
 */
export interface ChatProps {
  username: string;
  roomName: string;
}

