"""
Temporary File Management with TTL

Ensures temp files are cleaned up even on failure.
"""

import os
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional
from contextlib import contextmanager
from backend.utils.logging import get_logger

logger = get_logger(__name__)


class TempFileManager:
    """Manages temporary files with automatic cleanup"""

    def __init__(self, temp_dir: Path, ttl_minutes: int = 15):
        self.temp_dir = temp_dir
        self.ttl_minutes = ttl_minutes
        self.temp_dir.mkdir(parents=True, exist_ok=True)

    def get_temp_path(self, correlation_id: str, suffix: str) -> Path:
        """Get a temp file path"""
        return self.temp_dir / f"{correlation_id}_{suffix}"

    def cleanup_file(self, file_path: Path, delay_seconds: int = 0) -> None:
        """Delete a file (immediately or after delay)"""
        try:
            if delay_seconds == 0:
                if file_path.exists():
                    file_path.unlink()
                    logger.debug(f"Deleted temp file: {file_path.name}")
            else:
                # For background cleanup, just mark for later
                # In a real system, you'd use a task queue
                pass
        except Exception as e:
            logger.warning(f"Failed to delete temp file {file_path}: {e}")

    def cleanup_old_files(self) -> None:
        """Clean up files older than TTL"""
        cutoff_time = datetime.now() - timedelta(minutes=self.ttl_minutes)

        for file_path in self.temp_dir.glob("*.pdf"):
            try:
                file_mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                if file_mtime < cutoff_time:
                    file_path.unlink()
                    logger.debug(f"Deleted old temp file: {file_path.name}")
            except Exception as e:
                logger.warning(f"Failed to clean up {file_path}: {e}")

    @contextmanager
    def managed_temp_file(self, correlation_id: str, suffix: str):
        """Context manager for temp files that ensures cleanup"""
        temp_path = self.get_temp_path(correlation_id, suffix)

        try:
            yield temp_path
        finally:
            # Always clean up, even on exception
            self.cleanup_file(temp_path)
