"""
REPL интерфейс — интерактивный терминал.
"""

import os
from typing import Optional

from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from rich.console import Console
from rich.panel import Panel
from rich.text import Text


class REPLInterface:
    """Интерактивный терминальный интерфейс."""

    def __init__(self):
        self.console = Console()
        self.history_file = os.path.expanduser("~/.deepseek_agent_history")
        
        self.session = PromptSession(
            history=FileHistory(self.history_file),
        )

    def print_banner(self, model_info: str) -> None:
        """Показать приветственный баннер."""
        banner = Text()
        banner.append("╔══════════════════════════════════════╗\n", style="cyan")
        banner.append("║   ", style="cyan")
        banner.append("DeepSeek Terminal Agent", style="bold green")
        banner.append("    ║\n", style="cyan")
        banner.append("╠══════════════════════════════════════╣\n", style="cyan")
        banner.append("║  ", style="cyan")
        banner.append(model_info[:36].ljust(36), style="dim")
        banner.append("║\n", style="cyan")
        banner.append("╚══════════════════════════════════════╝\n", style="cyan")
        
        self.console.print(banner)
        self.console.print("Type /help for commands, /exit to quit\n", style="dim")

    def print_response(self, content: str) -> None:
        """Показать ответ агента."""
        self.console.print(Panel(content, border_style="green", title="Agent"))

    def print_tool_call(self, tool_name: str, arguments: str) -> None:
        """Показать вызов инструмента."""
        self.console.print(
            f"[dim]→ Running: {tool_name}[/dim]", 
            style="yellow"
        )

    def print_tool_result(self, result: str, success: bool = True) -> None:
        """Показать результат инструмента."""
        color = "green" if success else "red"
        self.console.print(f"[dim]← Result:[/dim]", style=color)
        if result:
            self.console.print(result[:500] + ("..." if len(result) > 500 else ""), style=color)

    def print_error(self, error: str) -> None:
        """Показать ошибку."""
        self.console.print(f"[red]Error: {error}[/red]")

    def print_info(self, message: str) -> None:
        """Показать информационное сообщение."""
        self.console.print(f"[dim]{message}[/dim]")

    def print_thinking(self, content: str) -> None:
        """Показать reasoning контент (R1)."""
        self.console.print(Panel(
            content[:2000] + ("..." if len(content) > 2000 else ""),
            border_style="blue",
            title="[blue]Thinking[/blue]",
        ))

    async def get_input(self) -> str:
        """Получить ввод пользователя."""
        try:
            return await self.session.prompt_async("\n> ")
        except KeyboardInterrupt:
            return "/exit"
        except EOFError:
            return "/exit"

    def print_help(self) -> None:
        """Показать справку."""
        help_text = """
[bold]Available Commands:[/bold]
  /exit, /quit      — Exit the agent
  /clear            — Clear conversation context
  /model <name>     — Switch model (e.g., deepseek-chat, deepseek-reasoner)
  /think            — Toggle reasoning mode (R1)
  /tools            — List available tools
  /help             — Show this help

[bold]Usage:[/bold]
  Just type your request in natural language.
  The agent will use tools automatically as needed.
  Examples:
    > Create a Python script that calculates fibonacci
    > Find all TODO comments in the project
    > Run the tests and fix any failures
    > Explain what this function does
"""
        self.console.print(help_text)
