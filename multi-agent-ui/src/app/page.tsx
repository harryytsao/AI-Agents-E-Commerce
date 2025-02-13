'use client';

import { useState } from 'react';
import { useChat } from 'ai/react';

const agents = ['assistant', 'researcher', 'analyst'];

export default function Home() {
  const [activeAgent, setActiveAgent] = useState('assistant');
  const { messages, input, handleInputChange, handleSubmit } = useChat({
    api: '/api/agents',
    body: { agent: activeAgent },
    maxSteps: 5,
  });

  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-gray-50 p-4">
      <main className="flex flex-col items-center w-full max-w-4xl mx-auto">
        <h1 className="text-4xl font-bold mb-8 text-gray-800">Multi-Agent UI</h1>

        <div className="flex space-x-4 mb-8">
          {agents.map((agent) => (
            <button
              key={agent}
              onClick={() => setActiveAgent(agent)}
              className={`px-6 py-2 rounded-lg font-medium transition-colors duration-200 ${activeAgent === agent
                ? 'bg-blue-500 text-white shadow-md'
                : 'bg-white text-gray-600 hover:bg-gray-100 border border-gray-200'
                }`}
            >
              {agent.charAt(0).toUpperCase() + agent.slice(1)}
            </button>
          ))}
        </div>

        <div className="w-full bg-white rounded-xl shadow-lg p-6">
          <div className="space-y-4 mb-6 max-h-[600px] overflow-y-auto">
            {messages.map((m) => (
              <div key={m.id} className={`p-4 rounded-lg ${m.role === 'user' ? 'bg-blue-50' : 'bg-gray-50'
                }`}>
                <div className="font-medium mb-1 text-gray-700">
                  {m.role === 'user' ? 'You' : activeAgent.charAt(0).toUpperCase() + activeAgent.slice(1)}
                </div>
                <div className="text-gray-600">{m.content}</div>
                {m.toolInvocations && (
                  <pre className="mt-2 p-3 bg-gray-100 rounded-md text-sm overflow-x-auto text-black">
                    {JSON.stringify(m.toolInvocations, null, 2)}
                  </pre>
                )}
              </div>
            ))}
          </div>

          <form onSubmit={handleSubmit} className="flex gap-2">
            <input
              className="flex-grow p-3 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-black"
              value={input}
              onChange={handleInputChange}
              placeholder={`Ask the ${activeAgent} something...`}
            />
            <button
              type="submit"
              className="px-6 py-3 bg-blue-500 text-white rounded-lg font-medium hover:bg-blue-600 transition-colors duration-200"
            >
              Send
            </button>
          </form>
        </div>
      </main>
    </div>
  );
}