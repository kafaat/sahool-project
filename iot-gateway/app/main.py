"""
IoT Gateway Service - Sahool Agricultural Platform
Handles MQTT connections, sensor data ingestion, and device management
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import asyncio
from typing import List
import logging

from app.mqtt_client import MQTTClient
from app.device_manager import DeviceManager
from app.data_processor import DataProcessor
from app.api import router as api_router

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global instances
mqtt_client: MQTTClient = None
device_manager: DeviceManager = None
data_processor: DataProcessor = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    global mqtt_client, device_manager, data_processor
    
    # Startup
    logger.info("Starting IoT Gateway Service...")
    
    device_manager = DeviceManager()
    data_processor = DataProcessor()
    mqtt_client = MQTTClient(
        broker_host="localhost",
        broker_port=1883,
        device_manager=device_manager,
        data_processor=data_processor
    )
    
    # Start MQTT client
    await mqtt_client.connect()
    
    logger.info("IoT Gateway Service started successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down IoT Gateway Service...")
    await mqtt_client.disconnect()
    logger.info("IoT Gateway Service stopped")


app = FastAPI(
    title="Sahool IoT Gateway",
    description="IoT Gateway for agricultural sensors and devices",
    version="1.0.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router, prefix="/api/v1")


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Sahool IoT Gateway",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "mqtt_connected": mqtt_client.is_connected() if mqtt_client else False,
        "active_devices": device_manager.get_active_count() if device_manager else 0
    }


# WebSocket for real-time sensor data
active_connections: List[WebSocket] = []


@app.websocket("/ws/sensors")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time sensor data"""
    await websocket.accept()
    active_connections.append(websocket)
    
    try:
        while True:
            # Keep connection alive
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        active_connections.remove(websocket)
        logger.info("WebSocket client disconnected")


async def broadcast_sensor_data(data: dict):
    """Broadcast sensor data to all connected WebSocket clients"""
    for connection in active_connections:
        try:
            await connection.send_json(data)
        except Exception as e:
            logger.error(f"Error broadcasting to WebSocket: {e}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8005)
