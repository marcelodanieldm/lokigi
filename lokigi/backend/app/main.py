from contextlib import asynccontextmanager
from typing import Any
from uuid import UUID

from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from starlette.middleware.trustedhost import TrustedHostMiddleware
from sqlalchemy import select
from sqlalchemy.orm import Session

from . import database
from .config import settings
from .database import Base, get_db
from .models import GoogleConnection, Review
from pydantic import BaseModel

from .services import (
    OAuthStateManager,
    build_google_oauth_url,
    get_pending_approvals,
    parse_pubsub_push,
    regenerate_review_reply,
    send_review_reply,
    store_new_review_from_webhook,
    upsert_google_connection,
    verify_pubsub_jwt,
)
from .sentiment_analysis import analyze_monthly_sentiment
from .monthly_report_worker import build_scheduler


class ApproveReplyRequest(BaseModel):
    reply_text: str


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=database.engine)
    scheduler = build_scheduler()
    scheduler.start()
    yield
    scheduler.shutdown(wait=False)


app = FastAPI(title=settings.app_name, lifespan=lifespan)
app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.parsed_allowed_hosts())


def render_starter_onboarding_html(user_id: UUID, location_id: str, connect_url: str) -> str:
    return f"""
<!doctype html>
<html lang=\"es\">
    <head>
        <meta charset=\"utf-8\" />
        <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
        <title>Plan Starter | Onboarding</title>
        <style>
            :root {{
                --bg: #f3f7f6;
                --card: #ffffff;
                --text: #1f2937;
                --muted: #6b7280;
                --accent: #0f766e;
                --accent-2: #115e59;
            }}
            * {{ box-sizing: border-box; }}
            body {{
                margin: 0;
                font-family: "Segoe UI", "Helvetica Neue", sans-serif;
                color: var(--text);
                background:
                    radial-gradient(circle at 10% 10%, #d1fae5 0%, transparent 35%),
                    radial-gradient(circle at 85% 20%, #cffafe 0%, transparent 30%),
                    var(--bg);
                min-height: 100vh;
                display: grid;
                place-items: center;
                padding: 24px;
            }}
            .card {{
                width: min(680px, 100%);
                background: var(--card);
                border: 1px solid #e5e7eb;
                border-radius: 20px;
                box-shadow: 0 10px 35px rgba(15, 23, 42, 0.08);
                padding: 28px;
            }}
            .pill {{
                display: inline-block;
                background: #ecfeff;
                color: #155e75;
                border: 1px solid #a5f3fc;
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
            p {{ margin: 0 0 10px; color: var(--muted); font-size: 16px; }}
            .meta {{
                margin-top: 14px;
                padding: 12px;
                border-radius: 10px;
                background: #f9fafb;
                border: 1px dashed #d1d5db;
                color: #374151;
                font-size: 13px;
            }}
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
                font-weight: 700;
                font-size: 16px;
                color: #ffffff;
                background: linear-gradient(135deg, var(--accent), var(--accent-2));
            }}
            .hint {{ margin-top: 10px; font-size: 12px; color: #6b7280; }}
        </style>
    </head>
    <body>
        <main class=\"card\">
            <span class=\"pill\">PLAN STARTER</span>
            <h1>Conecta tu negocio en menos de 3 clics</h1>
            <p>Activa tu canal de Google y comienza a centralizar tus reseñas automáticamente.</p>
            <div class=\"meta\">
                <div><strong>User ID:</strong> {user_id}</div>
                <div><strong>Location ID:</strong> {location_id}</div>
            </div>
            <a class=\"cta\" href=\"{connect_url}\">Conectar Google Maps</a>
            <div class=\"hint\">Click 1: conectar · Click 2: autorizar en Google · Click 3: dashboard listo</div>
        </main>
    </body>
</html>
"""


