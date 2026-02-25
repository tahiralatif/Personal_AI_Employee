"""
Bronze Tier AI Employee - Main Entry Point

This module provides the CLI interface for the AI Employee system.
It supports setup and watch commands for vault initialization and file monitoring.

Usage:
    python main.py setup    - Initialize the vault structure
    python main.py watch    - Start the file system watcher
"""

import argparse
import signal
import sys
from pathlib import Path

from src.ai_employee.core.vault import VaultManager
from src.ai_employee.config.settings import get_settings, Settings
from src.ai_employee.utils.logger import setup_logging, VaultLogger
from src.ai_employee.handlers.file_watcher import WatcherService, create_watcher_service


class CLIHandler:
    """
    Handles CLI commands for the AI Employee system.
    """

    def __init__(self, settings: Settings, logger: VaultLogger) -> None:
        """
        Initialize the CLI handler.

        Args:
            settings: Application settings
            logger: Application logger
        """
        self.settings = settings
        self.logger = logger
        self.vault_manager = VaultManager(settings.VAULT_PATH)
        self.watcher_service: WatcherService = None

    def setup_vault(self) -> int:
        """
        Set up the vault structure.

        Returns:
            0 if successful, 1 if failed
        """
        try:
            self.logger.info("Starting vault setup...")

            # Check if vault already exists (T025)
            if self.vault_manager.vault_exists():
                self.logger.warning("Vault structure already exists. Skipping creation.")
                print("[OK] Vault structure already exists")
                print(f"  Location: {self.vault_manager.vault_path}")
                return 0

            # Create vault structure
            if self.vault_manager.create_vault_structure():
                self.logger.info("Vault structure created successfully")
                print("[OK] Vault structure created successfully")
                print(f"  Location: {self.vault_manager.vault_path}")
                print("  Directories: Inbox, Needs_Action, Done, Plans, Logs")
                print("  Files: Dashboard.md, Company_Handbook.md")
                return 0
            else:
                self.logger.error("Failed to create vault structure")
                print("[ERROR] Failed to create vault structure")
                return 1

        except Exception as e:
            self.logger.error(f"Vault setup failed: {str(e)}")
            print(f"[ERROR] {str(e)}")
            return 1

    def start_watcher(self) -> int:
        """
        Start the file system watcher.

        Returns:
            0 if successful, 1 if failed
        """
        try:
            self.logger.info("Starting file system watcher...")

            # Validate vault exists before starting watcher
            if not self.vault_manager.vault_exists():
                self.logger.error("Vault structure does not exist. Run 'setup' command first.")
                print("[ERROR] Vault structure does not exist.")
                print("  Run 'python main.py setup' first to initialize the vault.")
                return 1

            # Create and start watcher service
            self.watcher_service = create_watcher_service(
                vault_path=self.settings.VAULT_PATH,
                settings=self.settings,
                logger=self.logger
            )

            if not self.watcher_service.start():
                self.logger.error("Failed to start watcher service")
                print("[ERROR] Failed to start watcher service")
                return 1

            print("[OK] File system watcher started")
            print(f"  Watching: {self.settings.WATCHED_FOLDER}")
            print("  Press Ctrl+C to stop")

            # Log system start
            self.logger.log_event("system_start", "File watcher started", "success")

            # Run forever until interrupted
            self.watcher_service.run_forever()

            return 0

        except KeyboardInterrupt:
            self.logger.info("Watcher stopped by user")
            print("\n[OK] Watcher stopped gracefully")
            return 0
        except Exception as e:
            self.logger.error(f"Watcher failed: {str(e)}")
            print(f"[ERROR] {str(e)}")
            return 1


def create_parser() -> argparse.ArgumentParser:
    """
    Create the argument parser for the CLI.

    Returns:
        Configured ArgumentParser
    """
    parser = argparse.ArgumentParser(
        prog="ai-employee-bronze",
        description="Bronze Tier AI Employee - Local-first AI assistant"
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Setup command
    setup_parser = subparsers.add_parser(
        "setup",
        help="Initialize the vault structure"
    )
    setup_parser.set_defaults(command="setup")

    # Watch command
    watch_parser = subparsers.add_parser(
        "watch",
        help="Start the file system watcher"
    )
    watch_parser.set_defaults(command="watch")

    return parser


def main() -> int:
    """
    Main entry point for the AI Employee CLI.

    Returns:
        Exit code (0 for success, 1 for error)
    """
    try:
        # Load settings
        settings = get_settings()

        # Setup logging
        logger = setup_logging("ai_employee", settings.LOG_LEVEL)

        # Create CLI handler
        cli = CLIHandler(settings, logger)

        # Parse arguments
        parser = create_parser()
        args = parser.parse_args()

        # Execute command
        if args.command == "setup":
            return cli.setup_vault()
        elif args.command == "watch":
            return cli.start_watcher()
        else:
            parser.print_help()
            return 1

    except Exception as e:
        print(f"✗ Fatal error: {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
