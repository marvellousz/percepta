import React from "react";
import { twMerge } from "tailwind-merge";

interface ChatMessageProps {
  message: string;
  isUser: boolean;
  sender: string;
}

const ChatMessage: React.FC<ChatMessageProps> = ({ message, isUser, sender }) => {
  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"} mb-4`}>
      <div
        className={twMerge(
          "max-w-[70%] rounded-lg p-3",
          isUser
            ? "bg-blue-500 text-white rounded-tr-none"
            : "bg-gray-200 dark:bg-gray-700 text-gray-800 dark:text-gray-200 rounded-tl-none"
        )}
      >
        <div className="text-xs mb-1 font-medium">
          {isUser ? "You" : sender}
        </div>
        <div className="whitespace-pre-wrap">{message}</div>
      </div>
    </div>
  );
};

export default ChatMessage;
