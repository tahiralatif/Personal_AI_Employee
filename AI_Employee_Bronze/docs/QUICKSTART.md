# Quick Start Guide - Bronze Tier AI Employee

Get your AI Employee up and running in 5 minutes!

## Prerequisites Checklist

Before starting, ensure you have:

- [ ] Python 3.12+ installed
- [ ] uv package manager installed
- [ ] Git installed

**Supported Platforms:** Windows, Windows WSL, Linux, macOS

## Step 1: Install Dependencies (2 minutes)

```bash
# Navigate to project directory
cd /path/to/AI_Employee_Bronze

# Create virtual environment
uv venv

# Activate virtual environment
# Windows (PowerShell):
.venv\Scripts\Activate.ps1

# Windows (CMD):
.venv\Scripts\activate

# Linux/macOS/WSL:
source .venv/bin/activate

# Install project dependencies
uv pip install -e .
```

**Verify installation:**
```bash
python -c "from src.ai_employee.core.vault import VaultManager; print('✓ Installation successful')"
```

## Step 2: Configure Environment (1 minute)

```bash
# Copy the example environment file
# Windows (PowerShell):
Copy-Item .env.example .env

# Linux/macOS/WSL:
cp .env.example .env
```

Edit `.env` with your path (use absolute paths):

**Windows:**
```
VAULT_PATH=C:\Users\YourUsername\AI_Employee_Vault
WATCHED_FOLDER=C:\Users\YourUsername\AI_Employee_Vault\Inbox
LOG_LEVEL=INFO
```

**Linux/WSL:**
```
VAULT_PATH=/home/username/AI_Employee_Vault
WATCHED_FOLDER=/home/username/AI_Employee_Vault/Inbox
LOG_LEVEL=INFO
```

**macOS:**
```
VAULT_PATH=/Users/username/AI_Employee_Vault
WATCHED_FOLDER=/Users/username/AI_Employee_Vault/Inbox
LOG_LEVEL=INFO
```

## Step 3: Initialize Vault (30 seconds)

```bash
python main.py setup
```

**Expected output:**
```
✓ Vault structure created successfully
  Location: /home/youruser/AI_Employee_Vault
  Directories: Inbox, Needs_Action, Done, Plans, Logs
  Files: Dashboard.md, Company_Handbook.md
```

**Verify vault created:**
```bash
ls ~/AI_Employee_Vault/
# Should show: Inbox/ Needs_Action/ Done/ Plans/ Logs/ Dashboard.md Company_Handbook.md
```

## Step 4: Start File Watcher (30 seconds)

```bash
python main.py watch
```

**Expected output:**
```
✓ File system watcher started
  Watching: /home/youruser/AI_Employee_Vault/Inbox
  Press Ctrl+C to stop
```

**Keep this terminal running!** The watcher needs to stay active.

## Step 5: Test the System (1 minute)

### Open a new terminal window

```bash
# Drop a test file in the Inbox
echo "Process this invoice from Client A - PKR 5000" > ~/AI_Employee_Vault/Inbox/test_invoice.txt

# Wait 10 seconds, then check Needs_Action folder
ls ~/AI_Employee_Vault/Needs_Action/
```

**Expected:** You should see a file like:
```
FILE_20260225_103045_test_invoice.txt.md
```

### Check the action file content:

```bash
cat ~/AI_Employee_Vault/Needs_Action/FILE_*_test_invoice.txt.md
```

**Expected output:**
```markdown
---
type: file_drop
original_name: test_invoice.txt
received: 2026-02-25 10:30:45
priority: medium
status: pending
---

# Task: Process test_invoice.txt

## What Needs to Be Done
...
```

### Check the Dashboard:

```bash
cat ~/AI_Employee_Vault/Dashboard.md
```

**Expected:** Dashboard should show "Pending Tasks: 1"

### Check the Logs:

```bash
cat ~/AI_Employee_Vault/Logs/$(date +%Y-%m-%d).log
```

**Expected:** Log entries showing file detection and processing.

## Success Criteria

Your AI Employee is working correctly if:

- ✅ Vault structure exists with all 5 folders
- ✅ Dashboard.md and Company_Handbook.md exist
- ✅ Watcher detects files within 10 seconds
- ✅ Action files are created in Needs_Action/
- ✅ Activity is logged in Logs/YYYY-MM-DD.log
- ✅ Dashboard shows correct pending task count

## Next Steps

### Using the AI CLI Agent

If you have an AI CLI agent (like Claude Code) set up:

1. Navigate to the vault:
   ```bash
   cd ~/AI_Employee_Vault
   ```

2. Launch your AI agent:
   ```bash
   claude --cwd .
   ```

3. Give it this prompt:
   ```
   Read Company_Handbook.md first and follow its rules.

   Task:
   1. Read all files in /Needs_Action
   2. For each file, create a Plan.md in /Plans/
   3. Update Dashboard.md with summary
   4. Move processed files to /Done/

   Start working.
   ```

### Stopping the Watcher

Press `Ctrl+C` in the terminal where the watcher is running.

### Restarting Later

```bash
# Activate virtual environment
source .venv/bin/activate

# Start watcher
python main.py watch
```

## Common Issues

### "Module not found" error
**Solution:** Make sure virtual environment is activated:
```bash
source .venv/bin/activate
```

### "Vault already exists" message
**Solution:** This is normal if you've already run setup. The vault is reusable!

### Watcher doesn't detect files
**Solution:** 
1. Check watcher is running (you should see "Watcher started" message)
2. Verify file was dropped in correct Inbox folder
3. Check logs for errors

### Permission denied errors
**Solution:** Ensure you have write permissions:
```bash
chmod -R u+w ~/AI_Employee_Vault
```

## Cleanup (if needed)

To remove the test vault and start fresh:

```bash
rm -rf ~/AI_Employee_Vault
python main.py setup  # Recreate
```

## Getting Help

- Read the full [README.md](../README.md) for detailed documentation
- Check [Company_Handbook.md](~/AI_Employee_Vault/Company_Handbook.md) for AI agent rules
- Review [spec.md](../specs/1-bronze-vault-setup/spec.md) for requirements

---

**Congratulations! Your AI Employee is ready to work! 🎉**
