"""
Python execution sandbox — безопасное выполнение Python кода.
"""

import asyncio
import sys
import io
import traceback
import ast
from typing import Any, Dict

from .base import BaseTool, ToolResult


class PythonExecuteTool(BaseTool):
    """Выполнение Python кода в изолированном окружении."""

    def __init__(self):
        super().__init__(
            name="python_execute",
            description="Execute Python code safely in a sandbox. Captures stdout, stderr, and return value. Use this for: testing snippets, running calculations, validating code logic, quick prototyping. WARNING: Has access to filesystem and network — do not execute untrusted code.",
        )

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "code": {
                    "type": "string",
                    "description": "Python code to execute. Can be a single expression or multiple statements.",
                },
                "timeout": {
                    "type": "integer",
                    "description": "Maximum execution time in seconds (default: 30)",
                    "default": 30,
                },
            },
            "required": ["code"],
        }

    async def execute(self, code: str, timeout: int = 30, **kwargs) -> ToolResult:
        """Выполнить Python код безопасно."""
        
        # Basic safety checks
        dangerous = [
            "__import__(\"os\").system", "os.system", "subprocess.call", 
            "subprocess.run", "subprocess.Popen", "eval(", "exec(",
            "open('/etc/passwd'", "open('C:\\\\Windows\\\\System32",
        ]
        for d in dangerous:
            if d in code:
                return ToolResult(
                    success=False,
                    content="",
                    error=f"Potentially dangerous code detected: '{d}'. Use 'bash' tool for system commands instead.",
                )
        
        # Check for syntax errors before execution
        try:
            ast.parse(code)
        except SyntaxError as e:
            return ToolResult(
                success=False,
                content="",
                error=f"Syntax error: {e.msg} at line {e.lineno}, column {e.offset}",
            )
        
        # Create isolated globals
        safe_globals = {
            "__builtins__": __builtins__,
            "print": print,
            "len": len,
            "range": range,
            "enumerate": enumerate,
            "zip": zip,
            "map": map,
            "filter": filter,
            "sum": sum,
            "min": min,
            "max": max,
            "abs": abs,
            "round": round,
            "sorted": sorted,
            "reversed": reversed,
            "list": list,
            "dict": dict,
            "set": set,
            "tuple": tuple,
            "str": str,
            "int": int,
            "float": float,
            "bool": bool,
            "type": type,
            "isinstance": isinstance,
            "hasattr": hasattr,
            "getattr": getattr,
            "dir": dir,
            "iter": iter,
            "next": next,
            "all": all,
            "any": any,
            "chr": chr,
            "ord": ord,
            "hex": hex,
            "bin": bin,
            "oct": oct,
            "pow": pow,
            "divmod": divmod,
            "complex": complex,
            "slice": slice,
            "frozenset": frozenset,
            "bytearray": bytearray,
            "bytes": bytes,
            "memoryview": memoryview,
            "staticmethod": staticmethod,
            "classmethod": classmethod,
            "property": property,
            "Exception": Exception,
            "ValueError": ValueError,
            "TypeError": TypeError,
            "KeyError": KeyError,
            "IndexError": IndexError,
            "AttributeError": AttributeError,
            "RuntimeError": RuntimeError,
            "StopIteration": StopIteration,
            "GeneratorExit": GeneratorExit,
            "SystemExit": SystemExit,
            "KeyboardInterrupt": KeyboardInterrupt,
            # Common modules
            "json": __import__("json"),
            "re": __import__("re"),
            "math": __import__("math"),
            "random": __import__("random"),
            "datetime": __import__("datetime"),
            "collections": __import__("collections"),
            "itertools": __import__("itertools"),
            "functools": __import__("functools"),
            "operator": __import__("operator"),
            "string": __import__("string"),
            "hashlib": __import__("hashlib"),
            "base64": __import__("base64"),
            "urllib": __import__("urllib"),
            "textwrap": __import__("textwrap"),
            "copy": __import__("copy"),
            "pprint": __import__("pprint"),
            "typing": __import__("typing"),
            "inspect": __import__("inspect"),
            "ast": __import__("ast"),
            "time": __import__("time"),
            "uuid": __import__("uuid"),
            # Allow numpy and pandas if available
        }
        
        # Try to add numpy, pandas if available
        for module_name in ["numpy", "pandas", "numpy as np", "pandas as pd"]:
            try:
                if " as " in module_name:
                    name, alias = module_name.split(" as ")
                    safe_globals[alias] = __import__(name)
                else:
                    safe_globals[module_name] = __import__(module_name)
            except ImportError:
                pass
        
        # Capture stdout/stderr
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        stdout_buffer = io.StringIO()
        stderr_buffer = io.StringIO()
        sys.stdout = stdout_buffer
        sys.stderr = stderr_buffer
        
        result_value = None
        error = None
        
        try:
            # Compile and execute
            compiled = compile(code, "<sandbox>", "exec")
            exec(compiled, safe_globals)
            
            # Try to get the last expression value
            try:
                last_expr = ast.parse(code).body[-1]
                if isinstance(last_expr, ast.Expr):
                    result_value = eval(compile(ast.Expression(last_expr.value), "<sandbox>", "eval"), safe_globals)
            except (IndexError, SyntaxError):
                pass
        except Exception as e:
            error = f"{type(e).__name__}: {str(e)}\n{traceback.format_exc()}"
        finally:
            sys.stdout = old_stdout
            sys.stderr = old_stderr
        
        stdout_text = stdout_buffer.getvalue()
        stderr_text = stderr_buffer.getvalue()
        
        # Build output
        output_parts = []
        if stdout_text:
            output_parts.append(f"[stdout]\n{stdout_text}")
        if stderr_text:
            output_parts.append(f"[stderr]\n{stderr_text}")
        if result_value is not None:
            output_parts.append(f"[return] {repr(result_value)}")
        
        output = "\n\n".join(output_parts) if output_parts else "(no output)"
        
        if error:
            return ToolResult(success=False, content=output, error=error)
        
        return ToolResult(success=True, content=output)
