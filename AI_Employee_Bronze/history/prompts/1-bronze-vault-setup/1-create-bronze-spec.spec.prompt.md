---
id: 1
title: "Create Bronze Spec"
stage: spec
date: 2026-02-22
surface: agent
model: claude-opus-4-6
feature: bronze-vault-setup
branch: 1-bronze-vault-setup
user: Tahira Latif
command: /sp.specify
labels: ["spec", "bronze", "vault", "setup"]
links:
  spec: specs/1-bronze-vault-setup/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - "specs/1-bronze-vault-setup/spec.md"
  - "specs/1-bronze-vault-setup/checklists/requirements.md"
tests: []
outcome: "Successfully created complete specification for Bronze Tier AI Employee - Vault Setup"
evaluation: "Specification includes all required sections with detailed requirements, user scenarios, and success criteria aligned with project constitution"
---

# Create Bronze Spec

## Prompt Text

```
# Bronze Tier — Complete Specification
# Personal AI Employee Hackathon 0
# Use this with: /sp.specify

---
version: 3.0
created: 2026-02-22
owner: Tahira Latif
github: https://github.com/tahiralatif/Personal_AI_Employee
tier: Bronze — Foundation (Minimum Viable Deliverable)
estimated_time: 8-12 hours
---

## /sp.specify PROMPT (Copy-Paste This Into Your AI CLI Agent)

```
/sp.specify

Project: Personal AI Employee — Bronze Tier
Repository: https://github.com/tahiralatif/Personal_AI_Employee
Branch workflow: feature/bronze-[feature-name] → develop → main

---

## INTENT

Build a Minimum Viable AI Employee that runs entirely on a local Windows laptop
(Ubuntu WSL). It monitors a local folder for new tasks, processes them using an
AI CLI agent, and keeps an Obsidian vault updated as its brain and dashboard.

The system must work offline — no cloud, no external APIs in Bronze Tier.
All intelligence is delivered through an AI CLI agent invoked manually.

---

## ENVIRONMENT

- OS: Windows 11 with Ubuntu WSL
- Vault location: ~/AI_Employee_Vault (inside WSL home)
- Python package manager: uv (NOT pip, NOT poetry)
- Python version: 3.12+
- AI tool: AI CLI agent (invoked via terminal)
- Local model server: LM Studio on localhost:1234
- Version control: Git + GitHub Desktop

---

## PROJECT INITIALIZATION — EXACT STEPS

### Step 1: Vault Create (Pure CLI)

  mkdir -p ~/AI_Employee_Vault
  cd ~/AI_Employee_Vault

  # All required folders
  mkdir -p Inbox Needs_Action Done Plans Pending_Approval Approved Rejected Logs

  # .gitignore — credentials kabhi git mein nahi jayein
  cat > .gitignore << EOF
  .env
  *.pyc
  __pycache__/
  .DS_Store
  *.log
  .venv/
  EOF

### Step 2: UV Project Initialize (inside vault)

  uv init --name ai-employee-bronze
  uv add watchdog
  uv add python-dotenv
  uv venv
  source .venv/bin/activate

### Step 3: Project Folder Structure

After uv init, final structure must look like this:

  ~/AI_Employee_Vault/
  │
  ├── pyproject.toml              ← uv manages dependencies
  ├── .python-version             ← pins Python version
  ├── .env                        ← secrets (NEVER in git)
  ├── .gitignore
  ├── README.md
  │
  ├── src/
  │   └── ai_employee/
  │       ├── __init__.py
  │       ├── main.py             ← entry point, runs everything
  │       ├── watcher.py          ← DropHandler + WatcherService classes
  │       ├── vault_manager.py    ← VaultManager class
  │       └── logger.py           ← ActivityLogger class
  │
  ├── tests/
  │   ├── __init__.py
  │   └── test_watcher.py
  │
  ├── Inbox/                      ← drop raw files here
  ├── Needs_Action/               ← AI agent reads from here
  ├── Done/                       ← completed tasks go here
  ├── Plans/                      ← AI agent writes plans here
  ├── Pending_Approval/           ← sensitive actions wait here
  ├── Approved/                   ← human approved — execute
  ├── Rejected/                   ← human rejected — skip
  ├── Logs/                       ← all action logs here
  ├── Dashboard.md                ← always up to date
  └── Company_Handbook.md         ← rules the AI agent follows

---

## FEATURE 1: Core Vault Files

