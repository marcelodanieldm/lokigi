import html
import json
import logging
from calendar import monthrange
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID

from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from starlette.middleware.trustedhost import TrustedHostMiddleware
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from . import database
from .billing_service import (
  check_growth_upgrade_needed,
  create_growth_checkout_session,
  get_subscription_summary,
  list_subscription_invoices,
)
from .config import settings
from .cancellation_service import CancellationService
from .database import Base, get_db
from .growth_seo_service import GrowthSeoService
from .models import GoogleConnection, GrowthSeoSuggestion, Review, StarterProfileSettings, User
from pydantic import BaseModel
from .google_client import GoogleBusinessProfileClient, GoogleOAuthError

from .services import (
    OAuthStateManager,
  build_review_processing_task_payload,
    build_google_oauth_url,
    get_pending_approvals,
    list_locations_for_user,
    parse_pubsub_push,
    regenerate_review_reply,
    send_review_reply,
    ensure_valid_access_token,
    process_review_workflow,
    store_new_review_from_webhook,
    upsert_google_connection,
    verify_pubsub_jwt,
)
from .sentiment_analysis import analyze_monthly_sentiment
from .review_reply_engine import generate_reply_by_tone
from .socketio_server import socketio_app
from .starter_tip_service import generate_starter_tip
from .monthly_report_worker import _build_response_velocity, build_scheduler
from tasks.review_processing import process_google_review, process_reviews
from .routes import (
  cancellation_routes,
  competitor_scrape_routes,
  grace_period_routes,
  growth_dashboard_routes,
  growth_event_routes,
  growth_routes,
  growth_seo_routes,
  nlp_analysis_routes,
  onboarding_routes,
  starter_inbox_routes,
)
from .routes.cancellation_routes import build_reviews_export_response


logger = logging.getLogger(__name__)


class ApproveReplyRequest(BaseModel):
    reply_text: str


class StarterActivationRequest(BaseModel):
  user_id: UUID
  tone: str
  manual_approval: bool = True
  whatsapp_negative_alerts: bool = False


class ToneSetRequest(BaseModel):
  user_id: UUID
  tone: str


class StarterProfileSaveRequest(BaseModel):
  user_id: UUID
  tone: str
  forbidden_words: str = ""
  response_schedule: str = "instant"


class GrowthUpgradeRequest(BaseModel):
  user_id: UUID


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=database.engine)
    scheduler = build_scheduler()
    scheduler.start()
    yield
    scheduler.shutdown(wait=False)


app = FastAPI(title=settings.app_name, lifespan=lifespan)
app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.parsed_allowed_hosts())

app.include_router(cancellation_routes.router)
app.include_router(grace_period_routes.router)
app.include_router(growth_routes.router)
app.include_router(growth_dashboard_routes.router)
app.include_router(growth_event_routes.router)
app.include_router(competitor_scrape_routes.router)
app.include_router(growth_seo_routes.router)
app.include_router(nlp_analysis_routes.router)
app.include_router(onboarding_routes.router)
app.include_router(starter_inbox_routes.router)
app.mount("/starter-realtime", socketio_app)


def _esc(value: Any) -> str:
  return html.escape(str(value or ""), quote=True)


def _tone_label(tone: str | None) -> str:
  labels = {
    "cercano": "Cercano",
    "formal": "Formal",
    "moderno": "Moderno/Emoji",
  }
  return labels.get((tone or "cercano").lower(), "Cercano")


def _tone_badge_class(tone: str | None) -> str:
  mapping = {
    "cercano": "tone-cercano",
    "formal": "tone-formal",
    "moderno": "tone-moderno",
  }
  return mapping.get((tone or "cercano").lower(), "tone-cercano")


def _highlight_keyword_html(text: str | None, keyword: str | None) -> str:
  safe_text = _esc(text).replace("\n", "<br />")
  if not safe_text or not keyword:
    return safe_text

  needle = keyword.strip()
  if not needle:
    return safe_text

  lower_text = safe_text.lower()
  lower_needle = needle.lower()
  start = lower_text.find(lower_needle)
  if start == -1:
    return safe_text

  end = start + len(needle)
  return f"{safe_text[:start]}<mark>{safe_text[start:end]}</mark>{safe_text[end:]}"


async def _sync_google_profile_snapshot(db: Session, connection: GoogleConnection) -> dict[str, Any]:
  profile_name = f"{connection.google_account_name}/locations/{connection.location_id}"
  access_token = await ensure_valid_access_token(db, connection)
  client = GoogleBusinessProfileClient(
    settings.google_client_id,
    settings.google_client_secret,
    settings.google_redirect_uri,
  )
  location_data = await client.get_location_metadata(access_token=access_token, location_name=profile_name)

  connection.business_name = location_data.get("title") or connection.business_name or connection.google_account_name
  profile_payload = location_data.get("profile") or {}
  description = profile_payload.get("description") if isinstance(profile_payload, dict) else None
  connection.google_profile_description = description.strip() if isinstance(description, str) and description.strip() else None
  db.add(connection)
  db.commit()
  db.refresh(connection)
  return location_data


def render_optimization_center_html(
  user_id: UUID,
  suggestion: GrowthSeoSuggestion | None,
  *,
  notice: str | None = None,
  notice_tone: str = "info",
) -> str:
  if not suggestion:
    return ""

  keyword = _esc(suggestion.keyword)
  suggestion_type = "Descripcion" if suggestion.suggestion_type == "description_update" else "Servicio destacado"
  current_text_raw = (suggestion.current_text or "").strip()
  suggested_text_raw = (suggestion.suggested_text or "").strip()
  current_text_html = (
    _highlight_keyword_html(current_text_raw, suggestion.keyword)
    if current_text_raw
    else '<span class="muted">Tu perfil no tiene una descripcion publicada en Google o aun no hay una copia local disponible. La sugerencia usa esta oportunidad como nueva base recomendada.</span>'
  )
  suggested_text_html = _highlight_keyword_html(suggested_text_raw, suggestion.keyword)

  justification = suggestion.justification_payload or {}
  support = int(justification.get("support") or 0)
  comp_share = float(justification.get("comp_share") or 0.0) * 100
  client_share = float(justification.get("client_share") or 0.0) * 100
  gap_share = float(justification.get("gap_share") or 0.0) * 100
  priority_score = int(suggestion.priority_score or 0)
  modal_id = f"optimization-confirm-{suggestion.id}"

  notice_html = ""
  if notice:
    notice_class = "optimization-notice ok" if notice_tone == "ok" else "optimization-notice error" if notice_tone == "error" else "optimization-notice"
    notice_html = f'<div class="{notice_class}">{_esc(notice)}</div>'

  return f"""
    <section class=\"card optimization-card\" id=\"optimization-center\">
      <div class=\"optimization-head\">
        <div>
          <div class=\"optimization-kicker\">Sección SEO</div>
          <h2>Tu competencia está ganando terreno con '{keyword}'</h2>
          <p class=\"muted\">¿Quieres añadirlo a tu descripción? Lokigi ya preparó un cambio para que compares tu texto actual con una versión nueva optimizada.</p>
        </div>
        <div class=\"optimization-priority\">Prioridad {priority_score}/100</div>
      </div>

      {notice_html}

      <div class=\"optimization-explainer\">
        <strong>Lectura de IA</strong>
        <p>Detectamos una brecha de <strong>{gap_share:.1f}%</strong> entre tu presencia y la de competidores locales para esta keyword. En la muestra analizada, ellos concentran <strong>{comp_share:.1f}%</strong> de las menciones frente a tu <strong>{client_share:.1f}%</strong>, con <strong>{support}</strong> apariciones de soporte.</p>
      </div>

      <div class=\"optimization-metrics\">
        <div class=\"optimization-metric\"><span>Keyword ganadora</span><strong>{keyword}</strong></div>
        <div class=\"optimization-metric\"><span>Tipo</span><strong>{_esc(suggestion_type)}</strong></div>
        <div class=\"optimization-metric\"><span>Riesgo</span><strong>{_esc(suggestion.risk_level.title())}</strong></div>
      </div>

      <div class=\"optimization-explainer\">
        <strong>Revisión</strong>
        <p>Compara tu texto viejo con el nuevo propuesto por Lokigi antes de confirmar el cambio.</p>
      </div>

      <div class=\"optimization-compare\">
        <article class=\"optimization-pane before\">
          <span class=\"optimization-label\">Antes</span>
          <div class=\"optimization-text\">{current_text_html}</div>
        </article>
        <article class=\"optimization-pane after\">
          <span class=\"optimization-label\">Despues</span>
          <div class=\"optimization-text\">{suggested_text_html}</div>
        </article>
      </div>

      <div class=\"cta-row\">
        <button
          class="btn"
          hx-post="/starter/optimization-center/refresh?user_id={user_id}"
          hx-target="#optimization-center"
          hx-swap="outerHTML swap:180ms"
        >Buscar nuevas oportunidades</button>
        <button
          class=\"btn primary\"
          type=\"button\"
          onclick=\"document.getElementById('optimization-confirm-{suggestion.id}').hidden = false\"
        >Revisar y aceptar</button>
        <button
          class=\"btn\"
          hx-post=\"/starter/optimization-center/{suggestion.id}/dismiss?user_id={user_id}\"
          hx-target=\"#optimization-center\"
          hx-swap="outerHTML swap:180ms"
        >Ahora no</button>
      </div>

      <div
        class=\"optimization-modal-backdrop\"
        id=\"optimization-confirm-{suggestion.id}\"
        hidden
        onclick=\"if (event.target === this) this.hidden = true\"
      >
        <div class=\"optimization-modal\" role=\"dialog\" aria-modal=\"true\" aria-labelledby=\"optimization-confirm-title-{suggestion.id}\">
          <div class=\"optimization-modal-kicker\">Confirmación</div>
          <h3 id=\"optimization-confirm-title-{suggestion.id}\">Confirmar actualización del perfil</h3>
          <p>Si aceptas, Lokigi enviará a Google tu nueva descripción con la keyword <strong>{keyword}</strong>. El cambio quedará aplicado para medir su impacto en el próximo reporte mensual.</p>
          <div class=\"cta-row\">
            <button class=\"btn\" type=\"button\" onclick=\"document.getElementById('optimization-confirm-{suggestion.id}').hidden = true\">Cancelar</button>
            <button
              class=\"btn primary\"
              hx-post=\"/starter/optimization-center/{suggestion.id}/apply?user_id={user_id}\"
              hx-target=\"#optimization-center\"
              hx-swap="outerHTML swap:180ms"
              hx-disabled-elt=\"this\"
              hx-on:htmx:before-request=\"this.dataset.originalText = this.textContent; this.textContent = 'Enviando a Google...'; this.disabled = true;\"
            >Aceptar</button>
          </div>
        </div>
      </div>
    </section>
  """


def render_optimization_success_html(user_id: UUID, keyword: str) -> str:
  safe_keyword = _esc(keyword)
  return f"""
    <section class=\"card optimization-success\" id=\"optimization-center\">
      <div class=\"optimization-success-icon\">OK</div>
      <div class=\"optimization-kicker\">Perfil actualizado</div>
      <h2>¡Perfil Actualizado!</h2>
      <p>¡Listo! Google ya tiene tu nueva información. Verás el impacto en el próximo reporte mensual.</p>
      <div class=\"cta-row\">
        <button
          class=\"btn\"
          hx-post=\"/starter/optimization-center/refresh?user_id={user_id}\"
          hx-target=\"#optimization-center\"
          hx-swap="outerHTML swap:180ms"
        >Buscar nuevas oportunidades</button>
      </div>
    </section>
  """


def render_optimization_hub_tab_html(has_alert: bool, *, oob: bool = False) -> str:
  active_class = " active" if has_alert else ""
  dot_html = '<span class="hub-tab-dot" aria-hidden="true"></span>' if has_alert else ""
  oob_attr = ' hx-swap-oob="outerHTML"' if oob else ""
  aria_current = ' aria-current="page"' if has_alert else ""
  return (
    f'<a class="hub-tab{active_class}" id="optimization-hub-tab" href="#optimization-section" '
    f'onclick="document.getElementById(\'optimization-section\')?.scrollIntoView({{behavior:\'smooth\', block:\'start\'}}); return false;"{aria_current}{oob_attr}>'
    f'Optimización{dot_html}</a>'
  )


def render_optimization_partial_response(content_html: str, *, has_alert: bool) -> str:
  return f"{content_html}{render_optimization_hub_tab_html(has_alert=has_alert, oob=True)}"


def render_starter_tone_selector_html(
  user_id: UUID,
  first_review_text: str,
  first_review_author: str,
  first_review_stars: int,
  business_name: str,
  current_tone: str,
  manual_approval_enabled: bool,
  whatsapp_negative_alerts_enabled: bool,
) -> str:
  """Step 3-4 onboarding screen with tone preview and pilot activation."""
  business_name_html = _esc(business_name)
  review_text_html = _esc(first_review_text)
  author_html = _esc(first_review_author)
  current_tone = (current_tone or "cercano").lower()
  review_text_js = json.dumps(first_review_text)
  author_js = json.dumps(first_review_author)
  business_name_js = json.dumps(business_name)
  stars_label = "★" * max(first_review_stars, 1)
  return f"""
<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Voz de Marca y Activación | Lokigi</title>
  <style>
    :root {{
      --bs-primary: #0d6efd;
      --bs-primary-dark: #0a58ca;
      --bs-success: #198754;
      --bs-warning: #ffc107;
      --bs-light: #f8f9fa;
      --bs-border: #dee2e6;
      --bs-body: #f4f7fb;
      --bs-text: #212529;
      --bs-muted: #6c757d;
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: Arial, "Helvetica Neue", sans-serif;
      background:
        radial-gradient(circle at top left, rgba(13, 110, 253, 0.14), transparent 32%),
        linear-gradient(180deg, #ffffff 0%, var(--bs-body) 100%);
      min-height: 100vh;
      color: var(--bs-text);
      padding: 24px 16px 40px;
    }}
    .container {{ max-width: 1120px; margin: 0 auto; }}
    .wizard-card {{ background: #fff; border: 1px solid var(--bs-border); border-radius: 20px; box-shadow: 0 1rem 2rem rgba(33, 37, 41, 0.08); overflow: hidden; }}
    .hero {{ padding: 28px 28px 20px; border-bottom: 1px solid var(--bs-border); background: linear-gradient(135deg, #ffffff, #eef5ff); }}
    .hero h1 {{ font-size: clamp(1.9rem, 4vw, 2.6rem); line-height: 1.05; margin: 10px 0 8px; font-weight: 700; }}
    .hero p {{ color: var(--bs-muted); max-width: 760px; font-size: 1rem; margin-bottom: 0; }}
    .stepper {{ display: flex; flex-wrap: wrap; gap: 10px; margin-top: 18px; }}
    .step-badge {{ display: inline-flex; align-items: center; gap: 8px; border-radius: 999px; padding: 8px 14px; border: 1px solid var(--bs-border); background: #fff; color: var(--bs-muted); font-size: 0.9rem; }}
    .step-badge.active {{ color: var(--bs-primary-dark); border-color: rgba(13, 110, 253, 0.25); background: rgba(13, 110, 253, 0.08); font-weight: 700; }}
    .content {{ display: grid; grid-template-columns: 1.15fr 0.85fr; gap: 24px; padding: 24px 28px 28px; }}
    .section-title {{ font-size: 1.3rem; font-weight: 700; margin-bottom: 6px; }}
    .section-subtitle {{ color: var(--bs-muted); margin-bottom: 18px; line-height: 1.5; }}
    .tones-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 16px; margin-bottom: 20px; }}
    .tone-card {{ background: #fff; border: 2px solid var(--bs-border); border-radius: 16px; padding: 18px; cursor: pointer; transition: transform 0.16s ease, border-color 0.16s ease, box-shadow 0.16s ease; box-shadow: 0 0.35rem 0.8rem rgba(33, 37, 41, 0.06); position: relative; }}
    .tone-card:hover {{ transform: translateY(-2px); border-color: rgba(13, 110, 253, 0.45); }}
    .tone-card.selected {{ border-color: var(--bs-primary); background: linear-gradient(180deg, rgba(13, 110, 253, 0.06), #fff); box-shadow: 0 0 0 0.2rem rgba(13, 110, 253, 0.12); }}
    .tone-card.selected::after {{ content: '✓'; position: absolute; top: 12px; right: 12px; width: 28px; height: 28px; background: var(--bs-primary); color: #fff; border-radius: 50%; display: grid; place-items: center; font-weight: 700; font-size: 16px; }}
    .tone-icon {{ font-size: 30px; margin-bottom: 12px; display: block; }}
    .tone-title {{ font-size: 18px; font-weight: 700; margin-bottom: 6px; }}
    .tone-desc {{ font-size: 14px; color: var(--bs-muted); line-height: 1.5; margin-bottom: 12px; }}
    .tone-example {{ background: var(--bs-light); border: 1px solid var(--bs-border); border-radius: 8px; padding: 10px; font-size: 12px; color: var(--bs-muted); line-height: 1.5; font-style: italic; }}
    .preview-shell, .activation-shell {{ background: #fff; border: 1px solid var(--bs-border); border-radius: 16px; padding: 20px; }}
    .preview-shell {{ margin-bottom: 16px; }}
    .eyebrow {{ display: inline-block; font-size: 0.78rem; font-weight: 700; text-transform: uppercase; color: var(--bs-primary-dark); letter-spacing: 0.05em; margin-bottom: 10px; }}
    .business-chip {{ display: inline-flex; align-items: center; gap: 8px; border: 1px solid rgba(25, 135, 84, 0.22); color: #146c43; background: rgba(25, 135, 84, 0.08); border-radius: 999px; padding: 7px 12px; font-size: 0.85rem; margin-bottom: 14px; }}
    .original-review {{ border: 1px solid var(--bs-border); border-radius: 14px; padding: 16px; background: var(--bs-light); margin-bottom: 16px; }}
    .review-author {{ display: block; font-weight: 700; margin-bottom: 4px; }}
    .review-stars {{ display: block; color: #b7791f; font-size: 0.85rem; font-weight: 700; margin-bottom: 6px; }}
    .review-text {{ color: var(--bs-muted); line-height: 1.6; font-size: 0.95rem; }}
    .preview-content {{ background: #eef5ff; border: 1px dashed rgba(13, 110, 253, 0.35); border-radius: 14px; padding: 16px; min-height: 104px; line-height: 1.6; font-size: 0.95rem; }}
    .preview-content.empty {{ color: var(--bs-muted); font-style: italic; }}
    .check-row {{ display: flex; gap: 12px; align-items: flex-start; padding: 14px 0; border-top: 1px solid var(--bs-border); }}
    .check-row:first-of-type {{ border-top: 0; }}
    .check-row input {{ margin-top: 3px; width: 18px; height: 18px; }}
    .check-copy strong {{ display: block; margin-bottom: 3px; }}
    .check-copy span {{ color: var(--bs-muted); font-size: 0.92rem; line-height: 1.5; }}
    .btn {{ display: inline-flex; align-items: center; justify-content: center; gap: 10px; width: 100%; padding: 14px 18px; border-radius: 12px; border: 1px solid transparent; font-weight: 700; font-size: 1rem; cursor: pointer; transition: transform 0.16s ease, box-shadow 0.16s ease; text-decoration: none; }}
    .btn-primary {{ background: linear-gradient(135deg, var(--bs-primary), var(--bs-primary-dark)); color: #fff; }}
    .btn-primary:hover {{ transform: translateY(-2px); box-shadow: 0 12px 20px rgba(13, 110, 253, 0.24); }}
    .btn-primary:disabled {{ opacity: 0.6; cursor: not-allowed; transform: none; }}
    .mini-note {{ color: var(--bs-muted); font-size: 0.85rem; margin-top: 10px; }}
    .footer-nav {{ display: flex; justify-content: space-between; align-items: center; gap: 16px; margin-top: 18px; color: var(--bs-muted); font-size: 0.88rem; }}
    .loading-spinner {{ display: inline-block; width: 16px; height: 16px; border: 2px solid rgba(255, 255, 255, 0.3); border-radius: 50%; border-top-color: #fff; animation: spin 0.8s linear infinite; }}
    @keyframes spin {{ to {{ transform: rotate(360deg); }} }}
    .stack {{ display: grid; gap: 16px; }}
    @media (max-width: 960px) {{ .content {{ grid-template-columns: 1fr; }} }}
    @media (max-width: 640px) {{ body {{ padding: 14px 10px 30px; }} .hero, .content {{ padding-left: 18px; padding-right: 18px; }} .footer-nav {{ flex-direction: column; align-items: stretch; }} }}
  </style>
</head>
<body>
<div class="container">
  <div class="wizard-card">
    <div class="hero">
      <div class="eyebrow">Paso 3 y 4 de 4</div>
      <h1>Del mapa al dashboard en menos de 3 minutos</h1>
      <p>Elige la voz de marca, revisa una respuesta real de tu negocio y activa el modo piloto con la configuración recomendada para arrancar sin fricción.</p>
      <div class="stepper">
        <span class="step-badge">1. Registro</span>
        <span class="step-badge">2. Conexión segura</span>
        <span class="step-badge active">3. Voz de marca</span>
        <span class="step-badge active">4. Activar Starter</span>
      </div>
    </div>
    <div class="content">
      <section>
        <div class="section-title">Configura la voz de {business_name_html}</div>
        <div class="section-subtitle">Valor inmediato: te mostramos una reseña real antigua y cómo la respondería la IA con el tono que elijas.</div>
        <div class="tones-grid">
          <div class="tone-card" data-tone="cercano" onclick="selectTone(this)">
            <span class="tone-icon">🤝</span>
            <div class="tone-title">Cercano</div>
            <div class="tone-desc">Humano, cálido y directo. Ideal para negocios donde la confianza personal mueve la recompra.</div>
            <div class="tone-example">"¡Hola! Qué bueno que viniste. Nos encanta saber que la experiencia estuvo a la altura."</div>
          </div>
          <div class="tone-card" data-tone="formal" onclick="selectTone(this)">
            <span class="tone-icon">📘</span>
            <div class="tone-title">Formal</div>
            <div class="tone-desc">Sobrio y profesional. Encaja mejor en servicios premium, jurídicos, médicos o B2B.</div>
            <div class="tone-example">"Estimado cliente, agradecemos su visita y valoramos su comentario."</div>
          </div>
          <div class="tone-card" data-tone="moderno" onclick="selectTone(this)">
            <span class="tone-icon">🚀</span>
            <div class="tone-title">Moderno/Emoji</div>
            <div class="tone-desc">Ágil y energético. Funciona bien para retail, gastronomía y marcas con identidad digital marcada.</div>
            <div class="tone-example">"¡Gracias por la buena onda! 🚀 Nos da pila leer reseñas así."</div>
          </div>
        </div>
      </section>
      <aside class="stack">
        <div class="preview-shell">
          <div class="eyebrow">Preview en tiempo real</div>
          <div class="business-chip">Negocio listo: {business_name_html}</div>
          <div class="original-review">
            <span class="review-author">{author_html}</span>
            <span class="review-stars">{stars_label} · {first_review_stars} estrellas</span>
            <div class="review-text">{review_text_html}</div>
          </div>
          <div id="preview-content" class="preview-content empty">Selecciona un tono para ver cómo respondería Lokigi a esta reseña.</div>
          <div class="mini-note">Puedes ajustar la voz después desde el dashboard, pero arrancar con una preferencia acelera la calidad de las respuestas.</div>
        </div>
        <div class="activation-shell">
          <div class="eyebrow">Modo piloto</div>
          <div class="section-title" style="font-size:1.15rem; margin-bottom: 8px;">Activa tu cuenta Starter</div>
          <div class="section-subtitle" style="margin-bottom:14px;">Configuración inicial recomendada para minimizar riesgo y darte el primer “aha moment” rápido.</div>
          <label class="check-row">
            <input id="manual-approval" type="checkbox" {'checked' if manual_approval_enabled else ''} />
            <div class="check-copy">
              <strong>Aprobar manualmente respuestas antes de publicar</strong>
              <span>Recomendado al inicio. Lokigi prepara la sugerencia y tú conservas el control final.</span>
            </div>
          </label>
          <label class="check-row">
            <input id="whatsapp-alerts" type="checkbox" {'checked' if whatsapp_negative_alerts_enabled else ''} />
            <div class="check-copy">
              <strong>Activar alertas tempranas para reseñas negativas</strong>
              <span>Opcional. Te avisa rápido cuando aparece una reseña sensible para que actúes antes de que escale.</span>
            </div>
          </label>
          <button id="activate-btn" class="btn btn-primary" onclick="activateStarter()">
            <span class="loading-spinner" id="spinner" style="display:none;"></span>
            Activar mi cuenta Starter
          </button>
          <div class="footer-nav">
            <span>Respuesta rápida. Sin frameworks pesados. Sin esperas innecesarias.</span>
            <span id="activation-status"></span>
          </div>
        </div>
      </aside>
    </div>
  </div>
</div>

<script>
const USER_ID = "{user_id}";
const BUSINESS_NAME = {business_name_js};
const REVIEW_TEXT = {review_text_js};
const AUTHOR_NAME = {author_js};
const REVIEW_STARS = {first_review_stars};
const DEFAULT_TONE = {json.dumps(current_tone)};

let selectedTone = null;

async function selectTone(el) {{
  document.querySelectorAll(".tone-card").forEach(c => c.classList.remove("selected"));
  el.classList.add("selected");
  selectedTone = el.dataset.tone;

  try {{
    const res = await fetch("/api/tone-preview", {{
      method: "POST",
      headers: {{ "Content-Type": "application/json" }},
      body: JSON.stringify({{
        tone: selectedTone,
        review_text: REVIEW_TEXT,
        stars: REVIEW_STARS,
        business_name: BUSINESS_NAME,
        author_name: AUTHOR_NAME,
      }}),
    }});

    if (!res.ok) throw new Error(`HTTP ${{res.status}}`);
    const data = await res.json();
    document.getElementById("preview-content").textContent = data.preview;
    document.getElementById("preview-content").classList.remove("empty");
  }} catch (e) {{
    document.getElementById("preview-content").textContent = "No se pudo generar el adelanto ahora mismo. Puedes continuar y ajustar después.";
    document.getElementById("preview-content").classList.add("empty");
  }}
}}

async function activateStarter() {{
  if (!selectedTone) {{
    const firstCard = document.querySelector(`.tone-card[data-tone="${{DEFAULT_TONE}}"]`) || document.querySelector('.tone-card');
    if (firstCard) {{
      await selectTone(firstCard);
    }}
  }}

  const btn = document.getElementById("activate-btn");
  const spinner = document.getElementById("spinner");
  const status = document.getElementById("activation-status");

  btn.disabled = true;
  spinner.style.display = "inline-block";
  status.textContent = "Guardando configuración...";

  try {{
    const res = await fetch("/api/starter/activate", {{
      method: "POST",
      headers: {{ "Content-Type": "application/json" }},
      body: JSON.stringify({{
        user_id: USER_ID,
        tone: selectedTone,
        manual_approval: document.getElementById("manual-approval").checked,
        whatsapp_negative_alerts: document.getElementById("whatsapp-alerts").checked,
      }}),
    }});

    if (!res.ok) throw new Error(`HTTP ${{res.status}}`);
    status.textContent = "Cuenta activada. Abriendo dashboard...";
    setTimeout(() => {{
      window.location.href = `/starter/dashboard?user_id=${{USER_ID}}`;
    }}, 450);
  }} catch (e) {{
    status.textContent = "No pudimos guardar la configuración.";
    alert("Error al activar tu cuenta Starter: " + e.message);
    btn.disabled = false;
    spinner.style.display = "none";
  }}
}}

window.addEventListener("DOMContentLoaded", () => {{
  const initialCard = document.querySelector(`.tone-card[data-tone="${{DEFAULT_TONE}}"]`) || document.querySelector('.tone-card');
  if (initialCard) {{
    selectTone(initialCard);
  }}
}});
</script>
</body>
</html>
"""


