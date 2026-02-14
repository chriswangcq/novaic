"""
Device Repository - Database operations for unified devices.
"""

from typing import Optional, List, Dict, Any
import json
import logging

from gateway.db.access import Database
from gateway.config.devices import (
    Device, LinuxDevice, AndroidDevice, 
    DeviceType, DeviceStatus, device_from_dict
)

logger = logging.getLogger(__name__)


class DeviceRepository:
    """Repository for device CRUD operations."""
    
    def __init__(self, db: Database):
        self.db = db
    
    def create(self, device: Device) -> Device:
        """Create a new device."""
        with self.db.transaction("global"):
            self.db.execute("""
                INSERT INTO devices (
                    id, agent_id, type, name, created_at, status,
                    memory, cpus, data_path, ports,
                    backend, os_type, os_version, image_path, cloud_init_complete,
                    avd_name, device_serial, managed, system_image
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                device.id,
                device.agent_id,
                device.type.value,
                device.name,
                device.created_at,
                device.status.value,
                device.memory,
                device.cpus,
                device.data_path,
                json.dumps(device.ports),
                getattr(device, 'backend', 'qemu'),
                getattr(device, 'os_type', 'ubuntu'),
                getattr(device, 'os_version', '24.04'),
                getattr(device, 'image_path', ''),
                1 if getattr(device, 'cloud_init_complete', False) else 0,
                getattr(device, 'avd_name', ''),
                getattr(device, 'device_serial', ''),
                1 if getattr(device, 'managed', True) else 0,
                getattr(device, 'system_image', ''),
            ))
        return device
    
    def get(self, device_id: str) -> Optional[Device]:
        """Get a device by ID."""
        row = self.db.fetchone(
            "SELECT * FROM devices WHERE id = ?",
            (device_id,)
        )
        if not row:
            return None
        return self._row_to_device(row)
    
    def list_by_agent(self, agent_id: str) -> List[Device]:
        """List all devices for an agent."""
        rows = self.db.fetchall(
            "SELECT * FROM devices WHERE agent_id = ? ORDER BY created_at",
            (agent_id,)
        )
        return [self._row_to_device(row) for row in rows]
    
    def list_by_type(self, agent_id: str, device_type: DeviceType) -> List[Device]:
        """List devices of a specific type for an agent."""
        rows = self.db.fetchall(
            "SELECT * FROM devices WHERE agent_id = ? AND type = ? ORDER BY created_at",
            (agent_id, device_type.value)
        )
        return [self._row_to_device(row) for row in rows]
    
    def get_first_by_type(self, agent_id: str, device_type: DeviceType) -> Optional[Device]:
        """Get the first device of a specific type for an agent."""
        row = self.db.fetchone(
            "SELECT * FROM devices WHERE agent_id = ? AND type = ? ORDER BY created_at LIMIT 1",
            (agent_id, device_type.value)
        )
        if not row:
            return None
        return self._row_to_device(row)
    
    def update(self, device_id: str, **kwargs) -> Optional[Device]:
        """Update a device."""
        if not kwargs:
            return self.get(device_id)
        
        # Handle special fields
        if 'ports' in kwargs and isinstance(kwargs['ports'], dict):
            kwargs['ports'] = json.dumps(kwargs['ports'])
        if 'status' in kwargs and isinstance(kwargs['status'], DeviceStatus):
            kwargs['status'] = kwargs['status'].value
        if 'type' in kwargs and isinstance(kwargs['type'], DeviceType):
            kwargs['type'] = kwargs['type'].value
        
        # Build update query
        set_clauses = [f"{k} = ?" for k in kwargs.keys()]
        values = list(kwargs.values()) + [device_id]
        
        with self.db.transaction("global"):
            self.db.execute(
                f"UPDATE devices SET {', '.join(set_clauses)} WHERE id = ?",
                tuple(values)
            )
        return self.get(device_id)
    
    def update_status(self, device_id: str, status: DeviceStatus) -> Optional[Device]:
        """Update device status."""
        return self.update(device_id, status=status.value)
    
    def delete(self, device_id: str) -> bool:
        """Delete a device."""
        with self.db.transaction("global"):
            self.db.execute("DELETE FROM devices WHERE id = ?", (device_id,))
        return True
    
    def delete_by_agent(self, agent_id: str) -> int:
        """Delete all devices for an agent."""
        with self.db.transaction("global"):
            cursor = self.db.execute(
                "DELETE FROM devices WHERE agent_id = ?",
                (agent_id,)
            )
            return cursor.rowcount
    
    def _row_to_device(self, row: Dict[str, Any]) -> Device:
        """Convert a database row to a Device object."""
        data = {
            'id': row['id'],
            'agent_id': row['agent_id'],
            'type': row['type'],
            'name': row['name'] or '',
            'created_at': row['created_at'] or '',
            'status': row['status'],
            'memory': row['memory'],
            'cpus': row['cpus'],
            'data_path': row['data_path'] or '',
            'ports': json.loads(row['ports'] or '{}'),
        }
        
        if row['type'] == 'linux':
            data.update({
                'backend': row['backend'] or 'qemu',
                'os_type': row['os_type'] or 'ubuntu',
                'os_version': row['os_version'] or '24.04',
                'image_path': row['image_path'] or '',
                'cloud_init_complete': bool(row['cloud_init_complete']),
            })
            return LinuxDevice(**data)
        else:
            data.update({
                'avd_name': row['avd_name'] or '',
                'device_serial': row['device_serial'] or '',
                'managed': bool(row['managed']),
                'system_image': row['system_image'] or '',
            })
            return AndroidDevice(**data)
