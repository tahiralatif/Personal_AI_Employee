"""
Integrations package for AI Employee.

This package contains integrations with external AI systems and services:
- Qwen Brain: Qwen AI integration via CLI
- Ralph Loop: Ralph Wiggum persistent loop
"""

from .qwen_brain import QwenBrain, create_qwen_brain
from .ralph_loop import RalphWiggumLoop, ralph_loop

__all__ = [
    "QwenBrain",
    "create_qwen_brain",
    "RalphWiggumLoop",
    "ralph_loop",
]
