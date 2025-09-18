import React from "react";
import { twMerge } from "tailwind-merge";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { oneDark } from "react-syntax-highlighter/dist/esm/styles/prism";

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
        <div className="prose prose-sm max-w-none dark:prose-invert">
          <ReactMarkdown
            remarkPlugins={[remarkGfm]}
            components={{
              code({ node, inline, className, children, ...props }) {
                const match = /language-(\w+)/.exec(className || '');
                const language = match ? match[1] : '';
                
                if (!inline && language) {
                  return (
                    <SyntaxHighlighter
                      style={oneDark}
                      language={language}
                      PreTag="div"
                      className="rounded-md"
                      {...props}
                    >
                      {String(children).replace(/\n$/, '')}
                    </SyntaxHighlighter>
                  );
                }
                
                return (
                  <code className="bg-gray-100 dark:bg-gray-800 px-1 py-0.5 rounded text-sm" {...props}>
                    {children}
                  </code>
                );
              },
              p: ({ children }) => <p className="mb-2 last:mb-0">{children}</p>,
              ul: ({ children }) => <ul className="list-disc list-inside mb-2 space-y-1">{children}</ul>,
              ol: ({ children }) => <ol className="list-decimal list-inside mb-2 space-y-1">{children}</ol>,
              li: ({ children }) => <li className="text-sm">{children}</li>,
              strong: ({ children }) => <strong className="font-semibold">{children}</strong>,
              em: ({ children }) => <em className="italic">{children}</em>,
              blockquote: ({ children }) => (
                <blockquote className="border-l-4 border-gray-300 dark:border-gray-600 pl-4 italic my-2">
                  {children}
                </blockquote>
              ),
              h1: ({ children }) => <h1 className="text-lg font-bold mb-2">{children}</h1>,
              h2: ({ children }) => <h2 className="text-base font-bold mb-2">{children}</h2>,
              h3: ({ children }) => <h3 className="text-sm font-bold mb-1">{children}</h3>,
            }}
          >
            {message}
          </ReactMarkdown>
        </div>
      </div>
    </div>
  );
};

export default ChatMessage;
