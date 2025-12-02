#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════════════
# Part 6: Backend Celery Tasks
# ═══════════════════════════════════════════════════════════════════════════════

log_info "إنشاء مهام Celery..."

# ─────────────────────────────────────────────────────────────────────────────
# Celery Configuration
# ─────────────────────────────────────────────────────────────────────────────
cat > "$PROJECT_NAME/backend/app/tasks/celery_app.py" << 'EOF'
"""
Celery Application Configuration
إعداد تطبيق Celery
"""
from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "field_suite_tasks",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "app.tasks.ndvi_tasks",
        "app.tasks.notification_tasks",
        "app.tasks.report_tasks"
    ]
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 hour max
    task_soft_time_limit=3000,  # 50 minutes soft limit
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    result_expires=86400,  # 24 hours

    # Task routing
    task_routes={
        "app.tasks.ndvi_tasks.*": {"queue": "ndvi"},
        "app.tasks.notification_tasks.*": {"queue": "notifications"},
        "app.tasks.report_tasks.*": {"queue": "reports"},
    },

    # Beat schedule for periodic tasks
    beat_schedule={
        "daily-ndvi-update": {
            "task": "app.tasks.ndvi_tasks.scheduled_ndvi_update",
            "schedule": 86400.0,  # Every 24 hours
        },
        "cleanup-expired-tokens": {
            "task": "app.tasks.cleanup_tasks.cleanup_expired_tokens",
            "schedule": 3600.0,  # Every hour
        },
    }
)
EOF

# ─────────────────────────────────────────────────────────────────────────────
# NDVI Tasks
# ─────────────────────────────────────────────────────────────────────────────
cat > "$PROJECT_NAME/backend/app/tasks/ndvi_tasks.py" << 'EOF'
"""
NDVI Computation Tasks
مهام حساب NDVI
"""
from typing import List, Dict, Any
from datetime import date, datetime
from celery import shared_task
import numpy as np
import rasterio
from rasterio.mask import mask
from shapely.geometry import shape
import httpx
import tempfile
import os

from app.tasks.celery_app import celery_app
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


@celery_app.task(bind=True, name="app.tasks.ndvi_tasks.compute_ndvi_task")
def compute_ndvi_task(
    self,
    field_ids: List[int],
    start_date: str,
    end_date: str,
    tenant_id: int,
    force_recompute: bool = False
) -> Dict[str, Any]:
    """
    Compute NDVI for multiple fields
    حساب NDVI لعدة حقول
    """
    logger.info(f"Starting NDVI computation for {len(field_ids)} fields")

    results = []
    total = len(field_ids)

    for i, field_id in enumerate(field_ids):
        try:
            # Update progress
            self.update_state(
                state="PROGRESS",
                meta={
                    "current": i + 1,
                    "total": total,
                    "field_id": field_id,
                    "status": "processing"
                }
            )

            # Compute NDVI for this field
            result = _compute_field_ndvi(
                field_id=field_id,
                start_date=start_date,
                end_date=end_date,
                tenant_id=tenant_id
            )

            results.append({
                "field_id": field_id,
                "status": "success",
                "data": result
            })

        except Exception as e:
            logger.error(f"Error computing NDVI for field {field_id}: {e}")
            results.append({
                "field_id": field_id,
                "status": "error",
                "error": str(e)
            })

    logger.info(f"NDVI computation completed for {len(field_ids)} fields")

    return {
        "status": "completed",
        "total_fields": total,
        "successful": len([r for r in results if r["status"] == "success"]),
        "failed": len([r for r in results if r["status"] == "error"]),
        "results": results
    }


def _compute_field_ndvi(
    field_id: int,
    start_date: str,
    end_date: str,
    tenant_id: int
) -> Dict[str, Any]:
    """Compute NDVI for a single field"""
    # In production, this would:
    # 1. Get field geometry from database
    # 2. Query Sentinel Hub API for satellite imagery
    # 3. Download and process bands
    # 4. Calculate NDVI
    # 5. Save results to database

    # Simulated computation for demo
    np.random.seed(field_id)

    # Generate mock NDVI values
    mean_ndvi = np.random.uniform(0.3, 0.8)
    std_ndvi = np.random.uniform(0.05, 0.15)

    # Calculate zones
    zones = {
        "critical": max(0, np.random.uniform(0, 0.1)),
        "low": np.random.uniform(0.1, 0.25),
        "medium": np.random.uniform(0.25, 0.4),
        "high": np.random.uniform(0.2, 0.35),
        "very_high": max(0, 1 - np.random.uniform(0.7, 0.9))
    }

    # Normalize zones to 100%
    total = sum(zones.values())
    zones = {k: round(v / total * 100, 2) for k, v in zones.items()}

    return {
        "field_id": field_id,
        "analysis_date": end_date,
        "mean_ndvi": round(mean_ndvi, 4),
        "min_ndvi": round(mean_ndvi - 2 * std_ndvi, 4),
        "max_ndvi": round(mean_ndvi + 2 * std_ndvi, 4),
        "std_ndvi": round(std_ndvi, 4),
        "median_ndvi": round(mean_ndvi + np.random.uniform(-0.05, 0.05), 4),
        "zones": zones,
        "pixel_count": np.random.randint(10000, 50000),
        "cloud_coverage": round(np.random.uniform(0, 20), 2),
        "satellite_source": "sentinel-2"
    }


