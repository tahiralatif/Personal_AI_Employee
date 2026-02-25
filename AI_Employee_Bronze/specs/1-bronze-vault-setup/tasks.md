# Implementation Tasks: Bronze Tier AI Employee - Vault Setup

**Feature**: Bronze Tier AI Employee - Vault Setup
**Generated**: 2026-02-24
**Based on**: specs/1-bronze-vault-setup/spec.md, plan.md, data-model.md, research.md

## Overview

This document outlines the implementation tasks for building a local-first AI employee system that monitors a folder for new tasks, processes them using an AI CLI agent, and maintains an Obsidian vault as its brain and dashboard. The system operates entirely offline on a Windows laptop with Ubuntu WSL.

## Implementation Strategy

- **MVP First**: Implement User Story 1 (Local AI Employee Setup) as the minimum viable product
- **Incremental Delivery**: Each user story builds upon the previous, forming independently testable increments
- **Parallel Work**: Identified tasks that can be worked on in parallel (marked with [P])
- **Testable Increments**: Each user story has independent test criteria

## Dependencies

- **User Story 1 (P1)**: Foundation for all other stories - must be completed first
- **User Story 2 (P1)**: Depends on User Story 1 completion
- **User Story 3 (P2)**: Can be implemented in parallel with User Story 2 after User Story 1

## Parallel Execution Examples

- **After User Story 1**: User Story 2 and User Story 3 can be developed in parallel
- **Within User Story 2**: File monitoring and action file creation can be parallelized
- **Within User Story 3**: Dashboard and Handbook creation can be parallelized

---

## Phase 1: Setup Tasks

Initialize the project structure and dependencies.

- [x] T001 Initialize project with uv init and Create project directory structure with src/, tests/, and docs/ folders
- [x] T002 Set up pyproject.toml with uv and dependencies (watchdog, python-dotenv)
- [x] T003 Create .gitignore with proper exclusions for credentials and logs
- [x] T004 [P] Create initial README.md with project overview and setup instructions
- [x] T005 [P] Create .env.example with template for required environment variables

---

## Phase 2: Foundational Tasks

Implement core infrastructure needed by all user stories.

- [x] T010 Implement VaultManager class to handle vault folder structure creation
- [x] T011 Create configuration system using python-dotenv for settings
- [x] T012 Implement logging system that writes to the Logs folder
- [x] T013 Create base file utility functions for safe file operations
- [x] T014 Set up proper exception handling patterns across the application

---

## Phase 3: User Story 1 - Local AI Employee Setup (Priority: P1)

User sets up the AI Employee system locally on their Windows laptop with WSL. They create the vault structure with all required folders and initialize the Python project using uv. This establishes the foundation for the AI employee to operate.

**Independent Test**: Can be fully tested by verifying the vault folder structure exists with all required directories and the Python project is properly initialized with required dependencies.

**Acceptance Scenarios**:
1. Given a Windows laptop with WSL, When user runs the setup commands, Then the ~/AI_Employee_Vault directory is created with all required subdirectories
2. Given the vault directory exists, When user initializes the Python project, Then pyproject.toml is created with watchdog and python-dotenv dependencies

- [x] T020 [US1] Create VaultInitializer class to manage vault folder structure
- [x] T021 [US1] Implement method to create all required vault directories (Inbox, Needs_Action, Done, Plans, Logs)
- [x] T022 [US1] Create method to generate initial Dashboard.md with template structure
- [x] T023 [US1] Create method to generate Company_Handbook.md with required sections
- [x] T024 [US1] Implement CLI command for vault setup in main.py
- [x] T025 [US1] Add validation to check if vault structure already exists

---

## Phase 4: User Story 2 - File System Monitoring (Priority: P1)

User drops a file in the Inbox folder, and the system automatically detects it, creates a structured .md action file in Needs_Action with proper YAML frontmatter, and logs the event in the Logs folder.

**Independent Test**: Can be fully tested by dropping a test file in the Inbox and verifying a corresponding action file is created in Needs_Action with proper format.

**Acceptance Scenarios**:
1. Given a file is dropped in the Inbox folder, When the file watcher detects it, Then a .md file is created in Needs_Action with correct YAML frontmatter within 10 seconds
2. Given a new file is detected, When the DropHandler processes it, Then an entry is logged in the daily log file in the Logs folder

- [x] T030 [US2] Implement FileWatcher class using watchdog library
- [x] T031 [US2] Create FileDropHandler to process incoming files
- [x] T032 [US2] [P] Implement YAML frontmatter generation for action files
- [x] T033 [US2] [P] Create method to sanitize filenames with special characters
- [x] T034 [US2] Implement file size validation (reject files >100MB)
- [x] T035 [US2] Create method to move large files to quarantine folder
- [x] T036 [US2] Implement proper file processing flow from Inbox to Needs_Action
- [x] T037 [US2] Add logging functionality for file processing events
- [x] T038 [US2] Implement graceful shutdown with Ctrl+C support

---

## Phase 5: User Story 3 - Dashboard and Handbook Creation (Priority: P2)

System creates and maintains Dashboard.md to show current status and Company_Handbook.md that contains rules for the AI agent to follow.

**Independent Test**: Can be fully tested by verifying both documents exist with the required content structure.

**Acceptance Scenarios**:
1. Given the vault is initialized, When system starts, Then Dashboard.md exists with proper structure and current status information
2. Given the AI agent needs guidance, When it reads Company_Handbook.md, Then it finds clear rules about what it can/cannot do without approval

- [x] T040 [US3] Enhance DashboardManager to update status information
- [x] T041 [US3] [P] Implement method to count pending tasks in Needs_Action folder
- [x] T042 [US3] [P] Implement method to track completed tasks in Done folder
- [x] T043 [US3] Create CompanyHandbookManager to maintain rules
- [x] T044 [US3] Implement template for Company_Handbook.md with required sections
- [x] T045 [US3] Add functionality to update dashboard with latest activity

---

## Phase 6: Polish & Cross-Cutting Concerns

Final touches and system integration.

- [x] T050 Implement comprehensive error handling across all modules
- [x] T051 Add type hints to all public interfaces
- [x] T052 Create comprehensive documentation for all classes and methods
- [x] T053 Implement proper dependency injection for testability
- [x] T054 Add unit tests for all core functionality
- [x] T055 Create integration tests for end-to-end workflows
- [x] T056 Perform final system validation against all acceptance criteria
- [x] T057 Update README.md with complete usage instructions
- [x] T058 Perform security review to ensure no credentials in code
- [x] T059 Create quick start guide for new users

---

## MVP Scope

The MVP consists of User Story 1 tasks (T020-T025) which establish the foundational vault structure and project initialization. This provides the minimum viable system that can be tested independently.

## Task Completion Criteria

Each task should be marked complete only when:
- Code is implemented and follows project standards
- Unit tests pass (where applicable)
- Code follows OOP principles with proper documentation
- All acceptance criteria are met
- No hardcoded credentials exist in the code