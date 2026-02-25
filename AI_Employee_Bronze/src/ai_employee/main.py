"""
Main entry point for the AI Employee system.

This module provides the command-line interface for the AI Employee system.
"""

import sys
import argparse
from pathlib import Path
import signal
import sys
import time

from .core.vault import VaultManager, initialize_vault
from .config.settings import get_settings
from .utils.logger import get_logger, setup_logging
from .utils.exceptions import handle_exception, AIEmployeeException


def setup_signal_handlers(watcher_instance=None):
    """
    Setup signal handlers for graceful shutdown.
    """
    def signal_handler(sig, frame):
        print('\nReceived interrupt signal. Shutting down gracefully...')
        if watcher_instance and hasattr(watcher_instance, 'stop'):
            watcher_instance.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)


def cmd_setup(args):
    """
    Command to setup the vault structure.
    """
    logger = setup_logging("ai_employee.setup")

    print("Setting up AI Employee vault structure...")

    # Use the vault path from settings or command line
    vault_path = args.vault_path or get_settings().VAULT_PATH

    if initialize_vault(vault_path):
        print(f"✅ Vault successfully created at {Path(vault_path).expanduser()}")
        logger.info(f"Vault initialized at {Path(vault_path).expanduser()}")
        return True
    else:
        print(f"❌ Failed to create vault at {Path(vault_path).expanduser()}")
        logger.error(f"Failed to initialize vault at {Path(vault_path).expanduser()}")
        return False


def cmd_watch(args):
    """
    Command to start watching for files.
    """
    from .core.watcher import FileWatcher  # Import here to avoid circular dependencies

    logger = setup_logging("ai_employee.watcher")

    print("Starting AI Employee file watcher...")
    logger.info("Starting AI Employee file watcher")

    # Use the watched folder from settings or command line
    watched_folder = args.folder or get_settings().WATCHED_FOLDER

    # Setup signal handlers for graceful shutdown
    watcher = FileWatcher(watched_folder)
    setup_signal_handlers(watcher)

    try:
        print(f"Monitoring {Path(watched_folder).expanduser()} for new files...")
        logger.info(f"Monitoring {watched_folder} for new files")
        watcher.start()
    except KeyboardInterrupt:
        print("\nStopping file watcher...")
        logger.info("File watcher stopped by user")
    except Exception as e:
        handle_exception(e, logger)
        return False

    return True


def cmd_status(args):
    """
    Command to show the system status.
    """
    from .core.vault import VaultManager
    from .config.settings import get_settings

    logger = setup_logging("ai_employee.status")

    print("Checking AI Employee system status...")

    # Get vault path from settings
    vault_path = get_settings().vault_path_expanded

    # Check if vault exists
    vault_manager = VaultManager(str(vault_path))
    vault_exists = vault_manager.vault_exists()

    print(f"\nVault Path: {vault_path}")
    print(f"Vault Exists: {'✅ Yes' if vault_exists else '❌ No'}")

    if vault_exists:
        stats = vault_manager.get_vault_stats()
        print("\nDirectory Contents:")
        for directory, count in stats['directories'].items():
            print(f"  {directory}/: {count} items")

        print("\nRequired Files:")
        for filename, exists in stats['files'].items():
            status = "✅" if exists else "❌"
            print(f"  {filename}: {status}")

    logger.info(f"Status check completed for vault at {vault_path}")
    return True


def main():
    """
    Main entry point for the AI Employee CLI.
    """
    parser = argparse.ArgumentParser(description="AI Employee System")
    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Setup command
    setup_parser = subparsers.add_parser('setup', help='Setup the vault structure')
    setup_parser.add_argument('--vault-path', '-p', type=str,
                             help='Path to the vault directory (default: ~/AI_Employee_Vault)')
    setup_parser.set_defaults(func=cmd_setup)

    # Watch command
    watch_parser = subparsers.add_parser('watch', help='Start watching for files')
    watch_parser.add_argument('--folder', '-f', type=str,
                             help='Folder to watch for new files (default: Inbox folder in vault)')
    watch_parser.set_defaults(func=cmd_watch)

    # Status command
    status_parser = subparsers.add_parser('status', help='Show system status')
    status_parser.set_defaults(func=cmd_status)

    # If no arguments provided, show help
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)

    # Parse arguments and call appropriate function
    args = parser.parse_args()

    try:
        success = args.func(args)
        if not success:
            sys.exit(1)
    except Exception as e:
        logger = get_logger()
        handle_exception(e, logger)
        sys.exit(1)


if __name__ == "__main__":
    main()