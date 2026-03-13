# 🤖 CLAUDE.MD - PERSONAL AI EMPLOYEE CONFIGURATION

**Project**: Personal AI Employee - Autonomous FTE (Full-Time Equivalent)
**Version**: 0.2.0
**Last Updated**: 2026-03-07
**Status**: Building Autonomous Agents with Local-First Architecture
**Tagline**: *Your life and business on autopilot. Local-first, agent-driven, human-in-the-loop.*

---

## 🎯 PROJECT GOAL

Build a **100% autonomous AI employee system** that:
- ✅ Monitors Gmail, WhatsApp, LinkedIn, Bank Accounts automatically
- ✅ Processes tasks using autonomous reasoning (Claude Code OR Qwen)
- ✅ Requests human approval before sensitive actions (HITL)
- ✅ Maintains Obsidian vault as brain & dashboard
- ✅ Runs 24/7 in background with watchers + Ralph Wiggum loop
- ✅ Supports English & Urdu languages
- ✅ Local-first (all data stays on machine)

**Key Difference from Current Implementation**:
- **Current**: OpenAI Agents SDK + Gemini API (Python agents)
- **New Goal**: Claude Code/Qwen as Brain + Python Watchers + MCP Servers/PowerShell CCR

---

## 💡 DIGITAL FTE CONCEPT

A **Digital FTE (Full-Time Equivalent)** is an AI agent that is built, "hired," and priced as if it were a human employee. This shifts the conversation from "software licenses" to "headcount budgets."

### **Human FTE vs Digital FTE**

| Feature | Human FTE | Digital FTE (Custom Agent) |
|---------|-----------|---------------------------|
| Availability | 40 hours/week | 168 hours/week (24/7) |
| Monthly Cost | $4,000 – $8,000+ | $500 – $2,000 |
| Ramp-up Time | 3 – 6 Months | Instant (via SKILL.md) |
| Consistency | Variable (85–95% accuracy) | Predictable (99%+ consistency) |
| Scaling | Linear (Hire 10 for 10x work) | Exponential (Instant duplication) |
| Cost per Task | ~$3.00 – $6.00 | ~$0.25 – $0.50 |
| Annual Hours | ~2,000 hours | ~8,760 hours |

> **The 'Aha!' Moment**: A Digital FTE works nearly 9,000 hours a year vs a human's 2,000. The cost per task reduction (from ~$5.00 to ~$0.50) is an 85–90% cost saving—usually the threshold where a CEO approves a project without further debate.

---

## 📋 PREREQUISITES & SETUP

### **Required Software**

