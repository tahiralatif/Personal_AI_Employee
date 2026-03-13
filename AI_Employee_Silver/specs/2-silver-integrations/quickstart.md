# Silver Tier Quickstart Guide

## Overview
This guide provides a quick path to get the Silver Tier AI Employee system up and running with all enhanced features including multiple watchers, MCP servers, and advanced workflows.

## Prerequisites

### System Requirements
- **OS**: Windows 10+, macOS 10.15+, or Linux (Ubuntu 20.04+)
- **Python**: 3.12+
- **Node.js**: v18+ LTS
- **Disk Space**: 5GB available
- **RAM**: 8GB recommended

### Software Dependencies
```bash
# Python package manager
pip install uv

# For MCP servers
npm install -g @modelcontextprotocol/cli

# For web automation
pip install playwright
playwright install chromium
```

### External Services (for integrations)
- **Google Account** with Gmail API enabled
- **WhatsApp Business Account** (for automation, respecting ToS)
- **LinkedIn Account** (for automation, respecting ToS)

## Installation

### 1. Clone and Setup Environment
```bash
# Navigate to your project directory
cd AI_Employee_Bronze

# Install Python dependencies
uv sync

# Activate virtual environment
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

### 2. Configure Environment Variables
```bash
# Copy the example environment file
cp .env.example .env

# Edit the .env file with your credentials
nano .env
```

**Essential environment variables for Silver Tier:**
```bash
# Gmail API credentials
GMAIL_CLIENT_ID=your_client_id
GMAIL_CLIENT_SECRET=your_client_secret
GMAIL_REFRESH_TOKEN=your_refresh_token

# LinkedIn credentials (if using LinkedIn integration)
LINKEDIN_EMAIL=your_email
LINKEDIN_PASSWORD=your_password

# WhatsApp session path
WHATSAPP_SESSION_PATH=./whatsapp_session.json

# MCP server configurations
QWEN_API_URL=http://localhost:1234
```

### 3. Initialize the Enhanced Vault
```bash
# Initialize the complete vault structure (includes Silver tier additions)
python main.py setup
```

## Configuration

### 1. Configure Watchers
Edit your `.env` file to enable/disable specific watchers:

```bash
# Enable watchers
ENABLE_GMAIL_WATCHER=true
ENABLE_WHATSAPP_WATCHER=true
ENABLE_LINKEDIN_WATCHER=true
ENABLE_FILE_WATCHER=true

# Set check intervals (in seconds)
GMAIL_CHECK_INTERVAL=120
WHATSAPP_CHECK_INTERVAL=30
LINKEDIN_CHECK_INTERVAL=300
FILE_CHECK_INTERVAL=10
```

### 2. Configure MCP Servers
Create or update your MCP configuration file at `~/.config/claude-code/mcp.json`:

```json
{
  "servers": [
    {
      "name": "email",
      "command": "node",
      "args": ["src/ai_employee/mcp/email_mcp_server.js"],
      "env": {
        "GMAIL_CREDENTIALS": "./path/to/credentials.json"
      }
    },
    {
      "name": "browser",
      "command": "node",
      "args": ["src/ai_employee/mcp/browser_mcp_server.js"],
      "env": {
        "HEADLESS": "true"
      }
    },
    {
      "name": "linkedin",
      "command": "node",
      "args": ["src/ai_employee/mcp/linkedin_mcp_server.js"],
      "env": {
        "LINKEDIN_EMAIL": "your_email",
        "LINKEDIN_PASSWORD": "your_password"
      }
    },
    {
      "name": "filesystem",
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "~/AI_Employee_Vault"]
    }
  ]
}
```

## Quick Start Commands

### 1. Start Individual Components

#### Start the File Watcher Only
```bash
python main.py watch
```

#### Process Tasks with Qwen AI
```bash
python main.py process
```

#### Run Ralph Wiggum Loop (Persistent Processing)
```bash
python main.py ralph
```

#### Run Single Orchestration Cycle
```bash
python main.py orchestrate
```

#### Run Continuous Orchestration
```bash
python main.py run
```

### 2. Start Complete Silver Tier System

#### Terminal 1: Start MCP Servers
```bash
# Navigate to MCP server directories and start them
cd src/ai_employee/mcp/
node email_mcp_server.js &
node browser_mcp_server.js &
node linkedin_mcp_server.js &
```

#### Terminal 2: Start the Orchestrator
```bash
# Run the complete system with all watchers and processing
python main.py run
```

## Verification Steps

### 1. Check Vault Structure
Verify all Silver Tier folders exist:
```bash
ls -la ~/AI_Employee_Vault/
# Should show: Inbox/, Needs_Action/, In_Progress/, Plans/, Pending_Approval/,
# Approved/, Rejected/, Done/, Logs/, Quarantine/, Briefings/, Dashboard.md, Company_Handbook.md
```

### 2. Test File Watcher
```bash
# Create a test file in Inbox
echo "Test task" > ~/AI_Employee_Vault/Inbox/test.txt

