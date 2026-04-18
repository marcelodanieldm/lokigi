from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.responses import RedirectResponse
from starlette.middleware.trustedhost import TrustedHostMiddleware
from sqlalchemy.orm import Session

from . import database
from .config import settings
from .database import Base, get_db
from .models import Review
from .services import (
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


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/oauth/google/start")
def oauth_google_start(user_id: str, location_id: str) -> RedirectResponse:
    if not settings.google_client_id or not settings.google_client_secret:
        raise HTTPException(status_code=500, detail="Google OAuth is not configured")
    url = build_google_oauth_url(user_id=user_id, location_id=location_id)
    return RedirectResponse(url=url)


@app.get("/oauth/google/callback")
async def oauth_google_callback(code: str, state: str, db: Session = Depends(get_db)) -> dict[str, str]:
    connection = await upsert_google_connection(db=db, code=code, state=state)
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

    return {"status": "stored", "review_id": review.review_id, "location_id": review.location_id}
