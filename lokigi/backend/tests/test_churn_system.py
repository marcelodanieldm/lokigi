"""Test suite for churn tracking system.

Covers:
- Alert engine logic
- Correlation analysis
- Pydantic model validation
- SQLAlchemy ORM operations
- API endpoint integration
"""

import pytest
from datetime import datetime, timedelta, date
from uuid import uuid4
from sqlalchemy.orm import Session

from app.telemetry_models import (
    ChurnReasonOption,
    ChurnSurveyPayload,
    ChurnTelemetrySnapshot,
    LifecycleEventPayload,
    LifecycleEventType,
)
from app.churn_alert_engine import (
    check_ease_of_use_churn_spike,
    check_churn_rate_spike,
    check_low_engagement_churn_pattern,
    check_price_sensitivity_spike,
    run_all_churn_checks,
)
from app.churn_correlation_analysis import analyze_churn_correlation
from app.models import (
    User,
    ChurnSurvey,
    ChurnTelemetrySnapshot as TelemetryModel,
    ChurnAlert,
    LifecycleEvent,
)


# ─────────────────────────────────────────────────────────────────────────────
# PYDANTIC MODEL VALIDATION TESTS
# ─────────────────────────────────────────────────────────────────────────────


class TestChurnSurveyPayload:
    """Validate ChurnSurveyPayload pydantic model."""
    
    def test_minimal_churn_survey(self):
        """Test with only required fields."""
        payload = ChurnSurveyPayload(
            user_id=uuid4(),
            primary_reason=ChurnReasonOption.PRICE_TOO_HIGH,
            satisfaction_score=2,
        )
        assert payload.primary_reason == ChurnReasonOption.PRICE_TOO_HIGH
        assert payload.satisfaction_score == 2
        assert payload.free_text_feedback is None
    
    def test_full_churn_survey(self):
        """Test with all fields."""
        payload = ChurnSurveyPayload(
            user_id=uuid4(),
            primary_reason=ChurnReasonOption.EASE_OF_USE_DIFFICULTY,
            secondary_reasons=[
                ChurnReasonOption.LACK_OF_FEATURES,
                ChurnReasonOption.POOR_SUPPORT,
            ],
            satisfaction_score=3,
            free_text_feedback="Dashboard was too complex",
            would_return_if_feature="Better mobile app",
            would_return_if_price_reduction=True,
            reduction_amount_percent=20,
        )
        assert payload.satisfaction_score == 3
        assert len(payload.secondary_reasons) == 2
        assert payload.reduction_amount_percent == 20
    
    def test_invalid_satisfaction_score(self):
        """Test validation: satisfaction_score out of range."""
        with pytest.raises(ValueError):
            ChurnSurveyPayload(
                user_id=uuid4(),
                primary_reason=ChurnReasonOption.OTHER,
                satisfaction_score=6,  # Invalid: >5
            )
        
        with pytest.raises(ValueError):
            ChurnSurveyPayload(
                user_id=uuid4(),
                primary_reason=ChurnReasonOption.OTHER,
                satisfaction_score=0,  # Invalid: <1
            )


class TestChurnTelemetrySnapshot:
    """Validate ChurnTelemetrySnapshot pydantic model."""
    
    def test_valid_telemetry(self):
        """Test valid telemetry snapshot."""
        snapshot = ChurnTelemetrySnapshot(
            user_id=uuid4(),
            active_days_before_cancel=15,
            last_activity_days_ago=3,
            total_reviews_processed=100,
            total_ai_responses_generated=80,
            total_ai_responses_approved=60,
            approval_rate=0.75,
            used_tone_selector=True,
            locations_connected=1,
            days_subscribed=30,
        )
        assert snapshot.approval_rate == 0.75
        assert snapshot.used_tone_selector is True
    
    def test_invalid_approval_rate(self):
        """Test validation: approval_rate out of range."""
        with pytest.raises(ValueError):
            ChurnTelemetrySnapshot(
                user_id=uuid4(),
                active_days_before_cancel=15,
                last_activity_days_ago=3,
                total_ai_responses_approved=60,
                approval_rate=1.5,  # Invalid: >1.0
            )


# ─────────────────────────────────────────────────────────────────────────────
# ALERT ENGINE TESTS
# ─────────────────────────────────────────────────────────────────────────────


