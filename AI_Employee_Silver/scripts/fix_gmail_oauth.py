"""
Quick fix script for Gmail OAuth redirect_uri_mismatch

Is script ko run karein aur yeh:
1. Browser open karega
2. Exact redirect URI ke sath OAuth URL generate karega
3. Aap directly login kar sakte hain
"""

import webbrowser
import sys
from pathlib import Path

# Add project to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.ai_employee_silver.config.settings import get_settings

def main():
    print("=" * 60)
    print("GMAIL OAUTH - QUICK FIX")
    print("=" * 60)
    print()
    
    settings = get_settings()
    
    # Check if credentials are set
    if not settings.GMAIL_CLIENT_ID or settings.GMAIL_CLIENT_ID == "PASTE_YOUR_CLIENT_ID_HERE":
        print("ERROR: GMAIL_CLIENT_ID not set in .env file!")
        print()
        print("Please edit .env file and add your Gmail Client ID")
        print("Then run this script again.")
        return
    
    # Generate OAuth URL
    oauth_url = (
        "https://accounts.google.com/o/oauth2/auth?"
        f"response_type=code&"
        f"client_id={settings.GMAIL_CLIENT_ID}&"
        f"redirect_uri=http://localhost:8080&"
        f"scope=https://www.googleapis.com/auth/gmail.readonly&"
        f"access_type=offline&"
        f"prompt=consent"
    )
    
    print("Step 1: Google Cloud Console jaayein:")
    print("  https://console.cloud.google.com/apis/credentials")
    print()
    print("Step 2: Apne OAuth client ko edit karein")
    print()
    print("Step 3: Authorized redirect URIs mein ADD karein:")
    print(f"  {settings.GMAIL_REDIRECT_URI}")
    print()
    print("Step 4: SAVE karein aur 10 minutes WAIT karein")
    print()
    print("=" * 60)
    print()
    print("Step 5: Neeche diye gaye URL ko browser mein open karein:")
    print()
    print(oauth_url)
    print()
    print("=" * 60)
    print()
    
    # Ask to open browser
    response = input("Kya browser open karein? (y/n): ")
    if response.lower() == 'y':
        webbrowser.open(oauth_url)
        print()
        print("Browser open ho gaya hai!")
        print()
        print("Agar redirect_uri_mismatch error aaye toh:")
        print("  1. Google Cloud Console jaayein")
        print("  2. OAuth client edit karein")
        print("  3. Authorized redirect URI: http://localhost:8080")
        print("  4. Save karein aur 10 minutes wait karein")
        print("  5. Phir retry karein")
    else:
        print()
        print("URL copy kar lein aur manually browser mein open karein")

if __name__ == "__main__":
    main()
