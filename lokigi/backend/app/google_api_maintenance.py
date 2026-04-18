"""Google API permission maintenance helpers for cancellation grace period.

This lightweight service keeps the cancellation flow operational without
hard dependencies on extra token-revocation tables/fields.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy.orm import Session

from app.models import GoogleConnection


class GoogleAPIMaintenanceService:
    """Read-only grace period status service.

    Returns conservative status values based on current model fields.
    If advanced revocation fields are not present in the model, it falls back
    to "active" for existing connections.
    """

    @staticmethod
    def get_grace_period_status(user_id: UUID, db: Session) -> dict:
        connection = db.query(GoogleConnection).filter_by(user_id=user_id).first()
        if not connection:
            return {"status": "no_connection"}

        # The current GoogleConnection model has no token_expiry/is_revoked fields.
        # Keep behavior predictable until advanced lifecycle fields are added.
        return {
            "status": "active",
            "grace_period": False,
            "message": "Google API permissions are active for this connection.",
            "checked_at": datetime.utcnow().isoformat(),
        }
