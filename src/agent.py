"""
Основной цикл агента — улучшенная версия с proactive behavior и streaming.
"""

import json
import os
from typing import Any, Dict, List, Optional

from .llm_client import LLMClient
from .context import ContextManager
from .tools.registry import ToolRegistry, create_default_registry
from .prompts import SYSTEM_PROMPT, REASONING_PROMPT
from .repl import REPLInterface


class Agent:
    """Терминальный ИИ-агент с проактивным поведением."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: str = "deepseek-chat",
        working_dir: str = ".",
    ):
        self.working_dir = os.path.abspath(working_dir)
        self.model = model
        self.reasoning_mode = model == "deepseek-reasoner"
        
        # Initialize components
        self.llm = LLMClient(
            api_key=api_key,
            base_url=base_url,
            model=model,
        )
        self.tools = create_default_registry(working_dir=self.working_dir)
        self.context = ContextManager()
        self.repl = REPLInterface()
        
        # Load previous session memory
        self.context.load_session()
        
        # Set system prompt
        self._update_system_prompt()

    def _update_system_prompt(self) -> None:
        """Обновить системный промпт."""
        tool_descriptions = self.tools.get_tool_descriptions()
        prompt = SYSTEM_PROMPT.format(
            tool_descriptions=tool_descriptions,
            working_dir=self.working_dir,
        )
        if self.reasoning_mode:
            prompt += "\n\n" + REASONING_PROMPT
        self.context.set_system_prompt(prompt)

    def set_model(self, model: str) -> None:
        """Сменить модель."""
        self.model = model
        self.reasoning_mode = model == "deepseek-reasoner"
        self.llm.set_model(model)
        self._update_system_prompt()

    async def run(self) -> None:
        """Запустить REPL."""
        self.repl.print_banner(self.llm.get_model_info())
        
        if len(self.context.messages) > 1:
            self.repl.print_info("💾 Previous session loaded. Type /clear to start fresh.")
        
        while True:
            user_input = await self.repl.get_input()
            
            if not user_input.strip():
                continue
            
            # Handle commands
            if user_input.startswith("/"):
                if await self._handle_command(user_input):
                    break
                continue
            
            # Process user request
            await self._process_request(user_input)
            
            # Save session after each turn
            self.context.save_session()
            
            # Print divider for readability
            self.repl.print_divider()

    async def _handle_command(self, command: str) -> bool:
        """Обработать слэш-команду. Возвращает True если нужно выйти."""
        parts = command.strip().split()
        cmd = parts[0].lower()
        
        if cmd in ["/exit", "/quit"]:
            self.repl.print_info("Goodbye! Session saved.")
            self.context.save_session()
            return True
        
        elif cmd == "/clear":
            self.context.clear()
            self.repl.print_info("Context cleared. Starting fresh.")
        
        elif cmd == "/model" and len(parts) > 1:
            new_model = parts[1]
            self.set_model(new_model)
            self.repl.print_info(f"Model switched to: {new_model}")
        
        elif cmd == "/think":
            self.reasoning_mode = not self.reasoning_mode
            new_model = "deepseek-reasoner" if self.reasoning_mode else "deepseek-chat"
            self.set_model(new_model)
            self.repl.print_info(f"Reasoning mode: {'ON' if self.reasoning_mode else 'OFF'}")
        
        elif cmd == "/tools":
            self.repl.print_info("Available tools:")
            for name in self.tools.list_tools():
                self.repl.print_info(f"  • {name}")
        
        elif cmd == "/status":
            self.repl.print_info(f"Session: {self.repl.session_count} messages | {self.context.estimate_tokens()} est. tokens")
            self.repl.print_info(f"Model: {self.model}")
            self.repl.print_info(f"Working dir: {self.working_dir}")
            self.repl.print_info(f"Tool calls this session: {self.repl.total_tool_calls}")
        
        elif cmd == "/help":
            self.repl.print_help()
        
        else:
            self.repl.print_error(f"Unknown command: {cmd}. Type /help for available commands.")
        
        return False

    async def _process_request(self, user_input: str) -> None:
        """Обработать запрос пользователя."""
        # Add user message to context
        self.context.add_user_message(user_input)
        self.repl.session_count += 1
        
        # Get available tools
        tool_schemas = self.tools.get_schemas()
        
        # Call LLM
        try:
            response = await self.llm.chat(
                messages=self.context.get_messages(),
                tools=tool_schemas,
            )
        except Exception as e:
            self.repl.print_error(f"LLM error: {e}")
            return
        
        # Show reasoning if present (R1 mode)
        if response.get("reasoning_content"):
            self.repl.print_thinking(response["reasoning_content"])
        
        # Show token usage
        if response.get("usage"):
            u = response["usage"]
            self.repl.print_token_usage(u["prompt_tokens"], u["completion_tokens"])
        
        # Handle tool calls in a loop (LLM may want multiple rounds)
        max_iterations = 10
        iteration = 0
        
        while response.get("tool_calls") and iteration < max_iterations:
            iteration += 1
            
            # Add assistant message with tool calls to context
            self.context.add_assistant_message(
                content=None,
                tool_calls=response["tool_calls"],
            )
            
            # Execute all tools in this round
            for tc in response["tool_calls"]:
                tool_name = tc["function"]["name"]
                tool_id = tc["id"]
                
                try:
                    args = json.loads(tc["function"]["arguments"])
                except json.JSONDecodeError:
                    args = {}
                
                self.repl.print_tool_call(tool_name, tc["function"]["arguments"])
                
                if not self.tools.has(tool_name):
                    error = f"Tool '{tool_name}' not found"
                    self.repl.print_tool_result(error, success=False)
                    self.context.add_tool_result(tool_id, tool_name, error)
                    continue
                
                tool = self.tools.get(tool_name)
                try:
                    result = await tool.execute(**args)
                    self.repl.print_tool_result(result.content, success=result.success)
                    self.context.add_tool_result(
                        tool_id, tool_name, 
                        f"{'Success' if result.success else 'Error'}: {result.content}"
                    )
                except Exception as e:
                    error = str(e)
                    self.repl.print_tool_result(error, success=False)
                    self.context.add_tool_result(tool_id, tool_name, f"Error: {error}")
            
            # Call LLM again with tool results
            try:
                response = await self.llm.chat(
                    messages=self.context.get_messages(),
                    tools=tool_schemas,
                )
            except Exception as e:
                self.repl.print_error(f"LLM error: {e}")
                return
            
            # Show reasoning if present (R1 mode)
            if response.get("reasoning_content"):
                self.repl.print_thinking(response["reasoning_content"])
            
            # Show token usage for this round
            if response.get("usage"):
                u = response["usage"]
                self.repl.print_token_usage(u["prompt_tokens"], u["completion_tokens"])
        
        # Add final assistant message (no tool calls)
        self.context.add_assistant_message(
            content=response.get("content"),
        )
        
        # Show final response
        if response.get("content"):
            self.repl.print_response(response["content"])
        
        # If max iterations reached, warn
        if iteration >= max_iterations:
            self.repl.print_warning("Reached maximum tool call iterations (10). The task may be incomplete. Try breaking it into smaller steps.")
        
        # Proactive: if no content but also no tool calls, something is wrong
        if not response.get("content") and not response.get("tool_calls"):
            self.repl.print_info("The model returned an empty response. This can happen with some models. Try rephrasing your request.")
