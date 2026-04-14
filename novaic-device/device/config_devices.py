"""
Unified Device Configuration Models.

This module defines the unified device model that replaces the separate
VmConfig and AndroidConfig. All devices (Linux VM, Android) are now
managed through a single Device abstraction.
"""

from enum import Enum
from typing import Optional, Dict, Any, List, Union
from pydantic import BaseModel, Field
import uuid
from datetime import datetime, timezone


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class DeviceType(str, Enum):
    """Device type enumeration."""
    LINUX = "linux"
    ANDROID = "android"
    HOST_DESKTOP = "host_desktop"


class DeviceStatus(str, Enum):
    """Device lifecycle status."""
    CREATED = "created"      # Config created, not initialized
    SETUP = "setup"          # Initialization in progress
    READY = "ready"          # Ready to start
    RUNNING = "running"      # Currently running
    STOPPED = "stopped"      # Stopped
    ERROR = "error"          # Error state


class DeviceConfig(BaseModel):
    """Base device configuration."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""
    type: DeviceType
    name: str = ""
    created_at: str = Field(default_factory=utc_now_iso)
    status: DeviceStatus = DeviceStatus.CREATED

    # P2-8: 设备所属物理 PC（setup 时记录，多 PC 路由用）
    pc_client_id: Optional[str] = None

    # Common resource config
    memory: int = 4096  # MB
    cpus: int = 4
    data_path: str = ""
    ports: Dict[str, int] = Field(default_factory=dict)


class LinuxDevice(DeviceConfig):
    """Linux VM device configuration."""
    type: DeviceType = DeviceType.LINUX
    
    # Linux specific
    backend: str = "qemu"
    os_type: str = "ubuntu"
    os_version: str = "24.04"
    image_path: str = ""
    cloud_init_complete: bool = False


class AndroidDevice(DeviceConfig):
    """Android device configuration."""
    type: DeviceType = DeviceType.ANDROID
    
    # Android specific
    avd_name: str = ""
    device_serial: str = ""
    managed: bool = True
    system_image: str = ""


class HostDesktopDevice(DeviceConfig):
    """Host Desktop device — represents the host PC's screen for remote control."""
    type: DeviceType = DeviceType.HOST_DESKTOP
    memory: int = 0
    cpus: int = 0


# Type alias for any device
Device = Union[LinuxDevice, AndroidDevice, HostDesktopDevice]


def device_from_dict(data: Dict[str, Any]) -> Device:
    """Create a Device instance from a dictionary."""
    device_type = data.get("type", "linux")
    if device_type == "linux":
        return LinuxDevice(**data)
    elif device_type == "android":
        return AndroidDevice(**data)
    elif device_type == "host_desktop":
        return HostDesktopDevice(**data)
    else:
        raise ValueError(f"Unknown device type: {device_type}")
