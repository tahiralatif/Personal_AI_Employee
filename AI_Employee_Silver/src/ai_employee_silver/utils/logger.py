"""
Logging utilities for Silver Tier AI Employee.

Provides structured logging with daily log files, similar to Bronze Tier.
"""

import logging
from pathlib import Path
from datetime import datetime
from typing import Optional


class VaultLogger:
    """
    Logger that writes to daily log files in the vault's Logs folder.

    Attributes:
        logger: Python logging.Logger instance
        log_dir: Path to the Logs directory
    """

    def __init__(
        self,
        name: str,
        log_level: str = "INFO",
        vault_path: Optional[str] = None
    ) -> None:
        """
        Initialize the VaultLogger.

        Args:
            name: Logger name (usually module name)
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            vault_path: Path to the vault directory
        """
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, log_level.upper()))

        # Clear existing handlers
        self.logger.handlers = []

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(getattr(logging, log_level.upper()))
        console_format = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(console_format)
        self.logger.addHandler(console_handler)

        # File handler (daily logs)
        self.log_dir: Optional[Path] = None
        if vault_path:
            self.log_dir = Path(vault_path).expanduser() / "Logs"
            self.log_dir.mkdir(parents=True, exist_ok=True)
            self._setup_file_handler()

    def _setup_file_handler(self) -> None:
        """Set up file handler for daily log files."""
        if not self.log_dir:
            return

        log_file = self.log_dir / f"{datetime.now().strftime('%Y-%m-%d')}.log"
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)  # Log everything to file
        file_format = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_format)
        self.logger.addHandler(file_handler)

    def debug(self, message: str) -> None:
        """Log debug message."""
        self.logger.debug(message)

    def info(self, message: str) -> None:
        """Log info message."""
        self.logger.info(message)

    def warning(self, message: str) -> None:
        """Log warning message."""
        self.logger.warning(message)

    def error(self, message: str) -> None:
        """Log error message."""
        self.logger.error(message)

    def critical(self, message: str) -> None:
        """Log critical message."""
        self.logger.critical(message)

    def log_event(
        self,
        event_type: str,
        detail: str,
        result: str,
        file_reference: Optional[str] = None
    ) -> None:
        """
        Log a structured event.

        Args:
            event_type: Type of event (e.g., "file_processed", "email_fetched")
            detail: Event description
            result: Event result (success, warning, error)
            file_reference: Optional file path reference
        """
        log_message = f"[EVENT] type={event_type} | detail='{detail}' | result={result}"
        if file_reference:
            log_message += f" | file_ref='{file_reference}'"

        if result == "success":
            self.info(log_message)
        elif result == "warning":
            self.warning(log_message)
        else:
            self.error(log_message)


def setup_logging(
    name: str,
    log_level: str = "INFO",
    vault_path: Optional[str] = None
) -> VaultLogger:
    """
    Set up logging for a module.

    Args:
        name: Logger name (usually __name__)
        log_level: Logging level
        vault_path: Path to the vault directory (for file logging)

    Returns:
        Configured VaultLogger instance
    """
    return VaultLogger(name, log_level, vault_path)


def get_logger(name: str = "ai_employee_silver") -> VaultLogger:
    """
    Get a logger instance.

    Args:
        name: Logger name

    Returns:
        VaultLogger instance
    """
    # Try to get settings for vault path
    try:
        from .config.settings import get_settings
        settings = get_settings()
        vault_path = settings.VAULT_PATH
        log_level = settings.LOG_LEVEL
    except Exception:
        vault_path = None
        log_level = "INFO"

    return VaultLogger(name, log_level, vault_path)
