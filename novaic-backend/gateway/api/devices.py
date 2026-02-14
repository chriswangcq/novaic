"""
Unified Device API - CRUD and operations for all device types.

This module provides a unified API for managing devices (Linux VM, Android)
attached to agents. It replaces the separate VM and Android APIs.
"""

from typing import Optional, List
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
import logging
import shutil
from pathlib import Path

from gateway.db.access import get_database, Database
from gateway.db.repositories import DeviceRepository
from gateway.config.devices import (
    Device, LinuxDevice, AndroidDevice,
    DeviceType, DeviceStatus,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["devices"])


# ==================== Request/Response Models ====================

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
    # Linux specific
    os_type: Optional[str] = None
    os_version: Optional[str] = None
    # Android specific
    avd_name: Optional[str] = None
    device_serial: Optional[str] = None
    managed: Optional[bool] = None


class DeviceResponse(BaseModel):
    """Device response model."""
    id: str
    agent_id: str
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


class DeviceListResponse(BaseModel):
    """List of devices response."""
    devices: List[DeviceResponse]


class SetupDeviceRequest(BaseModel):
    """Request to setup a device."""
    source_image: Optional[str] = None  # For Linux: cloud image path
    use_cn_mirrors: bool = False


# ==================== Helper Functions ====================

def get_device_repo(db: Database = Depends(get_database)) -> DeviceRepository:
    return DeviceRepository(db)


def device_to_response(device: Device) -> DeviceResponse:
    """Convert Device to response model."""
    data = device.model_dump()
    data['type'] = device.type.value
    data['status'] = device.status.value
    return DeviceResponse(**data)


def get_data_dir() -> Path:
    """Get the data directory."""
    import os
    return Path(os.environ.get('NOVAIC_DATA_DIR', './data'))


def allocate_ports_for_device(db: Database, device_type: DeviceType) -> dict:
    """Allocate ports for a new device."""
    # Find the next available port range
    from gateway.config.agents_db import BASE_PORT, BASE_VMUSE_PORT
    
    # Get all used ports
    rows = db.fetchall("SELECT ports FROM devices WHERE ports != '{}'")
    used_ssh = set()
    used_vmuse = set()
    for row in rows:
        import json
        ports = json.loads(row['ports'] or '{}')
        if 'ssh' in ports:
            used_ssh.add(ports['ssh'])
        if 'vmuse' in ports:
            used_vmuse.add(ports['vmuse'])
    
    # Find next available
    ssh_port = BASE_PORT
    while ssh_port in used_ssh:
        ssh_port += 1
    
    vmuse_port = BASE_VMUSE_PORT
    while vmuse_port in used_vmuse:
        vmuse_port += 1
    
    if device_type == DeviceType.LINUX:
        return {'ssh': ssh_port, 'vmuse': vmuse_port}
    else:
        return {}  # Android doesn't need ports


# ==================== Device CRUD Endpoints ====================

@router.get("/agents/{agent_id}/devices", response_model=DeviceListResponse)
def list_devices(agent_id: str, repo: DeviceRepository = Depends(get_device_repo)):
    """List all devices for an agent."""
    devices = repo.list_by_agent(agent_id)
    return DeviceListResponse(devices=[device_to_response(d) for d in devices])


@router.post("/agents/{agent_id}/devices/linux", response_model=DeviceResponse)
def create_linux_device(
    agent_id: str,
    request: CreateLinuxDeviceRequest,
    repo: DeviceRepository = Depends(get_device_repo),
    db: Database = Depends(get_database),
):
    """Create a new Linux device for an agent."""
    # Check if agent exists
    agent = db.fetchone("SELECT id FROM agents WHERE id = ?", (agent_id,))
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    # Check if agent already has a Linux device (limit: 1 per agent)
    existing = repo.get_first_by_type(agent_id, DeviceType.LINUX)
    if existing:
        raise HTTPException(
            status_code=400, 
            detail="Agent already has a Linux device. Only one Linux VM per agent is allowed."
        )
    
    # Allocate ports
    ports = allocate_ports_for_device(db, DeviceType.LINUX)
    
    # Create device directory
    data_dir = get_data_dir()
    import uuid
    device_id = str(uuid.uuid4())
    device_path = data_dir / "agents" / agent_id / "devices" / device_id
    device_path.mkdir(parents=True, exist_ok=True)
    
    # Create device
    device = LinuxDevice(
        id=device_id,
        agent_id=agent_id,
        name=request.name or f"Linux VM",
        memory=request.memory,
        cpus=request.cpus,
        os_type=request.os_type,
        os_version=request.os_version,
        data_path=str(device_path),
        ports=ports,
        image_path=str(device_path / "disk.qcow2"),
        status=DeviceStatus.CREATED,
    )
    
    repo.create(device)
    logger.info(f"Created Linux device {device_id} for agent {agent_id}")
    
    return device_to_response(device)


