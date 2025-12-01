"""
Data Processor for IoT Gateway
Processes and validates sensor data before storage
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime
import json

logger = logging.getLogger(__name__)


class DataProcessor:
    """Process and validate sensor data"""

    def __init__(self):
        self.processed_count = 0
        self.error_count = 0

    def process_sensor_data(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Process incoming sensor data

        Args:
            data: Raw sensor data from MQTT

        Returns:
            Processed and validated data, or None if invalid
        """
        try:
            # Validate required fields
            if not self._validate_data(data):
                logger.warning(f"Invalid sensor data: {data}")
                self.error_count += 1
                return None

            # Add processing timestamp
            processed_data = {
                **data,
                "processed_at": datetime.utcnow().isoformat(),
                "processor_version": "1.0.0"
            }

            # Normalize values
            processed_data = self._normalize_data(processed_data)

            # Apply business rules
            processed_data = self._apply_rules(processed_data)

            self.processed_count += 1
            logger.info(f"Processed sensor data from device: {data.get('device_id')}")

            return processed_data

        except Exception as e:
            logger.error(f"Error processing sensor data: {e}", exc_info=True)
            self.error_count += 1
            return None

    def _validate_data(self, data: Dict[str, Any]) -> bool:
        """Validate sensor data structure"""
        required_fields = ["device_id", "timestamp", "data"]

        # Check required fields
        for field in required_fields:
            if field not in data:
                logger.error(f"Missing required field: {field}")
                return False

        # Validate timestamp format
        try:
            datetime.fromisoformat(data["timestamp"].replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            logger.error(f"Invalid timestamp format: {data.get('timestamp')}")
            return False

        # Validate data payload
        if not isinstance(data["data"], dict):
            logger.error("Sensor data payload must be a dictionary")
            return False

        return True

    def _normalize_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize sensor values"""
        sensor_data = data.get("data", {})

        # Round numeric values to 2 decimal places
        for key, value in sensor_data.items():
            if isinstance(value, (int, float)):
                sensor_data[key] = round(value, 2)

        data["data"] = sensor_data
        return data

    def _apply_rules(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Apply business rules and add alerts if needed"""
        sensor_data = data.get("data", {})
        alerts = []

        # Soil moisture rules
        if "moisture" in sensor_data:
            moisture = sensor_data["moisture"]
            if moisture < 20:
                alerts.append({
                    "type": "low_moisture",
                    "severity": "high",
                    "message": "Soil moisture critically low"
                })
            elif moisture < 30:
                alerts.append({
                    "type": "low_moisture",
                    "severity": "medium",
                    "message": "Soil moisture low"
                })

        # Temperature rules
        if "temperature" in sensor_data:
            temp = sensor_data["temperature"]
            if temp > 40:
                alerts.append({
                    "type": "high_temperature",
                    "severity": "high",
                    "message": "Temperature critically high"
                })
            elif temp < 0:
                alerts.append({
                    "type": "low_temperature",
                    "severity": "high",
                    "message": "Freezing temperature detected"
                })

        # Battery rules
        if "battery" in sensor_data:
            battery = sensor_data["battery"]
            if battery < 15:
                alerts.append({
                    "type": "low_battery",
                    "severity": "medium",
                    "message": "Device battery critically low"
                })

        if alerts:
            data["alerts"] = alerts

        return data

    def get_stats(self) -> Dict[str, int]:
        """Get processing statistics"""
        return {
            "processed_count": self.processed_count,
            "error_count": self.error_count,
            "success_rate": round(
                (self.processed_count / (self.processed_count + self.error_count) * 100)
                if (self.processed_count + self.error_count) > 0 else 0,
                2
            )
        }
