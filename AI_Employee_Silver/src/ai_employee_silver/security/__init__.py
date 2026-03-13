"""
Security module for AI Employee Silver Tier.

Provides secure credential management, OAuth token refresh,
session management, audit logging, and permission enforcement.

Agent Skills Pattern: Each security operation is exposed as a skill.
"""

from .security_manager import SecurityManager, get_security_manager

__all__ = [
    "SecurityManager",
    "get_security_manager",
]
