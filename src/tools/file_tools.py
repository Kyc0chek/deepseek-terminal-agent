"""
Инструменты для работы с файлами.
"""

import os
import shutil
from pathlib import Path
from typing import Any, Dict, Optional

from .base import BaseTool, ToolResult


class ReadFileTool(BaseTool):
    """Чтение содержимого файла."""

    def __init__(self):
        super().__init__(
            name="read_file",
            description="Read the contents of a file. Returns the file content as text. "
                       "If the file is too large, it will be truncated with a notice.",
        )

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Relative or absolute path to the file to read",
                },
                "offset": {
                    "type": "integer",
                    "description": "Line number to start reading from (1-based, optional)",
                    "default": 1,
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of lines to read (optional)",
                    "default": 1000,
                },
            },
            "required": ["path"],
        }

    async def execute(self, path: str, offset: int = 1, limit: int = 1000, **kwargs) -> ToolResult:
        try:
            file_path = Path(path).resolve()
            
            if not file_path.exists():
                return ToolResult(success=False, content="", error=f"File not found: {path}")
            
            if not file_path.is_file():
                return ToolResult(success=False, content="", error=f"Path is not a file: {path}")

            # Security check: prevent reading outside working directory
            # (simplified — in production needs proper sandboxing)
            
            content = file_path.read_text(encoding="utf-8", errors="replace")
            lines = content.split("\n")
            
            total_lines = len(lines)
            start = max(0, offset - 1)
            end = min(start + limit, total_lines)
            
            selected_lines = lines[start:end]
            result = "\n".join(selected_lines)
            
            if total_lines > limit:
                result += f"\n\n... [{total_lines - limit} more lines]"
            
            metadata = {
                "path": str(file_path),
                "total_lines": total_lines,
                "shown_lines": end - start,
                "offset": offset,
            }
            
            return ToolResult(success=True, content=result, metadata=metadata)
            
        except Exception as e:
            return ToolResult(success=False, content="", error=str(e))


class WriteFileTool(BaseTool):
    """Запись/создание файла."""

    def __init__(self):
        super().__init__(
            name="write_file",
            description="Write content to a file. Creates the file if it doesn't exist, "
                       "overwrites it if it does. Creates parent directories as needed.",
        )

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Relative or absolute path to the file",
                },
                "content": {
                    "type": "string",
                    "description": "Content to write to the file",
                },
            },
            "required": ["path", "content"],
        }

    async def execute(self, path: str, content: str, **kwargs) -> ToolResult:
        try:
            file_path = Path(path).resolve()
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            file_path.write_text(content, encoding="utf-8")
            
            return ToolResult(
                success=True,
                content=f"File written successfully: {file_path}",
                metadata={"path": str(file_path), "size": len(content)},
            )
            
        except Exception as e:
            return ToolResult(success=False, content="", error=str(e))


class EditFileTool(BaseTool):
    """Редактирование файла — замена строк."""

    def __init__(self):
        super().__init__(
            name="edit_file",
            description="Edit a file by replacing specific text. Uses exact string matching. "
                       "The old_string must match exactly (including whitespace).",
        )

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Path to the file to edit",
                },
                "old_string": {
                    "type": "string",
                    "description": "Exact text to replace (must match exactly)",
                },
                "new_string": {
                    "type": "string",
                    "description": "Text to replace with",
                },
            },
            "required": ["path", "old_string", "new_string"],
        }

    async def execute(self, path: str, old_string: str, new_string: str, **kwargs) -> ToolResult:
        try:
            file_path = Path(path).resolve()
            
            if not file_path.exists():
                return ToolResult(success=False, content="", error=f"File not found: {path}")
            
            content = file_path.read_text(encoding="utf-8")
            
            if old_string not in content:
                return ToolResult(
                    success=False,
                    content="",
                    error=f"old_string not found in file. File may have changed.",
                )
            
            new_content = content.replace(old_string, new_string, 1)
            file_path.write_text(new_content, encoding="utf-8")
            
            return ToolResult(
                success=True,
                content=f"File edited successfully: {file_path}",
                metadata={"path": str(file_path)},
            )
            
        except Exception as e:
            return ToolResult(success=False, content="", error=str(e))


class ListDirTool(BaseTool):
    """Просмотр содержимого директории."""

    def __init__(self):
        super().__init__(
            name="list_dir",
            description="List the contents of a directory. Returns files and subdirectories.",
        )

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Path to the directory (default: current)",
                    "default": ".",
                },
            },
            "required": [],
        }

    async def execute(self, path: str = ".", **kwargs) -> ToolResult:
        try:
            dir_path = Path(path).resolve()
            
            if not dir_path.exists():
                return ToolResult(success=False, content="", error=f"Directory not found: {path}")
            
            if not dir_path.is_dir():
                return ToolResult(success=False, content="", error=f"Path is not a directory: {path}")
            
            entries = []
            for entry in sorted(dir_path.iterdir()):
                entry_type = "dir" if entry.is_dir() else "file"
                size = ""
                if entry.is_file():
                    try:
                        size_bytes = entry.stat().st_size
                        if size_bytes < 1024:
                            size = f"{size_bytes}B"
                        elif size_bytes < 1024 * 1024:
                            size = f"{size_bytes / 1024:.1f}KB"
                        else:
                            size = f"{size_bytes / (1024 * 1024):.1f}MB"
                    except:
                        pass
                entries.append(f"[{entry_type}] {entry.name} {size}")
            
            content = "\n".join(entries) if entries else "(empty directory)"
            
            return ToolResult(
                success=True,
                content=content,
                metadata={"path": str(dir_path), "count": len(entries)},
            )
            
        except Exception as e:
            return ToolResult(success=False, content="", error=str(e))


class DeleteFileTool(BaseTool):
    """Удаление файла или директории."""

    def __init__(self):
        super().__init__(
            name="delete_file",
            description="Delete a file or directory. For directories, removes recursively.",
        )

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Path to the file or directory to delete",
                },
            },
            "required": ["path"],
        }

    async def execute(self, path: str, **kwargs) -> ToolResult:
        try:
            file_path = Path(path).resolve()
            
            if not file_path.exists():
                return ToolResult(success=False, content="", error=f"Path not found: {path}")
            
            if file_path.is_dir():
                shutil.rmtree(file_path)
            else:
                file_path.unlink()
            
            return ToolResult(
                success=True,
                content=f"Deleted: {file_path}",
                metadata={"path": str(file_path)},
            )
            
        except Exception as e:
            return ToolResult(success=False, content="", error=str(e))
