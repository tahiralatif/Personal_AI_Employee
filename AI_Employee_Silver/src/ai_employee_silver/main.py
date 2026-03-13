"""
AI Employee Silver Tier - Autonomous AI Agents

Main entry point for running AI Employee agents powered by Gemini.

Usage:
    python -m src.ai_employee_silver.main [agent_name]

Available Agents:
    gmail         - Gmail Agent (email processing)
    whatsapp      - WhatsApp Agent (message monitoring)
    linkedin      - LinkedIn Agent (post management)
    orchestrator  - Main Coordinator (routes to all agents)
    all           - Run all agents (not recommended for interactive use)

Examples:
    python -m src.ai_employee_silver.main gmail
    python -m src.ai_employee_silver.main whatsapp
    python -m src.ai_employee_silver.main linkedin
    python -m src.ai_employee_silver.main orchestrator
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from agents.gmail_agent import run_gmail_agent
from agents.whatsapp_agent import run_whatsapp_agent
from agents.linkedin_agent import run_linkedin_agent
from agents.orchestrator_agent import run_orchestrator


def print_help():
    """Print help information."""
    print("""
🤖 AI Employee - Autonomous AI Agents
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Available Agents:

  📧 gmail         - Gmail Agent
                     • Monitor emails with attachments
                     • Save attachments to Inbox
                     • Create action files
                     • Request approval before processing

  💬 whatsapp      - WhatsApp Agent
                     • Monitor WhatsApp messages
                     • Detect tasks (English & Urdu)
                     • Create action files
                     • Send approval requests

  💼 linkedin      - LinkedIn Agent
                     • Manage scheduled posts
                     • Publish to LinkedIn
                     • Track engagement metrics
                     • Request approval before posting

  🎯 orchestrator  - Orchestrator Agent
                     • Coordinate all agents
                     • Route tasks automatically
                     • System status & reports
                     • Main interface

Usage:
  python -m src.ai_employee_silver.main <agent_name>

Examples:
  python -m src.ai_employee_silver.main gmail
  python -m src.ai_employee_silver.main whatsapp
  python -m src.ai_employee_silver.main linkedin
  python -m src.ai_employee_silver.main orchestrator

Setup:
  1. Get Gemini API key: https://aistudio.google.com/apikey
  2. Copy .env.example to .env
  3. Add your API key to .env
  4. Configure other services (Gmail, WhatsApp, LinkedIn)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
""")


async def main():
    """Main entry point."""
    
    if len(sys.argv) < 2:
        print_help()
        print("❌ Error: No agent specified")
        print("\nUse 'python -m src.ai_employee_silver.main help' for usage information.")
        return
    
    agent_name = sys.argv[1].lower()
    
    if agent_name in ["help", "-h", "--help"]:
        print_help()
        return
    
    if agent_name == "gmail":
        await run_gmail_agent()
    elif agent_name == "whatsapp":
        await run_whatsapp_agent()
    elif agent_name == "linkedin":
        await run_linkedin_agent()
    elif agent_name == "orchestrator":
        await run_orchestrator()
    elif agent_name == "all":
        print("⚠️  Running all agents simultaneously is not recommended for interactive use.")
        print("   Please run agents individually in separate terminal windows.")
        print("\n   Recommended:")
        print("   - Terminal 1: python -m src.ai_employee_silver.main gmail")
        print("   - Terminal 2: python -m src.ai_employee_silver.main whatsapp")
        print("   - Terminal 3: python -m src.ai_employee_silver.main linkedin")
        print("   - Terminal 4: python -m src.ai_employee_silver.main orchestrator")
    else:
        print(f"❌ Unknown agent: {agent_name}")
        print("\nUse 'python -m src.ai_employee_silver.main help' for usage information.")


if __name__ == "__main__":
    asyncio.run(main())
