"""
Structured Logging with Correlation IDs

Every conversion gets a unique correlation ID that threads through all log messages.
"""

import logging
import sys
from typing import Optional, Dict, Any
from datetime import datetime
import json

# Configure root logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)


class StructuredLogger:
    """Logger that emits structured JSON logs with correlation IDs"""

    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        self.correlation_id: Optional[str] = None

    def set_correlation_id(self, correlation_id: str):
        """Set correlation ID for this logger context"""
        self.correlation_id = correlation_id

    def _log(self, level: str, message: str, **kwargs):
        """Internal log method with structured data"""
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "correlation_id": self.correlation_id,
            "level": level,
            "message": message,
            **kwargs
        }

        if level == "ERROR":
            self.logger.error(json.dumps(log_data))
        elif level == "WARNING":
            self.logger.warning(json.dumps(log_data))
        elif level == "DEBUG":
            self.logger.debug(json.dumps(log_data))
        else:
            self.logger.info(json.dumps(log_data))

    def info(self, message: str, **kwargs):
        """Log info message"""
        self._log("INFO", message, **kwargs)

    def error(self, message: str, **kwargs):
        """Log error message"""
        self._log("ERROR", message, **kwargs)

    def warning(self, message: str, **kwargs):
        """Log warning message"""
        self._log("WARNING", message, **kwargs)

    def debug(self, message: str, **kwargs):
        """Log debug message"""
        self._log("DEBUG", message, **kwargs)

    def stage_start(self, stage: str, **kwargs):
        """Log start of pipeline stage"""
        self.info(f"Stage {stage} started", stage=stage, event="stage_start", **kwargs)

    def stage_complete(self, stage: str, duration_seconds: float, **kwargs):
        """Log completion of pipeline stage"""
        self.info(
            f"Stage {stage} completed",
            stage=stage,
            event="stage_complete",
            duration_seconds=duration_seconds,
            **kwargs
        )

    def stage_error(self, stage: str, error: str, **kwargs):
        """Log error in pipeline stage"""
        self.error(
            f"Stage {stage} failed",
            stage=stage,
            event="stage_error",
            error=error,
            **kwargs
        )


def get_logger(name: str) -> StructuredLogger:
    """Get a structured logger instance"""
    return StructuredLogger(name)
