"""
Shared tool definitions for gateway and tools_server.

Canonical source for BUILTIN_TOOLS and VM_TOOLS.
Gateway imports from here to avoid depending on tools_server.
"""

from .definitions import BUILTIN_TOOLS, VM_TOOLS

__all__ = ["BUILTIN_TOOLS", "VM_TOOLS"]
