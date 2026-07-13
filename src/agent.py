"""
Основной цикл агента — v3.1 PERFECT. Sequential tools, ideal context flow.
"""

import json
import os
from typing import Any, Dict, List, Optional, Set

from .llm_client import LLMClient
from .context import ContextManager
from .tools.registry import create_default_registry
from .prompts import SYSTEM_PROMPT, REASONING_PROMPT
from .repl import REPLInterface
from .tools.undo_tracker import UndoTracker


class Agent:
    """Терминальный ИИ-агент v3.1 — идеальный поток."""

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
        
        self.llm = LLMClient(api_key=api_key, base_url=base_url, model=model)
        self.tools = create_default_registry(working_dir=self.working_dir)
        self.context = ContextManager()
        self.repl = REPLInterface()
        self.undo = UndoTracker()
        
        self.context.load_session()
        self._update_system_prompt()
        
        self.total_turns = 0
        self.total_cost_usd = 0.0

    def _update_system_prompt(self) -> None:
        tool_descriptions = self.tools.get_tool_descriptions()
        prompt = SYSTEM_PROMPT.format(
            tool_descriptions=tool_descriptions,
            working_dir=self.working_dir,
        )
        if self.reasoning_mode:
            prompt += "\n\n" + REASONING_PROMPT
        self.context.set_system_prompt(prompt)

    def set_model(self, model: str) -> None:
        self.model = model
        self.reasoning_mode = model == "deepseek-reasoner"
        self.llm.set_model(model)
        self._update_system_prompt()

    async def run(self) -> None:
        self.repl.print_banner(self.llm.get_model_info())
        
        if len(self.context.messages) > 0:
            self.repl.print_info("💾 Previous session loaded. Type /clear to start fresh.")
        
        while True:
            user_input = await self.repl.get_input()
            
            if not user_input.strip():
                continue
            
            if user_input.startswith("/"):
                if await self._handle_command(user_input):
                    break
                continue
            
            await self._process_request(user_input)
            self.context.save_session()
            self.repl.print_divider()

    async def _handle_command(self, command: str) -> bool:
        parts = command.strip().split()
        cmd = parts[0].lower()
        
        if cmd in ["/exit", "/quit"]:
            self.repl.print_info(f"Goodbye! Session saved. Total cost: ${self.total_cost_usd:.4f}")
            self.context.save_session()
            return True
        
        elif cmd == "/clear":
            self.context.clear()
            self.repl.print_info("Context cleared. Starting fresh.")
        
        elif cmd == "/model" and len(parts) > 1:
            self.set_model(parts[1])
            self.repl.print_info(f"Model switched to: {self.model}")
        
        elif cmd == "/think":
            self.reasoning_mode = not self.reasoning_mode
            self.set_model("deepseek-reasoner" if self.reasoning_mode else "deepseek-chat")
            self.repl.print_info(f"Reasoning mode: {'ON' if self.reasoning_mode else 'OFF'}")
        
        elif cmd == "/tools":
            for name in self.tools.list_tools():
                self.repl.print_info(f"  • {name}")
        
        elif cmd == "/status":
            self.repl.print_info(f"Turns: {self.total_turns} | Est. tokens: {self.context.estimate_tokens()}")
            self.repl.print_info(f"Model: {self.model} | Working dir: {self.working_dir}")
            self.repl.print_info(f"Tool calls: {self.repl.total_tool_calls} | Est. cost: ${self.total_cost_usd:.4f}")
        
        elif cmd == "/undo":
            undone = self.undo.undo_last()
            if undone:
                self.repl.print_success(f"Undid: {undone}")
            else:
                self.repl.print_error("Nothing to undo.")
        
        elif cmd == "/help":
            self.repl.print_help()
        
        else:
            self.repl.print_error(f"Unknown command: {cmd}. Type /help.")
        
        return False

    async def _process_request(self, user_input: str) -> None:
        """Process a user request with perfect tool flow.
        
        Flow:
        1. Add user message to context
        2. Call LLM -> get response
        3. If tool_calls: add assistant with tool_calls, execute each tool, add tool results
        4. Repeat step 2-3 up to 25 iterations
        5. Final assistant message with content
        """
        self.context.add_user_message(user_input)
        self.total_turns += 1
        self.repl.session_count += 1
        
        tool_schemas = self.tools.get_schemas()
        
        # Main interaction loop
        for iteration in range(25):
            # Call LLM
            try:
                response = await self.llm.chat(
                    messages=self.context.get_messages(),
                    tools=tool_schemas,
                )
            except Exception as e:
                self.repl.print_error(f"LLM error: {e}")
                return
            
            self._track_cost(response)
            
            # Show reasoning if present (R1 mode)
            if response.get("reasoning_content"):
                self.repl.print_thinking(response["reasoning_content"])
            
            tool_calls = response.get("tool_calls")
            content = response.get("content")
            
            # No tool calls — this is the final response
            if not tool_calls:
                self.context.add_assistant_message(content=content)
                if content:
                    self.repl.print_response(content)
                else:
                    self.repl.print_info("Model returned empty response. Try rephrasing.")
                return
            
            # Has tool calls — add assistant message with tool_calls
            # IMPORTANT: content must be None for assistant with tool_calls
            self.context.add_assistant_message(content=None, tool_calls=tool_calls)
            
            # Execute each tool SEQUENTIALLY (ensures correct order)
            for tc in tool_calls:
                tool_id = tc["id"]
                tool_name = tc["function"]["name"]
                try:
                    args = json.loads(tc["function"]["arguments"])
                except json.JSONDecodeError:
                    args = {}
                
                self.repl.print_tool_call(tool_name, tc["function"]["arguments"])
                
                # Execute tool with retry
                result_content, success = await self._execute_tool(
                    tool_name, args, tool_id
                )
                
                # Add tool result to context IMMEDIATELY after each tool execution
                # This ensures the API always sees: assistant(tool_calls) -> tool -> tool -> ...
                self.context.add_tool_result(
                    tool_id,
                    tool_name,
                    f"{'Success' if success else 'Error'}: {result_content}",
                )
            
            # Loop continues — call LLM again with tool results
        
        # Max iterations reached
        self.repl.print_warning(
            "Reached maximum tool call iterations (25). The task may be incomplete. "
            "Try breaking it into smaller steps or ask a more specific question."
        )

    async def _execute_tool(
        self,
        tool_name: str,
        args: Dict,
        tool_id: str,
        max_retries: int = 1,
    ) -> tuple[str, bool]:
        """Execute a single tool with retry logic.
        
        Returns: (result_content, success)
        """
        if not self.tools.has(tool_name):
            error = f"Tool '{tool_name}' not found"
            self.repl.print_tool_result(error, success=False)
            return error, False
        
        tool = self.tools.get(tool_name)
        
        for attempt in range(max_retries + 1):
            try:
                result = await tool.execute(**args)
                self.repl.print_tool_result(result.content, success=result.success)
                
                # Track for undo
                if tool_name in ("write_file", "edit_file") and "path" in args:
                    self.undo.track_change(args["path"], tool_name)
                
                return result.content, result.success
            except Exception as e:
                error = str(e)
                if attempt < max_retries:
                    self.repl.print_info(f"Retrying {tool_name}... (attempt {attempt + 2}/{max_retries + 1})")
                    import asyncio
                    await asyncio.sleep(0.5)
                else:
                    self.repl.print_tool_result(error, success=False)
                    return error, False
        
        return "Unknown error", False

    def _track_cost(self, response: Dict) -> None:
        """Track estimated API cost."""
        if response.get("usage"):
            u = response["usage"]
            total = u.get("total_tokens", 0)
            cost = total * 0.20 / 1_000_000
            self.total_cost_usd += cost
            self.repl.print_token_usage(
                u.get("prompt_tokens", 0),
                u.get("completion_tokens", 0),
            )
