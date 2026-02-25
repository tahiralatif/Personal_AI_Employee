# Bronze Tier AI Employee - Vault Setup

## Feature Description

Build a Minimum Viable AI Employee that runs entirely on a local Windows laptop (Ubuntu WSL). It monitors a local folder for new tasks, processes them using an AI CLI agent, and keeps an Obsidian vault updated as its brain and dashboard. The system must work offline — no cloud, no external APIs in Bronze Tier. All intelligence is delivered through an AI CLI agent invoked manually.

## User Scenarios & Testing

### User Story 1 - Local AI Employee Setup (Priority: P1)

User sets up the AI Employee system locally on their Windows laptop with WSL. They create the vault structure with all required folders and initialize the Python project using uv. This establishes the foundation for the AI employee to operate.

**Why this priority**: This is the foundational setup that enables all other functionality. Without the vault structure and project initialization, no other features can work.

**Independent Test**: Can be fully tested by verifying the vault folder structure exists with all required directories and the Python project is properly initialized with required dependencies.

**Acceptance Scenarios**:

1. **Given** a Windows laptop with WSL, **When** user runs the setup commands, **Then** the ~/AI_Employee_Vault directory is created with all required subdirectories
2. **Given** the vault directory exists, **When** user initializes the Python project, **Then** pyproject.toml is created with watchdog and python-dotenv dependencies

---

### User Story 2 - File System Monitoring (Priority: P1)

User drops a file in the Inbox folder, and the system automatically detects it, creates a structured .md action file in Needs_Action with proper YAML frontmatter, and logs the event in the Logs folder.

**Why this priority**: This is the core functionality that enables the AI employee to respond to tasks. Without file monitoring, the system is passive and unusable.

**Independent Test**: Can be fully tested by dropping a test file in the Inbox and verifying a corresponding action file is created in Needs_Action with proper format.

**Acceptance Scenarios**:

1. **Given** a file is dropped in the Inbox folder, **When** the file watcher detects it, **Then** a .md file is created in Needs_Action with correct YAML frontmatter within 10 seconds
2. **Given** a new file is detected, **When** the DropHandler processes it, **Then** an entry is logged in the daily log file in the Logs folder

---

### User Story 3 - Dashboard and Handbook Creation (Priority: P2)

System creates and maintains Dashboard.md to show current status and Company_Handbook.md that contains rules for the AI agent to follow.

**Why this priority**: These documents provide the foundation for AI behavior and system visibility. The handbook ensures the AI follows proper protocols.

**Independent Test**: Can be fully tested by verifying both documents exist with the required content structure.

**Acceptance Scenarios**:

1. **Given** the vault is initialized, **When** system starts, **Then** Dashboard.md exists with proper structure and current status information
2. **Given** the AI agent needs guidance, **When** it reads Company_Handbook.md, **Then** it finds clear rules about what it can/cannot do without approval

---

### Edge Cases

- What happens when the Inbox receives a large file (>100MB)? -> Large files should be moved to a quarantine folder
- How does the system handle files with special characters in the name? -> Special characters should be sanitized by replacing with underscores
- What if the Logs directory becomes full?
- How does the system behave when the AI agent is processing multiple files simultaneously?

## Requirements

### Functional Requirements

- **FR-001**: System MUST create the complete vault folder structure with all required directories
- **FR-002**: System MUST initialize a Python project with uv package manager and required dependencies
- **FR-003**: System MUST monitor the Inbox folder for new files using the watchdog library
- **FR-004**: System MUST create properly formatted .md action files in Needs_Action when new files are detected
- **FR-005**: System MUST include YAML frontmatter in created action files with only essential fields: type, original_name, received timestamp, priority, and status
- **FR-006**: System MUST log all file detection events to daily log files in the Logs folder
- **FR-007**: System MUST create and maintain Dashboard.md with current status information
- **FR-008**: System MUST create Company_Handbook.md with a template containing sections for authorized actions, prohibited actions, escalation procedures
- **FR-009**: System MUST handle KeyboardInterrupt gracefully and stop cleanly with Ctrl+C
- **FR-010**: System MUST move processed files from Needs_Action to Done folder after processing (when AI marks status as "completed" in the action file)

### Non-functional Requirements

- **NFR-001**: System MUST run locally on Windows with Ubuntu WSL without requiring internet connection
- **NFR-002**: File detection and action file creation MUST occur within 10 seconds of file drop
- **NFR-003**: System MUST handle files up to 100MB in size
- **NFR-004**: Python code MUST follow OOP standards with classes, type hints, and docstrings
- **NFR-005**: System MUST NOT store any credentials in the vault or commit them to Git

### Key Entities

- **Task File**: Represents a file dropped in the Inbox that needs processing; has attributes like original name, received time, priority, and status
- **Action File**: Structured .md file created in Needs_Action from incoming task files; contains YAML frontmatter with metadata
- **Log Entry**: Record of system activity with timestamp, action type, detail, and result
- **Dashboard**: Central document showing system status, pending tasks, and quick links
- **Handbook**: Document containing rules and guidelines for AI agent behavior

## Success Criteria

### Measurable Outcomes

- **SC-001**: User can set up the complete vault structure with all required directories in under 5 minutes
- **SC-002**: File dropped in Inbox creates a properly formatted .md file in Needs_Action within 10 seconds
- **SC-003**: All Python classes have docstrings and type hints as required by OOP standards
- **SC-004**: System logs every file detection event with timestamp and file name
- **SC-005**: Dashboard.md shows accurate counts of pending tasks and last action
- **SC-006**: No credentials exist anywhere in vault or Git repository
- **SC-007**: All 3 SKILL.md files exist and are readable by AI agent
- **SC-008**: uv run python src/ai_employee/main.py starts with no errors

## Assumptions

- User has Windows 11 with Ubuntu WSL installed
- User has Python 3.12+ available in WSL
- User has uv package manager installed
- User has access to LM Studio running on localhost:1234 for local AI model
- User will manually invoke the AI CLI agent when needed
- The system operates in offline mode during Bronze tier

## Dependencies

- Python 3.12+
- uv package manager
- watchdog library
- python-dotenv library
- Ubuntu WSL (on Windows)
- LM Studio for local AI model (localhost:1234)
- AI CLI agent for processing tasks

## Out of Scope

- Gmail integration (Silver Tier)
- WhatsApp monitoring (Silver Tier)
- Email sending capabilities (Silver Tier)
- LinkedIn posting (Silver Tier)
- Scheduled cron jobs (Silver Tier)
- MCP servers (Silver Tier)
- Payment automation (Gold Tier)
- CEO Briefing generation (Gold Tier)
- Cloud deployment (Platinum Tier)
- Multi-agent coordination (Platinum Tier)

## Clarifications

### Session 2026-02-24

- Q: What is the expected behavior when a file larger than 100MB is dropped in the Inbox? → A: Move the large file to a quarantine folder
- Q: What specific fields should be included in the YAML frontmatter? → A: Only the essential fields mentioned (type, original_name, received timestamp, priority, status)
- Q: How should the system determine when a file has been "processed"? → A: When AI marks status as "completed" in the action file
- Q: What approach should be taken for file names with special characters? → A: Sanitize by replacing special characters with underscores
- Q: What should be the default content or structure for the handbook? → A: Template with sections for authorized actions, prohibited actions, escalation procedures