"use client";

import { useEffect, useState, useRef } from "react";
import { useRouter } from "next/navigation";
import ChatMessage from "@/components/ChatMessage";
import ChatInput from "@/components/ChatInput";
import AgentSelector from "@/components/AgentSelector";

type Message = {
  id: string;
  content: string;
  sender: string;
  timestamp: Date;
  username?: string; // To identify which user sent the message
  isSystem?: boolean; // For system messages like "user joined"
  isUser?: boolean;   // Flag to indicate if this message is from the current user
};

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const [username, setUsername] = useState("");
  const [roomName, setRoomName] = useState("");
  const [websocket, setWebsocket] = useState<WebSocket | null>(null);
  const [currentAgent, setCurrentAgent] = useState(() => {
    // Try to get the saved agent from localStorage, or default to support-agent
    if (typeof window !== 'undefined') {
      return localStorage.getItem("selected_agent") || "support-agent";
    }
    return "support-agent";
  });
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const router = useRouter();

  // Scroll to bottom whenever messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Initialize chat connection
  useEffect(() => {
    const storedUsername = localStorage.getItem("username");
    const storedRoomName = localStorage.getItem("room_name");

    if (!storedUsername || !storedRoomName) {
      router.push("/");
      return;
    }

    setUsername(storedUsername);
    setRoomName(storedRoomName);

    // Connect to WebSocket
    const backendWsUrl = process.env.NEXT_PUBLIC_BACKEND_WS_URL || 'ws://localhost:8000';
    console.log(`Connecting to WebSocket at ${backendWsUrl}/ws/${storedUsername}/${storedRoomName}`);
    const ws = new WebSocket(
      `${backendWsUrl}/ws/${storedUsername}/${storedRoomName}`
    );

    ws.onopen = () => {
      console.log("Connected to WebSocket");
      setIsConnected(true);
      
      // Make sure we're using the current agent
      const savedAgent = localStorage.getItem("selected_agent");
      if (savedAgent) {
        setCurrentAgent(savedAgent);
      }
    };

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      console.log("Received WebSocket message:", data);
      
      if (data.type === "message" || data.type === "system") {
        setMessages((prev) => [
          ...prev,
          {
            id: Date.now().toString(),
            content: data.content,
            sender: data.sender,
            timestamp: new Date(),
            username: data.username,
            isSystem: data.type === "system",
            // Server now sends isUser flag to tell if this is the current user's message
            isUser: !!data.isUser
          },
        ]);
      }
    };

    ws.onclose = () => {
      console.log("Disconnected from WebSocket");
      setIsConnected(false);
    };

    ws.onerror = (error) => {
      console.error("WebSocket error:", error);
    };

    setWebsocket(ws);

    return () => {
      ws.close();
    };
  }, [router]);

  const sendMessage = async (content: string) => {
    if (!content.trim()) return;

    // Don't add message to local state immediately
    // Let the server broadcast it back to everyone including the sender
    
    // If websocket is open, send message through it
    if (websocket && websocket.readyState === WebSocket.OPEN) {
      websocket.send(
        JSON.stringify({
          message: content,
          agent: currentAgent,
        })
      );
    } else {
      // Otherwise use the REST API with the selected agent
      try {
        const response = await fetch(`/api/agent-response?agent=${currentAgent}`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            username,
            message: content,
          }),
        });

        if (!response.ok) {
          throw new Error("Failed to get agent response");
        }

        const data = await response.json();
        
        // Add AI response to messages
        setMessages((prev) => [
          ...prev,
          {
            id: Date.now().toString(),
            content: data.response,
            sender: data.agent || currentAgent,
            timestamp: new Date(),
          },
        ]);
      } catch (error) {
        console.error("Error getting agent response:", error);
        // Add error message
        setMessages((prev) => [
          ...prev,
          {
            id: Date.now().toString(),
            content: "Sorry, I couldn't process your message. Please try again.",
            sender: "system",
            timestamp: new Date(),
          },
        ]);
      }
    }
  };
  
  const handleAgentChange = async (agentName: string) => {
    setCurrentAgent(agentName);
    // Save the selected agent to localStorage
    localStorage.setItem("selected_agent", agentName);
    
    // Notify the user about agent change
    setMessages((prev) => [
      ...prev,
      {
        id: Date.now().toString(),
        content: `Switching to ${agentName.replace("-agent", "")} agent...`,
        sender: "system",
        timestamp: new Date(),
      },
    ]);
    
    try {
      const response = await fetch("/api/handoff", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          username,
          from_agent: "current-agent",
          to_agent: agentName,
          reason: "User requested agent change",
        }),
      });

      if (!response.ok) {
        throw new Error("Failed to handoff conversation");
      }

      const data = await response.json();
      
      // Add handoff message
      setMessages((prev) => [
        ...prev,
        {
          id: Date.now().toString(),
          content: data.message,
          sender: data.to_agent,
          timestamp: new Date(),
        },
      ]);
    } catch (error) {
      console.error("Error in agent handoff:", error);
    }
  };

  const handleLeave = () => {
    if (websocket) {
      websocket.close();
    }
    localStorage.removeItem("livekit_token");
    localStorage.removeItem("username");
    localStorage.removeItem("room_name");
    router.push("/");
  };

  return (
    <div className="flex flex-col h-screen bg-gray-100 dark:bg-gray-900">
      {/* Header */}
      <header className="bg-white dark:bg-gray-800 shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex justify-between items-center">
          <div>
            <h1 className="text-xl font-semibold text-gray-900 dark:text-white">
              Attack Capital Chat
            </h1>
            <p className="text-sm text-gray-500 dark:text-gray-400">
              Room: {roomName} | User: {username}
            </p>
          </div>
          <div className="flex items-center space-x-4">
            <span
              className={`inline-block h-3 w-3 rounded-full ${
                isConnected ? "bg-green-500" : "bg-red-500"
              }`}
            ></span>
            <button
              onClick={handleLeave}
              className="px-3 py-1 bg-red-500 text-white rounded hover:bg-red-600 text-sm"
            >
              Leave
            </button>
          </div>
        </div>
      </header>

      {/* Chat Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-2">
        {messages.map((message) => (
          <ChatMessage
            key={message.id}
            message={message.content}
            isUser={!!message.isUser}
            sender={message.sender}
            username={message.username}
            isSystem={message.isSystem}
          />
        ))}
        <div ref={messagesEndRef} />
      </div>

      {/* Agent Selector and Chat Input */}
      <div className="bg-white dark:bg-gray-800 border-t border-gray-200 dark:border-gray-700 p-4">
        <AgentSelector onAgentChange={handleAgentChange} currentAgent={currentAgent} />
        <ChatInput onSendMessage={sendMessage} disabled={false} />
      </div>
    </div>
  );
}