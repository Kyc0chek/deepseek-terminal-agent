"""
Инструменты для выполнения shell команд.
"""

import asyncio
import os
import subprocess
from typing import Any, Dict, Optional

from .base import BaseTool, ToolResult


class BashTool(BaseTool):
    """Выполнение shell/bash команд."""

    def __init__(self, timeout: int = 120, working_dir: Optional[str] = None):
        super().__init__(
            name="bash",
            description="Execute a shell command. Returns stdout and stderr. "
                       "Use this for running tests, installing packages, git operations, etc. "
                       "Commands run in a bash shell.",
        )
        self.timeout = timeout
        self.working_dir = working_dir or os.getcwd()

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "The shell command to execute",
                },
                "timeout": {
                    "type": "integer",
                    "description": "Timeout in seconds (optional, default 120)",
                    "default": 120,
                },
            },
            "required": ["command"],
        }

    async def execute(self, command: str, timeout: Optional[int] = None, **kwargs) -> ToolResult:
        timeout = timeout or self.timeout
        
        try:
            # Run command in bash shell
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=self.working_dir,
                executable="/bin/bash",
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(), timeout=timeout
                )
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                return ToolResult(
                    success=False,
                    content="",
                    error=f"Command timed out after {timeout} seconds",
                )
            
            stdout_text = stdout.decode("utf-8", errors="replace")
            stderr_text = stderr.decode("utf-8", errors="replace")
            
            # Combine output
            output = stdout_text
            if stderr_text:
                output += f"\n\n[stderr]:\n{stderr_text}"
            
            # Truncate if too long
            max_output = 50000
            if len(output) > max_output:
                output = output[:max_output] + f"\n\n... [truncated, total {len(output)} chars]"
            
            success = process.returncode == 0
            
            return ToolResult(
                success=success,
                content=output,
                error=None if success else f"Exit code: {process.returncode}",
                metadata={
                    "returncode": process.returncode,
                    "command": command,
                },
            )
            
        except Exception as e:
            return ToolResult(success=False, content="", error=str(e))


class ViewWorkingDirTool(BaseTool):
    """Показать текущую рабочую директорию."""

    def __init__(self, working_dir: Optional[str] = None):
        super().__init__(
            name="view_working_dir",
            description="Show the current working directory path.",
        )
        self.working_dir = working_dir or os.getcwd()

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {},
        }

    async def execute(self, **kwargs) -> ToolResult:
        return ToolResult(
            success=True,
            content=self.working_dir,
            metadata={"cwd": self.working_dir},
        )
