'use client';

import React, { useState, useEffect, useRef } from 'react';
import { Room, RemoteParticipant } from 'livekit-client';
import { ChatMessage, ReceivedMessage, ChatProps } from '../types/chat';
import { connectToRoom, sendChatMessage, listenForChatMessages, disconnectFromRoom, fetchToken } from '../lib/livekit';
import { AGENT_IDENTITY } from '../constants';

const Chat: React.FC<ChatProps> = ({ username, roomName, agentName = AGENT_IDENTITY }) => {
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
        const { url, token } = await fetchToken(username, roomName);
        
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
    
    const isAgent = participant.identity === agentName;
    const sender = isAgent ? agentName : participant.identity;
    
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
    return <div className="flex items-center justify-center h-full p-4">
      <div className="text-center">
        <div className="spinner mb-4"></div>
        <p>Connecting to chat...</p>
      </div>
    </div>;
  }
  
  if (error) {
    return (
      <div className="flex flex-col items-center justify-center h-full p-4 text-red-500">
        <p className="mb-4">Error: {error}</p>
        <button 
          className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
          onClick={() => window.location.reload()}
        >
          Retry Connection
        </button>
      </div>
    );
  }
  
  return (
    <div className="flex flex-col h-full border rounded-lg overflow-hidden">
      <div className="bg-gray-100 p-4 border-b">
        <h2 className="text-lg font-semibold">Room: {roomName}</h2>
        <div>
          {isConnected ? (
            <span className="text-green-500 text-sm">Connected as {username}</span>
          ) : (
            <span className="text-red-500 text-sm">Disconnected</span>
          )}
        </div>
      </div>
      
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 ? (
          <div className="text-center text-gray-500 my-8">No messages yet. Start the conversation!</div>
        ) : (
          messages.map(message => (
            <div 
              key={message.id} 
              className={`max-w-[80%] p-3 rounded-lg ${
                message.isAgent 
                  ? "bg-blue-100 ml-0 mr-auto" 
                  : message.sender === username 
                    ? "bg-green-100 ml-auto mr-0" 
                    : "bg-gray-100 ml-0 mr-auto"
              }`}
            >
              <div className="flex justify-between mb-1 text-xs text-gray-500">
                <span className="font-semibold">{message.sender}</span>
                <span>{formatTimestamp(message.timestamp)}</span>
              </div>
              <div className="text-sm">{message.text}</div>
            </div>
          ))
        )}
        <div ref={messagesEndRef} />
      </div>
      
      <form className="border-t p-4 flex gap-2" onSubmit={handleSendMessage}>
        <input
          type="text"
          value={inputText}
          onChange={e => setInputText(e.target.value)}
          placeholder="Type a message..."
          disabled={!isConnected}
          className="flex-1 border rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
        <button 
          type="submit" 
          disabled={!isConnected || !inputText.trim()} 
          className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:bg-gray-300 disabled:cursor-not-allowed"
        >
          Send
        </button>
      </form>
    </div>
  );
};

export default Chat;