def render_starter_dashboard_html(user_id: UUID, connection: GoogleConnection | None, recent_reviews: list[Review]) -> str:
    status_text = "Conectado" if connection else "Sin conectar"
    status_color = "#047857" if connection else "#b91c1c"
    subtitle = (
        f"Cuenta: {connection.business_name or connection.google_account_name} · Location: {connection.location_id}"
        if connection
        else "Conecta Google Maps para empezar a recibir reseñas."
    )

    reviews_html = "".join(
        f"""
        <li class=\"review-item\">
            <div class=\"review-top\">
                <strong>{review.author_display_name or 'Cliente'}</strong>
                <span>{review.rating or 0}★</span>
            </div>
            <p>{(review.comment or 'Sin comentario.')[:240]}</p>
        </li>
        """
        for review in recent_reviews
    )
    if not reviews_html:
        reviews_html = '<li class="empty">Todavía no hay reseñas recibidas.</li>'

    return f"""
<!doctype html>
<html lang=\"es\">
    <head>
        <meta charset=\"utf-8\" />
        <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
        <title>Starter Dashboard</title>
        <style>
            :root {{
                --bg: #f8fafc;
                --card: #ffffff;
                --text: #111827;
                --muted: #6b7280;
            }}
            * {{ box-sizing: border-box; }}
            body {{ margin: 0; background: var(--bg); color: var(--text); font-family: "Segoe UI", "Helvetica Neue", sans-serif; }}
            .wrap {{ max-width: 900px; margin: 0 auto; padding: 20px; }}
            .header {{ background: var(--card); border: 1px solid #e5e7eb; border-radius: 16px; padding: 18px; box-shadow: 0 6px 20px rgba(15, 23, 42, 0.06); }}
            .status {{ display: inline-block; padding: 5px 10px; border-radius: 999px; font-size: 12px; font-weight: 700; color: white; background: {status_color}; }}
            h1 {{ margin: 12px 0 8px; font-size: clamp(22px, 4vw, 30px); }}
            .sub {{ color: var(--muted); margin: 0; }}
            .meta {{ margin-top: 8px; color: #475569; font-size: 12px; }}
            .panel {{ margin-top: 18px; background: var(--card); border: 1px solid #e5e7eb; border-radius: 16px; padding: 16px; }}
            .panel h2 {{ margin: 0 0 12px; font-size: 18px; }}
            .reviews {{ list-style: none; margin: 0; padding: 0; display: grid; gap: 10px; }}
            .review-item {{ border: 1px solid #e5e7eb; border-radius: 12px; padding: 12px; background: #fcfcfd; }}
            .review-top {{ display: flex; align-items: center; justify-content: space-between; margin-bottom: 6px; }}
            .review-item p {{ margin: 0; color: #4b5563; font-size: 14px; line-height: 1.4; }}
            .empty {{ border: 1px dashed #cbd5e1; border-radius: 12px; padding: 12px; color: var(--muted); }}
        </style>
    </head>
    <body>
        <div class=\"wrap\">
            <section class=\"header\">
                <span class=\"status\">{status_text}</span>
                <h1>Starter Dashboard</h1>
                <p class=\"sub\">{subtitle}</p>
                <div class=\"meta\">User ID: {user_id}</div>
            </section>
            <section class=\"panel\">
                <h2>Ultimas 5 reseñas</h2>
                <ul class=\"reviews\">{reviews_html}</ul>
            </section>
        </div>
    </body>
</html>
"""


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/starter/onboarding", response_class=HTMLResponse)
def starter_onboarding(user_id: UUID, location_id: str) -> HTMLResponse:
    connect_url = f"/starter/connect-google?user_id={user_id}&location_id={location_id}"
    return HTMLResponse(render_starter_onboarding_html(user_id=user_id, location_id=location_id, connect_url=connect_url))


@app.get("/starter/connect-google")
def starter_connect_google(user_id: UUID, location_id: str) -> RedirectResponse:
    oauth_url = build_google_oauth_url(
        user_id=str(user_id),
        location_id=location_id,
        extra_state={"starter_flow": True},
    )
    return RedirectResponse(url=oauth_url)


