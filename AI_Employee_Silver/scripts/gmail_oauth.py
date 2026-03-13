"""
Gmail OAuth Authentication Script

Is script ko run karein aur browser mein login complete karein.
"""

import sys
from pathlib import Path

# Add project to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.ai_employee_silver.integrations.gmail_watcher import GmailWatcher
from src.ai_employee_silver.config.settings import get_settings
from src.ai_employee_silver.utils.logger import get_logger

def main():
    print("=" * 60)
    print("GMAIL OAUTH AUTHENTICATION")
    print("=" * 60)
    print()
    print("Yeh script apko Gmail API se connect karegi.")
    print()
    print("STEPS:")
    print("1. Browser automatically open hoga")
    print("2. Apne Gmail account se login karein")
    print("3. 'Allow access' pe click karein")
    print("4. Token automatically save ho jayega")
    print()
    print("=" * 60)
    print()
    
    # Get settings and logger
    settings = get_settings()
    logger = get_logger()
    
    # Create GmailWatcher
    watcher = GmailWatcher(settings, logger)
    
    print("Starting OAuth flow...")
    print()
    
    # Authenticate
    result = watcher.authenticate()
    
    if result:
        print()
        print("=" * 60)
        print("SUCCESS! Gmail OAuth complete ho gaya!")
        print("=" * 60)
        print()
        print("Token save ho gaya hai:")
        token_path = project_root / "token.json"
        print(f"  {token_path}")
        print()
        print("Ab Gmail watcher automatically emails check karega!")
        print()
    else:
        print()
        print("=" * 60)
        print("FAILED! OAuth complete nahi hua.")
        print("=" * 60)
        print()
        print("Possible reasons:")
        print("  - Browser open nahi hua")
        print("  - Login cancel kiya")
        print("  - Network issue")
        print()
        print("Retry karein ya check karein:")
        print(f"  - GMAIL_CLIENT_ID: {settings.GMAIL_CLIENT_ID[:20]}...")
        print(f"  - GMAIL_CLIENT_SECRET: {settings.GMAIL_CLIENT_SECRET[:10]}...")
        print()

if __name__ == "__main__":
    main()
