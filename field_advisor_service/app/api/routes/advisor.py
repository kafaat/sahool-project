"""
Field Advisor API Routes
"""
from typing import Optional, List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ...models import get_db
from ...schemas.advisor import (
    AnalyzeFieldRequest,
    AnalyzeFieldResponse,
    RecommendationResponse,
    AlertResponse,
    PlaybookRequest,
    PlaybookResponse,
    ActionLogCreate,
    ActionLogResponse,
    RecommendationType,
    AlertSeverity,
    AlertStatus,
    ActionStatus,
)
from ...services.advisor_service import AdvisorService
from ...core.logging import logger

router = APIRouter(prefix="/advisor", tags=["Field Advisor"])


# ==================== Analysis Endpoints ====================

@router.post("/analyze-field", response_model=AnalyzeFieldResponse)
async def analyze_field(
    request: AnalyzeFieldRequest,
    db: Session = Depends(get_db),
):
    """
    Analyze a field and generate recommendations

    This endpoint:
    1. Aggregates context from NDVI, Weather, Crop, and Soil data
    2. Runs the rules engine to generate recommendations and alerts
    3. Stores the analysis session and results
    4. Returns comprehensive analysis with actionable insights

    **Request Body:**
    - `field_id`: UUID of the field to analyze
    - `tenant_id`: Optional tenant UUID for multi-tenant environments
    - `include_weather`: Include weather data in analysis (default: true)
    - `include_forecast`: Include weather forecast (default: true)
    - `analysis_depth`: quick, standard, or deep analysis (default: standard)
    - `language`: Response language - en or ar (default: en)

    **Optional Overrides:**
    - `ndvi_data`: Override NDVI data
    - `weather_data`: Override weather data
    - `crop_data`: Override crop data
    - `soil_data`: Override soil data
    """
    logger.info(f"Analyze field request received for {request.field_id}")

    service = AdvisorService(db)

    try:
        result = await service.analyze_field(request)
        return result
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


# ==================== Recommendations Endpoints ====================