### Dashboard.md — Exact Format

  ---
  title: AI Employee Dashboard
  tier: Bronze
  last_updated: YYYY-MM-DD HH:MM
  status: active
  ---

  # AI Employee Dashboard (Bronze Tier)

  ## Status
  - Watcher: Running (File System)
  - Pending Tasks: 0
  - Last Action: None yet

  ## Quick Links
  - [Needs Action](./Needs_Action/)
  - [Company Handbook](./Company_Handbook.md)
  - [Done](./Done/)

  ## Today's Brief
  (AI agent will write summary here after each session)

### Company_Handbook.md — Exact Format

  ---
  title: Company Handbook
  version: 1.0
  owner: Tahira
  ---

  # Company Handbook — AI Employee Rules

  ## Core Principles
  - Always be polite and professional
  - Keep everything local-first
  - Log every action in /Logs/
  - Never delete files — only move them

  ## Approval Required For (Human-in-the-Loop)
  - Any payment (ANY amount)
  - Sending any email
  - Any social media post
  - Contacting unknown people

  ## Priority Levels
  - HIGH: Payment requests, urgent client messages
  - MEDIUM: Regular tasks, follow-ups
  - LOW: Newsletters, general updates

  ## What AI Agent Can Do Autonomously
  - Read files from any folder
  - Create Plan.md files in /Plans
  - Update Dashboard.md
  - Move files to /Done
  - Write to /Logs

  ## What AI Agent Must NOT Do Without Approval
  - Send emails
  - Make payments
  - Delete any file
  - Post on social media
  - Contact unknown people

### Task File Format (YAML Frontmatter — All Task Files Must Use This)

  ---
  type: file_drop          # file_drop | email | manual
  original_name: file.pdf
  received: 2026-02-22 10:30:00
  priority: high           # high | medium | low
  status: pending          # pending | in_progress | done
  ---

  # Task Title

  ## What Needs to Be Done
  (description)

  ## Suggested Next Steps
  - [ ] Step 1
  - [ ] Step 2

---

## FEATURE 2: Python Watcher — OOP Standards

### ALL Python code must follow these rules:
- Every logical unit is a class (no standalone functions except main())
- Type hints on every method parameter and return type
- Docstring on every class and every method
- Exception handling with try/except on every I/O operation
- No hardcoded paths — always read from config or __init__ parameter

### Class: DropHandler (in src/ai_employee/watcher.py)

Inherits from: watchdog.events.FileSystemEventHandler

Responsibilities:
- Detect new files dropped in /Inbox
- Create a structured .md action file in /Needs_Action
- Include YAML frontmatter in created file
- Call ActivityLogger to log the event

Interface:
  class DropHandler(FileSystemEventHandler):
      def __init__(self, vault_path: str, logger: ActivityLogger) -> None
      def on_created(self, event: FileSystemEvent) -> None
      def _create_action_file(self, source: Path) -> Path
      def _build_frontmatter(self, source: Path) -> str

### Class: WatcherService (in src/ai_employee/watcher.py)

Responsibilities:
- Own the Observer lifecycle (start, stop)
- Register DropHandler on /Inbox folder
- Handle KeyboardInterrupt gracefully (Ctrl+C stops cleanly)
- Print status messages to terminal

Interface:
  class WatcherService:
      def __init__(self, vault_path: str, logger: ActivityLogger) -> None
      def start(self) -> None
      def stop(self) -> None

Run command:
  uv run python src/ai_employee/main.py

Background run (WSL):
  nohup uv run python src/ai_employee/main.py > watcher.log 2>&1 &

### Class: VaultManager (in src/ai_employee/vault_manager.py)

Responsibilities:
- Read all .md files from /Needs_Action
- Update Dashboard.md with current counts and timestamp
- Move files between folders (Needs_Action → Done, etc.)
- Create Plan.md files in /Plans with correct format

Interface:
  class VaultManager:
      def __init__(self, vault_path: str) -> None
      def read_needs_action(self) -> list[dict]
      def update_dashboard(self, pending_count: int, last_action: str) -> None
      def move_to_done(self, filename: str) -> None
      def move_to_pending_approval(self, filename: str) -> None
      def create_plan(self, task_name: str, steps: list[str]) -> Path

### Class: ActivityLogger (in src/ai_employee/logger.py)

Responsibilities:
- Log every action to /Logs/YYYY-MM-DD.md
- Each log entry has: timestamp, action type, detail, result
- Create new log file each day automatically

