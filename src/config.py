"""
Configuration — v3.1 PERFECT.
"""

import os
from pathlib import Path

# ── Paths ────────────────────────────────────────────────────────────────
# Project root: directory containing src/
PROJECT_ROOT = Path(__file__).parent.parent

# Working directory (where the agent operates)
WORKSPACE_DIR = os.getenv("DEEPSEEK_WORKSPACE", str(PROJECT_ROOT))

# History and state
STATE_DIR = Path.home() / ".deepseek_agent"
PROMPT_HISTORY_FILE = str(STATE_DIR / "history.txt")
SESSION_FILE = str(STATE_DIR / "session.json")
MEMORY_FILE = str(STATE_DIR / "memory.json")
BACKUP_DIR = STATE_DIR / "backups"

# Create state directory
STATE_DIR.mkdir(parents=True, exist_ok=True)
BACKUP_DIR.mkdir(parents=True, exist_ok=True)

# ── API ──────────────────────────────────────────────────────────────────
API_KEY = os.getenv("DEEPSEEK_API_KEY")
BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")

# ── Context ──────────────────────────────────────────────────────────────
MAX_CONTEXT_MESSAGES = int(os.getenv("DEEPSEEK_MAX_CONTEXT", "100"))
MAX_TOOL_ITERATIONS = int(os.getenv("DEEPSEEK_MAX_ITERATIONS", "25"))

# ── Display ──────────────────────────────────────────────────────────────
MAX_OUTPUT_LENGTH = int(os.getenv("DEEPSEEK_MAX_OUTPUT", "10000"))
TRUNCATE_THRESHOLD = int(os.getenv("DEEPSEEK_TRUNCATE", "8000"))
