"""
MQTT Client for IoT Gateway
Handles connections to MQTT broker and message routing
"""

import asyncio
import json
import logging
from typing import Callable, Optional
from datetime import datetime

try:
    import paho.mqtt.client as mqtt
except ImportError:
    mqtt = None

logger = logging.getLogger(__name__)


class MQTTClient:
    """MQTT Client for handling sensor connections"""
    
    def __init__(
        self,
        broker_host: str = "localhost",
        broker_port: int = 1883,
        username: Optional[str] = None,
        password: Optional[str] = None,
        device_manager=None,
        data_processor=None
    ):
        self.broker_host = broker_host
        self.broker_port = broker_port
        self.username = username
        self.password = password
        self.device_manager = device_manager
        self.data_processor = data_processor
        
        self.client: Optional[mqtt.Client] = None
        self.connected = False
        
        # Topic patterns
        self.topics = {
            "sensors": "sahool/sensors/+/data",
            "devices": "sahool/devices/+/status",
            "commands": "sahool/commands/+",
        }
    
    async def connect(self):
        """Connect to MQTT broker"""
        if mqtt is None:
            logger.warning("paho-mqtt not installed, MQTT functionality disabled")
            return
        
        try:
            self.client = mqtt.Client(client_id="sahool_iot_gateway")
            
            # Set callbacks
            self.client.on_connect = self._on_connect
            self.client.on_disconnect = self._on_disconnect
            self.client.on_message = self._on_message
            
            # Set credentials if provided
            if self.username and self.password:
                self.client.username_pw_set(self.username, self.password)
            
            # Connect to broker
            self.client.connect(self.broker_host, self.broker_port, 60)
            self.client.loop_start()
            
            logger.info(f"Connecting to MQTT broker at {self.broker_host}:{self.broker_port}")
            
        except Exception as e:
            logger.error(f"Failed to connect to MQTT broker: {e}")
    
    async def disconnect(self):
        """Disconnect from MQTT broker"""
        if self.client:
            self.client.loop_stop()
            self.client.disconnect()
            logger.info("Disconnected from MQTT broker")
    
    def _on_connect(self, client, userdata, flags, rc):
        """Callback when connected to broker"""
        if rc == 0:
            self.connected = True
            logger.info("Connected to MQTT broker successfully")
            
            # Subscribe to topics
            for topic_name, topic_pattern in self.topics.items():
                client.subscribe(topic_pattern)
                logger.info(f"Subscribed to {topic_name}: {topic_pattern}")
        else:
            logger.error(f"Failed to connect to MQTT broker, return code: {rc}")
    
    def _on_disconnect(self, client, userdata, rc):
        """Callback when disconnected from broker"""
        self.connected = False
        if rc != 0:
            logger.warning(f"Unexpected disconnection from MQTT broker, code: {rc}")
        else:
            logger.info("Disconnected from MQTT broker")
    
    def _on_message(self, client, userdata, msg):
        """Callback when message received"""
        try:
            topic = msg.topic
            payload = msg.payload.decode('utf-8')
            
            logger.debug(f"Received message on {topic}: {payload}")
            
            # Parse JSON payload
            data = json.loads(payload)
            
            # Route message based on topic
            if "sensors" in topic:
                self._handle_sensor_data(topic, data)
            elif "devices" in topic:
                self._handle_device_status(topic, data)
            elif "commands" in topic:
                self._handle_command(topic, data)
            
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON in message: {payload}")
        except Exception as e:
            logger.error(f"Error processing message: {e}")
    
    def _handle_sensor_data(self, topic: str, data: dict):
        """Handle sensor data messages"""
        # Extract device ID from topic
        parts = topic.split('/')
        device_id = parts[2] if len(parts) > 2 else "unknown"
        
        # Add metadata
        data['device_id'] = device_id
        data['timestamp'] = data.get('timestamp', datetime.utcnow().isoformat())
        data['topic'] = topic
        
        # Process data
        if self.data_processor:
            asyncio.create_task(self.data_processor.process_sensor_data(data))
        
        # Update device last seen
        if self.device_manager:
            self.device_manager.update_device_activity(device_id)
        
        logger.info(f"Processed sensor data from {device_id}")
    
    def _handle_device_status(self, topic: str, data: dict):
        """Handle device status messages"""
        parts = topic.split('/')
        device_id = parts[2] if len(parts) > 2 else "unknown"
        
        if self.device_manager:
            self.device_manager.update_device_status(device_id, data)
        
        logger.info(f"Updated status for device {device_id}")
    
    def _handle_command(self, topic: str, data: dict):
        """Handle command messages"""
        parts = topic.split('/')
        device_id = parts[2] if len(parts) > 2 else "unknown"
        
        logger.info(f"Received command for device {device_id}: {data}")
        
        # Commands are typically published to device-specific topics
        # This would be implemented based on specific device protocols
    
    def publish(self, topic: str, payload: dict):
        """Publish message to MQTT broker"""
        if self.client and self.connected:
            try:
                payload_str = json.dumps(payload)
                self.client.publish(topic, payload_str)
                logger.debug(f"Published to {topic}: {payload_str}")
            except Exception as e:
                logger.error(f"Failed to publish message: {e}")
        else:
            logger.warning("Cannot publish, not connected to MQTT broker")
    
    def is_connected(self) -> bool:
        """Check if connected to broker"""
        return self.connected
