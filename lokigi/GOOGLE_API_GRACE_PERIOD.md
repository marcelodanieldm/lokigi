# Google API Permissions Maintenance on Cancellation

## Objetivo

Asegurar que los permisos de Google API permanezcan **activos hasta el final del ciclo de facturación** después de la cancelación de la suscripción. Esto permite:

1. ✅ Continuidad de acceso a datos de Google Business Profile
2. ✅ Evitar sorpresas para el usuario durante el período de gracia
3. ✅ Permitir reactivación sin autenticación Google nuevamente
4. ✅ Cumplimiento con Google's API terms (no revocar inmediatamente)

---

## Arquitectura de Solución

### 1. Database Schema (Alembic 0007 - Ya existe)

```sql
-- En GoogleConnection model:
- token_expiry: TIMESTAMP  -- Cuándo se revoca el token
- is_revoked: BOOLEAN      -- Si fue revocado manualmente
- cancellation_metadata: JSON  -- {cancelled_date, access_until, reason}
```

### 2. Flujo de Cancelación

```
┌─────────────────────────────────────────────────────────────┐
│ User clicks "Confirmar Cancelación" in Modal                 │
└────────────┬────────────────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────────────┐
│ POST /api/cancellation/confirm                              │
│ - Save ChurnSurvey                                          │
│ - Capture TelemetrySnapshot                                 │
│ - Set GoogleConnection.token_expiry = NOW + 30 days        │
│ - Add cancellation_metadata                                 │
│ - Run alert checks                                          │
└────────────┬────────────────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────────────┐
│ DON'T revoke Google token immediately ⚠️                    │
│ - Token remains valid for 30 days                           │
│ - Scheduled job removes access after expiry                │
│ - User can re-activate within grace period                  │
└─────────────────────────────────────────────────────────────┘
```

### 3. Implementation Checklist

- [ ] **Backend**: Update `GoogleConnection` model with `token_expiry` and `cancellation_metadata`
- [ ] **Backend**: Modify `confirm_cancellation()` to NOT revoke tokens immediately
- [ ] **Backend**: Create `google_api_maintenance.py` for scheduled cleanup
- [ ] **Backend**: Create scheduled job for automatic token cleanup
- [ ] **Frontend**: Show "Access active until: [DATE]" message
- [ ] **Testing**: Verify token remains valid during grace period
- [ ] **Documentation**: Document the grace period policy

---

## Implementation Details

### Step 1: Update GoogleConnection Model

**File**: `backend/app/models.py`

```python
class GoogleConnection(Base):
    __tablename__ = "google_connections"
    
    # Existing fields...
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    
    # ADD THESE FIELDS:
    token_expiry: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
        comment="When Google API token should be revoked (set on cancellation)"
    )
    is_revoked: Mapped[bool] = mapped_column(
        default=False,
        comment="Manual revocation flag"
    )
    cancellation_metadata: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
        comment="Metadata about cancellation: {cancelled_date, access_until, reason}"
    )
    
    # Relationships
    user: Mapped["User"] = relationship(
        back_populates="google_connections",
        cascade="all, delete-orphan",
    )
```

### Step 2: Alembic Migration

**File**: `backend/alembic/versions/20260418_0008_add_google_api_grace_period.py` (NEW)

```python
"""Add Google API grace period tracking.

Revision ID: 0008
Revises: 0007
Create Date: 2024-06-18 10:00:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '0008'
down_revision = '0007'
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.add_column(
        'google_connections',
        sa.Column(
            'token_expiry',
            sa.DateTime(),
            nullable=True,
            comment='When Google API token should be revoked'
        )
    )
    op.add_column(
        'google_connections',
        sa.Column(
            'is_revoked',
            sa.Boolean(),
            nullable=False,
            server_default='false',
            comment='Manual revocation flag'
        )
    )
    op.add_column(
        'google_connections',
        sa.Column(
            'cancellation_metadata',
            postgresql.JSON(),
            nullable=True,
            comment='Metadata: {cancelled_date, access_until, reason}'
        )
    )
    op.create_index(
        'ix_google_connections_token_expiry',
        'google_connections',
        ['token_expiry'],
        unique=False
    )

def downgrade() -> None:
    op.drop_index('ix_google_connections_token_expiry')
    op.drop_column('google_connections', 'cancellation_metadata')
    op.drop_column('google_connections', 'is_revoked')
    op.drop_column('google_connections', 'token_expiry')
```

### Step 3: Google API Maintenance Service

**File**: `backend/app/google_api_maintenance.py` (NEW)