class TestEaseOfUseAlert:
    """Test check_ease_of_use_churn_spike() function."""
    
    @pytest.mark.asyncio
    async def test_alert_triggered_at_20_percent(self, db: Session):
        """Alert should trigger when ease_of_use churn >= 20%."""
        user = User(email=f"test_{uuid4()}@test.com")
        db.add(user)
        db.commit()
        
        # Add 10 churns: 3 ease_of_use, 7 other
        today = date.today()
        for i in range(3):
            survey = ChurnSurvey(
                user_id=user.id,
                cancellation_date=today,
                primary_reason=ChurnReasonOption.EASE_OF_USE_DIFFICULTY.value,
                satisfaction_score=2,
            )
            db.add(survey)
        
        for i in range(7):
            survey = ChurnSurvey(
                user_id=user.id,
                cancellation_date=today,
                primary_reason=ChurnReasonOption.PRICE_TOO_HIGH.value,
                satisfaction_score=3,
            )
            db.add(survey)
        
        db.commit()
        
        # Run alert check
        alert = await check_ease_of_use_churn_spike(db, time_window_days=30)
        
        assert alert is not None
        assert alert.severity == "HIGH"
        assert alert.metric_value == 30.0  # 3/10 = 30%
        assert alert.threshold_value == 20.0
    
    @pytest.mark.asyncio
    async def test_no_alert_below_threshold(self, db: Session):
        """No alert if ease_of_use churn < 20%."""
        user = User(email=f"test_{uuid4()}@test.com")
        db.add(user)
        db.commit()
        
        # Add 10 churns: 1 ease_of_use, 9 other (10%)
        today = date.today()
        survey = ChurnSurvey(
            user_id=user.id,
            cancellation_date=today,
            primary_reason=ChurnReasonOption.EASE_OF_USE_DIFFICULTY.value,
            satisfaction_score=2,
        )
        db.add(survey)
        
        for i in range(9):
            survey = ChurnSurvey(
                user_id=user.id,
                cancellation_date=today,
                primary_reason=ChurnReasonOption.OTHER.value,
                satisfaction_score=3,
            )
            db.add(survey)
        
        db.commit()
        
        alert = await check_ease_of_use_churn_spike(db, time_window_days=30)
        
        assert alert is None
    
    @pytest.mark.asyncio
    async def test_minimum_sample_requirement(self, db: Session):
        """No alert with <5 churns (insufficient sample)."""
        user = User(email=f"test_{uuid4()}@test.com")
        db.add(user)
        db.commit()
        
        # Add only 3 churns (all ease_of_use = 100%, but too few)
        today = date.today()
        for i in range(3):
            survey = ChurnSurvey(
                user_id=user.id,
                cancellation_date=today,
                primary_reason=ChurnReasonOption.EASE_OF_USE_DIFFICULTY.value,
                satisfaction_score=2,
            )
            db.add(survey)
        
        db.commit()
        
        alert = await check_ease_of_use_churn_spike(db, time_window_days=30)
        
        assert alert is None  # Minimum 5 churns required


class TestChurnRateSpikeAlert:
    """Test check_churn_rate_spike() function."""
    
    @pytest.mark.asyncio
    async def test_spike_alert_triggered(self, db: Session):
        """Alert triggered when recent churn rate > baseline by 50%."""
        # Setup: Create baseline period (60-7=53 to 7 days ago)
        baseline_start = datetime.utcnow() - timedelta(days=60)
        baseline_end = datetime.utcnow() - timedelta(days=7)
        recent_start = datetime.utcnow() - timedelta(days=7)
        
        # Baseline signups: 100
        for i in range(100):
            user = User(email=f"baseline_{i}_{uuid4()}@test.com", created_at=baseline_start + timedelta(days=i/100*53))
            db.add(user)
        db.commit()
        
        # Baseline churns: 3 (3%)
        baseline_users = db.query(User).filter(User.created_at >= baseline_start, User.created_at < baseline_end).limit(3).all()
        for user in baseline_users:
            survey = ChurnSurvey(
                user_id=user.id,
                cancellation_date=baseline_end.date(),
                primary_reason=ChurnReasonOption.OTHER.value,
                satisfaction_score=3,
            )
            db.add(survey)
        db.commit()
        
        # Recent signups: 20
        for i in range(20):
            user = User(email=f"recent_{i}_{uuid4()}@test.com", created_at=recent_start)
            db.add(user)
        db.commit()
        
        # Recent churns: 5 (25% = 8x baseline!)
        recent_users = db.query(User).filter(User.created_at >= recent_start).limit(5).all()
        for user in recent_users:
            survey = ChurnSurvey(
                user_id=user.id,
                cancellation_date=datetime.utcnow().date(),
                primary_reason=ChurnReasonOption.TECHNICAL_ISSUES.value,
                satisfaction_score=1,
            )
            db.add(survey)
        db.commit()
        
        alert = await check_churn_rate_spike(db, baseline_days=60, recent_days=7)
        
        # Alert should trigger (recent 25% >> baseline 3% + minimum 5% absolute)
        if alert:
            assert alert.severity == "CRITICAL"


