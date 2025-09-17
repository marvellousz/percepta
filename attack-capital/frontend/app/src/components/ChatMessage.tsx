import React from "react";
import { twMerge } from "tailwind-merge";

interface ChatMessageProps {
  message: string;
  isUser: boolean;
  sender: string;
  username?: string;  // Add username to show who sent the message
  isSystem?: boolean; // For system messages like "user joined"
}

const ChatMessage: React.FC<ChatMessageProps> = ({ message, isUser, sender, username, isSystem = false }) => {
  // For system messages like "user joined" or "user left"
  if (isSystem) {
    return (
      <div className="flex justify-center my-2">
        <div className="bg-gray-100 dark:bg-gray-800 px-4 py-1 rounded-full text-sm text-gray-600 dark:text-gray-300">
          {message}
        </div>
      </div>
    );
  }

  // Determine if message is from another user (not AI, not the current user)
  const messageFromOtherUser = !isUser && username && sender === "user";
  
  // Choose styles based on sender type
  let messageStyle = "";
  let senderName = "";
  
  if (isUser) {
    // User's own messages (right side)
    messageStyle = "bg-blue-500 text-white rounded-tr-lg rounded-tl-lg rounded-bl-lg rounded-br-none";
    senderName = "You";
  } else if (messageFromOtherUser) {
    // Messages from other users (left side)
    messageStyle = "bg-green-500 text-white rounded-tr-lg rounded-tl-none rounded-bl-lg rounded-br-lg";
    senderName = username || "Other User";
  } else {
    // AI messages (left side)
    messageStyle = "bg-gray-200 dark:bg-gray-700 text-gray-800 dark:text-gray-200 rounded-tr-lg rounded-tl-none rounded-bl-lg rounded-br-lg";
    senderName = sender || "AI Assistant";
  }
  
  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"} mb-4`}>
      <div
        className={twMerge(
          "max-w-[70%] rounded-lg p-3",
          messageStyle
        )}
      >
        <div className="text-xs mb-1 font-medium">
          {senderName}
        </div>
        <div className="whitespace-pre-wrap">{message}</div>
      </div>
    </div>
  );
};

export default ChatMessage;
