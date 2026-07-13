"""
Undo tracker — отслеживает изменения файлов и позволяет откатить.
"""

import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional
from datetime import datetime


@dataclass
class FileChange:
    """Одно изменение файла."""
    path: str
    operation: str  # write_file, edit_file
    backup_path: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


class UndoTracker:
    """Отслеживает изменения и позволяет откатить."""

    def __init__(self, max_history: int = 100):
        self.history: List[FileChange] = []
        self.max_history = max_history
        self.backup_dir = Path.home() / ".deepseek_agent_backups"
        self.backup_dir.mkdir(exist_ok=True)

    def track_change(self, file_path: str, operation: str) -> None:
        """Записать изменение перед выполнением."""
        path = Path(file_path).resolve()
        
        backup_path = None
        if path.exists() and path.is_file():
            # Create backup
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            backup_name = f"{path.name}_{timestamp}.bak"
            backup_path = str(self.backup_dir / backup_name)
            try:
                shutil.copy2(path, backup_path)
            except Exception:
                backup_path = None
        
        change = FileChange(
            path=str(path),
            operation=operation,
            backup_path=backup_path,
        )
        
        self.history.append(change)
        if len(self.history) > self.max_history:
            self.history.pop(0)
    
    def undo_last(self) -> Optional[str]:
        """Откатить последнее изменение."""
        if not self.history:
            return None
        
        change = self.history.pop()
        
        if change.backup_path and Path(change.backup_path).exists():
            try:
                shutil.copy2(change.backup_path, change.path)
                return f"Restored {change.path} from backup"
            except Exception as e:
                return f"Failed to restore {change.path}: {e}"
        else:
            # No backup — try to delete if it was a new file
            try:
                Path(change.path).unlink()
                return f"Deleted {change.path} (was newly created)"
            except Exception as e:
                return f"Could not undo {change.path}: {e}"
    
    def get_history(self) -> List[str]:
        """Получить историю изменений."""
        return [f"{c.operation}: {c.path}" for c in reversed(self.history)]
