import React from "react";

interface LoadingAnimationProps {
  type: "agent-switching" | "generating";
  message?: string;
}

const LoadingAnimation: React.FC<LoadingAnimationProps> = ({ 
  type, 
  message = type === "agent-switching" ? "Switching agent..." : "Thinking..." 
}) => {
  if (type === "agent-switching") {
    return (
      <div className="flex justify-center my-2">
        <div className="bg-blue-100 dark:bg-blue-900 px-4 py-2 rounded-lg text-sm text-blue-700 dark:text-blue-300 flex items-center gap-2">
          <span>{message}</span>
          <div className="flex space-x-1">
            <div className="w-1.5 h-1.5 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
            <div className="w-1.5 h-1.5 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
            <div className="w-1.5 h-1.5 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
          </div>
        </div>
      </div>
    );
  }

  // ChatGPT-style generating response animation
  return (
    <div className="flex justify-start mb-4">
      <div className="bg-gray-200 dark:bg-gray-700 text-gray-800 dark:text-gray-200 rounded-lg p-3 max-w-[70%] rounded-bl-none">
        <div className="text-xs mb-1 font-medium text-gray-600 dark:text-gray-400">
          AI Assistant
        </div>
        <div className="flex items-center">
          <span className="mr-2">{message}</span>
          <span className="flex space-x-1">
            <span className="h-1.5 w-1.5 bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: "0ms" }}></span>
            <span className="h-1.5 w-1.5 bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: "200ms" }}></span>
            <span className="h-1.5 w-1.5 bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: "400ms" }}></span>
          </span>
        </div>
      </div>
    </div>
  );
};

export default LoadingAnimation;
