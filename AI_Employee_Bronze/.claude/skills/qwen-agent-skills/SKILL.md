# Qwen AI Employee Skills

**Version**: 1.0  
**Brain**: Qwen AI (via LM Studio)  
**Last Updated**: 2026-03-07

---

## Overview

This skill pack enables Qwen AI to function as an autonomous AI employee with the following capabilities:

- Read and process tasks from the vault
- Create action plans
- Request human approval for sensitive actions
- Execute autonomous tasks
- Update dashboard and logs

---

## Prerequisites

1. **LM Studio** running on `localhost:1234`
2. **Qwen Model** loaded (recommended: `qwen-2.5-coder-32b` or similar)
3. **Python 3.12+** with dependencies installed
4. **Vault structure** initialized

---

## Agent Skills

### 1. `read_needs_action`

**Purpose**: Read all pending tasks from the Needs_Action folder.

**Usage**:
```python
from ai_employee.integrations.qwen_brain import QwenBrain

brain = QwenBrain(vault_path="/path/to/vault")
tasks = brain.read_needs_action()

for task in tasks:
    print(f"Task: {task.name}")
```

**Returns**: List of file paths in Needs_Action folder.

---

### 2. `process_task`

**Purpose**: Process a single task file using Qwen AI.

**Usage**:
```python
success, message = brain.process_task(task_file)
print(f"Result: {message}")
```

**Action Types**:
- `APPROVAL_REQUIRED` - Task needs human approval
- `AUTONOMOUS` - Task can be completed automatically
- `REJECT` - Task cannot be processed

**Returns**: Tuple of (success: bool, message: str)

---

### 3. `process_all_tasks`

**Purpose**: Process all tasks in Needs_Action folder.

**Usage**:
```python
results = brain.process_all_tasks()
print(f"Processed: {results['processed']}")
print(f"Success: {results['success']}")
print(f"Approval Required: {results['approval_required']}")
```

**Returns**: Dictionary with processing statistics.

---

### 4. `create_plan`

**Purpose**: Create an action plan in the Plans folder.

**Usage**:
```python
plan_path = brain._create_plan(
    task_name="task_file.md",
    action={"plan": "Step-by-step plan...", "next_step": "Execute and move to Done"}
)
```

**Returns**: Path to created plan file.

---

### 5. `create_approval_request`

**Purpose**: Create an approval request in Pending_Approval folder.

**Usage**:
```python
approval_path = brain._create_approval_request(
    task_name="payment_task.md",
    action={"reason": "Payment > PKR 1,000", "plan": "Process payment..."}
)
```

**Returns**: Path to created approval request file.

---

### 6. `ralph_loop`

**Purpose**: Keep Qwen working until all tasks are complete.

**Usage**:
```python
from ai_employee.integrations.ralph_loop import ralph_loop

results = ralph_loop(
    vault_path="/path/to/vault",
    max_iterations=10,
    check_interval=5
)

print(f"Completed: {results['completed']}")
```

**Features**:
- Automatically processes all tasks
- Re-injects context on each iteration
- Stops when all tasks complete or max iterations reached
- Updates dashboard after each iteration

---

## CLI Commands

### Process All Tasks

```bash
cd AI_Employee_Bronze
uv run python -m src.ai_employee.integrations.qwen_brain
```

### Run Ralph Wiggum Loop

```bash
uv run python -m src.ai_employee.integrations.ralph_loop
```

---

## Integration with main.py

Add these commands to `main.py`:

```python
# Process command
elif args.command == "process":
    brain = create_qwen_brain()
    results = brain.process_all_tasks()
    print(f"Processed: {results['processed']}")
    print(f"Success: {results['success']}")

# Ralph loop command
elif args.command == "ralph":
    results = ralph_loop()
    if results['completed']:
        print("✅ All tasks complete!")
    else:
        print(f"⚠️ {results['reason']}")
```

---

## File Operations

### Read Files
```python
# Read any file in vault
content = Path("/path/to/vault/Needs_Action/task.md").read_text()
```

