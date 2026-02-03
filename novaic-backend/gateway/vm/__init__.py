"""
VM Management Module

Handles all VM lifecycle operations:
- VM disk creation (qemu-img)
- Cloud-init ISO generation
- QEMU process management
- SSH key management

This module replaces the Tauri-based VM management,
centralizing all VM control in the Gateway.
"""

from .manager import VmManager, get_vm_manager
from .setup import VmSetup
from .ssh import SshKeyManager, get_ssh_key_manager

__all__ = [
    "VmManager",
    "get_vm_manager",
    "VmSetup",
    "SshKeyManager",
    "get_ssh_key_manager",
]
