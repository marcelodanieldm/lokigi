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
from .services import (
    OAuthStateManager,
    build_google_oauth_url,
    parse_pubsub_push,
    store_new_review_from_webhook,
    upsert_google_connection,
    verify_pubsub_jwt,
)


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=database.engine)
    yield


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
