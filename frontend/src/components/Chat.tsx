// frontend/src/components/Chat.tsx
import React, { useState, useEffect, useRef } from 'react';
import { Room, RemoteParticipant } from 'livekit-client';
import { ChatMessage, ReceivedMessage, ChatProps } from '../types/chat';
import { connectToRoom, sendChatMessage, listenForChatMessages, disconnectFromRoom } from '../lib/livekit';
import { AGENT_IDENTITY } from '../constants';

import styles from '../styles/Chat.module.css';

const Chat: React.FC<ChatProps> = ({ username, roomName }) => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputText, setInputText] = useState('');
  const [isConnected, setIsConnected] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const roomRef = useRef<Room | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Connect to the room on component mount
  useEffect(() => {
    const connectToLiveKit = async () => {
      try {
        setIsLoading(true);
        setError(null);
        
        // Fetch token from backend
        const response = await fetch('/api/token', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ username, room: roomName }),
        });
        
        if (!response.ok) {
          throw new Error(`Failed to get token: ${response.statusText}`);
        }
        
        const { url, token } = await response.json();
        
        // Connect to the room
        const room = await connectToRoom(url, token);
        roomRef.current = room;
        setIsConnected(true);
        
        // Listen for chat messages
        const cleanup = listenForChatMessages(room, handleMessageReceived);
        
        return () => {
          cleanup();
          disconnectFromRoom(room).catch(console.error);
          roomRef.current = null;
          setIsConnected(false);
        };
      } catch (err) {
        console.error('Failed to connect:', err);
        setError(err instanceof Error ? err.message : 'Failed to connect');
      } finally {
        setIsLoading(false);
      }
    };
    
    connectToLiveKit();
  }, [username, roomName]);
  
  // Scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);
  
  // Handle received messages
  const handleMessageReceived = (message: ReceivedMessage, participant: RemoteParticipant) => {
    if (message.type !== 'chat') return;
    
    const isAgent = participant.identity === AGENT_IDENTITY;
    const sender = isAgent ? AGENT_IDENTITY : participant.identity;
    
    const chatMessage: ChatMessage = {
      id: `${message.timestamp}-${sender}`,
      text: message.text,
      sender,
      timestamp: message.timestamp,
      isAgent,
    };
    
    setMessages(prev => [...prev, chatMessage]);
  };
  
  // Send a message
  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!inputText.trim() || !roomRef.current || !isConnected) return;
    
    try {
      // Add message to UI immediately
      const newMessage: ChatMessage = {
        id: `${Date.now()}-${username}`,
        text: inputText,
        sender: username,
        timestamp: Date.now(),
        isAgent: false,
      };
      
      setMessages(prev => [...prev, newMessage]);
      
      // Send message to room
      await sendChatMessage(roomRef.current, inputText);
      
      // Clear input
      setInputText('');
    } catch (err) {
      console.error('Failed to send message:', err);
      setError('Failed to send message');
    }
  };
  
  // Format timestamp
  const formatTimestamp = (timestamp: number) => {
    return new Date(timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };
  
  if (isLoading) {
    return <div className={styles.loading}>Connecting to chat...</div>;
  }
  
  if (error) {
    return (
      <div className={styles.error}>
        <p>Error: {error}</p>
        <button 
          className={styles.retryButton}
          onClick={() => window.location.reload()}
        >
          Retry Connection
        </button>
      </div>
    );
  }
  
  return (
    <div className={styles.chatContainer}>
      <div className={styles.header}>
        <h2>Chat Room: {roomName}</h2>
        <div className={styles.status}>
          {isConnected ? (
            <span className={styles.connected}>Connected as {username}</span>
          ) : (
            <span className={styles.disconnected}>Disconnected</span>
          )}
        </div>
      </div>
      
      <div className={styles.messagesContainer}>
        {messages.length === 0 ? (
          <div className={styles.emptyState}>No messages yet. Start the conversation!</div>
        ) : (
          messages.map(message => (
            <div 
              key={message.id} 
              className={`${styles.message} ${
                message.isAgent 
                  ? styles.agentMessage 
                  : message.sender === username 
                    ? styles.ownMessage 
                    : styles.otherMessage
              }`}
            >
              <div className={styles.messageHeader}>
                <span className={styles.sender}>{message.sender}</span>
                <span className={styles.timestamp}>{formatTimestamp(message.timestamp)}</span>
              </div>
              <div className={styles.messageText}>{message.text}</div>
            </div>
          ))
        )}
        <div ref={messagesEndRef} />
      </div>
      
      <form className={styles.inputForm} onSubmit={handleSendMessage}>
        <input
          type="text"
          value={inputText}
          onChange={e => setInputText(e.target.value)}
          placeholder="Type a message..."
          disabled={!isConnected}
          className={styles.input}
        />
        <button 
          type="submit" 
          disabled={!isConnected || !inputText.trim()} 
          className={styles.sendButton}
        >
          Send
        </button>
      </form>
    </div>
  );
};

export default Chat;
