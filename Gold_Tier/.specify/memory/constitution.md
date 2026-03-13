<!-- SYNC IMPACT REPORT
Version change: N/A (initial creation) → 2.0.0
Modified principles: N/A
Added sections: All sections from provided constitution
Removed sections: N/A
Templates requiring updates:
  - .specify/templates/plan-template.md ⚠ pending
  - .specify/templates/spec-template.md ⚠ pending
  - .specify/templates/tasks-template.md ⚠ pending
  - .specify/templates/commands/*.md ⚠ pending
Follow-up TODOs: None
-->

# Personal AI Employee Constitution

## Core Principles

### I. Local-First
<!-- Rule: Data stays on local machine. No cloud without approval. -->
Data MUST remain on the local machine unless explicit cloud approval is granted. All processing occurs locally to maintain data sovereignty and privacy.

### II. Human-in-the-Loop
<!-- Rule: AI NEVER takes sensitive action without human approval. -->
AI systems MUST obtain human approval before performing any sensitive actions including sending emails, making payments, deleting files, or engaging with unknown contacts.

### III. Vault as Brain
<!-- Rule: Obsidian vault is the single source of truth. -->
The Obsidian vault serves as the single source of truth for all project data, tasks, and documentation. All important information MUST be stored in the vault structure.

### IV. Simplicity First
<!-- Rule: Build the simplest thing that works. -->
Development efforts MUST prioritize the simplest solution that meets requirements. Complexity should be added only when absolutely necessary and clearly justified.

### V. Security Always
<!-- Rule: Credentials NEVER in vault or Git. -->
Credentials, API keys, and sensitive data MUST NEVER be stored in the vault or committed to Git. These must be managed through secure environment variables or credential files properly ignored by Git.

### VI. Branch per Feature
<!-- Rule: Every feature = its own Git branch. Never work on main. -->
Each feature MUST be developed on its own Git branch following the naming convention feature/[tier]-[feature-name]. Development on the main branch is strictly prohibited.

## GitHub Workflow (Non-Negotiable)

### Repository Info
Repository URL: https://github.com/tahiralatif/Personal_AI_Employee
Main branch: main — only finished, reviewed code
Dev branch: develop — integration branch

### Branch Naming Convention
All branches MUST follow the format: feature/[tier]-[feature-name]
Examples:
- feature/bronze-vault-setup
- feature/bronze-watcher-script
- feature/bronze-claude-integration
- feature/silver-gmail-watcher (for later tiers)

### Commit Message Format
All commits MUST follow the format: [tier] type: description
Examples:
- [bronze] feat: add file system watcher
- [bronze] fix: watcher path issue on WSL
- [silver] feat: add gmail watcher (for later tiers)

### What Goes in Git vs Not
ALWAYS COMMIT:
- Scripts (watcher.py, orchestrator.py)
- Documentation files (*.md)
- README.md, requirements.txt, .gitignore
- SKILL.md files

NEVER COMMIT:
- .env files (credentials)
- credentials.json, token.json
- Session files (*.session)
- Cache directories (__pycache__/)
- Model files from LM Studio

### .gitignore Requirements
The .gitignore file MUST always contain:
.env
*.env
credentials.json
token.json
*.session
__pycache__/
*.pyc
.DS_Store
*.log

## Security Rules

### Credential Management
No credentials in vault: API keys go in .env ONLY
No .env in Git: Always in .gitignore — no exceptions

### Action Thresholds
Payment threshold: ANY payment over PKR 1,000 = human approval required
Email rule: Claude NEVER sends email without human approval
Delete rule: Claude NEVER deletes files without human approval
Unknown contacts: Always require human approval

## Vault Folder Structure

The vault MUST follow this exact structure:
```
AI_Employee_Vault/
├── Inbox/              ← New unprocessed items
├── Needs_Action/       ← Tasks ready for Claude
├── Done/               ← Completed tasks only
├── Plans/              ← Claude-generated plans
├── Logs/               ← All action logs
├── Dashboard.md        ← Always up to date
└── Company_Handbook.md ← Claude's rules
```

## Code Quality Standards

All Python scripts MUST:
- Handle exceptions (try/except)
- Log to /Logs folder with timestamps
- Stop cleanly with Ctrl+C
- Have no hardcoded credentials
- Include a comment explaining its purpose
- Use YAML frontmatter for all vault task files (--- type, priority, date ---)

## Agent Behavior Standards

Claude Code MUST ALWAYS:
- Read Company_Handbook.md before any task
- Create Plan.md before taking action
- Update Dashboard.md after completing work
- Log every action to /Logs/YYYY-MM-DD.md
- Ask for approval before any external action

Claude Code MUST NEVER:
- Send emails without approval
- Make payments without approval
- Delete files from Done/
- Ignore Company_Handbook.md rules

## Tier Roadmap

Bronze tier (feature/bronze-*): NOW - Vault + Watcher + Claude Code
Silver tier (feature/silver-*): NEXT - Gmail + LinkedIn + MCP
Gold tier (feature/gold-*): LATER - Full automation + CEO Briefing
Platinum tier (feature/platinum-*): DREAM - Cloud 24/7 deployment

## Governance

This Constitution defines immutable rules that apply to EVERY tier of this project. Every spec, every plan, every line of code MUST respect these rules. The Constitution applies to Bronze NOW and Silver, Gold, Platinum LATER. It is written ONCE and never changes without a deliberate decision.

Amendment Procedure:
- Any changes to this Constitution require explicit owner approval
- Versioning follows semantic versioning rules (MAJOR.MINOR.PATCH)
- Compliance reviews are mandatory for all development activities

**Version**: 2.0.0 | **Ratified**: 2026-02-22 | **Last Amended**: 2026-02-22
