from typing import Dict, Any, Optional
from datetime import datetime

class ToolMetrics:
    """Track performance metrics for tools"""
    def __init__(self):
        self.start_time = datetime.now()
        self.computation_time = None
        self.success = False
        self.error = None

    def complete(self, success: bool, error: Optional[str] = None):
        self.computation_time = (datetime.now() - self.start_time).total_seconds()
        self.success = success
        self.error = error

class Tool:
    """Base class for all tools"""
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.metrics = ToolMetrics()

    def validate_input(self, **kwargs) -> bool:
        """Validate input types - override in subclasses"""
        return True

    def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute the tool - override in subclasses"""
        raise NotImplementedError

class ToolRepository:
    """Central repository for all available tools"""
    def __init__(self):
        self._tools: Dict[str, Tool] = {}
        
    def register_tool(self, tool: Tool):
        """Register a new tool"""
        self._tools[tool.name] = tool
        
    def get_tool(self, name: str) -> Optional[Tool]:
        """Get a tool by name"""
        return self._tools.get(name)
        
    def list_tools(self) -> list[Dict[str, str]]:
        """List all available tools"""
        return [{"name": t.name, "description": t.description} 
                for t in self._tools.values()] 