@celery_app.task(name="app.tasks.ndvi_tasks.scheduled_ndvi_update")
def scheduled_ndvi_update() -> Dict[str, Any]:
    """
    Scheduled task to update NDVI for all active fields
    مهمة مجدولة لتحديث NDVI لجميع الحقول النشطة
    """
    logger.info("Starting scheduled NDVI update")

    # In production, this would:
    # 1. Get all active fields
    # 2. Check which fields need updates
    # 3. Queue computation tasks

    return {
        "status": "completed",
        "message": "Scheduled NDVI update completed"
    }


@celery_app.task(bind=True, name="app.tasks.ndvi_tasks.process_satellite_image")
def process_satellite_image(
    self,
    image_path: str,
    field_geometry: Dict,
    output_path: str
) -> Dict[str, Any]:
    """
    Process satellite image and extract NDVI
    معالجة صورة القمر الصناعي واستخراج NDVI
    """
    try:
        with rasterio.open(image_path) as src:
            # Get geometry
            geom = shape(field_geometry)

            # Mask raster with field geometry
            out_image, out_transform = mask(src, [geom], crop=True)

            # Extract bands (assuming B4=Red, B8=NIR for Sentinel-2)
            red = out_image[0].astype(float)
            nir = out_image[1].astype(float)

            # Calculate NDVI
            with np.errstate(divide='ignore', invalid='ignore'):
                ndvi = (nir - red) / (nir + red)
                ndvi = np.nan_to_num(ndvi, nan=0, posinf=1, neginf=-1)

            # Calculate statistics
            valid_pixels = ndvi[~np.isnan(ndvi) & (ndvi != 0)]

            return {
                "mean": float(np.mean(valid_pixels)),
                "std": float(np.std(valid_pixels)),
                "min": float(np.min(valid_pixels)),
                "max": float(np.max(valid_pixels)),
                "median": float(np.median(valid_pixels)),
                "pixel_count": len(valid_pixels)
            }

    except Exception as e:
        logger.error(f"Error processing satellite image: {e}")
        raise
EOF

# ─────────────────────────────────────────────────────────────────────────────
# Notification Tasks
# ─────────────────────────────────────────────────────────────────────────────
cat > "$PROJECT_NAME/backend/app/tasks/notification_tasks.py" << 'EOF'
"""
Notification Tasks
مهام الإشعارات
"""
from typing import List, Dict, Any
from celery import shared_task
import httpx

from app.tasks.celery_app import celery_app
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


@celery_app.task(name="app.tasks.notification_tasks.send_email")
def send_email(
    to: List[str],
    subject: str,
    body: str,
    html_body: str = None
) -> Dict[str, Any]:
    """
    Send email notification
    إرسال إشعار بريد إلكتروني
    """
    logger.info(f"Sending email to {len(to)} recipients: {subject}")

    # In production, integrate with email service (SendGrid, SES, etc.)
    # For now, just log

    return {
        "status": "sent",
        "recipients": len(to),
        "subject": subject
    }


@celery_app.task(name="app.tasks.notification_tasks.send_sms")
def send_sms(
    phone_numbers: List[str],
    message: str
) -> Dict[str, Any]:
    """
    Send SMS notification
    إرسال إشعار SMS
    """
    logger.info(f"Sending SMS to {len(phone_numbers)} numbers")

    # In production, integrate with SMS service (Twilio, etc.)

    return {
        "status": "sent",
        "recipients": len(phone_numbers)
    }


@celery_app.task(name="app.tasks.notification_tasks.send_push_notification")
def send_push_notification(
    user_ids: List[int],
    title: str,
    body: str,
    data: Dict = None
) -> Dict[str, Any]:
    """
    Send push notification
    إرسال إشعار push
    """
    logger.info(f"Sending push notification to {len(user_ids)} users")

    # In production, integrate with Firebase FCM

    return {
        "status": "sent",
        "recipients": len(user_ids)
    }


