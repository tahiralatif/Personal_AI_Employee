"""
File system watcher for monitoring the Inbox folder.

This module implements the FileWatcher and FileDropHandler classes
that detect new files dropped in the Inbox folder and process them
by creating structured action files in Needs_Action.

Follows OOP standards with type hints, docstrings, and exception handling.
"""

import os
import signal
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileCreatedEvent, FileSystemEvent

from ..config.settings import Settings, get_settings
from ..utils.logger import VaultLogger, get_logger
from ..utils.file_utils import (
    sanitize_filename,
    is_safe_filename,
    validate_file_size,
    safe_move_file,
    write_file_safely,
    ensure_directory_exists,
)
from ..utils.exceptions import (
    FileOperationError,
    FileSizeError,
    HandlerError,
    handle_exception,
)


class FileDropHandler(FileSystemEventHandler):
    """
    Handles file system events for files dropped in the Inbox folder.

    When a new file is detected, this handler:
    1. Validates the file (size, name safety)
    2. Creates a structured .md action file in Needs_Action
    3. Includes YAML frontmatter with metadata
    4. Logs the event to the daily log file

    Inherits from watchdog.events.FileSystemEventHandler.
    """

    def __init__(
        self,
        vault_path: str,
        settings: Settings,
        logger: Optional[VaultLogger] = None
    ) -> None:
        """
        Initialize the FileDropHandler.

        Args:
            vault_path: Path to the vault directory
            settings: Application settings
            logger: Application logger (optional, will use get_logger() if None)
        """
        super().__init__()
        self.vault_path = Path(vault_path).expanduser()
        self.settings = settings
        self.logger = logger if logger is not None else get_logger()

        # Define folder paths
        self.inbox_path = self.vault_path / "Inbox"
        self.needs_action_path = self.vault_path / "Needs_Action"
        self.quarantine_path = self.vault_path / "Quarantine"

        # Ensure directories exist
        self._ensure_directories()

    def _ensure_directories(self) -> None:
        """
        Ensure all required directories exist.
        """
        ensure_directory_exists(self.inbox_path)
        ensure_directory_exists(self.needs_action_path)
        ensure_directory_exists(self.quarantine_path)

    def on_created(self, event: FileSystemEvent) -> None:
        """
        Handle file creation events.

        Args:
            event: File system event object
        """
        try:
            # Only process file creation events (not directories)
            if event.is_directory:
                return

            source_path = Path(event.src_path)

            # Only process files in Inbox folder
            if not self._is_in_inbox(source_path):
                return

            # Skip temporary files (e.g., .tmp, .part)
            if source_path.suffix.lower() in ['.tmp', '.part', '.crdownload']:
                self.logger.debug(f"Skipping temporary file: {source_path.name}")
                return

            self.logger.info(f"File detected in Inbox: {source_path.name}")
            self._process_file(source_path)

        except Exception as e:
            handle_exception(e, self.logger, reraise=False)

    def _is_in_inbox(self, file_path: Path) -> bool:
        """
        Check if a file is in the Inbox folder.

        Args:
            file_path: Path to check

        Returns:
            True if file is in Inbox, False otherwise
        """
        try:
            return str(file_path.parent).startswith(str(self.inbox_path))
        except Exception as e:
            self.logger.error(f"Error checking inbox location: {str(e)}")
            return False

    def _process_file(self, source_path: Path) -> None:
        """
        Process a file dropped in the Inbox.

        Args:
            source_path: Path to the source file
        """
        try:
            # Validate filename safety
            if not is_safe_filename(source_path.name):
                self.logger.warning(f"Unsafe filename detected: {source_path.name}")
                return

            # Validate file size
            is_valid, size_message = validate_file_size(
                source_path,
                self.settings.MAX_FILE_SIZE
            )

            if not is_valid:
                self.logger.warning(f"File too large: {source_path.name} - {size_message}")
                self._move_to_quarantine(source_path, "File exceeds maximum size limit (100MB)")
                return

            # Generate action file
            action_file_path = self._create_action_file(source_path)

            if action_file_path:
                self.logger.log_event(
                    event_type="file_processed",
                    detail=f"Created action file from {source_path.name}",
                    result="success",
                    file_reference=str(action_file_path)
                )
            else:
                self.logger.error(f"Failed to create action file for {source_path.name}")

        except FileSizeError as e:
            self.logger.error(f"File size error: {e.message}")
            self._move_to_quarantine(source_path, str(e.message))
        except FileOperationError as e:
            self.logger.error(f"File operation error: {e.message}")
        except Exception as e:
            handle_exception(e, self.logger, reraise=False)
            self.logger.error(f"Unexpected error processing file {source_path.name}")

    def _create_action_file(self, source_path: Path) -> Optional[Path]:
        """
        Create a structured .md action file in Needs_Action.

        Args:
            source_path: Path to the source file

        Returns:
            Path to the created action file, or None if failed
        """
        try:
            # Generate unique filename for action file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_name = sanitize_filename(source_path.stem)
            action_filename = f"FILE_{timestamp}_{safe_name}.md"
            action_file_path = self.needs_action_path / action_filename

            # Build YAML frontmatter
            frontmatter = self._build_frontmatter(source_path)

            # Build action file content
            content = self._build_action_content(source_path, frontmatter)

            # Write action file
            if write_file_safely(action_file_path, content):
                self.logger.info(f"Action file created: {action_filename}")
                return action_file_path
            else:
                raise FileOperationError(f"Failed to write action file: {action_filename}")

        except Exception as e:
            handle_exception(e, self.logger, reraise=False)
            return None

    def _build_frontmatter(self, source_path: Path) -> Dict[str, Any]:
        """
        Build YAML frontmatter for the action file.

        Args:
            source_path: Path to the source file

        Returns:
            Dictionary containing frontmatter data
        """
        return {
            "type": "file_drop",
            "original_name": source_path.name,
            "received": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "priority": "medium",
            "status": "pending",
            "source_path": str(source_path),
            "file_size": source_path.stat().st_size,
            "file_type": source_path.suffix.lower() if source_path.suffix else "unknown"
        }

    def _build_action_content(self, source_path: Path, frontmatter: Dict[str, Any]) -> str:
        """
        Build the complete content for the action file.

        Args:
            source_path: Path to the source file
            frontmatter: Frontmatter dictionary

        Returns:
            Complete action file content as string
        """
        # Build YAML frontmatter section
        fm_lines = ["---"]
        for key, value in frontmatter.items():
            fm_lines.append(f"{key}: {value}")
        fm_lines.append("---")
        fm_lines.append("")

        # Build body content
        body = f"""# Task: Process {source_path.name}

## What Needs to Be Done
A new file was detected in the Inbox folder and requires processing.

## File Details
- **Original Name:** {source_path.name}
- **Received:** {frontmatter['received']}
- **File Size:** {self._format_file_size(frontmatter['file_size'])}
- **File Type:** {frontmatter['file_type'].upper()}

## Suggested Next Steps
- [ ] Review the file content
- [ ] Determine required action
- [ ] Create a plan in /Plans/
- [ ] Execute the plan
- [ ] Move to /Done/ when complete

---
*Automatically generated by AI Employee Bronze Tier*
"""
        return "\n".join(fm_lines) + body

    def _format_file_size(self, size_bytes: int) -> str:
        """
        Format file size in human-readable format.

        Args:
            size_bytes: Size in bytes

        Returns:
            Formatted string (e.g., "1.5 MB")
        """
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} TB"

    def _move_to_quarantine(self, source_path: Path, reason: str) -> None:
        """
        Move a file to the quarantine folder.

        Args:
            source_path: Path to the file to quarantine
            reason: Reason for quarantine
        """
        try:
            if not source_path.exists():
                return

            # Create quarantine directory if needed
            ensure_directory_exists(self.quarantine_path)

            # Generate unique quarantine filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            quarantine_name = f"QUARANTINE_{timestamp}_{source_path.name}"
            quarantine_path = self.quarantine_path / quarantine_name

            # Move file
            if safe_move_file(source_path, quarantine_path):
                self.logger.log_event(
                    event_type="file_quarantined",
                    detail=f"Moved {source_path.name} to quarantine: {reason}",
                    result="warning",
                    file_reference=str(quarantine_path)
                )
            else:
                raise FileOperationError(f"Failed to move {source_path.name} to quarantine")

        except Exception as e:
            handle_exception(e, self.logger, reraise=False)


