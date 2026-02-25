# Quickstart Guide: Bronze Tier AI Employee - Vault Setup

## Prerequisites

- Windows 11 with Ubuntu WSL installed
- Python 3.12+ available in WSL
- uv package manager installed
- Access to LM Studio running on localhost:1234 for local AI model

## Installation Steps

1. **Clone the repository:**
   ```bash
   git clone https://github.com/tahiralatif/Personal_AI_Employee.git
   cd Personal_AI_Employee
   git checkout feature/bronze-vault-setup
   ```

2. **Install dependencies using uv:**
   ```bash
   uv venv
   source .venv/bin/activate  # On Windows WSL
   uv pip install watchdog python-dotenv
   ```

3. **Set up the project structure:**
   ```bash
   # Initialize the project with uv
   uv init
   # The setup script will create the required directory structure
   ```

4. **Configure environment variables:**
   Create a `.env` file in the project root (this will be ignored by Git):
   ```
   VAULT_PATH=~/AI_Employee_Vault
   WATCHED_FOLDER=~/AI_Employee_Vault/Inbox
   LM_STUDIO_HOST=localhost
   LM_STUDIO_PORT=1234
   LOG_LEVEL=INFO
   ```

5. **Run the vault setup:**
   ```bash
   python -m src.ai_employee.main setup
   ```

## Initial Setup

The setup process will:

1. Create the complete vault folder structure:
   ```
   ~/AI_Employee_Vault/
   ├── Inbox/              # New unprocessed items
   ├── Needs_Action/       # Tasks ready for Claude
   ├── Done/               # Completed tasks only
   ├── Plans/              # Claude-generated plans
   ├── Logs/               # All action logs
   ├── Dashboard.md        # Always up to date
   └── Company_Handbook.md # Claude's rules
   ```

2. Initialize the required documentation files:
   - `Dashboard.md` with initial structure
   - `Company_Handbook.md` with template sections for authorized actions, prohibited actions, and escalation procedures

## Running the System

1. **Start the file watcher:**
   ```bash
   python -m src.ai_employee.main watch
   ```

2. **The system will:**
   - Monitor the Inbox folder for new files
   - When a file is detected, create a structured .md action file in Needs_Action
   - Include YAML frontmatter with type, original_name, received timestamp, priority, and status
   - Log the event to the daily log file in the Logs folder

3. **To stop the system:**
   Press `Ctrl+C` to stop the watcher gracefully

## Testing the Setup

1. **Verify vault structure:**
   ```bash
   ls -la ~/AI_Employee_Vault/
   ```

2. **Test file processing:**
   - Place a test file in the Inbox folder
   - Verify that a corresponding .md file appears in Needs_Action within 10 seconds
   - Check the log file in the Logs folder for the event

3. **Check dashboard:**
   - Open Dashboard.md to verify it shows the current system status

## Troubleshooting

- **File watcher not detecting changes:**
  - Ensure the system has read/write permissions to the vault directory
  - Verify the path in your `.env` file matches the actual vault location

- **Large files not being handled properly:**
  - Files >100MB should be moved to a quarantine folder
  - Check the logs for error messages about file size

- **Special characters in filenames:**
  - Files with special characters should have them sanitized (replaced with underscores)
  - Verify this behavior during testing

## Next Steps

Once the Bronze Tier is operational:

1. Manually invoke the AI CLI agent when files appear in Needs_Action
2. Monitor the system's performance and logs
3. Prepare for Silver Tier integration (Gmail, LinkedIn, etc.)