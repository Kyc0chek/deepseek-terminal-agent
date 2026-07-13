"""
REPL интерфейс — v3.1 PERFECT. Без микса sync/async.
"""

import sys
from typing import Optional

from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.styles import Style as PTStyle
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.syntax import Syntax
from rich.text import Text
from rich.rule import Rule
from rich.columns import Columns
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.live import Live
from rich.align import Align

from .config import WORKSPACE_DIR, PROMPT_HISTORY_FILE


PROMPT_STYLE = PTStyle.from_dict({
    "prompt": "#00D1FF bold",
    "bottom-toolbar": "#00D1FF bg:#1a1a2e",
})


class REPLInterface:
    """Rich-based terminal interface."""
    
    def __init__(self):
        self.console = Console()
        self.total_tool_calls = 0
        self.session_count = 0
        
        # Prompt session — для async prompt
        self.prompt_session = None
        self._setup_prompt_session()
    
    def _setup_prompt_session(self):
        try:
            history = FileHistory(PROMPT_HISTORY_FILE)
        except Exception:
            history = None
        
        commands = ["/exit", "/quit", "/clear", "/model", "/think", "/tools",
                    "/status", "/undo", "/help"]
        
        self.prompt_session = PromptSession(
            history=history,
            auto_suggest=AutoSuggestFromHistory(),
            completer=WordCompleter(commands, ignore_case=True),
            style=PROMPT_STYLE,
            complete_while_typing=True,
        )
    
    async def get_input(self) -> str:
        """Get user input via prompt_toolkit (async)."""
        try:
            return await self.prompt_session.prompt_async(
                [
                    ("class:prompt", "deepseek"),
                    ("class:prompt", "> "),
                ],
                bottom_toolbar=self._get_toolbar,
                rprompt=self._get_rprompt,
            )
        except (EOFError, KeyboardInterrupt):
            return "/exit"
    
    def _get_toolbar(self):
        return f" Model: {self._model_name} | Tools: {self.total_tool_calls} | Turns: {self.session_count} | /help for commands"
    
    @property
    def _model_name(self) -> str:
        return "deepseek-reasoner" if self.session_count < 0 else "deepseek-chat"  # Placeholder
    
    def _get_rprompt(self):
        return "v3.1"
    
    def print_banner(self, model_info: Optional[dict] = None):
        """Print startup banner."""
        self.console.clear()
        self.console.print()
        self.console.print(Align.center(
            Text("🚀 DeepSeek Terminal Agent", style="bold #00D1FF"),
        ))
        self.console.print(Align.center(
            Text("v3.1 — Sequential Tools, Ideal Context", style="dim #666666"),
        ))
        if model_info:
            self.console.print(Align.center(
                Text(f"Model: {model_info.get('model', 'deepseek-chat')} | "
                     f"Max context: {model_info.get('max_tokens', '64K')}",
                     style="dim #666666"),
            ))
        self.console.print()
        self.console.print(Align.center(
            Text("Type /help for commands or just ask me anything!", style="dim"),
        ))
        self.console.print()
    
    def print_response(self, content: str):
        """Print assistant response."""
        self.console.print()
        self.console.print(Markdown(content))
        self.console.print()
    
    def print_thinking(self, reasoning: str):
        """Print reasoning content (R1 mode)."""
        self.console.print()
        self.console.print(Panel(
            Markdown(f"**Reasoning:**\n\n{reasoning}"),
            title="[yellow]🧠 Chain of Thought[/]",
            border_style="yellow",
            padding=(1, 2),
        ))
        self.console.print()
    
    def print_tool_call(self, tool_name: str, arguments: str):
        """Print tool call notification."""
        self.total_tool_calls += 1
        try:
            import json
            args = json.loads(arguments)
            arg_str = ", ".join(f"{k}={v!r}" for k, v in args.items())
        except Exception:
            arg_str = arguments
        
        self.console.print(Panel(
            f"[bold]{tool_name}[/bold]({arg_str})",
            title=f"[cyan]🔧 Tool Call #{self.total_tool_calls}[/]",
            border_style="cyan",
            padding=(1, 2),
        ))
    
    def print_tool_result(self, result: str, success: bool = True):
        """Print tool execution result."""
        if success:
            self.console.print(f"  [green]✓[/green] {result[:200]}")
        else:
            self.console.print(f"  [red]✗[/red] {result[:200]}")
    
    def print_token_usage(self, prompt_tokens: int, completion_tokens: int):
        """Print token usage."""
        total = prompt_tokens + completion_tokens
        self.console.print(f"  [dim]Tokens: {total} ({prompt_tokens} prompt + {completion_tokens} completion)[/dim]")
    
    def print_info(self, message: str):
        self.console.print(f"[cyan]ℹ {message}[/cyan]")
    
    def print_success(self, message: str):
        self.console.print(f"[green]✓ {message}[/green]")
    
    def print_error(self, message: str):
        self.console.print(f"[red]✗ {message}[/red]")
    
    def print_warning(self, message: str):
        self.console.print(f"[yellow]⚠ {message}[/yellow]")
    
    def print_divider(self):
        self.console.print(Rule(style="dim #333333"))
    
    def print_help(self):
        """Print help panel."""
        commands = [
            ("/exit, /quit", "Exit the agent"),
            ("/clear", "Clear conversation context"),
            ("/model <name>", "Switch model (deepseek-chat, deepseek-reasoner)"),
            ("/think", "Toggle reasoning mode (R1)"),
            ("/tools", "List available tools"),
            ("/status", "Show agent status"),
            ("/undo", "Undo last file change"),
            ("/help", "Show this help"),
        ]
        
        help_text = "\n".join(
            f"[bold]{cmd}[/bold] — {desc}"
            for cmd, desc in commands
        )
        
        self.console.print(Panel(
            help_text,
            title="[bold]Available Commands[/bold]",
            border_style="blue",
            padding=(1, 2),
        ))