Interface:
  class ActivityLogger:
      def __init__(self, logs_path: str) -> None
      def log(self, action: str, detail: str, result: str) -> None
      def _get_today_log_path(self) -> Path
      def _ensure_log_file_exists(self) -> None

Log entry format:
  ## 2026-02-22 10:30:45
  - Action: file_detected
  - Detail: invoice_client_a.pdf dropped in /Inbox
  - Result: Created Needs_Action/FILE_20260222_103045_invoice.md

### main.py — Entry Point

  def main() -> None:
      # 1. Load .env with python-dotenv
      # 2. Initialize ActivityLogger
      # 3. Initialize VaultManager
      # 4. Initialize WatcherService
      # 5. Print startup message
      # 6. Start WatcherService (blocking loop)

  if __name__ == "__main__":
      main()

---

## FEATURE 3: Agent Skills (SKILL.md Files)

Location: ~/AI_Employee_Vault/.claude/skills/

### Skill 1: task_processor.md

  # SKILL: Process Needs Action

  ## When to Use
  When there are .md files in /Needs_Action that need processing

  ## Steps
  1. Read Company_Handbook.md — follow all rules
  2. Read every .md file in /Needs_Action
  3. For each file:
     a. Understand the task
     b. Check if approval needed (see Handbook)
     c. If approval needed: move to /Pending_Approval, stop
     d. If no approval needed: create Plan.md in /Plans
     e. Move processed file to /Done
  4. Update Dashboard.md when done

  ## Plan.md Format
  ---
  task: [task name]
  created: [timestamp]
  status: complete
  ---
  # Plan: [Task Name]
  ## Steps Taken
  - [x] Step 1
  ## Result
  [what was done]

  ## Rules
  - NEVER send emails
  - NEVER make payments
  - ALWAYS log actions
  - ALWAYS create Plan before acting

### Skill 2: dashboard_updater.md

  # SKILL: Update Dashboard

  ## When to Use
  After any task is processed

  ## Steps
  1. Count .md files in /Needs_Action
  2. Count .md files in /Done
  3. Get current timestamp
  4. Rewrite Dashboard.md with updated info
  5. Keep Today's Brief section updated

### Skill 3: create_plan.md

  # SKILL: Create Plan

  ## When to Use
  Before taking any action on any task

  ## Steps
  1. Read the task file fully
  2. Break it into checklist steps
  3. Write Plan.md to /Plans/PLAN_[taskname]_[date].md
  4. Return plan path

---

## FEATURE 4: AI CLI Agent Integration

### Launch Command
  cd ~/AI_Employee_Vault
  ai-agent --cwd .        # or: claude --cwd .

### Settings File (for local model)
  Location: ~/.claude/lmstudio.setting.json
  Purpose: Points agent to LM Studio at localhost:1234

### First Test Prompt (after launch)
  You are my Bronze Tier AI Employee.
  Read Company_Handbook.md first and follow its rules.

  Task:
  1. Read all files in /Needs_Action
  2. For each file, create a Plan.md in /Plans/
  3. Update Dashboard.md with summary
  4. Move processed files to /Done/

  Start working.

---

## GITHUB WORKFLOW

### Branch Per Feature (one branch per item below)

  feature/bronze-vault-setup          ← Feature 1
  feature/bronze-watcher-script       ← Feature 2
  feature/bronze-agent-skills         ← Feature 3
  feature/bronze-integration-test     ← Final test

### Workflow Steps (every feature)

  1. Cut branch from develop:
     git checkout develop
     git checkout -b feature/bronze-vault-setup

  2. Work and commit often:
     git add .
     git commit -m "[bronze] feat: add vault folder structure and core files"

  3. Push to GitHub:
     git push origin feature/bronze-vault-setup

  4. Create Pull Request: feature/bronze-* → develop
     Tahira reviews → approves → merges

  5. When all Bronze features merged:
     PR: develop → main

### Commit Message Format
  [bronze] feat: add file system watcher classes
  [bronze] fix: watcher path issue on WSL home directory
  [bronze] docs: add README setup instructions
  [bronze] test: add end-to-end vault test

### What To Commit vs Not

  COMMIT:                         DO NOT COMMIT:
  src/**/*.py                     .env
  *.md (vault templates)          credentials.json
  pyproject.toml                  *.session
  requirements.txt                __pycache__/
  .gitignore                      .venv/
  README.md                       watcher.log

---

## SUCCESS CRITERIA (All Must Pass Before Bronze Is Complete)