### Create Files
```python
# Create plan
Path("/path/to/vault/Plans/PLAN_001.md").write_text(content)

# Create approval request
Path("/path/to/vault/Pending_Approval/APPROVAL_001.md").write_text(content)
```

### Move Files
```python
# Move to Done
source.rename(Path("/path/to/vault/Done/task.md"))
```

### Update Dashboard
```python
from ai_employee.core.vault import DashboardManager

dashboard = DashboardManager(vault_path)
dashboard.update_dashboard(last_action="Processed 5 tasks")
```

---

## Approval Workflow

### When to Request Approval

| Action | Threshold | Approval Required |
|--------|-----------|-------------------|
| Payment | > PKR 1,000 | ✅ Yes |
| Payment | <= PKR 1,000 | ❌ No (auto) |
| Email Send | Any | ✅ Yes |
| File Delete | Any | ✅ Yes |
| Unknown Contact | Any | ✅ Yes |
| Task from Needs_Action | Simple | ❌ No (auto) |

### Approval Request Format

```markdown
---
type: approval_request
task_file: payment_invoice.md
created: 2026-03-07T10:30:00
status: pending
action_type: Payment processing
---

# Approval Request

## Task
payment_invoice.md

## Reason for Approval
Payment amount exceeds PKR 1,000 threshold

## Suggested Plan
1. Verify invoice details
2. Process payment via bank API
3. Move to Done

## To Approve
Move this file to `/Approved` folder.

## To Reject
Move this file to `/Rejected` folder with reason.
```

---

## Error Handling

### Common Errors

| Error | Cause | Solution |
|-------|-------|----------|
| `Cannot connect to LM Studio` | LM Studio not running | Start LM Studio on localhost:1234 |
| `No tasks to process` | Needs_Action is empty | Add files to Needs_Action folder |
| `Max iterations reached` | Tasks stuck in loop | Review Company_Handbook.md rules |

### Error Recovery

```python
try:
    results = brain.process_all_tasks()
except Exception as e:
    logger.error(f"Processing failed: {str(e)}")
    # Move stuck tasks to Quarantine
    # Alert human for review
```

---

## Best Practices

1. **Always log actions** - Use logger for all operations
2. **Request approval early** - When in doubt, ask for approval
3. **Update dashboard** - Keep Dashboard.md current
4. **Move completed tasks** - Don't leave files in In_Progress
5. **Handle errors gracefully** - Don't crash on bad input

---

## Testing

### Unit Test Example

```python
def test_qwen_brain_process_task():
    brain = create_qwen_brain(vault_path="/tmp/test_vault")
    
    # Create test task
    task_file = brain.needs_action_path / "test_task.md"
    task_file.write_text("---\ntype: test\n---\n\nTest task")
    
    # Process task
    success, message = brain.process_task(task_file)
    
    assert success == True
    assert "Done" in message or "Approval" in message
```

### Integration Test

```python
def test_ralph_loop():
    results = ralph_loop(
        vault_path="/tmp/test_vault",
        max_iterations=3
    )
    
    assert results['iterations'] <= 3
    assert results['total_processed'] >= 0
```

---

## Troubleshooting

### Qwen not responding

1. Check LM Studio is running: `curl http://localhost:1234/v1/models`
2. Verify model is loaded in LM Studio
3. Check firewall settings for port 1234

### Tasks not moving to Done

1. Check file permissions
2. Verify task was processed successfully
3. Review logs in Logs/YYYY-MM-DD.log

### Approval requests not created

1. Check action parsing logic
2. Verify task requires approval
3. Review Qwen's response format

---

## Related Files

- `src/ai_employee/integrations/qwen_brain.py` - Main Qwen integration
- `src/ai_employee/integrations/ralph_loop.py` - Ralph Wiggum loop
- `src/ai_employee/core/vault.py` - Vault management
- `Company_Handbook.md` - AI rules and guidelines

---

*Generated for AI Employee Bronze Tier - Qwen Brain Integration*
