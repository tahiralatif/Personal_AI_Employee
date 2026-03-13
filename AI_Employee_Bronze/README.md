# Bronze Tier AI Employee

A local-first AI employee system that monitors a folder for new tasks, processes them using **Qwen AI** as the brain, and maintains an Obsidian vault as its memory and dashboard. The system operates entirely offline on Windows, Linux, or macOS.

## 🎯 Features

### Core Features

- **Local-first**: Runs entirely offline with no cloud dependencies
- **Cross-platform**: Works on Windows, WSL, Linux, and macOS
- **File monitoring**: Watches the Inbox folder for new files using watchdog
- **Qwen AI Brain**: Processes tasks using Qwen CLI (`qwen --cwd`)
- **Ralph Wiggum Loop**: Persistent task processing until complete
- **Vault-based**: Uses Obsidian vault structure as the single source of truth
- **Secure**: No credentials stored in code or committed to Git
- **Real-time dashboard**: Tracks pending, completed, and inbox task counts
- **Company handbook**: Built-in rules and guidelines for AI agent behavior
- **Human-in-the-Loop**: Approval workflow for sensitive actions

### AI Brain Configuration

- **Model**: Qwen (any version accessible via CLI)
- **Interface**: Command-line (`qwen --cwd <path> --prompt <prompt>`)
- **Privacy**: All data stays on your machine
- **No Cloud**: Works completely offline

## Prerequisites

### Required Software

| Component | Version | Purpose |
|-----------|---------|---------|
| **Python** | 3.12+ | Core runtime |
| **uv** | Latest | Package manager |
| **Qwen** | Any | AI brain (via CLI) |

### Installing Qwen

Qwen can be installed via various methods:

**Option 1: Using Ollama (Recommended)**
```bash
# Install Ollama: https://ollama.ai
ollama pull qwen2.5-coder:32b

# Qwen is now available via CLI
```

**Option 2: Using vLLM**
```bash
pip install vllm
# Run Qwen server
```

**Option 3: Using LM Studio (GUI)**
```bash
# Download from https://lmstudio.ai
# Download Qwen model and start CLI
```

**Verify Qwen Installation:**
```bash
qwen --version
# or
qwen --help
```

### Optional Software

| Component | Purpose |
|-----------|---------|
| **Obsidian** | Vault GUI and dashboard |
| **Git** | Version control |

## Quick Start

### 1. Initialize the Vault

```bash
python main.py setup
```

This creates:
- Vault directory structure (`~/AI_Employee_Vault/`)
- Required folders: `Inbox/`, `Needs_Action/`, `Done/`, `Plans/`, `Logs/`
- `Dashboard.md` - Real-time status dashboard
- `Company_Handbook.md` - AI agent rules and guidelines

### 2. Start the File Watcher

```bash
python main.py watch
```

The watcher will:
- Monitor the `Inbox/` folder for new files
- Automatically create action files in `Needs_Action/` when files are detected
- Log all activity to `Logs/YYYY-MM-DD.log`
- Move files >100MB to `Quarantine/` folder

### 3. Drop a File to Test

In a separate terminal, drop a test file:

```bash
echo "Test task content" > ~/AI_Employee_Vault/Inbox/test_task.txt
```

Within 10 seconds, an action file will be created in `Needs_Action/`:

```bash
ls ~/AI_Employee_Vault/Needs_Action/
# FILE_20260225_103045_test_task.txt.md
```

### 4. Check the Dashboard

```bash
cat ~/AI_Employee_Vault/Dashboard.md
```

## Vault Structure

```
~/AI_Employee_Vault/
├── Inbox/              # Drop new files here
├── Needs_Action/       # Action files ready for processing
├── Done/               # Completed tasks
├── Plans/              # AI-generated plans
├── Quarantine/         # Large files (>100MB)
├── Logs/               # Daily activity logs
├── Dashboard.md        # Real-time status
└── Company_Handbook.md # AI agent rules
```

## CLI Commands

### `python main.py setup`

Initialize the vault structure with all required folders and files.

**Output:**
```
✓ Vault structure created successfully
  Location: /home/user/AI_Employee_Vault
  Directories: Inbox, Needs_Action, Done, Plans, Logs
  Files: Dashboard.md, Company_Handbook.md
```

### `python main.py watch`

Start the file system watcher. Press `Ctrl+C` to stop.

**Output:**
```
✓ File system watcher started
  Watching: /home/user/AI_Employee_Vault/Inbox
  Press Ctrl+C to stop
```

### `python main.py --help`

Show available commands and options.

## Action File Format

