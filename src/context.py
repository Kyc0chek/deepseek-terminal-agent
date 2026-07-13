"""
Управление контекстом и историей сообщений.
"""

import json
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class Message:
    """Одно сообщение в контексте."""
    role: str  # system, user, assistant, tool
    content: str
    tool_calls: Optional[List[Dict]] = None
    tool_call_id: Optional[str] = None
    name: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        result = {
            "role": self.role,
            "content": self.content,
        }
        if self.tool_calls:
            result["tool_calls"] = self.tool_calls
        if self.tool_call_id:
            result["tool_call_id"] = self.tool_call_id
        if self.name:
            result["name"] = self.name
        return result


class ContextManager:
    """Управление контекстом разговора с LLM."""

    def __init__(self, max_messages: int = 100, max_tokens_estimate: int = 64000):
        self.messages: List[Message] = []
        self.max_messages = max_messages
        self.max_tokens_estimate = max_tokens_estimate
        self.system_prompt: str = ""

    def set_system_prompt(self, prompt: str) -> None:
        self.system_prompt = prompt
        # Remove old system prompt if exists
        self.messages = [m for m in self.messages if m.role != "system"]
        # Insert new system prompt at the beginning
        self.messages.insert(0, Message(role="system", content=prompt))

    def add_user_message(self, content: str) -> None:
        self.messages.append(Message(role="user", content=content))
        self._trim_context()

    def add_assistant_message(
        self, content: str, tool_calls: Optional[List[Dict]] = None
    ) -> None:
        self.messages.append(
            Message(role="assistant", content=content, tool_calls=tool_calls)
        )
        self._trim_context()

    def add_tool_result(self, tool_call_id: str, name: str, result: str) -> None:
        self.messages.append(
            Message(
                role="tool",
                content=result,
                tool_call_id=tool_call_id,
                name=name,
            )
        )
        self._trim_context()

    def get_messages(self) -> List[Dict[str, Any]]:
        """Получить сообщения в формате для OpenAI API."""
        result = []
        for msg in self.messages:
            if msg.role == "system" and self.system_prompt:
                result.append({"role": "system", "content": self.system_prompt})
            elif msg.role == "assistant" and msg.tool_calls:
                d = {"role": "assistant", "content": msg.content or ""}
                d["tool_calls"] = msg.tool_calls
                result.append(d)
            elif msg.role == "tool":
                result.append({
                    "role": "tool",
                    "content": msg.content,
                    "tool_call_id": msg.tool_call_id,
                    "name": msg.name,
                })
            else:
                result.append({"role": msg.role, "content": msg.content})
        return result

    def clear(self) -> None:
        """Очистить историю (кроме system prompt)."""
        system_msgs = [m for m in self.messages if m.role == "system"]
        self.messages = system_msgs

    def _trim_context(self) -> None:
        """Удалить старые сообщения если контекст слишком большой."""
        # Simple strategy: keep last N messages
        if len(self.messages) > self.max_messages:
            # Always keep system prompt
            system_msgs = [m for m in self.messages if m.role == "system"]
            other_msgs = [m for m in self.messages if m.role != "system"]
            # Keep last N-1 other messages (leave room for system)
            keep = self.max_messages - len(system_msgs)
            other_msgs = other_msgs[-keep:]
            self.messages = system_msgs + other_msgs

    def estimate_tokens(self) -> int:
        """Грубая оценка количества токенов."""
        total_chars = sum(len(m.content) for m in self.messages)
        # Rough estimate: ~4 chars per token
        return total_chars // 4

    def __len__(self) -> int:
        return len(self.messages)

    def __repr__(self) -> str:
        return f"ContextManager(messages={len(self.messages)}, estimated_tokens={self.estimate_tokens()})"
