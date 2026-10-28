from typing import Dict, Optional, List, Any
from app.engine.tools.base import BaseTool
from app.engine.tools.profiling import DatasetProfilingTool
from app.engine.tools.validation import DataValidationTool
from app.engine.tools.aggregation import GroupedAggregationTool
from app.engine.tools.timeseries import TimeSeriesAnalysisTool


class ToolRegistry:
    """Centralized registry of approved ConsultOS analytical tools."""

    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}
        # Automatically register the standard approved tools
        self.register(DatasetProfilingTool())
        self.register(DataValidationTool())
        self.register(GroupedAggregationTool())
        self.register(TimeSeriesAnalysisTool())

    def register(self, tool: BaseTool) -> None:
        """Register an approved tool instance."""
        self._tools[tool.name] = tool

    def get(self, name: str) -> Optional[BaseTool]:
        """Retrieve a registered tool by unique name."""
        return self._tools.get(name)

    def has(self, name: str) -> bool:
        """Check if a tool name is registered."""
        return name in self._tools

    def list_tools(self) -> List[Dict[str, Any]]:
        """List metadata for all approved tools."""
        return [
            {
                "name": tool.name,
                "description": tool.description,
            }
            for tool in self._tools.values()
        ]


# Global singleton instance
tool_registry = ToolRegistry()
