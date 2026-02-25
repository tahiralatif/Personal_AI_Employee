---
id: 3
title: "Implement File Watcher Classes"
stage: tasks
date: 2026-02-25
surface: agent
model: claude-opus-4-6
feature: 1-bronze-vault-setup
branch: 1-bronze-vault-setup
user: Tahira Latif
command: /sp.tasks
labels: ["tasks", "bronze", "watcher", "file-monitoring"]
links:
  spec: specs/1-bronze-vault-setup/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - "src/ai_employee/handlers/file_watcher.py"
  - "main.py"
  - "specs/1-bronze-vault-setup/tasks.md"
tests: []
---

## Prompt Text

```
Implement T030-T038 from tasks.md (User Story 2 - File System Monitoring):
- T030: Implement FileWatcher class using watchdog library
- T031: Create FileDropHandler to process incoming files
- T032: Implement YAML frontmatter generation for action files
- T033: Create method to sanitize filenames with special characters
- T034: Implement file size validation (reject files >100MB)
- T035: Create method to move large files to quarantine folder
- T036: Implement proper file processing flow from Inbox to Needs_Action
- T037: Add logging functionality for file processing events
- T038: Implement graceful shutdown with Ctrl+C support

Requirements:
1. Use watchdog library for file system monitoring
2. Follow OOP standards with type hints and docstrings
3. Handle exceptions properly with try/except
4. Log all actions using VaultLogger
5. Use existing file_utils for safe file operations
6. Support graceful Ctrl+C shutdown
7. Move large files (>100MB) to quarantine folder
```

## Response snapshot

Implemented complete file system watcher in `src/ai_employee/handlers/file_watcher.py` (519 lines):

1. **FileDropHandler class** (inherits from FileSystemEventHandler)
   - `on_created()` - Handles file creation events
   - `_process_file()` - Validates and processes files
   - `_create_action_file()` - Creates .md action files in Needs_Action
   - `_build_frontmatter()` - Generates YAML frontmatter with type, original_name, received, priority, status
   - `_build_action_content()` - Builds complete action file content
   - `_move_to_quarantine()` - Moves large files to quarantine folder
   - Filename sanitization using existing `sanitize_filename()` from file_utils
   - File size validation using `validate_file_size()` from file_utils

2. **WatcherService class**
   - `start()` - Starts the Observer
   - `stop()` - Stops observer gracefully
   - `run_forever()` - Runs until interrupted with signal handling
   - `_signal_handler()` - Handles SIGINT/SIGTERM for Ctrl+C support

3. **Integration with main.py**
   - Updated `start_watcher()` to use WatcherService
   - Proper vault validation before starting watcher
   - Graceful shutdown on Ctrl+C

All tasks T030-T038 marked complete in tasks.md.

## Outcome

- ✅ Impact: User Story 2 (File System Monitoring) now complete - all 9 tasks finished
- 🧪 Tests: Manual testing needed - drop file in Inbox, verify action file created in Needs_Action
- 📁 Files: file_watcher.py (519 lines), main.py updated, tasks.md updated
- 🔁 Next prompts: T040-T045 - Dashboard and Handbook updates (User Story 3)
- 🧠 Reflection: Implementation follows Constitution standards - OOP, logging, exception handling, local-first

## Evaluation notes (flywheel)

- Failure modes observed: None - implementation complete
- Graders run and results: Pending manual testing
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): Implement T040 DashboardManager updates
