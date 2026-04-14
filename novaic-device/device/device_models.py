"""
Device API — Pydantic Models

Request/Response models for device management endpoints.
Separated from route handlers for clarity.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict


# ==================== Request Models ====================

class CreateLinuxDeviceRequest(BaseModel):
    """Request to create a Linux device."""
    name: str = ""
    memory: int = 4096
    cpus: int = 4
    os_type: str = "ubuntu"
    os_version: str = "24.04"


class CreateAndroidDeviceRequest(BaseModel):
    """Request to create an Android device."""
    name: str = ""
    memory: int = 4096
    cpus: int = 4
    avd_name: str = ""
    managed: bool = True
    system_image: str = ""


class UpdateDeviceRequest(BaseModel):
    """Request to update a device."""
    name: Optional[str] = None
    memory: Optional[int] = None
    cpus: Optional[int] = None
    status: Optional[str] = None
    # P2-8: 手动修正设备所属物理 PC
    pc_client_id: Optional[str] = None
    # Linux specific
    os_type: Optional[str] = None
    os_version: Optional[str] = None
    # Android specific
    avd_name: Optional[str] = None
    device_serial: Optional[str] = None
    managed: Optional[bool] = None


class SetupDeviceRequest(BaseModel):
    """Request to setup a device."""
    source_image: Optional[str] = None  # For Linux: cloud image path
    use_cn_mirrors: bool = False


# ==================== Response Models ====================

class DeviceResponse(BaseModel):
    """Device response model."""
    id: str
    user_id: str = ""
    type: str
    name: str
    created_at: str
    status: str
    memory: int
    cpus: int
    data_path: str
    ports: dict
    # Linux specific
    backend: Optional[str] = None
    os_type: Optional[str] = None
    os_version: Optional[str] = None
    image_path: Optional[str] = None
    cloud_init_complete: Optional[bool] = None
    # Android specific
    avd_name: Optional[str] = None
    device_serial: Optional[str] = None
    managed: Optional[bool] = None
    system_image: Optional[str] = None
    # P2-8: 设备所属物理 PC（多 PC 路由用）
    pc_client_id: Optional[str] = None
    # P4-1: 设备是否可用（pc_client 在线且 device 运行中）
    available: Optional[bool] = None


class DeviceListResponse(BaseModel):
    """List of devices response."""
    devices: List[DeviceResponse]


class DeviceSubjectResponse(BaseModel):
    device_id: str
    device_type: str
    subject_type: str
    subject_id: str
    label: str
    desktop_resource_id: str
    supported_tools: Dict[str, List[str]] = Field(default_factory=dict)
    username: Optional[str] = None
    display_num: Optional[int] = None
    linux_user: Optional[str] = None
    home_path: Optional[str] = None
    android_serial: Optional[str] = None


class DeviceSubjectsResponse(BaseModel):
    subjects: List[DeviceSubjectResponse] = Field(default_factory=list)


class DeviceToolCapabilitiesResponse(BaseModel):
    device_id: str
    subject_type: Optional[str] = None
    subject_id: Optional[str] = None
    capabilities: List[str] = Field(default_factory=list)


class DeviceVmuseSyncResponse(BaseModel):
    status: str
    message: str
    source_root: str
    target_root: str
    files_synced: int
    health_status: str
    health_response: Optional[str] = None
