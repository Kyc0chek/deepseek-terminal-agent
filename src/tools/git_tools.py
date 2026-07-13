"""
Git-инструменты для работы с репозиторием.
"""

import asyncio
import os
from typing import Any, Dict, Optional

from .base import BaseTool, ToolResult


class GitStatusTool(BaseTool):
    """Показать git status — изменённые файлы."""

    def __init__(self, working_dir: Optional[str] = None):
        super().__init__(
            name="git_status",
            description="Show git status of the repository — modified, untracked, and staged files.",
        )
        self.working_dir = working_dir or os.getcwd()

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {},
        }

    async def execute(self, **kwargs) -> ToolResult:
        try:
            process = await asyncio.create_subprocess_shell(
                "git status --short",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=self.working_dir,
            )
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=30)
            
            output = stdout.decode("utf-8", errors="replace").strip()
            if not output:
                output = "Working tree clean — no changes."
            
            return ToolResult(success=True, content=output)
        except Exception as e:
            return ToolResult(success=False, content="", error=str(e))


class GitLogTool(BaseTool):
    """Показать последние коммиты."""

    def __init__(self, working_dir: Optional[str] = None):
        super().__init__(
            name="git_log",
            description="Show recent git commits. Returns last N commits with hash, author, date, and message.",
        )
        self.working_dir = working_dir or os.getcwd()

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "limit": {
                    "type": "integer",
                    "description": "Number of commits to show (default: 5)",
                    "default": 5,
                },
            },
        }

    async def execute(self, limit: int = 5, **kwargs) -> ToolResult:
        try:
            process = await asyncio.create_subprocess_shell(
                f'git log --oneline -{limit} --format="%h | %an | %ar | %s"',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=self.working_dir,
            )
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=30)
            
            output = stdout.decode("utf-8", errors="replace").strip()
            if not output:
                output = "No commits found (or not a git repository)."
            
            return ToolResult(success=True, content=output)
        except Exception as e:
            return ToolResult(success=False, content="", error=str(e))


class GitDiffTool(BaseTool):
    """Показать diff изменений."""

    def __init__(self, working_dir: Optional[str] = None):
        super().__init__(
            name="git_diff",
            description="Show git diff — changes in the working tree. Can show full diff or diff for a specific file.",
        )
        self.working_dir = working_dir or os.getcwd()

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "file": {
                    "type": "string",
                    "description": "Specific file to diff (optional, default: all changed files)",
                    "default": "",
                },
            },
        }

    async def execute(self, file: str = "", **kwargs) -> ToolResult:
        try:
            cmd = f"git diff -- {file}" if file else "git diff"
            process = await asyncio.create_subprocess_shell(
                cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=self.working_dir,
            )
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=30)
            
            output = stdout.decode("utf-8", errors="replace").strip()
            if not output:
                output = "No changes to show."
            elif len(output) > 50000:
                output = output[:50000] + "\n\n... [truncated, diff is too large]"
            
            return ToolResult(success=True, content=output)
        except Exception as e:
            return ToolResult(success=False, content="", error=str(e))