def render_starter_loading_html(user_id: UUID, next_url: str) -> str:
  """Fast, Bootstrap-like loading screen for secure connection step."""
  return f"""
<!doctype html>
<html lang="es">
<head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Conexión segura | Lokigi</title>
    <style>
        :root {{
      --bs-primary: #0d6efd;
      --bs-primary-dark: #0a58ca;
      --bs-success: #198754;
      --bs-border: #dee2e6;
      --bs-text: #212529;
      --bs-muted: #6c757d;
        }}
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
      font-family: Arial, "Helvetica Neue", sans-serif;
      background: linear-gradient(180deg, #ffffff, #f4f7fb);
            min-height: 100vh;
            display: grid;
            place-items: center;
            padding: 24px;
        }}
        .container {{
      width: min(620px, 100%);
      background: #fff;
      border: 1px solid var(--bs-border);
      border-radius: 22px;
      box-shadow: 0 1rem 2rem rgba(33, 37, 41, 0.08);
      padding: 32px 28px;
    }}
    .eyebrow {{
      display: inline-block;
      padding: 7px 12px;
      border-radius: 999px;
      background: rgba(13, 110, 253, 0.08);
      color: var(--bs-primary-dark);
      border: 1px solid rgba(13, 110, 253, 0.16);
      font-size: 0.82rem;
      font-weight: 700;
      margin-bottom: 12px;
    }}
    h1 {{
      font-size: clamp(1.8rem, 4vw, 2.4rem);
      margin-bottom: 10px;
      line-height: 1.08;
    }}
    .lead {{
      font-size: 1rem;
      color: var(--bs-muted);
      margin-bottom: 26px;
      line-height: 1.55;
        }}
        .milestones {{
      display: grid;
      gap: 14px;
      margin: 22px 0 26px;
        }}
        .milestone {{
            display: flex;
            gap: 14px;
            opacity: 0.5;
            transition: all 0.4s ease;
      border: 1px solid var(--bs-border);
      border-radius: 16px;
      padding: 14px;
      background: #fff;
        }}
        .milestone.active {{
            opacity: 1;
      border-color: rgba(13, 110, 253, 0.28);
      box-shadow: 0 0 0 0.15rem rgba(13, 110, 253, 0.08);
        }}
        .milestone.completed {{
      opacity: 1;
        }}
        .milestone-icon {{
            flex: 0 0 40px;
            width: 40px;
            height: 40px;
            border-radius: 50%;
            background: #e9ecef;
            display: grid;
            place-items: center;
            font-size: 20px;
            font-weight: 700;
            color: var(--bs-muted);
            position: relative;
            transition: all 0.4s ease;
        }}
        .milestone.active .milestone-icon {{
            background: linear-gradient(135deg, var(--bs-primary), var(--bs-primary-dark));
            color: #fff;
            box-shadow: 0 0 20px rgba(13, 110, 253, 0.25);
            animation: pulse-icon 1.5s ease-in-out infinite;
        }}
        .milestone.completed .milestone-icon {{
            background: var(--bs-success);
            color: #fff;
            animation: none;
        }}
        @keyframes pulse-icon {{
            0%, 100% {{ transform: scale(1); }}
            50% {{ transform: scale(1.08); }}
        }}
        .milestone-content {{
            flex: 1;
            padding-top: 4px;
        }}
        .milestone-title {{
            font-size: 14px;
            font-weight: 700;
          color: var(--bs-text);
            margin-bottom: 2px;
        }}
        .milestone.active .milestone-title {{
          color: var(--bs-primary-dark);
        }}
        .milestone-desc {{
            font-size: 12px;
          color: var(--bs-muted);
            line-height: 1.4;
        }}
        .milestone-loader {{
            margin-top: 6px;
            display: flex;
            gap: 3px;
        }}
        .dot {{
            width: 4px;
            height: 4px;
            border-radius: 50%;
            background: var(--bs-primary);
            opacity: 0.3;
            animation: bounce 1.4s infinite;
        }}
        .dot:nth-child(2) {{ animation-delay: 0.2s; }}
        .dot:nth-child(3) {{ animation-delay: 0.4s; }}
        @keyframes bounce {{
            0%, 80%, 100% {{ opacity: 0.3; transform: translateY(0); }}
            40% {{ opacity: 1; transform: translateY(-6px); }}
        }}
        .milestone.completed .milestone-loader {{
            display: none;
        }}
        .progress-wrap {{
          margin: 24px 0 18px;
        }}
        .progress-label {{
            font-size: 11px;
            font-weight: 700;
            text-transform: uppercase;
          color: var(--bs-muted);
            margin-bottom: 8px;
            letter-spacing: 0.05em;
        }}
        .progress-bar {{
            width: 100%;
            height: 6px;
          background: #e9ecef;
            border-radius: 3px;
            overflow: hidden;
        }}
        .progress-fill {{
            height: 100%;
          background: linear-gradient(90deg, var(--bs-primary), var(--bs-success));
            border-radius: 3px;
            width: 0%;
            transition: width 0.6s ease;
        }}
        .footer {{
          display: flex;
          justify-content: space-between;
          gap: 14px;
          align-items: center;
          color: var(--bs-muted);
          font-size: 0.88rem;
        }}
        .scan-label {{
          font-weight: 700;
          color: var(--bs-primary-dark);
        }}
        @media (max-width: 640px) {{
          .footer {{
            flex-direction: column;
            align-items: flex-start;
          }}
        }}
    </style>
</head>
<body>
<div class="container">
      <div class="eyebrow">Paso 2 de 4 · Conexión segura</div>
      <h1>Escaneando tu perfil para dejar el dashboard listo</h1>
      <div class="lead">Lokigi ya obtuvo acceso a tu perfil de empresa. Ahora estamos validando la cuenta, leyendo historial reciente y preparando la experiencia inicial sin pasos técnicos extra.</div>

    <div class="milestones">
        <div class="milestone active" data-milestone="1">
            <div class="milestone-icon">🔐</div>
            <div class="milestone-content">
            <div class="milestone-title">Validando permisos de Google</div>
            <div class="milestone-desc">Comprobamos acceso para ver y administrar tus perfiles de empresa.</div>
                <div class="milestone-loader">
                    <div class="dot"></div>
                    <div class="dot"></div>
                    <div class="dot"></div>
                </div>
            </div>
        </div>

        <div class="milestone" data-milestone="2">
            <div class="milestone-icon">📚</div>
            <div class="milestone-content">
            <div class="milestone-title">Escaneando historial del perfil</div>
            <div class="milestone-desc">Buscamos reseñas reales para mostrarte valor inmediato en el siguiente paso.</div>
                <div class="milestone-loader">
                    <div class="dot"></div>
                    <div class="dot"></div>
                    <div class="dot"></div>
                </div>
            </div>
        </div>

        <div class="milestone" data-milestone="3">
            <div class="milestone-icon">🧠</div>
            <div class="milestone-content">
            <div class="milestone-title">Preparando el modo piloto</div>
            <div class="milestone-desc">Dejamos lista la experiencia para que elijas tono y actives tu cuenta Starter.</div>
                <div class="milestone-loader">
                    <div class="dot"></div>
                    <div class="dot"></div>
                    <div class="dot"></div>
                </div>
            </div>
        </div>
    </div>

    <div class="progress-wrap">
        <div class="progress-label">Progreso</div>
        <div class="progress-bar">
            <div class="progress-fill" id="progressFill"></div>
        </div>
    </div>

    <div class="footer">
      <div>
        <div class="scan-label">Escaneo activo</div>
        <div>Sin spinners vacíos: este paso comunica progreso real y reduce incertidumbre durante el onboarding.</div>
      </div>
      <div>Redirigiendo automáticamente...</div>
    </div>
</div>

<script>
(function() {{
    const NEXT_URL = {json.dumps(next_url)};
    const DURATIONS = [1400, 1500, 1300];
    const TOTAL_DURATION = DURATIONS.reduce((a, b) => a + b, 0);
    let elapsedTime = 0;

    function updateMilestones() {{
        let timeAccum = 0;
        for (let i = 1; i <= 3; i++) {{
            const el = document.querySelector(`[data-milestone="${{i}}"]`);
            const nextTime = timeAccum + DURATIONS[i - 1];

            if (elapsedTime >= nextTime) {{
                // Completed
                el.classList.remove('active');
                el.classList.add('completed');
            }} else if (elapsedTime >= timeAccum) {{
                // Currently active
                el.classList.add('active');
                el.classList.remove('completed');
            }} else {{
                // Not reached yet
                el.classList.remove('active', 'completed');
            }}

            timeAccum = nextTime;
        }}
    }}

    function updateProgress() {{
        const percent = Math.min((elapsedTime / TOTAL_DURATION) * 100, 100);
        document.getElementById('progressFill').style.width = percent + '%';
    }}

    function animate() {{
        updateMilestones();
        updateProgress();

        if (elapsedTime >= TOTAL_DURATION) {{
          window.location.href = NEXT_URL;
            return;
        }}

        elapsedTime += 50;
        setTimeout(animate, 50);
    }}

    animate();
}})();
</script>
</body>
</html>
"""


def render_starter_onboarding_html(user_id: UUID, location_id: str, connect_url: str) -> str:
  detected_business = _esc(location_id or "Google Business Profile")
  return f"""
<!doctype html>
<html lang=\"es\">
    <head>
        <meta charset=\"utf-8\" />
        <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
    <title>Onboarding Starter | Lokigi</title>
        <style>
            :root {{
        --bs-primary: #0d6efd;
        --bs-primary-dark: #0a58ca;
        --bs-info-bg: rgba(13, 202, 240, 0.12);
        --bs-body: #f4f7fb;
        --bs-card: #ffffff;
        --bs-text: #212529;
        --bs-muted: #6c757d;
        --bs-border: #dee2e6;
            }}
            * {{ box-sizing: border-box; }}
            body {{
                margin: 0;
        font-family: Arial, "Helvetica Neue", sans-serif;
        color: var(--bs-text);
                background:
          radial-gradient(circle at top left, rgba(13, 110, 253, 0.12) 0%, transparent 32%),
          linear-gradient(180deg, #ffffff, var(--bs-body));
                min-height: 100vh;
                padding: 24px;
            }}
      .container {{ max-width: 1080px; margin: 0 auto; }}
      .shell {{ background: var(--bs-card); border: 1px solid var(--bs-border); border-radius: 24px; box-shadow: 0 1rem 2rem rgba(33, 37, 41, 0.08); overflow: hidden; }}
      .row {{ display: grid; grid-template-columns: 1.1fr 0.9fr; gap: 0; }}
      .hero, .aside {{ padding: 32px 30px; }}
      .hero {{ background: linear-gradient(135deg, #ffffff, #eef5ff); }}
      .pill {{
        display: inline-block;
        background: var(--bs-info-bg);
        color: var(--bs-primary-dark);
        border: 1px solid rgba(13, 110, 253, 0.16);
        border-radius: 999px;
        font-size: 12px;
        font-weight: 700;
        letter-spacing: 0.04em;
        padding: 6px 10px;
            }}
            h1 {{
                margin: 14px 0 12px;
                line-height: 1.1;
                font-size: clamp(30px, 5vw, 44px);
            }}
      p {{ margin: 0 0 12px; color: var(--bs-muted); font-size: 16px; line-height: 1.55; }}
      .location-box {{ margin-top: 18px; border: 1px solid var(--bs-border); border-radius: 16px; padding: 18px; background: #fff; }}
      .location-kicker {{ font-size: 12px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.04em; color: var(--bs-primary-dark); margin-bottom: 8px; }}
      .location-title {{ font-size: 22px; font-weight: 700; margin-bottom: 6px; }}
      .location-meta {{ font-size: 14px; color: var(--bs-muted); }}
            .cta {{
                margin-top: 20px;
                display: inline-flex;
                align-items: center;
                justify-content: center;
                width: 100%;
                padding: 14px 18px;
                border-radius: 12px;
                border: 0;
                text-decoration: none;
                background: linear-gradient(135deg, var(--bs-primary), var(--bs-primary-dark));
                font-size: 16px;
              .hint {{ margin-top: 10px; font-size: 12px; color: var(--bs-muted); }}
              .step-list {{ list-style: none; margin: 0; padding: 0; display: grid; gap: 12px; }}
              .step-item {{ border: 1px solid var(--bs-border); border-radius: 16px; padding: 14px 16px; background: #fff; }}
              .step-item strong {{ display: block; margin-bottom: 4px; }}
              .step-item span {{ color: var(--bs-muted); font-size: 14px; line-height: 1.45; }}
              .aside-title {{ font-size: 20px; margin-bottom: 12px; }}
              .note {{ margin-top: 16px; padding: 14px 16px; border-radius: 14px; border: 1px dashed rgba(13, 110, 253, 0.24); color: var(--bs-muted); background: rgba(13, 110, 253, 0.04); font-size: 14px; }}
              @media (max-width: 860px) {{ .row {{ grid-template-columns: 1fr; }} }}
                background: linear-gradient(135deg, var(--accent), var(--accent-2));
            }}
            .hint {{ margin-top: 10px; font-size: 12px; color: #6b7280; }}
            <main class="container">
              <section class="shell">
                <div class="row">
                  <div class="hero">
                    <span class="pill">Onboarding Starter · Paso 1 de 4</span>
                    <h1>¿Cuál es el negocio que vamos a potenciar hoy?</h1>
                    <p>Ingresa con Google y deja que Lokigi detecte tus perfiles asociados. El objetivo es llevarte del mapa al dashboard con el menor roce técnico posible.</p>
                    <div class="location-box">
                      <div class="location-kicker">Negocio objetivo</div>
                      <div class="location-title">{detected_business}</div>
                      <div class="location-meta">Si tu cuenta tiene más de un perfil, Google te llevará al flujo seguro para validar la ubicación correcta.</div>
                    </div>
                    <a class="cta" href="{connect_url}">Entrar con Google y continuar</a>
                    <div class="hint">Usamos permisos oficiales para ver y administrar tus perfiles de empresa. Nada de instalaciones ni pasos técnicos extra.</div>
                  </div>
                  <aside class="aside">
                    <div class="aside-title">Del mapa al dashboard en 3 minutos</div>
                    <ul class="step-list">
                      <li class="step-item"><strong>1. Registro y selección</strong><span>Social login con Google y detección del negocio a potenciar hoy.</span></li>
                      <li class="step-item"><strong>2. Conexión segura</strong><span>Validamos permisos y mostramos una barra tipo “escaneando” mientras se prepara el perfil.</span></li>
                      <li class="step-item"><strong>3. Voz de marca</strong><span>Eliges entre Cercano, Formal o Moderno y ves una respuesta real antes de activar.</span></li>
                      <li class="step-item"><strong>4. Modo piloto</strong><span>Enciendes aprobación manual y alertas tempranas para empezar con seguridad.</span></li>
                    </ul>
                    <div class="note">Carga rápida, HTML directo desde FastAPI y estilo tipo Bootstrap. Sin React, sin bundle, sin demoras innecesarias.</div>
                  </aside>
                </div>
              </section>
            </main>
            <a class=\"cta\" href=\"{connect_url}\">Conectar Google Maps</a>
            <div class=\"hint\">Click 1: conectar · Click 2: autorizar en Google · Click 3: dashboard listo</div>
        </main>
    </body>
</html>
"""


