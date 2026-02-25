---
id: 1
title: "Create Initial Constitution"
stage: constitution
date: 2026-02-22
surface: agent
model: claude-opus-4-6
feature: none
branch: main
user: Tahira Latif
command: /sp.constitution
labels: ["constitution", "setup", "governance"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
  - ".specify/memory/constitution.md"
tests: []
outcome: "Successfully created initial constitution document based on user-provided content"
evaluation: "Constitution document created with all required principles, workflows, and governance rules"
---

# Create Initial Constitution

## Prompt Text

```
# Project Constitution
# Personal AI Employee Hackathon 0
# AI_Employee_Vault — Applies to ALL Tiers

---
version: 2.0
created: 2026-02-22
owner: Tahira Latif
github: https://github.com/tahiralatif/Personal_AI_Employee
applies_to: Bronze, Silver, Gold, Platinum
---

## What Is This Constitution?

This Constitution defines **immutable rules** that apply to EVERY tier of this project.
Every spec, every plan, every line of code must respect these rules.

This file applies to Bronze NOW — and Silver, Gold, Platinum LATER.
You write it ONCE. It never changes without a deliberate decision.

---

## Core Principles

1. **Local-First** — Data stays on local machine. No cloud without approval.
2. **Human-in-the-Loop** — AI NEVER takes sensitive action without human approval.
3. **Vault as Brain** — Obsidian vault is the single source of truth.
4. **Simplicity First** — Build the simplest thing that works.
5. **Security Always** — Credentials NEVER in vault or Git.
6. **Branch per Feature** — Every feature = its own Git branch. Never work on main.

---

## GitHub Workflow (Non-Negotiable)

### Repository Info
- **URL:** https://github.com/tahiralatif/Personal_AI_Employee
- **Main branch:** `main` — only finished, reviewed code
- **Dev branch:** `develop` — integration branch

### How We Work

```
main (production)
  └── develop (integration)
        ├── feature/bronze-vault-setup
        ├── feature/bronze-watcher-script
        ├── feature/bronze-agent-skills
        ├── feature/silver-gmail-watcher     (later)
        └── feature/gold-ralph-wiggum        (later)
```

### Step by Step — Every Feature

```
1. New feature starts:
   git checkout develop
   git checkout -b feature/bronze-vault-setup

2. Work on feature — commit often:
   git add .
   git commit -m "[bronze] feat: add vault folder structure"

3. Feature done — create Pull Request:
   Push branch to GitHub
   Create PR: feature/bronze-vault-setup → develop
   Tahira reviews → approves → merges

4. Tier complete — merge to main:
   PR: develop → main
```

### Branch Naming Convention

```
feature/[tier]-[feature-name]

Bronze examples:
  feature/bronze-vault-setup
  feature/bronze-watcher-script
  feature/bronze-claude-integration
  feature/bronze-agent-skills

Silver examples (later):
  feature/silver-gmail-watcher
  feature/silver-linkedin-post

Gold examples (later):
  feature/gold-ralph-wiggum
  feature/gold-ceo-briefing
```

### Commit Message Format

```
[bronze] feat: add file system watcher
[bronze] fix: watcher path issue on WSL
[bronze] docs: update README with setup steps
[silver] feat: add gmail watcher         (later)
```

### What Goes in Git vs Not

```
✅ ALWAYS COMMIT:
  watcher.py, orchestrator.py (scripts)
  *.md files (vault templates, docs)
  README.md
  requirements.txt
  .gitignore
  SKILL.md files

❌ NEVER COMMIT:
  .env (credentials)
  credentials.json
  token.json
  *.session (WhatsApp)
  __pycache__/
  LM Studio model files
```

### .gitignore Must Always Contain

```
.env
*.env
credentials.json
token.json
*.session
__pycache__/
*.pyc
.DS_Store
*.log
```

---

## Security Rules

| Rule | Detail |
|------|--------|
| No credentials in vault | API keys go in .env ONLY |
| No .env in Git | Always in .gitignore — no exceptions |
| Payment threshold | ANY payment over PKR 1,000 = human approval |
| Email rule | Claude NEVER sends email without human approval |
| Delete rule | Claude NEVER deletes files without human approval |
| Unknown contacts | Always require human approval |

---

## Vault Folder Structure

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

---

## Code Quality Standards

- All Python scripts must handle exceptions (try/except)
- All scripts must log to /Logs folder with timestamps
- All scripts must stop cleanly with Ctrl+C
- No hardcoded credentials anywhere
- Every script must have a comment explaining its purpose
- All vault task files must use YAML frontmatter (--- type, priority, date ---)

---

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

---

## Tier Roadmap

| Tier | Branches | Status | Key Deliverable |
|------|----------|--------|-----------------|
| Bronze | feature/bronze-* | 🎯 NOW | Vault + Watcher + Claude Code |
| Silver | feature/silver-* | ⬜ Next | Gmail + LinkedIn + MCP |
| Gold | feature/gold-* | ⬜ Later | Full automation + CEO Briefing |
| Platinum | feature/platinum-* | ⬜ Dream | Cloud 24/7 deployment |

---

## Judging Criteria Alignment

| Criterion | Weight | How Constitution Supports It |
|-----------|--------|------------------------------|
| Functionality | 30% | Testable success criteria for each tier |
| Innovation | 25% | Local-first + Agent Skills approach |
| Practicality | 20% | Real Pakistani business use case |
| Security | 15% | Explicit security rules + .env + HITL |
| Documentation | 10% | README + Constitution + demo video |

---

*This Constitution was created once and applies to ALL tiers.*
*GitHub: https://github.com/tahiralatif/Personal_AI_Employee*
*Owner: Tahira Latif | Created: February 2026*
```

## Response Text

I've created and updated the project constitution based on the provided content. The constitution at `.specify/memory/constitution.md` now contains all the specified principles, workflows, security rules, and governance structures. The document includes:

- Six core principles: Local-First, Human-in-the-Loop, Vault as Brain, Simplicity First, Security Always, and Branch per Feature
- Detailed GitHub workflow with repository info, branching strategy, and commit message format
- Security rules covering credential management and action thresholds
- Required vault folder structure
- Code quality standards for Python scripts
- Agent behavior standards specifying what Claude Code must/must not do
- Tier roadmap for Bronze, Silver, Gold, and Platinum levels
- Governance section with amendment procedures

The constitution is now properly configured with version 2.0.0, ratified on 2026-02-22, and follows all the required formatting and structure from the original document.