"""
Device Manager for IoT Gateway
Manages registered devices and their status
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class Device:
    """Represents an IoT device"""
    
    def __init__(
        self,
        device_id: str,
        device_type: str,
        field_id: Optional[int] = None,
        location: Optional[Dict] = None,
        metadata: Optional[Dict] = None
    ):
        self.device_id = device_id
        self.device_type = device_type
        self.field_id = field_id
        self.location = location or {}
        self.metadata = metadata or {}
        
        self.status = "offline"
        self.last_seen = None
        self.last_data = None
        self.battery_level = None
        self.signal_strength = None
    
    def to_dict(self) -> Dict:
        """Convert device to dictionary"""
        return {
            "device_id": self.device_id,
            "device_type": self.device_type,
            "field_id": self.field_id,
            "location": self.location,
            "status": self.status,
            "last_seen": self.last_seen.isoformat() if self.last_seen else None,
            "battery_level": self.battery_level,
            "signal_strength": self.signal_strength,
            "metadata": self.metadata
        }


class DeviceManager:
    """Manages IoT devices"""
    
    def __init__(self):
        self.devices: Dict[str, Device] = {}
        self.activity_timeout = timedelta(minutes=5)
    
    def register_device(
        self,
        device_id: str,
        device_type: str,
        field_id: Optional[int] = None,
        location: Optional[Dict] = None,
        metadata: Optional[Dict] = None
    ) -> Device:
        """Register a new device"""
        device = Device(
            device_id=device_id,
            device_type=device_type,
            field_id=field_id,
            location=location,
            metadata=metadata
        )
        
        self.devices[device_id] = device
        logger.info(f"Registered device: {device_id} ({device_type})")
        
        return device
    
    def unregister_device(self, device_id: str) -> bool:
        """Unregister a device"""
        if device_id in self.devices:
            del self.devices[device_id]
            logger.info(f"Unregistered device: {device_id}")
            return True
        return False
    
    def get_device(self, device_id: str) -> Optional[Device]:
        """Get device by ID"""
        return self.devices.get(device_id)
    
    def get_all_devices(self) -> List[Device]:
        """Get all registered devices"""
        return list(self.devices.values())
    
    def get_devices_by_field(self, field_id: int) -> List[Device]:
        """Get all devices for a specific field"""
        return [
            device for device in self.devices.values()
            if device.field_id == field_id
        ]
    
    def get_devices_by_type(self, device_type: str) -> List[Device]:
        """Get all devices of a specific type"""
        return [
            device for device in self.devices.values()
            if device.device_type == device_type
        ]
    
    def update_device_activity(self, device_id: str):
        """Update device last seen timestamp"""
        device = self.devices.get(device_id)
        if device:
            device.last_seen = datetime.utcnow()
            device.status = "online"
            logger.debug(f"Updated activity for device: {device_id}")
    
    def update_device_status(self, device_id: str, status_data: Dict):
        """Update device status"""
        device = self.devices.get(device_id)
        if device:
            device.battery_level = status_data.get('battery_level')
            device.signal_strength = status_data.get('signal_strength')
            device.status = status_data.get('status', 'online')
            device.last_seen = datetime.utcnow()
            
            logger.debug(f"Updated status for device: {device_id}")
    
    def update_device_data(self, device_id: str, data: Dict):
        """Update device last data"""
        device = self.devices.get(device_id)
        if device:
            device.last_data = data
            device.last_seen = datetime.utcnow()
    
    def check_device_timeouts(self):
        """Check for devices that haven't reported in a while"""
        now = datetime.utcnow()
        
        for device in self.devices.values():
            if device.last_seen:
                time_since_seen = now - device.last_seen
                if time_since_seen > self.activity_timeout:
                    if device.status != "offline":
                        device.status = "offline"
                        logger.warning(f"Device {device.device_id} marked as offline")
    
    def get_active_count(self) -> int:
        """Get count of active (online) devices"""
        return sum(1 for device in self.devices.values() if device.status == "online")
    
    def get_offline_count(self) -> int:
        """Get count of offline devices"""
        return sum(1 for device in self.devices.values() if device.status == "offline")
