# Implementation Plan: Bronze Tier AI Employee - Vault Setup

**Branch**: `1-bronze-vault-setup` | **Date**: 2026-02-24 | **Spec**: [specs/1-bronze-vault-setup/spec.md](specs/1-bronze-vault-setup/spec.md)

**Note**: This template is filled in by the `/sp.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Implementation of a local-first AI employee system that monitors a folder for new tasks, processes them using an AI CLI agent, and maintains an Obsidian vault as its brain and dashboard. The system operates entirely offline on a Windows laptop with Ubuntu WSL, with file system monitoring using the watchdog library and structured task processing.

## Technical Context

**Language/Version**: Python 3.12+
**Primary Dependencies**: watchdog, python-dotenv, uv package manager
**Storage**: File system-based (Obsidian vault structure)
**Testing**: pytest for unit and integration tests
**Target Platform**: Windows with Ubuntu WSL
**Project Type**: Single project with file system monitoring
**Performance Goals**: File detection and action file creation within 10 seconds of file drop
**Constraints**: Must run offline without internet connection, handle files up to 100MB, follow OOP standards with type hints and docstrings
**Scale/Scope**: Single-user local system, designed for personal productivity tasks

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- ✅ **Local-First**: System operates entirely offline on local machine with no cloud dependencies
- ✅ **Human-in-the-Loop**: AI requires human approval before performing sensitive actions
- ✅ **Vault as Brain**: Obsidian vault serves as single source of truth with defined folder structure
- ✅ **Simplicity First**: Building minimal viable solution with core functionality first
- ✅ **Security Always**: Credentials managed through .env files and properly ignored by Git
- ✅ **Branch per Feature**: Following feature/bronze-vault-setup naming convention

## Project Structure

### Documentation (this feature)

```text
specs/1-bronze-vault-setup/
├── plan.md              # This file (/sp.plan command output)
├── research.md          # Phase 0 output (/sp.plan command)
├── data-model.md        # Phase 1 output (/sp.plan command)
├── quickstart.md        # Phase 1 output (/sp.plan command)
├── contracts/           # Phase 1 output (/sp.plan command)
└── tasks.md             # Phase 2 output (/sp.tasks command - NOT created by /sp.plan)
```

### Source Code (repository root)

```text
src/
├── ai_employee/
│   ├── __init__.py
│   ├── main.py          # Main entry point and file watcher
│   ├── config/
│   │   ├── __init__.py
│   │   └── settings.py  # Configuration loading
│   ├── core/
│   │   ├── __init__.py
│   │   ├── vault.py     # Vault structure management
│   │   └── watcher.py   # File system watcher
│   ├── handlers/
│   │   ├── __init__.py
│   │   └── drop_handler.py  # Process incoming files
│   └── utils/
│       ├── __init__.py
│       ├── logger.py    # Logging functionality
│       └── file_utils.py # File processing utilities

tests/
├── unit/
│   ├── test_vault.py
│   ├── test_watcher.py
│   └── test_drop_handler.py
├── integration/
│   └── test_end_to_end.py
└── fixtures/
    └── sample_files/

AI_Employee_Vault/      # Created by the system
├── Inbox/              # New unprocessed items
├── Needs_Action/       # Tasks ready for Claude
├── Done/               # Completed tasks only
├── Plans/              # Claude-generated plans
├── Logs/               # All action logs
├── Dashboard.md        # Always up to date
└── Company_Handbook.md # Claude's rules

.env                    # Ignored by Git - contains local settings
pyproject.toml          # Project dependencies and configuration
README.md               # Project documentation
.gitignore              # Properly excludes sensitive files
```

**Structure Decision**: Selected single project structure with modular organization following the specified vault folder structure. The system separates concerns into configuration, core functionality, handlers, and utilities, with proper test organization.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| [None] | [No violations identified] | [Constitution fully respected] |