@router.get("/recommendations/{field_id}", response_model=List[RecommendationResponse])
async def get_recommendations(
    field_id: UUID,
    type: Optional[RecommendationType] = Query(None, description="Filter by type"),
    active_only: bool = Query(True, description="Only active recommendations"),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """
    Get recommendations for a field

    Returns list of recommendations sorted by priority (highest first)
    """
    service = AdvisorService(db)
    return service.get_recommendations(
        field_id=field_id,
        recommendation_type=type,
        active_only=active_only,
        limit=limit,
    )


@router.post("/recommendations/{recommendation_id}/accept")
async def accept_recommendation(
    recommendation_id: UUID,
    db: Session = Depends(get_db),
):
    """Mark a recommendation as accepted"""
    from ...models.advisor import Recommendation

    rec = db.query(Recommendation).filter(Recommendation.id == recommendation_id).first()
    if not rec:
        raise HTTPException(status_code=404, detail="Recommendation not found")

    rec.is_accepted = True
    db.commit()

    return {"status": "accepted", "recommendation_id": str(recommendation_id)}


@router.post("/recommendations/{recommendation_id}/dismiss")
async def dismiss_recommendation(
    recommendation_id: UUID,
    feedback: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Dismiss a recommendation"""
    from ...models.advisor import Recommendation

    rec = db.query(Recommendation).filter(Recommendation.id == recommendation_id).first()
    if not rec:
        raise HTTPException(status_code=404, detail="Recommendation not found")

    rec.is_active = False
    rec.is_accepted = False
    rec.user_feedback = feedback
    db.commit()

    return {"status": "dismissed", "recommendation_id": str(recommendation_id)}


# ==================== Alerts Endpoints ====================

@router.get("/alerts/{field_id}", response_model=List[AlertResponse])
async def get_alerts(
    field_id: UUID,
    severity: Optional[AlertSeverity] = Query(None, description="Filter by severity"),
    status: Optional[AlertStatus] = Query(None, description="Filter by status"),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    """
    Get alerts for a field

    Returns list of alerts sorted by severity and recency
    """
    service = AdvisorService(db)
    return service.get_alerts(
        field_id=field_id,
        severity=severity,
        status=status,
        limit=limit,
    )


@router.post("/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(
    alert_id: UUID,
    user_id: UUID = Query(..., description="User acknowledging the alert"),
    db: Session = Depends(get_db),
):
    """Acknowledge an alert"""
    service = AdvisorService(db)
    success = service.acknowledge_alert(alert_id, user_id)

    if not success:
        raise HTTPException(status_code=404, detail="Alert not found")

    return {"status": "acknowledged", "alert_id": str(alert_id)}


@router.post("/alerts/{alert_id}/resolve")
async def resolve_alert(
    alert_id: UUID,
    user_id: UUID = Query(..., description="User resolving the alert"),
    notes: Optional[str] = Query(None, description="Resolution notes"),
    db: Session = Depends(get_db),
):
    """Resolve an alert"""
    service = AdvisorService(db)
    success = service.resolve_alert(alert_id, user_id, notes)

    if not success:
        raise HTTPException(status_code=404, detail="Alert not found")

    return {"status": "resolved", "alert_id": str(alert_id)}


# ==================== Playbook Endpoints ====================

@router.post("/playbook", response_model=PlaybookResponse)
async def generate_playbook(
    request: PlaybookRequest,
    db: Session = Depends(get_db),
):
    """
    Generate action playbook from recommendations

    Creates a prioritized and scheduled list of actions based on
    active recommendations for the field.

    **Request Body:**
    - `field_id`: UUID of the field
    - `recommendation_ids`: Optional list of specific recommendations to include
    - `time_horizon_days`: Planning horizon (1-90 days, default: 14)
    - `include_resources`: Include resource estimates (default: true)
    """
    service = AdvisorService(db)
    return service.generate_playbook(request)


# ==================== Action Log Endpoints ====================

@router.post("/actions/{field_id}", response_model=ActionLogResponse)
async def create_action_log(
    field_id: UUID,
    action: ActionLogCreate,
    db: Session = Depends(get_db),
):
    """
    Create an action log entry

    Records an action taken based on a recommendation
    """
    service = AdvisorService(db)
    return service.create_action_log(field_id, action)


@router.patch("/actions/{action_id}/status", response_model=ActionLogResponse)
async def update_action_status(
    action_id: UUID,
    status: ActionStatus,
    outcome: Optional[str] = Query(None),
    outcome_notes: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """
    Update action log status

    Updates the status of an action (pending, in_progress, completed, skipped)
    """
    service = AdvisorService(db)
    result = service.update_action_status(
        action_id=action_id,
        status=status,
        outcome=outcome,
        outcome_notes=outcome_notes,
    )

    if not result:
        raise HTTPException(status_code=404, detail="Action not found")

    return result


@router.get("/actions/{field_id}", response_model=List[ActionLogResponse])
async def get_action_logs(
    field_id: UUID,
    status: Optional[ActionStatus] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    """Get action logs for a field"""
    from ...models.advisor import ActionLog, ActionStatus as DBActionStatus

    query = db.query(ActionLog).filter(ActionLog.field_id == field_id)

    if status:
        query = query.filter(ActionLog.status == DBActionStatus(status.value))

    query = query.order_by(ActionLog.created_at.desc()).limit(limit)

    actions = query.all()

    return [
        ActionLogResponse(
            id=action.id,
            recommendation_id=action.recommendation_id,
            field_id=action.field_id,
            status=ActionStatus(action.status.value),
            action_type=action.action_type,
            description=action.description,
            scheduled_date=action.scheduled_date,
            started_at=action.started_at,
            completed_at=action.completed_at,
            outcome=action.outcome,
            outcome_notes=action.outcome_notes,
            created_at=action.created_at,
        )
        for action in actions
    ]


# ==================== Stats Endpoints ====================

@router.get("/stats/{field_id}")
async def get_field_stats(
    field_id: UUID,
    db: Session = Depends(get_db),
):
    """
    Get advisor statistics for a field

    Returns counts and summaries of recommendations, alerts, and actions
    """
    from ...models.advisor import (
        AdvisorSession, Recommendation, Alert, ActionLog,
        AlertSeverity as DBAlertSeverity, AlertStatus as DBAlertStatus,
        ActionStatus as DBActionStatus,
    )
    from sqlalchemy import func

    # Count recommendations
    total_recs = db.query(func.count(Recommendation.id)).filter(
        Recommendation.field_id == field_id
    ).scalar()

    active_recs = db.query(func.count(Recommendation.id)).filter(
        Recommendation.field_id == field_id,
        Recommendation.is_active == True
    ).scalar()

    # Count alerts
    total_alerts = db.query(func.count(Alert.id)).filter(
        Alert.field_id == field_id
    ).scalar()

    active_alerts = db.query(func.count(Alert.id)).filter(
        Alert.field_id == field_id,
        Alert.status == DBAlertStatus.ACTIVE
    ).scalar()

    critical_alerts = db.query(func.count(Alert.id)).filter(
        Alert.field_id == field_id,
        Alert.status == DBAlertStatus.ACTIVE,
        Alert.severity == DBAlertSeverity.CRITICAL
    ).scalar()

    # Count actions
    total_actions = db.query(func.count(ActionLog.id)).filter(
        ActionLog.field_id == field_id
    ).scalar()

    completed_actions = db.query(func.count(ActionLog.id)).filter(
        ActionLog.field_id == field_id,
        ActionLog.status == DBActionStatus.COMPLETED
    ).scalar()

    # Last session
    last_session = db.query(AdvisorSession).filter(
        AdvisorSession.field_id == field_id
    ).order_by(AdvisorSession.created_at.desc()).first()

    return {
        "field_id": str(field_id),
        "recommendations": {
            "total": total_recs,
            "active": active_recs,
        },
        "alerts": {
            "total": total_alerts,
            "active": active_alerts,
            "critical": critical_alerts,
        },
        "actions": {
            "total": total_actions,
            "completed": completed_actions,
            "completion_rate": completed_actions / total_actions if total_actions > 0 else 0,
        },
        "last_analysis": {
            "session_id": str(last_session.id) if last_session else None,
            "date": last_session.analysis_date.isoformat() if last_session else None,
            "health_score": last_session.health_score if last_session else None,
            "risk_level": last_session.risk_level if last_session else None,
        },
    }
