"""
MCP Server modules for AI Employee Silver Tier.

MCP (Model Context Protocol) servers are the action layer of the AI Employee system.
They provide capabilities for external actions via standardized tool interfaces.

Available MCP Servers:
    - EmailMCPServer: Send, draft, read emails via Gmail API
    - BrowserMCPServer: Web automation via Playwright
    - LinkedInMCPServer: LinkedIn automation with sales content generation

Agent Skills Pattern: Each MCP server exposes its operations as skills.
"""

from .email_mcp import EmailMCPServer, get_email_server
from .browser_mcp import BrowserMCPServer, get_browser_server
from .linkedin_mcp import LinkedInMCPServer, get_linkedin_server

__all__ = [
    "EmailMCPServer",
    "get_email_server",
    "BrowserMCPServer",
    "get_browser_server",
    "LinkedInMCPServer",
    "get_linkedin_server",
]