@router.post("/agents/{agent_id}/devices/android", response_model=DeviceResponse)
def create_android_device(
    agent_id: str,
    request: CreateAndroidDeviceRequest,
    repo: DeviceRepository = Depends(get_device_repo),
    db: Database = Depends(get_database),
):
    """Create a new Android device for an agent."""
    # Check if agent exists
    agent = db.fetchone("SELECT id FROM agents WHERE id = ?", (agent_id,))
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    # Check if agent already has an Android device (limit: 1 per agent)
    existing = repo.get_first_by_type(agent_id, DeviceType.ANDROID)
    if existing:
        raise HTTPException(
            status_code=400, 
            detail="Agent already has an Android device. Only one Android device per agent is allowed."
        )
    
    # Create device directory
    data_dir = get_data_dir()
    import uuid
    device_id = str(uuid.uuid4())
    device_path = data_dir / "agents" / agent_id / "devices" / device_id
    device_path.mkdir(parents=True, exist_ok=True)
    
    # Generate AVD name if not provided
    avd_name = request.avd_name
    if not avd_name and request.managed:
        # Generate a unique AVD name based on agent_id
        avd_name = f"novaic_{agent_id[:8]}"
    
    # Create device
    device = AndroidDevice(
        id=device_id,
        agent_id=agent_id,
        name=request.name or f"Android Device",
        memory=request.memory,
        cpus=request.cpus,
        avd_name=avd_name,
        managed=request.managed,
        system_image=request.system_image,
        data_path=str(device_path),
        status=DeviceStatus.CREATED,
    )
    
    repo.create(device)
    logger.info(f"Created Android device {device_id} for agent {agent_id}")
    
    return device_to_response(device)


@router.get("/agents/{agent_id}/devices/{device_id}", response_model=DeviceResponse)
def get_device(
    agent_id: str,
    device_id: str,
    repo: DeviceRepository = Depends(get_device_repo),
):
    """Get a specific device."""
    device = repo.get(device_id)
    if not device or device.agent_id != agent_id:
        raise HTTPException(status_code=404, detail="Device not found")
    return device_to_response(device)


@router.patch("/agents/{agent_id}/devices/{device_id}", response_model=DeviceResponse)
def update_device(
    agent_id: str,
    device_id: str,
    request: UpdateDeviceRequest,
    repo: DeviceRepository = Depends(get_device_repo),
):
    """Update a device."""
    device = repo.get(device_id)
    if not device or device.agent_id != agent_id:
        raise HTTPException(status_code=404, detail="Device not found")
    
    # Build update dict
    updates = request.model_dump(exclude_none=True)
    if not updates:
        return device_to_response(device)
    
    # Convert status string to enum
    if 'status' in updates:
        updates['status'] = DeviceStatus(updates['status'])
    
    updated = repo.update(device_id, **updates)
    return device_to_response(updated)


@router.delete("/agents/{agent_id}/devices/{device_id}")
def delete_device(
    agent_id: str,
    device_id: str,
    repo: DeviceRepository = Depends(get_device_repo),
):
    """Delete a device and its files."""
    device = repo.get(device_id)
    if not device or device.agent_id != agent_id:
        raise HTTPException(status_code=404, detail="Device not found")
    
    # Stop device if running
    if device.status == DeviceStatus.RUNNING:
        try:
            _stop_device(device)
        except Exception as e:
            logger.warning(f"Failed to stop device {device_id}: {e}")
    
    # Delete device files
    if device.data_path:
        device_path = Path(device.data_path)
        if device_path.exists():
            shutil.rmtree(device_path)
            logger.info(f"Deleted device directory: {device_path}")
    
    # For managed Android, also delete AVD
    if device.type == DeviceType.ANDROID and getattr(device, 'managed', False):
        avd_name = getattr(device, 'avd_name', '')
        if avd_name:
            try:
                _delete_avd(avd_name)
            except Exception as e:
                logger.warning(f"Failed to delete AVD {avd_name}: {e}")
    
    # Delete from database
    repo.delete(device_id)
    
    return {"status": "ok", "message": "Device deleted"}


# ==================== Device Operation Endpoints ====================

