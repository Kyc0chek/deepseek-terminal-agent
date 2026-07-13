"""
Управление контекстом и историей сообщений — идеальная реализация.
"""

import json
import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from pathlib import Path


@dataclass
class Message:
    """Одно сообщение в контексте."""
    role: str
    content: Optional[str] = None
    tool_calls: Optional[List[Dict]] = None
    tool_call_id: Optional[str] = None
    name: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to OpenAI API format."""
        if self.role == "assistant" and self.tool_calls:
            # Assistant with tool_calls: content MUST be null
            return {
                "role": "assistant",
                "content": None,
                "tool_calls": self.tool_calls,
            }
        elif self.role == "tool":
            # Tool result
            return {
                "role": "tool",
                "content": self.content or "",
                "tool_call_id": self.tool_call_id or "",
                "name": self.name or "",
            }
        else:
            # user, assistant (no tool_calls), system
            return {
                "role": self.role,
                "content": self.content or "",
            }

    @classmethod
    def from_dict(cls, d: Dict) -> "Message":
        return cls(
            role=d["role"],
            content=d.get("content"),
            tool_calls=d.get("tool_calls"),
            tool_call_id=d.get("tool_call_id"),
            name=d.get("name"),
        )


class ContextManager:
    """Идеальное управление контекстом разговора с LLM."""

    def __init__(self, max_messages: int = 100):
        # System prompt stored separately — NOT in messages
        self.system_prompt: str = ""
        # Only user/assistant/tool messages here
        self.messages: List[Message] = []
        self.max_messages = max_messages
        self.memory_file = Path.home() / ".deepseek_agent_memory.json"

    def set_system_prompt(self, prompt: str) -> None:
        """Set system prompt (stored separately from conversation)."""
        self.system_prompt = prompt

    def add_user_message(self, content: str) -> None:
        """Add user message."""
        self.messages.append(Message(role="user", content=content))
        self._trim_context()

    def add_assistant_message(
        self,
        content: Optional[str],
        tool_calls: Optional[List[Dict]] = None,
    ) -> None:
        """Add assistant message.
        
        If tool_calls provided, content should be None (API requirement).
        If no tool_calls, content is the text response.
        """
        self.messages.append(
            Message(role="assistant", content=content, tool_calls=tool_calls)
        )
        self._trim_context()

    def add_tool_result(
        self,
        tool_call_id: str,
        name: str,
        result: str,
    ) -> None:
        """Add tool result message.
        
        Must immediately follow an assistant message with matching tool_calls.
        """
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
        """Get all messages in exact API format.
        
        Order: system -> user -> assistant (tool_calls) -> tool -> tool -> ... -> assistant
        """
        result = []
        
        # System prompt first
        if self.system_prompt:
            result.append({"role": "system", "content": self.system_prompt})
        
        # Then all conversation messages
        for msg in self.messages:
            result.append(msg.to_dict())
        
        return result

    def get_last_assistant_tool_calls(self) -> Optional[List[Dict]]:
        """Get tool_calls from the most recent assistant message."""
        for msg in reversed(self.messages):
            if msg.role == "assistant" and msg.tool_calls:
                return msg.tool_calls
        return None

    def clear(self) -> None:
        """Clear all conversation messages (keeps system prompt)."""
        self.messages = []
        self._save_memory()

    def save_session(self) -> None:
        """Save current session to disk."""
        self._save_memory()

    def load_session(self) -> None:
        """Load previous session from disk."""
        if not self.memory_file.exists():
            return
        try:
            data = json.loads(self.memory_file.read_text(encoding="utf-8"))
            for m in data:
                if m.get("role") == "system":
                    continue  # Skip saved system prompts
                self.messages.append(Message.from_dict(m))
            self._trim_context()
        except Exception:
            pass

    def _save_memory(self) -> None:
        """Save messages to disk."""
        try:
            data = [msg.to_dict() for msg in self.messages]
            self.memory_file.write_text(
                json.dumps(data, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        except Exception:
            pass

    def _trim_context(self) -> None:
        """Trim old messages if context too large."""
        if len(self.messages) <= self.max_messages:
            return
        
        # Strategy: keep system prompt + most recent messages
        # But we must preserve the structure: assistant(tool_calls) + tool results
        # So we trim from the beginning, but never break a tool_calls block
        
        to_remove = len(self.messages) - self.max_messages
        if to_remove <= 0:
            return
        
        # Find a safe cut point — after all tool results of a tool_calls block
        cut_idx = 0
        i = 0
        while i < to_remove:
            msg = self.messages[i]
            if msg.role == "assistant" and msg.tool_calls:
                # Skip past all tool results for this tool_calls
                i += 1
                while i < len(self.messages) and self.messages[i].role == "tool":
                    i += 1
            else:
                i += 1
            cut_idx = i
        
        self.messages = self.messages[cut_idx:]

    def estimate_tokens(self) -> int:
        """Rough token estimate."""
        total_chars = len(self.system_prompt)
        for msg in self.messages:
            total_chars += len(msg.content or "")
            if msg.tool_calls:
                for tc in msg.tool_calls:
                    total_chars += len(tc.get("function", {}).get("arguments", ""))
        return total_chars // 4

    def __len__(self) -> int:
        return len(self.messages)
