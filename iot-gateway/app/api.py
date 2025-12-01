"""
API Routes for IoT Gateway
Handles device management and sensor data endpoints
"""

from fastapi import APIRouter, HTTPException, status, Depends
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, validator
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

router = APIRouter(tags=["IoT Gateway"])


# Pydantic Models
class DeviceRegistration(BaseModel):
    """Device registration request"""
    device_id: str = Field(..., min_length=3, max_length=100)
    device_type: str = Field(..., min_length=3, max_length=50)
    field_id: int = Field(..., gt=0)
    location: Optional[Dict[str, float]] = None

    @validator('device_type')
    def validate_device_type(cls, v):
        allowed_types = [
            "soil_moisture", "temperature", "humidity",
            "light", "ph", "ec", "weather_station"
        ]
        if v not in allowed_types:
            raise ValueError(f"Device type must be one of: {', '.join(allowed_types)}")
        return v


class DeviceUpdate(BaseModel):
    """Device update request"""
    device_type: Optional[str] = None
    field_id: Optional[int] = None
    location: Optional[Dict[str, float]] = None
    active: Optional[bool] = None


class SensorData(BaseModel):
    """Sensor data model"""
    device_id: str
    timestamp: str
    data: Dict[str, Any]

    @validator('timestamp')
    def validate_timestamp(cls, v):
        try:
            datetime.fromisoformat(v.replace("Z", "+00:00"))
        except ValueError:
            raise ValueError("Invalid timestamp format. Use ISO format.")
        return v


class DeviceResponse(BaseModel):
    """Device response model"""
    device_id: str
    device_type: str
    field_id: int
    status: str
    last_seen: Optional[str] = None
    battery_level: Optional[int] = None
    signal_strength: Optional[int] = None


# In-memory storage (replace with database in production)
devices_db: Dict[str, Dict[str, Any]] = {}
sensor_data_db: List[Dict[str, Any]] = []


# Device Management Endpoints

@router.post("/devices", response_model=DeviceResponse, status_code=status.HTTP_201_CREATED)
async def register_device(device: DeviceRegistration):
    """
    Register a new IoT device

    - **device_id**: Unique device identifier
    - **device_type**: Type of sensor device
    - **field_id**: Associated field ID
    - **location**: Optional GPS coordinates
    """
    if device.device_id in devices_db:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Device {device.device_id} already registered"
        )

    device_data = {
        "device_id": device.device_id,
        "device_type": device.device_type,
        "field_id": device.field_id,
        "location": device.location,
        "status": "online",
        "registered_at": datetime.utcnow().isoformat(),
        "last_seen": datetime.utcnow().isoformat(),
        "battery_level": 100,
        "signal_strength": -50
    }

    devices_db[device.device_id] = device_data
    logger.info(f"Device registered: {device.device_id}")

    return DeviceResponse(**device_data)


@router.get("/devices", response_model=List[DeviceResponse])
async def list_devices(
    field_id: Optional[int] = None,
    device_type: Optional[str] = None,
    status: Optional[str] = None
):
    """
    List all registered devices with optional filtering

    - **field_id**: Filter by field ID
    - **device_type**: Filter by device type
    - **status**: Filter by status (online/offline)
    """
    devices = list(devices_db.values())

    # Apply filters
    if field_id is not None:
        devices = [d for d in devices if d["field_id"] == field_id]

    if device_type is not None:
        devices = [d for d in devices if d["device_type"] == device_type]

    if status is not None:
        devices = [d for d in devices if d["status"] == status]

    return [DeviceResponse(**d) for d in devices]


@router.get("/devices/{device_id}", response_model=DeviceResponse)
async def get_device(device_id: str):
    """Get device details by ID"""
    if device_id not in devices_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Device {device_id} not found"
        )

    return DeviceResponse(**devices_db[device_id])


@router.put("/devices/{device_id}", response_model=DeviceResponse)
async def update_device(device_id: str, update: DeviceUpdate):
    """Update device information"""
    if device_id not in devices_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Device {device_id} not found"
        )

    device = devices_db[device_id]

    # Update fields
    if update.device_type is not None:
        device["device_type"] = update.device_type
    if update.field_id is not None:
        device["field_id"] = update.field_id
    if update.location is not None:
        device["location"] = update.location
    if update.active is not None:
        device["status"] = "online" if update.active else "offline"

    device["updated_at"] = datetime.utcnow().isoformat()

    logger.info(f"Device updated: {device_id}")
    return DeviceResponse(**device)