When a file is detected, an action file is created with this structure:

```markdown
---
type: file_drop
original_name: document.pdf
received: 2026-02-25 10:30:45
priority: medium
status: pending
source_path: /home/user/AI_Employee_Vault/Inbox/document.pdf
file_size: 2048
file_type: .pdf
---

# Task: Process document.pdf

## What Needs to Be Done
A new file was detected in the Inbox folder and requires processing.

## File Details
- **Original Name:** document.pdf
- **Received:** 2026-02-25 10:30:45
- **File Size:** 2.00 KB
- **File Type:** PDF

## Suggested Next Steps
- [ ] Review the file content
- [ ] Determine required action
- [ ] Create a plan in /Plans/
- [ ] Execute the plan
- [ ] Move to /Done/ when complete
```

## Dashboard Features

The Dashboard.md is automatically updated with:

- **System Status**: Active, Idle, or Error
- **Task Summary**: Counts of pending, completed, and inbox items
- **Recent Activity**: Last action performed
- **Quick Links**: Navigation to all vault folders

## Company Handbook

The Company_Handbook.md includes:

- **Authorized Actions**: What the AI can do autonomously
- **Prohibited Actions**: What requires human approval
- **Escalation Procedures**: When to ask for approval
- **Security Guidelines**: Data protection rules
- **Priority Levels**: HIGH, MEDIUM, LOW definitions

## Security

- Credentials are managed through `.env` files (never committed to Git)
- All data remains on the local machine
- No cloud dependencies
- Human approval required for:
  - Payments over PKR 1,000
  - Sending emails
  - Deleting files
  - Contacting unknown entities

## Running Tests

### Unit Tests

```bash
python -m pytest tests/unit/ -v
```

### Integration Tests

```bash
python -m pytest tests/integration/ -v
```

### All Tests

```bash
python -m pytest tests/ -v
```

## Troubleshooting

### Watcher doesn't detect files

1. Ensure the watcher is running: `python main.py watch`
2. Check that `WATCHED_FOLDER` in `.env` points to the correct Inbox path
3. Verify the Inbox folder exists and has read permissions

### Action files not created

1. Check the logs in `Logs/YYYY-MM-DD.log`
2. Ensure `Needs_Action/` folder exists
3. Verify file size is under 100MB

### Large files not quarantined

1. Check `MAX_FILE_SIZE` in `.env` (default: 104857600 = 100MB)
2. Verify `Quarantine/` folder exists
3. Check logs for quarantine events

## Project Structure

```
AI_Employee_Bronze/
├── main.py                     # CLI entry point
├── pyproject.toml              # Project dependencies
├── .env.example                # Environment template
├── .gitignore                  # Git exclusions
├── README.md                   # This file
├── src/ai_employee/
│   ├── __init__.py
│   ├── main.py                 # Module entry point
│   ├── core/
│   │   ├── vault.py            # VaultManager, DashboardManager, CompanyHandbookManager
│   │   └── __init__.py
│   ├── config/
│   │   ├── settings.py         # Settings class
│   │   └── __init__.py
│   ├── handlers/
│   │   ├── file_watcher.py     # FileDropHandler, WatcherService
│   │   └── __init__.py
│   └── utils/
│       ├── logger.py           # VaultLogger
│       ├── file_utils.py       # File utilities
│       ├── exceptions.py       # Custom exceptions
│       └── __init__.py
├── tests/
│   ├── unit/
│   │   ├── test_vault.py
│   │   └── test_watcher.py
│   ├── integration/
│   │   └── test_workflow.py
│   └── fixtures/
│       └── __init__.py
└── specs/
    └── 1-bronze-vault-setup/
        ├── spec.md
        ├── plan.md
        ├── tasks.md
        └── data-model.md
```

## License

This project follows the Personal AI Employee Constitution and is governed by the principles defined in `.specify/memory/constitution.md`.

## GitHub Repository

- **URL**: https://github.com/tahiralatif/Personal_AI_Employee
- **Branch**: `feature/bronze-vault-setup`
- **CI/CD**: Manual testing required

## Contributing

1. Create a feature branch: `git checkout -b feature/bronze-[feature-name]`
2. Make changes and commit: `git commit -m "[bronze] feat: description"`
3. Push to GitHub: `git push origin feature/bronze-[feature-name]`
4. Create a pull request to `develop` branch

## Support

For issues or questions, please refer to:
- [Constitution](.specify/memory/constitution.md)
- [Specification](specs/1-bronze-vault-setup/spec.md)
- [Tasks](specs/1-bronze-vault-setup/tasks.md)