| Component | Requirement | Purpose |
|-----------|-------------|---------|
| [Claude Code](https://claude.com/product/claude-code) | Active subscription (Pro or Use Free Gemini API with Claude Code Router) | Primary reasoning engine |
| [Obsidian](https://obsidian.md/download) | v1.10.6+ (free) | Knowledge base & dashboard |
| [Python](https://www.python.org/downloads/) | 3.13 or higher | Sentinel scripts & orchestration |
| [Node.js](http://Node.js) | v24+ LTS | MCP servers & automation |
| [Github Desktop](https://desktop.github.com/download/) | Latest stable | Version control for your vault |

### **Hardware Requirements**

- **Minimum**: 8GB RAM, 4-core CPU, 20GB free disk space
- **Recommended**: 16GB RAM, 8-core CPU, SSD storage
- **For always-on operation**: Consider a dedicated mini-PC or cloud VM
- **Internet**: Stable connection for API calls (10+ Mbps recommended)

### **Skill Level Expectations**

This hackathon assumes intermediate technical proficiency:

- ✅ Comfortable with command-line interfaces (terminal/bash)
- ✅ Understanding of file systems and folder structures
- ✅ Familiarity with APIs (what they are, how to call them)
- ✅ No prior AI/ML experience required
- ✅ Able to use and prompt Claude Code
- ✅ Prompt Claude Code to convert AI functionality into [Agent Skills](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview)

### **Pre-Hackathon Checklist**

1. [ ] Install all required software listed above
2. [ ] Create a new Obsidian vault named "AI_Employee_Vault"
3. [ ] Verify Claude Code works by running: `claude --version`
4. [ ] Set up a UV Python project
5. [ ] Join the Wednesday Research Meeting Zoom link

---

## 🏗️ ARCHITECTURE OVERVIEW

### **Core Architecture: Perception → Reasoning → Action**

```
┌─────────────────────────────────────────────────────────────┐
│         PERSONAL AI EMPLOYEE - AUTONOMOUS FTE              │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  EXTERNAL SOURCES                                           │
│  Gmail │ WhatsApp │ LinkedIn │ Bank APIs │ File System     │
│    ↓         ↓           ↓          ↓            ↓          │
│  PERCEPTION LAYER (Python Watchers)                        │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐      │
│  │  Gmail   │ │ WhatsApp │ │ LinkedIn │ │ Finance  │      │
│  │ Watcher  │ │ Watcher  │ │ Watcher  │ │ Watcher  │      │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘      │
│       ↓            ↓            ↓            ↓              │
│  OBSIDIAN VAULT (Memory/GUI)                                │
│  /Inbox/ /Needs_Action/ /Plans/ /Done/ /Logs/              │
│  Dashboard.md │ Company_Handbook.md │ Business_Goals.md    │
│       ↓                                                     │
│  REASONING LAYER (Brain)                                    │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  CLAUDE CODE  OR  QWEN (Terminal/PowerShell CCR)    │   │
│  │  Read → Think → Plan → Write → Request Approval     │   │
│  └─────────────────────────────────────────────────────┘   │
│       ↓                                                     │
│  HUMAN-IN-THE-LOOP (Approval Required)                     │
│  /Pending_Approval/ → Human Reviews → /Approved/           │
│       ↓                                                     │
│  ACTION LAYER (Hands)                                       │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐      │
│  │   MCP    │ │ PowerShell│ │ Playwright│ │  Custom  │     │
│  │  Servers │ │   CCR    │ │  (Backup) │ │  Scripts │     │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘      │
│       ↓            ↓            ↓            ↓              │
│  EXTERNAL ACTIONS: Send Email, Post Social, Payments      │
│                                                             │
│  ORCHESTRATION: orchestrator.py + watchdog.py             │
│  RALPH WIGGUM LOOP: Keep working until task complete      │
└─────────────────────────────────────────────────────────────┘
```

### **The Foundational Layer (Local Engine)**

| Component | Role | Description |
|-----------|------|-------------|
| **Obsidian (Nerve Center)** | GUI + Long-Term Memory | `Dashboard.md` for real-time summary, `Company_Handbook.md` for rules |
| **Claude Code (Muscle)** | Reasoning Engine | Uses File System tools, Ralph Wiggum loop for persistence |
| **Python Watchers (Senses)** | Perception Layer | Monitor Gmail, WhatsApp, files; create action files |
| **MCP Servers (Hands)** | Action Layer | Send emails, click buttons, interact with websites |

### **Operation Modes**

| Operation Type | Example Task | Local Trigger |
|----------------|--------------|---------------|
| **Scheduled** | Daily Briefing at 8:00 AM | cron (Mac/Linux) or Task Scheduler (Win) |
| **Continuous** | Lead Capture from WhatsApp | Python watchdog monitoring /Inbox |
| **Project-Based** | Q1 Tax Prep | Manual drag-and-drop to /Active_Project |

---

## 📁 VAULT STRUCTURE

```
AI_Employee_Vault/
├── Inbox/                      # Raw incoming items
├── Needs_Action/               # Items requiring processing
│   ├── Gmail/
│   ├── WhatsApp/
│   ├── LinkedIn/
│   └── Finance/
├── In_Progress/                # Currently being worked on
│   └── <agent_name>/           # Claim-by-move rule
├── Plans/                      # Action plans created by AI
├── Pending_Approval/           # Awaiting human approval
├── Approved/                   # Approved for execution
├── Rejected/                   # Rejected by human
├── Done/                       # Completed tasks
│   ├── Gmail/
│   ├── WhatsApp/
│   ├── LinkedIn/
│   └── Finance/
├── Logs/                       # Audit logs (JSON, daily)
├── Updates/                    # Cloud agent updates (Platinum)
├── Signals/                    # Cross-agent signals (Platinum)
├── Dashboard.md                # Real-time summary
├── Company_Handbook.md         # Rules of engagement
├── Business_Goals.md           # Q1/Q2 objectives & metrics
└── Briefings/                  # CEO Briefings (weekly)
```

### **Claim-by-Move Rule (Platinum Tier)**

- First agent to move an item from `/Needs_Action` to `/In_Progress/<agent>/` owns it
- Other agents must ignore items in `/In_Progress/<other_agent>/`
- Single-writer rule for `Dashboard.md` (Local only)
- Cloud writes to `/Updates/` or `/Signals/`, Local merges into `Dashboard.md`

---

## 🏛️ COMPLETE SYSTEM ARCHITECTURE

```
┌─────────────────────────────────────────────────────────────────┐
│                    PERSONAL AI EMPLOYEE                         │
│                      SYSTEM ARCHITECTURE                        │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                      EXTERNAL SOURCES                           │
├─────────────────┬─────────────────┬─────────────────────────────┤
│     Gmail       │    WhatsApp     │     Bank APIs    │  Files   │
└────────┬────────┴────────┬────────┴─────────┬────────┴────┬─────┘
         │                 │                  │             │
         ▼                 ▼                  ▼             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    PERCEPTION LAYER                             │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐             │
│  │ Gmail Watcher│ │WhatsApp Watch│ │Finance Watcher│            │
│  │  (Python)    │ │ (Playwright) │ │   (Python)   │            │
│  └──────┬───────┘ └──────┬───────┘ └──────┬───────┘            │
└─────────┼────────────────┼────────────────┼────────────────────┘
          │                │                │
          ▼                ▼                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    OBSIDIAN VAULT (Local)                       │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ /Needs_Action/  │ /Plans/  │ /Done/  │ /Logs/            │  │
│  ├──────────────────────────────────────────────────────────┤  │
│  │ Dashboard.md    │ Company_Handbook.md │ Business_Goals.md│  │
│  ├──────────────────────────────────────────────────────────┤  │
│  │ /Pending_Approval/  │  /Approved/  │  /Rejected/         │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────────────┬────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                    REASONING LAYER                              │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │                      CLAUDE CODE                          │ │
│  │   Read → Think → Plan → Write → Request Approval          │ │
│  └───────────────────────────────────────────────────────────┘ │
└────────────────────────────────┬────────────────────────────────┘
                                 │
              ┌──────────────────┴───────────────────┐
              ▼                                      ▼
┌────────────────────────────┐    ┌────────────────────────────────┐
│    HUMAN-IN-THE-LOOP       │    │         ACTION LAYER           │
│  ┌──────────────────────┐  │    │  ┌─────────────────────────┐   │
│  │ Review Approval Files│──┼───▶│  │    MCP SERVERS          │   │
│  │ Move to /Approved    │  │    │  │  ┌──────┐ ┌──────────┐  │   │
│  └──────────────────────┘  │    │  │  │Email │ │ Browser  │  │   │
│                            │    │  │  │ MCP  │ │   MCP    │  │   │
└────────────────────────────┘    │  │  └──┬───┘ └────┬─────┘  │   │
                                  │  └─────┼──────────┼────────┘   │
                                  └────────┼──────────┼────────────┘
                                           │          │
                                           ▼          ▼
                                  ┌────────────────────────────────┐
                                  │     EXTERNAL ACTIONS           │
                                  │  Send Email │ Make Payment     │
                                  │  Post Social│ Update Calendar  │
                                  └────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                    ORCHESTRATION LAYER                          │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │              Orchestrator.py (Master Process)             │ │
│  │   Scheduling │ Folder Watching │ Process Management       │ │
│  └───────────────────────────────────────────────────────────┘ │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │              Watchdog.py (Health Monitor)                 │ │
│  │   Restart Failed Processes │ Alert on Errors              │ │
│  └───────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🥉 TIER SYSTEM & DELIVERABLES

### **Bronze Tier: Foundation (8-12 hours)**

- [ ] Obsidian vault with `Dashboard.md` and `Company_Handbook.md`
- [ ] One working Watcher script (Gmail OR file system monitoring)
- [ ] Claude Code successfully reading from and writing to the vault
- [ ] Basic folder structure: `/Inbox`, `/Needs_Action`, `/Done`
- [ ] All AI functionality implemented as [Agent Skills](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview)

### **Silver Tier: Functional Assistant (20-30 hours)**

- [ ] All Bronze requirements plus:
- [ ] Two or more Watcher scripts (Gmail + WhatsApp + LinkedIn)
- [ ] Automatically post on LinkedIn about business to generate sales
- [ ] Claude reasoning loop that creates `Plan.md` files
- [ ] One working MCP server for external action (e.g., sending emails)
- [ ] Human-in-the-loop approval workflow for sensitive actions
- [ ] Basic scheduling via cron or Task Scheduler
- [ ] All AI functionality implemented as [Agent Skills](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview)

### **Gold Tier: Autonomous Employee (40+ hours)**

- [ ] All Silver requirements plus:
- [ ] Full cross-domain integration (Personal + Business)
- [ ] Create accounting system in Odoo Community (self-hosted, local)
- [ ] Integrate Odoo via [MCP server](https://github.com/AlanOgic/mcp-odoo-adv) using JSON-RPC APIs (Odoo 19+)
- [ ] Integrate Facebook and Instagram (post messages + summary)
- [ ] Integrate Twitter (X) (post messages + summary)
- [ ] Multiple MCP servers for different action types
- [ ] Weekly Business and Accounting Audit with CEO Briefing generation
- [ ] Error recovery and graceful degradation
- [ ] Comprehensive audit logging
- [ ] Ralph Wiggum loop for autonomous multi-step task completion
- [ ] Documentation of architecture and lessons learned
- [ ] All AI functionality implemented as [Agent Skills](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview)

### **Platinum Tier: Always-On Cloud + Local Executive (60+ hours)**

- [ ] All Gold requirements plus:
- [ ] **Run AI Employee on Cloud 24/7** (Oracle/AWS VM with health monitoring)
- [ ] **Work-Zone Specialization**:
  - **Cloud owns**: Email triage + draft replies + social post drafts (draft-only)
  - **Local owns**: approvals, WhatsApp session, payments/banking, final "send/post"
- [ ] **Delegation via Synced Vault**:
  - Agents communicate by writing files to `/Needs_Action/<domain>/`, `/Plans/<domain>/`, `/Pending_Approval/<domain>/`
  - Prevent double-work using claim-by-move rule
  - Cloud writes to `/Updates/` or `/Signals/`, Local merges to `Dashboard.md`
  - Vault sync via Git (recommended) or Syncthing
- [ ] **Security rule**: Vault sync includes only markdown/state. Secrets never sync (.env, tokens, WhatsApp sessions, banking creds)
- [ ] **Deploy Odoo Community on Cloud VM (24/7)** with HTTPS, backups, health monitoring
- [ ] **Optional A2A Upgrade (Phase 2)**: Replace some file handoffs with direct A2A messages
- [ ] **Platinum demo (minimum passing gate)**: Email arrives while Local offline → Cloud drafts reply + writes approval file → Local returns, user approves → Local executes send via MCP → logs → moves to `/Done`

---

## 🧠 BRAIN OPTIONS

### **Option 1: Claude Code (Primary)**

```bash
# Interactive mode with Ralph Wiggum loop
claude --cwd "D:\...\AI_Employee_Vault"

# Process Needs_Action folder
claude "Check /Needs_Action and /Plans folders. Process all pending items. Create action files in /Pending_Approval for sensitive actions."

# Ralph Wiggum pattern (keep working until complete)
/ralph-loop "Process all files in /Needs_Action, move to /Done when complete" \
  --completion-promise "TASK_COMPLETE" \
  --max-iterations 10
```

### **Option 2: Qwen (Alternative)**

```bash
# Run Qwen via terminal (similar pattern)
qwen --cwd "D:\...\AI_Employee_Vault" \
     --prompt "Check /Needs_Action and /Plans folders. Process all pending items."

# PowerShell CCR integration
$task = "Process WhatsApp messages and create action files"
Invoke-Qwen -Task $task -VaultPath "D:\...\AI_Employee_Vault"
```

### **Option 3: PowerShell CCR Code**

```powershell
# CCR (Claude Code Router) pattern
function Invoke-AITask {
    param(
        [string]$Task,
        [string]$VaultPath
    )
    
    # Check if task complete
    $taskFile = Get-ChildItem "D:\...\AI_Employee_Vault\Needs_Action"
    
    if ($taskFile.Count -eq 0) {
        Write-Host "All tasks complete"
        return
    }
    
    # Run AI reasoning
    claude --cwd $VaultPath --prompt $Task
    
    # Ralph Wiggum loop: re-inject if not complete
    while ($taskFile.Count -gt 0) {
        claude --cwd $VaultPath --prompt "Continue working. Move completed tasks to /Done"
        Start-Sleep -Seconds 5
    }
}
```

---

## 👁️ WATCHERS (PERCEPTION LAYER)

### **Watcher Pattern Template**

```python
# base_watcher.py
import time
import logging
from pathlib import Path
from abc import ABC, abstractmethod

class BaseWatcher(ABC):
    def __init__(self, vault_path: str, check_interval: int = 60):
        self.vault_path = Path(vault_path)
        self.needs_action = self.vault_path / 'Needs_Action'
        self.check_interval = check_interval
        self.logger = logging.getLogger(self.__class__.__name__)
        self.processed_ids = set()

    @abstractmethod
    def check_for_updates(self) -> list:
        '''Return list of new items to process'''
        pass

    @abstractmethod
    def create_action_file(self, item) -> Path:
        '''Create .md file in Needs_Action folder'''
        pass

    def run(self):
        self.logger.info(f'Starting {self.__class__.__name__}')
        while True:
            try:
                items = self.check_for_updates()
                for item in items:
                    if item['id'] not in self.processed_ids:
                        self.create_action_file(item)
                        self.processed_ids.add(item['id'])
            except Exception as e:
                self.logger.error(f'Error: {e}')
                time.sleep(5)  # Backoff on error
            time.sleep(self.check_interval)
```

### **Gmail Watcher**

```python
# gmail_watcher.py
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from base_watcher import BaseWatcher
from datetime import datetime

class GmailWatcher(BaseWatcher):
    def __init__(self, vault_path: str, credentials_path: str):
        super().__init__(vault_path, check_interval=120)
        self.creds = Credentials.from_authorized_user_file(credentials_path)
        self.service = build('gmail', 'v1', credentials=self.creds)

    def check_for_updates(self) -> list:
        results = self.service.users().messages().list(
            userId='me', q='is:unread is:important'
        ).execute()
        messages = results.get('messages', [])
        return [{'id': m['id'], 'type': 'email'} for m in messages]

    def create_action_file(self, message) -> Path:
        msg = self.service.users().messages().get(
            userId='me', id=message['id']
        ).execute()
        
        headers = {h['name']: h['value'] for h in msg['payload']['headers']}
        
        content = f'''---
type: email
from: {headers.get('From', 'Unknown')}
to: {headers.get('To', '')}
subject: {headers.get('Subject', 'No Subject')}
received: {datetime.now().isoformat()}
priority: high
status: pending
---

## Email Content
{msg.get('snippet', '')}

## Suggested Actions
- [ ] Reply to sender
- [ ] Forward to relevant party
- [ ] Archive after processing
'''
        filepath = self.needs_action / f'Gmail/EMAIL_{message["id"]}.md'
        filepath.parent.mkdir(exist_ok=True)
        filepath.write_text(content)
        
        # Mark as read
        self.service.users().messages().modify(
            userId='me', id=message['id'], body={'removeLabelIds': ['UNREAD']}
        ).execute()
        
        return filepath
```

### **WhatsApp Watcher (Playwright-based)**

```python
# whatsapp_watcher.py
from playwright.sync_api import sync_playwright
from base_watcher import BaseWatcher
from pathlib import Path
import json

class WhatsAppWatcher(BaseWatcher):
    def __init__(self, vault_path: str, session_path: str):
        super().__init__(vault_path, check_interval=30)
        self.session_path = Path(session_path)
        self.keywords = ['urgent', 'asap', 'invoice', 'payment', 'help', 'task']
        self.urdu_keywords = ['فوری', 'ادھار', 'بل', 'مدد', 'کام']

    def check_for_updates(self) -> list:
        with sync_playwright() as p:
            browser = p.chromium.launch_persistent_context(
                self.session_path, headless=True
            )
            page = browser.pages[0]
            page.goto('https://web.whatsapp.com')
            page.wait_for_selector('[data-testid="chat-list"]')

            # Find unread messages
            unread = page.query_selector_all('[aria-label*="unread"]')
            messages = []
            for chat in unread:
                text = chat.inner_text()
                if any(kw in text.lower() for kw in self.keywords) or \
                   any(kw in text for kw in self.urdu_keywords):
                    messages.append({
                        'id': f'whatsapp_{len(messages)}',
                        'text': text,
                        'chat': chat,
                        'type': 'whatsapp'
                    })
            browser.close()
            return messages

    def create_action_file(self, message) -> Path:
        content = f'''---
type: whatsapp
from: {message['chat']}
received: {datetime.now().isoformat()}
priority: high
status: pending
keywords_detected: true
---

## Message Content
{message['text']}

## Suggested Actions
- [ ] Reply to sender
- [ ] Create task from message
- [ ] Flag for follow-up
'''
        filepath = self.needs_action / f'WhatsApp/WHATSAPP_{message["id"]}.md'
        filepath.parent.mkdir(exist_ok=True)
        filepath.write_text(content)
        return filepath
```

### **File System Watcher**

```python
# filesystem_watcher.py
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from pathlib import Path
import shutil
from datetime import datetime

class DropFolderHandler(FileSystemEventHandler):
    def __init__(self, vault_path: str):
        self.vault_path = Path(vault_path)
        self.needs_action = self.vault_path / 'Needs_Action'

    def on_created(self, event):
        if event.is_directory:
            return
        source = Path(event.src_path)
        self.create_action_file(source)

    def create_action_file(self, source: Path) -> Path:
        dest = self.needs_action / f'FileDrop/FILE_{source.name}'
        dest.parent.mkdir(exist_ok=True)
        shutil.copy2(source, dest)
        
        meta_path = dest.with_suffix('.md')
        meta_path.write_text(f'''---
type: file_drop
original_name: {source.name}
size: {source.stat().st_size}
received: {datetime.now().isoformat()}
status: pending
---

New file dropped for processing.

## Suggested Actions
- [ ] Read and categorize file
- [ ] Extract relevant information
- [ ] Create action plan
''')
        return meta_path
```

---

## 🤖 ORCHESTRATION

### **Master Orchestrator**

```python
# orchestrator.py
import subprocess
import time
from pathlib import Path
from datetime import datetime

class Orchestrator:
    def __init__(self, vault_path: str, brain: str = 'claude'):
        self.vault_path = Path(vault_path)
        self.brain = brain
        self.needs_action = self.vault_path / 'Needs_Action'
        self.plans = self.vault_path / 'Plans'
        self.approved = self.vault_path / 'Approved'
        self.done = self.vault_path / 'Done'
        self.logger = self.setup_logger()

    def setup_logger(self):
        log_file = self.vault_path / 'Logs' / f'{datetime.now().strftime("%Y-%m-%d")}.log'
        log_file.parent.mkdir(exist_ok=True)
        # Setup logging...

    def check_needs_action(self) -> list:
        """Check for new items in Needs_Action folder"""
        items = []
        for category in ['Gmail', 'WhatsApp', 'LinkedIn', 'Finance', 'FileDrop']:
            folder = self.needs_action / category
            if folder.exists():
                items.extend(folder.glob('*.md'))
        return items

    def process_item(self, item_path: Path):
        """Process a single item with AI brain"""
        self.logger.info(f'Processing: {item_path.name}')
        
        # Move to In_Progress (claim-by-move rule)
        in_progress = self.vault_path / 'In_Progress' / 'orchestrator'
        in_progress.mkdir(exist_ok=True)
        temp_path = in_progress / item_path.name
        shutil.move(str(item_path), str(temp_path))
        
        # Trigger AI reasoning
        if self.brain == 'claude':
            prompt = f'''Read {temp_path.name} and create a plan.
If action requires approval, create file in /Pending_Approval.
If no approval needed, execute and move to /Done.'''
            
            result = subprocess.run(
                ['claude', '--cwd', str(self.vault_path), '--prompt', prompt],
                capture_output=True, text=True
            )
        
        # Check if plan created
        plan_files = list(self.plans.glob(f'*{item_path.stem}*'))
        if plan_files:
            self.logger.info(f'Plan created: {plan_files[0].name}')

    def check_approved(self) -> list:
        """Check for approved actions ready to execute"""
        return list(self.approved.glob('*.md'))

    def execute_approved(self, approval_path: Path):
        """Execute approved action via MCP or scripts"""
        content = approval_path.read_text()
        # Parse approval file and execute action
        # Move to Done after execution

    def run(self):
        """Main orchestration loop"""
        self.logger.info('Orchestrator started')
        while True:
            try:
                # Process Needs_Action
                items = self.check_needs_action()
                for item in items:
                    self.process_item(item)
                
                # Execute Approved
                approved = self.check_approved()
                for approval in approved:
                    self.execute_approved(approval)
                
            except Exception as e:
                self.logger.error(f'Orchestrator error: {e}')
            
            time.sleep(10)  # Check every 10 seconds
```

### **Watchdog (Health Monitor)**

```python
# watchdog.py
import subprocess
import time
from pathlib import Path

PROCESSES = {
    'orchestrator': 'python orchestrator.py',
    'gmail_watcher': 'python gmail_watcher.py',
    'whatsapp_watcher': 'python whatsapp_watcher.py',
    'file_watcher': 'python filesystem_watcher.py'
}

def is_process_running(pid_file: Path) -> bool:
    if not pid_file.exists():
        return False
    try:
        pid = int(pid_file.read_text())
        # Check if process exists
        import os
        os.kill(pid, 0)
        return True
    except (ValueError, ProcessLookupError, OSError):
        return False

def notify_human(message: str):
    """Send notification to user (WhatsApp, email, etc.)"""
    print(f'NOTIFICATION: {message}')
    # Implement actual notification

def check_and_restart():
    for name, cmd in PROCESSES.items():
        pid_file = Path(f'/tmp/{name}.pid')
        if not is_process_running(pid_file):
            print(f'{name} not running, restarting...')
            proc = subprocess.Popen(
                cmd.split(),
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == 'nt' else 0
            )
            pid_file.write_text(str(proc.pid))
            notify_human(f'{name} was restarted')

if __name__ == '__main__':
    print('Watchdog started')
    while True:
        check_and_restart()
        time.sleep(60)
```

---

## 🔄 RALPH WIGGUM LOOP (PERSISTENCE)

### **Pattern Overview**

The Ralph Wiggum pattern keeps the AI working until the task is complete by intercepting exit attempts.

### **Implementation**

```python
# ralph_loop.py
import subprocess
import sys
from pathlib import Path

def ralph_loop(prompt: str, vault_path: str, max_iterations: int = 10):
    """
    Ralph Wiggum pattern: Keep AI working until task complete
    
    Args:
        prompt: Initial task description
        vault_path: Path to Obsidian vault
        max_iterations: Maximum loop iterations
    """
    vault = Path(vault_path)
    needs_action = vault / 'Needs_Action'
    
    iteration = 0
    while iteration < max_iterations:
        iteration += 1
        print(f' Ralph Loop - Iteration {iteration}/{max_iterations}')
        
        # Run AI
        result = subprocess.run(
            ['claude', '--cwd', vault_path, '--prompt', prompt],
            capture_output=True, text=True
        )
        
        # Check completion
        remaining = list(needs_action.glob('**/*.md'))
        if len(remaining) == 0:
            print(' Task complete! All items processed.')
            return True
        
        # Re-inject prompt with context
        prompt = f'''Continue working. {len(remaining)} items remaining.
Previous output:
{result.stdout[-2000:]}  # Last 2000 chars for context

Move completed items to /Done and continue processing.'''
    
    print(' Max iterations reached. Task may be incomplete.')
    return False
```

### **PowerShell CCR Version**

```powershell
# ralph_loop.ps1
param(
    [string]$Task,
    [string]$VaultPath,
    [int]$MaxIterations = 10
)

$needsAction = Join-Path $VaultPath "Needs_Action"
$iteration = 0

while ($iteration -lt $MaxIterations) {
    $iteration++
    Write-Host " Ralph Loop - Iteration $iteration/$MaxIterations"
    
    # Run AI
    $result = claude --cwd $VaultPath --prompt $Task 2>&1
    
    # Check completion
    $remaining = Get-ChildItem -Path $needsAction -Filter *.md -Recurse
    if ($remaining.Count -eq 0) {
        Write-Host " Task complete!"
        return
    }
    
    # Re-inject with context
    $Task = @"
Continue working. $($remaining.Count) items remaining.
Previous output (last 2000 chars):
$($result | Out-String | Select-Object -Last 50)

Move completed items to /Done and continue processing.
"@
}

Write-Host " Max iterations reached."
```

---

## 🛠️ MCP SERVERS (ACTION LAYER)

### **Email MCP Server**

```javascript
// email-mcp/index.js
const { Server } = require('@modelcontextprotocol/sdk/server');
const { StdioServerTransport } = require('@modelcontextprotocol/sdk/server/stdio');
const { google } = require('googleapis');

const server = new Server({
  name: 'email-mcp',
  version: '1.0.0'
}, {
  capabilities: {
    resources: {},
    tools: {}
  }
});

server.setRequestHandler('tools/call', async (request) => {
  const { name, arguments: args } = request.params;
  
  if (name === 'send_email') {
    return await sendEmail(args);
  } else if (name === 'read_emails') {
    return await readEmails(args);
  }
});

async function sendEmail({ to, subject, body, attachment }) {
  // Implement Gmail send
  const oauth2Client = new google.auth.OAuth2(/* creds */);
  const gmail = google.gmail({ version: 'v1', auth: oauth2Client });
  
  const result = await gmail.users.messages.send({
    userId: 'me',
    requestBody: { /* raw message */ }
  });
  
  return {
    content: [{ type: 'text', text: `Email sent: ${result.data.id}` }]
  };
}

async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
}

main();
```

### **Browser MCP (Playwright)**

```javascript
// browser-mcp/index.js
const { chromium } = require('playwright');

server.setRequestHandler('tools/call', async (request) => {
  const { name, arguments: args } = request.params;
  
  if (name === 'navigate') {
    return await navigate(args.url);
  } else if (name === 'click') {
    return await click(args.selector);
  } else if (name === 'fill') {
    return await fill(args.selector, args.value);
  } else if (name === 'screenshot') {
    return await screenshot();
  }
});

async function navigate(url) {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();
  await page.goto(url);
  // Keep browser alive for subsequent actions
  return { content: [{ type: 'text', text: `Navigated to ${url}` }] };
}
```

### **Claude Code MCP Configuration**

```json
// ~/.config/claude-code/mcp.json
{
  "servers": [
    {
      "name": "email",
      "command": "node",
      "args": ["/path/to/email-mcp/index.js"],
      "env": {
        "GMAIL_CREDENTIALS": "/path/to/credentials.json"
      }
    },
    {
      "name": "browser",
      "command": "npx",
      "args": ["@anthropic/browser-mcp"],
      "env": {
        "HEADLESS": "true"
      }
    },
    {
      "name": "filesystem",
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "/path/to/vault"]
    }
  ]
}
```

---

## ✅ HUMAN-IN-THE-LOOP (HITL)

### **Approval Request Template**

```markdown
---
type: approval_request
action: payment
amount: 500.00
recipient: Client A
reason: Invoice #1234 payment
created: 2026-03-07T10:30:00Z
expires: 2026-03-08T10:30:00Z
status: pending
---

## Payment Details
- **Amount**: $500.00
- **To**: Client A (Bank: XXXX1234)
- **Reference**: Invoice #1234

## To Approve
Move this file to `/Approved` folder.

## To Reject
Move this file to `/Rejected` folder with reason.
```

### **Approval Workflow**

```python
# approval_workflow.py
from pathlib import Path
import shutil

class ApprovalWorkflow:
    def __init__(self, vault_path: Path):
        self.vault = vault_path
        self.pending = vault / 'Pending_Approval'
        self.approved = vault / 'Approved'
        self.rejected = vault / 'Rejected'

    def request_approval(self, action_type: str, details: dict) -> Path:
        """Create approval request file"""
        content = f'''---
type: approval_request
action: {action_type}
created: {datetime.now().isoformat()}
status: pending
---

## Details
'''
        for key, value in details.items():
            content += f'- **{key}**: {value}\n'
        
        content += '''
## To Approve
Move this file to `/Approved` folder.

## To Reject
Move this file to `/Rejected` folder with reason.
'''
        
        filepath = self.pending / f'{action_type.upper()}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.md'
        filepath.write_text(content)
        return filepath

    def check_approvals(self) -> list:
        """Check for approved files"""
        return list(self.approved.glob('*.md'))

    def execute_approved(self, approval_path: Path):
        """Execute approved action"""
        content = approval_path.read_text()
        # Parse and execute
        # Move to Done after execution
        shutil.move(str(approval_path), str(self.vault / 'Done' / approval_path.name))
```

---

## 📊 TEMPLATES

### **Dashboard.md**

```markdown
# 📊 AI Employee Dashboard

**Last Updated**: 2026-03-07 10:30 AM
**Status**: 🟢 Running

## Quick Stats
| Metric | Value |
|--------|-------|
| Pending Items | 3 |
| In Progress | 1 |
| Awaiting Approval | 2 |
| Completed Today | 5 |

## Recent Activity
- [2026-03-07 10:25] Email received from Client A
- [2026-03-07 10:20] WhatsApp message processed
- [2026-03-07 10:15] Invoice sent to Client B ($1,500)

## Pending Approvals
1. Payment to Client A - $500
2. Email reply to Vendor C

## Active Projects
1. Q1 Tax Preparation (Due: Jan 31)
2. Website Redesign (Due: Feb 15)

## Alerts
- ⚠️ Bank balance below $5,000
- ℹ️ 3 emails unread in Gmail

---
*Generated by AI Employee v0.1*
```

### **Company_Handbook.md**

```markdown
# 📖 Company Handbook - Rules of Engagement

**Last Updated**: 2026-03-07

## Communication Rules
1. Always be polite and professional
2. Response time target: < 24 hours
3. Flag urgent messages immediately
4. Never send bulk emails without approval

## Financial Rules
1. Auto-approve payments < $50 to known recipients
2. Always require approval for:
   - New recipients
   - Payments > $100
   - Recurring payments > $50/month
3. Flag transactions > $500 for review

## Social Media Rules
1. Auto-post scheduled content
2. Require approval for:
   - Replies to comments
   - Direct messages
   - Sensitive topics

## Privacy Rules
1. Never share credentials
2. Log all actions
3. Encrypt sensitive data
4. Review logs weekly

## Escalation Rules
1. Unknown sender + large amount = Alert immediately
2. Legal/medical topics = Require human review
3. Emotional content = Flag for human handling
```

### **Business_Goals.md**

```markdown
# 🎯 Business Goals - Q1 2026

**Last Updated**: 2026-03-07
**Review Frequency**: Weekly

## Revenue Targets
| Metric | Target | Current | Status |
|--------|--------|---------|--------|
| Monthly Revenue | $10,000 | $4,500 | 🟡 45% |
| MTD | $4,500 | $4,500 | 🟢 On Track |

## Key Metrics to Track
| Metric | Target | Alert Threshold |
|--------|--------|-----------------|
| Client response time | < 24 hours | > 48 hours |
| Invoice payment rate | > 90% | < 80% |
| Software costs | < $500/month | > $600/month |

## Active Projects
1. **Project Alpha** - Due Jan 15 - Budget $2,000
2. **Project Beta** - Due Jan 30 - Budget $3,500

## Subscription Audit Rules
Flag for review if:
- No login in 30 days
- Cost increased > 20%
- Duplicate functionality with another tool
```

### **CEO Briefing Template**

```markdown
# 📋 Monday Morning CEO Briefing

**Period**: 2026-03-01 to 2026-03-07
**Generated**: 2026-03-07 07:00 AM

## Executive Summary
Strong week with revenue ahead of target. One bottleneck identified.

## Revenue
- **This Week**: $2,450
- **MTD**: $4,500 (45% of $10,000 target)
- **Trend**: 🟢 On track

## Completed Tasks
- [x] Client A invoice sent and paid
- [x] Project Alpha milestone 2 delivered
- [x] Weekly social media posts scheduled

## Bottlenecks
| Task | Expected | Actual | Delay |
|------|----------|--------|-------|
| Client B proposal | 2 days | 5 days | +3 days |

## Proactive Suggestions

### Cost Optimization
- **Notion**: No team activity in 45 days. Cost: $15/month.
  - [ACTION] Cancel subscription? → Moved to /Pending_Approval

### Upcoming Deadlines
- Project Alpha final delivery: Jan 15 (8 days)
- Quarterly tax prep: Jan 31 (25 days)

---
*Generated by AI Employee v0.1*
```

---

## 💼 BUSINESS HANDOVER FEATURE

The **Business Handover** transforms your AI Employee from reactive to proactive. It autonomously audits your business and generates a "Monday Morning CEO Briefing."

### **How It Works**

1. **The Trigger**: Scheduled task runs every Sunday night
2. **The Process**: Claude Code reads `Business_Goals.md`, checks `Tasks/Done` folder, and reviews `Bank_Transactions.md`
3. **The Deliverable**: Writes "Monday Morning CEO Briefing" highlighting:
   - **Revenue**: Total earned this week
   - **Bottlenecks**: Tasks that took too long
   - **Proactive Suggestion**: "I noticed we spent $200 on software we don't use; shall I cancel the subscription?"

### **Business_Goals.md Template**

```markdown
# /Vault/Business_Goals.md
---
last_updated: 2026-01-07
review_frequency: weekly
---

## Q1 2026 Objectives

### Revenue Target
- Monthly goal: $10,000
- Current MTD: $4,500

### Key Metrics to Track
| Metric | Target | Alert Threshold |
|--------|--------|-----------------|
| Client response time | < 24 hours | > 48 hours |
| Invoice payment rate | > 90% | < 80% |
| Software costs | < $500/month | > $600/month |

### Active Projects
1. Project Alpha - Due Jan 15 - Budget $2,000
2. Project Beta - Due Jan 30 - Budget $3,500

### Subscription Audit Rules
Flag for review if:
- No login in 30 days
- Cost increased > 20%
- Duplicate functionality with another tool
```

### **Weekly Audit Logic**

```python
# audit_logic.py
SUBSCRIPTION_PATTERNS = {
    'netflix.com': 'Netflix',
    'spotify.com': 'Spotify',
    'adobe.com': 'Adobe Creative Cloud',
    'notion.so': 'Notion',
    'slack.com': 'Slack',
    # Add your common subscriptions
}

def analyze_transaction(transaction):
    for pattern, name in SUBSCRIPTION_PATTERNS.items():
        if pattern in transaction['description'].lower():
            return {
                'type': 'subscription',
                'name': name,
                'amount': transaction['amount'],
                'date': transaction['date']
            }
    return None
```

---

## 🔒 SECURITY & PRIVACY

### **Credential Management**

```bash
# .env file (NEVER commit to git)
GMAIL_CLIENT_ID=your_client_id
GMAIL_CLIENT_SECRET=your_client_secret
BANK_API_TOKEN=your_token
WHATSAPP_SESSION_PATH=/secure/path/session

# Add to .gitignore
.env
*.pid
session/
logs/
```

### **Dry Run Mode**

```python
# In all action scripts
import os

DRY_RUN = os.getenv('DRY_RUN', 'true').lower() == 'true'

def send_email(to, subject, body):
    if DRY_RUN:
        logger.info(f'[DRY RUN] Would send email to {to}')
        return
    # Actual send logic
```

### **Audit Logging**

```python
# Required log format
import json
from datetime import datetime

def log_action(action_type, target, parameters, result, approved_by='system'):
    log_entry = {
        'timestamp': datetime.now().isoformat(),
        'action_type': action_type,
        'actor': 'ai_employee',
        'target': target,
        'parameters': parameters,
        'approval_status': 'approved' if approved_by else 'auto',
        'approved_by': approved_by,
        'result': result
    }
    
    log_file = f'Logs/{datetime.now().strftime("%Y-%m-%d")}.json'
    with open(log_file, 'a') as f:
        f.write(json.dumps(log_entry) + '\n')
```

### **Permission Boundaries**

| Action Category | Auto-Approve | Require Approval |
|-----------------|--------------|------------------|
| Email replies | Known contacts | New contacts, bulk |
| Payments | < $50 recurring | New payees, > $100 |
| Social media | Scheduled posts | Replies, DMs |
| File operations | Create, read | Delete, move outside |

---

## 🚀 QUICK START

### **Step 1: Setup Vault**

```bash
# Create Obsidian vault
mkdir AI_Employee_Vault
cd AI_Employee_Vault

# Create folder structure
mkdir -p Inbox Needs_Action/Gmail Needs_Action/WhatsApp Needs_Action/LinkedIn Needs_Action/Finance
mkdir -p In_Progress Plans Pending_Approval Approved Rejected Done Logs Updates Signals Briefings

# Create initial files
echo "# Dashboard" > Dashboard.md
echo "# Company Handbook" > Company_Handbook.md
echo "# Business Goals" > Business_Goals.md
```

### **Step 2: Install Dependencies**

```bash
# Python dependencies
pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib
pip install playwright
pip install watchdog
pip install python-dotenv

# Playwright browsers
playwright install

# Node.js for MCP servers
npm install -g @anthropic/claude-code
npm install @modelcontextprotocol/sdk
```

### **Step 3: Configure Credentials**

```bash
# Copy .env.example
cp .env.example .env

# Edit .env with your credentials
nano .env
```

### **Step 4: Start Watchers**

```bash
# Option A: Direct (development)
python gmail_watcher.py &
python whatsapp_watcher.py &
python orchestrator.py

# Option B: PM2 (production)
npm install -g pm2
pm2 start gmail_watcher.py --interpreter python3
pm2 start whatsapp_watcher.py --interpreter python3
pm2 start orchestrator.py --interpreter python3
pm2 save
pm2 startup
```

### **Step 5: Start Ralph Loop**

```bash
# PowerShell
.\ralph_loop.ps1 -Task "Process all files in Needs_Action" -VaultPath "D:\...\AI_Employee_Vault"

# Or Python
python ralph_loop.py --task "Process all files" --vault "D:\...\AI_Employee_Vault"
```

---

## 📝 TESTING CHECKLIST

### **Bronze Tier (Minimum)**
- [ ] Obsidian vault with Dashboard.md, Company_Handbook.md
- [ ] One working Watcher (Gmail OR file system)
- [ ] Claude/Qwen reading from and writing to vault
- [ ] Basic folder structure: /Inbox, /Needs_Action, /Done

### **Silver Tier (Functional)**
- [ ] All Bronze requirements
- [ ] Two or more Watchers (Gmail + WhatsApp + LinkedIn)
- [ ] Auto-post to LinkedIn
- [ ] Claude reasoning loop creating Plan.md files
- [ ] One working MCP server
- [ ] Human-in-the-loop approval workflow
- [ ] Basic scheduling via cron/Task Scheduler

### **Gold Tier (Autonomous)**
- [ ] All Silver requirements
- [ ] Full cross-domain integration
- [ ] Odoo accounting integration via MCP
- [ ] Facebook/Instagram integration
- [ ] Twitter (X) integration
- [ ] Multiple MCP servers
- [ ] Weekly CEO Briefing generation
- [ ] Error recovery and graceful degradation
- [ ] Comprehensive audit logging
- [ ] Ralph Wiggum loop working

### **Platinum Tier (Production)**
- [ ] All Gold requirements
- [ ] Cloud VM deployment (24/7)
- [ ] Cloud/Local split (Cloud drafts, Local approves)
- [ ] Vault sync via Git/Syncthing
- [ ] Claim-by-move rule implemented
- [ ] Odoo on Cloud VM with HTTPS
- [ ] A2A upgrade (optional)
- [ ] Platinum demo passing

---

## 🎯 JUDGING CRITERIA (Hackathon)

| Criterion | Weight | Description |
|-----------|--------|-------------|
| Functionality | 30% | Does it work? Core features complete? |
| Innovation | 25% | Creative solutions, novel integrations |
| Practicality | 20% | Would you actually use this daily? |
| Security | 15% | Proper credential handling, HITL |
| Documentation | 10% | Clear README, setup instructions, demo |

---

## 📚 LEARNING RESOURCES

### **Prerequisites**
- [Claude Code Fundamentals](https://agentfactory.panaversity.org/docs/AI-Tool-Landscape/claude-code-features-and-workflows)
- [Obsidian Basics](https://help.obsidian.md/Getting+started)
- [Python File I/O](https://realpython.com/read-write-files-python)
- [MCP Introduction](https://modelcontextprotocol.io/introduction)
- [Agent Skills](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview)

### **Core Learning**
- [Claude + Obsidian](https://www.youtube.com/watch?v=sCIS05Qt79Y)
- [Building MCP Servers](https://modelcontextprotocol.io/quickstart)
- [Claude Agent Teams](https://www.youtube.com/watch?v=0J2_YGuNrDo)
- [Gmail API Setup](https://developers.google.com/gmail/api/quickstart)
- [Playwright](https://playwright.dev/python/docs/intro)

### **Deep Dives**
- [MCP Servers Reference](https://github.com/anthropics/mcp-servers)
- [Automate the Boring Stuff](https://automatetheboringstuff.com/)
- [OWASP API Security](https://owasp.org/www-project-api-security/)

---

## 🔧 TROUBLESHOOTING

### **Common Issues**

**Q: Claude Code says "command not found"**
```bash
npm install -g @anthropic/claude-code
# Restart terminal
```

**Q: Watcher scripts stop running**
```bash
# Use PM2 for process management
pm2 start watcher.py --interpreter python3
pm2 save
pm2 startup
```

**Q: Gmail API returns 403**
- Enable Gmail API in Google Cloud Console
- Configure OAuth consent screen
- Add your app to test users

**Q: MCP server won't connect**
```bash
# Check server is running
ps aux | grep mcp

# Verify path in mcp.json is absolute
# Check Claude Code logs
```

---

## 📞 CONTACT & SUBMISSION

**Hackathon Submission**:
- GitHub repository (public or private)
- README.md with setup instructions
- Demo video (5-10 minutes)
- Security disclosure
- Submit Form: https://forms.gle/JR9T1SJq5rmQyGkGA

**Wednesday Research Meetings**:
- Zoom: https://us06web.zoom.us/j/87188707642?pwd=a9XloCsinvn1JzICbPc2YGUvWTbOTr.1
- Meeting ID: 871 8870 7642
- Passcode: 744832
- Every Wednesday 10:00 PM

---

**Last Updated**: 2026-03-07
**Maintained By**: Development Team
**License**: MIT
