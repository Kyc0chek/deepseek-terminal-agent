#!/usr/bin/env python3
"""
DeepSeek Terminal Agent v3.1 — Perfect Entry Point.

Исправленные проблемы:
- Корректный импорт через sys.path для cross-platform
- Без асинхронного EventLoopPolicy (Windows compatible)
- Sequential tool execution (без race conditions)
- Безопасный trim контекста (не разрывает tool_calls блоки)
"""

import sys
import os
import asyncio
from pathlib import Path

# ── Cross-platform path resolution ──────────────────────────────────────
# Get absolute path of the project root (where this file is: src/)
CURRENT_FILE = Path(__file__).resolve()
PROJECT_ROOT = CURRENT_FILE.parent.parent  # src/ -> project_root/

# Ensure src is in path for imports
SRC_DIR = CURRENT_FILE.parent
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

# ── Environment ──────────────────────────────────────────────────────────
from dotenv import load_dotenv
env_file = PROJECT_ROOT / ".env"
if env_file.exists():
    load_dotenv(str(env_file))

# ── Main ─────────────────────────────────────────────────────────────────
from agent import Agent
from config import WORKSPACE_DIR


async def main():
    agent = Agent(
        api_key=os.getenv("DEEPSEEK_API_KEY"),
        base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
        model=os.getenv("DEEPSEEK_MODEL", "deepseek-chat"),
        working_dir=WORKSPACE_DIR,
    )
    await agent.run()


if __name__ == "__main__":
    asyncio.run(main())
