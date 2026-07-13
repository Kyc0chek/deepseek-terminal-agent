"""
Точка входа — запуск терминального агента.
"""

import asyncio
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

# Add project root to path so 'src' imports work when running src/main.py directly
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
load_dotenv(project_root / ".env")

from src.agent import Agent


def main():
    """Главная функция."""
    # Check for API key
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        print("Error: DEEPSEEK_API_KEY not set.")
        print("Please create a .env file with your DeepSeek API key:")
        print("  DEEPSEEK_API_KEY=your-key-here")
        print("\nGet your API key at: https://platform.deepseek.com/")
        sys.exit(1)
    
    # Get configuration
    base_url = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
    model = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
    working_dir = os.getenv("WORKING_DIR", ".")
    
    # Create and run agent
    agent = Agent(
        api_key=api_key,
        base_url=base_url,
        model=model,
        working_dir=working_dir,
    )
    
    try:
        asyncio.run(agent.run())
    except KeyboardInterrupt:
        print("\nGoodbye!")
        sys.exit(0)


if __name__ == "__main__":
    main()
