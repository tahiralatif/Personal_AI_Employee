"""
Configuration management for the AI Employee system.

This module handles loading and managing configuration settings using python-dotenv.
"""

import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv


class Settings:
    """
    Configuration settings for the AI Employee system.
    """

    def __init__(self, env_file: str = ".env"):
        """
        Initialize settings by loading from environment variables.

        Args:
            env_file: Path to the .env file to load
        """
        # Load environment variables from .env file
        env_path = Path(env_file)
        if env_path.exists():
            load_dotenv(dotenv_path=env_path)
        else:
            # If .env file doesn't exist, still load any existing environment variables
            load_dotenv()

        # Vault settings
        self.VAULT_PATH = self._get_env_var('VAULT_PATH', '~/AI_Employee_Vault')
        self.WATCHED_FOLDER = self._get_env_var('WATCHED_FOLDER', f'{self.VAULT_PATH}/Inbox')

        # Qwen AI settings
        self.QWEN_COMMAND = self._get_env_var('QWEN_COMMAND', 'qwen')

        # Logging settings
        self.LOG_LEVEL = self._get_env_var('LOG_LEVEL', 'INFO')

        # Application settings
        self.MAX_FILE_SIZE = int(self._get_env_var('MAX_FILE_SIZE', '104857600'))  # 100MB in bytes
        self.CUSTOM_PROMPT_PATH = self._get_env_var('CUSTOM_PROMPT_PATH', './prompts/default.txt')

        # Validation
        self._validate_settings()

    def _get_env_var(self, key: str, default_value: str) -> str:
        """
        Get an environment variable with a default value.

        Args:
            key: Environment variable key
            default_value: Default value if key is not found

        Returns:
            Value of the environment variable or default value
        """
        return os.getenv(key, default_value)

    def _validate_settings(self):
        """
        Validate the loaded settings.
        """
        # Validate paths
        vault_path = Path(self.VAULT_PATH).expanduser()
        if not vault_path.is_absolute():
            raise ValueError(f"VAULT_PATH must be an absolute path: {self.VAULT_PATH}")

        watched_folder = Path(self.WATCHED_FOLDER).expanduser()
        if not watched_folder.is_absolute():
            raise ValueError(f"WATCHED_FOLDER must be an absolute path: {self.WATCHED_FOLDER}")

        # Validate Qwen command
        if not self.QWEN_COMMAND or not isinstance(self.QWEN_COMMAND, str):
            raise ValueError(f"QWEN_COMMAND must be a valid command: {self.QWEN_COMMAND}")

        # Validate log level
        valid_log_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if self.LOG_LEVEL.upper() not in valid_log_levels:
            raise ValueError(f"LOG_LEVEL must be one of {valid_log_levels}: {self.LOG_LEVEL}")

        # Validate max file size
        if self.MAX_FILE_SIZE <= 0:
            raise ValueError(f"MAX_FILE_SIZE must be positive: {self.MAX_FILE_SIZE}")

    @property
    def vault_path_expanded(self) -> Path:
        """
        Get the expanded vault path (with ~ replaced by home directory).

        Returns:
            Expanded vault path as a Path object
        """
        return Path(self.VAULT_PATH).expanduser()

    @property
    def watched_folder_expanded(self) -> Path:
        """
        Get the expanded watched folder path (with ~ replaced by home directory).

        Returns:
            Expanded watched folder path as a Path object
        """
        return Path(self.WATCHED_FOLDER).expanduser()

    def __repr__(self):
        """
        String representation of the settings (excluding sensitive data).
        """
        return (
            f"Settings(VAULT_PATH={self.VAULT_PATH}, "
            f"QWEN_COMMAND={self.QWEN_COMMAND}, "
            f"LOG_LEVEL={self.LOG_LEVEL})"
        )


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """
    Get the global settings instance.

    Returns:
        Settings instance
    """
    return settings


if __name__ == "__main__":
    # Example usage
    config = Settings()
    print(config)
    print(f"Vault path: {config.vault_path_expanded}")
    print(f"Watched folder: {config.watched_folder_expanded}")