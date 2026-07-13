"""
Клиент для DeepSeek API (OpenAI-compatible).
"""

import json
import os
from typing import Any, AsyncGenerator, Dict, List, Optional

from openai import AsyncOpenAI


class LLMClient:
    """Клиент для взаимодействия с DeepSeek API."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: str = "deepseek-chat",
        max_tokens: int = 8192,
        temperature: float = 0.7,
    ):
        self.api_key = api_key or os.getenv("DEEPSEEK_API_KEY")
        self.base_url = base_url or os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
        self.model = model or os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
        self.max_tokens = max_tokens
        self.temperature = temperature

        if not self.api_key:
            raise ValueError("DeepSeek API key is required. Set DEEPSEEK_API_KEY environment variable.")

        self.client = AsyncOpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
        )

    async def chat(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict]] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Отправить запрос к LLM и получить ответ."""
        
        kwargs = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature or self.temperature,
            "max_tokens": max_tokens or self.max_tokens,
        }
        
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"

        response = await self.client.chat.completions.create(**kwargs)
        
        message = response.choices[0].message
        result = {
            "content": message.content,
            "role": message.role,
            "tool_calls": None,
            "reasoning_content": None,
        }
        
        # Extract tool calls if present
        if hasattr(message, "tool_calls") and message.tool_calls:
            result["tool_calls"] = [
                {
                    "id": tc.id,
                    "name": tc.function.name,
                    "arguments": tc.function.arguments,
                }
                for tc in message.tool_calls
            ]
        
        # DeepSeek R1 reasoning content
        if hasattr(message, "reasoning_content") and message.reasoning_content:
            result["reasoning_content"] = message.reasoning_content
        
        # Usage info
        if hasattr(response, "usage") and response.usage:
            result["usage"] = {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens,
            }
        
        return result

    async def stream_chat(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict]] = None,
        temperature: Optional[float] = None,
    ) -> AsyncGenerator[str, None]:
        """Стриминговый ответ от LLM."""
        
        kwargs = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature or self.temperature,
            "stream": True,
        }
        
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"

        stream = await self.client.chat.completions.create(**kwargs)
        
        async for chunk in stream:
            delta = chunk.choices[0].delta
            if delta.content:
                yield delta.content

    def set_model(self, model: str) -> None:
        """Сменить модель."""
        self.model = model

    def get_model_info(self) -> str:
        """Информация о текущей модели."""
        return f"Model: {self.model} | Base URL: {self.base_url}"