1. uv run python src/ai_employee/main.py starts with no errors
2. Dropping a file in /Inbox creates a .md file in /Needs_Action within 10 seconds
3. Created .md file has correct YAML frontmatter
4. Event is logged in /Logs/YYYY-MM-DD.md with timestamp
5. Dashboard.md pending count is correct after each watcher cycle
6. AI CLI agent reads Company_Handbook.md before processing any task
7. AI CLI agent creates Plan.md in /Plans for every task
8. Task file moves to /Done after processing
9. All Python classes have docstrings and type hints
10. No credentials exist anywhere in vault or Git repo
11. All 3 SKILL.md files exist and are readable by AI agent
12. End-to-end test passes (see Acceptance Test below)

---

## NON-GOALS (Not in Bronze — Future Tiers)

NOT building in Bronze:
- Gmail integration           → Silver Tier
- WhatsApp monitoring         → Silver Tier
- Email sending via MCP       → Silver Tier
- LinkedIn posting            → Silver Tier
- Scheduled cron jobs         → Silver Tier
- MCP servers                 → Silver Tier
- Payment automation          → Gold Tier
- CEO Briefing generation     → Gold Tier
- Ralph Wiggum loop           → Gold Tier
- Cloud deployment            → Platinum Tier
- Multi-agent coordination    → Platinum Tier

---

## ACCEPTANCE TEST (End-to-End — Run This Last)

GIVEN:
  - LM Studio running on localhost:1234
  - uv run python src/ai_employee/main.py running in terminal 1
  - AI CLI agent running in ~/AI_Employee_Vault in terminal 2

STEP 1: Drop test file
  echo "Test invoice from Client A - PKR 5000" > ~/AI_Employee_Vault/Inbox/test_invoice.txt

STEP 2: Verify watcher (within 10 seconds)
  ls ~/AI_Employee_Vault/Needs_Action/
  # Expected: FILE_[timestamp]_test_invoice.txt.md

STEP 3: Verify log
  cat ~/AI_Employee_Vault/Logs/$(date +%Y-%m-%d).md
  # Expected: entry with timestamp and file name

STEP 4: Run AI agent
  (in terminal 2, give agent the task prompt)

STEP 5: Verify results
  ls ~/AI_Employee_Vault/Plans/       # Plan.md must exist
  ls ~/AI_Employee_Vault/Done/        # task file must be here
  cat ~/AI_Employee_Vault/Dashboard.md  # must show updated status

ALL 5 STEPS PASS = Bronze Tier Complete ✅
```

---

## AFTER /sp.specify — RUN IN THIS ORDER

```
/sp.clarify
Check:
- Are OOP class interfaces complete?
- Is uv project structure matching exactly?
- Any missing edge cases in watcher?
- Does anything conflict with Constitution?

/sp.plan
Generate implementation plan.
Phase order:
  1. Vault folders + core .md files
  2. uv init + project structure
  3. ActivityLogger class (needed by others)
  4. VaultManager class
  5. DropHandler + WatcherService classes
  6. main.py entry point
  7. Agent SKILL.md files
  8. README.md
  9. End-to-end acceptance test

/sp.tasks
Break each phase into 15-30 minute atomic tasks.
Each task = one class OR one file OR one test.

/sp.implement
Start with Phase 1 (vault structure).
Follow OOP standards from Constitution.
After each phase: git commit on feature branch.
```

---

*Specification v3.0 — Combined from hackathon document + OOP + uv + GitHub standards*
*GitHub: https://github.com/tahiralatif/Personal_AI_Employee*
*Constitution: .specify/memory/constitution.md*
```

## Response Text

I have successfully created a complete specification for the Bronze Tier AI Employee - Vault Setup feature. The specification includes:

- A detailed feature description explaining the core functionality
- Three prioritized user stories covering the essential functionality:
  1. Local AI Employee Setup (P1 priority)
  2. File System Monitoring (P1 priority)
  3. Dashboard and Handbook Creation (P2 priority)
- Comprehensive functional and non-functional requirements (10 FRs and 5 NFRs)
- Key entities that represent the data and objects in the system
- Measurable success criteria (8 specific outcomes)
- Clear assumptions, dependencies and out-of-scope items

The specification adheres to the project constitution by focusing on local-first design, human-in-the-loop approval requirements, and proper security practices. It follows the OOP standards specified in the requirements with proper class design, type hints, and documentation.

The specification is ready for the next phase: /sp.plan to generate an implementation plan.