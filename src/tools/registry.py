"""
Реестр инструментов v3 — MAX POWER.
"""

from typing import Dict, List

from .base import BaseTool
from .file_tools import ReadFileTool, WriteFileTool, EditFileTool, ListDirTool, DeleteFileTool
from .shell_tools import BashTool, ViewWorkingDirTool
from .search_tools import SearchFilesTool, GrepTool
from .git_tools import GitStatusTool, GitLogTool, GitDiffTool
from .code_tools import ViewProjectTreeTool, CodeReviewTool, GetFileSummaryTool
from .sandbox import PythonExecuteTool
from .web_search import WebSearchTool


class ToolRegistry:
    """Реестр всех доступных инструментов."""

    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}

    def register(self, tool: BaseTool) -> None:
        self._tools[tool.name] = tool

    def get(self, name: str) -> BaseTool:
        if name not in self._tools:
            raise KeyError(f"Tool '{name}' not found")
        return self._tools[name]

    def has(self, name: str) -> bool:
        return name in self._tools

    def list_tools(self) -> List[str]:
        return list(self._tools.keys())

    def get_schemas(self) -> List[dict]:
        return [tool.get_schema() for tool in self._tools.values()]

    def get_tool_descriptions(self) -> str:
        lines = []
        for name, tool in self._tools.items():
            lines.append(f"- {name}: {tool.description}")
        return "\n".join(lines)


def create_default_registry(working_dir: str = ".") -> ToolRegistry:
    """Создать реестр со всеми инструментами v3."""
    registry = ToolRegistry()
    
    # File tools
    registry.register(ReadFileTool())
    registry.register(WriteFileTool())
    registry.register(EditFileTool())
    registry.register(ListDirTool())
    registry.register(DeleteFileTool())
    
    # Shell tools
    registry.register(BashTool(working_dir=working_dir))
    registry.register(ViewWorkingDirTool(working_dir=working_dir))
    
    # Search tools
    registry.register(SearchFilesTool())
    registry.register(GrepTool())
    
    # Git tools
    registry.register(GitStatusTool(working_dir=working_dir))
    registry.register(GitLogTool(working_dir=working_dir))
    registry.register(GitDiffTool(working_dir=working_dir))
    
    # Code analysis tools
    registry.register(ViewProjectTreeTool())
    registry.register(CodeReviewTool())
    registry.register(GetFileSummaryTool())
    
    # NEW v3 tools
    registry.register(PythonExecuteTool())
    registry.register(WebSearchTool())
    
    return registry