@app.get("/starter/dashboard", response_class=HTMLResponse)
def starter_dashboard(user_id: UUID, db: Session = Depends(get_db)) -> HTMLResponse:
    connection = db.scalar(select(GoogleConnection).where(GoogleConnection.user_id == user_id))

    recent_reviews = db.scalars(
        select(Review)
        .join(GoogleConnection, Review.connection_id == GoogleConnection.id)
        .where(GoogleConnection.user_id == user_id)
        .order_by(Review.created_at.desc())
        .limit(5)
    ).all()

    return HTMLResponse(render_starter_dashboard_html(user_id=user_id, connection=connection, recent_reviews=recent_reviews))


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
        return RedirectResponse(url=f"/starter/dashboard?user_id={state_payload['user_id']}")

    return {
        "status": "linked",
        "user_id": str(connection.user_id),
        "location_id": connection.location_id,
    }


# ── Review Approval API ──────────────────────────────────────────────────────

@app.get("/api/reviews/pending")
def api_reviews_pending(user_id: UUID, db: Session = Depends(get_db)) -> list[dict[str, Any]]:
    """List AUTO_REPLY reviews pending human approval for the given user."""
    reviews = get_pending_approvals(db, str(user_id))
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

    <!-- Word cloud — sentiment -->
    <div class="word-cloud">
      <p class="section-title">Qué dicen tus clientes</p>
      <div class="cloud-area" id="cloud-area">
        <span style="color:#9ca3af;font-size:13px">Sin datos de sentimiento</span>
      </div>
    </div>

    <!-- Sentiment bar chart -->
    <div class="chart-card" id="sentiment-chart-card" style="display:none">
      <p class="section-title">Temas más mencionados este mes</p>
      <canvas id="sentimentChart" height="220"></canvas>
    </div>

  </div><!-- /report-body -->

  <div class="report-footer" id="report-footer" style="display:none">
    Generado por Lokigi · {period_label} · <a href="javascript:window.print()" class="no-print" style="color:#6b7280">Imprimir / Guardar PDF</a>
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
  function drawWordCloud(sentiment) {{
    const area = document.getElementById("cloud-area");
    const pos  = sentiment.positive_concepts || [];
    const neg  = sentiment.negative_concepts || [];

    if (!pos.length && !neg.length) return;

    // Combine and normalise sizes relative to max count
    const all = [
      ...pos.map(c => ({{ ...c, polarity: "pos" }})),
      ...neg.map(c => ({{ ...c, polarity: "neg" }})),
    ];
    const maxCount = Math.max(...all.map(c => c.count), 1);

    area.innerHTML = "";
    // Shuffle for variety
    all.sort(() => Math.random() - 0.5);

    all.forEach(c => {{
      const size  = 12 + Math.round((c.count / maxCount) * 16); // 12px – 28px
      const span  = document.createElement("span");
      span.className = "cloud-word " + (c.polarity === "pos" ? "cloud-pos" : "cloud-neg");
      span.style.fontSize = size + "px";
      span.title = c.count + " mención" + (c.count !== 1 ? "es" : "") + " · " + c.pct + "%";
      span.textContent = c.concept;
      area.appendChild(span);
    }});
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
      const [report, history] = await Promise.all([
        fetchJSON(`/api/reports/monthly?user_id=${{USER_ID}}&year=${{YEAR}}&month=${{MONTH}}`),
        fetchJSON(`/api/reports/history?user_id=${{USER_ID}}`),
      ]);

      // Header
      text("hdr-period", MONTHS_ES[MONTH] + " " + YEAR);
      text("hdr-biz", report.business_name || "");

      // KPIs
      const kpis = report.kpis || {{}};
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

      // Charts
      if (history.length > 0) {{
        drawRatingChart(history);
        drawResponseChart(history);
      }}

      // Sentiment
      const sentiment = report.sentiment || {{}};
      drawWordCloud(sentiment);
      drawSentimentChart(sentiment);

      hide("loading-state");
      show("report-body");
      show("report-footer");

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

    response = {
        "status": "stored",
        "review_id": review.review_id,
        "location_id": review.location_id,
        "decision_action": review.reply_action,
        "detected_language": review.reply_detected_language,
    }

    if review.reply_action == "AUTO_REPLY":
        response["public_reply"] = review.reply_public_text
    elif review.reply_action == "ALERT":
        response["alert_priority"] = review.reply_alert_priority
        response["alert_summary"] = review.reply_alert_summary

    return response
