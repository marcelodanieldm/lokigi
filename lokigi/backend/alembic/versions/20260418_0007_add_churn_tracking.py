"""Add lifecycle and churn tracking tables

Revision ID: 20260418_0007
Revises: 20260418_0006
Create Date: 2025-04-18 08:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ENUM as PgEnum


# revision identifiers, used by Alembic.
revision = '20260418_0007'
down_revision = '20260418_0006'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create enum types via raw SQL to avoid duplicate-type issues
    op.execute(sa.text(
        "CREATE TYPE lifecycle_event_type AS ENUM ("
        "'signup', 'first_connection', 'first_reply_generated', 'first_reply_approved',"
        "'onboarding_complete', 'payment_method_added', 'subscription_activated',"
        "'subscription_downgrade', 'subscription_paused', 'churn_initiated')"
    ))
    op.execute(sa.text(
        "CREATE TYPE churn_reason AS ENUM ("
        "'price_too_high', 'lack_of_features', 'ease_of_use_difficulty',"
        "'switched_competitor', 'not_using_enough', 'poor_support',"
        "'technical_issues', 'personal_reasons', 'other')"
    ))

    # 1. lifecycle_events - Track user journey milestones
    op.create_table(
        'lifecycle_events',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('event_type', PgEnum(name='lifecycle_event_type', create_type=False), nullable=False),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.Index('ix_lifecycle_user_type', 'user_id', 'event_type'),
        sa.Index('ix_lifecycle_created_at', 'created_at'),
    )

    # 2. churn_surveys - Qualitative churn feedback
    op.create_table(
        'churn_surveys',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('cancellation_date', sa.Date(), nullable=False),
        sa.Column('primary_reason', PgEnum(name='churn_reason', create_type=False), nullable=False),
        sa.Column('secondary_reasons', sa.JSON(), nullable=True),
        sa.Column('satisfaction_score', sa.Integer(), nullable=False),
        sa.Column('free_text_feedback', sa.String(1000), nullable=True),
        sa.Column('would_return_if_feature', sa.String(255), nullable=True),
        sa.Column('would_return_if_price_reduction', sa.Boolean(), default=False),
        sa.Column('reduction_amount_percent', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.Index('ix_churn_survey_reason', 'primary_reason'),
        sa.Index('ix_churn_survey_date', 'cancellation_date'),
        sa.Index('ix_churn_survey_score', 'satisfaction_score'),
    )

    # 3. churn_telemetry_snapshot - Engagement metrics at churn time
    op.create_table(
        'churn_telemetry_snapshot',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('active_days_before_cancel', sa.Integer(), nullable=False),
        sa.Column('last_activity_days_ago', sa.Integer(), nullable=False),
        sa.Column('total_reviews_processed', sa.Integer(), default=0),
        sa.Column('total_ai_responses_generated', sa.Integer(), default=0),
        sa.Column('total_ai_responses_approved', sa.Integer(), default=0),
        sa.Column('approval_rate', sa.Float(), nullable=False),
        sa.Column('used_tone_selector', sa.Boolean(), default=False),
        sa.Column('used_sentiment_reports', sa.Boolean(), default=False),
        sa.Column('used_manual_approval', sa.Boolean(), default=False),
        sa.Column('locations_connected', sa.Integer(), default=0),
        sa.Column('days_subscribed', sa.Integer(), default=0),
        sa.Column('subscription_plan', sa.String(50), default='starter'),
        sa.Column('captured_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', name='uq_telemetry_one_per_user'),
        sa.Index('ix_telemetry_approval_rate', 'approval_rate'),
        sa.Index('ix_telemetry_active_days', 'active_days_before_cancel'),
    )

    # 4. churn_alerts - Alert tracking and notifications
    op.create_table(
        'churn_alerts',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('alert_type', sa.String(100), nullable=False),
        sa.Column('severity', sa.String(20), nullable=False),
        sa.Column('triggered_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('acknowledged_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('acknowledged_by_user_id', sa.UUID(), nullable=True),
        sa.Column('time_window_days', sa.Integer(), nullable=False),
        sa.Column('metric_name', sa.String(100), nullable=True),
        sa.Column('metric_value', sa.Float(), nullable=True),
        sa.Column('threshold_value', sa.Float(), nullable=True),
        sa.Column('alert_message', sa.Text(), nullable=False),
        sa.Column('details', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['acknowledged_by_user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.Index('ix_alert_severity', 'severity'),
        sa.Index('ix_alert_triggered_at', 'triggered_at'),
        sa.Index('ix_alert_type', 'alert_type'),
        sa.Index('ix_alert_acknowledged', 'acknowledged_at'),
    )


def downgrade() -> None:
    op.drop_table('churn_alerts')
    op.drop_table('churn_telemetry_snapshot')
    op.drop_table('churn_surveys')
    op.drop_table('lifecycle_events')
    op.execute(sa.text('DROP TYPE IF EXISTS churn_reason'))
    op.execute(sa.text('DROP TYPE IF EXISTS lifecycle_event_type'))
