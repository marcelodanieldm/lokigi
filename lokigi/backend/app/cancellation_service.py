"""Cancellation and retention logic for Starter panel.

Handles:
- Calculating hours saved during subscription
- Impact modal data
- Plan Pause downsellingoferta alternativa de pausa
- Maintaining Google API permissions until billing cycle ends
"""

from datetime import date, datetime, timedelta
from uuid import UUID

import httpx
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.billing_service import get_or_create_subscription_profile
from app.config import settings
from app.models import User, Review, GoogleConnection, ChurnSurvey, SubscriptionProfile
from app.telemetry_models import ChurnReasonOption


_SENDGRID_SEND_URL = "https://api.sendgrid.com/v3/mail/send"


class CancellationService:
    """Service for handling subscription cancellation with retention logic."""

    FEEDBACK_OPTIONS = [
        {
            "key": "price",
            "label": "Precio",
            "description": "El costo actual no encaja con el valor percibido o el volumen del negocio.",
        },
        {
            "key": "difficulty",
            "label": "Dificultad",
            "description": "La configuración o el uso diario de Lokigi resultó confuso.",
        },
        {
            "key": "business_closed",
            "label": "Cierre de negocio",
            "description": "El negocio cerró o pausó su operación y ya no necesita automatización activa.",
        },
    ]
    
    @staticmethod
    def _cutoff_date() -> datetime:
        """Current implementation assumes a 30-day remaining cycle window."""
        return datetime.utcnow() + timedelta(days=30)

    @staticmethod
    def _normalize_reason(churn_reason: str) -> ChurnReasonOption:
        """Map UI reasons to persisted enum values without schema changes."""
        mapping = {
            "price": ChurnReasonOption.PRICE_TOO_HIGH,
            "price_too_high": ChurnReasonOption.PRICE_TOO_HIGH,
            "difficulty": ChurnReasonOption.EASE_OF_USE_DIFFICULTY,
            "ease_of_use_difficulty": ChurnReasonOption.EASE_OF_USE_DIFFICULTY,
            "business_closed": ChurnReasonOption.PERSONAL_REASONS,
            "business_temporarily_closed": ChurnReasonOption.PERSONAL_REASONS,
            "switched_competitor": ChurnReasonOption.SWITCHED_COMPETITOR,
        }
        return mapping.get(churn_reason, ChurnReasonOption.OTHER)

    @staticmethod
    def allowed_feedback_reasons() -> list[str]:
        return [item["key"] for item in CancellationService.FEEDBACK_OPTIONS]

    @staticmethod
    def feedback_options() -> list[dict[str, str]]:
        return list(CancellationService.FEEDBACK_OPTIONS)

    @staticmethod
    def _metrics_pdf_url(user_id: UUID, cutoff_date: datetime) -> str:
        """Point to print/PDF-ready monthly report page for export handoff."""
        return (
            f"/starter/report?user_id={user_id}&year={cutoff_date.year}&month={cutoff_date.month}"
        )

    @staticmethod
    def _reviews_csv_url(user_id: UUID) -> str:
        return f"/subscription/export-csv?user_id={user_id}"

    @staticmethod
    async def _send_cancellation_farewell_email(
        *,
        to_email: str,
        business_name: str,
        cut_off_date_iso: str,
        metrics_pdf_url: str,
        reviews_csv_url: str,
    ) -> bool:
        """Send legal cancellation confirmation and goodwill links via SendGrid."""
        if not settings.sendgrid_api_key or not to_email:
            return False

        subject = "Confirmación de cancelación | Lokigi"
        full_metrics_url = f"https://{settings.app_domain}{metrics_pdf_url}"
        full_reviews_csv_url = f"https://{settings.app_domain}{reviews_csv_url}"

        html_body = f"""
<!doctype html>
<html lang=\"es\">
<head><meta charset=\"utf-8\"><title>{subject}</title></head>
<body style=\"font-family:Arial,sans-serif;background:#f4f6f9;padding:24px\">
  <div style=\"max-width:620px;margin:0 auto;background:#fff;border-radius:10px;overflow:hidden;border:1px solid #e5e7eb\">
    <div style=\"background:#111827;padding:20px 24px\">
      <h1 style=\"margin:0;color:#fff;font-size:20px\">Lokigi</h1>
      <p style=\"margin:6px 0 0;color:#d1d5db\">Confirmación de desuscripción</p>
    </div>
    <div style=\"padding:24px\">
      <p style=\"margin-top:0\">Tu solicitud de cancelación fue procesada correctamente.</p>
      <p><strong>Tu plan seguirá activo hasta el {cut_off_date_iso}.</strong></p>
      <p style=\"margin-bottom:18px\">Como gesto de buena voluntad, dejamos listo tu historial de métricas en formato imprimible/PDF.</p>
      <div style=\"margin:18px 0\">
        <a href=\"{full_metrics_url}\" style=\"background:#1d4ed8;color:#fff;padding:10px 16px;border-radius:6px;text-decoration:none;font-weight:700\">Descargar historial (PDF)</a>
      </div>
            <div style=\"margin:18px 0\">
                <a href=\"{full_reviews_csv_url}\" style=\"background:#0f766e;color:#fff;padding:10px 16px;border-radius:6px;text-decoration:none;font-weight:700\">Exportar reseñas y respuestas IA (CSV)</a>
            </div>
      <p style=\"font-size:14px;color:#4b5563\">Negocio asociado: <strong>{business_name}</strong></p>
      <p style=\"font-size:13px;color:#6b7280\">Este correo sirve como confirmación legal de la cancelación.</p>
    </div>
    <div style=\"background:#f9fafb;padding:14px 24px;font-size:12px;color:#9ca3af\">Lokigi · {settings.app_domain}</div>
  </div>
</body>
</html>
"""

        payload = {
            "personalizations": [{"to": [{"email": to_email}]}],
            "from": {"email": settings.sendgrid_from_email, "name": "Lokigi"},
            "subject": subject,
            "content": [{"type": "text/html", "value": html_body}],
        }

        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(
                _SENDGRID_SEND_URL,
                headers={"Authorization": f"Bearer {settings.sendgrid_api_key}"},
                json=payload,
            )
            return resp.status_code in (200, 202)

    @staticmethod
    def calculate_hours_saved_this_month(
        db: Session,
        user_id: UUID,
    ) -> dict:
        """
        Calculate hours saved by user this month.
        
        Estimation: Each AI-approved reply saves ~2-3 minutes of manual writing + 1-2 min review
        Assumption: 3 minutes saved per approved response (conservative)
        """
        # Get current month start
        today = datetime.utcnow()
        month_start = datetime(today.year, today.month, 1)
        
        # Count AI responses approved THIS MONTH
        approved_this_month = db.scalar(
            select(func.count(Review.id))
            .join(GoogleConnection, Review.connection_id == GoogleConnection.id)
            .where(
                GoogleConnection.user_id == user_id,
                Review.reply_sent_at >= month_start,
                Review.reply_sent_at.isnot(None),
            )
        ) or 0
        
        # Calculate hours saved (3 minutes per response = 0.05 hours)
        minutes_saved = approved_this_month * 3
        hours_saved = minutes_saved / 60
        
        # Get user's subscription plan (for context)
        subscription_profile = db.scalar(select(SubscriptionProfile).where(SubscriptionProfile.user_id == user_id))
        plan = subscription_profile.subscription_plan if subscription_profile else "starter"
        
        return {
            "hours_saved": round(hours_saved, 1),
            "responses_approved": approved_this_month,
            "minutes_saved": minutes_saved,
            "plan": plan,
            "month": today.strftime("%B %Y"),
            "impact_message": f"🎯 Has ahorrado <strong>{hours_saved:.1f} horas</strong> este mes procesando {approved_this_month} reseñas automáticamente.",
        }
    
    @staticmethod
    def get_impact_data_for_user(
        db: Session,
        user_id: UUID,
    ) -> dict:
        """
        Get comprehensive impact data for cancellation modal.
        
        Shows:
        - Hours saved this month
        - Total reviews processed
        - Current plan features
        - Alternative offer (Plan Pausa)
        """
        hours_data = CancellationService.calculate_hours_saved_this_month(db, user_id)
        
        # Get total lifetime stats
        total_reviews = db.scalar(
            select(func.count(Review.id))
            .join(GoogleConnection, Review.connection_id == GoogleConnection.id)
            .where(GoogleConnection.user_id == user_id)
        ) or 0
        
        total_approved = db.scalar(
            select(func.count(Review.id))
            .join(GoogleConnection, Review.connection_id == GoogleConnection.id)
            .where(
                GoogleConnection.user_id == user_id,
                Review.reply_sent_at.isnot(None),
            )
        ) or 0
        
        # Get user's subscription info
        user = db.query(User).filter_by(id=user_id).first()
        connection = db.query(GoogleConnection).filter_by(user_id=user_id).first()
        subscription_profile = get_or_create_subscription_profile(db, user_id)
        
        if not user or not connection:
            raise ValueError("User or connection not found")
        
        # Calculate days subscribed
        days_subscribed = (datetime.utcnow() - user.created_at).days
        
        # Determine if user is high-value (>100 approved responses)
        is_high_value = total_approved > 100
        
        return {
            "user_id": str(user_id),
            "hours_saved_this_month": hours_data["hours_saved"],
            "responses_approved_this_month": hours_data["responses_approved"],
            "impact_message": hours_data["impact_message"],
            "total_reviews_processed": total_reviews,
            "total_approved_responses": total_approved,
            "approval_rate": (total_approved / total_reviews * 100) if total_reviews > 0 else 0,
            "days_subscribed": days_subscribed,
            "current_plan": subscription_profile.subscription_plan,
            "is_high_value": is_high_value,
            "plan_price_monthly": 29.0,  # TODO: Get from subscription data
        }
    
    @staticmethod
    def start_cancellation_process(
        db: Session,
        user_id: UUID,
        churn_reason: str,
    ) -> dict:
        """
        Initiate cancellation process.
        
        Returns:
        - Impact data for modal
        - Churn reason for tracking
        - Suggested alternative offers
        """
        impact_data = CancellationService.get_impact_data_for_user(db, user_id)
        
        # Always offer Plan Pausa before final churn.
        offers = [{
            "type": "plan_pausa",
            "name": "Plan Pausa",
            "description": "Pausa tu cuenta por $5/mes y conserva tu historial IA y reportes; solo se suspende la automatización.",
            "price": 5,
            "duration_days": 90,
            "features": [
                "✅ Conserva histórico de reseñas y respuestas IA",
                "✅ Mantén acceso a reportes y exportaciones",
                "❌ Automatización de respuestas suspendida",
                "❌ Sin envío automático mientras la cuenta esté pausada",
            ],
            "benefit_message": "Mantén el valor acumulado sin perder tu cuenta ni tus reportes.",
        }]

        if churn_reason in {"price", "price_too_high"}:
            # Also offer annual plan discount if applicable
            offers.append({
                "type": "annual_discount",
                "name": "Plan Anual (20% OFF)",
                "description": "Cambia a plan anual y ahorra 20% ($278/año en lugar de $348)",
                "price": 278,
                "duration_days": 365,
                "features": [
                    "✅ Todas las features del plan Starter",
                    "✅ Acceso IA completo",
                    "✅ Alertas de competidores",
                    "✅ 20% de descuento anual",
                ],
                "benefit_message": "Mejor valor si planeas quedarte",
            })
        
        elif churn_reason in {"difficulty", "ease_of_use_difficulty"}:
            # Offer support + extended trial
            offers.append({
                "type": "onboarding_support",
                "name": "Soporte Personalizado (Gratis)",
                "description": "Sesión 1:1 con nuestro equipo para optimizar tu setup",
                "price": 0,
                "duration_days": 30,  # Valid for 30 days
                "features": [
                    "✅ Sesión de configuración 1:1",
                    "✅ Optimizar respuestas IA",
                    "✅ Mejora tu workflow",
                    "✅ Primeros 30 días en nuestra mano",
                ],
                "benefit_message": "Te ayudamos a maximizar tu ROI",
            })
        
        return {
            "status": "cancellation_initiated",
            "impact_data": impact_data,
            "churn_reason": churn_reason,
            "feedback_options": CancellationService.feedback_options(),
            "alternative_offers": offers,
            "billing_cycle_end": CancellationService._cutoff_date().date().isoformat(),
        }
    
    @staticmethod
    def activate_plan_pausa(
        db: Session,
        user_id: UUID,
        duration_days: int = 90,
    ) -> dict:
        """
        Activate Plan Pausa ($5/month, read-only access).
        
        - Downgrades subscription
        - Maintains Google API permissions
        - Records event in lifecycle_events
        - Saves pause reason
        
        Returns: Confirmation data
        """
        connection = db.query(GoogleConnection).filter_by(user_id=user_id).first()
        if not connection:
            raise ValueError("Google connection not found")

        subscription_profile = get_or_create_subscription_profile(db, user_id)
        original_plan = subscription_profile.subscription_plan
        
        # TODO: In production, update Stripe subscription to $5/month plan
        # For now, just update our records
        
        # Record the pause event
        from app.models import LifecycleEvent
        from app.telemetry_models import LifecycleEventType
        
        connection.manual_approval_enabled = True
        connection.negative_review_whatsapp_enabled = False
        subscription_profile.subscription_plan = "plan_pausa"
        subscription_profile.subscription_status = "active"
        subscription_profile.current_period_end = datetime.utcnow() + timedelta(days=duration_days)

        pause_event = LifecycleEvent(
            user_id=user_id,
            event_type=LifecycleEventType.SUBSCRIPTION_PAUSED.value,
            event_metadata={
                "original_plan": original_plan,
                "paused_plan": "plan_pausa",
                "pause_duration_days": duration_days,
                "paused_at": datetime.utcnow().isoformat(),
                "resume_date": (datetime.utcnow() + timedelta(days=duration_days)).isoformat(),
                "automation_status": "suspended",
            }
        )
        db.add(pause_event)
        db.commit()
        
        return {
            "status": "success",
            "message": "Cuenta pausada por $5/mes. Conservamos historial y reportes; la automatización queda suspendida.",
            "plan": "plan_pausa",
            "price": 5.0,
            "duration_days": duration_days,
            "resume_date": (datetime.utcnow() + timedelta(days=duration_days)).date().isoformat(),
            "google_api_permissions": "active",
            "access_level": "history_and_reports_only",
        }
    
    @staticmethod
    async def confirm_cancellation(
        db: Session,
        user_id: UUID,
        churn_reason: str,
        churn_detail: str | None = None,
    ) -> dict:
        """
        Confirm and process subscription cancellation.
        
        Actions:
        1. Save churn survey data
        2. Capture telemetry snapshot
        3. Ensure Google API permissions active until cycle end
        4. Record cancellation in lifecycle_events
        5. Run all churn alerts
        """
        from app.models import ChurnSurvey, ChurnTelemetrySnapshot as TelemetryModel, LifecycleEvent
        from app.telemetry_models import LifecycleEventType
        from app.churn_alert_engine import run_all_churn_checks
        
        user = db.query(User).filter_by(id=user_id).first()
        connection = db.query(GoogleConnection).filter_by(user_id=user_id).first()
        
        if not user or not connection:
            raise ValueError("User or connection not found")
        
        # 1. Save churn survey
        today = datetime.utcnow().date()
        
        # Parse churn reason from allowed UI options.
        reason_enum = CancellationService._normalize_reason(churn_reason)
        
        survey = ChurnSurvey(
            user_id=user_id,
            cancellation_date=today,
            primary_reason=reason_enum.value,
            satisfaction_score=3,  # Default; would be from survey
            free_text_feedback=churn_detail,
        )
        db.add(survey)
        db.flush()
        
        # 2. Capture telemetry snapshot
        total_reviews = db.scalar(
            select(func.count(Review.id))
            .join(GoogleConnection, Review.connection_id == GoogleConnection.id)
            .where(GoogleConnection.user_id == user_id)
        ) or 0
        
        approved_reviews = db.scalar(
            select(func.count(Review.id))
            .join(GoogleConnection, Review.connection_id == GoogleConnection.id)
            .where(
                GoogleConnection.user_id == user_id,
                Review.reply_sent_at.isnot(None),
            )
        ) or 0
        
        approval_rate = (approved_reviews / total_reviews) if total_reviews > 0 else 0.0
        active_days = (datetime.utcnow().date() - user.created_at.date()).days
        
        # Delete old snapshot if exists (unique constraint)
        db.query(TelemetryModel).filter_by(user_id=user_id).delete()
        
        telemetry = TelemetryModel(
            user_id=user_id,
            active_days_before_cancel=active_days,
            last_activity_days_ago=3,  # TODO: Calculate real value
            total_reviews_processed=total_reviews,
            total_ai_responses_generated=approved_reviews,  # Simplified
            total_ai_responses_approved=approved_reviews,
            approval_rate=approval_rate,
            used_tone_selector=connection.preferred_tone != "cercano",
            locations_connected=1,  # TODO: Count actual
            days_subscribed=active_days,
            subscription_plan=subscription_profile.subscription_plan,
        )
        db.add(telemetry)
        db.flush()
        
        # 3. Ensure Google API permissions stay active until billing cycle end.
        billing_cycle_end = CancellationService._cutoff_date()
        metrics_pdf_url = CancellationService._metrics_pdf_url(user_id, billing_cycle_end)
        reviews_csv_url = CancellationService._reviews_csv_url(user_id)

        connection.manual_approval_enabled = True
        connection.negative_review_whatsapp_enabled = False
        subscription_profile.subscription_status = "cancelled"
        subscription_profile.current_period_end = billing_cycle_end
        
        # 4. Record churn lifecycle event
        churn_event = LifecycleEvent(
            user_id=user_id,
            event_type=LifecycleEventType.CHURN_INITIATED.value,
            event_metadata={
                "reason": reason_enum.value,
                "detail": churn_detail,
                "plan": subscription_profile.subscription_plan,
                "approval_rate": approval_rate,
                "active_days": active_days,
                "google_api_permissions_active_until": billing_cycle_end.isoformat(),
                "metrics_pdf_url": metrics_pdf_url,
                "reviews_csv_url": reviews_csv_url,
                "automation_status": "suspended",
            }
        )
        db.add(churn_event)
        db.commit()
        
        # 5. Run all churn alerts (async, fire-and-forget)
        # In production: Queue this as a background task
        alerts = await run_all_churn_checks(db)

        farewell_email_sent = await CancellationService._send_cancellation_farewell_email(
            to_email=user.email,
            business_name=connection.business_name or connection.google_account_name,
            cut_off_date_iso=billing_cycle_end.date().isoformat(),
            metrics_pdf_url=metrics_pdf_url,
            reviews_csv_url=reviews_csv_url,
        )
        
        return {
            "status": "cancelled",
            "message": "Subscription successfully cancelled",
            "user_id": str(user_id),
            "cancellation_date": today.isoformat(),
            "last_charge_date": datetime.utcnow().date().isoformat(),
            "google_api_permissions_active_until": billing_cycle_end.isoformat(),
            "access_level_after_cancellation": "read_only_until_" + billing_cycle_end.date().isoformat(),
            "cutoff_date": billing_cycle_end.date().isoformat(),
            "metrics_pdf_url": metrics_pdf_url,
            "reviews_csv_url": reviews_csv_url,
            "logout_url": "/api/cancellation/logout",
            "goodbye_email_sent": farewell_email_sent,
            "alerts_triggered": len([a for a in alerts if a.severity in ["HIGH", "CRITICAL"]]),
        }
