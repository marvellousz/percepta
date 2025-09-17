import React, { useEffect, useState } from "react";

interface Agent {
  name: string;
  role: string;
  description: string;
}

interface AgentSelectorProps {
  onAgentChange: (agentName: string) => void;
  currentAgent: string;
}

const AgentSelector: React.FC<AgentSelectorProps> = ({
  onAgentChange,
  currentAgent,
}) => {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchAgents = async () => {
      try {
        setIsLoading(true);
        const response = await fetch("/api/agents");
        
        if (!response.ok) {
          throw new Error("Failed to fetch agents");
        }
        
        const data = await response.json();
        setAgents(data.agents || []);
        setError(null);
      } catch (err) {
        console.error("Error fetching agents:", err);
        setError("Failed to load agents. Using default agent.");
        // Set default agents as fallback
        setAgents([
          {
            name: "support-agent",
            role: "Customer Support",
            description: "Helps with technical issues",
          },
          {
            name: "sales-agent",
            role: "Sales Representative",
            description: "Provides product information",
          },
          {
            name: "advisor-agent",
            role: "Financial Advisor",
            description: "Offers financial guidance",
          },
        ]);
      } finally {
        setIsLoading(false);
      }
    };

    fetchAgents();
  }, []);

  return (
    <div className="mb-4">
      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
        Select AI Agent
      </label>
      <div className="flex flex-wrap gap-2">
        {isLoading ? (
          <div className="text-sm text-gray-500">Loading agents...</div>
        ) : (
          agents.map((agent) => (
            <button
              key={agent.name}
              onClick={() => onAgentChange(agent.name)}
              className={`px-3 py-1.5 text-sm rounded-full transition-colors ${
                currentAgent === agent.name
                  ? "bg-blue-500 text-white"
                  : "bg-gray-200 dark:bg-gray-700 text-gray-800 dark:text-gray-200 hover:bg-gray-300 dark:hover:bg-gray-600"
              }`}
              title={agent.description}
            >
              {agent.role}
            </button>
          ))
        )}
      </div>
      {error && <p className="text-xs text-red-500 mt-1">{error}</p>}
    </div>
  );
};

export default AgentSelector;
