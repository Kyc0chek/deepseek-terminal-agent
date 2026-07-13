"""
REPL интерфейс — улучшенный интерактивный терминал с токен-трекером и прогрессом.
"""

import os
from typing import Optional

from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.live import Live
from rich.spinner import Spinner
from rich.layout import Layout


class REPLInterface:
    """Интерактивный терминальный интерфейс с расширенным UI."""

    def __init__(self):
        self.console = Console()
        self.history_file = os.path.expanduser("~/.deepseek_agent_history")
        self.total_tokens_used = 0
        self.total_tool_calls = 0
        self.session_count = 0
        
        self.session = PromptSession(
            history=FileHistory(self.history_file),
        )

    def print_banner(self, model_info: str) -> None:
        """Показать приветственный баннер."""
        banner = Text()
        banner.append("╔══════════════════════════════════════════╗\n", style="cyan")
        banner.append("║   ", style="cyan")
        banner.append("🔥 DeepSeek Terminal Agent", style="bold green")
        banner.append("      ║\n", style="cyan")
        banner.append("╠══════════════════════════════════════════╣\n", style="cyan")
        banner.append("║  ", style="cyan")
        banner.append(model_info[:40].ljust(40), style="dim")
        banner.append("║\n", style="cyan")
        banner.append("╚══════════════════════════════════════════╝\n", style="cyan")
        
        self.console.print(banner)
        self.console.print("Type /help for commands, /exit to quit\n", style="dim")

    def print_response(self, content: str, title: str = "🤖 Agent") -> None:
        """Показать ответ агента."""
        self.console.print(Panel(content, border_style="green", title=title, title_align="left"))

    def print_streaming(self, content: str) -> None:
        """Показать чанк стримингового ответа."""
        self.console.print(content, end="")

    def end_streaming(self) -> None:
        """Закончить стриминг."""
        self.console.print()

    def print_tool_call(self, tool_name: str, arguments: str) -> None:
        """Показать вызов инструмента."""
        self.total_tool_calls += 1
        self.console.print(f"[dim]→ [{self.total_tool_calls}] Running:[/dim] {tool_name}", style="yellow")

    def print_tool_result(self, result: str, success: bool = True) -> None:
        """Показать результат инструмента."""
        color = "green" if success else "red"
        self.console.print(f"[dim]← Result:[/dim]", style=color)
        if result:
            display = result[:800] + ("\n... [truncated]" if len(result) > 800 else "")
            self.console.print(display, style=color)

    def print_error(self, error: str) -> None:
        """Показать ошибку."""
        self.console.print(Panel(f"[red]{error}[/red]", border_style="red", title="❌ Error"))

    def print_info(self, message: str) -> None:
        """Показать информационное сообщение."""
        self.console.print(f"[dim]ℹ {message}[/dim]")

    def print_thinking(self, content: str) -> None:
        """Показать reasoning контент (R1)."""
        self.console.print(Panel(
            content[:3000] + ("..." if len(content) > 3000 else ""),
            border_style="blue",
            title="[blue]🧠 Thinking Process[/blue]",
            title_align="left",
        ))

    def print_token_usage(self, prompt_tokens: int = 0, completion_tokens: int = 0) -> None:
        """Показать статистику токенов."""
        total = prompt_tokens + completion_tokens
        self.total_tokens_used += total
        self.console.print(
            f"[dim]📊 Tokens: {prompt_tokens} prompt + {completion_tokens} completion = {total} total | Session: {self.total_tokens_used}[/dim]",
            style="dim"
        )

    def print_suggestion(self, suggestion: str) -> None:
        """Показать предложение/совет."""
        self.console.print(Panel(
            f"[yellow]💡 {suggestion}[/yellow]",
            border_style="yellow",
            title="💡 Suggestion",
            title_align="left",
        ))

    def print_warning(self, warning: str) -> None:
        """Показать предупреждение."""
        self.console.print(Panel(
            f"[orange1]⚠️ {warning}[/orange1]",
            border_style="orange1",
            title="⚠️ Warning",
            title_align="left",
        ))

    def print_success(self, message: str) -> None:
        """Показать сообщение об успехе."""
        self.console.print(f"[green]✅ {message}[/green]")

    def print_divider(self) -> None:
        """Разделитель."""
        self.console.print("─" * 60, style="dim")

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
[bold cyan]🚀 DeepSeek Terminal Agent — Help[/bold cyan]

[bold]Commands:[/bold]
  /exit, /quit      — Exit the agent
  /clear            — Clear conversation context
  /model <name>     — Switch model (e.g., deepseek-chat, deepseek-reasoner)
  /think            — Toggle reasoning mode (R1)
  /tools            — List available tools
  /status           — Show session status (tokens, tool calls)
  /help             — Show this help

[bold]Usage:[/bold]
  Type your request in natural language. The agent will:
  • Explore the codebase if needed
  • Use tools automatically
  • Suggest improvements and point out issues
  • Keep working until the task is done

[bold]Examples:[/bold]
  > Create a Python script that calculates fibonacci
  > Find all TODO comments and fix them
  > Run the tests and fix any failures
  > Review the code in src/ for bugs and issues
  > Explain what this function does step by step
"""
        self.console.print(help_text)
