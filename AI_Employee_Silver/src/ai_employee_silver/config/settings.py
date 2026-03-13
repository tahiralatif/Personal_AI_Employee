"""
Settings loader for Silver Tier AI Employee.

Loads environment variables from .env file and provides type-safe access
to configuration values.
"""

import os
from pathlib import Path
from typing import Optional, List
from dotenv import load_dotenv


class Settings:
    """
    Application settings loaded from environment variables.

    Attributes:
        VAULT_PATH: Path to the AI Employee vault
        WATCHED_FOLDER: Path to the Inbox folder
        LOG_LEVEL: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)

        # Gmail API
        GMAIL_CLIENT_ID: OAuth 2.0 client ID
        GMAIL_CLIENT_SECRET: OAuth 2.0 client secret
        GMAIL_REDIRECT_URI: OAuth redirect URI
        GMAIL_SCOPES: Gmail API scopes
        GMAIL_ACCOUNT_EMAIL: Gmail account email
        GMAIL_POLL_INTERVAL: Polling interval in seconds

        # WhatsApp API
        WHATSAPP_BUSINESS_ACCOUNT_ID: Business account ID
        WHATSAPP_ACCESS_TOKEN: Access token
        WHATSAPP_PHONE_NUMBER_ID: Phone number ID
        WHATSAPP_API_VERSION: API version
        WHATSAPP_WEBHOOK_VERIFY_TOKEN: Webhook verify token
        WHATSAPP_POLL_INTERVAL: Polling interval in seconds
        WHATSAPP_TASK_KEYWORDS: Task detection keywords

        # LinkedIn API
        LINKEDIN_CLIENT_ID: API client ID
        LINKEDIN_CLIENT_SECRET: API client secret
        LINKEDIN_ACCESS_TOKEN: OAuth access token
        LINKEDIN_ORGANIZATION_ID: Organization ID for company posts
        LINKEDIN_API_VERSION: API version

        # Scheduler
        SCHEDULER_TIMEZONE: Timezone for scheduled tasks
        SCHEDULER_HOLIDAY_DETECTION: Enable holiday detection
        SCHEDULER_HOLIDAY_REGION: Holiday calendar region

        # MCP
        MCP_ENABLED: Enable MCP coordination
        MCP_SERVER_URLS: List of MCP server URLs
        MCP_SERVER_API_KEYS: List of API keys
        MCP_FILE_LOCK_TIMEOUT: File lock timeout in seconds

        # Retry Configuration
        MAX_RETRY_ATTEMPTS: Maximum retry attempts
        RETRY_INITIAL_DELAY: Initial retry delay in seconds
        RETRY_MAX_DELAY: Maximum retry delay in seconds
        RETRY_EXPONENTIAL_BACKOFF: Enable exponential backoff
    """

    def __init__(self, env_path: Optional[str] = None) -> None:
        """
        Initialize settings by loading from .env file.

        Args:
            env_path: Optional path to .env file (default: .env in project root)
        """
        # Load .env file
        if env_path:
            load_dotenv(env_path)
        else:
            # Try to find .env in project root
            project_root = Path(__file__).parent.parent.parent.parent
            env_file = project_root / ".env"
            if env_file.exists():
                load_dotenv(env_file)

        # Vault Configuration
        self.VAULT_PATH = self._get_required("VAULT_PATH")
        self.WATCHED_FOLDER = self._get_required("WATCHED_FOLDER")
        self.LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

        # Gmail API
        self.GMAIL_CLIENT_ID = os.getenv("GMAIL_CLIENT_ID", "")
        self.GMAIL_CLIENT_SECRET = os.getenv("GMAIL_CLIENT_SECRET", "")
        self.GMAIL_REDIRECT_URI = os.getenv("GMAIL_REDIRECT_URI", "http://localhost:8080")
        self.GMAIL_SCOPES = os.getenv("GMAIL_SCOPES", "https://www.googleapis.com/auth/gmail.readonly")
        self.GMAIL_ACCOUNT_EMAIL = os.getenv("GMAIL_ACCOUNT_EMAIL", "")
        self.GMAIL_POLL_INTERVAL = int(os.getenv("GMAIL_POLL_INTERVAL", "60"))

        # WhatsApp API
        self.WHATSAPP_BUSINESS_ACCOUNT_ID = os.getenv("WHATSAPP_BUSINESS_ACCOUNT_ID", "")
        self.WHATSAPP_ACCESS_TOKEN = os.getenv("WHATSAPP_ACCESS_TOKEN", "")
        self.WHATSAPP_PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID", "")
        self.WHATSAPP_API_VERSION = os.getenv("WHATSAPP_API_VERSION", "v18.0")
        self.WHATSAPP_WEBHOOK_VERIFY_TOKEN = os.getenv("WHATSAPP_WEBHOOK_VERIFY_TOKEN", "")
        self.WHATSAPP_POLL_INTERVAL = int(os.getenv("WHATSAPP_POLL_INTERVAL", "30"))
        self.WHATSAPP_TASK_KEYWORDS = self._parse_list(
            os.getenv("WHATSAPP_TASK_KEYWORDS", "please,need,urgent,task,action,required,must,should")
        )

        # Twilio WhatsApp API (Sandbox)
        self.TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID", "")
        self.TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", "")
        self.TWILIO_WHATSAPP_NUMBER = os.getenv("TWILIO_WHATSAPP_NUMBER", "")
        self.YOUR_PHONE_NUMBER = os.getenv("YOUR_PHONE_NUMBER", "")

        # LinkedIn API
        self.LINKEDIN_CLIENT_ID = os.getenv("LINKEDIN_CLIENT_ID", "")
        self.LINKEDIN_CLIENT_SECRET = os.getenv("LINKEDIN_CLIENT_SECRET", "")
        self.LINKEDIN_ACCESS_TOKEN = os.getenv("LINKEDIN_ACCESS_TOKEN", "")
        self.LINKEDIN_ORGANIZATION_ID = os.getenv("LINKEDIN_ORGANIZATION_ID", "")
        self.LINKEDIN_API_VERSION = os.getenv("LINKEDIN_API_VERSION", "202402")
        # LinkedIn Playwright (browser-based) credentials
        self.LINKEDIN_EMAIL = os.getenv("LINKEDIN_EMAIL", "")
        self.LINKEDIN_PASSWORD = os.getenv("LINKEDIN_PASSWORD", "")

        # Scheduler
        self.SCHEDULER_TIMEZONE = os.getenv("SCHEDULER_TIMEZONE", "UTC")
        self.SCHEDULER_HOLIDAY_DETECTION = os.getenv("SCHEDULER_HOLIDAY_DETECTION", "false").lower() == "true"
        self.SCHEDULER_HOLIDAY_REGION = os.getenv("SCHEDULER_HOLIDAY_REGION", "")

        # MCP
        self.MCP_ENABLED = os.getenv("MCP_ENABLED", "false").lower() == "true"
        self.MCP_SERVER_URLS = self._parse_list(os.getenv("MCP_SERVER_URLS", ""))
        self.MCP_SERVER_API_KEYS = self._parse_list(os.getenv("MCP_SERVER_API_KEYS", ""))
        self.MCP_FILE_LOCK_TIMEOUT = int(os.getenv("MCP_FILE_LOCK_TIMEOUT", "30"))

        # Retry Configuration
        self.MAX_RETRY_ATTEMPTS = int(os.getenv("MAX_RETRY_ATTEMPTS", "3"))
        self.RETRY_INITIAL_DELAY = float(os.getenv("RETRY_INITIAL_DELAY", "1.0"))
        self.RETRY_MAX_DELAY = float(os.getenv("RETRY_MAX_DELAY", "60.0"))
        self.RETRY_EXPONENTIAL_BACKOFF = os.getenv("RETRY_EXPONENTIAL_BACKOFF", "true").lower() == "true"

    def _get_required(self, key: str) -> str:
        """
        Get a required environment variable.

        Args:
            key: Environment variable name

        Returns:
            Environment variable value

        Raises:
            ValueError: If environment variable is not set
        """
        value = os.getenv(key)
        if not value:
            raise ValueError(f"Required environment variable {key} is not set")
        return value

    def _parse_list(self, value: str) -> List[str]:
        """
        Parse a comma-separated list.

        Args:
            value: Comma-separated string

        Returns:
            List of strings
        """
        if not value:
            return []
        return [item.strip() for item in value.split(",")]

    def is_gmail_configured(self) -> bool:
        """Check if Gmail API is configured."""
        return bool(self.GMAIL_CLIENT_ID and self.GMAIL_CLIENT_SECRET)

    def is_whatsapp_configured(self) -> bool:
        """Check if WhatsApp API is configured."""
        return bool(
            self.WHATSAPP_BUSINESS_ACCOUNT_ID and
            self.WHATSAPP_ACCESS_TOKEN and
            self.WHATSAPP_PHONE_NUMBER_ID
        )

    def is_linkedin_configured(self) -> bool:
        """Check if LinkedIn API is configured."""
        return bool(
            self.LINKEDIN_CLIENT_ID and
            self.LINKEDIN_CLIENT_SECRET and
            self.LINKEDIN_ACCESS_TOKEN
        )

    def is_scheduler_enabled(self) -> bool:
        """Check if scheduler is enabled."""
        return True  # Scheduler is always available

    def is_mcp_enabled(self) -> bool:
        """Check if MCP coordination is enabled."""
        return self.MCP_ENABLED and len(self.MCP_SERVER_URLS) > 0


# Global settings instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """
    Get the global settings instance.

    Returns:
        Settings instance
    """
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


def reload_settings() -> Settings:
    """
    Reload settings from .env file.

    Returns:
        New Settings instance
    """
    global _settings
    _settings = Settings()
    return _settings
