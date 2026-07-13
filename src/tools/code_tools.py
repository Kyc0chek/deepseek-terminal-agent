"""
Инструменты для анализа кода и структуры проекта.
"""

import os
from pathlib import Path
from typing import Any, Dict, List

from .base import BaseTool, ToolResult


class ViewProjectTreeTool(BaseTool):
    """Показать дерево структуры проекта."""

    def __init__(self):
        super().__init__(
            name="view_project_tree",
            description="Show the project directory tree. Like the 'tree' command but skips common ignored directories (node_modules, .git, __pycache__, etc.). Returns a visual tree representation.",
        )

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "max_depth": {
                    "type": "integer",
                    "description": "Maximum depth to show (default: 4)",
                    "default": 4,
                },
            },
        }

    async def execute(self, max_depth: int = 4, **kwargs) -> ToolResult:
        try:
            skip = {".git", "node_modules", "__pycache__", ".venv", "venv", ".pytest_cache", ".mypy_cache", ".idea", ".vscode", "dist", "build", "*.egg-info"}
            
            def build_tree(path: Path, prefix: str = "", depth: int = 0) -> str:
                if depth > max_depth:
                    return ""
                
                lines = []
                entries = []
                try:
                    for entry in sorted(path.iterdir(), key=lambda e: (not e.is_dir(), e.name.lower())):
                        if entry.name in skip or entry.name.endswith(".pyc"):
                            continue
                        entries.append(entry)
                except PermissionError:
                    return ""
                
                for i, entry in enumerate(entries):
                    is_last = i == len(entries) - 1
                    connector = "└── " if is_last else "├── "
                    lines.append(f"{prefix}{connector}{entry.name}")
                    
                    if entry.is_dir() and depth < max_depth:
                        extension = "    " if is_last else "│   "
                        subtree = build_tree(entry, prefix + extension, depth + 1)
                        if subtree:
                            lines.append(subtree)
                
                return "\n".join(lines)
            
            root = Path.cwd()
            tree = f"{root.name}\n" + build_tree(root)
            
            return ToolResult(success=True, content=tree, metadata={"root": str(root)})
        except Exception as e:
            return ToolResult(success=False, content="", error=str(e))


class CodeReviewTool(BaseTool):
    """Базовый анализ кода на проблемы."""

    def __init__(self):
        super().__init__(
            name="code_review",
            description="Analyze a code file for common issues: syntax errors, style violations, potential bugs, missing imports, security issues, and performance concerns. Returns a structured review.",
        )

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Path to the code file to review",
                },
            },
            "required": ["path"],
        }

    async def execute(self, path: str, **kwargs) -> ToolResult:
        try:
            file_path = Path(path).resolve()
            if not file_path.exists():
                return ToolResult(success=False, content="", error=f"File not found: {path}")
            if not file_path.is_file():
                return ToolResult(success=False, content="", error=f"Path is not a file: {path}")
            
            content = file_path.read_text(encoding="utf-8", errors="replace")
            lines = content.split("\n")
            total_lines = len(lines)
            
            issues = []
            
            # Basic checks
            for i, line in enumerate(lines, 1):
                stripped = line.strip()
                # TODO/FIXME comments
                if "TODO" in line or "FIXME" in line or "HACK" in line:
                    issues.append(f"Line {i}: {stripped}")
                # Hardcoded secrets (basic pattern)
                if any(kw in line.lower() for kw in ["password", "secret", "api_key", "token"]):
                    if "=" in line and not line.strip().startswith("#") and not line.strip().startswith("//"):
                        issues.append(f"Line {i}: Potential hardcoded secret: {stripped}")
                # Very long lines
                if len(line) > 120:
                    issues.append(f"Line {i}: Very long line ({len(line)} chars)")
                # Trailing whitespace
                if line.rstrip() != line and line.strip():
                    issues.append(f"Line {i}: Trailing whitespace")
                # Empty except blocks
                if "except" in line and i < len(lines) and (lines[i].strip() == "pass" or "..." in lines[i]):
                    issues.append(f"Line {i}: Bare except/pass block")
            
            # Check for missing newlines at end
            if content and not content.endswith("\n"):
                issues.append(f"Missing newline at end of file")
            
            # Check for too many blank lines at end
            if content.endswith("\n\n\n"):
                issues.append(f"Too many trailing blank lines")
            
            summary = f"File: {path} ({total_lines} lines)\n"
            summary += f"Issues found: {len(issues)}\n\n"
            if issues:
                summary += "\n".join(issues[:50])
                if len(issues) > 50:
                    summary += f"\n\n... ({len(issues) - 50} more issues)"
            else:
                summary += "No obvious issues detected."
            
            return ToolResult(success=True, content=summary, metadata={"path": str(file_path), "issues": len(issues)})
        except Exception as e:
            return ToolResult(success=False, content="", error=str(e))


class GetFileSummaryTool(BaseTool):
    """Сводка по файлу: строки, импорты, функции, классы."""

    def __init__(self):
        super().__init__(
            name="get_file_summary",
            description="Get a quick summary of a code file: line count, imports, functions/classes defined, and main purpose. Useful for understanding unfamiliar files.",
        )

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Path to the code file",
                },
            },
            "required": ["path"],
        }

    async def execute(self, path: str, **kwargs) -> ToolResult:
        try:
            file_path = Path(path).resolve()
            if not file_path.exists():
                return ToolResult(success=False, content="", error=f"File not found: {path}")
            if not file_path.is_file():
                return ToolResult(success=False, content="", error=f"Path is not a file: {path}")
            
            content = file_path.read_text(encoding="utf-8", errors="replace")
            lines = content.split("\n")
            total_lines = len(lines)
            
            imports = [l.strip() for l in lines if l.strip().startswith("import ") or l.strip().startswith("from ")]
            functions = [l.strip() for l in lines if l.strip().startswith("def ")]
            classes = [l.strip() for l in lines if l.strip().startswith("class ")]
            
            summary = f"""File Summary: {path}
Total Lines: {total_lines}
Imports: {len(imports)}
Functions: {len(functions)}
Classes: {len(classes)}
"""
            if imports:
                summary += f"\nImports:\n" + "\n".join(f"  - {i}" for i in imports[:15])
                if len(imports) > 15:
                    summary += f"\n  ... ({len(imports) - 15} more)"
            
            if functions:
                summary += f"\n\nFunctions:\n" + "\n".join(f"  - {f}" for f in functions[:15])
                if len(functions) > 15:
                    summary += f"\n  ... ({len(functions) - 15} more)"
            
            if classes:
                summary += f"\n\nClasses:\n" + "\n".join(f"  - {c}" for c in classes[:10])
                if len(classes) > 10:
                    summary += f"\n  ... ({len(classes) - 10} more)"
            
            return ToolResult(success=True, content=summary, metadata={"path": str(file_path)})
        except Exception as e:
            return ToolResult(success=False, content="", error=str(e))