class WatcherService:
    """
    Service that manages the file system watcher lifecycle.

    Responsibilities:
    - Own the Observer lifecycle (start, stop)
    - Register FileDropHandler on the Inbox folder
    - Handle KeyboardInterrupt gracefully
    - Print status messages to terminal
    """

    def __init__(
        self,
        vault_path: str,
        settings: Settings,
        logger: VaultLogger
    ) -> None:
        """
        Initialize the WatcherService.

        Args:
            vault_path: Path to the vault directory
            settings: Application settings
            logger: Application logger
        """
        self.vault_path = Path(vault_path).expanduser()
        self.settings = settings
        self.logger = logger

        # Initialize observer and handler
        self.observer: Optional[Observer] = None
        self.handler: Optional[FileDropHandler] = None

        # Watched folder
        self.watch_folder = self.vault_path / "Inbox"

        # Running state
        self._running = False

    def start(self) -> bool:
        """
        Start the file system watcher.

        Returns:
            True if started successfully, False otherwise
        """
        try:
            self.logger.info("Starting WatcherService...")

            # Validate watch folder exists
            if not self.watch_folder.exists():
                ensure_directory_exists(self.watch_folder)
                self.logger.info(f"Created watch folder: {self.watch_folder}")

            # Create handler and observer
            self.handler = FileDropHandler(
                vault_path=str(self.vault_path),
                settings=self.settings,
                logger=self.logger
            )

            self.observer = Observer()
            self.observer.schedule(
                self.handler,
                str(self.watch_folder),
                recursive=False
            )

            # Start observer
            self.observer.start()
            self._running = True

            self.logger.info(f"Watcher started on: {self.watch_folder}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to start watcher: {str(e)}")
            self._running = False
            return False

    def stop(self) -> None:
        """
        Stop the file system watcher gracefully.
        """
        try:
            self.logger.info("Stopping WatcherService...")

            if self.observer:
                self.observer.stop()
                self.observer.join(timeout=5)
                self.logger.info("Observer stopped")

            self._running = False
            self.logger.log_event(
                event_type="system_stop",
                detail="File watcher stopped",
                result="success"
            )

        except Exception as e:
            self.logger.error(f"Error stopping watcher: {str(e)}")

    def is_running(self) -> bool:
        """
        Check if the watcher is currently running.

        Returns:
            True if running, False otherwise
        """
        return self._running

    def run_forever(self) -> None:
        """
        Run the watcher until interrupted.

        Handles Ctrl+C gracefully and stops the observer.
        """
        try:
            # Setup signal handlers for graceful shutdown
            signal.signal(signal.SIGINT, self._signal_handler)
            signal.signal(signal.SIGTERM, self._signal_handler)

            self.logger.info("Watcher running. Press Ctrl+C to stop.")

            while self._running:
                time.sleep(1)

        except KeyboardInterrupt:
            self.logger.info("KeyboardInterrupt received")
        finally:
            self.stop()

    def _signal_handler(self, signum, frame) -> None:
        """
        Handle shutdown signals.

        Args:
            signum: Signal number
            frame: Current stack frame
        """
        self.logger.info(f"Signal {signum} received, shutting down...")
        self._running = False


def create_watcher_service(
    vault_path: Optional[str] = None,
    settings: Optional[Settings] = None,
    logger: Optional[VaultLogger] = None
) -> WatcherService:
    """
    Factory function to create a WatcherService instance.

    Args:
        vault_path: Optional vault path (uses settings if not provided)
        settings: Optional settings instance (uses global if not provided)
        logger: Optional logger instance (uses global if not provided)

    Returns:
        Configured WatcherService instance
    """
    if settings is None:
        settings = get_settings()

    if logger is None:
        logger = get_logger()

    if vault_path is None:
        vault_path = settings.VAULT_PATH

    return WatcherService(
        vault_path=vault_path,
        settings=settings,
        logger=logger
    )


if __name__ == "__main__":
    # Example usage / testing
    print("Starting File Watcher (Test Mode)...")

    settings = get_settings()
    logger = get_logger()

    service = create_watcher_service()

    if service.start():
        print(f"✓ Watcher started on: {service.watch_folder}")
        print("Press Ctrl+C to stop...")
        service.run_forever()
    else:
        print("✗ Failed to start watcher")
        sys.exit(1)
