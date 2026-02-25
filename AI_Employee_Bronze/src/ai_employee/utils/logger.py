"""
Logging system for the AI Employee.

This module implements a logging system that writes to the Logs folder
in the vault structure, following the requirements specified in the constitution.
"""

import logging
import logging.handlers
from pathlib import Path
from datetime import datetime
from typing import Optional
from ..config.settings import get_settings


class VaultLogger:
    """
    Logger class that writes to the vault's Logs folder.
    """

    def __init__(self, name: str = "ai_employee", log_level: Optional[str] = None):
        """
        Initialize the VaultLogger.

        Args:
            name: Name of the logger
            log_level: Log level (uses settings if not provided)
        """
        self.name = name
        self.settings = get_settings()

        # Set log level based on config or parameter
        if log_level is None:
            log_level = self.settings.LOG_LEVEL
        self.log_level = getattr(logging, log_level.upper())

        # Create logger
        self.logger = logging.getLogger(name)
        self.logger.setLevel(self.log_level)

        # Prevent adding multiple handlers if logger already has handlers
        if self.logger.handlers:
            self.logger.handlers.clear()

        # Create formatter
        self.formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

        # Setup file handler for vault logs
        self._setup_vault_file_handler()

        # Setup console handler for immediate feedback
        self._setup_console_handler()

    def _setup_vault_file_handler(self):
        """
        Setup file handler that writes to the vault's Logs folder.
        """
        # Get the vault logs path
        vault_logs_path = self.settings.vault_path_expanded / "Logs"
        vault_logs_path.mkdir(parents=True, exist_ok=True)

        # Create a log file for today
        today = datetime.now().strftime("%Y-%m-%d")
        log_file_path = vault_logs_path / f"{today}.log"

        # Create rotating file handler
        file_handler = logging.handlers.RotatingFileHandler(
            log_file_path,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5
        )
        file_handler.setLevel(self.log_level)
        file_handler.setFormatter(self.formatter)

        self.logger.addHandler(file_handler)

    def _setup_console_handler(self):
        """
        Setup console handler for immediate feedback.
        """
        console_handler = logging.StreamHandler()
        console_handler.setLevel(self.log_level)
        console_handler.setFormatter(self.formatter)

        self.logger.addHandler(console_handler)

    def debug(self, message: str):
        """
        Log a debug message.

        Args:
            message: Message to log
        """
        self.logger.debug(message)

    def info(self, message: str):
        """
        Log an info message.

        Args:
            message: Message to log
        """
        self.logger.info(message)

    def warning(self, message: str):
        """
        Log a warning message.

        Args:
            message: Message to log
        """
        self.logger.warning(message)

    def error(self, message: str):
        """
        Log an error message.

        Args:
            message: Message to log
        """
        self.logger.error(message)

    def critical(self, message: str):
        """
        Log a critical message.

        Args:
            message: Message to log
        """
        self.logger.critical(message)

    def log_event(self, event_type: str, detail: str, result: str = "success", file_reference: Optional[str] = None):
        """
        Log a structured event following the data model specification.

        Args:
            event_type: Type of action (file_detected, file_processed, error, etc.)
            detail: Details about the action
            result: Result of the action (success, failure, warning)
            file_reference: Reference to the file involved (optional)
        """
        event_data = {
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type,
            "detail": detail,
            "result": result
        }

        if file_reference:
            event_data["file_reference"] = file_reference

        # Format as a structured log message
        log_message = (
            f"[EVENT] type={event_type} | "
            f"detail='{detail}' | "
            f"result={result}"
        )

        if file_reference:
            log_message += f" | file_ref='{file_reference}'"

        # Log with appropriate level based on result
        if result.lower() == "error":
            self.logger.error(log_message)
        elif result.lower() == "warning":
            self.logger.warning(log_message)
        else:
            self.logger.info(log_message)


# Global logger instances
_default_logger = None


def get_logger(name: str = "ai_employee") -> VaultLogger:
    """
    Get a logger instance.

    Args:
        name: Name of the logger

    Returns:
        VaultLogger instance
    """
    global _default_logger
    if _default_logger is None:
        _default_logger = VaultLogger(name)
    return _default_logger


def setup_logging(name: str = "ai_employee", log_level: Optional[str] = None) -> VaultLogger:
    """
    Setup and return a logger instance.

    Args:
        name: Name of the logger
        log_level: Log level (uses settings if not provided)

    Returns:
        VaultLogger instance
    """
    return VaultLogger(name, log_level)


# Convenience functions
def debug(message: str):
    """Log a debug message."""
    get_logger().debug(message)


def info(message: str):
    """Log an info message."""
    get_logger().info(message)


def warning(message: str):
    """Log a warning message."""
    get_logger().warning(message)


def error(message: str):
    """Log an error message."""
    get_logger().error(message)


def critical(message: str):
    """Log a critical message."""
    get_logger().critical(message)


def log_event(event_type: str, detail: str, result: str = "success", file_reference: Optional[str] = None):
    """
    Log a structured event.

    Args:
        event_type: Type of action (file_detected, file_processed, error, etc.)
        detail: Details about the action
        result: Result of the action (success, failure, warning)
        file_reference: Reference to the file involved (optional)
    """
    get_logger().log_event(event_type, detail, result, file_reference)


if __name__ == "__main__":
    # Example usage
    logger = setup_logging()
    logger.info("Logger initialized successfully")
    logger.log_event("system_start", "AI Employee system started", "success")
    logger.warning("This is a test warning message")
    logger.error("This is a test error message")