def render_starter_dashboard_html(
    user_id: UUID,
    connection: GoogleConnection | None,
    recent_reviews: list[Review],
    pending_reviews: list[Review],
    replies_sent_month: int,
    minutes_saved_month: int,
    current_avg_rating: float | None,
    trend_direction: str,
    trend_delta: float,
    days_to_report_close: int,
    response_velocity: dict[str, Any],
    sentiment_snapshot: dict[str, Any],
    keyword_concepts: list[dict[str, Any]],
    starter_tip: dict[str, Any],
    report_history: list[dict[str, Any]],
    optimization_center_html: str,
) -> str:
    status_text = "Conectado" if connection else "Sin conectar"
    status_color = "#0f766e" if connection else "#b91c1c"
    subtitle = (
        f"Cuenta: {connection.business_name or connection.google_account_name}"
        if connection
        else "Conecta Google Maps para empezar a recibir reseñas."
    )

    business_name = _esc(connection.business_name or connection.google_account_name) if connection else "Sin negocio conectado"
    current_tone = _tone_label(connection.preferred_tone if connection else "cercano")
    tone_class = _tone_badge_class(connection.preferred_tone if connection else "cercano")
    has_optimization_alert = bool((optimization_center_html or "").strip())

    hours_saved = round(minutes_saved_month / 60, 1)
    hero_time_text = f"{hours_saved} h" if minutes_saved_month >= 60 else f"{minutes_saved_month} min"

    trend_symbol = "↗"
    trend_color = "#047857"
    trend_copy = "al alza"
    if trend_direction == "down":
        trend_symbol = "↘"
        trend_color = "#b91c1c"
        trend_copy = "a la baja"
    elif trend_direction == "flat":
        trend_symbol = "→"
        trend_color = "#475569"
        trend_copy = "estable"

    avg_rating_text = f"{current_avg_rating:.1f}★" if current_avg_rating is not None else "—"
    trend_delta_text = f"{abs(trend_delta):.1f}" if trend_delta else "0.0"

    pending_html = "".join(
        f"""
        <li class=\"pending-item\">
          <div class=\"pending-top\">
            <strong>{_esc(r.author_display_name or 'Cliente')}</strong>
            <span class=\"stars\">{(r.rating or 0)}★</span>
          </div>
          <p class=\"pending-review\">{_esc((r.comment or 'Sin comentario.')[:120])}</p>
          <p class=\"pending-reply\">IA: {_esc((r.reply_public_text or '')[:140])}</p>
        </li>
        """
        for r in pending_reviews[:4]
    )
    if not pending_html:
        pending_html = '<li class="empty">No hay respuestas pendientes por aprobar.</li>'

    recent_reviews_html = "".join(
        f"""
        <li class=\"review-item\">
            <div class=\"review-top\">
              <strong>{_esc(review.author_display_name or 'Cliente')}</strong>
              <span>{review.rating or 0}★</span>
            </div>
            <p>{_esc((review.comment or 'Sin comentario.')[:220])}</p>
        </li>
        """
        for review in recent_reviews
    )
    if not recent_reviews_html:
        recent_reviews_html = '<li class="empty">Todavía no hay reseñas recibidas.</li>'

    velocity_current = _format_minutes_compact(response_velocity.get("current_avg_minutes"))
    velocity_baseline = _format_minutes_compact(response_velocity.get("baseline_avg_minutes"))
    velocity_improvement = (
      f"{response_velocity.get('improvement_pct', 0):.1f}%"
      if response_velocity.get("improvement_pct") is not None
      else "—"
    )
    velocity_note = (
      "Comparado contra historial real previo en Google."
      if response_velocity.get("baseline_source") == "google_history"
      else "Comparado contra referencia de 24 h por falta de historial previo usable."
    )

    snapshot_counts = sentiment_snapshot.get("counts") or [0, 0, 0]
    snapshot_percentages = sentiment_snapshot.get("percentages") or [0.0, 0.0, 0.0]
    sentiment_rows = [
      ("Positivas", snapshot_counts[0], snapshot_percentages[0], "#60a5fa"),
      ("Neutrales", snapshot_counts[1], snapshot_percentages[1], "#cbd5e1"),
      ("Negativas", snapshot_counts[2], snapshot_percentages[2], "#f87171"),
    ]
    sentiment_html = "".join(
      f"""
      <div class=\"sentiment-row\">
        <div class=\"sentiment-label\">{label}<span>{count}</span></div>
        <div class=\"sentiment-bar\"><span style=\"width:{pct}%; background:{color};\"></span></div>
      </div>
      """
      for label, count, pct, color in sentiment_rows
    )

    keyword_html = "".join(
      f'<span class="keyword-chip">{_esc(item.get("concept", ""))} · {item.get("count", 0)}</span>'
      for item in keyword_concepts[:5]
    )
    if not keyword_html:
      keyword_html = '<span class="empty">Todavía no hay conceptos suficientes este mes.</span>'

    month_names_es = {
      1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril",
      5: "Mayo", 6: "Junio", 7: "Julio", 8: "Agosto",
      9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre",
    }
    history_items_html = ""
    for item in report_history:
      month_value = int(item.get("month") or 0)
      year_value = int(item.get("year") or 0)
      month_name = month_names_es.get(month_value, str(month_value))
      period_label = f"{month_name} {year_value}"
      view_url = f"/starter/report?user_id={user_id}&year={year_value}&month={month_value}"

      status = str(item.get("pdf_status") or "pending")
      pdf_url = item.get("pdf_signed_url")
      if status == "ready" and isinstance(pdf_url, str) and pdf_url:
        pdf_button_html = f'<a href="{_esc(pdf_url)}" target="_blank" rel="noreferrer" class="btn btn-download">Descargar PDF</a>'
      elif status == "failed":
        pdf_button_html = '<button type="button" class="btn btn-disabled" disabled>No disponible</button>'
      elif status == "processing":
        pdf_button_html = '<button type="button" class="btn btn-disabled" disabled>Generando PDF</button>'
      else:
        pdf_button_html = '<button type="button" class="btn btn-disabled" disabled>PDF pendiente</button>'

      history_items_html += f"""
      <li class=\"history-item\">
        <div>
          <div class=\"history-period\">{period_label}</div>
          <div class=\"history-meta\">Estado PDF: {_esc(status)}</div>
        </div>
        <div class=\"history-actions\">
          <a href=\"{view_url}\" class=\"btn\" target=\"_blank\" rel=\"noreferrer\">Ver Online</a>
          {pdf_button_html}
        </div>
      </li>
      """
    if not history_items_html:
      history_items_html = '<li class="empty">Aún no hay reportes mensuales generados.</li>'

    report_days_copy = (
        "Hoy cierra el reporte mensual."
        if days_to_report_close == 0
        else f"Faltan {days_to_report_close} día{'s' if days_to_report_close != 1 else ''} para el cierre del reporte mensual."
    )

    tip_text = _esc(starter_tip.get("tip_del_dia") or "Activa más reseñas recientes para desbloquear recomendaciones más precisas.")
    tip_focus = _esc(str(starter_tip.get("focus") or "other").replace("_", " "))
    tip_source = _esc(starter_tip.get("source") or "fallback")
    tip_tone = _esc(starter_tip.get("tone") or "opportunity")
    tip_confidence = starter_tip.get("confidence")
    tip_confidence_copy = f"{float(tip_confidence) * 100:.0f}%" if tip_confidence is not None else "—"
    tip_evidence = int(starter_tip.get("evidence_count") or 0)
    tip_fallback = bool(starter_tip.get("is_fallback"))

    tip_signals = starter_tip.get("supporting_signals") or []
    tip_signals_html = "".join(
      f'<li>{_esc(str(signal))}</li>' for signal in tip_signals[:3] if str(signal).strip()
    )
    if not tip_signals_html:
      tip_signals_html = '<li>Sin señales textuales fuertes en el último lote de reseñas.</li>'

    tip_badge = "Tip con fallback" if tip_fallback else "Tip context-aware"
    tip_badge_class = "tip-badge fallback" if tip_fallback else "tip-badge"

    return f"""
<!doctype html>
<html lang=\"es\">
  <head>
    <meta charset=\"utf-8\" />
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
    <title>Dashboard Starter | Lokigi</title>
    <script src="https://unpkg.com/htmx.org@1.9.12"></script>
    <style>
      :root {{
        --bg: #eff3f8;
        --card: #ffffff;
        --text: #0f172a;
        --muted: #64748b;
        --border: #dbe3ee;
        --primary: #0f62fe;
        --primary-dark: #0b4fd4;
      }}
      * {{ box-sizing: border-box; }}
      body {{
        margin: 0;
        font-family: Arial, "Helvetica Neue", sans-serif;
        color: var(--text);
        background:
          radial-gradient(circle at 10% 0%, rgba(15, 98, 254, 0.15), transparent 32%),
          linear-gradient(180deg, #ffffff, var(--bg));
      }}
      .wrap {{ max-width: 1100px; margin: 0 auto; padding: 18px; }}
      .topbar {{
        background: var(--card);
        border: 1px solid var(--border);
        border-radius: 16px;
        padding: 14px 18px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        gap: 10px;
      }}
      .status {{ display: inline-flex; align-items: center; gap: 8px; padding: 6px 12px; border-radius: 999px; font-size: 12px; font-weight: 700; color: #fff; background: {status_color}; }}
      .subtitle {{ color: var(--muted); font-size: 14px; margin-top: 5px; }}
      html {{ scroll-behavior: smooth; }}
      .hero {{
        margin-top: 14px;
        background: linear-gradient(135deg, #0f62fe, #0b4fd4);
        color: #fff;
        border-radius: 18px;
        padding: 24px;
        box-shadow: 0 14px 30px rgba(15, 98, 254, 0.28);
      }}
      .hero-kicker {{ font-size: 12px; text-transform: uppercase; letter-spacing: 0.05em; opacity: 0.85; font-weight: 700; }}
      .hero-grid {{ display: grid; grid-template-columns: 1.2fr 0.8fr; gap: 16px; align-items: end; margin-top: 10px; }}
      .hero h1 {{ margin: 0; font-size: clamp(30px, 5vw, 50px); line-height: 1; }}
      .hero p {{ margin: 8px 0 0; opacity: 0.95; }}
      .hero-mini {{ background: rgba(255,255,255,0.12); border: 1px solid rgba(255,255,255,0.22); border-radius: 14px; padding: 12px; }}
      .hero-mini strong {{ font-size: 22px; display: block; }}

      .grid {{ display: grid; grid-template-columns: 0.95fr 1.05fr; gap: 14px; margin-top: 14px; }}
      .card {{ background: var(--card); border: 1px solid var(--border); border-radius: 16px; padding: 16px; }}
      .card h2 {{ margin: 0 0 10px; font-size: 18px; }}
      .muted {{ color: var(--muted); }}

      .rep-score {{ font-size: 40px; font-weight: 800; margin: 2px 0; }}
      .rep-trend {{ font-weight: 700; color: {trend_color}; display: inline-flex; gap: 8px; align-items: center; }}

      .value-grid {{ display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 14px; margin-top: 14px; }}
      .value-card {{ background: linear-gradient(180deg, #ffffff, #f8fbff); border: 1px solid var(--border); border-radius: 16px; padding: 16px; }}
      .value-title {{ font-size: 12px; text-transform: uppercase; color: var(--muted); font-weight: 700; letter-spacing: .04em; margin-bottom: 10px; }}
      .velocity-grid {{ display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 8px; }}
      .velocity-stat {{ background: #fff; border: 1px solid var(--border); border-radius: 12px; padding: 10px; }}
      .velocity-stat strong {{ display: block; font-size: 20px; line-height: 1; margin-bottom: 4px; }}
      .velocity-stat span {{ color: var(--muted); font-size: 12px; }}
      .value-footnote {{ color: var(--muted); font-size: 12px; line-height: 1.45; margin-top: 10px; }}
      .sentiment-row {{ margin-bottom: 10px; }}
      .sentiment-label {{ display:flex; justify-content:space-between; font-size: 13px; margin-bottom: 5px; color: #334155; }}
      .sentiment-bar {{ height: 10px; background: #e5e7eb; border-radius: 999px; overflow:hidden; }}
      .sentiment-bar span {{ display:block; height:100%; border-radius: 999px; }}
      .keyword-cloud {{ display:flex; flex-wrap:wrap; gap:8px; }}
      .keyword-chip {{ display:inline-flex; align-items:center; padding:7px 12px; border-radius:999px; background:#eef5ff; color:#1d4ed8; font-size:13px; font-weight:700; }}

      .tip-card {{ margin-top: 14px; border: 1px solid #bfdbfe; background: linear-gradient(180deg, #f8fbff, #eef5ff); }}
      .hub-tabs {{ display:flex; gap:10px; flex-wrap:wrap; margin-top:14px; }}
      .hub-tab {{ display:inline-flex; align-items:center; gap:8px; padding:10px 14px; border-radius:999px; border:1px solid var(--border); background:#fff; color:#0f172a; text-decoration:none; font-weight:700; font-size:14px; }}
      .hub-tab.active {{ border-color:#bfdbfe; background:#eff6ff; color:#0f62fe; }}
      .hub-tab-dot {{ width:9px; height:9px; border-radius:999px; background:#ef4444; box-shadow:0 0 0 4px rgba(239, 68, 68, 0.14); }}
      .optimization-section {{ scroll-margin-top: 18px; min-height: 1px; }}
      .tip-header {{ display: flex; justify-content: space-between; gap: 10px; align-items: center; flex-wrap: wrap; margin-bottom: 10px; }}
      .tip-badge {{ display: inline-flex; border-radius: 999px; padding: 6px 10px; font-size: 12px; font-weight: 700; color: #0f62fe; background: rgba(15, 98, 254, 0.12); }}
      .tip-badge.fallback {{ color: #b45309; background: rgba(245, 158, 11, 0.22); }}
      .tip-main {{ font-size: 16px; line-height: 1.45; color: #0f172a; margin: 0 0 10px; }}
      .tip-meta {{ display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 10px; }}
      .tip-chip {{ display: inline-flex; border-radius: 999px; padding: 6px 10px; border: 1px solid #dbe3ee; background: #fff; font-size: 12px; color: #334155; }}
      .tip-signals {{ margin: 0; padding-left: 18px; color: #475569; font-size: 13px; line-height: 1.45; }}

      .optimization-card {{ margin-top: 14px; border: 1px solid #bfdbfe; background: linear-gradient(180deg, #ffffff, #f8fbff); }}
      .optimization-head {{ display:flex; justify-content:space-between; gap:12px; align-items:flex-start; flex-wrap:wrap; }}
      .optimization-kicker {{ font-size: 12px; text-transform: uppercase; letter-spacing: .05em; color: #0f62fe; font-weight: 700; margin-bottom: 6px; }}
      .optimization-priority {{ display:inline-flex; align-items:center; border-radius:999px; padding:8px 12px; background:#e0ecff; color:#0f62fe; font-size:12px; font-weight:700; }}
      .optimization-explainer {{ margin-top: 12px; border:1px solid #dbeafe; border-radius:12px; padding:12px; background:#eff6ff; }}
      .optimization-explainer p {{ margin:6px 0 0; color:#334155; line-height:1.5; }}
      .optimization-metrics {{ display:grid; grid-template-columns:repeat(3, minmax(0,1fr)); gap:10px; margin-top:12px; }}
      .optimization-metric {{ border:1px solid var(--border); border-radius:12px; padding:10px 12px; background:#fff; }}
      .optimization-metric span {{ display:block; color:var(--muted); font-size:12px; text-transform:uppercase; letter-spacing:.04em; margin-bottom:6px; }}
      .optimization-metric strong {{ font-size:16px; }}
      .optimization-compare {{ display:grid; grid-template-columns:1fr 1fr; gap:12px; margin-top:12px; }}
      .optimization-pane {{ border-radius:14px; padding:14px; border:1px solid var(--border); }}
      .optimization-pane.before {{ background:#fff; }}
      .optimization-pane.after {{ background:linear-gradient(180deg, #eef5ff, #ffffff); border-color:#bfdbfe; }}
      .optimization-label {{ display:inline-flex; margin-bottom:8px; border-radius:999px; padding:5px 9px; background:#e2e8f0; color:#334155; font-size:11px; text-transform:uppercase; font-weight:700; letter-spacing:.05em; }}
      .optimization-text {{ color:#0f172a; line-height:1.6; font-size:14px; }}
      .optimization-text mark {{ background:#fde68a; color:#713f12; padding:0 3px; border-radius:4px; }}
      .optimization-notice {{ margin-top:12px; border-radius:12px; padding:10px 12px; border:1px solid #cbd5e1; background:#fff; color:#334155; }}
      .optimization-notice.ok {{ border-color:#86efac; background:#ecfdf5; color:#166534; }}
      .optimization-notice.error {{ border-color:#fecaca; background:#fef2f2; color:#991b1b; }}
      .optimization-modal-backdrop {{ position:fixed; inset:0; background:rgba(15, 23, 42, .48); display:flex; align-items:center; justify-content:center; padding:18px; z-index:50; animation: optimization-fade-in .18s ease-out; }}
      .optimization-modal {{ width:min(520px, 100%); background:#fff; border:1px solid #dbeafe; border-radius:18px; padding:20px; box-shadow:0 24px 60px rgba(15, 23, 42, .22); animation: optimization-modal-in .22s cubic-bezier(.2,.8,.2,1); transform-origin:center; }}
      .optimization-modal h3 {{ margin:6px 0 10px; font-size:24px; }}
      .optimization-modal p {{ margin:0; color:#475569; line-height:1.6; }}
      .optimization-modal-kicker {{ font-size:12px; text-transform:uppercase; letter-spacing:.05em; color:#0f62fe; font-weight:700; }}
      .optimization-success {{ margin-top:14px; border:1px solid #86efac; background:linear-gradient(180deg, #ecfdf5, #ffffff); text-align:center; animation: optimization-success-in .28s cubic-bezier(.16,1,.3,1); }}
      .optimization-success h2 {{ margin:10px 0 8px; font-size:30px; }}
      .optimization-success p {{ margin:0 auto; max-width:620px; color:#166534; line-height:1.6; }}
      .optimization-success-icon {{ width:64px; height:64px; border-radius:999px; margin:0 auto; display:flex; align-items:center; justify-content:center; background:#16a34a; color:#fff; font-size:18px; font-weight:800; letter-spacing:.05em; }}
      .htmx-swapping#optimization-center {{ opacity:0; transform:translateY(8px) scale(.985); transition:opacity .2s ease, transform .2s ease; }}
      @keyframes optimization-fade-in {{ from {{ opacity:0; }} to {{ opacity:1; }} }}
      @keyframes optimization-modal-in {{ from {{ opacity:0; transform:translateY(16px) scale(.96); }} to {{ opacity:1; transform:translateY(0) scale(1); }} }}
      @keyframes optimization-success-in {{ from {{ opacity:0; transform:translateY(12px) scale(.98); }} to {{ opacity:1; transform:translateY(0) scale(1); }} }}

      .pending-list, .reviews {{ list-style: none; margin: 0; padding: 0; display: grid; gap: 10px; }}
      .pending-item, .review-item {{ border: 1px solid var(--border); border-radius: 12px; padding: 10px 12px; background: #fbfcff; }}
      .pending-top, .review-top {{ display: flex; align-items: center; justify-content: space-between; margin-bottom: 5px; }}
      .pending-review, .pending-reply, .review-item p {{ margin: 0; font-size: 13px; color: #334155; line-height: 1.45; }}
      .pending-reply {{ color: #475569; margin-top: 4px; }}
      .stars {{ color: #a16207; font-weight: 700; }}
      .empty {{ border: 1px dashed #cbd5e1; border-radius: 12px; padding: 12px; color: var(--muted); }}

      .history-list {{ list-style: none; margin: 0; padding: 0; display: grid; gap: 10px; }}
      .history-item {{ border: 1px solid var(--border); border-radius: 12px; padding: 11px 12px; display: flex; justify-content: space-between; align-items: center; gap: 10px; background: #fbfcff; }}
      .history-period {{ font-size: 14px; font-weight: 700; color: #0f172a; }}
      .history-meta {{ font-size: 12px; color: var(--muted); margin-top: 4px; }}
      .history-actions {{ display: flex; gap: 8px; flex-wrap: wrap; }}
      .btn-download {{ background: var(--primary); border-color: var(--primary); color: #fff; }}
      .btn-download:hover {{ background: var(--primary-dark); }}
      .btn-disabled {{ color: #94a3b8; background: #f8fafc; border-color: #e2e8f0; cursor: not-allowed; }}

      .banner {{
        margin-top: 14px;
        background: linear-gradient(135deg, #fff7db, #fff1c4);
        border: 1px solid #f8d36d;
        border-radius: 14px;
        padding: 12px 14px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        gap: 12px;
      }}
      .banner strong {{ color: #92400e; }}

      .cta-row {{ display: flex; gap: 10px; flex-wrap: wrap; margin-top: 12px; }}
      .btn {{ display: inline-flex; align-items: center; justify-content: center; text-decoration: none; padding: 10px 14px; border-radius: 10px; border: 1px solid var(--border); background: #fff; color: var(--text); font-weight: 700; font-size: 14px; }}
      .btn.primary {{ background: var(--primary); border-color: var(--primary); color: #fff; }}
      .btn.primary:hover {{ background: var(--primary-dark); }}
      .tone-pill {{ display: inline-flex; align-items: center; border-radius: 999px; padding: 6px 10px; font-size: 12px; font-weight: 700; }}
      .tone-cercano {{ background: rgba(25, 135, 84, 0.12); color: #146c43; }}
      .tone-formal {{ background: rgba(13, 110, 253, 0.12); color: #0a58ca; }}
      .tone-moderno {{ background: rgba(255, 193, 7, 0.24); color: #92400e; }}

      @media (max-width: 900px) {{ .hero-grid, .grid, .value-grid, .optimization-compare, .optimization-metrics {{ grid-template-columns: 1fr; }} .velocity-grid {{ grid-template-columns: 1fr; }} }}
    </style>
  </head>
  <body>
    <div class=\"wrap\">
      <section class=\"topbar\">
        <div>
          <span class=\"status\">{status_text}</span>
          <div class=\"subtitle\">{subtitle}</div>
        </div>
        <div class=\"tone-pill {tone_class}\">Voz activa: {current_tone}</div>
      </section>

      <section class=\"hero\">
        <div class=\"hero-kicker\">Valor generado por IA este mes</div>
        <div class=\"hero-grid\">
          <div>
            <h1>{hero_time_text}</h1>
            <p>Tiempo ahorrado estimado (respuestas publicadas × 4 min).</p>
          </div>
          <div class=\"hero-mini\">
            <span class=\"muted\" style=\"color:#dbeafe\">Respuestas enviadas</span>
            <strong>{replies_sent_month}</strong>
            <span class=\"muted\" style=\"color:#dbeafe\">{business_name}</span>
          </div>
        </div>
      </section>

      <nav class=\"hub-tabs\" aria-label=\"Secciones del dashboard\">
        <a class=\"hub-tab\" href=\"#resumen\">Resumen</a>
        {render_optimization_hub_tab_html(has_optimization_alert)}
        <a class=\"hub-tab\" href=\"#reviews-section\">Reseñas</a>
      </nav>

      <section class=\"grid\" id=\"resumen\">
        <article class=\"card\">
          <h2>Reputación en Google Maps</h2>
          <div class=\"rep-score\">{avg_rating_text}</div>
          <div class=\"rep-trend\">{trend_symbol} {trend_copy} ({trend_delta_text})</div>
          <p class=\"muted\" style=\"margin-top:8px\">Comparativa contra el promedio del mes anterior.</p>
        </article>

        <article class=\"card\">
          <h2>Pendientes de aprobación</h2>
          <p class=\"muted\" style=\"margin:0 0 10px; font-size:13px\">La IA ya redactó respuesta. Solo falta un clic para publicar.</p>
          <ul class=\"pending-list\">{pending_html}</ul>
          <div class=\"cta-row\">
            <a href=\"/starter/approvals?user_id={user_id}\" class=\"btn primary\">Publicar pendientes</a>
          </div>
        </article>
      </section>

      <section class=\"banner\">
        <div>
          <strong>Próximo reporte mensual</strong>
          <div class=\"muted\" style=\"font-size:13px\">{report_days_copy}</div>
        </div>
        <a href=\"/starter/report?user_id={user_id}&year={datetime.utcnow().year}&month={datetime.utcnow().month}\" class=\"btn\">Ver reporte</a>
      </section>

      <section class=\"card tip-card\">
        <div class=\"tip-header\">
          <h2 style=\"margin:0\">Tip del Día</h2>
          <span class=\"{tip_badge_class}\">{tip_badge}</span>
        </div>
        <p class=\"tip-main\">{tip_text}</p>
        <div class=\"tip-meta\">
          <span class=\"tip-chip\">Foco: {tip_focus}</span>
          <span class=\"tip-chip\">Confianza: {tip_confidence_copy}</span>
          <span class=\"tip-chip\">Evidencia: {tip_evidence}/10</span>
          <span class=\"tip-chip\">Fuente: {tip_source}</span>
          <span class=\"tip-chip\">Tono: {tip_tone}</span>
        </div>
        <ul class=\"tip-signals\">{tip_signals_html}</ul>
      </section>

      <section class=\"optimization-section\" id=\"optimization-section\">{optimization_center_html}</section>

      <section class=\"value-grid\">
        <article class=\"value-card\">
          <div class=\"value-title\">Response Velocity</div>
          <div class=\"velocity-grid\">
            <div class=\"velocity-stat\"><strong>{velocity_current}</strong><span>Lokigi</span></div>
            <div class=\"velocity-stat\"><strong>{velocity_baseline}</strong><span>Antes</span></div>
            <div class=\"velocity-stat\"><strong>{velocity_improvement}</strong><span>Mejora</span></div>
          </div>
          <div class=\"value-footnote\">{velocity_note}</div>
        </article>
        <article class=\"value-card\">
          <div class=\"value-title\">Sentiment Snapshot</div>
          {sentiment_html}
        </article>
        <article class=\"value-card\">
          <div class=\"value-title\">Keyword Cloud</div>
          <div class=\"keyword-cloud\">{keyword_html}</div>
        </article>
      </section>

      <section class=\"card\" style=\"margin-top:14px\" id=\"reviews-section\">
        <h2>Últimas reseñas</h2>
        <ul class=\"reviews\">{recent_reviews_html}</ul>
        <div class=\"cta-row\">
          <a href=\"/starter/tone-selector?user_id={user_id}\" class=\"btn\">Ajustar voz de marca</a>
          <a href=\"/starter/profile?user_id={user_id}\" class=\"btn\">Configuración de perfil</a>
          <a href=\"/starter/subscription?user_id={user_id}\" class=\"btn\">Suscripción y facturas</a>
        </div>
      </section>

      <section class="card" style="margin-top:14px">
        <h2>Historial de Reportes</h2>
        <p class="muted" style="margin:0 0 10px; font-size:13px">Lista cronológica mensual con acceso al reporte online y al PDF.</p>
        <ul class="history-list">{history_items_html}</ul>
      </section>
    </div>
  </body>
</html>
"""