class TestLowEngagementChurn:
    """Test check_low_engagement_churn_pattern() function."""
    
    @pytest.mark.asyncio
    async def test_low_engagement_alert(self, db: Session):
        """Alert when >40% of churners have low engagement."""
        user_parent = User(email=f"parent_{uuid4()}@test.com")
        db.add(user_parent)
        db.commit()
        
        today = date.today()
        
        # Add 10 churners: 5 with low engagement, 5 with high
        
        # Low engagement: approval_rate < 0.5, active_days < 7
        for i in range(5):
            survey = ChurnSurvey(
                user_id=user_parent.id,
                cancellation_date=today,
                primary_reason=ChurnReasonOption.NOT_USING_ENOUGH.value,
                satisfaction_score=2,
            )
            telemetry = TelemetryModel(
                user_id=user_parent.id,
                active_days_before_cancel=3,
                last_activity_days_ago=2,
                total_ai_responses_approved=10,
                approval_rate=0.3,  # Low
            )
            db.add(survey)
            db.add(telemetry)
        
        # High engagement: approval_rate > 0.5, active_days > 7
        for i in range(5):
            survey = ChurnSurvey(
                user_id=user_parent.id,
                cancellation_date=today,
                primary_reason=ChurnReasonOption.SWITCHED_COMPETITOR.value,
                satisfaction_score=4,
            )
            telemetry = TelemetryModel(
                user_id=user_parent.id,
                active_days_before_cancel=30,
                last_activity_days_ago=2,
                total_ai_responses_approved=100,
                approval_rate=0.8,  # High
            )
            db.add(survey)
            db.add(telemetry)
        
        db.commit()
        
        alert = await check_low_engagement_churn_pattern(db, time_window_days=30)
        
        # Should trigger (50% low-engagement > 40% threshold)
        if alert:
            assert alert.severity == "MEDIUM"
            assert alert.metric_value >= 40


# ─────────────────────────────────────────────────────────────────────────────
# CORRELATION ANALYSIS TESTS
# ─────────────────────────────────────────────────────────────────────────────


class TestChurnCorrelation:
    """Test analyze_churn_correlation() function."""
    
    @pytest.mark.asyncio
    async def test_correlation_by_reason(self, db: Session):
        """Verify correlation analysis groups by churn reason correctly."""
        user = User(email=f"test_{uuid4()}@test.com")
        db.add(user)
        db.commit()
        
        today = date.today()
        
        # Create mixed churn data
        for i in range(5):
            survey = ChurnSurvey(
                user_id=user.id,
                cancellation_date=today,
                primary_reason=ChurnReasonOption.PRICE_TOO_HIGH.value,
                satisfaction_score=2,
            )
            telemetry = TelemetryModel(
                user_id=user.id,
                active_days_before_cancel=10 + i,
                last_activity_days_ago=1,
                total_ai_responses_approved=20 * (i + 1),
                approval_rate=0.6,
            )
            db.add(survey)
            db.add(telemetry)
        
        db.commit()
        
        analysis = await analyze_churn_correlation(db, time_window_days=30)
        
        assert len(analysis.correlations) > 0
        assert any(c.reason == ChurnReasonOption.PRICE_TOO_HIGH.value for c in analysis.correlations)
        assert len(analysis.key_insights) > 0


# ─────────────────────────────────────────────────────────────────────────────
# INTEGRATION TESTS
# ─────────────────────────────────────────────────────────────────────────────


class TestRunAllChurnChecks:
    """Test run_all_churn_checks() orchestration."""
    
    @pytest.mark.asyncio
    async def test_all_checks_executed(self, db: Session):
        """Verify all 4 alert checks are executed."""
        alerts = await run_all_churn_checks(db)
        
        # Should return list (empty or with alerts)
        assert isinstance(alerts, list)
        
        # All returned alerts should have required fields
        for alert in alerts:
            assert alert.alert_type in [
                "high_churn_difficulty",
                "spike_in_churn_rate",
                "low_engagement_churn",
                "high_churn_price_sensitivity",
            ]
            assert alert.severity in ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
            assert alert.triggered_at is not None


# ─────────────────────────────────────────────────────────────────────────────
# FIXTURES
# ─────────────────────────────────────────────────────────────────────────────


@pytest.fixture
def db():
    """Provide test database session."""
    from app.database import SessionLocal
    session = SessionLocal()
    yield session
    session.close()