```python
"""
Google API Permission Maintenance
Handles graceful token expiration and cleanup after cancellation.
"""

from sqlalchemy.orm import Session
from sqlalchemy import select
from datetime import datetime, timedelta
from uuid import UUID
import logging

from app.models import GoogleConnection, User
from app.database import SessionLocal

logger = logging.getLogger(__name__)

GRACE_PERIOD_DAYS = 30  # Allow 30 days of read-only access after cancellation


class GoogleAPIMaintenanceService:
    """Manages Google API token lifecycle during cancellation."""
    
    @staticmethod
    def set_token_expiry_on_cancellation(
        db: Session,
        user_id: UUID,
        grace_period_days: int = GRACE_PERIOD_DAYS,
    ) -> dict:
        """
        Set token expiry date when user cancels subscription.
        
        Token will remain valid for grace_period_days, then auto-cleanup.
        """
        connection = db.query(GoogleConnection).filter_by(user_id=user_id).first()
        
        if not connection:
            raise ValueError(f"Google connection not found for user {user_id}")
        
        # Set expiry to end of billing cycle (30 days)
        expiry_date = datetime.utcnow() + timedelta(days=grace_period_days)
        
        connection.token_expiry = expiry_date
        connection.cancellation_metadata = {
            "cancelled_at": datetime.utcnow().isoformat(),
            "access_until": expiry_date.isoformat(),
            "grace_period_days": grace_period_days,
            "status": "grace_period_active"
        }
        
        db.commit()
        
        logger.info(
            f"Token expiry set for user {user_id}: {expiry_date}",
            extra={
                "user_id": str(user_id),
                "expiry_date": expiry_date.isoformat(),
            }
        )
        
        return {
            "user_id": str(user_id),
            "token_expiry": expiry_date.isoformat(),
            "grace_period_days": grace_period_days,
            "status": "grace_period_active",
        }
    
    @staticmethod
    async def cleanup_expired_tokens(
        db: Session,
        dry_run: bool = False,
    ) -> dict:
        """
        Cleanup expired Google API tokens (scheduled job).
        
        Run daily via APScheduler.
        
        Actions:
        1. Find all connections with token_expiry < NOW
        2. Revoke tokens via Google API
        3. Mark as revoked in database
        4. Log for audit trail
        """
        now = datetime.utcnow()
        
        # Find all expired tokens
        expired_connections = db.query(GoogleConnection).filter(
            GoogleConnection.token_expiry < now,
            GoogleConnection.is_revoked == False,
        ).all()
        
        revoked_count = 0
        failed_count = 0
        
        for connection in expired_connections:
            try:
                # In production: Revoke token via Google API
                # await revoke_google_token(connection.refresh_token)
                
                connection.is_revoked = True
                connection.cancellation_metadata = connection.cancellation_metadata or {}
                connection.cancellation_metadata["revoked_at"] = now.isoformat()
                connection.cancellation_metadata["status"] = "revoked"
                
                if not dry_run:
                    db.commit()
                
                revoked_count += 1
                
                logger.info(
                    f"Revoked expired token for user {connection.user_id}",
                    extra={"user_id": str(connection.user_id)}
                )
            
            except Exception as e:
                failed_count += 1
                logger.error(
                    f"Failed to revoke token for user {connection.user_id}: {str(e)}",
                    extra={"user_id": str(connection.user_id), "error": str(e)}
                )
        
        return {
            "revoked": revoked_count,
            "failed": failed_count,
            "total_expired": len(expired_connections),
            "dry_run": dry_run,
        }
    
    @staticmethod
    def get_grace_period_status(
        user_id: UUID,
        db: Session,
    ) -> dict:
        """Get current grace period status for a user."""
        connection = db.query(GoogleConnection).filter_by(user_id=user_id).first()
        
        if not connection:
            return {"status": "no_connection"}
        
        if not connection.token_expiry:
            return {"status": "active", "grace_period": False}
        
        now = datetime.utcnow()
        days_remaining = (connection.token_expiry - now).days
        
        if connection.is_revoked:
            return {
                "status": "revoked",
                "revoked_at": connection.cancellation_metadata.get("revoked_at"),
            }
        
        if days_remaining > 0:
            return {
                "status": "grace_period_active",
                "days_remaining": days_remaining,
                "expires_at": connection.token_expiry.isoformat(),
                "reactivation_possible": True,
            }
        else:
            return {
                "status": "expired",
                "expired_at": connection.token_expiry.isoformat(),
                "reactivation_requires_reauth": True,
            }
```

### Step 4: Integration with Cancellation Flow

**File**: `backend/app/cancellation_service.py` (MODIFY)

```python
# Add this import at top
from app.google_api_maintenance import GoogleAPIMaintenanceService

# In confirm_cancellation() function, add:
async def confirm_cancellation(
    db: Session,
    user_id: UUID,
    churn_reason: str | None = None,
    churn_detail: str | None = None,
) -> dict:
    """Confirm and process subscription cancellation."""
    
    # ... existing code ...
    
    # 3. Set Google API grace period (NEW)
    grace_status = GoogleAPIMaintenanceService.set_token_expiry_on_cancellation(
        db=db,
        user_id=user_id,
        grace_period_days=30,  # End of billing cycle
    )
    
    # ... rest of function ...
    
    return {
        "status": "cancelled",
        "message": "Subscription successfully cancelled",
        "user_id": str(user_id),
        "cancellation_date": today.isoformat(),
        "google_api_permissions_active_until": grace_status["token_expiry"],
        "grace_period_days": grace_status["grace_period_days"],
        # ... rest ...
    }
```