def _format_storefront_address(address_payload: dict[str, Any] | None) -> str:
    if not isinstance(address_payload, dict):
        return "No disponible"
    ordered_keys = [
        "addressLines",
        "locality",
        "administrativeArea",
        "postalCode",
        "regionCode",
    ]
    parts: list[str] = []
    for key in ordered_keys:
        value = address_payload.get(key)
        if isinstance(value, list):
            parts.extend([str(item).strip() for item in value if str(item).strip()])
        elif value:
            parts.append(str(value).strip())
    return ", ".join(parts) if parts else "No disponible"


def _remaining_auto_send_minutes(decided_at: datetime | None, response_schedule: str) -> int | None:
    """Return minutes until auto-send when schedule is delay_1h."""
    if response_schedule != "delay_1h" or decided_at is None:
        return None

    decided_naive = decided_at.astimezone(timezone.utc).replace(tzinfo=None) if decided_at.tzinfo else decided_at
    due_at = decided_naive + timedelta(hours=1)
    now = datetime.utcnow()
    delta = due_at - now
    remaining = int(delta.total_seconds() // 60)
    return max(0, remaining)


def _format_minutes_compact(value: float | None) -> str:
    if value is None:
        return "—"
    if value < 60:
        return f"{round(value)} min"
    if value < 1440:
        return f"{value / 60:.1f} h"
    return f"{value / 1440:.1f} d"


def render_subscription_cancel_choice_html(user_id: UUID) -> str:
    return f"""
    <div class=\"cancel-flow-backdrop\" onclick=\"if (event.target === this) document.getElementById('subscription-cancel-shell').innerHTML = '';\">
      <div class=\"cancel-flow-card\" role=\"dialog\" aria-modal=\"true\" aria-labelledby=\"cancel-flow-title\">
        <div class=\"cancel-flow-kicker\">Retención inteligente</div>
        <h2 id=\"cancel-flow-title\">¿Necesitas un respiro?</h2>
        <p class=\"cancel-flow-copy\">Antes de cancelar, te ofrecemos una pausa ligera para conservar el valor que ya construiste en Lokigi.</p>
        <section class=\"pause-offer\">
          <div class=\"pause-offer-badge\">Recomendada</div>
          <h3>Pausar mi cuenta</h3>
          <p>Mantendremos tus datos a salvo y tus reportes activos por solo $5/mes. Vuelve cuando quieras.</p>
          <button class=\"btn primary\" hx-post=\"/starter/subscription/cancel-flow/pause?user_id={user_id}\" hx-target=\"#subscription-cancel-shell\" hx-swap=\"innerHTML\">Pausar mi cuenta</button>
        </section>
        <div class=\"cancel-flow-actions\">
          <button class=\"btn\" type=\"button\" onclick=\"document.getElementById('subscription-cancel-shell').innerHTML = '';\">Seguir con mi plan</button>
          <button class=\"link-btn\" hx-get=\"/starter/subscription/cancel-flow/survey?user_id={user_id}\" hx-target=\"#subscription-cancel-shell\" hx-swap=\"innerHTML\">No, prefiero cancelar mi suscripción</button>
        </div>
      </div>
    </div>
    """


def render_subscription_cancel_survey_html(
  user_id: UUID,
  *,
  selected_reason: str | None = None,
  confirmed: bool = False,
) -> str:
  reason_copy = {
    "price": ("$", "Es caro"),
    "difficulty": ("Config", "Dificil de usar"),
    "business_closed": ("Cierre", "Cerre mi local"),
  }
  button_chunks: list[str] = []
  for key, (icon, label) in reason_copy.items():
    selected_class = " selected" if selected_reason == key else ""
    if confirmed:
      attrs = 'type="button" disabled'
    else:
      attrs = (
        f'type="button" '
        f'hx-post="/starter/subscription/cancel-flow/confirm?user_id={user_id}" '
        f'hx-vals=\'{{"churn_reason":"{key}"}}\' '
        'hx-target="#subscription-cancel-shell" '
        'hx-swap="innerHTML"'
      )
    button_chunks.append(
      f'''<button class="reason-btn{selected_class}" {attrs}><span class="reason-icon">{_esc(icon)}</span><span>{_esc(label)}</span></button>'''
    )
  buttons_html = "".join(button_chunks)

  selected_html = ""
  download_button_html = '<button class="btn primary" type="button" disabled>Generar y Descargar mi historial (.CSV)</button>'
  logout_button_html = '<button class="btn" type="button" disabled>Cerrar Sesion definitiva</button>'

  if confirmed and selected_reason in reason_copy:
    _, label = reason_copy[selected_reason]
    selected_html = f"""
    <div class="notice ok" style="margin-top:14px">Motivo registrado: <strong>{_esc(label)}</strong>. Ya puedes descargar tu CSV y cerrar la sesion definitiva cuando quieras.</div>
    """
    download_button_html = f'<a class="btn primary" href="/subscription/export-csv?user_id={user_id}">Generar y Descargar mi historial (.CSV)</a>'
    logout_button_html = '<a class="btn" href="/api/cancellation/logout">Cerrar Sesion definitiva</a>'

  return f"""
  <div class="cancel-flow-backdrop" onclick="if (event.target === this) document.getElementById('subscription-cancel-shell').innerHTML = '';">
    <div class="cancel-flow-card" role="dialog" aria-modal="true" aria-labelledby="cancel-survey-title">
      <div class="cancel-flow-kicker">Encuesta de salida</div>
      <h2 id="cancel-survey-title">Cuentanos por que te vas</h2>
      <p class="cancel-flow-copy">Cada motivo se registra via HTMX sin recargar la pagina. Despues habilitamos tu regalo y el cierre definitivo.</p>
      <div class="reason-grid">{buttons_html}</div>
      <section class="data-gift">
        <h3>Antes de irte, llevate tu historial</h3>
        <p>Hemos preparado un archivo con tus resenas y las respuestas que Lokigi genero para tu negocio. Primero registra el motivo y luego habilitamos la descarga.</p>
        <div class="cancel-confirm-form">{download_button_html}</div>
      </section>
      {selected_html}
      <div class="cancel-flow-actions">
        <button class="btn" hx-get="/starter/subscription/cancel-flow?user_id={user_id}" hx-target="#subscription-cancel-shell" hx-swap="innerHTML">Volver</button>
        {logout_button_html}
      </div>
    </div>
  </div>
  """


def render_subscription_pause_success_html(user_id: UUID, message: str) -> str:
  return f"""
  <div class="cancel-flow-backdrop" onclick="if (event.target === this) window.location.href = '/starter/subscription?user_id={user_id}';">
    <div class="cancel-flow-card" role="dialog" aria-modal="true" aria-labelledby="pause-success-title">
      <div class="cancel-flow-kicker">Cuenta pausada</div>
      <h2 id="pause-success-title">Tu Plan Pausa ya esta activo</h2>
      <p class="cancel-flow-copy">{_esc(message)}</p>
      <div class="notice ok">Tus datos, historico de IA y reportes siguen disponibles. Solo se suspende la automatizacion de respuestas.</div>
      <div class="cancel-flow-actions">
        <a class="btn primary" href="/starter/subscription?user_id={user_id}">Volver a Suscripcion</a>
      </div>
    </div>
  </div>
  """


def render_subscription_goodbye_html(*, business_name: str, csv_url: str, logout_url: str) -> str:
    safe_business_name = _esc(business_name)
    return f"""
<!doctype html>
<html lang=\"es\">
  <head>
    <meta charset=\"utf-8\" />
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
    <title>Hasta pronto | Lokigi</title>
    <style>
      body {{ margin:0; font-family:Arial, \"Helvetica Neue\", sans-serif; color:#0f172a; background:linear-gradient(180deg,#ffffff,#eef5ff); }}
      .farewell {{ max-width:760px; margin:0 auto; padding:42px 20px; }}
      .farewell-card {{ background:#fff; border:1px solid #dbe3ee; border-radius:24px; padding:30px; box-shadow:0 24px 60px rgba(15,23,42,.12); text-align:center; }}
      .farewell-kicker {{ display:inline-flex; padding:7px 12px; border-radius:999px; background:#ecfdf5; color:#166534; font-size:12px; font-weight:700; letter-spacing:.04em; text-transform:uppercase; }}
      h1 {{ margin:16px 0 10px; font-size:clamp(30px,5vw,44px); }}
      p {{ color:#475569; line-height:1.6; }}
      .download-note {{ margin-top:18px; padding:14px 16px; border-radius:16px; background:#eff6ff; border:1px solid #bfdbfe; color:#1e3a8a; }}
      .btn {{ display:inline-flex; align-items:center; justify-content:center; text-decoration:none; padding:12px 16px; border-radius:12px; border:1px solid #dbe3ee; background:#fff; color:#0f172a; font-weight:700; margin-top:18px; }}
      .btn.primary {{ background:#0f62fe; border-color:#0f62fe; color:#fff; }}
    </style>
  </head>
  <body>
    <main class=\"farewell\">
      <section class=\"farewell-card\">
        <div class=\"farewell-kicker\">Último paso</div>
        <h1>Gracias por todo, {safe_business_name}</h1>
        <p>En unos segundos descargaremos automáticamente tu historial en CSV y luego te llevaremos al landing page.</p>
        <div class=\"download-note\">El archivo incluye las reseñas gestionadas y las respuestas de IA que Lokigi preparó por ti.</div>
        <a class=\"btn primary\" href=\"{_esc(csv_url)}\">Descargar CSV ahora</a>
        <a class=\"btn\" href=\"{_esc(logout_url)}\">Ir al landing ahora</a>
      </section>
    </main>
    <script>
      (function () {{
        const csvUrl = {json.dumps(csv_url)};
        const logoutUrl = {json.dumps(logout_url)};
        const iframe = document.createElement('iframe');
        iframe.style.display = 'none';
        iframe.src = csvUrl;
        document.body.appendChild(iframe);
        window.setTimeout(function () {{
          window.location.href = logoutUrl;
        }}, 2200);
      }})();
    </script>
  </body>
</html>
"""


def render_starter_subscription_html(
    user_id: UUID,
    connection: GoogleConnection | None,
    subscription_summary: dict[str, Any],
    invoices: list[dict[str, Any]],
    upsell_payload: dict[str, Any] | None = None,
    upgrade_success: bool = False,
) -> str:
    business_name = _esc(connection.business_name or connection.google_account_name) if connection else "Cuenta Starter"
    status_label = _esc(subscription_summary.get("status_label") or "Activa")
    status_value = (subscription_summary.get("status") or "active").lower()
    status_color = "#0f766e"
    if status_value in {"past_due", "unpaid"}:
        status_color = "#b45309"
    elif status_value in {"canceled", "cancelled", "incomplete_expired"}:
        status_color = "#b91c1c"

    renewal_copy = "Sin fecha sincronizada"
    current_period_end = subscription_summary.get("current_period_end")
    if current_period_end:
        try:
            renewal_dt = datetime.fromisoformat(current_period_end.replace("Z", "+00:00"))
            renewal_copy = renewal_dt.strftime("%d/%m/%Y")
        except ValueError:
            renewal_copy = str(current_period_end)

    invoice_rows = "".join(
        f"""
        <tr>
          <td>{_esc(item.get('number') or item.get('id') or 'Factura')}</td>
          <td>{_esc(item.get('status') or 'paid')}</td>
          <td>{float(item.get('amount_paid') or 0):.2f} {_esc(item.get('currency') or 'USD')}</td>
          <td>{_esc((item.get('created_at') or '').split('T')[0] or '—')}</td>
          <td><a class=\"btn small\" href=\"{_esc(item.get('invoice_pdf') or item.get('hosted_invoice_url') or '#')}\" target=\"_blank\" rel=\"noreferrer\">Descargar factura</a></td>
        </tr>
        """
        for item in invoices
    )
    if not invoice_rows:
        invoice_rows = '<tr><td colspan="5" class="empty-row">Todavía no hay facturas disponibles para esta cuenta.</td></tr>'

    upsell_modal = ""
    if upsell_payload and upsell_payload.get("upgrade_required"):
        upsell = upsell_payload.get("upsell") or {}
        upsell_modal = f"""
        <div class=\"modal-backdrop\" id=\"upsell-modal\">
          <div class=\"modal-card\">
            <span class=\"modal-kicker\">Upgrade Check</span>
            <h2>{_esc(upsell.get('title') or 'Actualiza a Growth')}</h2>
            <p>{_esc(upsell_payload.get('message') or upsell.get('body') or '')}</p>
            <div class=\"modal-actions\">
              <button class=\"btn\" type=\"button\" onclick=\"document.getElementById('upsell-modal').style.display='none'\">Ahora no</button>
              <button class=\"btn primary\" type=\"button\" onclick=\"startGrowthUpgrade()\">{_esc(upsell.get('cta_label') or 'Actualizar a Growth')}</button>
            </div>
          </div>
        </div>
        """

    success_banner = ""
    if upgrade_success:
        success_banner = '<div class="notice ok">La actualización fue iniciada correctamente. En cuanto Stripe confirme el cambio, verás el nuevo estado aquí.</div>'

    return f"""
<!doctype html>
<html lang=\"es\">
  <head>
    <meta charset=\"utf-8\" />
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
    <title>Gestión de Suscripción | Lokigi</title>
    <script src=\"https://unpkg.com/htmx.org@1.9.12\"></script>
    <style>
      :root {{ --bg:#f2f6fb; --card:#fff; --text:#0f172a; --muted:#64748b; --border:#dbe3ee; --primary:#0f62fe; }}
      * {{ box-sizing:border-box; }}
      body {{ margin:0; font-family:Arial, \"Helvetica Neue\", sans-serif; color:var(--text); background:linear-gradient(180deg,#ffffff,#f2f6fb); }}
      .wrap {{ max-width:1100px; margin:0 auto; padding:20px; }}
      .hero {{ background:linear-gradient(135deg,#082f49,#0f62fe); color:#fff; border-radius:20px; padding:24px; }}
      .hero-top {{ display:flex; justify-content:space-between; gap:12px; align-items:flex-start; flex-wrap:wrap; }}
      .status-badge {{ display:inline-flex; padding:7px 12px; border-radius:999px; font-weight:700; font-size:12px; background:{status_color}; color:#fff; }}
      .hero p {{ margin:8px 0 0; color:#dbeafe; max-width:620px; }}
      .grid {{ display:grid; grid-template-columns:0.8fr 1.2fr; gap:16px; margin-top:16px; }}
      .card {{ background:var(--card); border:1px solid var(--border); border-radius:18px; padding:18px; }}
      .metric {{ font-size:32px; font-weight:800; margin:4px 0; }}
      .muted {{ color:var(--muted); }}
      .btn {{ display:inline-flex; align-items:center; justify-content:center; text-decoration:none; padding:10px 14px; border-radius:10px; border:1px solid var(--border); background:#fff; color:var(--text); font-weight:700; cursor:pointer; }}
      .btn.primary {{ background:var(--primary); border-color:var(--primary); color:#fff; }}
      .btn.small {{ padding:8px 10px; font-size:13px; }}
      .cta-row, .subscription-actions {{ display:flex; gap:10px; flex-wrap:wrap; margin-top:14px; }}
      table {{ width:100%; border-collapse:collapse; }}
      th, td {{ text-align:left; padding:12px 10px; border-bottom:1px solid var(--border); font-size:14px; }}
      th {{ color:#475569; font-size:12px; text-transform:uppercase; letter-spacing:.04em; }}
      .empty-row {{ color:var(--muted); text-align:center; padding:18px 10px; }}
      .notice {{ margin-top:16px; border-radius:12px; padding:12px 14px; border:1px solid #cbd5e1; background:#fff; }}
      .notice.ok {{ background:#ecfdf5; border-color:#86efac; color:#166534; }}
      .modal-backdrop {{ position:fixed; inset:0; background:rgba(15,23,42,.45); display:flex; align-items:center; justify-content:center; padding:18px; }}
      .modal-card {{ width:min(520px,100%); background:#fff; border-radius:20px; padding:24px; box-shadow:0 24px 60px rgba(15,23,42,.25); }}
      .modal-kicker {{ display:inline-block; font-size:12px; font-weight:700; text-transform:uppercase; letter-spacing:.05em; color:#0f62fe; margin-bottom:10px; }}
      .modal-card h2 {{ margin:0 0 10px; }}
      .modal-card p {{ color:#475569; line-height:1.5; }}
      .modal-actions {{ display:flex; gap:10px; justify-content:flex-end; margin-top:18px; flex-wrap:wrap; }}
      .cancel-flow-backdrop {{ position:fixed; inset:0; background:rgba(15,23,42,.55); display:flex; align-items:center; justify-content:center; padding:18px; z-index:70; animation:fadeIn .18s ease-out; }}
      .cancel-flow-card {{ width:min(760px,100%); background:#fff; border-radius:24px; padding:24px; box-shadow:0 28px 60px rgba(15,23,42,.28); animation:slideUp .24s cubic-bezier(.2,.8,.2,1); }}
      .cancel-flow-kicker {{ display:inline-flex; padding:6px 10px; border-radius:999px; background:#eef5ff; color:#0f62fe; font-size:12px; font-weight:700; text-transform:uppercase; letter-spacing:.05em; }}
      .cancel-flow-card h2 {{ margin:12px 0 8px; font-size:30px; }}
      .cancel-flow-copy {{ color:#475569; line-height:1.6; margin:0; }}
      .pause-offer {{ margin-top:18px; border:1px solid #bfdbfe; background:linear-gradient(180deg,#f8fbff,#eef5ff); border-radius:18px; padding:18px; }}
      .pause-offer-badge {{ display:inline-flex; padding:5px 9px; border-radius:999px; background:#0f62fe; color:#fff; font-size:11px; font-weight:700; text-transform:uppercase; letter-spacing:.05em; }}
      .pause-offer h3 {{ margin:12px 0 8px; }}
      .pause-offer p {{ margin:0 0 14px; color:#334155; line-height:1.55; }}
      .cancel-flow-actions {{ display:flex; justify-content:space-between; gap:12px; flex-wrap:wrap; margin-top:18px; }}
      .link-btn {{ border:none; background:transparent; color:#475569; font-weight:700; text-decoration:underline; cursor:pointer; padding:0; }}
      .reason-grid {{ display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:12px; margin-top:18px; }}
      .reason-btn {{ display:flex; flex-direction:column; gap:10px; align-items:flex-start; justify-content:flex-start; min-height:118px; border:1px solid var(--border); border-radius:18px; background:#fff; padding:16px; font:inherit; font-weight:700; color:#0f172a; cursor:pointer; text-align:left; }}
      .reason-btn.selected {{ border-color:#0f62fe; background:#eef5ff; box-shadow:0 0 0 3px rgba(15,98,254,.12); }}
      .reason-icon {{ font-size:26px; line-height:1; }}
      .data-gift {{ margin-top:18px; border:1px dashed #94a3b8; border-radius:18px; padding:18px; background:#f8fafc; }}
      .data-gift h3 {{ margin:0 0 8px; }}
      .data-gift p {{ margin:0 0 14px; color:#475569; line-height:1.55; }}
      .cancel-confirm-form {{ margin-top:12px; }}
      @keyframes fadeIn {{ from {{ opacity:0; }} to {{ opacity:1; }} }}
      @keyframes slideUp {{ from {{ opacity:0; transform:translateY(18px) scale(.98); }} to {{ opacity:1; transform:translateY(0) scale(1); }} }}
      @media (max-width:900px) {{ .grid {{ grid-template-columns:1fr; }} .reason-grid {{ grid-template-columns:1fr; }} }}
    </style>
  </head>
  <body>
    <div class=\"wrap\">
      <section class=\"hero\">
        <div class=\"hero-top\">
          <div>
            <span class=\"status-badge\">{status_label}</span>
            <h1 style=\"margin:12px 0 0\">Gestión de Suscripción</h1>
            <p>Administra el estado del Plan Starter, consulta el histórico de facturas de Stripe y decide cuándo escalar a Growth.</p>
          </div>
          <a href=\"/starter/dashboard?user_id={user_id}\" class=\"btn\">Volver al dashboard</a>
        </div>
      </section>

      {success_banner}

      <section class=\"grid\">
        <article class=\"card\">
          <div class=\"muted\">Negocio conectado</div>
          <div class=\"metric\" style=\"font-size:26px\">{business_name}</div>
          <div class=\"muted\">Plan actual: {_esc(subscription_summary.get('plan') or 'starter').title()}</div>
          <div class=\"muted\" style=\"margin-top:6px\">Renovación / fin de ciclo: {renewal_copy}</div>
          <div class=\"subscription-actions\">
            <button class=\"btn primary\" type=\"button\" onclick=\"startGrowthUpgrade()\">Actualizar a Growth</button>
            <button class=\"btn\" hx-get=\"/starter/subscription/cancel-flow?user_id={user_id}\" hx-target=\"#subscription-cancel-shell\" hx-swap=\"innerHTML\">Gestionar Suscripción</button>
          </div>
        </article>

        <article class=\"card\">
          <h2 style=\"margin-top:0\">Histórico de facturas</h2>
          <div class=\"muted\" style=\"margin-bottom:12px\">Cada factura enlaza al PDF o al hosted invoice de Stripe.</div>
          <table>
            <thead>
              <tr>
                <th>Factura</th>
                <th>Estado</th>
                <th>Importe</th>
                <th>Fecha</th>
                <th>Acción</th>
              </tr>
            </thead>
            <tbody>{invoice_rows}</tbody>
          </table>
        </article>
      </section>

      <div id=\"subscription-cancel-shell\"></div>
    </div>

    {upsell_modal}

    <script>
      const USER_ID = {json.dumps(str(user_id))};
      async function startGrowthUpgrade() {{
        const response = await fetch('/api/subscription/upgrade/growth', {{
          method: 'POST',
          headers: {{ 'Content-Type': 'application/json' }},
          body: JSON.stringify({{ user_id: USER_ID }}),
        }});
        const payload = await response.json();
        if (!response.ok || !payload.checkout_url) {{
          window.alert('No se pudo iniciar el upgrade a Growth.');
          return;
        }}
        window.location.href = payload.checkout_url;
      }}
    </script>
  </body>
</html>
"""


def render_starter_profile_html(
    user_id: UUID,
    connection: GoogleConnection,
    location_title: str,
    location_address: str,
    location_hours: list[str],
    current_tone: str,
    forbidden_words: str,
    response_schedule: str,
) -> str:
    title_html = _esc(location_title)
    address_html = _esc(location_address)
    hours_html = "".join(f"<li>{_esc(line)}</li>" for line in location_hours) if location_hours else "<li>No disponible</li>"
    forbidden_words_html = _esc(forbidden_words)
    response_schedule = response_schedule if response_schedule in {"instant", "delay_1h"} else "instant"

    return f"""
<!doctype html>
<html lang=\"es\">
<head>
  <meta charset=\"utf-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
  <title>Configuración de Perfil | Lokigi</title>
  <style>
    :root {{
      --primary: #0d6efd;
      --primary-dark: #0a58ca;
      --bg: #f3f6fb;
      --card: #ffffff;
      --text: #0f172a;
      --muted: #64748b;
      --border: #d9e2ec;
      --ok: #166534;
      --ok-bg: #dcfce7;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      color: var(--text);
      font-family: Arial, "Helvetica Neue", sans-serif;
      background:
        radial-gradient(circle at 5% 0%, rgba(13, 110, 253, 0.16), transparent 28%),
        linear-gradient(180deg, #fff, var(--bg));
    }}
    .wrap {{ max-width: 1080px; margin: 0 auto; padding: 18px; }}
    .top {{ background: var(--card); border: 1px solid var(--border); border-radius: 16px; padding: 16px; }}
    .top h1 {{ margin: 0 0 4px; font-size: clamp(24px, 4vw, 34px); }}
    .top p {{ margin: 0; color: var(--muted); }}
    .grid {{ display: grid; gap: 14px; grid-template-columns: 1fr 1fr; margin-top: 14px; }}
    .card {{ background: var(--card); border: 1px solid var(--border); border-radius: 14px; padding: 16px; }}
    .card h2 {{ margin: 0 0 10px; font-size: 18px; }}
    .meta-row {{ margin-bottom: 10px; }}
    .meta-label {{ display: block; font-size: 12px; text-transform: uppercase; color: var(--muted); font-weight: 700; margin-bottom: 4px; }}
    .meta-value {{ font-size: 14px; line-height: 1.5; }}
    .hours-list {{ margin: 0; padding-left: 18px; color: #334155; display: grid; gap: 5px; font-size: 14px; }}

    .tones-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(190px, 1fr)); gap: 10px; }}
    .tone-card {{ border: 2px solid var(--border); border-radius: 12px; padding: 12px; background: #fff; cursor: pointer; transition: border-color .15s ease, box-shadow .15s ease; }}
    .tone-card.selected {{ border-color: var(--primary); box-shadow: 0 0 0 3px rgba(13,110,253,0.12); }}
    .tone-card strong {{ display: block; margin-bottom: 6px; }}
    .tone-card span {{ color: var(--muted); font-size: 13px; line-height: 1.4; }}
    .preview {{ margin-top: 10px; border: 1px dashed rgba(13, 110, 253, 0.4); border-radius: 12px; padding: 12px; min-height: 86px; background: #eef5ff; font-size: 14px; line-height: 1.5; }}
    .preview.empty {{ color: var(--muted); font-style: italic; }}

    .field-label {{ display: block; font-size: 13px; font-weight: 700; margin-bottom: 6px; }}
    textarea {{ width: 100%; min-height: 100px; border: 1px solid var(--border); border-radius: 10px; padding: 10px; resize: vertical; font: inherit; }}
    .help {{ margin-top: 6px; color: var(--muted); font-size: 12px; }}
    .schedule {{ display: grid; gap: 10px; }}
    .schedule label {{ display: flex; align-items: flex-start; gap: 10px; border: 1px solid var(--border); border-radius: 10px; padding: 10px; }}
    .schedule strong {{ display: block; font-size: 14px; }}
    .schedule span {{ color: var(--muted); font-size: 13px; }}
    .schedule-status {{ margin-top: 10px; font-size: 13px; color: #0c4a6e; background: #e0f2fe; border: 1px solid #bae6fd; border-radius: 8px; padding: 8px 10px; }}

    .actions {{ margin-top: 14px; display: flex; gap: 10px; flex-wrap: wrap; }}
    .btn {{ display: inline-flex; align-items: center; justify-content: center; text-decoration: none; border-radius: 10px; padding: 10px 14px; border: 1px solid var(--border); background: #fff; color: var(--text); font-weight: 700; cursor: pointer; }}
    .btn.primary {{ background: linear-gradient(135deg, var(--primary), var(--primary-dark)); color: #fff; border-color: var(--primary); }}
    .status {{ margin-top: 10px; font-size: 13px; color: var(--muted); }}
    .status.ok {{ color: var(--ok); background: var(--ok-bg); border: 1px solid #86efac; border-radius: 8px; padding: 8px 10px; display: inline-block; }}
    @media (max-width: 920px) {{ .grid {{ grid-template-columns: 1fr; }} }}
  </style>
</head>
<body>
  <div class=\"wrap\">
    <section class=\"top\">
      <h1>Configuración de Perfil</h1>
      <p>Ajusta cómo responde la IA y revisa los datos actuales de tu ubicación en Google (solo lectura).</p>
    </section>

    <section class=\"grid\">
      <article class=\"card\">
        <h2>Ubicación en Google</h2>
        <div class=\"meta-row\">
          <span class=\"meta-label\">Nombre</span>
          <div class=\"meta-value\">{title_html}</div>
        </div>
        <div class=\"meta-row\">
          <span class=\"meta-label\">Dirección</span>
          <div class=\"meta-value\">{address_html}</div>
        </div>
        <div class=\"meta-row\">
          <span class=\"meta-label\">Horarios</span>
          <ul class=\"hours-list\">{hours_html}</ul>
        </div>
      </article>

      <article class=\"card\">
        <h2>Voz de Marca</h2>
        <div class=\"tones-grid\">
          <div class=\"tone-card\" data-tone=\"cercano\" onclick=\"selectTone(this)\"><strong>Cercano</strong><span>Cálido, humano y directo.</span></div>
          <div class=\"tone-card\" data-tone=\"formal\" onclick=\"selectTone(this)\"><strong>Formal</strong><span>Profesional y sobrio.</span></div>
          <div class=\"tone-card\" data-tone=\"moderno\" onclick=\"selectTone(this)\"><strong>Moderno/Emoji</strong><span>Ágil y digital.</span></div>
        </div>
        <div id=\"tone-preview\" class=\"preview empty\">Selecciona un tono para previsualizar una respuesta.</div>
      </article>
    </section>

    <section class=\"grid\">
      <article class=\"card\">
        <h2>Palabras Prohibidas</h2>
        <label class=\"field-label\" for=\"forbidden-words\">Términos que la IA nunca debe usar</label>
        <textarea id=\"forbidden-words\" placeholder=\"Ejemplo: barato, mediocre, urgente\">{forbidden_words_html}</textarea>
        <div class=\"help\">Separa por comas o saltos de línea. Lokigi bloqueará estos términos en futuras respuestas sugeridas.</div>
      </article>

      <article class=\"card\">
        <h2>Horario de Respuesta</h2>
        <div class=\"schedule\">
          <label>
            <input type=\"radio\" name=\"response-schedule\" value=\"instant\" {'checked' if response_schedule == 'instant' else ''} />
            <div><strong>Responder al instante</strong><span>Publicación inmediata tras aprobación/automatización.</span></div>
          </label>
          <label>
            <input type=\"radio\" name=\"response-schedule\" value=\"delay_1h\" {'checked' if response_schedule == 'delay_1h' else ''} />
            <div><strong>Esperar 1 hora</strong><span>Simula una respuesta más humana antes de publicar.</span></div>
          </label>
        </div>
        <div id=\"schedule-status\" class=\"schedule-status\"></div>
      </article>
    </section>

    <section class=\"actions\">
      <button class=\"btn primary\" id=\"save-btn\" onclick=\"saveProfile()\">Guardar configuración</button>
      <a class=\"btn\" href=\"/starter/dashboard?user_id={user_id}\">Volver al dashboard</a>
    </section>
    <div id=\"save-status\" class=\"status\"></div>
  </div>

<script>
const USER_ID = {json.dumps(str(user_id))};
const CURRENT_TONE = {json.dumps((current_tone or 'cercano').lower())};
const BUSINESS_NAME = {json.dumps(connection.business_name or connection.google_account_name)};
const SAMPLE_REVIEW = "Gracias por la buena atención y la rapidez.";
const SAMPLE_AUTHOR = "Cliente";

let selectedTone = CURRENT_TONE;

function setSelectedToneCard() {{
  document.querySelectorAll('.tone-card').forEach((card) => {{
    card.classList.toggle('selected', card.dataset.tone === selectedTone);
  }});
}}

async function renderTonePreview() {{
  const preview = document.getElementById('tone-preview');
  try {{
    const res = await fetch('/api/tone-preview', {{
      method: 'POST',
      headers: {{ 'Content-Type': 'application/json' }},
      body: JSON.stringify({{
        tone: selectedTone,
        review_text: SAMPLE_REVIEW,
        stars: 5,
        business_name: BUSINESS_NAME,
        author_name: SAMPLE_AUTHOR,
      }}),
    }});
    if (!res.ok) throw new Error(`HTTP ${{res.status}}`);
    const data = await res.json();
    preview.textContent = data.preview;
    preview.classList.remove('empty');
  }} catch (_) {{
    preview.textContent = 'No se pudo generar el preview en este momento.';
    preview.classList.add('empty');
  }}
}}

function selectTone(el) {{
  selectedTone = el.dataset.tone;
  setSelectedToneCard();
  renderTonePreview();
}}

function getSelectedSchedule() {{
  const checked = document.querySelector('input[name="response-schedule"]:checked');
  return checked ? checked.value : 'instant';
}}

function updateScheduleStatus() {{
  const status = document.getElementById('schedule-status');
  const mode = getSelectedSchedule();
  if (mode === 'delay_1h') {{
    status.textContent = 'Estado actual: Auto-publicación diferida. La IA esperará 1 hora antes de enviar.';
  }} else {{
    status.textContent = 'Estado actual: Auto-publicación inmediata cuando aplique.';
  }}
}}

async function saveProfile() {{
  const btn = document.getElementById('save-btn');
  const status = document.getElementById('save-status');
  btn.disabled = true;
  status.textContent = 'Guardando cambios...';
  status.className = 'status';

  try {{
    const res = await fetch('/api/starter/profile', {{
      method: 'POST',
      headers: {{ 'Content-Type': 'application/json' }},
      body: JSON.stringify({{
        user_id: USER_ID,
        tone: selectedTone,
        forbidden_words: document.getElementById('forbidden-words').value,
        response_schedule: getSelectedSchedule(),
      }}),
    }});
    if (!res.ok) throw new Error(`HTTP ${{res.status}}`);
    status.textContent = 'Configuración guardada correctamente.';
    status.className = 'status ok';
  }} catch (e) {{
    status.textContent = 'No se pudo guardar la configuración. Intenta nuevamente.';
    status.className = 'status';
  }} finally {{
    btn.disabled = false;
  }}
}}

window.addEventListener('DOMContentLoaded', () => {{
  setSelectedToneCard();
  renderTonePreview();
  document.querySelectorAll('input[name="response-schedule"]').forEach((el) => {{
    el.addEventListener('change', updateScheduleStatus);
  }});
  updateScheduleStatus();
}});
</script>
</body>
</html>
"""


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/starter/onboarding", response_class=HTMLResponse)
def starter_onboarding(user_id: UUID, location_id: str = "") -> HTMLResponse:
    query_suffix = f"&location_id={location_id}" if location_id else ""
    connect_url = f"/starter/connect-google?user_id={user_id}{query_suffix}"
    return HTMLResponse(render_starter_onboarding_html(user_id=user_id, location_id=location_id, connect_url=connect_url))


@app.get("/starter/connect-google")
def starter_connect_google(user_id: UUID, location_id: str = "", db: Session = Depends(get_db)) -> RedirectResponse:
  upgrade_check = check_growth_upgrade_needed(db, user_id, location_id)
  if upgrade_check.get("upgrade_required"):
    return RedirectResponse(url=f"/starter/subscription?user_id={user_id}&upsell=growth&requested_location_id={location_id}")

  oauth_url = build_google_oauth_url(
    user_id=str(user_id),
    location_id=location_id or None,
    extra_state={"starter_flow": True},
  )
  return RedirectResponse(url=oauth_url)


@app.get("/starter/loading", response_class=HTMLResponse)
def starter_loading(user_id: UUID) -> HTMLResponse:
    """Active loading screen with animated milestones for step 2 onboarding.
    
    Shown after OAuth callback to display progress while backend initializes user data.
    Automatically redirects to dashboard after ~7 seconds.
    """
    return HTMLResponse(render_starter_loading_html(user_id=user_id, next_url=f"/starter/tone-selector?user_id={user_id}"))


@app.get("/starter/tone-selector", response_class=HTMLResponse)
def starter_tone_selector(user_id: UUID, db: Session = Depends(get_db)) -> HTMLResponse:
    """Interactive tone selector with real-time preview.
    
    Allows user to select between 'cercano', 'formal', 'moderno' voice tones.
    Fetches the user's first positive review to use as preview example.
    """
    connection = db.scalar(select(GoogleConnection).where(GoogleConnection.user_id == user_id))
    if not connection:
        raise HTTPException(status_code=404, detail="User not connected")
    
    # Get the user's first positive review for preview
    first_review = db.scalar(
        select(Review)
        .where(Review.connection_id == connection.id, Review.rating >= 4)
        .order_by(Review.created_at.asc())
        .limit(1)
    )
    
    if not first_review:
        # Fallback to any review if no positive ones
        first_review = db.scalar(
            select(Review)
            .where(Review.connection_id == connection.id)
            .order_by(Review.created_at.asc())
            .limit(1)
        )
    
    if not first_review:
        # Last resort: use a placeholder review
        first_review_text = "Esta ha sido una excelente experiencia. El servicio fue impecable."
        first_review_author = "Cliente Ejemplo"
        first_review_stars = 5
    else:
        first_review_text = first_review.comment or "(sin comentario)"
        first_review_author = first_review.author_display_name or "Cliente"
        first_review_stars = first_review.rating or 5
    
    html = render_starter_tone_selector_html(
        user_id=user_id,
        first_review_text=first_review_text,
        first_review_author=first_review_author,
        first_review_stars=first_review_stars,
        business_name=connection.business_name or "nuestro negocio",
        current_tone=connection.preferred_tone,
        manual_approval_enabled=connection.manual_approval_enabled,
        whatsapp_negative_alerts_enabled=connection.negative_review_whatsapp_enabled,
    )
    return HTMLResponse(html)


@app.get("/starter/dashboard", response_class=HTMLResponse)
async def starter_dashboard(user_id: UUID, db: Session = Depends(get_db)) -> HTMLResponse:
    from .models import MonthlyReport as MonthlyReportModel

    connection = db.scalar(select(GoogleConnection).where(GoogleConnection.user_id == user_id))

    now = datetime.utcnow()
    month_start = datetime(now.year, now.month, 1)

    replies_sent_month = db.scalar(
        select(func.count(Review.id))
        .join(GoogleConnection, Review.connection_id == GoogleConnection.id)
        .where(
            GoogleConnection.user_id == user_id,
            Review.reply_sent_at.is_not(None),
            Review.reply_sent_at >= month_start,
        )
    ) or 0
    minutes_saved_month = replies_sent_month * 4

    pending_reviews = get_pending_approvals(db, str(user_id))

    rating_reviews = db.scalars(
        select(Review)
        .join(GoogleConnection, Review.connection_id == GoogleConnection.id)
        .where(
            GoogleConnection.user_id == user_id,
            Review.rating.is_not(None),
        )
        .order_by(Review.created_at.desc())
        .limit(320)
    ).all()

    ratings = [float(r.rating) for r in rating_reviews if r.rating is not None]
    current_avg_rating = round(sum(ratings) / len(ratings), 1) if ratings else None

    prev_month_year = now.year if now.month > 1 else now.year - 1
    prev_month_num = now.month - 1 if now.month > 1 else 12
    current_month_ratings: list[float] = []
    previous_month_ratings: list[float] = []

    for review in rating_reviews:
        dt = review.create_time or review.created_at
        if not dt or review.rating is None:
            continue
        if dt.year == now.year and dt.month == now.month:
            current_month_ratings.append(float(review.rating))
        elif dt.year == prev_month_year and dt.month == prev_month_num:
            previous_month_ratings.append(float(review.rating))

    trend_direction = "flat"
    trend_delta = 0.0
    if current_month_ratings and previous_month_ratings:
        curr_avg = sum(current_month_ratings) / len(current_month_ratings)
        prev_avg = sum(previous_month_ratings) / len(previous_month_ratings)
        trend_delta = round(curr_avg - prev_avg, 1)
        if trend_delta > 0:
            trend_direction = "up"
        elif trend_delta < 0:
            trend_direction = "down"

    days_in_month = monthrange(now.year, now.month)[1]
    days_to_report_close = max(days_in_month - now.day, 0)

    current_month_reviews = db.scalars(
      select(Review)
      .join(GoogleConnection, Review.connection_id == GoogleConnection.id)
      .where(
        GoogleConnection.user_id == user_id,
        Review.create_time.is_not(None),
        func.extract("year", Review.create_time) == now.year,
        func.extract("month", Review.create_time) == now.month,
      )
      .order_by(Review.create_time.desc())
    ).all()

    sentiment_report = analyze_monthly_sentiment(
      [
        {"rating": review.rating, "comment": review.comment or ""}
        for review in current_month_reviews
      ],
      year=now.year,
      month=now.month,
      location_id=connection.location_id if connection else str(user_id),
      top_n=5,
    ).to_dict()

    response_velocity = (
      _build_response_velocity(db, user_id, connection, now.year, now.month)
      if connection
      else {}
    )

    recent_reviews = db.scalars(
        select(Review)
        .join(GoogleConnection, Review.connection_id == GoogleConnection.id)
        .where(GoogleConnection.user_id == user_id)
        .order_by(Review.created_at.desc())
        .limit(5)
    ).all()

    tip_reviews = db.scalars(
      select(Review)
      .join(GoogleConnection, Review.connection_id == GoogleConnection.id)
      .where(
        GoogleConnection.user_id == user_id,
        Review.comment.is_not(None),
      )
      .order_by(Review.create_time.desc().nullslast(), Review.created_at.desc())
      .limit(10)
    ).all()

    starter_tip = generate_starter_tip(
      business_name=(connection.business_name if connection and connection.business_name else "tu negocio"),
      business_type="negocio local",
      location=(connection.location_id if connection else "tu zona"),
      reviews=[r.comment or "" for r in tip_reviews],
    )

    history_rows = db.scalars(
      select(MonthlyReportModel)
      .where(MonthlyReportModel.user_id == user_id)
      .order_by(MonthlyReportModel.year.desc(), MonthlyReportModel.month.desc())
      .limit(24)
    ).all()
    report_history = [
      {
        "year": row.year,
        "month": row.month,
        "pdf_status": row.pdf_status,
        "pdf_signed_url": row.pdf_signed_url,
      }
      for row in history_rows
    ]

    optimization_center_html = ""
    if connection:
      try:
        await _sync_google_profile_snapshot(db, connection)
      except GoogleOAuthError:
        pass

      seo_service = GrowthSeoService(db)
      active_suggestions = seo_service.list_or_generate_suggestions(user_id=user_id)
      effective_description = connection.google_profile_description or ""
      should_force_refresh = any((item.current_text or "") != effective_description for item in active_suggestions)
      seo_suggestions = seo_service.list_or_generate_suggestions(user_id=user_id, force_refresh=True) if should_force_refresh else active_suggestions
      optimization_center_html = render_optimization_center_html(
        user_id=user_id,
        suggestion=seo_suggestions[0] if seo_suggestions else None,
      )

    return HTMLResponse(
        render_starter_dashboard_html(
            user_id=user_id,
            connection=connection,
            recent_reviews=recent_reviews,
            pending_reviews=pending_reviews,
            replies_sent_month=replies_sent_month,
            minutes_saved_month=minutes_saved_month,
            current_avg_rating=current_avg_rating,
            trend_direction=trend_direction,
            trend_delta=trend_delta,
            days_to_report_close=days_to_report_close,
            response_velocity=response_velocity,
            sentiment_snapshot=sentiment_report.get("sentiment_snapshot", {}),
            keyword_concepts=sentiment_report.get("top_concepts", []),
            starter_tip=starter_tip,
            report_history=report_history,
            optimization_center_html=optimization_center_html,
        )
    )


@app.post("/starter/optimization-center/{suggestion_id}/apply", response_class=HTMLResponse)
async def starter_optimization_center_apply(
    suggestion_id: UUID,
    user_id: UUID,
    db: Session = Depends(get_db),
) -> HTMLResponse:
    service = GrowthSeoService(db)
    try:
      await service.apply_suggestion(user_id=user_id, suggestion_id=suggestion_id)
    except ValueError as exc:
      return HTMLResponse(render_optimization_partial_response(render_optimization_center_html(user_id=user_id, suggestion=None, notice=str(exc), notice_tone="error"), has_alert=False))
    except RuntimeError as exc:
      suggestion = db.get(GrowthSeoSuggestion, suggestion_id)
      failed_suggestion = suggestion if suggestion and suggestion.user_id == user_id and suggestion.status == "active" else None
      return HTMLResponse(
        render_optimization_partial_response(
          render_optimization_center_html(
            user_id=user_id,
            suggestion=failed_suggestion,
            notice=f"No se pudo aplicar el cambio en Google: {exc}",
            notice_tone="error",
          ),
          has_alert=bool(failed_suggestion),
        )
      )

    suggestion = db.get(GrowthSeoSuggestion, suggestion_id)
    keyword = suggestion.keyword if suggestion else "tu keyword objetivo"
    return HTMLResponse(render_optimization_partial_response(render_optimization_success_html(user_id=user_id, keyword=keyword), has_alert=False))


@app.post("/starter/optimization-center/refresh", response_class=HTMLResponse)
async def starter_optimization_center_refresh(
    user_id: UUID,
    db: Session = Depends(get_db),
) -> HTMLResponse:
    connection = db.scalar(select(GoogleConnection).where(GoogleConnection.user_id == user_id))
    if not connection:
      return HTMLResponse(render_optimization_partial_response(render_optimization_center_html(user_id=user_id, suggestion=None, notice="Google connection not found.", notice_tone="error"), has_alert=False))

    try:
      await _sync_google_profile_snapshot(db, connection)
    except GoogleOAuthError as exc:
      suggestions = GrowthSeoService(db).list_or_generate_suggestions(user_id=user_id)
      active_suggestion = suggestions[0] if suggestions else None
      return HTMLResponse(
        render_optimization_partial_response(
          render_optimization_center_html(
            user_id=user_id,
            suggestion=active_suggestion,
            notice=f"No se pudo sincronizar el perfil desde Google: {exc}",
            notice_tone="error",
          ),
          has_alert=bool(active_suggestion),
        )
      )

    suggestions = GrowthSeoService(db).list_or_generate_suggestions(user_id=user_id, force_refresh=True)
    active_suggestion = suggestions[0] if suggestions else None
    return HTMLResponse(
      render_optimization_partial_response(
        render_optimization_center_html(
          user_id=user_id,
          suggestion=active_suggestion,
          notice="Oportunidades recalculadas con la descripcion real del perfil.",
          notice_tone="ok",
        ),
        has_alert=bool(active_suggestion),
      )
    )


@app.post("/starter/optimization-center/{suggestion_id}/dismiss", response_class=HTMLResponse)
def starter_optimization_center_dismiss(
    suggestion_id: UUID,
    user_id: UUID,
    db: Session = Depends(get_db),
) -> HTMLResponse:
    service = GrowthSeoService(db)
    try:
      service.dismiss_suggestion(user_id=user_id, suggestion_id=suggestion_id, reason="starter_dashboard")
    except ValueError as exc:
      return HTMLResponse(render_optimization_partial_response(render_optimization_center_html(user_id=user_id, suggestion=None, notice=str(exc), notice_tone="error"), has_alert=False))

    remaining = service.list_or_generate_suggestions(user_id=user_id)
    active_suggestion = remaining[0] if remaining else None
    return HTMLResponse(
      render_optimization_partial_response(
        render_optimization_center_html(
          user_id=user_id,
          suggestion=active_suggestion,
          notice="Oportunidad descartada. Te mostraremos la siguiente sugerencia disponible.",
        ),
        has_alert=bool(active_suggestion),
      )
    )


@app.get("/starter/profile", response_class=HTMLResponse)
async def starter_profile(user_id: UUID, db: Session = Depends(get_db)) -> HTMLResponse:
    connection = db.scalar(select(GoogleConnection).where(GoogleConnection.user_id == user_id))
    if not connection:
        raise HTTPException(status_code=404, detail="User not connected")

    location_title = connection.business_name or connection.google_account_name
    location_address = "No disponible"
    location_hours: list[str] = []

    try:
        location_data = await _sync_google_profile_snapshot(db, connection)
        location_title = location_data.get("title") or location_title
        location_address = _format_storefront_address(location_data.get("storefrontAddress"))
        weekday_lines = (location_data.get("regularHours") or {}).get("weekdayDescriptions") or []
        location_hours = [str(x) for x in weekday_lines if str(x).strip()]
    except GoogleOAuthError:
        # Keep fallback values from persisted connection when Google metadata is unavailable.
        pass

    profile_settings = db.scalar(select(StarterProfileSettings).where(StarterProfileSettings.user_id == user_id))
    forbidden_words = profile_settings.forbidden_words if profile_settings else ""
    response_schedule = profile_settings.response_schedule if profile_settings else "instant"

    return HTMLResponse(
        render_starter_profile_html(
            user_id=user_id,
            connection=connection,
            location_title=location_title,
            location_address=location_address,
            location_hours=location_hours,
            current_tone=connection.preferred_tone,
            forbidden_words=forbidden_words,
            response_schedule=response_schedule,
        )
    )


@app.post("/api/starter/profile")
def api_starter_profile_save(req: StarterProfileSaveRequest, db: Session = Depends(get_db)) -> dict[str, Any]:
    connection = db.scalar(select(GoogleConnection).where(GoogleConnection.user_id == req.user_id))
    if not connection:
        raise HTTPException(status_code=404, detail="User not connected")

    tone_lower = (req.tone or "cercano").lower().strip()
    if tone_lower == "amistoso":
      tone_lower = "cercano"
    if tone_lower not in ["cercano", "formal", "moderno"]:
        raise HTTPException(status_code=400, detail="Invalid tone. Must be one of: cercano, formal, moderno")

    response_schedule = (req.response_schedule or "instant").strip().lower()
    if response_schedule not in {"instant", "delay_1h"}:
        raise HTTPException(status_code=400, detail="Invalid response_schedule. Use instant or delay_1h")

    connection.preferred_tone = tone_lower

    profile_settings = db.scalar(select(StarterProfileSettings).where(StarterProfileSettings.user_id == req.user_id))
    if not profile_settings:
        profile_settings = StarterProfileSettings(user_id=req.user_id)
        db.add(profile_settings)

    profile_settings.forbidden_words = (req.forbidden_words or "").strip()
    profile_settings.response_schedule = response_schedule

    db.commit()
    db.refresh(connection)
    db.refresh(profile_settings)

    return {
        "status": "saved",
        "user_id": str(req.user_id),
        "preferred_tone": connection.preferred_tone,
        "forbidden_words": profile_settings.forbidden_words,
        "response_schedule": profile_settings.response_schedule,
    }


@app.get("/starter/subscription", response_class=HTMLResponse)
def starter_subscription_page(
    user_id: UUID,
    upsell: str = "",
    requested_location_id: str = "",
    upgrade: str = "",
    db: Session = Depends(get_db),
) -> HTMLResponse:
    connection = db.scalar(select(GoogleConnection).where(GoogleConnection.user_id == user_id))
    subscription_summary = get_subscription_summary(db, user_id)
    invoices = list_subscription_invoices(db, user_id)
    upsell_payload = None
    if upsell == "growth":
        upsell_payload = check_growth_upgrade_needed(db, user_id, requested_location_id)

    return HTMLResponse(
        render_starter_subscription_html(
            user_id=user_id,
            connection=connection,
            subscription_summary=subscription_summary,
            invoices=invoices,
            upsell_payload=upsell_payload,
            upgrade_success=upgrade == "success",
        )
    )


@app.get("/starter/subscription/cancel-flow", response_class=HTMLResponse)
def starter_subscription_cancel_flow(user_id: UUID, db: Session = Depends(get_db)) -> HTMLResponse:
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return HTMLResponse(render_subscription_cancel_choice_html(user_id))


@app.get("/starter/subscription/cancel-flow/survey", response_class=HTMLResponse)
def starter_subscription_cancel_survey(
    user_id: UUID,
    reason: str = "",
    db: Session = Depends(get_db),
) -> HTMLResponse:
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    selected_reason = reason if reason in CancellationService.allowed_feedback_reasons() else None
    return HTMLResponse(render_subscription_cancel_survey_html(user_id, selected_reason=selected_reason))


@app.post("/starter/subscription/cancel-flow/confirm", response_class=HTMLResponse)
async def starter_subscription_cancel_confirm(
    user_id: UUID,
    churn_reason: str,
    db: Session = Depends(get_db),
) -> HTMLResponse:
    if churn_reason not in CancellationService.allowed_feedback_reasons():
        raise HTTPException(status_code=400, detail="Invalid churn reason")

    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    await CancellationService.confirm_cancellation(
        db=db,
        user_id=user_id,
        churn_reason=churn_reason,
        churn_detail=None,
    )
    return HTMLResponse(
        render_subscription_cancel_survey_html(
            user_id,
            selected_reason=churn_reason,
            confirmed=True,
        )
    )


@app.post("/starter/subscription/cancel-flow/pause", response_class=HTMLResponse)
def starter_subscription_pause_flow(user_id: UUID, db: Session = Depends(get_db)) -> HTMLResponse:
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    result = CancellationService.activate_plan_pausa(db=db, user_id=user_id, duration_days=90)
    return HTMLResponse(render_subscription_pause_success_html(user_id, result.get("message") or "Cuenta pausada correctamente."))


@app.post("/starter/subscription/cancel-flow/farewell", response_class=HTMLResponse)
async def starter_subscription_cancel_farewell(
    user_id: UUID,
    churn_reason: str,
    db: Session = Depends(get_db),
) -> HTMLResponse:
    if churn_reason not in CancellationService.allowed_feedback_reasons():
        raise HTTPException(status_code=400, detail="Invalid churn reason")

    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    connection = db.scalar(select(GoogleConnection).where(GoogleConnection.user_id == user_id))
    result = await CancellationService.confirm_cancellation(
        db=db,
        user_id=user_id,
        churn_reason=churn_reason,
        churn_detail=None,
    )
    business_name = connection.business_name or connection.google_account_name if connection else user.email
    return HTMLResponse(
        render_subscription_goodbye_html(
            business_name=business_name,
            csv_url=result["reviews_csv_url"],
            logout_url=result["logout_url"],
        )
    )


@app.get("/subscription/export-csv")
def subscription_export_csv(user_id: UUID, db: Session = Depends(get_db)) -> Response:
    return build_reviews_export_response(db, user_id)


@app.get("/api/subscription/status")
def api_subscription_status(user_id: UUID, db: Session = Depends(get_db)) -> dict[str, Any]:
    return get_subscription_summary(db, user_id)


@app.get("/api/subscription/invoices")
def api_subscription_invoices(user_id: UUID, db: Session = Depends(get_db)) -> dict[str, Any]:
    return {"items": list_subscription_invoices(db, user_id)}


@app.get("/api/subscription/upgrade-check")
def api_subscription_upgrade_check(user_id: UUID, requested_location_id: str, db: Session = Depends(get_db)) -> dict[str, Any]:
    return check_growth_upgrade_needed(db, user_id, requested_location_id)


@app.post("/api/subscription/upgrade/growth")
def api_subscription_upgrade_growth(req: GrowthUpgradeRequest, db: Session = Depends(get_db)) -> dict[str, Any]:
    return create_growth_checkout_session(db, req.user_id)


@app.get("/oauth/google/start")
def oauth_google_start(user_id: str, location_id: str) -> RedirectResponse:
    if not settings.google_client_id or not settings.google_client_secret:
        raise HTTPException(status_code=500, detail="Google OAuth is not configured")
    url = build_google_oauth_url(user_id=user_id, location_id=location_id)
    return RedirectResponse(url=url)


@app.get("/oauth/google/callback", response_model=None)
async def oauth_google_callback(code: str, state: str, db: Session = Depends(get_db)) -> Any:
    connection = await upsert_google_connection(db=db, code=code, state=state)
    state_payload = OAuthStateManager(settings.oauth_state_secret).verify(state)
    if state_payload.get("starter_flow") and state_payload.get("user_id"):
        # Redirect to loading screen instead of dashboard for better UX
        return RedirectResponse(url=f"/starter/loading?user_id={state_payload['user_id']}")

    return {
        "status": "linked",
        "user_id": str(connection.user_id),
        "location_id": connection.location_id,
    }


# ── Location Discovery (Zero-Friction Onboarding) ────────────────────────────

@app.get("/api/locations")
def api_locations(user_id: UUID, db: Session = Depends(get_db)) -> dict[str, Any]:
    """List available Google Business Profile locations for onboarding.

    Returns:
    <div class="cancel-flow-card" role="dialog" aria-modal="true" aria-labelledby="cancel-flow-title">
      <div class="cancel-flow-kicker">Retencion inteligente</div>
      <h2 id="cancel-flow-title">Necesitas un respiro?</h2>
      <p class="cancel-flow-copy">Antes de cancelar, te ofrecemos una pausa ligera para conservar el valor que ya construiste en Lokigi y salir sin friccion.</p>
      <section class="pause-offer">
        <div class="pause-offer-badge">Recomendada</div>
        <h3>Pausar mi cuenta</h3>
        <p>Mantendremos tus datos a salvo y tus reportes activos por solo $5/mes. Vuelve cuando quieras.</p>
        <button class="btn primary" hx-post="/starter/subscription/cancel-flow/pause?user_id={user_id}" hx-target="#subscription-cancel-shell" hx-swap="innerHTML">Pausar mi cuenta</button>
      </section>
      <div class="cancel-flow-actions">
        <button class="btn" type="button" onclick="document.getElementById('subscription-cancel-shell').innerHTML = '';">Seguir con mi plan</button>
        <button class="link-btn" hx-get="/starter/subscription/cancel-flow/survey?user_id={user_id}" hx-target="#subscription-cancel-shell" hx-swap="innerHTML">No, quiero ir a la encuesta de salida</button>
      </div>

    return [
        {
            "id": str(r.id),
            "review_id": r.review_id,
            "location_id": r.location_id,
            "rating": r.rating,
            "author": r.author_display_name or "Cliente",
            "comment": r.comment or "",
            "suggested_reply": r.reply_public_text or "",
            "detected_language": r.reply_detected_language,
            "decided_at": r.reply_decided_at.isoformat() if r.reply_decided_at else None,
            "response_schedule": response_schedule,
            "auto_send_eta_minutes": _remaining_auto_send_minutes(r.reply_decided_at, response_schedule),
        }
        for r in reviews
    ]


@app.post("/api/reviews/{review_id}/approve")
async def api_review_approve(
    review_id: UUID,
    body: ApproveReplyRequest,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Approve and send a reply to Google for the given review."""
    review = db.get(Review, review_id)
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    if not body.reply_text.strip():
        raise HTTPException(status_code=422, detail="reply_text must not be empty")
    sent = await send_review_reply(db=db, review=review, reply_text=body.reply_text)
    return {
        "status": "sent",
        "review_id": sent.review_id,
        "sent_at": sent.reply_sent_at.isoformat() if sent.reply_sent_at else None,
    }


@app.post("/api/reviews/{review_id}/regenerate")
async def api_review_regenerate(
    review_id: UUID,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Re-run NLP engine for the review and return the new suggestion."""
    review = db.get(Review, review_id)
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    updated = await regenerate_review_reply(db=db, review=review)
    return {
        "status": "regenerated",
        "review_id": updated.review_id,
        "suggested_reply": updated.reply_public_text or "",
    }


# ── Tone Selection & Preview ───────────────────────────────────────────────

class TonePreviewRequest(BaseModel):
    tone: str
    review_text: str
    stars: int
    business_name: str
    author_name: str


@app.post("/api/tone-preview")
def api_tone_preview(req: TonePreviewRequest) -> dict[str, str]:
    """Generate a preview reply based on the selected tone.
    
    Tones: 'cercano' (friendly), 'formal' (corporate), 'moderno' (contemporary)
    """
    reply = generate_reply_by_tone(
        tone=req.tone,
        review_text=req.review_text,
        stars=req.stars,
        business_name=req.business_name,
        author_name=req.author_name,
    )
    return {"preview": reply, "tone": req.tone}


@app.post("/api/tone/set")
def api_tone_set(
    req: ToneSetRequest,
    db: Session = Depends(get_db),
) -> dict[str, str]:
    """Save the user's preferred tone for reply generation.
    
    Tones: 'cercano', 'formal', 'moderno'
    """
    connection = db.scalar(select(GoogleConnection).where(GoogleConnection.user_id == req.user_id))
    if not connection:
        raise HTTPException(status_code=404, detail="User not connected")
    
    tone_lower = (req.tone or "cercano").lower().strip()
    if tone_lower == "amistoso":
      tone_lower = "cercano"
    if tone_lower not in ["cercano", "formal", "moderno"]:
        raise HTTPException(status_code=400, detail=f"Invalid tone. Must be one of: cercano, formal, moderno")
    
    connection.preferred_tone = tone_lower
    db.commit()
    db.refresh(connection)
    
    return {"status": "saved", "preferred_tone": connection.preferred_tone}




@app.post("/api/starter/activate")
def api_starter_activate(req: StarterActivationRequest, db: Session = Depends(get_db)) -> dict[str, Any]:
    """Persist initial Starter onboarding preferences and enable pilot mode."""
    connection = db.scalar(select(GoogleConnection).where(GoogleConnection.user_id == req.user_id))
    if not connection:
        raise HTTPException(status_code=404, detail="User not connected")

    tone_lower = (req.tone or "cercano").lower().strip()
    if tone_lower not in ["cercano", "formal", "moderno"]:
        raise HTTPException(status_code=400, detail="Invalid tone. Must be one of: cercano, formal, moderno")

    connection.preferred_tone = tone_lower
    connection.manual_approval_enabled = bool(req.manual_approval)
    connection.negative_review_whatsapp_enabled = bool(req.whatsapp_negative_alerts)
    db.commit()
    db.refresh(connection)

    return {
        "status": "activated",
        "user_id": str(req.user_id),
        "preferred_tone": connection.preferred_tone,
        "manual_approval_enabled": connection.manual_approval_enabled,
        "negative_review_whatsapp_enabled": connection.negative_review_whatsapp_enabled,
        "dashboard_url": f"/starter/dashboard?user_id={req.user_id}",
    }


@app.get("/api/tone/current")
def api_tone_current(user_id: UUID, db: Session = Depends(get_db)) -> dict[str, str]:
    """Get the current tone preference for the user."""
    connection = db.scalar(select(GoogleConnection).where(GoogleConnection.user_id == user_id))
    if not connection:
        raise HTTPException(status_code=404, detail="User not connected")
    return {"tone": connection.preferred_tone}


@app.get("/api/reports/monthly-sentiment")
def api_monthly_sentiment(
    user_id: UUID,
    year: int,
    month: int,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Return top-3 positive and negative concepts for the user's reviews in a given month.

    Query params: user_id, year, month
    Response: JSON ready to drive a simple bar chart (see chart_data key).
    """
    if not (1 <= month <= 12):
        raise HTTPException(status_code=422, detail="month must be between 1 and 12")
    if year < 2020 or year > 2100:
        raise HTTPException(status_code=422, detail="year out of valid range")

    # Resolve the active location for this user
    conn = db.scalars(
        select(GoogleConnection).where(GoogleConnection.user_id == user_id)
    ).first()
    location_id = conn.location_id if conn else str(user_id)

    # Fetch reviews for the target month, scoped to this user's location
    from sqlalchemy import extract
    from .models import Review as ReviewModel

    stmt = (
        select(ReviewModel)
        .join(GoogleConnection, ReviewModel.connection_id == GoogleConnection.id)
        .where(
            GoogleConnection.user_id == user_id,
            extract("year", ReviewModel.create_time) == year,
            extract("month", ReviewModel.create_time) == month,
        )
    )
    reviews_orm = db.scalars(stmt).all()

    review_dicts = [
        {
            "comment": r.comment or "",
            "rating": r.rating,
        }
        for r in reviews_orm
    ]

    report = analyze_monthly_sentiment(
        review_dicts,
        year=year,
        month=month,
        location_id=location_id,
    )
    return report.to_dict()


# ── Monthly report: stored JSON payload ──────────────────────────────────────

@app.get("/api/reports/monthly")
def api_monthly_report(
    user_id: UUID,
    year: int,
    month: int,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Return the stored MonthlyReport payload for a given user/year/month."""
    from .models import MonthlyReport as MonthlyReportModel

    row = db.scalars(
        select(MonthlyReportModel).where(
            MonthlyReportModel.user_id == user_id,
            MonthlyReportModel.year == year,
            MonthlyReportModel.month == month,
        )
    ).first()
    if not row:
        raise HTTPException(status_code=404, detail="Report not found for this period")
    return row.payload


@app.get("/api/reports/monthly-pdf")
def api_monthly_report_pdf(
    user_id: UUID,
    year: int,
    month: int,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Return signed PDF URL and generation status for a monthly report."""
    from .models import MonthlyReport as MonthlyReportModel

    row = db.scalars(
        select(MonthlyReportModel).where(
            MonthlyReportModel.user_id == user_id,
            MonthlyReportModel.year == year,
            MonthlyReportModel.month == month,
        )
    ).first()
    if not row:
        raise HTTPException(status_code=404, detail="Report not found for this period")

    return {
        "status": row.pdf_status,
        "signed_url": row.pdf_signed_url,
        "expires_at": row.pdf_signed_url_expires_at.isoformat() if row.pdf_signed_url_expires_at else None,
        "generated_at": row.pdf_generated_at.isoformat() if row.pdf_generated_at else None,
        "error": row.pdf_error,
    }


@app.get("/api/reports/history")
def api_reports_history(
    user_id: UUID,
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    """Return avg_rating and total_reviews per month, ordered oldest→newest.
    Used by the rating-evolution chart.
    """
    from .models import MonthlyReport as MonthlyReportModel

    rows = db.scalars(
        select(MonthlyReportModel)
        .where(MonthlyReportModel.user_id == user_id)
        .order_by(MonthlyReportModel.year, MonthlyReportModel.month)
    ).all()
    return [
        {
            "year": r.year,
            "month": r.month,
            "avg_rating": r.payload.get("kpis", {}).get("avg_rating"),
            "total_reviews": r.payload.get("kpis", {}).get("total_reviews", 0),
        }
        for r in rows
    ]


# ── Monthly report HTML page ──────────────────────────────────────────────────

@app.get("/starter/report", response_class=HTMLResponse)
def starter_monthly_report_page(
    user_id: UUID,
    year: int,
    month: int,
) -> HTMLResponse:
    """Starter monthly report — single page, print/PDF-ready, mobile-friendly."""
    _MONTHS_ES = {
        1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril",
        5: "Mayo", 6: "Junio", 7: "Julio", 8: "Agosto",
        9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre",
    }
    period_label = f"{_MONTHS_ES.get(month, month)} {year}"

    html = f"""\
<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Reporte Mensual {period_label} | Lokigi</title>
  <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.3/dist/chart.umd.min.js"></script>
  <style>
    /* ── Reset / base ─────────────────────────────────────── */
    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
      background: #f0f4f8;
      color: #1a202c;
      padding: 24px 16px 48px;
    }}
    /* ── Layout ───────────────────────────────────────────── */
    .page {{
      max-width: 720px;
      margin: 0 auto;
    }}
    /* ── Header ───────────────────────────────────────────── */
    .header {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      flex-wrap: wrap;
      gap: 12px;
      margin-bottom: 28px;
    }}
    .logo {{ font-size: 22px; font-weight: 800; color: #1a56db; letter-spacing: -.5px; }}
    .header-meta {{ text-align: right; }}
    .header-meta .period {{ font-size: 18px; font-weight: 700; color: #1a202c; }}
    .header-meta .biz  {{ font-size: 13px; color: #6b7280; margin-top: 2px; }}
    /* ── Section title ────────────────────────────────────── */
    .section-title {{
      font-size: 11px;
      font-weight: 700;
      letter-spacing: .1em;
      text-transform: uppercase;
      color: #6b7280;
      margin-bottom: 12px;
    }}
    /* ── KPI cards ────────────────────────────────────────── */
    .kpi-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
      gap: 14px;
      margin-bottom: 28px;
    }}
    .kpi-card {{
      background: #fff;
      border-radius: 14px;
      padding: 20px 18px;
      box-shadow: 0 1px 4px rgba(0,0,0,.08);
    }}
    .kpi-card .kpi-icon {{
      font-size: 24px;
      margin-bottom: 8px;
      display: block;
    }}
    .kpi-card .kpi-value {{
      font-size: 30px;
      font-weight: 800;
      line-height: 1;
      color: #1a56db;
    }}
    .kpi-card .kpi-label {{
      font-size: 12px;
      color: #6b7280;
      margin-top: 4px;
    }}
    .kpi-card.green  .kpi-value {{ color: #059669; }}
    .kpi-card.orange .kpi-value {{ color: #d97706; }}
    /* ── Chart cards ─────────────────────────────────────── */
    .chart-card {{
      background: #fff;
      border-radius: 14px;
      padding: 22px 20px;
      box-shadow: 0 1px 4px rgba(0,0,0,.08);
      margin-bottom: 20px;
    }}
    .value-card {{
      background: linear-gradient(135deg, #eff6ff, #ffffff);
      border: 1px solid #bfdbfe;
      border-radius: 14px;
      padding: 22px 20px;
      box-shadow: 0 1px 4px rgba(0,0,0,.08);
      margin-bottom: 20px;
    }}
    .velocity-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
      gap: 14px;
      margin-top: 10px;
    }}
    .velocity-stat {{
      background: rgba(255,255,255,.82);
      border: 1px solid #dbeafe;
      border-radius: 12px;
      padding: 14px;
    }}
    .velocity-stat .label {{ font-size: 12px; color: #6b7280; margin-bottom: 5px; }}
    .velocity-stat .value {{ font-size: 26px; line-height: 1; font-weight: 800; color: #1d4ed8; }}
    .velocity-footnote {{ margin-top: 12px; color: #64748b; font-size: 12px; line-height: 1.45; }}
    .insight-grid {{
      display: grid;
      grid-template-columns: 0.9fr 1.1fr;
      gap: 20px;
      margin-bottom: 20px;
    }}
    .insight-card {{
      background: #fff;
      border-radius: 14px;
      padding: 22px 20px;
      box-shadow: 0 1px 4px rgba(0,0,0,.08);
    }}
    .chart-card canvas {{ display: block; width: 100% !important; }}
    /* ── Word cloud ──────────────────────────────────────── */
    .word-cloud {{
      background: #fff;
      border-radius: 14px;
      padding: 22px 20px;
      box-shadow: 0 1px 4px rgba(0,0,0,.08);
      margin-bottom: 20px;
    }}
    .cloud-area {{
      display: flex;
      flex-wrap: wrap;
      gap: 8px 10px;
      margin-top: 10px;
    }}
    .cloud-word {{
      border-radius: 20px;
      padding: 5px 14px;
      font-weight: 700;
      white-space: nowrap;
      transition: transform .15s;
    }}
    .cloud-word:hover {{ transform: scale(1.06); cursor: default; }}
    .cloud-pos {{ background: #dbeafe; color: #1e40af; }}
    .cloud-neg {{ background: #fee2e2; color: #991b1b; }}
    .cloud-neutral {{ background: #e5e7eb; color: #374151; }}
    /* ── Divider ─────────────────────────────────────────── */
    hr.section-sep {{
      border: none;
      border-top: 1px solid #e5e7eb;
      margin: 24px 0;
    }}
    /* ── Footer ──────────────────────────────────────────── */
    .report-footer {{
      text-align: center;
      font-size: 11px;
      color: #9ca3af;
      margin-top: 36px;
    }}
    /* ── Loading / error states ──────────────────────────── */
    .state-box {{
      text-align: center;
      padding: 48px 16px;
      color: #6b7280;
      font-size: 15px;
    }}
    .state-box .state-icon {{ font-size: 40px; margin-bottom: 12px; display: block; }}
    /* ── Print overrides ─────────────────────────────────── */
    @media print {{
      body {{ background: #fff; padding: 0; }}
      .page {{ max-width: 100%; }}
      .no-print {{ display: none !important; }}
    }}
    @media (max-width: 480px) {{
      .kpi-card .kpi-value {{ font-size: 26px; }}
    }}
    @media (max-width: 640px) {{
      .insight-grid {{ grid-template-columns: 1fr; }}
    }}
  </style>
</head>
<body>
<div class="page" id="page">
  <!-- Header -->
  <div class="header">
    <div class="logo">Lokigi</div>
    <div class="header-meta">
      <div class="period" id="hdr-period">Cargando…</div>
      <div class="biz"   id="hdr-biz"></div>
    </div>
  </div>

  <!-- Loading state -->
  <div class="state-box" id="loading-state">
    <span class="state-icon">⏳</span>
    Cargando tu reporte…
  </div>

  <!-- Error state (hidden by default) -->
  <div class="state-box" id="error-state" style="display:none;color:#b91c1c">
    <span class="state-icon">⚠️</span>
    <span id="error-msg">No se encontró el reporte para este período.</span>
  </div>

  <!-- Report body (hidden until data loads) -->
  <div id="report-body" style="display:none">

    <!-- KPI row -->
    <p class="section-title">Resumen del mes</p>
    <div class="kpi-grid">
      <div class="kpi-card">
        <span class="kpi-icon">⭐</span>
        <div class="kpi-value" id="kpi-rating">—</div>
        <div class="kpi-label">Nota media</div>
      </div>
      <div class="kpi-card green">
        <span class="kpi-icon">💬</span>
        <div class="kpi-value" id="kpi-total">—</div>
        <div class="kpi-label">Reseñas recibidas</div>
      </div>
      <div class="kpi-card orange">
        <span class="kpi-icon">🤖</span>
        <div class="kpi-value" id="kpi-ai">—</div>
        <div class="kpi-label">Respondidas por IA</div>
      </div>
      <div class="kpi-card">
        <span class="kpi-icon">⚡</span>
        <div class="kpi-value" id="kpi-speed">—</div>
        <div class="kpi-label">Tiempo de respuesta</div>
      </div>
    </div>

    <hr class="section-sep" />

    <div class="value-card">
      <p class="section-title">Response Velocity</p>
      <div class="velocity-grid">
        <div class="velocity-stat">
          <div class="label">Promedio Lokigi</div>
          <div class="value" id="velocity-current">—</div>
        </div>
        <div class="velocity-stat">
          <div class="label">Antes de Lokigi</div>
          <div class="value" id="velocity-baseline">—</div>
        </div>
        <div class="velocity-stat">
          <div class="label">Mejora</div>
          <div class="value" id="velocity-improvement">—</div>
        </div>
      </div>
      <div class="velocity-footnote" id="velocity-footnote">Sin datos suficientes para comparar velocidad de respuesta.</div>
    </div>

    <!-- Rating evolution chart -->
    <div class="chart-card">
      <p class="section-title">Evolución de la nota media</p>
      <canvas id="ratingChart" height="180"></canvas>
    </div>

    <!-- AI responses chart -->
    <div class="chart-card">
      <p class="section-title">Reseñas respondidas por la IA</p>
      <canvas id="responseChart" height="160"></canvas>
    </div>

    <hr class="section-sep" />

    <div class="insight-grid">
      <div class="insight-card">
        <p class="section-title">Sentiment Snapshot</p>
        <canvas id="sentimentSnapshotChart" height="220"></canvas>
      </div>

      <!-- Word cloud — sentiment -->
      <div class="word-cloud" style="margin-bottom:0">
        <p class="section-title">Keyword Cloud</p>
        <div class="cloud-area" id="cloud-area">
          <span style="color:#9ca3af;font-size:13px">Sin conceptos detectados este mes</span>
        </div>
      </div>
    </div>

    <!-- Sentiment bar chart -->
    <div class="chart-card" id="sentiment-chart-card" style="display:none">
      <p class="section-title">Temas más mencionados este mes</p>
      <canvas id="sentimentChart" height="220"></canvas>
    </div>

  </div><!-- /report-body -->

  <div class="report-footer" id="report-footer" style="display:none">
    Generado por Lokigi · {period_label} · <a href="javascript:window.print()" class="no-print" style="color:#6b7280">Imprimir / Guardar PDF</a> · <span id="pdf-download-slot" class="no-print">Preparando PDF descargable…</span>
  </div>
</div>

<script>
(function () {{
  const USER_ID = "{user_id}";
  const YEAR    = {year};
  const MONTH   = {month};

  const MONTHS_ES = ["","Enero","Febrero","Marzo","Abril","Mayo","Junio",
                     "Julio","Agosto","Septiembre","Octubre","Noviembre","Diciembre"];

  // ── UI helpers ────────────────────────────────────────────────────────────
  function show(id)  {{ document.getElementById(id).style.display = ""; }}
  function hide(id)  {{ document.getElementById(id).style.display = "none"; }}
  function text(id, v) {{ document.getElementById(id).textContent = v; }}

  function showError(msg) {{
    hide("loading-state");
    text("error-msg", msg || "No se encontró el reporte para este período.");
    show("error-state");
  }}

  // ── Fetch helpers ─────────────────────────────────────────────────────────
  async function fetchJSON(url) {{
    const r = await fetch(url);
    if (!r.ok) throw new Error("HTTP " + r.status);
    return r.json();
  }}

  // ── Star rendering ────────────────────────────────────────────────────────
  function stars(v) {{
    if (v == null) return "—";
    const full = Math.round(v);
    return "★".repeat(full) + "☆".repeat(5 - full) + " " + v.toFixed(1);
  }}

  function formatMinutes(mins) {{
    if (mins == null) return "—";
    if (mins < 60) return Math.round(mins) + " min";
    if (mins < 1440) return (mins / 60).toFixed(1) + " h";
    return (mins / 1440).toFixed(1) + " d";
  }}

  // ── Rating evolution chart ────────────────────────────────────────────────
  function drawRatingChart(history) {{
    const labels = history.map(h => MONTHS_ES[h.month].slice(0,3) + " " + String(h.year).slice(2));
    const data   = history.map(h => h.avg_rating);

    // Mark the current period
    const pointColors = history.map(h =>
      h.year === YEAR && h.month === MONTH ? "#1a56db" : "rgba(26,86,219,.35)"
    );
    const pointR = history.map(h =>
      h.year === YEAR && h.month === MONTH ? 7 : 4
    );

    new Chart(document.getElementById("ratingChart"), {{
      type: "line",
      data: {{
        labels,
        datasets: [{{
          label: "Nota media",
          data,
          fill: true,
          tension: 0.4,
          borderColor: "#1a56db",
          backgroundColor: "rgba(26,86,219,.08)",
          pointBackgroundColor: pointColors,
          pointRadius: pointR,
          pointHoverRadius: 8,
        }}]
      }},
      options: {{
        plugins: {{ legend: {{ display: false }} }},
        scales: {{
          y: {{
            min: 1, max: 5,
            grid: {{ color: "#f3f4f6" }},
            ticks: {{ stepSize: 1, callback: v => v + "★" }}
          }},
          x: {{ grid: {{ display: false }} }}
        }},
        responsive: true,
        maintainAspectRatio: true,
      }}
    }});
  }}

  // ── AI response chart ─────────────────────────────────────────────────────
  function drawResponseChart(history) {{
    const labels = history.map(h => MONTHS_ES[h.month].slice(0,3) + " " + String(h.year).slice(2));
    const data   = history.map(h => h.total_reviews);

    new Chart(document.getElementById("responseChart"), {{
      type: "bar",
      data: {{
        labels,
        datasets: [{{
          label: "Reseñas recibidas",
          data,
          backgroundColor: history.map(h =>
            h.year === YEAR && h.month === MONTH ? "#1a56db" : "rgba(26,86,219,.25)"
          ),
          borderRadius: 6,
          borderSkipped: false,
        }}]
      }},
      options: {{
        plugins: {{ legend: {{ display: false }} }},
        scales: {{
          y: {{
            beginAtZero: true,
            grid: {{ color: "#f3f4f6" }},
            ticks: {{ precision: 0 }}
          }},
          x: {{ grid: {{ display: false }} }}
        }},
        responsive: true,
        maintainAspectRatio: true,
      }}
    }});
  }}

  // ── Word cloud ────────────────────────────────────────────────────────────
  function drawWordCloud(topConcepts) {{
    const area = document.getElementById("cloud-area");
    const all = topConcepts || [];
    if (!all.length) return;

    const maxCount = Math.max(...all.map(c => c.count), 1);

    area.innerHTML = "";
    all.forEach(c => {{
      const size  = 12 + Math.round((c.count / maxCount) * 16); // 12px – 28px
      const span  = document.createElement("span");
      span.className = "cloud-word cloud-neutral";
      span.style.fontSize = size + "px";
      span.title = c.count + " mención" + (c.count !== 1 ? "es" : "") + " · " + c.pct + "%";
      span.textContent = c.concept;
      area.appendChild(span);
    }});
  }}

  function drawSentimentSnapshot(snapshot) {{
    if (!snapshot || !snapshot.labels || !snapshot.labels.length) return;

    new Chart(document.getElementById("sentimentSnapshotChart"), {{
      type: "doughnut",
      data: {{
        labels: snapshot.labels,
        datasets: [{{
          data: snapshot.counts,
          backgroundColor: ["#60a5fa", "#cbd5e1", "#f87171"],
          borderWidth: 0,
        }}],
      }},
      options: {{
        plugins: {{
          legend: {{ position: "bottom", labels: {{ boxWidth: 12 }} }},
          tooltip: {{
            callbacks: {{
              label: (ctx) => `${{ctx.label}}: ${{ctx.raw}} reseñas (${{snapshot.percentages?.[ctx.dataIndex] ?? 0}}%)`
            }}
          }}
        }},
        cutout: "62%",
        responsive: true,
        maintainAspectRatio: true,
      }}
    }});
  }}

  function renderResponseVelocity(valueMetrics) {{
    const velocity = (valueMetrics || {{}}).response_velocity || {{}};
    text("velocity-current", formatMinutes(velocity.current_avg_minutes));
    text("velocity-baseline", formatMinutes(velocity.baseline_avg_minutes));
    text("velocity-improvement", velocity.improvement_pct != null ? velocity.improvement_pct.toFixed(1) + "%" : "—");

    const note = document.getElementById("velocity-footnote");
    if (velocity.current_avg_minutes == null) {{
      note.textContent = "Todavía no hay suficientes respuestas este mes para calcular velocidad actual.";
      return;
    }}

    const baselineLabel = velocity.baseline_source === "google_history"
      ? "Comparado contra tiempos históricos detectados en Google antes de usar Lokigi."
      : "Comparado contra una referencia de 24 h por falta de historial previo usable en Google.";

    note.textContent = `${{baselineLabel}} Muestras actuales: ${{velocity.current_sample_size || 0}} · baseline: ${{velocity.baseline_sample_size || 0}}.`;
  }}

  // ── Sentiment bar chart ───────────────────────────────────────────────────
  function drawSentimentChart(sentiment) {{
    const cd = (sentiment || {{}}).chart_data;
    if (!cd || !cd.labels || !cd.labels.length) return;

    show("sentiment-chart-card");
    new Chart(document.getElementById("sentimentChart"), {{
      type: "bar",
      data: {{
        labels: cd.labels,
        datasets: [
          {{
            label: "Positivo",
            data: cd.positive,
            backgroundColor: "#93c5fd",
            borderRadius: 5,
          }},
          {{
            label: "Negativo",
            data: cd.negative,
            backgroundColor: "#fca5a5",
            borderRadius: 5,
          }},
        ]
      }},
      options: {{
        indexAxis: "y",
        plugins: {{
          legend: {{ position: "top", labels: {{ boxWidth: 12 }} }}
        }},
        scales: {{
          x: {{
            beginAtZero: true,
            grid: {{ color: "#f3f4f6" }},
            ticks: {{ precision: 0 }}
          }},
          y: {{ grid: {{ display: false }} }}
        }},
        responsive: true,
        maintainAspectRatio: true,
      }}
    }});
  }}

  // ── Main loader ───────────────────────────────────────────────────────────
  async function load() {{
    try {{
      const [report, history, pdfMeta] = await Promise.all([
        fetchJSON(`/api/reports/monthly?user_id=${{USER_ID}}&year=${{YEAR}}&month=${{MONTH}}`),
        fetchJSON(`/api/reports/history?user_id=${{USER_ID}}`),
        fetchJSON(`/api/reports/monthly-pdf?user_id=${{USER_ID}}&year=${{YEAR}}&month=${{MONTH}}`).catch(() => null),
      ]);

      // Header
      text("hdr-period", MONTHS_ES[MONTH] + " " + YEAR);
      text("hdr-biz", report.business_name || "");

      // KPIs
      const kpis = report.kpis || {{}};
      const valueMetrics = report.value_metrics || {{}};
      text("kpi-rating", kpis.avg_rating != null ? kpis.avg_rating.toFixed(1) + "★" : "—");
      text("kpi-total",  kpis.total_reviews ?? "—");

      const aiCount = kpis.response_rate_pct != null
        ? Math.round((kpis.response_rate_pct / 100) * (kpis.total_reviews || 0))
        : null;
      text("kpi-ai",    aiCount != null ? aiCount : "—");

      const speed = kpis.avg_response_time_minutes;
      if (speed != null) {{
        text("kpi-speed", speed < 60
          ? Math.round(speed) + " min"
          : (speed / 60).toFixed(1) + " h");
      }}

      renderResponseVelocity(valueMetrics);

      // Charts
      if (history.length > 0) {{
        drawRatingChart(history);
        drawResponseChart(history);
      }}

      // Sentiment
      const sentiment = report.sentiment || {{}};
      drawSentimentSnapshot(valueMetrics.sentiment_snapshot || sentiment.sentiment_snapshot);
      drawWordCloud((valueMetrics.keyword_cloud || {{}}).top_concepts || sentiment.top_concepts);
      drawSentimentChart(sentiment);

      hide("loading-state");
      show("report-body");
      show("report-footer");

      const downloadSlot = document.getElementById("pdf-download-slot");
      if (downloadSlot) {{
        if (pdfMeta && pdfMeta.signed_url && pdfMeta.status === "ready") {{
          const expiresCopy = pdfMeta.expires_at ? ` (expira: ${{new Date(pdfMeta.expires_at).toLocaleString()}})` : "";
          downloadSlot.innerHTML = `<a href="${{pdfMeta.signed_url}}" target="_blank" rel="noreferrer" style="color:#1a56db">Descargar PDF generado</a>${{expiresCopy}}`;
        }} else if (pdfMeta && pdfMeta.status === "failed") {{
          downloadSlot.textContent = "No se pudo generar el PDF automático. Puedes usar Imprimir / Guardar PDF.";
        }} else {{
          downloadSlot.textContent = "PDF automático en generación. Refresca en unos minutos.";
        }}
      }}

    }} catch (err) {{
      showError(err.message.includes("404")
        ? "No se encontró el reporte para este período. El reporte se genera automáticamente el día 1 de cada mes."
        : "Error al cargar el reporte. Intenta de nuevo más tarde."
      );
    }}
  }}

  load();
}})();
</script>
</body>
</html>"""
    return HTMLResponse(html)


@app.get("/starter/approvals", response_class=HTMLResponse)
def starter_approvals_page(user_id: UUID) -> HTMLResponse:
    """Bootstrap 5 interface for human review of AI-suggested replies."""
    html = f"""\
<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Aprobación de Respuestas | Lokigi</title>
  <link rel="stylesheet"
        href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css"
        crossorigin="anonymous" />
  <style>
    body {{ background: #f5f7fa; }}
    .review-card {{ border-left: 4px solid #0d6efd; }}
    .badge-stars {{ font-size: .75rem; }}
    .badge-schedule {{ font-size: .72rem; }}
    .reply-textarea {{ font-size: .9rem; resize: vertical; min-height: 90px; }}
    .spinner-border {{ width: 1rem; height: 1rem; border-width: .15em; }}
    .sent-badge {{ display: none; }}
    .toast-container {{ position: fixed; bottom: 1rem; right: 1rem; z-index: 9999; }}
  </style>
</head>
<body>
<div class="container py-4">
  <div class="d-flex align-items-center justify-content-between mb-4">
    <div>
      <h1 class="h4 mb-0">Aprobación de Respuestas</h1>
      <small class="text-muted">Solo respuestas sugeridas por IA pendientes de envío</small>
      <div id="auto-mode-indicator" class="mt-2"></div>
    </div>
    <a href="/starter/dashboard?user_id={user_id}" class="btn btn-sm btn-outline-secondary">&larr; Dashboard</a>
  </div>

  <div id="loading" class="text-center py-5">
    <div class="spinner-border text-primary" role="status"></div>
    <p class="mt-2 text-muted">Cargando reseñas pendientes…</p>
  </div>
  <div id="empty-state" class="text-center py-5 d-none">
    <p class="fs-5">&#10003; No hay respuestas pendientes de aprobación.</p>
  </div>
  <div id="cards-container" class="d-none"></div>
</div>

<!-- Toast container -->
<div class="toast-container" id="toast-container"></div>

<!-- Card template (hidden) -->
<template id="review-tpl">
  <div class="card review-card shadow-sm mb-4" data-id="">
    <div class="card-body">
      <div class="d-flex justify-content-between align-items-start mb-2">
        <div>
          <strong class="js-author"></strong>
          <span class="badge bg-warning text-dark ms-2 badge-stars js-stars"></span>
          <span class="badge bg-info text-dark ms-2 badge-schedule d-none js-eta"></span>
        </div>
        <span class="badge bg-success sent-badge">Enviado &#10003;</span>
      </div>
      <p class="text-secondary js-comment mb-3" style="font-size:.9rem"></p>
      <label class="form-label fw-semibold">Respuesta sugerida por IA</label>
      <textarea class="form-control reply-textarea js-textarea" rows="4"></textarea>
      <div class="d-flex gap-2 mt-3 flex-wrap">
        <button class="btn btn-primary btn-sm js-approve">
          <span class="spinner-border d-none me-1 js-spin"></span>
          Aprobar y Enviar
        </button>
        <button class="btn btn-outline-secondary btn-sm js-regenerate">
          <span class="spinner-border d-none me-1 js-regen-spin"></span>
          Regenerar
        </button>
      </div>
      <div class="alert alert-danger mt-2 d-none js-error" role="alert"></div>
    </div>
  </div>
</template>

<script>
const USER_ID = "{user_id}";

function stars(n) {{
  return "★".repeat(n || 0) + "☆".repeat(Math.max(0, 5 - (n || 0)));
}}

function toast(msg, type = "success") {{
  const t = document.createElement("div");
  t.className = `toast align-items-center text-bg-${{type}} border-0 show`;
  t.setAttribute("role", "alert");
  t.innerHTML = `<div class="d-flex"><div class="toast-body">${{msg}}</div>
    <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button></div>`;
  document.getElementById("toast-container").appendChild(t);
  setTimeout(() => t.remove(), 5000);
}}

async function loadPending() {{
  try {{
    const res = await fetch(`/api/reviews/pending?user_id=${{USER_ID}}`);
    if (!res.ok) throw new Error(`HTTP ${{res.status}}`);
    const reviews = await res.json();
    renderCards(reviews);
  }} catch (e) {{
    document.getElementById("loading").innerHTML =
      `<div class="alert alert-danger">Error cargando reseñas: ${{e.message}}</div>`;
  }}
}}

function renderCards(reviews) {{
  document.getElementById("loading").classList.add("d-none");

  const indicator = document.getElementById("auto-mode-indicator");
  if (reviews.length) {{
    const schedule = reviews[0].response_schedule || "instant";
    if (schedule === "delay_1h") {{
      indicator.innerHTML = '<span class="badge text-bg-warning">Modo automático: espera 1 hora antes de publicar</span>';
    }} else {{
      indicator.innerHTML = '<span class="badge text-bg-success">Modo automático: envío inmediato</span>';
    }}
  }}

  if (!reviews.length) {{
    document.getElementById("empty-state").classList.remove("d-none");
    return;
  }}
  const container = document.getElementById("cards-container");
  container.classList.remove("d-none");
  const tpl = document.getElementById("review-tpl");
  reviews.forEach(r => {{
    const node = tpl.content.cloneNode(true);
    const card = node.querySelector(".card");
    card.dataset.id = r.id;
    card.querySelector(".js-author").textContent = r.author;
    card.querySelector(".js-stars").textContent = stars(r.rating);
    card.querySelector(".js-comment").textContent = r.comment || "(sin comentario)";
    card.querySelector(".js-textarea").value = r.suggested_reply;

    const etaEl = card.querySelector(".js-eta");
    if (r.response_schedule === "delay_1h" && r.auto_send_eta_minutes != null) {{
      etaEl.textContent = r.auto_send_eta_minutes > 0
        ? `Auto-envío en ${{r.auto_send_eta_minutes}} min`
        : "Auto-envío habilitado";
      etaEl.classList.remove("d-none");
    }}

    card.querySelector(".js-approve").addEventListener("click", () => handleApprove(card));
    card.querySelector(".js-regenerate").addEventListener("click", () => handleRegenerate(card));
    container.appendChild(node);
  }});
}}

async function handleApprove(card) {{
  const id = card.dataset.id;
  const text = card.querySelector(".js-textarea").value.trim();
  if (!text) {{ toast("La respuesta no puede estar vacía.", "warning"); return; }}
  const btn = card.querySelector(".js-approve");
  const spin = card.querySelector(".js-spin");
  const errEl = card.querySelector(".js-error");
  btn.disabled = true; spin.classList.remove("d-none");
  errEl.classList.add("d-none");
  try {{
    const res = await fetch(`/api/reviews/${{id}}/approve`, {{
      method: "POST",
      headers: {{ "Content-Type": "application/json" }},
      body: JSON.stringify({{ reply_text: text }}),
    }});
    if (res.status === 409) {{
      throw new Error("Esta reseña ya tiene una respuesta publicada en Google.");
    }}
    if (!res.ok) {{
      const err = await res.json().catch(() => ({{}}));
      throw new Error(err.detail || `Error ${{res.status}}`);
    }}
    card.querySelector(".sent-badge").style.display = "inline-block";
    card.querySelector(".js-textarea").disabled = true;
    btn.disabled = true;
    card.querySelector(".js-regenerate").disabled = true;
    toast("Respuesta enviada correctamente ✓");
  }} catch (e) {{
    errEl.textContent = e.message;
    errEl.classList.remove("d-none");
    btn.disabled = false;
  }} finally {{
    spin.classList.add("d-none");
  }}
}}

async function handleRegenerate(card) {{
  const id = card.dataset.id;
  const btn = card.querySelector(".js-regenerate");
  const spin = card.querySelector(".js-regen-spin");
  const errEl = card.querySelector(".js-error");
  btn.disabled = true; spin.classList.remove("d-none");
  errEl.classList.add("d-none");
  try {{
    const res = await fetch(`/api/reviews/${{id}}/regenerate`, {{ method: "POST" }});
    if (!res.ok) {{
      const err = await res.json().catch(() => ({{}}));
      throw new Error(err.detail || `Error ${{res.status}}`);
    }}
    const data = await res.json();
    card.querySelector(".js-textarea").value = data.suggested_reply;
    toast("Respuesta regenerada.", "info");
  }} catch (e) {{
    errEl.textContent = e.message;
    errEl.classList.remove("d-none");
  }} finally {{
    btn.disabled = false; spin.classList.add("d-none");
  }}
}}

loadPending();
</script>
<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"
        crossorigin="anonymous"></script>
</body>
</html>
"""
    return HTMLResponse(html)


@app.post("/webhooks/google/reviews")
async def webhook_google_reviews(
    body: dict,
    authorization: str = Header(default="", alias="Authorization"),
    x_webhook_secret: str = Header(default="", alias="X-Webhook-Secret"),
    db: Session = Depends(get_db),
) -> dict[str, str]:
    if settings.webhook_shared_secret and x_webhook_secret != settings.webhook_shared_secret:
        raise HTTPException(status_code=401, detail="Invalid webhook secret")

    verify_pubsub_jwt(authorization)
    payload = parse_pubsub_push(body)

    try:
        review: Review = await store_new_review_from_webhook(db=db, webhook_payload=payload)
    except HTTPException as exc:
        if exc.status_code == 202:
            return {"status": "ignored"}
        raise

    task_id: str | None = None
    processing_mode = "celery"
    try:
      async_result = process_google_review.delay(str(review.id))
      task_id = async_result.id
    except Exception:
      processing_mode = "inline-fallback"
      logger.exception("Falling back to inline review processing for review_id=%s", review.review_id)
      review = await process_review_workflow(db=db, review_id=review.id)

    response = {
      "status": "queued" if processing_mode == "celery" else "processed",
      "review_id": review.review_id,
      "location_id": review.location_id,
      "task_id": task_id,
      "processing_mode": processing_mode,
    }

    if processing_mode == "inline-fallback":
      response["decision_action"] = review.reply_action
      response["detected_language"] = review.reply_detected_language
      if review.reply_action == "AUTO_REPLY":
        response["public_reply"] = review.reply_public_text
      elif review.reply_action == "ALERT":
        response["alert_priority"] = review.reply_alert_priority
        response["alert_summary"] = review.reply_alert_summary

    return response


@app.post("/webhooks/google-reviews")
async def webhook_google_reviews_queue_only(
  body: dict,
  authorization: str = Header(default="", alias="Authorization"),
  x_webhook_secret: str = Header(default="", alias="X-Webhook-Secret"),
) -> dict[str, Any]:
  if settings.webhook_shared_secret and x_webhook_secret != settings.webhook_shared_secret:
    raise HTTPException(status_code=401, detail="Invalid webhook secret")

  verify_pubsub_jwt(authorization)
  task_payload = build_review_processing_task_payload(body)
  async_result = process_reviews.delay(task_payload)
  return {
    "status": "queued",
    "queue": "process_reviews",
    "task_id": async_result.id,
    "review_id": task_payload.get("review_id"),
    "rating": task_payload.get("rating"),
    "comment": task_payload.get("comment"),
  }

