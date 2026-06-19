"""
Main Advisor Service
Coordinates context aggregation, rules engine, and recommendation storage
"""
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from uuid import UUID
from sqlalchemy.orm import Session

from ..core.logging import logger
from ..models.advisor import (
    AdvisorSession,
    Recommendation,
    Alert,
    ActionLog,
    RecommendationType as DBRecommendationType,
    AlertSeverity as DBAlertSeverity,
    AlertStatus as DBAlertStatus,
    ActionStatus as DBActionStatus,
)
from ..schemas.advisor import (
    AnalyzeFieldRequest,
    AnalyzeFieldResponse,
    RecommendationResponse,
    AlertResponse,
    PlaybookRequest,
    PlaybookResponse,
    PlaybookAction,
    ActionLogCreate,
    ActionLogResponse,
    FieldContext,
    RecommendationType,
    AlertSeverity,
    AlertStatus,
    ActionStatus,
)
from .context_aggregator import ContextAggregator
from ..engines.rules_engine import RulesEngine


class AdvisorService:
    """
    Main service for field analysis and recommendations
    """

    def __init__(self, db: Session):
        self.db = db
        self.context_aggregator = ContextAggregator()
        self.rules_engine = RulesEngine()

    async def analyze_field(
        self,
        request: AnalyzeFieldRequest,
    ) -> AnalyzeFieldResponse:
        """
        Analyze a field and generate recommendations

        Args:
            request: Analysis request with field_id and options

        Returns:
            AnalyzeFieldResponse with recommendations and alerts
        """
        logger.info(f"Starting field analysis for {request.field_id}")

        # Build context
        context = await self._build_context(request)

        # Run rules engine
        recommendations, alerts, health_score, risk_level = self.rules_engine.analyze(
            context=context,
            language=request.language,
        )

        # Generate summary
        summary_en, summary_ar = self.rules_engine.generate_summary(
            context=context,
            health_score=health_score,
            risk_level=risk_level,
            recommendations=recommendations,
            alerts=alerts,
            language=request.language,
        )

        # Create session in database
        session = self._create_session(
            field_id=request.field_id,
            tenant_id=request.tenant_id,
            context=context,
            health_score=health_score,
            risk_level=risk_level.value,
        )

        # Store recommendations
        self._store_recommendations(session.id, request.field_id, recommendations)

        # Store alerts
        self._store_alerts(session.id, request.field_id, request.tenant_id, alerts)

        # Build response
        ndvi_trend = context.ndvi.trend if context.ndvi else None

        return AnalyzeFieldResponse(
            session_id=session.id,
            field_id=request.field_id,
            analysis_date=datetime.utcnow(),
            health_score=health_score,
            risk_level=risk_level,
            ndvi_trend=ndvi_trend,
            summary=summary_en,
            summary_ar=summary_ar,
            context=context,
            recommendations=recommendations,
            alerts=alerts,
            recommendation_count=len(recommendations),
            alert_count=len(alerts),
            critical_alerts=sum(1 for a in alerts if a.severity == AlertSeverity.CRITICAL),
        )

    async def _build_context(self, request: AnalyzeFieldRequest) -> FieldContext:
        """Build field context from various sources or request overrides"""

        # Use provided data or fetch from services
        if request.ndvi_data or request.weather_data or request.crop_data or request.soil_data:
            # Use provided overrides
            context = FieldContext(
                field_id=request.field_id,
                ndvi=request.ndvi_data,
                weather=request.weather_data,
                crop=request.crop_data,
                soil=request.soil_data,
            )
        else:
            # Fetch from context aggregator
            # TODO: Get location from field database
            location = {"lat": 24.7136, "lng": 46.6753}  # Default: Riyadh

            context = await self.context_aggregator.aggregate_context(
                field_id=request.field_id,
                include_weather=request.include_weather,
                include_forecast=request.include_forecast,
                location=location,
            )

        return context

    def _create_session(
        self,
        field_id: UUID,
        tenant_id: Optional[UUID],
        context: FieldContext,
        health_score: float,
        risk_level: str,
    ) -> AdvisorSession:
        """Create advisor session in database"""
        session = AdvisorSession(
            field_id=field_id,
            tenant_id=tenant_id,
            context_data=context.model_dump() if context else None,
            ndvi_mean=context.ndvi.mean if context.ndvi else None,
            ndvi_min=context.ndvi.min if context.ndvi else None,
            ndvi_max=context.ndvi.max if context.ndvi else None,
            ndvi_trend=context.ndvi.trend.value if context.ndvi and context.ndvi.trend else None,
            weather_summary=context.weather.model_dump() if context.weather else None,
            health_score=health_score,
            risk_level=risk_level,
        )

        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)

        return session

    def _store_recommendations(
        self,
        session_id: UUID,
        field_id: UUID,
        recommendations: List[RecommendationResponse],
    ) -> None:
        """Store recommendations in database"""
        for rec in recommendations:
            db_rec = Recommendation(
                id=rec.id,
                session_id=session_id,
                field_id=field_id,
                type=DBRecommendationType(rec.type.value),
                title=rec.title,
                title_ar=rec.title_ar,
                description=rec.description,
                description_ar=rec.description_ar,
                priority=rec.priority,
                urgency=rec.urgency,
                recommended_date=rec.recommended_date,
                deadline=rec.deadline,
                parameters=rec.parameters,
                affected_zones=rec.affected_zones,
                confidence_score=rec.confidence_score,
                rule_source=rec.rule_source,
            )
            self.db.add(db_rec)

        self.db.commit()

    def _store_alerts(
        self,
        session_id: UUID,
        field_id: UUID,
        tenant_id: Optional[UUID],
        alerts: List[AlertResponse],
    ) -> None:
        """Store alerts in database"""
        for alert in alerts:
            db_alert = Alert(
                id=alert.id,
                session_id=session_id,
                field_id=field_id,
                tenant_id=tenant_id,
                severity=DBAlertSeverity(alert.severity.value),
                status=DBAlertStatus(alert.status.value),
                title=alert.title,
                title_ar=alert.title_ar,
                message=alert.message,
                message_ar=alert.message_ar,
                alert_type=alert.alert_type,
                threshold_value=alert.threshold_value,
                actual_value=alert.actual_value,
                affected_zones=alert.affected_zones,
            )
            self.db.add(db_alert)

        self.db.commit()

    def get_recommendations(
        self,
        field_id: UUID,
        recommendation_type: Optional[RecommendationType] = None,
        active_only: bool = True,
        limit: int = 20,
    ) -> List[RecommendationResponse]:
        """Get recommendations for a field"""
        query = self.db.query(Recommendation).filter(
            Recommendation.field_id == field_id
        )

        if active_only:
            query = query.filter(Recommendation.is_active == True)

        if recommendation_type:
            query = query.filter(
                Recommendation.type == DBRecommendationType(recommendation_type.value)
            )

        query = query.order_by(
            Recommendation.priority.desc(),
            Recommendation.created_at.desc(),
        ).limit(limit)

        recommendations = query.all()

        return [
            RecommendationResponse(
                id=rec.id,
                type=RecommendationType(rec.type.value),
                title=rec.title,
                title_ar=rec.title_ar,
                description=rec.description,
                description_ar=rec.description_ar,
                priority=rec.priority,
                urgency=rec.urgency,
                recommended_date=rec.recommended_date,
                deadline=rec.deadline,
                parameters=rec.parameters,
                affected_zones=rec.affected_zones,
                confidence_score=rec.confidence_score,
                rule_source=rec.rule_source,
                created_at=rec.created_at,
            )
            for rec in recommendations
        ]

    def get_alerts(
        self,
        field_id: UUID,
        severity: Optional[AlertSeverity] = None,
        status: Optional[AlertStatus] = None,
        limit: int = 50,
    ) -> List[AlertResponse]:
        """Get alerts for a field"""
        query = self.db.query(Alert).filter(Alert.field_id == field_id)

        if severity:
            query = query.filter(Alert.severity == DBAlertSeverity(severity.value))

        if status:
            query = query.filter(Alert.status == DBAlertStatus(status.value))
        else:
            # Default: active alerts only
            query = query.filter(Alert.status == DBAlertStatus.ACTIVE)

        query = query.order_by(
            Alert.severity.desc(),
            Alert.created_at.desc(),
        ).limit(limit)

        alerts = query.all()

        return [
            AlertResponse(
                id=alert.id,
                severity=AlertSeverity(alert.severity.value),
                status=AlertStatus(alert.status.value),
                title=alert.title,
                title_ar=alert.title_ar,
                message=alert.message,
                message_ar=alert.message_ar,
                alert_type=alert.alert_type,
                threshold_value=alert.threshold_value,
                actual_value=alert.actual_value,
                affected_zones=alert.affected_zones,
                created_at=alert.created_at,
            )
            for alert in alerts
        ]

    def generate_playbook(
        self,
        request: PlaybookRequest,
    ) -> PlaybookResponse:
        """Generate action playbook from recommendations"""
        # Get active recommendations
        recommendations = self.get_recommendations(
            field_id=request.field_id,
            active_only=True,
            limit=50,
        )

        # Filter by IDs if provided
        if request.recommendation_ids:
            recommendations = [
                r for r in recommendations
                if r.id in request.recommendation_ids
            ]

        # Sort by priority and deadline
        recommendations.sort(
            key=lambda x: (x.priority, x.deadline or datetime.max),
            reverse=True,
        )

        # Generate actions
        actions: List[PlaybookAction] = []
        current_date = datetime.utcnow()
        total_hours = 0.0
        resources: Dict[str, Any] = {}

        for i, rec in enumerate(recommendations[:20]):  # Max 20 actions
            # Estimate duration based on type
            duration = self._estimate_duration(rec.type)
            total_hours += duration

            # Aggregate resources
            if rec.parameters:
                for key, value in rec.parameters.items():
                    if key not in resources:
                        resources[key] = []
                    resources[key].append(value)

            # Schedule action
            scheduled = rec.recommended_date or (current_date + timedelta(days=i))

            actions.append(PlaybookAction(
                order=i + 1,
                recommendation_id=rec.id,
                action_type=rec.type.value,
                title=rec.title,
                title_ar=rec.title_ar,
                description=rec.description,
                description_ar=rec.description_ar,
                scheduled_date=scheduled,
                duration_hours=duration,
                resources=rec.parameters,
            ))

        # Generate calendar view
        calendar = self._generate_calendar_view(actions, request.time_horizon_days)

        return PlaybookResponse(
            field_id=request.field_id,
            generated_at=datetime.utcnow(),
            time_horizon_days=request.time_horizon_days,
            actions=actions,
            total_estimated_hours=total_hours,
            resource_summary=resources if request.include_resources else None,
            calendar_view=calendar,
        )

    def _estimate_duration(self, rec_type: RecommendationType) -> float:
        """Estimate action duration in hours"""
        durations = {
            RecommendationType.IRRIGATION: 2.0,
            RecommendationType.FERTILIZATION: 3.0,
            RecommendationType.PEST_CONTROL: 4.0,
            RecommendationType.DISEASE_TREATMENT: 4.0,
            RecommendationType.HARVEST: 8.0,
            RecommendationType.SOIL_MANAGEMENT: 6.0,
            RecommendationType.GENERAL: 1.0,
        }
        return durations.get(rec_type, 2.0)

    def _generate_calendar_view(
        self,
        actions: List[PlaybookAction],
        days: int,
    ) -> List[Dict[str, Any]]:
        """Generate calendar view of actions"""
        calendar = []
        current = datetime.utcnow().date()

        for day_offset in range(days):
            date = current + timedelta(days=day_offset)
            day_actions = [
                a for a in actions
                if a.scheduled_date and a.scheduled_date.date() == date
            ]

            if day_actions:
                calendar.append({
                    "date": date.isoformat(),
                    "action_count": len(day_actions),
                    "actions": [
                        {"order": a.order, "title": a.title, "type": a.action_type}
                        for a in day_actions
                    ],
                })

        return calendar

    def create_action_log(
        self,
        field_id: UUID,
        action: ActionLogCreate,
    ) -> ActionLogResponse:
        """Create action log entry"""
        db_action = ActionLog(
            recommendation_id=action.recommendation_id,
            field_id=field_id,
            action_type=action.action_type,
            description=action.description,
            scheduled_date=action.scheduled_date,
            performer_notes=action.performer_notes,
        )

        self.db.add(db_action)
        self.db.commit()
        self.db.refresh(db_action)

        return ActionLogResponse(
            id=db_action.id,
            recommendation_id=db_action.recommendation_id,
            field_id=db_action.field_id,
            status=ActionStatus(db_action.status.value),
            action_type=db_action.action_type,
            description=db_action.description,
            scheduled_date=db_action.scheduled_date,
            started_at=db_action.started_at,
            completed_at=db_action.completed_at,
            outcome=db_action.outcome,
            outcome_notes=db_action.outcome_notes,
            created_at=db_action.created_at,
        )

    def update_action_status(
        self,
        action_id: UUID,
        status: ActionStatus,
        outcome: Optional[str] = None,
        outcome_notes: Optional[str] = None,
    ) -> Optional[ActionLogResponse]:
        """Update action log status"""
        action = self.db.query(ActionLog).filter(ActionLog.id == action_id).first()

        if not action:
            return None

        action.status = DBActionStatus(status.value)

        if status == ActionStatus.IN_PROGRESS:
            action.started_at = datetime.utcnow()
        elif status == ActionStatus.COMPLETED:
            action.completed_at = datetime.utcnow()
            action.outcome = outcome
            action.outcome_notes = outcome_notes

        self.db.commit()
        self.db.refresh(action)

        return ActionLogResponse(
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

    def acknowledge_alert(
        self,
        alert_id: UUID,
        user_id: UUID,
    ) -> bool:
        """Acknowledge an alert"""
        alert = self.db.query(Alert).filter(Alert.id == alert_id).first()

        if not alert:
            return False

        alert.status = DBAlertStatus.ACKNOWLEDGED
        alert.acknowledged_at = datetime.utcnow()
        alert.acknowledged_by = user_id

        self.db.commit()
        return True

    def resolve_alert(
        self,
        alert_id: UUID,
        user_id: UUID,
        notes: Optional[str] = None,
    ) -> bool:
        """Resolve an alert"""
        alert = self.db.query(Alert).filter(Alert.id == alert_id).first()

        if not alert:
            return False

        alert.status = DBAlertStatus.RESOLVED
        alert.resolved_at = datetime.utcnow()
        alert.resolved_by = user_id
        alert.resolution_notes = notes

        self.db.commit()
        return True
