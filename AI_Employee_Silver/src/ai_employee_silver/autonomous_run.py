"""
AI Employee - Fully Autonomous Mode

ALL agents run automatically in background with ONE command.
No manual intervention needed.

Features:
- All agents start simultaneously
- Run 24/7 in background
- Automatic monitoring
- Automatic task detection
- Automatic approval requests
- Human-in-the-loop for approvals only

Usage:
    python -m src.ai_employee_silver.autonomous_run
"""

import asyncio
import sys
import os
from pathlib import Path
from datetime import datetime
import threading
from dotenv import load_dotenv

load_dotenv()

from agents import Agent, Runner, RunConfig, OpenAIChatCompletionsModel, AsyncOpenAI

# Import all tools
from tools.gmail_tools import read_emails, save_attachment_to_inbox, create_email_action_file
from tools.whatsapp_tools import monitor_whatsapp_messages, detect_task_keywords, create_whatsapp_task_file, send_whatsapp_message
from tools.linkedin_tools import read_scheduled_posts, publish_linkedin_post
from tools.approval_tools import request_approval, list_pending_approvals


class AutonomousAgent:
    """Base class for autonomous agents that run continuously."""
    
    def __init__(self, name: str, instructions: str, tools: list, check_interval: int = 60):
        self.name = name
        self.instructions = instructions
        self.tools = tools
        self.check_interval = check_interval  # seconds
        self.running = False
        
        # Get Gemini configuration
        self.gemini_api_key = os.getenv("GEMINI_API_KEY")
        self.model_name = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
        
        if not self.gemini_api_key:
            raise ValueError("GEMINI_API_KEY not found in .env")
        
        # Initialize client
        self.external_client = AsyncOpenAI(
            api_key=self.gemini_api_key,
            base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
        )
        
        self.model = OpenAIChatCompletionsModel(
            model=self.model_name,
            openai_client=self.external_client
        )
        
        self.config = RunConfig(
            model=self.model,
            model_provider=self.external_client,
            tracing_disabled=True
        )
    
    async def run_autonomous_loop(self):
        """Run agent autonomously in continuous loop."""
        self.running = True
        
        print(f"\n✅ {self.name} started (checking every {self.check_interval}s)")
        
        while self.running:
            try:
                # Create agent instance
                agent = Agent(
                    name=self.name,
                    instructions=self.instructions,
                    tools=self.tools
                )
                
                # Run autonomous check
                result = await Runner.run(
                    starting_agent=agent,
                    input=f"Autonomous check - perform your duties and report status"
                )
                
                # Print status
                timestamp = datetime.now().strftime("%H:%M:%S")
                print(f"[{timestamp}] {self.name}: {result.final_output[:200]}...")
                
                # Wait for next check
                await asyncio.sleep(self.check_interval)
                
            except Exception as e:
                print(f"❌ {self.name} error: {str(e)}")
                await asyncio.sleep(self.check_interval)
    
    def stop(self):
        """Stop the agent."""
        self.running = False
        print(f"\n⏹️  {self.name} stopped")


class GmailAutonomousAgent(AutonomousAgent):
    """Autonomous Gmail Agent - runs continuously."""
    
    def __init__(self):
        super().__init__(
            name="📧 Gmail Agent",
            instructions="""You are an autonomous Gmail monitoring agent.

AUTONOMOUS DUTIES:
1. Check for new unread emails every 60 seconds
2. Look for emails with attachments
3. Save attachments to Inbox folder
4. Create action files for emails with tasks
5. Request human approval before processing

WORKFLOW:
1. Use read_emails(query="is:unread has:attachment") to check for new emails
2. For each email found:
   - Save attachments with save_attachment_to_inbox
   - Create action file with create_email_action_file
   - Request approval with request_approval
3. Report summary of actions taken

Be autonomous - don't wait for user input. Just do your duties.
""",
            tools=[read_emails, save_attachment_to_inbox, create_email_action_file, request_approval],
            check_interval=60  # Check every 60 seconds
        )