@router.post("/devices/{device_id}/setup")
def setup_device(
    device_id: str,
    request: SetupDeviceRequest,
    repo: DeviceRepository = Depends(get_device_repo),
):
    """Setup/initialize a device."""
    device = repo.get(device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    if device.type == DeviceType.LINUX:
        return _setup_linux_device(device, request, repo)
    else:
        return _setup_android_device(device, request, repo)


@router.post("/devices/{device_id}/start")
def start_device(
    device_id: str,
    repo: DeviceRepository = Depends(get_device_repo),
):
    """Start a device."""
    device = repo.get(device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    if device.status == DeviceStatus.RUNNING:
        return {"status": "ok", "message": "Device already running"}
    
    if device.status not in [DeviceStatus.READY, DeviceStatus.STOPPED]:
        raise HTTPException(
            status_code=400, 
            detail=f"Device not ready to start (status: {device.status.value})"
        )
    
    if device.type == DeviceType.LINUX:
        return _start_linux_device(device, repo)
    else:
        return _start_android_device(device, repo)


@router.post("/devices/{device_id}/stop")
def stop_device(
    device_id: str,
    repo: DeviceRepository = Depends(get_device_repo),
):
    """Stop a device."""
    device = repo.get(device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    if device.status != DeviceStatus.RUNNING:
        return {"status": "ok", "message": "Device not running"}
    
    result = _stop_device(device)
    repo.update_status(device_id, DeviceStatus.STOPPED)
    
    return result


@router.get("/devices/{device_id}/status")
def get_device_status(
    device_id: str,
    repo: DeviceRepository = Depends(get_device_repo),
):
    """Get device status."""
    device = repo.get(device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    # Get runtime status
    if device.type == DeviceType.LINUX:
        running = _is_linux_device_running(device)
    else:
        running = _is_android_device_running(device)
    
    # Update status if changed
    if running and device.status != DeviceStatus.RUNNING:
        repo.update_status(device_id, DeviceStatus.RUNNING)
        device.status = DeviceStatus.RUNNING
    elif not running and device.status == DeviceStatus.RUNNING:
        repo.update_status(device_id, DeviceStatus.STOPPED)
        device.status = DeviceStatus.STOPPED
    
    return {
        "device_id": device_id,
        "type": device.type.value,
        "status": device.status.value,
        "running": running,
    }


# ==================== Internal Functions ====================

def _setup_linux_device(device: LinuxDevice, request: SetupDeviceRequest, repo: DeviceRepository):
    """Setup a Linux VM device."""
    from gateway.vm.setup import VmSetup
    
    repo.update_status(device.id, DeviceStatus.SETUP)
    
    try:
        vm_setup = VmSetup()
        vm_setup.setup_vm(
            agent_id=device.agent_id,
            source_image=request.source_image,
            use_cn_mirrors=request.use_cn_mirrors,
            # Use device's data_path instead of default agent path
            # Note: VmSetup.setup_vm uses get_vm_dir internally, we need to override
        )
        
        # Copy the created files to device's data_path
        # VmSetup creates files in data_dir/agents/{agent_id}/
        # We need them in device.data_path
        data_dir = get_data_dir()
        agent_vm_dir = data_dir / "agents" / device.agent_id
        device_path = Path(device.data_path)
        
        # Move disk and cloud-init files to device directory
        for filename in ["disk.qcow2", "cloud-init.iso", "QEMU_EFI.fd", "QEMU_VARS.fd"]:
            src = agent_vm_dir / filename
            dst = device_path / filename
            if src.exists() and not dst.exists():
                shutil.move(str(src), str(dst))
        
        # Move cloud-init directory
        src_cloudinit = agent_vm_dir / "cloud-init"
        dst_cloudinit = device_path / "cloud-init"
        if src_cloudinit.exists() and not dst_cloudinit.exists():
            shutil.move(str(src_cloudinit), str(dst_cloudinit))
        
        repo.update(device.id, 
            status=DeviceStatus.READY,
            cloud_init_complete=False,  # Will be set after first boot
            image_path=str(device_path / "disk.qcow2"),
        )
        
        return {"status": "ok", "message": "Linux device setup complete"}
    except Exception as e:
        repo.update_status(device.id, DeviceStatus.ERROR)
        raise HTTPException(status_code=500, detail=str(e))


def _setup_android_device(device: AndroidDevice, request: SetupDeviceRequest, repo: DeviceRepository):
    """Setup an Android device."""
    import httpx
    
    if not device.managed:
        # External device, just mark as ready
        repo.update_status(device.id, DeviceStatus.READY)
        return {"status": "ok", "message": "External Android device ready"}
    
    repo.update_status(device.id, DeviceStatus.SETUP)
    
    try:
        # Create AVD via vmcontrol
        VMCONTROL_URL = "http://localhost:19996"
        with httpx.Client(timeout=60.0) as client:
            response = client.post(
                f"{VMCONTROL_URL}/api/android/avd/create",
                json={
                    "name": device.avd_name,
                    "device": "pixel_7",  # Default to Pixel 7
                    "memory": str(device.memory),  # vmcontrol expects string
                    "cores": device.cpus,
                }
            )
            response.raise_for_status()
        
        repo.update_status(device.id, DeviceStatus.READY)
        return {"status": "ok", "message": "Android AVD created"}
    except Exception as e:
        repo.update_status(device.id, DeviceStatus.ERROR)
        raise HTTPException(status_code=500, detail=str(e))


def _start_linux_device(device: LinuxDevice, repo: DeviceRepository):
    """Start a Linux VM."""
    from gateway.vm.manager import get_vm_manager
    from gateway.config.agents_db import PortConfig
    
    vm_manager = get_vm_manager()
    
    try:
        # Build port config from device ports
        port_config = PortConfig(
            ssh=device.ports.get('ssh', 0),
            vmuse=device.ports.get('vmuse', 0),
        )
        
        # Start VM with device's port config and image path
        result = vm_manager.start(
            agent_id=device.agent_id,
            memory=str(device.memory),
            cpus=device.cpus,
            ports=port_config,
            image_path=device.image_path,
        )
        
        repo.update_status(device.id, DeviceStatus.RUNNING)
        return {"status": "ok", "message": "Linux VM started", **result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def _start_android_device(device: AndroidDevice, repo: DeviceRepository):
    """Start an Android device."""
    import httpx
    
    VMCONTROL_URL = "http://localhost:19996"
    
    try:
        with httpx.Client(timeout=60.0) as client:  # Longer timeout for emulator start
            response = client.post(
                f"{VMCONTROL_URL}/api/android/emulator/start",
                json={"avd": device.avd_name}  # vmcontrol expects "avd" not "avd_name"
            )
            result = response.json()
            
            # Update device serial - vmcontrol returns {"device": {"serial": "..."}}
            device_info = result.get('device', {})
            serial = device_info.get('serial', '')
            if serial:
                repo.update(device.id, 
                    device_serial=serial,
                    status=DeviceStatus.RUNNING,
                )
            else:
                repo.update_status(device.id, DeviceStatus.RUNNING)
            
            return {"status": "ok", "message": "Android device started", "serial": serial, **result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def _stop_device(device: Device):
    """Stop a device."""
    if device.type == DeviceType.LINUX:
        from gateway.vm.manager import get_vm_manager
        vm_manager = get_vm_manager()
        vm_manager.stop(device.agent_id)
        return {"status": "ok", "message": "Linux VM stopped"}
    else:
        import httpx
        VMCONTROL_URL = "http://localhost:19996"
        with httpx.Client(timeout=30.0) as client:
            client.post(
                f"{VMCONTROL_URL}/api/android/emulator/stop",
                json={"serial": device.device_serial}
            )
        return {"status": "ok", "message": "Android device stopped"}


def _is_linux_device_running(device: LinuxDevice) -> bool:
    """Check if Linux VM is running."""
    from gateway.vm.manager import get_vm_manager
    vm_manager = get_vm_manager()
    status = vm_manager.get_status(device.agent_id)
    return status.running if status else False


def _is_android_device_running(device: AndroidDevice) -> bool:
    """Check if Android device is running."""
    import httpx
    VMCONTROL_URL = "http://localhost:19996"
    
    try:
        with httpx.Client(timeout=5.0) as client:
            response = client.get(f"{VMCONTROL_URL}/api/android/devices")
            devices = response.json().get('devices', [])
            for d in devices:
                # Match by serial or avd_name
                if device.device_serial and d.get('serial') == device.device_serial:
                    # vmcontrol returns 'connected' for running emulators
                    return d.get('status') in ['device', 'connected']
                if device.avd_name and d.get('avd_name') == device.avd_name:
                    return d.get('status') in ['device', 'connected']
    except:
        pass
    return False


def _delete_avd(avd_name: str):
    """Delete an AVD via vmcontrol."""
    import httpx
    VMCONTROL_URL = "http://localhost:19996"
    with httpx.Client(timeout=30.0) as client:
        client.delete(f"{VMCONTROL_URL}/api/android/avd/{avd_name}")