@router.delete("/devices/{device_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_device(device_id: str):
    """Unregister a device"""
    if device_id not in devices_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Device {device_id} not found"
        )

    del devices_db[device_id]
    logger.info(f"Device deleted: {device_id}")
    return None


# Sensor Data Endpoints

@router.post("/sensors/data", status_code=status.HTTP_201_CREATED)
async def ingest_sensor_data(data: SensorData):
    """
    Ingest sensor data from devices

    This endpoint is typically called by MQTT bridge or directly by devices
    """
    # Verify device exists
    if data.device_id not in devices_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Device {data.device_id} not registered"
        )

    # Update device last_seen
    devices_db[data.device_id]["last_seen"] = datetime.utcnow().isoformat()
    devices_db[data.device_id]["status"] = "online"

    # Store sensor data
    sensor_entry = {
        "device_id": data.device_id,
        "timestamp": data.timestamp,
        "data": data.data,
        "received_at": datetime.utcnow().isoformat()
    }

    sensor_data_db.append(sensor_entry)

    # Keep only last 1000 entries (in production, use database with TTL)
    if len(sensor_data_db) > 1000:
        sensor_data_db.pop(0)

    logger.info(f"Sensor data ingested from device: {data.device_id}")

    return {
        "status": "success",
        "device_id": data.device_id,
        "timestamp": data.timestamp
    }


@router.get("/sensors/data")
async def get_sensor_data(
    device_id: Optional[str] = None,
    field_id: Optional[int] = None,
    limit: int = 100
):
    """
    Get sensor data with optional filtering

    - **device_id**: Filter by specific device
    - **field_id**: Filter by field ID
    - **limit**: Maximum number of records (default: 100)
    """
    data = sensor_data_db.copy()

    # Filter by device_id
    if device_id is not None:
        data = [d for d in data if d["device_id"] == device_id]

    # Filter by field_id
    if field_id is not None:
        device_ids = [
            dev_id for dev_id, dev in devices_db.items()
            if dev["field_id"] == field_id
        ]
        data = [d for d in data if d["device_id"] in device_ids]

    # Limit results
    data = data[-limit:]

    return {
        "count": len(data),
        "data": data
    }


@router.get("/sensors/{device_id}/latest")
async def get_latest_sensor_data(device_id: str):
    """Get the latest sensor reading from a specific device"""
    if device_id not in devices_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Device {device_id} not registered"
        )

    # Find latest data for this device
    device_data = [d for d in sensor_data_db if d["device_id"] == device_id]

    if not device_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No data found for device {device_id}"
        )

    return device_data[-1]


# Field-specific Endpoints

@router.get("/fields/{field_id}/devices", response_model=List[DeviceResponse])
async def get_field_devices(field_id: int):
    """Get all devices for a specific field"""
    devices = [d for d in devices_db.values() if d["field_id"] == field_id]

    if not devices:
        return []

    return [DeviceResponse(**d) for d in devices]


@router.get("/fields/{field_id}/sensors")
async def get_field_sensor_data(field_id: int, limit: int = 100):
    """Get all sensor data for a specific field"""
    # Get all devices for this field
    device_ids = [
        dev_id for dev_id, dev in devices_db.items()
        if dev["field_id"] == field_id
    ]

    if not device_ids:
        return {
            "field_id": field_id,
            "device_count": 0,
            "data": []
        }

    # Get sensor data for these devices
    field_data = [
        d for d in sensor_data_db
        if d["device_id"] in device_ids
    ][-limit:]

    return {
        "field_id": field_id,
        "device_count": len(device_ids),
        "data_count": len(field_data),
        "data": field_data
    }


# Stats and Monitoring

@router.get("/stats")
async def get_stats():
    """Get IoT Gateway statistics"""
    return {
        "total_devices": len(devices_db),
        "online_devices": len([d for d in devices_db.values() if d["status"] == "online"]),
        "offline_devices": len([d for d in devices_db.values() if d["status"] == "offline"]),
        "total_data_points": len(sensor_data_db),
        "device_types": {
            device_type: len([d for d in devices_db.values() if d["device_type"] == device_type])
            for device_type in set(d["device_type"] for d in devices_db.values())
        }
    }
