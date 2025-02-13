# E-commerce Calculator

## Setup Instructions

1. After opening the codespace, install the dependencies:

```bash
pip install -e .
```

2. Configure the required environment variables:

```bash
export OPENAI_API_KEY=<your-openai-api-key>
export DATABASE_URL=<your-database-url>
```

3. Run the application:

```bash
cd ecommerce_calculator
python main.py
```

## Environment Variables

- `OPENAI_API_KEY`: Your OpenAI API key for AI functionality
- `DATABASE_URL`: Connection string for your database (format: `postgresql://user:password@host:port/dbname`)

## Development

For local development, you can create a `.env` file in the root directory with the above environment variables.

Test Product IDs:

- `985b030a-f6b0-47d9-98d3-98c3c7d35f06`
- `d7d13480-fe01-4a2c-85f2-bcdee4c2a5b0`
- `4a5cfd0f-bda6-460b-a4b2-af5e608ced99`

---

# Enhancements

- Support multiple agents

```python
from typing import Dict, Any
from abc import ABC, abstractmethod

class Agent(ABC):
    """Base class for LLM agents"""
    def __init__(self, agent_id: str, capabilities: List[str]):
        self.agent_id = agent_id
        self.capabilities = capabilities
        self.metrics = AgentMetrics()

    @abstractmethod
    def process_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Process incoming requests using available tools"""
        pass

    @abstractmethod
    def validate_access(self, tool_name: str) -> bool:
        """Validate agent's access to requested tool"""
        pass
```

```python
class AgentManager:
    """Manages multiple LLM agents and their tool access"""
    def __init__(self):
        self._agents: Dict[str, Agent] = {}
        self._tool_repository = ToolRepository()

    def register_agent(self, agent: Agent):
        """Register a new agent"""
        self._agents[agent.agent_id] = agent

    def route_request(self, agent_id: str, request: Dict[str, Any]) -> Dict[str, Any]:
        """Route request to appropriate agent"""
        agent = self._agents.get(agent_id)
        if not agent:
            raise ValueError(f"Unknown agent: {agent_id}")

        return agent.process_request(request)
```
