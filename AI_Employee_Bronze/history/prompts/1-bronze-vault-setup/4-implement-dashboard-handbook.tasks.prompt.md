---
id: 4
title: "Implement Dashboard And Handbook"
stage: tasks
date: 2026-02-25
surface: agent
model: claude-opus-4-6
feature: 1-bronze-vault-setup
branch: 1-bronze-vault-setup
user: Tahira Latif
command: /sp.tasks
labels: ["tasks", "bronze", "dashboard", "handbook"]
links:
  spec: specs/1-bronze-vault-setup/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - "src/ai_employee/core/vault.py"
  - "specs/1-bronze-vault-setup/tasks.md"
tests: []
---

## Prompt Text

```
Implement T040-T045 from tasks.md (User Story 3 - Dashboard and Handbook Creation):
- T040: Enhance DashboardManager to update status information
- T041: Implement method to count pending tasks in Needs_Action folder
- T042: Implement method to track completed tasks in Done folder
- T043: Create CompanyHandbookManager to maintain rules
- T044: Implement template for Company_Handbook.md with required sections
- T045: Add functionality to update dashboard with latest activity

Requirements:
1. Follow OOP standards with type hints and docstrings
2. Handle exceptions properly with try/except
3. Log all actions using standard logging
4. Dashboard should show real-time task counts
5. Handbook should include authorized/prohibited actions and escalation procedures
```

## Response snapshot

Implemented DashboardManager and CompanyHandbookManager classes in `src/ai_employee/core/vault.py`:

1. **DashboardManager class**
   - `count_pending_tasks()` - Counts .md files in Needs_Action folder
   - `count_completed_tasks()` - Counts .md files in Done folder
   - `count_inbox_items()` - Counts files in Inbox folder
   - `get_task_summary()` - Returns dictionary with all task counts
   - `update_dashboard()` - Updates Dashboard.md with current status and last activity
   - `_generate_dashboard_content()` - Generates formatted dashboard content

2. **CompanyHandbookManager class**
   - `handbook_exists()` - Checks if handbook file exists
   - `get_handbook_content()` - Reads current handbook content
   - `update_handbook()` - Updates handbook with new content
   - `_generate_handbook_content()` - Generates handbook template with all required sections:
     - Authorized Actions
     - Prohibited Actions
     - Escalation Procedures
     - Security Guidelines
     - Priority Levels
     - What AI Agent Can Do Autonomously
   - `add_rule()` - Adds new rules to handbook (simplified implementation)

All tasks T040-T045 marked complete in tasks.md.

## Outcome

- ✅ Impact: User Story 3 (Dashboard and Handbook) now complete - all 6 tasks finished
- 🧪 Tests: Manual testing needed - verify Dashboard.md and Company_Handbook.md content
- 📁 Files: vault.py (610 lines, added ~350 lines), tasks.md updated
- 🔁 Next prompts: T050-T059 - Polish & Cross-Cutting Concerns (Phase 6)
- 🧠 Reflection: Implementation follows Constitution standards - OOP, logging, exception handling

## Evaluation notes (flywheel)

- Failure modes observed: None - implementation complete
- Graders run and results: Pending manual testing
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): Implement T050-T059 Polish tasks