# Check if action file was created
ls ~/AI_Employee_Vault/Needs_Action/
# Should show a FILE_* action file
```

### 3. Check Dashboard Status
```bash
cat ~/AI_Employee_Vault/Dashboard.md
# Should show system status and task counts
```

## Silver Tier Features Walkthrough

### 1. Enhanced Watchers

#### Gmail Watcher
- Monitors Gmail for new important emails
- Creates action files in `Needs_Action/Gmail/`
- Respects API quotas and rate limits

#### WhatsApp Watcher
- Monitors WhatsApp for urgent messages
- Detects keywords ('urgent', 'asap', 'invoice', 'payment', 'help')
- Creates action files in `Needs_Action/WhatsApp/`

#### LinkedIn Watcher
- Monitors LinkedIn for connection requests and messages
- Creates action files in `Needs_Action/LinkedIn/`
- Respects LinkedIn's Terms of Service

### 2. MCP Server Integration

#### Email MCP Server
- Send emails via Gmail API
- Create email drafts
- Search and read emails

#### Browser MCP Server
- Navigate to web pages
- Click elements and buttons
- Fill forms and input fields
- Take screenshots

#### LinkedIn MCP Server
- Post updates to LinkedIn
- Send connection requests
- Like and comment on posts
- Send messages to connections

### 3. Plan Generation
- AI creates structured plans in `Plans/` folder
- Plans include step-by-step execution instructions
- Plans specify approval requirements

### 4. Enhanced Approval Workflow
- Multiple approval categories (financial, communication, data, system)
- Risk assessment for each action
- Auto-reject for expired requests

## Troubleshooting

### Common Issues

#### Issue: Watchers not detecting files
**Solution**:
```bash
# Check if watcher is running
python main.py watch

# Verify watched folder path in .env
echo $WATCHED_FOLDER
```

#### Issue: MCP servers not connecting
**Solution**:
```bash
# Check if MCP servers are running
ps aux | grep mcp

# Verify MCP configuration file exists and is valid
cat ~/.config/claude-code/mcp.json
```

#### Issue: Gmail API errors
**Solution**:
```bash
# Verify credentials in .env
# Regenerate refresh token if needed
# Check API quota limits
```

#### Issue: Playwright/WhatsApp errors
**Solution**:
```bash
# Reinstall browsers
playwright install chromium

# Clear session data if needed
rm ./whatsapp_session.json
```

## Next Steps

### 1. Customize Company Handbook
Review and customize `~/AI_Employee_Vault/Company_Handbook.md` with your specific rules and guidelines.

### 2. Set Up Scheduling
Configure cron jobs or Task Scheduler for automated tasks:
```bash
# Example cron job for daily processing
0 9 * * * cd /path/to/AI_Employee_Bronze && python main.py process
```

### 3. Monitor and Adjust
- Regularly check the dashboard for system status
- Review logs in `~/AI_Employee_Vault/Logs/`
- Adjust approval thresholds as needed

## Demo Scenario
Try this complete workflow to test all Silver Tier features:

1. Place a file in `~/AI_Employee_Vault/Inbox/`
2. Watch it create an action file in `Needs_Action/`
3. Observe the AI process it and potentially create a plan in `Plans/`
4. If approval is needed, see the request in `Pending_Approval/`
5. Move to `Approved/` to execute
6. See the result in `Done/` and dashboard updates

Your Silver Tier AI Employee system is now ready for advanced automation tasks!