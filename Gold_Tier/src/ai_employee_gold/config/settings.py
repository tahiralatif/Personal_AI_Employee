"""Configuration module for Gold Tier AI Employee system."""
import os
from dataclasses import dataclass
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

@dataclass
class GoldTierSettings:
    """Settings for Gold Tier AI Employee system."""

    # Vault settings
    VAULT_PATH: str = os.getenv("VAULT_PATH", "./AI_Employee_Vault")
    LOGS_DIR: str = os.getenv("LOGS_DIR", "Logs")

    # Claude settings
    CLAUDE_MODEL: str = os.getenv("CLAUDE_MODEL", "claude-3-5-sonnet-latest")

    # Gmail settings
    GMAIL_CREDENTIALS_FILE: str = os.getenv("GMAIL_CREDENTIALS_FILE", "credentials.json")
    GMAIL_TOKEN_FILE: str = os.getenv("GMAIL_TOKEN_FILE", "token.json")

    # WhatsApp settings
    TWILIO_ACCOUNT_SID: Optional[str] = os.getenv("TWILIO_ACCOUNT_SID")
    TWILIO_AUTH_TOKEN: Optional[str] = os.getenv("TWILIO_AUTH_TOKEN")
    TWILIO_WHATSAPP_NUMBER: Optional[str] = os.getenv("TWILIO_WHATSAPP_NUMBER")
    YOUR_PHONE_NUMBER: Optional[str] = os.getenv("YOUR_PHONE_NUMBER")

    # LinkedIn settings
    LINKEDIN_ACCESS_TOKEN: Optional[str] = os.getenv("LINKEDIN_ACCESS_TOKEN")
    LINKEDIN_CLIENT_ID: Optional[str] = os.getenv("LINKEDIN_CLIENT_ID")
    LINKEDIN_CLIENT_SECRET: Optional[str] = os.getenv("LINKEDIN_CLIENT_SECRET")

    # Facebook settings
    FACEBOOK_PAGE_ACCESS_TOKEN: Optional[str] = os.getenv("FACEBOOK_PAGE_ACCESS_TOKEN")
    FACEBOOK_APP_ID: Optional[str] = os.getenv("FACEBOOK_APP_ID")
    FACEBOOK_APP_SECRET: Optional[str] = os.getenv("FACEBOOK_APP_SECRET")

    # Instagram settings
    INSTAGRAM_ACCESS_TOKEN: Optional[str] = os.getenv("INSTAGRAM_ACCESS_TOKEN")
    INSTAGRAM_USER_ID: Optional[str] = os.getenv("INSTAGRAM_USER_ID")

    # Twitter/X settings
    TWITTER_API_KEY: Optional[str] = os.getenv("TWITTER_API_KEY")
    TWITTER_API_SECRET: Optional[str] = os.getenv("TWITTER_API_SECRET")
    TWITTER_ACCESS_TOKEN: Optional[str] = os.getenv("TWITTER_ACCESS_TOKEN")
    TWITTER_ACCESS_SECRET: Optional[str] = os.getenv("TWITTER_ACCESS_SECRET")

    # Odoo settings
    ODOO_URL: Optional[str] = os.getenv("ODOO_URL", "http://localhost:8069")
    ODOO_DB: Optional[str] = os.getenv("ODOO_DB", "odoo_db")
    ODOO_USERNAME: Optional[str] = os.getenv("ODOO_USERNAME")
    ODOO_PASSWORD: Optional[str] = os.getenv("ODOO_PASSWORD")
    ODOO_API_KEY: Optional[str] = os.getenv("ODOO_API_KEY")

    # Security settings
    ENCRYPTION_KEY: Optional[str] = os.getenv("ENCRYPTION_KEY")

    # Scheduler settings
    ENABLE_SCHEDULER: bool = os.getenv("ENABLE_SCHEDULER", "true").lower() == "true"

    # Debug settings
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    VERBOSE_LOGGING: bool = os.getenv("VERBOSE_LOGGING", "false").lower() == "true"

    def __post_init__(self):
        """Validate required settings."""
        if not os.path.exists(self.VAULT_PATH):
            raise ValueError(f"Vault path does not exist: {self.VAULT_PATH}")

    @classmethod
    def load(cls):
        """Load settings from environment variables."""
        return cls()


# Global settings instance
settings = GoldTierSettings.load()