@celery_app.task(name="app.tasks.notification_tasks.send_alert_notification")
def send_alert_notification(
    alert_id: int,
    field_id: int,
    tenant_id: int,
    alert_type: str,
    title: str,
    message: str
) -> Dict[str, Any]:
    """
    Send alert notification to relevant users
    إرسال تنبيه للمستخدمين المعنيين
    """
    logger.info(f"Processing alert notification: {alert_type} for field {field_id}")

    # In production:
    # 1. Get users subscribed to this field/alert type
    # 2. Get user notification preferences
    # 3. Send via appropriate channels

    return {
        "status": "processed",
        "alert_id": alert_id,
        "notifications_sent": 0
    }
EOF

# ─────────────────────────────────────────────────────────────────────────────
# Report Tasks
# ─────────────────────────────────────────────────────────────────────────────
cat > "$PROJECT_NAME/backend/app/tasks/report_tasks.py" << 'EOF'
"""
Report Generation Tasks
مهام إنشاء التقارير
"""
from typing import Dict, Any, List
from datetime import date, datetime
from celery import shared_task
import json

from app.tasks.celery_app import celery_app
from app.core.logging import get_logger

logger = get_logger(__name__)


@celery_app.task(bind=True, name="app.tasks.report_tasks.generate_field_report")
def generate_field_report(
    self,
    field_id: int,
    tenant_id: int,
    start_date: str,
    end_date: str,
    report_type: str = "comprehensive"
) -> Dict[str, Any]:
    """
    Generate comprehensive field report
    إنشاء تقرير شامل للحقل
    """
    logger.info(f"Generating {report_type} report for field {field_id}")

    self.update_state(
        state="PROGRESS",
        meta={"status": "collecting_data", "progress": 10}
    )

    # In production:
    # 1. Collect NDVI data
    # 2. Collect weather data
    # 3. Collect recommendations history
    # 4. Generate visualizations
    # 5. Create PDF/HTML report

    self.update_state(
        state="PROGRESS",
        meta={"status": "generating_report", "progress": 80}
    )

    report = {
        "field_id": field_id,
        "period": {
            "start": start_date,
            "end": end_date
        },
        "generated_at": datetime.utcnow().isoformat(),
        "type": report_type,
        "sections": [
            {"name": "overview", "status": "generated"},
            {"name": "ndvi_analysis", "status": "generated"},
            {"name": "weather_summary", "status": "generated"},
            {"name": "recommendations", "status": "generated"}
        ],
        "download_url": f"/api/v1/reports/{field_id}/download"
    }

    logger.info(f"Report generated for field {field_id}")

    return {
        "status": "completed",
        "report": report
    }


@celery_app.task(name="app.tasks.report_tasks.generate_tenant_summary")
def generate_tenant_summary(
    tenant_id: int,
    month: int,
    year: int
) -> Dict[str, Any]:
    """
    Generate monthly summary for tenant
    إنشاء ملخص شهري للمستأجر
    """
    logger.info(f"Generating monthly summary for tenant {tenant_id}: {month}/{year}")

    return {
        "status": "completed",
        "tenant_id": tenant_id,
        "period": f"{year}-{month:02d}",
        "summary": {
            "total_fields": 0,
            "total_area_ha": 0,
            "avg_ndvi": 0,
            "recommendations_count": 0,
            "alerts_count": 0
        }
    }


@celery_app.task(name="app.tasks.report_tasks.export_data")
def export_data(
    tenant_id: int,
    export_type: str,
    filters: Dict[str, Any],
    format: str = "csv"
) -> Dict[str, Any]:
    """
    Export data to file
    تصدير البيانات لملف
    """
    logger.info(f"Exporting {export_type} data for tenant {tenant_id}")

    # In production:
    # 1. Query data based on filters
    # 2. Format data
    # 3. Generate file
    # 4. Upload to storage
    # 5. Return download URL

    return {
        "status": "completed",
        "export_type": export_type,
        "format": format,
        "download_url": f"/api/v1/exports/{tenant_id}/download"
    }
EOF

# ─────────────────────────────────────────────────────────────────────────────
# Tasks Init
# ─────────────────────────────────────────────────────────────────────────────
cat > "$PROJECT_NAME/backend/app/tasks/__init__.py" << 'EOF'
"""Celery Tasks"""
from app.tasks.celery_app import celery_app
from app.tasks.ndvi_tasks import compute_ndvi_task, scheduled_ndvi_update
from app.tasks.notification_tasks import send_email, send_sms, send_alert_notification
from app.tasks.report_tasks import generate_field_report, export_data

__all__ = [
    "celery_app",
    "compute_ndvi_task",
    "scheduled_ndvi_update",
    "send_email",
    "send_sms",
    "send_alert_notification",
    "generate_field_report",
    "export_data"
]
EOF

log_success "تم إنشاء مهام Celery"
