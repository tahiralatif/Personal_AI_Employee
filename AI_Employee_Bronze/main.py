"""
Bronze Tier AI Employee - Main Entry Point

This module provides the CLI interface for the AI Employee system.
It supports setup, watch, and Qwen brain commands for vault initialization,
file monitoring, and AI-powered task processing.

Usage:
    python main.py setup      - Initialize the vault structure
    python main.py watch      - Start the file system watcher
    python main.py process    - Process tasks with Qwen AI
    python main.py ralph      - Run Ralph Wiggum loop
    python main.py orchestrate - Run orchestration cycle
    python main.py run        - Run continuously with orchestration
    python main.py agents     - Run Silver Tier autonomous agents
    python main.py handoff    - Hand off to specific Silver Tier agent
"""

import argparse
import signal
import sys
from pathlib import Path

from src.ai_employee.core.vault import VaultManager
from src.ai_employee.config.settings import get_settings, Settings
from src.ai_employee.utils.logger import setup_logging, VaultLogger
from src.ai_employee.handlers.file_watcher import WatcherService, create_watcher_service
from src.ai_employee.integrations.qwen_brain import create_qwen_brain
from src.ai_employee.integrations.ralph_loop import ralph_loop
from src.ai_employee.orchestrator import create_orchestrator


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
                print("  Directories: Inbox, Needs_Action, In_Progress, Plans,")
                print("               Pending_Approval, Approved, Rejected, Done, Logs, Briefings")
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

    def process_tasks(self) -> int:
        """
        Process tasks with Qwen AI.

        Returns:
            0 if successful, 1 if failed
        """
        try:
            self.logger.info("Processing tasks with Qwen AI...")
            print("\n🤖 Processing tasks with Qwen AI...")
            print("=" * 60)

            # Create Qwen brain
            brain = create_qwen_brain(
                vault_path=self.settings.VAULT_PATH,
                settings=self.settings,
                logger=self.logger
            )

            # Process all tasks
            results = brain.process_all_tasks()

            # Print results
            print(f"\n📊 Processing Results:")
            print(f"   Total: {results['total']}")
            print(f"   Processed: {results['processed']}")
            print(f"   Success: {results['success']}")
            print(f"   Approval Required: {results['approval_required']}")
            print(f"   Autonomous: {results['autonomous']}")
            print(f"   Failed: {results['failed']}")

            if results['errors']:
                print(f"\n⚠️ Errors:")
                for error in results['errors']:
                    print(f"   - {error}")

            print("=" * 60)

            return 0 if results['failed'] == 0 else 1

        except Exception as e:
            self.logger.error(f"Task processing failed: {str(e)}")
            print(f"[ERROR] {str(e)}")
            return 1

    def run_ralph_loop(self) -> int:
        """
        Run Ralph Wiggum loop for persistent task processing.

        Returns:
            0 if successful, 1 if failed
        """
        try:
            self.logger.info("Starting Ralph Wiggum loop...")

            # Run Ralph loop
            results = ralph_loop(
                vault_path=self.settings.VAULT_PATH,
                max_iterations=10,
                check_interval=5
            )

            # Return based on completion
            return 0 if results['completed'] else 1

        except Exception as e:
            self.logger.error(f"Ralph loop failed: {str(e)}")
            print(f"[ERROR] {str(e)}")
            return 1

    def orchestrate(self) -> int:
        """
        Run one orchestration cycle.

        Returns:
            0 if successful, 1 if failed
        """
        try:
            self.logger.info("Running orchestration cycle...")
            print("\n🤖 Running orchestration cycle...")

            # Create orchestrator
            orchestrator = create_orchestrator(
                vault_path=self.settings.VAULT_PATH,
                settings=self.settings,
                logger=self.logger
            )

            # Run cycle
            results = orchestrator.orchestrate_cycle()

            # Print results
            print(f"\n📊 Results:")
            print(f"   Tasks Processed: {results['tasks_processed']}")
            print(f"   Approved Executed: {results['approved_executed']}")

            if results['errors']:
                print(f"   Errors: {len(results['errors'])}")

            return 0 if not results['errors'] else 1

        except Exception as e:
            self.logger.error(f"Orchestration failed: {str(e)}")
            print(f"[ERROR] {str(e)}")
            return 1

    def run_continuous(self) -> int:
        """
        Run continuous orchestration.

        Returns:
            0 if successful, 1 if failed
        """
        try:
            self.logger.info("Starting continuous orchestration...")

            # Create orchestrator
            orchestrator = create_orchestrator(
                vault_path=self.settings.VAULT_PATH,
                settings=self.settings,
                logger=self.logger
            )

            # Setup signal handler for graceful shutdown
            def signal_handler(signum, frame):
                print("\n\n[OK] Stopping orchestration...")
                orchestrator.stop()
                sys.exit(0)

            signal.signal(signal.SIGINT, signal_handler)
            signal.signal(signal.SIGTERM, signal_handler)

            # Run continuous
            orchestrator.run_continuous(cycle_interval=30)

            return 0

        except Exception as e:
            self.logger.error(f"Continuous run failed: {str(e)}")
            print(f"[ERROR] {str(e)}")
            return 1

    def run_silver_agents(self) -> int:
        """
        Run Silver Tier autonomous agents.

        Returns:
            0 if successful, 1 if failed
        """
        try:
            self.logger.info("Starting Silver Tier autonomous agents...")
            print("\n🤖 Running Silver Tier Autonomous Agents...")
            print("=" * 60)

            # Create orchestrator
            orchestrator = create_orchestrator(
                vault_path=self.settings.VAULT_PATH,
                settings=self.settings,
                logger=self.logger
            )

            # Run Silver agents
            results = orchestrator.run_silver_agents()

            # Print results
            print(f"\n📊 Agent Results:")
            print(f"   Agents Run: {', '.join(results.get('agents_run', []))}")
            print(f"   Successful: {results.get('agents_successful', 0)}")
            print(f"   Failed: {results.get('agents_failed', 0)}")

            if results.get('errors'):
                print(f"\n⚠️ Errors:")
                for error in results['errors']:
                    print(f"   - {error}")

            print("=" * 60)

            return 0 if results.get('agents_failed', 0) == 0 else 1

        except Exception as e:
            self.logger.error(f"Silver agents run failed: {str(e)}")
            print(f"[ERROR] {str(e)}")
            return 1

    def run_agent_handoff(self, agent_type: str = "all") -> int:
        """
        Hand off to specific Silver Tier agent.

        Args:
            agent_type: Type of agent (gmail, whatsapp, linkedin, all)

        Returns:
            0 if successful, 1 if failed
        """
        try:
            self.logger.info(f"Handing off to {agent_type} agent...")
            print(f"\n🤖 Handing off to {agent_type.title()} Agent...")
            print("=" * 60)

            # Create orchestrator
            orchestrator = create_orchestrator(
                vault_path=self.settings.VAULT_PATH,
                settings=self.settings,
                logger=self.logger
            )

            # Run agent handoff
            results = orchestrator.run_agent_handoff(agent_type=agent_type)

            # Print results
            if results.get('success'):
                print(f"✓ {agent_type.title()} Agent completed successfully")
            else:
                print(f"✗ {agent_type.title()} Agent failed: {results.get('error', 'Unknown error')}")

            print("=" * 60)

            return 0 if results.get('success') else 1

        except Exception as e:
            self.logger.error(f"Agent handoff failed: {str(e)}")
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
        description="Bronze Tier AI Employee - Local-first AI assistant with Qwen Brain"
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

    # Process command (Qwen AI)
    process_parser = subparsers.add_parser(
        "process",
        help="Process tasks with Qwen AI"
    )
    process_parser.set_defaults(command="process")

    # Ralph Wiggum loop command
    ralph_parser = subparsers.add_parser(
        "ralph",
        help="Run Ralph Wiggum loop for persistent task processing"
    )
    ralph_parser.set_defaults(command="ralph")

    # Orchestrate command
    orchestrate_parser = subparsers.add_parser(
        "orchestrate",
        help="Run one orchestration cycle"
    )
    orchestrate_parser.set_defaults(command="orchestrate")

    # Run continuous command
    run_parser = subparsers.add_parser(
        "run",
        help="Run continuous orchestration"
    )
    run_parser.set_defaults(command="run")

    # Silver agents command
    agents_parser = subparsers.add_parser(
        "agents",
        help="Run Silver Tier autonomous agents (Gmail, WhatsApp, LinkedIn)"
    )
    agents_parser.set_defaults(command="agents")

    # Agent handoff command
    handoff_parser = subparsers.add_parser(
        "handoff",
        help="Hand off to specific Silver Tier agent"
    )
    handoff_parser.add_argument(
        "--type",
        choices=["gmail", "whatsapp", "linkedin", "all"],
        default="all",
        help="Type of agent to run (default: all)"
    )
    handoff_parser.set_defaults(command="handoff")

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
        elif args.command == "process":
            return cli.process_tasks()
        elif args.command == "ralph":
            return cli.run_ralph_loop()
        elif args.command == "orchestrate":
            return cli.orchestrate()
        elif args.command == "run":
            return cli.run_continuous()
        elif args.command == "agents":
            return cli.run_silver_agents()
        elif args.command == "handoff":
            return cli.run_agent_handoff(agent_type=args.type)
        else:
            parser.print_help()
            return 1

    except Exception as e:
        print(f"✗ Fatal error: {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
