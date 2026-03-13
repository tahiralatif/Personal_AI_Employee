"""Main entry point for Gold Tier AI Employee system."""
import argparse
import asyncio
import sys
from typing import Dict, Any
import logging
from .config.settings import settings
from .core.vault import vault
from .core.orchestrator import orchestrator
from .integrations.odoo_integration import odoo
from .integrations.facebook_integration import facebook
from .integrations.instagram_integration import instagram
from .integrations.twitter_integration import twitter


def setup_logging():
    """Setup basic logging configuration."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('gold_tier.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )


def initialize_system():
    """Initialize the Gold Tier system."""
    print("🚀 Initializing Gold Tier AI Employee System...")

    # Initialize vault
    print("📂 Setting up vault...")
    vault.initialize_vault()

    # Initialize integrations
    print("🔌 Initializing integrations...")

    # Odoo integration
    if all([settings.ODOO_URL, settings.ODOO_DB, settings.ODOO_USERNAME, settings.ODOO_PASSWORD]):
        print("🏢 Connecting to Odoo...")
        odoo.connect()
    else:
        print("⚠️  Odoo integration not configured (missing credentials)")

    # Facebook integration
    if settings.FACEBOOK_PAGE_ACCESS_TOKEN:
        print("📘 Connecting to Facebook...")
        facebook.verify_connection()
    else:
        print("⚠️  Facebook integration not configured (missing credentials)")

    # Instagram integration
    if settings.INSTAGRAM_ACCESS_TOKEN:
        print("📸 Connecting to Instagram...")
        instagram.verify_connection()
    else:
        print("⚠️  Instagram integration not configured (missing credentials)")

    # Twitter integration
    if all([settings.TWITTER_API_KEY, settings.TWITTER_API_SECRET,
            settings.TWITTER_ACCESS_TOKEN, settings.TWITTER_ACCESS_SECRET]):
        print("🐦 Connecting to Twitter/X...")
        twitter.connect()
    else:
        print("⚠️  Twitter/X integration not configured (missing credentials)")

    print("✅ Gold Tier system initialized successfully!")


def run_orchestrator():
    """Run the main orchestrator."""
    print("🤖 Starting Gold Tier Orchestrator...")
    orchestrator.run()


def run_agent(agent_type: str):
    """Run a specific agent."""
    print(f"🤖 Starting {agent_type} agent...")

    if agent_type == "odoo":
        # Example: run Odoo-specific tasks
        print("Running Odoo agent...")
        # Add specific Odoo agent logic here
    elif agent_type == "social":
        # Example: run social media agent
        print("Running social media agent...")
        # Add specific social media agent logic here
    elif agent_type == "accounting":
        # Example: run accounting agent
        print("Running accounting agent...")
        # Add specific accounting agent logic here
    elif agent_type == "orchestrator":
        run_orchestrator()
    else:
        print(f"Unknown agent type: {agent_type}")
        return


def show_help():
    """Show help information."""
    print("""
🏆 Gold Tier AI Employee System
==============================

Usage:
  python -m src.ai_employee_gold.main [options]

Options:
  --agent TYPE     Run a specific agent (orchestrator, odoo, social, accounting)
  --init          Initialize the system
  --help          Show this help message

Examples:
  python -m src.ai_employee_gold.main --init
  python -m src.ai_employee_gold.main --agent orchestrator
  python -m src.ai_employee_gold.main --agent social
    """)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Gold Tier AI Employee System')
    parser.add_argument('--agent', choices=['orchestrator', 'odoo', 'social', 'accounting'],
                       help='Run a specific agent')
    parser.add_argument('--init', action='store_true', help='Initialize the system')
    parser.add_argument('--help', action='store_true', help='Show help')

    args = parser.parse_args()

    setup_logging()

    if args.help:
        show_help()
        return

    if args.init:
        initialize_system()
        return

    if args.agent:
        run_agent(args.agent)
        return

    # Default: show help
    show_help()


if __name__ == "__main__":
    main()