### Step 5: Scheduled Job for Token Cleanup

**File**: `backend/app/main.py` (MODIFY lifespan)

```python
from contextlib import asynccontextmanager
from app.google_api_maintenance import GoogleAPIMaintenanceService

async def cleanup_expired_tokens():
    """
    Scheduled job to clean up expired Google API tokens.
    Runs daily at 2 AM UTC.
    """
    async with get_db_session() as db:
        result = await GoogleAPIMaintenanceService.cleanup_expired_tokens(db)
        logger.info(f"Token cleanup completed: {result}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    scheduler = AsyncIOScheduler()
    
    # ... existing jobs ...
    
    # ADD: Daily token cleanup
    scheduler.add_job(
        cleanup_expired_tokens,
        trigger="cron",
        hour=2,  # 2 AM UTC
        minute=0,
        id="cleanup_expired_tokens",
    )
    
    scheduler.start()
    
    # ... rest of startup ...
    
    yield
    
    # ... shutdown ...
```

### Step 6: Check Token Status in API Requests

**File**: `backend/app/auth.py` (MODIFY)

```python
def check_google_api_status(
    db: Session,
    user_id: UUID,
) -> dict:
    """Check if Google API tokens are active/expired for user."""
    from app.google_api_maintenance import GoogleAPIMaintenanceService
    
    status = GoogleAPIMaintenanceService.get_grace_period_status(
        user_id=user_id,
        db=db,
    )
    
    return status

# In your main API route guard:
async def get_current_user_with_api_check(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get current user and check if Google API is still active."""
    api_status = check_google_api_status(db, current_user.id)
    
    # Log warning if in grace period
    if api_status["status"] == "grace_period_active":
        logger.warning(
            f"User in grace period: {current_user.id}, "
            f"days remaining: {api_status['days_remaining']}"
        )
    
    # Block if revoked
    if api_status["status"] == "revoked":
        raise HTTPException(
            status_code=401,
            detail="Google API permissions have expired. Please resubscribe.",
        )
    
    return current_user
```

### Step 7: Frontend Display of Grace Period

**File**: `frontend/src/components/subscription/SubscriptionSettings.tsx` (MODIFY)

```tsx
// Add this to show grace period info
async function getGracePeriodStatus() {
  const response = await fetch('/api/cancellation/grace-period-status', {
    credentials: 'include',
  })
  
  if (response.ok) {
    const status = await response.json()
    
    if (status.status === 'grace_period_active') {
      return (
        <Alert>
          <AlertTriangle className="h-4 w-4" />
          <AlertDescription>
            Tu acceso a Google Business Profile permanecerá activo hasta el{' '}
            <strong>{new Date(status.expires_at).toLocaleDateString('es-ES')}</strong>
            ({status.days_remaining} días restantes).
          </AlertDescription>
        </Alert>
      )
    }
  }
}
```

---

## Testing Checklist

- [ ] User cancels → token_expiry is set to NOW + 30 days
- [ ] Token remains valid for API calls during grace period
- [ ] Scheduled job runs daily and finds expired tokens
- [ ] Expired tokens are revoked via Google API
- [ ] is_revoked flag is set to True in database
- [ ] User gets blocked after expiry with clear error message
- [ ] User can reactivate during grace period without re-auth
- [ ] Logs capture all events (cancellation, grace period, revocation)

---

## Monitoring & Alerts

```python
# Add to monitoring dashboard:
- "Users in Grace Period" (count)
- "Tokens Expiring in 7 Days" (alert)
- "Revocation Failures" (error rate)
- "Reactivations During Grace Period" (recovery metric)
```

---

## Customer Communication

When user cancels, show in email + dashboard:

```
Tu suscripción ha sido cancelada.

✅ Acceso a tus datos: ACTIVO hasta el 30 de Junio
✅ Permisos de Google API: ACTIVOS hasta el 30 de Junio  
✅ Puedes volver en cualquier momento: SÍ

Después del 30 de Junio:
- Acceso de lectura desactivado
- Permisos de Google API revocados
- Se requiere re-autenticación para volver
```

---

## Edge Cases

| Scenario | Behavior |
|----------|----------|
| User reactivates during grace period | Cancel the token_expiry, resume normal operations |
| User doesn't reactivate after expiry | Token is revoked, user must re-auth |
| Multiple Google connections | Handle each independently |
| User cancels Plan Pausa | Set new token_expiry from today |
| User upgrades back | Clear token_expiry and cancellation_metadata |

