"""app/subscription_manager.py — Billing-cycle lifecycle manager.

Responsibilities
────────────────
1. Daily expiry check: find subscriptions whose current_period_end has passed
   and transition them to 'expired', deactivating the org and its active
   Celery-processed locations.
2. Worker guard: `is_subscription_active()` — called by Celery tasks before
   processing to skip work for expired accounts.
3. Celery periodic-task entry point: `run_daily_expiry_check(db)`.

Design notes
────────────
• "Deactivating locations" is implemented by setting a flag on the
  Organization record (status='expired'), NOT by deleting or modifying the
  GoogleConnection rows directly. Workers check org status via
  `is_subscription_active()` before processing.
• Enterprise plans are excluded from automatic expiry (they may have custom
  billing terms managed outside Stripe).
• A grace period (EXPIRY_GRACE_DAYS) prevents accidental expiry due to
  clock skew or Stripe webhook delay.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import Organization, OrgMember, SubscriptionProfile, User

logger = logging.getLogger(__name__)

# Number of extra days to wait after current_period_end before marking expired.
EXPIRY_GRACE_DAYS: int = 3


class SubscriptionManager:
    # ── Public API ────────────────────────────────────────────────────────────

    @staticmethod
    def is_subscription_active(db: Session, user_id: UUID) -> bool:
        """Return True if the user's subscription is in a billable state.

        Called by Celery workers before processing jobs for a user.
        Returns True for enterprise plans unconditionally.
        """
        profile = db.scalar(
            select(SubscriptionProfile).where(SubscriptionProfile.user_id == user_id)
        )
        if profile is None:
            # No profile → treat as basic active (upserted on first use)
            return True
        if profile.subscription_plan == "enterprise":
            return True
        return profile.subscription_status in ("active", "trialing", "past_due")

    @staticmethod
    def check_expired_subscriptions(db: Session) -> list[dict[str, Any]]:
        """Identify and expire subscriptions past their grace period.

        Returns a list of dicts describing each expired account so callers
        (Celery task, admin endpoint) can log/report the actions taken.
        """
        cutoff = datetime.now(timezone.utc) - timedelta(days=EXPIRY_GRACE_DAYS)

        # Find profiles that have expired and are not already marked as such
        profiles = db.scalars(
            select(SubscriptionProfile).where(
                SubscriptionProfile.current_period_end < cutoff,
                SubscriptionProfile.subscription_status.not_in(
                    ["expired", "canceled", "active"]
                ),
                SubscriptionProfile.subscription_plan != "enterprise",
            )
        ).all()

        expired_records: list[dict[str, Any]] = []
        for profile in profiles:
            try:
                result = SubscriptionManager._expire_profile(db, profile)
                expired_records.append(result)
            except Exception as exc:
                logger.error(
                    "Failed to expire subscription for user_id=%s: %s",
                    profile.user_id,
                    exc,
                )

        if expired_records:
            db.commit()
            logger.info(
                "Daily expiry check: expired %d subscription(s)", len(expired_records)
            )
        return expired_records

    @staticmethod
    def expire_organization(db: Session, org_id: UUID) -> dict[str, Any]:
        """Manually expire an organization (e.g., from admin action or Stripe webhook).

        Sets org.status = 'expired' and marks the owner's subscription_status
        accordingly. Commits the changes.
        """
        org = db.get(Organization, org_id)
        if org is None:
            raise ValueError(f"Organization {org_id} not found")

        org.status = "expired"
        org.updated_at = datetime.utcnow()

        profile = db.scalar(
            select(SubscriptionProfile).where(
                SubscriptionProfile.user_id == org.owner_user_id
            )
        )
        if profile:
            profile.subscription_status = "expired"
            profile.updated_at = datetime.utcnow()

        db.commit()
        logger.info("Organization %s manually expired.", org_id)
        return {"org_id": str(org_id), "action": "expired"}

    @staticmethod
    def reactivate_subscription(db: Session, user_id: UUID) -> None:
        """Reset a previously expired subscription back to 'active'.

        Called after a successful Stripe payment or manual admin override.
        Also re-activates the user's Organization if it was suspended.
        """
        profile = db.scalar(
            select(SubscriptionProfile).where(SubscriptionProfile.user_id == user_id)
        )
        if profile:
            profile.subscription_status = "active"
            profile.updated_at = datetime.utcnow()

        # Re-activate all orgs owned by this user
        orgs = db.scalars(
            select(Organization).where(
                Organization.owner_user_id == user_id,
                Organization.status == "expired",
            )
        ).all()
        for org in orgs:
            org.status = "active"
            org.updated_at = datetime.utcnow()

        db.commit()
        logger.info("Subscription reactivated for user_id=%s", user_id)

    # ── Internal helpers ──────────────────────────────────────────────────────

    @staticmethod
    def _expire_profile(
        db: Session, profile: SubscriptionProfile
    ) -> dict[str, Any]:
        """Mark a single profile as expired and deactivate its org(s)."""
        profile.subscription_status = "expired"
        profile.updated_at = datetime.utcnow()

        # Deactivate any organizations this user owns
        orgs = db.scalars(
            select(Organization).where(
                Organization.owner_user_id == profile.user_id,
                Organization.status == "active",
            )
        ).all()
        deactivated_orgs = []
        for org in orgs:
            org.status = "expired"
            org.updated_at = datetime.utcnow()
            deactivated_orgs.append(str(org.id))

        logger.warning(
            "Subscription expired for user_id=%s (plan=%s, period_end=%s). "
            "Deactivated orgs: %s",
            profile.user_id,
            profile.subscription_plan,
            profile.current_period_end,
            deactivated_orgs or "none",
        )
        return {
            "user_id": str(profile.user_id),
            "plan": profile.subscription_plan,
            "period_end": (
                profile.current_period_end.isoformat()
                if profile.current_period_end
                else None
            ),
            "deactivated_orgs": deactivated_orgs,
        }


# ── Celery task entry point ───────────────────────────────────────────────────

def run_daily_expiry_check(db: Session) -> dict[str, Any]:
    """Called by a Celery beat task (e.g. every day at 02:00 UTC).

    Wire up in celery_app.py:
        @celery.on_after_configure.connect
        def setup_periodic_tasks(sender, **kwargs):
            sender.add_periodic_task(
                crontab(hour=2, minute=0),
                daily_expiry_task.s(),
                name="daily-subscription-expiry",
            )
    """
    results = SubscriptionManager.check_expired_subscriptions(db)
    return {
        "expired_count": len(results),
        "expired": results,
        "run_at": datetime.utcnow().isoformat(),
    }
