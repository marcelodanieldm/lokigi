"""routes/photo_optimizer_routes.py — Smart Upload endpoint with SSE checklist."""

from __future__ import annotations

import asyncio
import base64
import json
import logging
from typing import AsyncGenerator
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.requests import Request
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models import PhotoOptimizationJob, User
from app.photo_optimizer_service import optimize_photo

router = APIRouter(prefix="/photo", tags=["photo-optimizer"])
templates = Jinja2Templates(directory="app/templates")

logger = logging.getLogger(__name__)

_MAX_FILE_SIZE_MB = 10
_MAX_FILE_SIZE_BYTES = _MAX_FILE_SIZE_MB * 1024 * 1024
_ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp"}


# ──────────────────────────────────────────────────────────────────────────────
# HTML page
# ──────────────────────────────────────────────────────────────────────────────


@router.get("/optimizer", response_class=HTMLResponse, summary="Smart Upload page")
def photo_optimizer_page(request: Request, user_id: UUID, db: Session = Depends(get_db)):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return templates.TemplateResponse(
        "photo_optimizer.html",
        {"request": request, "user_id": str(user_id)},
    )


# ──────────────────────────────────────────────────────────────────────────────
# SSE streaming optimize endpoint
# ──────────────────────────────────────────────────────────────────────────────


def _sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


async def _optimize_stream(
    image_bytes: bytes,
    filename: str,
    lat: float | None,
    lon: float | None,
    keywords: list[str],
    user_id: UUID,
    db: Session,
) -> AsyncGenerator[str, None]:

    yield _sse("step", {"step": "resize", "status": "running", "msg": "Analizando y redimensionando imagen…"})
    await asyncio.sleep(0)

    result = await optimize_photo(
        image_bytes,
        lat=lat,
        lon=lon,
        keywords=keywords,
        use_llm=True,
        settings=settings,
    )

    yield _sse("step", {
        "step": "resize",
        "status": "done" if result["resized"] else "skipped",
        "msg": (
            f"Tamaño optimizado: {result['original_width']}×{result['original_height']} → "
            f"{result['output_width']}×{result['output_height']} px"
            if result["resized"]
            else f"Tamaño ya óptimo ({result['original_width']}×{result['original_height']} px)"
        ),
    })

    yield _sse("step", {
        "step": "gps",
        "status": "done" if result["gps_injected"] else "skipped",
        "msg": (
            f"Coordenadas GPS inyectadas ({lat:.5f}, {lon:.5f})"
            if result["gps_injected"]
            else "GPS omitido – no se proporcionaron coordenadas"
        ),
    })

    yield _sse("step", {
        "step": "alt",
        "status": "done",
        "msg": f"SEO Alt-text generado [{result['alt_text_source']}]",
        "alt_text": result["alt_text"],
    })

    # Persist job log
    try:
        job = PhotoOptimizationJob(
            user_id=user_id,
            original_filename=filename,
            original_width=result["original_width"],
            original_height=result["original_height"],
            output_width=result["output_width"],
            output_height=result["output_height"],
            gps_lat=lat,
            gps_lon=lon,
            gps_injected=result["gps_injected"],
            resized=result["resized"],
            alt_text=result["alt_text"],
            alt_text_source=result["alt_text_source"],
        )
        db.add(job)
        db.commit()
    except Exception:
        logger.exception("Failed to persist PhotoOptimizationJob")

    # Send back the optimized image as base64 data URI
    b64 = base64.b64encode(result["output_bytes"]).decode()
    yield _sse("done", {
        "image_data_uri": f"data:image/jpeg;base64,{b64}",
        "alt_text": result["alt_text"],
        "gps_injected": result["gps_injected"],
        "resized": result["resized"],
    })


@router.post("/optimize", summary="Optimize a photo: resize + GPS + alt-text (SSE stream)")
async def optimize_photo_endpoint(
    user_id: UUID = Form(...),
    lat: float | None = Form(default=None),
    lon: float | None = Form(default=None),
    keywords: str = Form(default=""),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    if file.content_type not in _ALLOWED_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Tipo no soportado: {file.content_type}. Use JPEG, PNG o WEBP.",
        )

    image_bytes = await file.read()
    if len(image_bytes) > _MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Imagen demasiado grande (máx {_MAX_FILE_SIZE_MB} MB).",
        )

    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    kw_list = [k.strip() for k in keywords.split(",") if k.strip()] if keywords else []

    return StreamingResponse(
        _optimize_stream(
            image_bytes=image_bytes,
            filename=file.filename or "upload.jpg",
            lat=lat,
            lon=lon,
            keywords=kw_list,
            user_id=user_id,
            db=db,
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
