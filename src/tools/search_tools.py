"""
Инструменты для поиска по файлам.
"""

import fnmatch
import os
import re
from pathlib import Path
from typing import Any, Dict, List

from .base import BaseTool, ToolResult


class SearchFilesTool(BaseTool):
    """Поиск файлов по имени/шаблону."""

    def __init__(self):
        super().__init__(
            name="search_files",
            description="Search for files matching a glob pattern in a directory tree. "
                       "Returns list of matching file paths.",
        )

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "pattern": {
                    "type": "string",
                    "description": "Glob pattern to match (e.g., '*.py', 'test_*.py')",
                },
                "path": {
                    "type": "string",
                    "description": "Directory to search in (default: current)",
                    "default": ".",
                },
                "recursive": {
                    "type": "boolean",
                    "description": "Search recursively (default: true)",
                    "default": True,
                },
            },
            "required": ["pattern"],
        }

    async def execute(
        self, pattern: str, path: str = ".", recursive: bool = True, **kwargs
    ) -> ToolResult:
        try:
            search_dir = Path(path).resolve()
            matches = []
            
            if recursive:
                for root, dirs, files in os.walk(search_dir):
                    # Skip common directories to ignore
                    dirs[:] = [d for d in dirs if d not in {".git", "node_modules", "__pycache__", ".venv", "venv", ".pytest_cache", ".mypy_cache"}]
                    for filename in files:
                        if fnmatch.fnmatch(filename, pattern):
                            matches.append(str(Path(root) / filename))
            else:
                for filename in os.listdir(search_dir):
                    if fnmatch.fnmatch(filename, pattern):
                        matches.append(str(search_dir / filename))
            
            content = "\n".join(matches) if matches else "No files found."
            
            return ToolResult(
                success=True,
                content=content,
                metadata={"count": len(matches), "pattern": pattern},
            )
            
        except Exception as e:
            return ToolResult(success=False, content="", error=str(e))


class GrepTool(BaseTool):
    """Поиск текста в файлах (grep)."""

    def __init__(self):
        super().__init__(
            name="grep",
            description="Search for a text pattern in files. Equivalent to grep. "
                       "Returns matching lines with file paths and line numbers.",
        )

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "pattern": {
                    "type": "string",
                    "description": "Text or regex pattern to search for",
                },
                "path": {
                    "type": "string",
                    "description": "File or directory to search in",
                    "default": ".",
                },
                "file_pattern": {
                    "type": "string",
                    "description": "Only search in files matching this glob (e.g., '*.py')",
                    "default": "*",
                },
            },
            "required": ["pattern"],
        }

    async def execute(
        self, pattern: str, path: str = ".", file_pattern: str = "*", **kwargs
    ) -> ToolResult:
        try:
            search_path = Path(path).resolve()
            regex = re.compile(pattern)
            matches = []
            
            files_to_search = []
            
            if search_path.is_file():
                files_to_search.append(search_path)
            else:
                for root, dirs, filenames in os.walk(search_path):
                    dirs[:] = [d for d in dirs if d not in {".git", "node_modules", "__pycache__", ".venv", "venv"}]
                    for filename in filenames:
                        if fnmatch.fnmatch(filename, file_pattern):
                            files_to_search.append(Path(root) / filename)
            
            for file_path in files_to_search:
                try:
                    with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                        for line_num, line in enumerate(f, 1):
                            if regex.search(line):
                                # Truncate long lines
                                line = line.rstrip()
                                if len(line) > 200:
                                    line = line[:200] + "..."
                                rel_path = file_path.relative_to(Path.cwd()) if file_path.is_relative_to(Path.cwd()) else file_path
                                matches.append(f"{rel_path}:{line_num}: {line}")
                except Exception:
                    continue
            
            # Limit results
            if len(matches) > 200:
                matches = matches[:200]
                matches.append(f"\n... [truncated, {len(matches)} total matches]")
            
            content = "\n".join(matches) if matches else "No matches found."
            
            return ToolResult(
                success=True,
                content=content,
                metadata={"count": len(matches), "pattern": pattern},
            )
            
        except Exception as e:
            return ToolResult(success=False, content="", error=str(e))
