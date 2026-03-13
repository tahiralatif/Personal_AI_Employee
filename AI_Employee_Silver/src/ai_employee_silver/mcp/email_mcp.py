"""
Email MCP Server for AI Employee Silver Tier.

This module implements email capabilities via MCP (Model Context Protocol) pattern.
It provides Agent Skills for sending, drafting, and reading emails via Gmail API.

Agent Skills:
    - email.send(to, subject, body, attachments) -> bool
    - email.draft(to, subject, body) -> str (draft ID)
    - email.read(query, max_results) -> list
    - email.search(query) -> list
"""

import base64
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from pathlib import Path
from typing import Optional, List, Dict, Any

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from ..config.settings import Settings, get_settings
from ..utils.logger import get_logger


# Gmail API Scopes
SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.compose",
    "https://www.googleapis.com/auth/gmail.modify"
]

TOKEN_FILE = "token_email_mcp.json"


class EmailMCPServer:
    """
    Email MCP Server providing email capabilities via Gmail API.
    
    This server exposes email operations as Agent Skills following
    the MCP (Model Context Protocol) pattern.
    """
    
    def __init__(
        self,
        settings: Optional[Settings] = None,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize Email MCP Server.
        
        Args:
            settings: Application settings
            logger: Logger instance
        """
        self.settings = settings if settings else get_settings()
        self.logger = logger if logger else get_logger()
        
        self.service = None
        self.creds = None
        self._authenticated = False
    
    def authenticate(self) -> bool:
        """
        Authenticate with Gmail API using OAuth 2.0.
        
        Returns:
            True if authentication successful
        """
        try:
            self.logger.info("Authenticating Email MCP Server...")
            
            if not self.settings.is_gmail_configured():
                self.logger.error("Gmail credentials not configured")
                return False
            
            # Token file path
            token_path = Path(__file__).parent.parent.parent.parent / TOKEN_FILE
            
            # Load existing credentials
            self.creds = None
            if token_path.exists():
                self.creds = Credentials.from_authorized_user_file(
                    str(token_path),
                    SCOPES
                )
            
            # Refresh or obtain new credentials
            if not self.creds or not self.creds.valid:
                if self.creds and self.creds.expired and self.creds.refresh_token:
                    self.logger.info("Refreshing credentials...")
                    self.creds.refresh(Request())
                else:
                    self.logger.info("Starting OAuth 2.0 flow...")
                    flow = InstalledAppFlow.from_client_config(
                        {
                            "installed": {
                                "client_id": self.settings.GMAIL_CLIENT_ID,
                                "client_secret": self.settings.GMAIL_CLIENT_SECRET,
                                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                                "token_uri": "https://oauth2.googleapis.com/token",
                                "redirect_uris": [self.settings.GMAIL_REDIRECT_URI],
                            }
                        },
                        SCOPES,
                    )
                    self.creds = flow.run_local_server(
                        port=int(self.settings.GMAIL_REDIRECT_URI.split(":")[-1]),
                        open_browser=False
                    )
                
                # Save credentials
                with open(token_path, "w") as token:
                    token.write(self.creds.to_json())
                self.logger.info("Credentials saved")
            
            # Build service
            self.service = build("gmail", "v1", credentials=self.creds)
            self._authenticated = True
            self.logger.info("Email MCP Server authenticated successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Authentication failed: {e}")
            return False
    
    def ensure_authenticated(self) -> bool:
        """Ensure server is authenticated, authenticate if needed."""
        if not self._authenticated or not self.service:
            return self.authenticate()
        return True
    
    # =========================================================================
    # Agent Skills - Email Operations
    # =========================================================================
    
    def send(
        self,
        to: str,
        subject: str,
        body: str,
        html: bool = False,
        attachments: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Send an email via Gmail API.
        
        Agent Skill: email.send
        
        Args:
            to: Recipient email address
            subject: Email subject
            body: Email body text
            html: Whether body is HTML (default: False)
            attachments: Optional list of file paths to attach
            
        Returns:
            dict with 'success' (bool) and 'message_id' (str) or 'error' (str)
        """
        try:
            if not self.ensure_authenticated():
                return {"success": False, "error": "Not authenticated"}
            
            self.logger.info(f"Sending email to {to}: {subject}")
            
            # Create message
            message = MIMEMultipart() if attachments else MIMEText("", "plain")
            message["to"] = to
            message["subject"] = subject
            
            # Add body
            mime_type = "html" if html else "plain"
            message.attach(MIMEText(body, mime_type))
            
            # Add attachments
            if attachments:
                for file_path in attachments:
                    self._attach_file(message, file_path)
            
            # Encode message
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
            
            # Send
            sent_message = self.service.users().messages().send(
                userId="me",
                body={"raw": raw_message}
            ).execute()
            
            self.logger.info(f"Email sent: {sent_message['id']}")
            
            return {
                "success": True,
                "message_id": sent_message["id"],
                "thread_id": sent_message["threadId"]
            }
            
        except Exception as e:
            self.logger.error(f"Failed to send email: {e}")
            return {"success": False, "error": str(e)}
    
    def _attach_file(self, message: MIMEMultipart, file_path: str) -> None:
        """
        Attach file to email message.
        
        Args:
            message: Email message
            file_path: Path to file
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Attachment not found: {file_path}")
        
        with open(path, "rb") as f:
            part = MIMEBase("application", "octet-stream")
            part.set_payload(f.read())
        
        encoders.encode_base64(part)
        part.add_header(
            "Content-Disposition",
            f"attachment; filename={path.name}"
        )
        message.attach(part)
    
    def draft(
        self,
        to: str,
        subject: str,
        body: str,
        html: bool = False
    ) -> Dict[str, Any]:
        """
        Create an email draft.
        
        Agent Skill: email.draft
        
        Args:
            to: Recipient email address
            subject: Email subject
            body: Email body text
            html: Whether body is HTML (default: False)
            
        Returns:
            dict with 'success' (bool) and 'draft_id' (str) or 'error' (str)
        """
        try:
            if not self.ensure_authenticated():
                return {"success": False, "error": "Not authenticated"}
            
            self.logger.info(f"Creating draft email to {to}: {subject}")
            
            # Create message
            message = MIMEText("", "plain")
            message["to"] = to
            message["subject"] = subject
            
            # Add body
            mime_type = "html" if html else "plain"
            message.attach(MIMEText(body, mime_type))
            
            # Encode message
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
            
            # Create draft
            draft = self.service.users().drafts().create(
                userId="me",
                body={"message": {"raw": raw_message}}
            ).execute()
            
            self.logger.info(f"Draft created: {draft['id']}")
            
            return {
                "success": True,
                "draft_id": draft["id"],
                "message_id": draft["message"]["id"]
            }
            
        except Exception as e:
            self.logger.error(f"Failed to create draft: {e}")
            return {"success": False, "error": str(e)}
    
    def read(
        self,
        query: str = "",
        max_results: int = 10
    ) -> Dict[str, Any]:
        """
        Read emails matching query.
        
        Agent Skill: email.read
        
        Args:
            query: Gmail search query (e.g., "is:unread", "from:example@gmail.com")
            max_results: Maximum number of emails to fetch
            
        Returns:
            dict with 'success' (bool) and 'emails' (list) or 'error' (str)
        """
        try:
            if not self.ensure_authenticated():
                return {"success": False, "error": "Not authenticated"}
            
            self.logger.info(f"Reading emails with query: {query or 'inbox'}")
            
            # List messages
            response = self.service.users().messages().list(
                userId="me",
                q=query,
                maxResults=max_results
            ).execute()
            
            messages = response.get("messages", [])
            if not messages:
                return {"success": True, "emails": [], "count": 0}
            
            # Fetch full messages
            emails = []
            for msg in messages:
                full_message = self.service.users().messages().get(
                    userId="me",
                    id=msg["id"],
                    format="metadata",
                    metadataHeaders=["From", "To", "Subject", "Date"]
                ).execute()
                
                email_data = self._parse_email_metadata(full_message)
                email_data["id"] = msg["id"]
                emails.append(email_data)
            
            self.logger.info(f"Read {len(emails)} emails")
            
            return {
                "success": True,
                "emails": emails,
                "count": len(emails)
            }
            
        except Exception as e:
            self.logger.error(f"Failed to read emails: {e}")
            return {"success": False, "error": str(e)}
    
    def _parse_email_metadata(self, message: Dict[str, Any]) -> Dict[str, str]:
        """
        Parse email metadata from Gmail API response.
        
        Args:
            message: Gmail API message object
            
        Returns:
            Dictionary with email metadata
        """
        headers = message["payload"]["headers"]
        metadata = {}
        
        for header in headers:
            name = header["name"].lower()
            if name == "from":
                metadata["from"] = header["value"]
            elif name == "to":
                metadata["to"] = header["value"]
            elif name == "subject":
                metadata["subject"] = header["value"]
            elif name == "date":
                metadata["date"] = header["value"]
        
        return metadata
    
    def search(self, query: str) -> Dict[str, Any]:
        """
        Search emails matching query.
        
        Agent Skill: email.search
        
        Args:
            query: Gmail search query
            
        Returns:
            dict with 'success' (bool) and 'message_ids' (list) or 'error' (str)
        """
        try:
            if not self.ensure_authenticated():
                return {"success": False, "error": "Not authenticated"}
            
            self.logger.info(f"Searching emails: {query}")
            
            response = self.service.users().messages().list(
                userId="me",
                q=query
            ).execute()
            
            messages = response.get("messages", [])
            message_ids = [msg["id"] for msg in messages]
            
            return {
                "success": True,
                "message_ids": message_ids,
                "count": len(message_ids)
            }
            
        except Exception as e:
            self.logger.error(f"Search failed: {e}")
            return {"success": False, "error": str(e)}
    
    def mark_as_read(self, message_id: str) -> Dict[str, Any]:
        """
        Mark email as read.
        
        Agent Skill: email.mark_as_read
        
        Args:
            message_id: Gmail message ID
            
        Returns:
            dict with 'success' (bool) or 'error' (str)
        """
        try:
            if not self.ensure_authenticated():
                return {"success": False, "error": "Not authenticated"}
            
            self.logger.info(f"Marking email as read: {message_id}")
            
            self.service.users().messages().modify(
                userId="me",
                id=message_id,
                body={"removeLabelIds": ["UNREAD"]}
            ).execute()
            
            return {"success": True}
            
        except Exception as e:
            self.logger.error(f"Failed to mark as read: {e}")
            return {"success": False, "error": str(e)}
    
    # =========================================================================
    # MCP Server Interface
    # =========================================================================
    
    def get_tools(self) -> List[Dict[str, Any]]:
        """
        Get list of MCP tools (Agent Skills).
        
        Returns:
            List of tool definitions
        """
        return [
            {
                "name": "email.send",
                "description": "Send an email via Gmail API",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "to": {"type": "string", "description": "Recipient email"},
                        "subject": {"type": "string", "description": "Email subject"},
                        "body": {"type": "string", "description": "Email body"},
                        "html": {"type": "boolean", "description": "Is HTML body"},
                        "attachments": {"type": "array", "items": {"type": "string"}}
                    },
                    "required": ["to", "subject", "body"]
                }
            },
            {
                "name": "email.draft",
                "description": "Create an email draft",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "to": {"type": "string", "description": "Recipient email"},
                        "subject": {"type": "string", "description": "Email subject"},
                        "body": {"type": "string", "description": "Email body"},
                        "html": {"type": "boolean", "description": "Is HTML body"}
                    },
                    "required": ["to", "subject", "body"]
                }
            },
            {
                "name": "email.read",
                "description": "Read emails matching query",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Gmail search query"},
                        "max_results": {"type": "integer", "description": "Max results"}
                    }
                }
            },
            {
                "name": "email.search",
                "description": "Search emails matching query",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Gmail search query"}
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "email.mark_as_read",
                "description": "Mark email as read",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "message_id": {"type": "string", "description": "Gmail message ID"}
                    },
                    "required": ["message_id"]
                }
            }
        ]
    
    def call_tool(self, name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """
        Call an MCP tool (Agent Skill) by name.
        
        Args:
            name: Tool name (e.g., "email.send")
            args: Tool arguments
            
        Returns:
            Tool execution result
        """
        tools = {
            "email.send": lambda **kwargs: self.send(**kwargs),
            "email.draft": lambda **kwargs: self.draft(**kwargs),
            "email.read": lambda **kwargs: self.read(**kwargs),
            "email.search": lambda **kwargs: self.search(**kwargs),
            "email.mark_as_read": lambda **kwargs: self.mark_as_read(**kwargs)
        }
        
        if name not in tools:
            return {"success": False, "error": f"Unknown tool: {name}"}
        
        return tools[name](**args)
    
    def get_skills(self) -> Dict[str, callable]:
        """
        Get all Agent Skills exposed by this server.
        
        Returns:
            Dictionary of skill names to callables
        """
        return {
            "email.send": self.send,
            "email.draft": self.draft,
            "email.read": self.read,
            "email.search": self.search,
            "email.mark_as_read": self.mark_as_read,
        }


# Global instance
_email_server: Optional[EmailMCPServer] = None


def get_email_server() -> EmailMCPServer:
    """Get or create global Email MCP Server instance."""
    global _email_server
    if _email_server is None:
        _email_server = EmailMCPServer()
    return _email_server


if __name__ == "__main__":
    # Test Email MCP Server
    print("=== Email MCP Server Test ===\n")
    
    server = get_email_server()
    
    # Authenticate
    if server.authenticate():
        print("✓ Authentication successful")
        
        # Test read
        result = server.read(max_results=5)
        if result["success"]:
            print(f"✓ Read {result['count']} emails")
        
        # Test send (commented out for safety)
        # result = server.send(
        #     to="test@example.com",
        #     subject="Test Email",
        #     body="This is a test email from Email MCP Server"
        # )
        # print(f"Send result: {result}")
        
        # Get tools
        tools = server.get_tools()
        print(f"\n✓ Available tools: {len(tools)}")
        for tool in tools:
            print(f"  - {tool['name']}: {tool['description']}")
    else:
        print("✗ Authentication failed")
