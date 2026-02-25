"""
Fixtures for AI Employee tests.

Provides common test data and helper functions.
"""

import tempfile
import shutil
from pathlib import Path
from typing import Dict, Any

from src.ai_employee.core.vault import VaultManager
from src.ai_employee.config.settings import Settings


def create_test_vault() -> Path:
    """
    Create a temporary test vault.

    Returns:
        Path to the test vault directory
    """
    test_dir = Path(tempfile.mkdtemp())
    vault_path = test_dir / "test_vault"

    vault_manager = VaultManager(str(vault_path))
    vault_manager.create_vault_structure()

    return vault_path


def cleanup_test_vault(vault_path: Path) -> None:
    """
    Clean up a test vault.

    Args:
        vault_path: Path to the vault to clean up
    """
    shutil.rmtree(vault_path.parent, ignore_errors=True)


def create_test_action_file(
    folder_path: Path,
    filename: str = "test_task.md",
    priority: str = "medium",
    status: str = "pending"
) -> Path:
    """
    Create a test action file with YAML frontmatter.

    Args:
        folder_path: Folder to create the file in
        filename: Name of the file
        priority: Task priority (high, medium, low)
        status: Task status (pending, in_progress, done)

    Returns:
        Path to the created file
    """
    content = f"""---
type: test
original_name: {filename}
received: 2026-02-25 10:00:00
priority: {priority}
status: {status}
---

# Test Task

This is a test task file.

## What Needs to Be Done
Test description.

## Suggested Next Steps
- [ ] Step 1
- [ ] Step 2
"""
    file_path = folder_path / filename
    file_path.write_text(content)
    return file_path


def get_test_settings(vault_path: Path) -> Settings:
    """
    Get test settings for a vault.

    Args:
        vault_path: Path to the vault

    Returns:
        Settings object configured for the vault
    """
    settings = Settings()
    settings.VAULT_PATH = str(vault_path)
    settings.WATCHED_FOLDER = str(vault_path / "Inbox")
    return settings