class WhatsAppAutonomousAgent(AutonomousAgent):
    """Autonomous WhatsApp Agent - runs continuously."""
    
    def __init__(self):
        super().__init__(
            name="💬 WhatsApp Agent",
            instructions="""You are an autonomous WhatsApp monitoring agent.

AUTONOMOUS DUTIES:
1. Check for new WhatsApp messages every 30 seconds
2. Detect task keywords in messages (English & Urdu)
3. Create action files for detected tasks
4. Send approval requests to human

WORKFLOW:
1. Use monitor_whatsapp_messages(limit=10) to check for new messages
2. For each message:
   - Analyze with detect_task_keywords
   - If task detected: create_whatsapp_task_file + request_approval
   - If no task: ignore
3. Report summary of actions taken

TASK KEYWORDS:
- English: please, need, urgent, task, action, required, must, should
- Urdu: meharbani, zaroori, kaam, chahiye, bhejo, taiyar

Be autonomous - don't wait for user input. Just do your duties.
""",
            tools=[monitor_whatsapp_messages, detect_task_keywords, create_whatsapp_task_file, request_approval],
            check_interval=30  # Check every 30 seconds
        )


class LinkedInAutonomousAgent(AutonomousAgent):
    """Autonomous LinkedIn Agent - runs continuously."""
    
    def __init__(self):
        super().__init__(
            name="💼 LinkedIn Agent",
            instructions="""You are an autonomous LinkedIn posting agent.

AUTONOMOUS DUTIES:
1. Check for scheduled posts every 120 seconds
2. Publish posts when scheduled time arrives
3. Track engagement metrics
4. Request approval before publishing

WORKFLOW:
1. Use read_scheduled_posts() to check for posts ready to publish
2. For each post ready:
   - Request approval with request_approval
   - If approved: publish with publish_linkedin_post
   - Move to Done folder
3. Report summary of actions taken

Be autonomous - don't wait for user input. Just do your duties.
""",
            tools=[read_scheduled_posts, publish_linkedin_post, request_approval],
            check_interval=120  # Check every 2 minutes
        )


async def run_autonomous_system():
    """Run ALL agents autonomously in parallel."""
    
    print("\n" + "="*70)
    print("🤖 AI EMPLOYEE - AUTONOMOUS MODE")
    print("="*70)
    print("\nStarting ALL agents in autonomous mode...")
    print("All agents will run continuously in background.")
    print("You'll see status updates every check interval.")
    print("\nPress Ctrl+C to stop all agents.")
    print("="*70 + "\n")
    
    # Check Gemini API key
    if not os.getenv("GEMINI_API_KEY"):
        print("❌ Error: GEMINI_API_KEY not found in .env")
        print("\nPlease:")
        print("1. Get FREE API key: https://aistudio.google.com/apikey")
        print("2. Copy .env.example to .env")
        print("3. Add your API key to .env")
        return
    
    # Create agents
    agents = [
        GmailAutonomousAgent(),
        WhatsAppAutonomousAgent(),
        LinkedInAutonomousAgent()
    ]
    
    # Run all agents in parallel
    tasks = [agent.run_autonomous_loop() for agent in agents]
    
    try:
        await asyncio.gather(*tasks)
    except KeyboardInterrupt:
        print("\n\n⏹️  Stopping all agents...")
        for agent in agents:
            agent.stop()
        print("\n✅ All agents stopped. Goodbye!")


def main():
    """Main entry point for autonomous mode."""
    print("\n🚀 Starting AI Employee Autonomous System...\n")
    
    try:
        asyncio.run(run_autonomous_system())
    except KeyboardInterrupt:
        print("\n\n👋 Autonomous system stopped by user.")
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        print("\nPlease check:")
        print("1. .env file exists with GEMINI_API_KEY")
        print("2. All dependencies are installed")
        print("3. Internet connection is active")


if __name__ == "__main__":
    main()
