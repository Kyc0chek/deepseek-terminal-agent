"""
Базовый класс и система инструментов для агента.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
import json


@dataclass
class ToolResult:
    """Результат выполнения инструмента."""
    success: bool
    content: str
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "content": self.content,
            "error": self.error,
            "metadata": self.metadata,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)


class BaseTool(ABC):
    """Базовый класс для всех инструментов."""

    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description

    @property
    @abstractmethod
    def parameters(self) -> Dict[str, Any]:
        """JSON Schema параметров инструмента."""
        pass

    @abstractmethod
    async def execute(self, **kwargs) -> ToolResult:
        """Выполнить инструмент с заданными параметрами."""
        pass

    def get_schema(self) -> Dict[str, Any]:
        """Получить OpenAI-compatible function schema."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }
