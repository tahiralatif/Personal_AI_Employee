"""
Gmail Watcher for monitoring Gmail inbox.

This module implements the GmailWatcher class that extends BaseWatcher
to monitor Gmail for new important emails and create structured action files.
"""

import time
import logging
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime
import os

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from .base_watcher import BaseWatcher


class GmailWatcher(BaseWatcher):
    """
    Gmail Watcher that monitors Gmail for new important emails.

    This watcher connects to Gmail via the Gmail API, looks for unread important emails,
    and creates structured action files in the Needs_Action/Gmail/ folder.
    """

    def __init__(self, vault_path: str, credentials_path: str = None, check_interval: int = 120):
        """
        Initialize the GmailWatcher.

        Args:
            vault_path: Path to the vault directory
            credentials_path: Path to the Gmail credentials file
            check_interval: Time interval (in seconds) between checks (default 120 seconds)
        """
        super().__init__(vault_path, check_interval)
        self.credentials_path = credentials_path or str(Path.home() / ".credentials" / "gmail_credentials.json")
        self.token_path = str(Path.home() / ".credentials" / "gmail_token.json")
        self.scopes = ['https://www.googleapis.com/auth/gmail.modify']
        self.service = None
        self.logger = logging.getLogger(self.__class__.__name__)

        # Initialize Gmail API service
        self._authenticate()

    def _authenticate(self):
        """
        Authenticate with Gmail API using OAuth 2.0.
        """
        creds = None

        # Load existing token if available
        token_path_obj = Path(self.token_path)
        if token_path_obj.exists():
            creds = Credentials.from_authorized_user_file(self.token_path, self.scopes)

        # If there are no valid credentials, get new ones
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                except Exception as e:
                    self.logger.error(f"Error refreshing credentials: {e}")
                    # If refresh fails, delete the token and get new credentials
                    if token_path_obj.exists():
                        token_path_obj.unlink()
                    creds = None

            if not creds:
                # Get new credentials
                credentials_path_obj = Path(self.credentials_path)
                if not credentials_path_obj.exists():
                    self.logger.error(f"Credentials file not found: {self.credentials_path}")
                    self.logger.error("Please set up Gmail API credentials first.")
                    return

                try:
                    flow = InstalledAppFlow.from_client_secrets_file(
                        self.credentials_path, self.scopes
                    )
                    creds = flow.run_local_server(port=0)
                except Exception as e:
                    self.logger.error(f"Error during authentication flow: {e}")
                    return

        # Save credentials for next run
        token_path_obj.parent.mkdir(parents=True, exist_ok=True)
        with open(self.token_path, 'w') as token:
            token.write(creds.to_json())

        # Build the Gmail service
        try:
            self.service = build('gmail', 'v1', credentials=creds)
            self.logger.info("Gmail API service initialized successfully")
        except Exception as e:
            self.logger.error(f"Error building Gmail service: {e}")

    def check_for_updates(self) -> List[Dict[str, Any]]:
        """
        Check Gmail for new important/unread emails.

        Returns:
            List of email dictionaries to process
        """
        if not self.service:
            self.logger.error("Gmail service not initialized. Attempting re-authentication...")
            self._authenticate()
            if not self.service:
                return []

        try:
            # Query for unread important emails
            query = 'is:unread is:important newer_than:1d'  # Look for unread important emails from last day
            results = self.service.users().messages().list(
                userId='me',
                q=query,
                maxResults=10  # Limit to 10 emails per check
            ).execute()

            messages = results.get('messages', [])
            emails = []

            for message in messages:
                try:
                    # Get full message details
                    msg = self.service.users().messages().get(
                        userId='me',
                        id=message['id'],
                        format='full'
                    ).execute()

                    # Extract email headers and snippet
                    headers = {header['name']: header['value']
                              for header in msg['payload'].get('headers', [])}

                    email_data = {
                        'id': msg['id'],
                        'threadId': msg['threadId'],
                        'from': headers.get('From', 'Unknown'),
                        'to': headers.get('To', ''),
                        'subject': headers.get('Subject', 'No Subject'),
                        'date': headers.get('Date', ''),
                        'snippet': msg.get('snippet', ''),
                        'sizeEstimate': msg.get('sizeEstimate', 0),
                        'labels': msg.get('labelIds', []),
                        'received_time': datetime.now().isoformat()
                    }

                    # Determine priority based on sender and subject
                    email_data['priority'] = self._determine_priority(email_data)

                    emails.append(email_data)

                except Exception as e:
                    self.logger.error(f"Error processing email {message['id']}: {e}")
                    continue

            self.logger.info(f"Found {len(emails)} new important emails to process")
            return emails

        except HttpError as e:
            self.logger.error(f"Gmail API error: {e}")
            # If authentication error, try to re-authenticate
            if e.resp.status in [401, 403]:
                self.logger.info("Attempting to re-authenticate...")
                self._authenticate()
            return []
        except Exception as e:
            self.logger.error(f"Error checking for Gmail updates: {e}")
            return []

    def create_action_file(self, email: Dict[str, Any]) -> Path:
        """
        Create a structured action file for the given email.

        Args:
            email: Dictionary containing email information

        Returns:
            Path to the created action file
        """
        # Generate filename with timestamp and email ID
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_subject = "".join(c for c in email['subject'][:50] if c.isalnum() or c in (' ', '-', '_')).rstrip()
        filename = f"GMAIL_{timestamp}_{email['id'][:8]}_{safe_subject.replace(' ', '_')}.md"

        # Build YAML frontmatter
        frontmatter = {
            "type": "email",
            "from": email['from'],
            "to": email['to'],
            "subject": email['subject'],
            "received": email['received_time'],
            "priority": email['priority'],
            "status": "pending",
            "gmail_id": email['id'],
            "thread_id": email['threadId'],
            "labels": email['labels'],
            "snippet": email['snippet'][:200] + "..." if len(email['snippet']) > 200 else email['snippet']
        }

        # Create the action file content
        content = self._build_action_file_content(email, frontmatter)

        # Create the action file
        action_file_path = self._create_structured_action_file(filename, content, "Gmail")

        # Mark email as read after creating action file
        try:
            self._mark_as_read(email['id'])
        except Exception as e:
            self.logger.error(f"Error marking email as read: {e}")

        self.logger.info(f"Created Gmail action file: {action_file_path.name}")
        return action_file_path

    def _build_action_file_content(self, email: Dict[str, Any], frontmatter: Dict[str, Any]) -> str:
        """
        Build the content for the action file.

        Args:
            email: Dictionary containing email information
            frontmatter: Dictionary containing frontmatter data

        Returns:
            String content for the action file
        """
        # Build YAML frontmatter
        fm_lines = ["---"]
        for key, value in frontmatter.items():
            if isinstance(value, list):
                fm_lines.append(f"{key}: {value}")
            elif isinstance(value, str):
                fm_lines.append(f'{key}: "{value}"')
            else:
                fm_lines.append(f"{key}: {value}")
        fm_lines.append("---")
        fm_lines.append("")  # Empty line after frontmatter

        # Build body content
        body_lines = [
            f"# Email: {email['subject']}",
            "",
            "## Email Details",
            f"- **From**: {email['from']}",
            f"- **To**: {email['to']}",
            f"- **Date**: {email['date']}",
            f"- **Size**: {email['sizeEstimate']} bytes",
            f"- **Labels**: {', '.join(email['labels'])}",
            "",
            "## Email Content",
            f"> {email['snippet']}",
            "",
            "## Suggested Actions",
            "- [ ] Reply to sender",
            "- [ ] Forward to relevant party",
            "- [ ] Archive after processing",
            "- [ ] Flag for follow-up",
            "",
            "---",
            f"*Automatically generated by AI Employee Gmail Watcher*"
        ]

        return "\n".join(fm_lines + body_lines)

    def _determine_priority(self, email: Dict[str, Any]) -> str:
        """
        Determine the priority of an email based on its content.

        Args:
            email: Dictionary containing email information

        Returns:
            Priority level ("high", "medium", or "low")
        """
        subject = email['subject'].lower()
        snippet = email['snippet'].lower()

        # Keywords that indicate high priority
        high_priority_keywords = [
            'urgent', 'asap', 'immediately', 'critical', 'emergency',
            'payment', 'invoice', 'billing', 'due', 'deadline', 'meeting',
            'client', 'customer', 'problem', 'issue', 'error'
        ]

        # Keywords that indicate medium priority
        medium_priority_keywords = [
            'follow', 'remind', 'update', 'report', 'schedule', 'proposal',
            'offer', 'opportunity', 'agreement', 'contract', 'order'
        ]

        # Combine subject and snippet for keyword search
        combined_text = f"{subject} {snippet}"

        # Check for high priority keywords
        for keyword in high_priority_keywords:
            if keyword in combined_text:
                return "high"

        # Check for medium priority keywords
        for keyword in medium_priority_keywords:
            if keyword in combined_text:
                return "medium"

        # Default to low priority
        return "low"

    def _mark_as_read(self, email_id: str):
        """
        Mark an email as read in Gmail.

        Args:
            email_id: ID of the email to mark as read
        """
        if not self.service:
            raise Exception("Gmail service not initialized")

        try:
            # Remove the UNREAD label
            self.service.users().messages().modify(
                userId='me',
                id=email_id,
                body={'removeLabelIds': ['UNREAD']}
            ).execute()
            self.logger.info(f"Marked email {email_id} as read")
        except Exception as e:
            self.logger.error(f"Error marking email {email_id} as read: {e}")

    def run(self):
        """
        Override the base run method to include error handling for Gmail API.
        """
        self.logger.info(f'Starting {self.__class__.__name__}')
        while True:
            try:
                items = self.check_for_updates()
                for item in items:
                    if item.get('id') not in self.processed_ids:
                        self.create_action_file(item)
                        self.processed_ids.add(item.get('id', ''))

            except Exception as e:
                self.logger.error(f'Error in {self.__class__.__name__}: {e}')
                # If it's an authentication error, try to re-authenticate
                if "invalid_grant" in str(e) or "unauthorized" in str(e).lower():
                    self.logger.info("Authentication error detected, attempting re-authentication...")
                    self._authenticate()

                # Exponential backoff on error
                time.sleep(min(self.check_interval * 2, 300))  # Max 5 minutes
            else:
                # Normal sleep interval
                time.sleep(self.check_interval)


def create_gmail_watcher(vault_path: str, credentials_path: str = None) -> GmailWatcher:
    """
    Factory function to create a GmailWatcher instance.

    Args:
        vault_path: Path to the vault directory
        credentials_path: Path to the Gmail credentials file

    Returns:
        GmailWatcher instance
    """
    return GmailWatcher(vault_path, credentials_path)