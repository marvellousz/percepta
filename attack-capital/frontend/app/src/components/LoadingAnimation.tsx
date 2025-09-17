import React from "react";

interface LoadingAnimationProps {
  type: "agent-switching" | "generating";
  message?: string;
}

const LoadingAnimation: React.FC<LoadingAnimationProps> = ({ 
  type, 
  message = type === "agent-switching" ? "Switching agent..." : "Generating response..." 
}) => {
  if (type === "agent-switching") {
    return (
      <div className="flex justify-center my-2">
        <div className="bg-blue-100 dark:bg-blue-900 px-4 py-2 rounded-full text-sm text-blue-700 dark:text-blue-300 flex items-center gap-2">
          <div className="flex space-x-1">
            <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
            <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
            <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
          </div>
          <span>{message}</span>
        </div>
      </div>
    );
  }

  // Generating response animation
  return (
    <div className="flex justify-start mb-4">
      <div className="bg-gray-200 dark:bg-gray-700 text-gray-800 dark:text-gray-200 rounded-lg p-3 max-w-[70%]">
        <div className="text-xs mb-1 font-medium text-gray-600 dark:text-gray-400">
          AI Assistant
        </div>
        <div className="flex items-center gap-2">
          <div className="flex space-x-1">
            <div className="w-2 h-2 bg-gray-500 rounded-full animate-pulse" style={{ animationDelay: '0ms' }}></div>
            <div className="w-2 h-2 bg-gray-500 rounded-full animate-pulse" style={{ animationDelay: '200ms' }}></div>
            <div className="w-2 h-2 bg-gray-500 rounded-full animate-pulse" style={{ animationDelay: '400ms' }}></div>
          </div>
          <span className="text-sm text-gray-600 dark:text-gray-400">{message}</span>
        </div>
      </div>
    </div>
  );
};

export default LoadingAnimation;
