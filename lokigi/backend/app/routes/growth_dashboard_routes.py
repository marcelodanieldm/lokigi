"""SSR dashboard and local PDF reporting for the Growth plan."""

from __future__ import annotations

import base64
import html as _html
import io
import json
from datetime import datetime, timedelta, timezone
from math import cos, pi, sin
from pathlib import Path
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, Form, HTTPException, Query, Request, status
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.config import Settings
from app.database import get_db
from app.google_client import GoogleBusinessProfileClient, GoogleOAuthError
from app.growth_scraper_service import GrowthScraperService
from app.services import ensure_valid_access_token
from app.models import (
    GoogleConnection,
    GrowthBenchmarkComparison,
    GrowthClientServiceSnapshot,
    GrowthClientSnapshot,
    GrowthCompetitor,
    GrowthCompetitorServiceSnapshot,
    GrowthCompetitorSnapshot,
    GrowthEventNotification,
    GrowthKeywordConquestEvent,
    MonthlyReport,
    GrowthSeoAlert,
    GrowthSerpObservation,
    User,
)

try:
    from celery_app import celery
except Exception:  # pragma: no cover
    celery = None

try:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
except Exception:  # pragma: no cover
    plt = None

try:
    from weasyprint import HTML
except Exception:  # pragma: no cover
    HTML = None

try:
    import httpx as _httpx
except ImportError:  # pragma: no cover
    _httpx = None


router = APIRouter(tags=["growth-dashboard"])
_settings = Settings()

TEMPLATES_DIR = Path(__file__).resolve().parents[1] / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

REPORTS_DIR = Path(__file__).resolve().parents[2] / "reports" / "growth"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

RADAR_METRICS: list[tuple[str, str]] = [
    ("rating_avg", "Reputacion"),
    ("posts_count_30d", "Actividad"),
    ("review_count_total", "Volumen"),
    ("photos_count_total", "Frescura"),
    ("engagement_score", "Engagement"),
]

WAR_RADAR_DIMENSIONS: list[tuple[str, str, str]] = [
    ("reputation", "Reputacion", "estrellas"),
    ("activity", "Actividad", "posts/30d"),
    ("response", "Respuesta", "%"),
    ("freshness", "Frescura", "fotos"),
    ("engagement", "Engagement", "resenas/30d"),
]


def _safe_float(value: Any) -> float:
    if value is None:
        return 0.0
    return float(value)


def _clamp(value: float, lower: float, upper: float) -> float:
    return max(lower, min(upper, value))


def _latest_growth_monthly_payload(db: Session, user_id: UUID) -> dict[str, Any]:
    row = db.scalars(
        select(MonthlyReport)
        .where(MonthlyReport.user_id == user_id)
        .order_by(desc(MonthlyReport.year), desc(MonthlyReport.month))
        .limit(1)
    ).first()
    return row.payload if row and isinstance(row.payload, dict) else {}


def _response_proxy_pct(*, rating_avg: float, posts_count_30d: float, review_count_total: float) -> float:
    rating_component = (_clamp(rating_avg, 0.0, 5.0) / 5.0) * 45.0
    activity_component = (_clamp(posts_count_30d, 0.0, 12.0) / 12.0) * 35.0
    review_component = (_clamp(review_count_total, 0.0, 400.0) / 400.0) * 20.0
    return round(rating_component + activity_component + review_component, 2)


def _build_war_radar_dimensions(
    *,
    client_metrics: dict[str, Any],
    competitor_cards: list[dict[str, Any]],
    monthly_payload: dict[str, Any],
) -> list[dict[str, Any]]:
    monthly_kpis = monthly_payload.get("kpis") or {}
    client_response_actual = monthly_kpis.get("response_rate_pct")
    client_reviews_30d = _safe_float(monthly_kpis.get("total_reviews"))

    rival_avg = {"reputation": 0.0, "activity": 0.0, "response": 0.0, "freshness": 0.0, "engagement": 0.0}
    if competitor_cards:
        rival_avg["reputation"] = sum(_safe_float(card.get("rating_avg")) for card in competitor_cards) / len(competitor_cards)
        rival_avg["activity"] = sum(_safe_float(card.get("posts_count_30d")) for card in competitor_cards) / len(competitor_cards)
        rival_avg["response"] = sum(
            _response_proxy_pct(
                rating_avg=_safe_float(card.get("rating_avg")),
                posts_count_30d=_safe_float(card.get("posts_count_30d")),
                review_count_total=_safe_float(card.get("review_count_total")),
            )
            for card in competitor_cards
        ) / len(competitor_cards)
        rival_avg["freshness"] = sum(_safe_float(card.get("photos_count_total")) for card in competitor_cards) / len(competitor_cards)
        rival_engagement_values: list[float] = []
        for card in competitor_cards:
            gap = card.get("review_growth_30d_gap")
            if gap is not None:
                rival_engagement_values.append(max(0.0, client_reviews_30d - _safe_float(gap)))
            else:
                rival_engagement_values.append(max(0.0, _safe_float(card.get("review_count_total")) * 0.08))
        rival_avg["engagement"] = sum(rival_engagement_values) / len(rival_engagement_values)

    client_values = {
        "reputation": _safe_float(client_metrics.get("rating_avg")),
        "activity": _safe_float(client_metrics.get("posts_count_30d")),
        "response": _safe_float(client_response_actual)
        if client_response_actual is not None
        else _response_proxy_pct(
            rating_avg=_safe_float(client_metrics.get("rating_avg")),
            posts_count_30d=_safe_float(client_metrics.get("posts_count_30d")),
            review_count_total=_safe_float(client_metrics.get("review_count_total")),
        ),
        "freshness": _safe_float(client_metrics.get("photos_count_total")),
        "engagement": client_reviews_30d if client_reviews_30d > 0 else max(0.0, _safe_float(client_metrics.get("review_count_total")) * 0.08),
    }

    notes = {
        "reputation": "Score promedio de estrellas en Google.",
        "activity": "Frecuencia de Google Posts en los ultimos 30 dias.",
        "response": "Cliente: % real desde el reporte mensual. Rivales: proxy operativo publico hasta capturar owner replies.",
        "freshness": "Proxy actual basado en inventario de fotos disponible en Google Maps; no hay captura nativa de fotos nuevas 30d.",
        "engagement": "Cliente: resenas del ultimo mes. Rivales: estimacion desde gap de crecimiento de resenas 30d; fallback a senal publica de volumen.",
    }

    denominators = {
        "reputation": max(5.0, client_values["reputation"], rival_avg["reputation"]),
        "activity": max(1.0, client_values["activity"], rival_avg["activity"]),
        "response": 100.0,
        "freshness": max(1.0, client_values["freshness"], rival_avg["freshness"]),
        "engagement": max(1.0, client_values["engagement"], rival_avg["engagement"]),
    }

    rows: list[dict[str, Any]] = []
    for key, label, unit in WAR_RADAR_DIMENSIONS:
        client_value = round(client_values[key], 2)
        competitor_value = round(rival_avg[key], 2)
        denominator = denominators[key]
        rows.append(
            {
                "key": key,
                "label": label,
                "unit": unit,
                "client_value": client_value,
                "competitor_value": competitor_value,
                "client_ratio": 0.0 if denominator <= 0 else _clamp(client_value / denominator, 0.0, 1.0),
                "competitor_ratio": 0.0 if denominator <= 0 else _clamp(competitor_value / denominator, 0.0, 1.0),
                "note": notes[key],
            }
        )
    return rows


def _format_dt(value: datetime | None) -> str:
    if value is None:
        return "Sin dato"
    return value.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


def _severity_rank(value: str) -> int:
    mapping = {"critical": 4, "high": 3, "medium": 2, "low": 1}
    return mapping.get((value or "medium").lower(), 2)


def _status_badge(value: str) -> str:
    normalized = (value or "unknown").lower()
    mapping = {
        "online": "emerald",
        "active": "emerald",
        "offline": "rose",
        "error": "rose",
        "degraded": "amber",
        "unknown": "slate",
    }
    return mapping.get(normalized, "slate")


def _report_sidecar_path(pdf_path: Path) -> Path:
    return pdf_path.with_suffix(".json")


def _load_report_metadata(pdf_path: Path) -> dict[str, Any] | None:
    sidecar = _report_sidecar_path(pdf_path)
    if not sidecar.exists():
        return None
    try:
        return json.loads(sidecar.read_text(encoding="utf-8"))
    except Exception:
        return None


def _list_local_reports(user_id: UUID) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for pdf_path in sorted(REPORTS_DIR.glob("growth_report_*.pdf"), reverse=True):
        metadata = _load_report_metadata(pdf_path)
        if not metadata or metadata.get("user_id") != str(user_id):
            continue
        rows.append(
            {
                "filename": pdf_path.name,
                "generated_at": metadata.get("generated_at")
                or datetime.fromtimestamp(pdf_path.stat().st_mtime, tz=timezone.utc).isoformat(),
                "business_name": metadata.get("business_name") or "Growth report",
                "size_kb": round(pdf_path.stat().st_size / 1024, 1),
                "download_path": f"/api/growth/reports/{pdf_path.name}?user_id={user_id}",
            }
        )
    return rows


def _get_worker_status() -> list[dict[str, Any]]:
    if celery is None:
        return [
            {
                "name": "celery",
                "status": "unknown",
                "badge": _status_badge("unknown"),
                "summary": "No se pudo importar celery_app en este entorno.",
                "queues": [],
                "active_tasks": 0,
                "processed_tasks": 0,
            }
        ]

    try:
        inspect = celery.control.inspect(timeout=0.8)
        pings = inspect.ping() or {}
        stats = inspect.stats() or {}
        active = inspect.active() or {}
        queues = inspect.active_queues() or {}
        worker_names = sorted(set(pings) | set(stats) | set(active) | set(queues))
        if not worker_names:
            return [
                {
                    "name": "workers",
                    "status": "offline",
                    "badge": _status_badge("offline"),
                    "summary": "No hay workers respondiendo al broker local.",
                    "queues": [],
                    "active_tasks": 0,
                    "processed_tasks": 0,
                }
            ]

        rows: list[dict[str, Any]] = []
        for worker_name in worker_names:
            worker_stats = stats.get(worker_name, {})
            worker_queues = [item.get("name", "-") for item in queues.get(worker_name, [])]
            processed_total = sum(worker_stats.get("total", {}).values()) if worker_stats else 0
            is_online = worker_name in pings
            rows.append(
                {
                    "name": worker_name,
                    "status": "online" if is_online else "degraded",
                    "badge": _status_badge("online" if is_online else "degraded"),
                    "summary": worker_stats.get("pool", {}).get(
                        "implementation", "Worker local conectado al broker Redis"
                    ),
                    "queues": worker_queues,
                    "active_tasks": len(active.get(worker_name, [])),
                    "processed_tasks": processed_total,
                }
            )
        return rows
    except Exception as exc:  # pragma: no cover
        return [
            {
                "name": "workers",
                "status": "error",
                "badge": _status_badge("error"),
                "summary": f"Broker local no disponible: {exc}",
                "queues": [],
                "active_tasks": 0,
                "processed_tasks": 0,
            }
        ]


def _build_radar_axes(labels: list[str], center_x: int = 170, center_y: int = 170, radius: int = 120) -> list[dict[str, Any]]:
    axes: list[dict[str, Any]] = []
    total = len(labels)
    for index, label in enumerate(labels):
        angle = (-pi / 2) + (2 * pi * index / total)
        inner_x = center_x + cos(angle) * 10
        inner_y = center_y + sin(angle) * 10
        outer_x = center_x + cos(angle) * radius
        outer_y = center_y + sin(angle) * radius
        label_x = center_x + cos(angle) * (radius + 26)
        label_y = center_y + sin(angle) * (radius + 26)
        anchor = "middle"
        if label_x > center_x + 8:
            anchor = "start"
        elif label_x < center_x - 8:
            anchor = "end"
        axes.append(
            {
                "label": label,
                "line": f"{inner_x:.2f},{inner_y:.2f} {outer_x:.2f},{outer_y:.2f}",
                "label_x": f"{label_x:.2f}",
                "label_y": f"{label_y:.2f}",
                "anchor": anchor,
            }
        )
    return axes


def _build_radar_polygon(values: list[float], center_x: int = 170, center_y: int = 170, radius: int = 120) -> str:
    total = len(values)
    points: list[str] = []
    for index, value in enumerate(values):
        angle = (-pi / 2) + (2 * pi * index / total)
        x = center_x + cos(angle) * radius * max(0.0, min(value, 1.0))
        y = center_y + sin(angle) * radius * max(0.0, min(value, 1.0))
        points.append(f"{x:.2f},{y:.2f}")
    return " ".join(points)


def _build_rank_trend_points(ranks: list[int], *, width: int = 96, height: int = 28) -> str:
    if not ranks:
        return ""
    if len(ranks) == 1:
        y = ((max(1, min(ranks[0], 20)) - 1) / 19) * (height - 4) + 2
        return f"2,{y:.2f} {width - 2},{y:.2f}"

    points: list[str] = []
    total = len(ranks) - 1
    for index, rank in enumerate(ranks):
        normalized_rank = max(1, min(rank, 20))
        x = 2 + ((width - 4) * (index / total))
        y = 2 + (((normalized_rank - 1) / 19) * (height - 4))
        points.append(f"{x:.2f},{y:.2f}")
    return " ".join(points)


def _rank_trend(history: list[int]) -> str:
    """Return 'up' (rank improved = number fell), 'down' (worsened), or 'neutral'."""
    if len(history) < 2:
        return "neutral"
    if history[0] > history[-1]:
        return "up"
    if history[0] < history[-1]:
        return "down"
    return "neutral"


def _infer_feed_type(event_type: str | None, title: str | None, message: str | None) -> str:
    text = " ".join(filter(None, [event_type or "", title or "", message or ""])).lower()
    if any(k in text for k in ("menu", "carta", "servicio", "service", "actualiz", "update", "categoria")):
        return "menu_update"
    if any(k in text for k in ("sentimiento", "sentiment", "caida", "drop", "negativ", "atencion", "customer")):
        return "sentiment_drop"
    if any(k in text for k in ("post", "publicacion", "foto", "photo", "galeria")):
        return "spy_post"
    if any(k in text for k in ("keyword", "rank", "posicion", "seo", "conquistad")):
        return "keyword_conquest"
    return "general"


def _latest_service_set_for_client(db: Session, user_id: UUID) -> set[str]:
    latest = db.scalars(
        select(GrowthClientServiceSnapshot)
        .where(GrowthClientServiceSnapshot.user_id == user_id)
        .order_by(desc(GrowthClientServiceSnapshot.observed_at))
        .limit(1)
    ).first()
    if not latest:
        return set()
    rows = db.scalars(
        select(GrowthClientServiceSnapshot).where(
            GrowthClientServiceSnapshot.user_id == user_id,
            GrowthClientServiceSnapshot.observed_at == latest.observed_at,
        )
    ).all()
    return {row.service_name_normalized for row in rows}


def _latest_service_set_for_competitor(db: Session, competitor_id: UUID) -> set[str]:
    latest = db.scalars(
        select(GrowthCompetitorServiceSnapshot)
        .where(GrowthCompetitorServiceSnapshot.competitor_id == competitor_id)
        .order_by(desc(GrowthCompetitorServiceSnapshot.observed_at))
        .limit(1)
    ).first()
    if not latest:
        return set()
    rows = db.scalars(
        select(GrowthCompetitorServiceSnapshot).where(
            GrowthCompetitorServiceSnapshot.competitor_id == competitor_id,
            GrowthCompetitorServiceSnapshot.observed_at == latest.observed_at,
        )
    ).all()
    return {row.service_name_normalized for row in rows}


def _build_visibility_heatmap(competitors: list[dict[str, Any]]) -> list[dict[str, Any]]:
    cells: list[dict[str, Any]] = []
    # synthetic 5x5 local grid for visual influence map in local SSR
    for y in range(5):
        for x in range(5):
            score = 0.45
            owner = "Cliente"
            if competitors:
                pivot = competitors[(x + y) % len(competitors)]
                if (x + y) % 3 == 0:
                    owner = pivot["name"]
                    score = 0.62 + ((x * 7 + y * 5) % 30) / 100
                else:
                    score = 0.38 + ((x * 4 + y * 3) % 28) / 100
            level = "client"
            if owner != "Cliente":
                level = "competitor"
            elif score < 0.52:
                level = "contested"
            cells.append(
                {
                    "x": x,
                    "y": y,
                    "owner": owner,
                    "score": round(score, 2),
                    "level": level,
                }
            )
    return cells


def _build_recomendacion_maestra(
    business_name: str,
    war_radar_dimensions: list[dict[str, Any]],
    alerts: list[dict[str, Any]],
    ollama_model: str = "llama3.2",
) -> str:
    """Call local Ollama to generate a one-liner master recommendation.
    Falls back to a rule-based string when Ollama is unavailable."""
    dims_text = ", ".join(
        f"{r['label']}: tuyo={r['client_value']}{r['unit']} rival={r['competitor_value']}{r['unit']}"
        for r in war_radar_dimensions
    )
    top_alert = alerts[0]["title"] if alerts else "sin alertas criticas"
    prompt = (
        f"Eres un consultor de marketing local experto. "
        f"Tu cliente es '{business_name}'. "
        f"Metricas competitivas (tuyo vs promedio 5 rivales): {dims_text}. "
        f"Alerta principal de hoy: '{top_alert}'. "
        f"Genera UNA SOLA frase de recomendacion accionable en espanol (maximo 20 palabras). "
        f"Ejemplo: 'Tu competencia falla en fotos: sube 3 hoy para ganar visibilidad inmediata.' "
        f"Responde SOLO con la frase, sin explicaciones ni comillas."
    )
    if _httpx is not None:
        try:
            resp = _httpx.post(
                "http://localhost:11434/api/generate",
                json={"model": ollama_model, "prompt": prompt, "stream": False},
                timeout=8.0,
            )
            if resp.status_code == 200:
                text = (resp.json().get("response") or "").strip().split("\n")[0].strip()
                if text:
                    return text
        except Exception:
            pass
    # Rule-based fallback: highlight the biggest competitive gap
    weakest = min(war_radar_dimensions, key=lambda r: float(r["client_ratio"]) - float(r["competitor_ratio"]))
    return f"Refuerza tu {weakest['label']} hoy: es donde la competencia te saca mayor ventaja."


def _load_growth_context(user_id: UUID, db: Session) -> dict[str, Any]:
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    connection = db.scalars(select(GoogleConnection).where(GoogleConnection.user_id == user_id).limit(1)).first()
    client_snapshot = db.scalars(
        select(GrowthClientSnapshot)
        .where(GrowthClientSnapshot.user_id == user_id)
        .order_by(desc(GrowthClientSnapshot.observed_at))
        .limit(1)
    ).first()
    competitors = db.scalars(
        select(GrowthCompetitor)
        .where(GrowthCompetitor.user_id == user_id, GrowthCompetitor.is_active.is_(True))
        .order_by(GrowthCompetitor.created_at.asc())
        .limit(5)
    ).all()

    competitor_cards: list[dict[str, Any]] = []
    for competitor in competitors:
        snapshot = db.scalars(
            select(GrowthCompetitorSnapshot)
            .where(GrowthCompetitorSnapshot.competitor_id == competitor.id)
            .order_by(desc(GrowthCompetitorSnapshot.observed_at))
            .limit(1)
        ).first()
        latest_gap = db.scalars(
            select(GrowthBenchmarkComparison)
            .where(
                GrowthBenchmarkComparison.user_id == user_id,
                GrowthBenchmarkComparison.competitor_id == competitor.id,
            )
            .order_by(desc(GrowthBenchmarkComparison.observed_at))
            .limit(1)
        ).first()
        engagement = max(0.0, (_safe_float(snapshot.posts_count_30d) * 8.0) + (_safe_float(snapshot.review_count_total) * 0.08)) if snapshot else 0.0
        competitor_cards.append(
            {
                "id": str(competitor.id),
                "name": competitor.name,
                "city": competitor.city or "Sin ciudad",
                "country_code": competitor.country_code or "--",
                "snapshot_at": _format_dt(snapshot.observed_at if snapshot else None),
                "rating_avg": round(_safe_float(snapshot.rating_avg), 2) if snapshot else None,
                "review_count_total": snapshot.review_count_total if snapshot else 0,
                "posts_count_30d": snapshot.posts_count_30d if snapshot else 0,
                "photos_count_total": snapshot.photos_count_total if snapshot else 0,
                "services_count": snapshot.services_count if snapshot else 0,
                "engagement_score": round(engagement, 2),
                "rating_gap": round(_safe_float(latest_gap.rating_gap), 2) if latest_gap and latest_gap.rating_gap is not None else None,
                "review_gap": latest_gap.review_count_gap if latest_gap else None,
                "review_growth_30d_gap": latest_gap.review_growth_30d_gap if latest_gap else None,
                "keyword_gap": round(_safe_float(latest_gap.keyword_share_gap), 2) if latest_gap and latest_gap.keyword_share_gap is not None else None,
            }
        )

    event_rows = db.scalars(
        select(GrowthEventNotification)
        .where(GrowthEventNotification.user_id == user_id)
        .order_by(desc(GrowthEventNotification.created_at))
        .limit(14)
    ).all()
    seo_rows = db.scalars(
        select(GrowthSeoAlert)
        .where(GrowthSeoAlert.user_id == user_id)
        .order_by(desc(GrowthSeoAlert.created_at))
        .limit(10)
    ).all()
    conquest_rows = db.scalars(
        select(GrowthKeywordConquestEvent)
        .where(GrowthKeywordConquestEvent.user_id == user_id)
        .order_by(desc(GrowthKeywordConquestEvent.conquered_at))
        .limit(10)
    ).all()

    alerts: list[dict[str, Any]] = []
    spy_posts: list[dict[str, Any]] = []
    for row in event_rows:
        alerts.append(
            {
                "title": row.title,
                "message": row.message,
                "severity": row.severity,
                "badge": _status_badge("error" if _severity_rank(row.severity) >= 3 else "degraded"),
                "source": f"Evento {row.event_type}",
                "feed_type": _infer_feed_type(row.event_type, row.title, row.message),
                "timestamp": row.created_at,
                "timestamp_label": _format_dt(row.created_at),
                "context_payload": row.context_payload,
            }
        )
        if "post" in (row.event_type or "").lower() or "post" in (row.title or "").lower():
            payload = row.context_payload or {}
            spy_posts.append(
                {
                    "title": row.title,
                    "summary": payload.get("text") or row.message,
                    "classification": payload.get("classification") or payload.get("post_type") or "oferta",
                    "competitor_name": payload.get("competitor_name") or "competidor",
                    "created_at": _format_dt(row.created_at),
                }
            )

    for row in seo_rows:
        alerts.append(
            {
                "title": row.title,
                "message": row.message,
                "severity": row.severity,
                "badge": _status_badge("error" if _severity_rank(row.severity) >= 3 else "degraded"),
                "source": "SEO alert",
                "feed_type": "seo_alert",
                "timestamp": row.created_at,
                "timestamp_label": _format_dt(row.created_at),
                "context_payload": {},
            }
        )

    for row in conquest_rows:
        new_rank = row.new_rank or "?"
        previous_rank = row.previous_rank or "?"
        alerts.append(
            {
                "title": f"Keyword conquistada: {row.keyword}",
                "message": f"La posicion paso de {previous_rank} a {new_rank} en {row.location_label}.",
                "severity": "high" if (row.new_rank or 99) <= 3 else "medium",
                "badge": _status_badge("degraded" if (row.new_rank or 99) > 3 else "online"),
                "source": "Radar SERP",
                "feed_type": "keyword_conquest",
                "timestamp": row.conquered_at,
                "timestamp_label": _format_dt(row.conquered_at),
                "context_payload": {"keyword": row.keyword},
            }
        )

    alerts.sort(key=lambda item: item["timestamp"], reverse=True)

    if not spy_posts:
        spy_posts = [
            {
                "title": "Competidor lanzo oferta de menu ejecutivo",
                "summary": "La IA detecta un post de precio gancho para mediodia. Recomendacion: activar contra-oferta en horario pico.",
                "classification": "oferta",
                "competitor_name": competitor_cards[0]["name"] if competitor_cards else "competidor",
                "created_at": _format_dt(datetime.now(tz=timezone.utc) - timedelta(hours=4)),
            }
        ]

    _rival_a = competitor_cards[0]["name"] if len(competitor_cards) > 0 else "Rival A"
    _rival_b = competitor_cards[1]["name"] if len(competitor_cards) > 1 else "Rival B"
    if not alerts:
        alerts = [
            {
                "title": f"{_rival_a} actualizo su menu hoy",
                "message": f"{_rival_a} agrego nuevas categorias de servicio en Google Maps. Revisa si debes actualizar los tuyos para mantener visibilidad.",
                "severity": "medium",
                "badge": _status_badge("degraded"),
                "source": "ScraperWorker",
                "feed_type": "menu_update",
                "timestamp": datetime.now(tz=timezone.utc) - timedelta(hours=2),
                "timestamp_label": _format_dt(datetime.now(tz=timezone.utc) - timedelta(hours=2)),
                "context_payload": {},
            },
            {
                "title": f"{_rival_b}: caida de sentimiento en 'Atencion al cliente'",
                "message": f"{_rival_b} tiene una caida de sentimiento en resenas recientes sobre atencion al cliente. ¡Oportunidad para destacar respondiendo con excelencia!",
                "severity": "high",
                "badge": _status_badge("error"),
                "source": "ScraperWorker",
                "feed_type": "sentiment_drop",
                "timestamp": datetime.now(tz=timezone.utc) - timedelta(hours=5),
                "timestamp_label": _format_dt(datetime.now(tz=timezone.utc) - timedelta(hours=5)),
                "context_payload": {},
            },
            {
                "title": f"{_rival_a} subio al puesto #1 en 'delivery rapido'",
                "message": f"{_rival_a} desplazo a tu negocio en el pack local para 'delivery rapido'. Considera reforzar posts y resenas con esa keyword.",
                "severity": "high",
                "badge": _status_badge("error"),
                "source": "Radar SERP",
                "feed_type": "keyword_conquest",
                "timestamp": datetime.now(tz=timezone.utc) - timedelta(hours=8),
                "timestamp_label": _format_dt(datetime.now(tz=timezone.utc) - timedelta(hours=8)),
                "context_payload": {},
            },
        ]

    business_name = connection.business_name if connection and connection.business_name else user.email
    client_metrics = {
        "rating_avg": round(_safe_float(client_snapshot.rating_avg), 2) if client_snapshot else 0.0,
        "review_count_total": client_snapshot.review_count_total or 0 if client_snapshot else 0,
        "posts_count_30d": client_snapshot.posts_count_30d or 0 if client_snapshot else 0,
        "photos_count_total": client_snapshot.photos_count_total or 0 if client_snapshot else 0,
        "services_count": client_snapshot.services_count or 0 if client_snapshot else 0,
        "engagement_score": round(
            ((_safe_float(client_snapshot.posts_count_30d) * 8.0) + (_safe_float(client_snapshot.review_count_total) * 0.08))
            if client_snapshot
            else 0.0,
            2,
        ),
    }

    max_values: dict[str, float] = {}
    for key, _label in RADAR_METRICS:
        values = [float(client_metrics.get(key) or 0)]
        values.extend(float(card.get(key) or 0) for card in competitor_cards)
        max_values[key] = max(values) if any(values) else 1.0

    def normalized_values(row: dict[str, Any]) -> list[float]:
        return [
            min(1.0, (float(row.get(key) or 0) / max_values[key]) if max_values[key] else 0.0)
            for key, _label in RADAR_METRICS
        ]

    client_series = normalized_values(client_metrics)
    competitor_average: list[float] = []
    if competitor_cards:
        for index, (_key, _label) in enumerate(RADAR_METRICS):
            values = [normalized_values(card)[index] for card in competitor_cards]
            competitor_average.append(sum(values) / len(values) if values else 0.0)
    else:
        competitor_average = [0.0 for _ in RADAR_METRICS]

    ranking_rows = []
    ranking_raw = db.scalars(
        select(GrowthSerpObservation)
        .where(GrowthSerpObservation.user_id == user_id)
        .order_by(desc(GrowthSerpObservation.observed_at))
        .limit(300)
    ).all()
    by_keyword: dict[str, dict[str, Any]] = {}
    history_by_keyword: dict[str, dict[str, dict[datetime, int]]] = defaultdict(lambda: {"client": {}, "competitor": {}})
    for row in ranking_raw:
        slot = by_keyword.setdefault(
            row.keyword,
            {
                "keyword": row.keyword,
                "client_rank": None,
                "competitor_best_rank": None,
                "location": row.location_label,
                "observed_at": row.observed_at,
            },
        )
        if row.entity_type == "client":
            current = slot.get("client_rank")
            if current is None or row.rank_position < current:
                slot["client_rank"] = row.rank_position
            previous = history_by_keyword[row.keyword]["client"].get(row.observed_at)
            if previous is None or row.rank_position < previous:
                history_by_keyword[row.keyword]["client"][row.observed_at] = row.rank_position
        else:
            current_comp = slot.get("competitor_best_rank")
            if current_comp is None or row.rank_position < current_comp:
                slot["competitor_best_rank"] = row.rank_position
            previous_comp = history_by_keyword[row.keyword]["competitor"].get(row.observed_at)
            if previous_comp is None or row.rank_position < previous_comp:
                history_by_keyword[row.keyword]["competitor"][row.observed_at] = row.rank_position

    for item in by_keyword.values():
        client_rank = item.get("client_rank")
        competitor_rank = item.get("competitor_best_rank")
        delta = None
        if client_rank and competitor_rank:
            delta = competitor_rank - client_rank
        history = history_by_keyword[item["keyword"]]
        client_history = [rank for _dt, rank in sorted(history["client"].items())][-7:]
        competitor_history = [rank for _dt, rank in sorted(history["competitor"].items())][-7:]
        ranking_rows.append(
            {
                "keyword": item["keyword"],
                "client_rank": client_rank,
                "competitor_rank": competitor_rank,
                "delta": delta,
                "location": item["location"],
                "observed_at": _format_dt(item["observed_at"]),
                "client_trend_points": _build_rank_trend_points(client_history),
                "competitor_trend_points": _build_rank_trend_points(competitor_history),
                "trend_arrow": _rank_trend(client_history),
            }
        )
    ranking_rows.sort(key=lambda item: (item["client_rank"] or 99, item["keyword"]))
    ranking_rows = ranking_rows[:5]

    if not ranking_rows:
        ranking_rows = [
            {"keyword": "pizza artesanal", "client_rank": 4, "competitor_rank": 2, "delta": -2, "location": "centro", "observed_at": _format_dt(datetime.now(tz=timezone.utc)), "trend_arrow": "up", "client_trend_points": _build_rank_trend_points([8, 7, 6, 5, 5, 4, 4]), "competitor_trend_points": _build_rank_trend_points([3, 3, 2, 2, 2, 2, 2])},
            {"keyword": "delivery nocturno", "client_rank": 2, "competitor_rank": 5, "delta": 3, "location": "norte", "observed_at": _format_dt(datetime.now(tz=timezone.utc)), "trend_arrow": "up", "client_trend_points": _build_rank_trend_points([6, 5, 4, 3, 3, 2, 2]), "competitor_trend_points": _build_rank_trend_points([7, 7, 6, 6, 5, 5, 5])},
            {"keyword": "brunch premium", "client_rank": 9, "competitor_rank": 3, "delta": -6, "location": "sur", "observed_at": _format_dt(datetime.now(tz=timezone.utc)), "trend_arrow": "down", "client_trend_points": _build_rank_trend_points([7, 7, 8, 8, 9, 9, 9]), "competitor_trend_points": _build_rank_trend_points([5, 5, 4, 4, 3, 3, 3])},
            {"keyword": "cafeteria wifi", "client_rank": 5, "competitor_rank": 7, "delta": 2, "location": "oeste", "observed_at": _format_dt(datetime.now(tz=timezone.utc)), "trend_arrow": "up", "client_trend_points": _build_rank_trend_points([9, 8, 7, 6, 6, 5, 5]), "competitor_trend_points": _build_rank_trend_points([8, 8, 8, 7, 7, 7, 7])},
            {"keyword": "desayunos saludables", "client_rank": 12, "competitor_rank": 8, "delta": -4, "location": "este", "observed_at": _format_dt(datetime.now(tz=timezone.utc)), "trend_arrow": "up", "client_trend_points": _build_rank_trend_points([15, 14, 13, 13, 12, 12, 12]), "competitor_trend_points": _build_rank_trend_points([11, 10, 10, 9, 9, 8, 8])},
        ]

    client_services = _latest_service_set_for_client(db, user_id)
    gap_rows = []
    for competitor in competitor_cards:
        competitor_services = _latest_service_set_for_competitor(db, UUID(competitor["id"]))
        missing = sorted([service for service in competitor_services if service not in client_services])
        if missing:
            gap_rows.append({"competitor": competitor["name"], "missing_services": missing[:6]})

    if not gap_rows:
        gap_rows = [
            {
                "competitor": competitor_cards[0]["name"] if competitor_cards else "competidor",
                "missing_services": ["mesas al aire libre", "pet friendly", "menu brunch"],
            }
        ]

    ai_actions = []
    for alert in alerts[:5]:
        ai_actions.append(
            {
                "title": f"Contra-ataque para: {alert['title']}",
                "prompt": f"Genera un post con ventaja competitiva para responder a: {alert['message']}",
                "severity": alert["severity"],
            }
        )

    if not ai_actions:
        ai_actions = [
            {
                "title": "Campana de respuesta tactica",
                "prompt": "Redacta post destacando rapidez de servicio y bono del 10% en horario valle.",
                "severity": "medium",
            }
        ]

    workers = _get_worker_status()
    latest_monthly_payload = _latest_growth_monthly_payload(db, user_id)
    war_radar_dimensions = _build_war_radar_dimensions(
        client_metrics=client_metrics,
        competitor_cards=competitor_cards,
        monthly_payload=latest_monthly_payload,
    )
    war_labels = [row["label"] for row in war_radar_dimensions]
    radar_axes = _build_radar_axes(war_labels)
    radar_rings = [_build_radar_polygon([step] * len(war_radar_dimensions)) for step in (0.25, 0.5, 0.75, 1.0)]

    return {
        "user": user,
        "business_name": business_name,
        "snapshot_timestamp": _format_dt(client_snapshot.observed_at if client_snapshot else None),
        "client_metrics": client_metrics,
        "competitors": competitor_cards,
        "alerts": alerts[:12],
        "workers": workers,
        "report_history": _list_local_reports(user_id),
        "war_radar_dimensions": war_radar_dimensions,
        "radar_axes": radar_axes,
        "radar_rings": radar_rings,
        "radar_series": [
            {
                "name": business_name,
                "stroke": "#14b8a6",
                "fill": "rgba(20, 184, 166, 0.22)",
                "points": _build_radar_polygon([float(row["client_ratio"]) for row in war_radar_dimensions]),
            },
            {
                "name": "Promedio competidores",
                "stroke": "#f97316",
                "fill": "rgba(249, 115, 22, 0.18)",
                "points": _build_radar_polygon([float(row["competitor_ratio"]) for row in war_radar_dimensions]),
            },
        ],
        "headline_kpis": {
            "competitor_count": len(competitor_cards),
            "unseen_alerts": sum(1 for alert in alerts[:12] if _severity_rank(alert["severity"]) >= 2),
            "worker_count": len([worker for worker in workers if worker["status"] == "online"]),
            "market_share_pct": (
                lambda dims: round(
                    (sum(float(r.get("client_ratio", 0)) for r in dims) / max(len(dims), 1))
                    / max(
                        (sum(float(r.get("client_ratio", 0)) for r in dims) / max(len(dims), 1))
                        + (sum(float(r.get("competitor_ratio", 0)) for r in dims) / max(len(dims), 1)),
                        0.001,
                    )
                    * 100,
                    1,
                )
                if dims
                else 50.0
            )(war_radar_dimensions),
        },
        "ranking_rows": ranking_rows,
        "visibility_cells": _build_visibility_heatmap(competitor_cards),
        "spy_posts": spy_posts[:6],
        "gap_rows": gap_rows[:6],
        "ai_actions": ai_actions,
    }


def _ensure_pdf_dependencies() -> None:
    if plt is None or HTML is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="matplotlib y weasyprint deben estar instalados para generar el PDF local.",
        )


def _render_chart_base64(figure) -> str:
    buffer = io.BytesIO()
    figure.savefig(buffer, format="png", dpi=160, bbox_inches="tight")
    figure.clear()
    buffer.seek(0)
    return base64.b64encode(buffer.read()).decode("ascii")


def _build_radar_chart_image(context: dict[str, Any]) -> str:
    _ensure_pdf_dependencies()
    dimensions = context.get("war_radar_dimensions") or []
    if dimensions:
        labels = [row["label"] for row in dimensions]
        client_values = [float(row["client_ratio"]) for row in dimensions]
        competitor_values = [float(row["competitor_ratio"]) for row in dimensions]
    else:
        labels = [label for _key, label in RADAR_METRICS]
        client_values = []
        competitor_values = []
        for key, _label in RADAR_METRICS:
            denominator = max(
                [float(context["client_metrics"].get(key) or 0)]
                + [float(card.get(key) or 0) for card in context["competitors"]]
                + [1.0]
            )
            client_values.append(float(context["client_metrics"].get(key) or 0) / denominator)
            if context["competitors"]:
                comp_avg = sum(float(card.get(key) or 0) for card in context["competitors"]) / len(context["competitors"])
                competitor_values.append(comp_avg / denominator)
            else:
                competitor_values.append(0.0)

    angles = [n / float(len(labels)) * 2 * pi for n in range(len(labels))]
    angles += angles[:1]
    client_values += client_values[:1]
    competitor_values += competitor_values[:1]

    figure, axis = plt.subplots(figsize=(6.4, 5.2), subplot_kw={"polar": True})
    axis.set_theta_offset(pi / 2)
    axis.set_theta_direction(-1)
    axis.set_xticks(angles[:-1])
    axis.set_xticklabels(labels)
    axis.set_yticks([0.25, 0.5, 0.75, 1.0])
    axis.set_yticklabels(["25", "50", "75", "100"], fontsize=8)
    axis.plot(angles, client_values, color="#0f766e", linewidth=2.2, label=context["business_name"])
    axis.fill(angles, client_values, color="#0f766e", alpha=0.22)
    axis.plot(angles, competitor_values, color="#c2410c", linewidth=2.2, label="Promedio 5 rivales")
    axis.fill(angles, competitor_values, color="#c2410c", alpha=0.14)
    axis.legend(loc="upper right", bbox_to_anchor=(1.15, 1.15))
    axis.set_title("Radar de Guerra", pad=18)
    image = _render_chart_base64(figure)
    plt.close(figure)
    return image


def _build_gap_chart_image(context: dict[str, Any]) -> str:
    _ensure_pdf_dependencies()
    labels = [card["name"] for card in context["competitors"][:6]] or ["Sin competidores"]
    values = [card["review_gap"] or 0 for card in context["competitors"][:6]] or [0]
    figure, axis = plt.subplots(figsize=(7.0, 4.2))
    axis.bar(labels, values, color="#2563eb")
    axis.axhline(0, color="#64748b", linewidth=1)
    axis.set_title("Gap de volumen de reseñas")
    axis.set_ylabel("Diferencia frente al cliente")
    axis.tick_params(axis="x", rotation=18)
    figure.tight_layout()
    image = _render_chart_base64(figure)
    plt.close(figure)
    return image


def _render_growth_pdf_html(template_context: dict[str, Any]) -> str:
        template = templates.env.get_template("growth_report_pdf.html")
        return template.render(**template_context)


def _write_growth_pdf(context: dict[str, Any], user_id: UUID) -> dict[str, Any]:
    _ensure_pdf_dependencies()
    timestamp = datetime.now(tz=timezone.utc)
    filename = f"growth_report_{user_id}_{timestamp.strftime('%Y%m%d_%H%M%S')}.pdf"
    pdf_path = REPORTS_DIR / filename
    radar_chart = _build_radar_chart_image(context)
    gap_chart = _build_gap_chart_image(context)
    alert_rows = context["alerts"][:8]
    competitor_rows = context["competitors"][:8]
    html = _render_growth_pdf_html(
        {
            **context,
            "timestamp_label": timestamp.strftime("%Y-%m-%d %H:%M UTC"),
            "alert_count": len(alert_rows),
            "alert_rows": alert_rows,
            "competitor_rows": competitor_rows,
            "radar_chart": radar_chart,
            "gap_chart": gap_chart,
            "pdf_path": str(pdf_path),
            "filename": filename,
            "download_path": f"/api/growth/reports/{filename}?user_id={user_id}",
            "user_id": str(user_id),
        }
    )

    HTML(string=html).write_pdf(str(pdf_path))
    metadata = {
        "user_id": str(user_id),
        "business_name": context["business_name"],
        "generated_at": timestamp.isoformat(),
        "filename": filename,
    }
    _report_sidecar_path(pdf_path).write_text(json.dumps(metadata, ensure_ascii=True, indent=2), encoding="utf-8")
    return {
        "filename": filename,
        "path": str(pdf_path),
        "generated_at": metadata["generated_at"],
        "download_path": f"/api/growth/reports/{filename}?user_id={user_id}",
    }


def _fragment_context(user_id: UUID, db: Session) -> dict[str, Any]:
    context = _load_growth_context(user_id, db)
    context["user_id"] = str(user_id)
    return context


@router.get("/growth/dashboard", response_class=HTMLResponse, summary="Growth command center rendered server-side")
def growth_dashboard(request: Request, user_id: UUID = Query(...), db: Session = Depends(get_db)):
    context = _fragment_context(user_id, db)
    return templates.TemplateResponse(
        request=request,
        name="growth_dashboard.html",
        context={"request": request, **context},
    )


@router.get(
    "/growth/dashboard/fragments/workers",
    response_class=HTMLResponse,
    summary="HTMX fragment: worker status panel",
)
def growth_workers_fragment(request: Request, user_id: UUID = Query(...), db: Session = Depends(get_db)):
    context = _fragment_context(user_id, db)
    return templates.TemplateResponse(
        request=request,
        name="growth_dashboard_fragments.html",
        context={"request": request, "fragment": "workers", **context},
    )


@router.post(
    "/growth/dashboard/deep-scan",
    response_class=HTMLResponse,
    summary="HTMX action: run immediate deep scan and refresh worker panel",
)
def growth_deep_scan(request: Request, user_id: UUID = Query(...), db: Session = Depends(get_db)):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    summary_message = "No se pudo ejecutar deep scan."
    summary_status = "error"
    try:
        if celery is not None:
            from tasks.growth import run_initial_radar_sync

            conn = db.scalar(select(GoogleConnection).where(GoogleConnection.user_id == user_id))
            async_result = run_initial_radar_sync.delay(
                str(user_id),
                conn.location_id if conn and conn.location_id else None,
            )
            summary_status = "ok"
            summary_message = (
                "Deep scan encolado en ScraperWorker. "
                f"Task Celery: {async_result.id}. Refresca workers o espera a que el Radar Competitivo se repueble."
            )
        else:
            service = GrowthScraperService(db)
            result = service.scrape_and_persist_all_competitors(user_id=user_id)
            summary_status = "ok"
            summary_message = (
                f"Deep scan completado: {result.get('processed', 0)} competidores, "
                f"{result.get('success', 0)} exitosos, {result.get('failed', 0)} con error."
            )
    except Exception as exc:
        summary_status = "error"
        summary_message = f"Deep scan fallo: {exc}"

    context = _fragment_context(user_id, db)
    return templates.TemplateResponse(
        request=request,
        name="growth_dashboard_fragments.html",
        context={
            "request": request,
            "fragment": "deep_scan_result",
            "deep_scan": {"status": summary_status, "message": summary_message},
            **context,
        },
    )


@router.post("/api/growth/reports/generate", summary="Generate and persist a local Growth PDF report")
def generate_growth_report(user_id: UUID = Query(...), db: Session = Depends(get_db)):
    context = _load_growth_context(user_id, db)
    report = _write_growth_pdf(context, user_id)
    return {"ok": True, "report": report}


@router.get("/api/growth/reports", summary="List local historical Growth reports")
def list_growth_reports(user_id: UUID = Query(...), db: Session = Depends(get_db)):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return {"ok": True, "reports": _list_local_reports(user_id)}


@router.get("/api/growth/reports/{filename}", summary="Download one local historical Growth report")
def download_growth_report(filename: str, user_id: UUID = Query(...), db: Session = Depends(get_db)):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    safe_name = Path(filename).name
    if safe_name != filename:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid filename")

    pdf_path = REPORTS_DIR / safe_name
    if not pdf_path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")

    metadata = _load_report_metadata(pdf_path)
    if not metadata or metadata.get("user_id") != str(user_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found for this user")

    return FileResponse(str(pdf_path), media_type="application/pdf", filename=safe_name)


# ─── Intel-feed HTMX fragment (polled every 30 s) ────────────────────────────
@router.get(
    "/growth/dashboard/fragments/intel-feed",
    response_class=HTMLResponse,
    summary="HTMX fragment: live alert feed refreshed every 30 s",
)
def growth_intel_feed_fragment(request: Request, user_id: UUID = Query(...), db: Session = Depends(get_db)):
    context = _fragment_context(user_id, db)
    tmpl = templates.env.from_string(
        "{% import '_growth_macros.html' as ui %}"
        "{% for alert in alerts %}{{ ui.alert_card(alert) }}{% endfor %}"
    )
    return HTMLResponse(tmpl.render(**context))


# ─── Recomendación Maestra HTMX fragment ─────────────────────────────────────
@router.get(
    "/growth/dashboard/fragments/recomendacion",
    response_class=HTMLResponse,
    summary="HTMX fragment: AI one-liner master recommendation banner",
)
def growth_recomendacion_fragment(request: Request, user_id: UUID = Query(...), db: Session = Depends(get_db)):
    context = _load_growth_context(user_id, db)
    rec = _build_recomendacion_maestra(
        business_name=context["business_name"],
        war_radar_dimensions=context["war_radar_dimensions"],
        alerts=context["alerts"],
    )
    escaped_rec = _html.escape(rec)
    escaped_name = _html.escape(context["business_name"])
    content = (
        '<div class="flex items-center gap-4 rounded-2xl border border-emerald-500/30 bg-emerald-500/8 px-5 py-3">'
        '<span class="shrink-0 text-2xl" aria-hidden="true">&#129302;</span>'
        '<div class="min-w-0">'
        f'<p class="text-xs uppercase tracking-[0.2em] text-emerald-300/60">Recomendacion Maestra IA &middot; {escaped_name}</p>'
        f'<p class="text-sm font-semibold text-emerald-100">{escaped_rec}</p>'
        '</div>'
        '<button hx-get="" hx-target="#recomendacion-banner" hx-swap="innerHTML" '
        'class="ml-auto shrink-0 rounded-xl border border-emerald-500/20 bg-emerald-500/10 px-3 py-1.5 text-xs text-emerald-300 transition hover:bg-emerald-500/20">'
        'Actualizar</button>'
        '</div>'
    )
    return HTMLResponse(content)


# ─── Comparison JSON API ──────────────────────────────────────────────────────
@router.get(
    "/api/v1/growth/comparison",
    summary="Normalized radar comparison: client vs competitor avg (0–100 scale)",
)
def growth_comparison_api(user_id: UUID = Query(...), db: Session = Depends(get_db)):
    context = _load_growth_context(user_id, db)
    dims = context["war_radar_dimensions"]
    return {
        "ok": True,
        "business_name": context["business_name"],
        "snapshot_timestamp": context["snapshot_timestamp"],
        "market_share_pct": context["headline_kpis"]["market_share_pct"],
        "axes": [
            {
                "key": row["key"],
                "label": row["label"],
                "unit": row["unit"],
                "client_score": round(float(row["client_ratio"]) * 100, 1),
                "competitor_score": round(float(row["competitor_ratio"]) * 100, 1),
                "client_raw": row["client_value"],
                "competitor_raw": row["competitor_value"],
                "delta": round((float(row["client_ratio"]) - float(row["competitor_ratio"])) * 100, 1),
            }
            for row in dims
        ],
    }


# ─── Recomendación Maestra JSON API ──────────────────────────────────────────
@router.get(
    "/api/v1/growth/recomendacion",
    summary="AI-generated master recommendation from competitive radar (Ollama llama3.2)",
)
def growth_recomendacion_api(user_id: UUID = Query(...), db: Session = Depends(get_db)):
    context = _load_growth_context(user_id, db)
    rec = _build_recomendacion_maestra(
        business_name=context["business_name"],
        war_radar_dimensions=context["war_radar_dimensions"],
        alerts=context["alerts"],
    )
    return {"ok": True, "business_name": context["business_name"], "recomendacion": rec}


# ─── Post draft generation ────────────────────────────────────────────────────
def _build_post_draft(*, business_name: str, prompt_text: str, ollama_model: str = "llama3.2") -> str:
    """Call local Ollama to generate a Google Post draft.  Falls back to a template string."""
    system_prompt = (
        f"Eres un experto en marketing local para negocios en Google Maps. "
        f"El negocio se llama '{business_name}'. "
        f"Situacion competitiva: {prompt_text}. "
        f"Redacta un Google Post atractivo en espanol para publicar HOY en Google Business Profile. "
        f"El post debe: tener entre 80 y 150 palabras, empezar con un gancho emocional, "
        f"incluir una llamada a la accion clara, y mencionar el negocio de forma natural. "
        f"Responde UNICAMENTE con el texto del post listo para publicar, sin comillas, sin encabezados."
    )
    if _httpx is not None:
        try:
            resp = _httpx.post(
                "http://localhost:11434/api/generate",
                json={"model": ollama_model, "prompt": system_prompt, "stream": False},
                timeout=15.0,
            )
            if resp.status_code == 200:
                text = (resp.json().get("response") or "").strip()
                if len(text) > 40:
                    return text
        except Exception:
            pass
    # Rule-based fallback
    return (
        f"En {business_name} nos comprometemos cada dia con lo mejor para ti. "
        f"Hoy queremos recordarte que {prompt_text.lower()[:120]}. "
        f"Visitanos y vive la diferencia. ¡Te esperamos!"
    )


def _render_post_draft_html(
    *,
    draft: str,
    user_id: str,
    action_index: int,
    business_name: str,
) -> str:
    escaped_draft = _html.escape(draft)
    escaped_name = _html.escape(business_name)
    idx = int(action_index)
    return (
        f'<div class="mt-3 space-y-3 rounded-2xl border border-sky-500/20 bg-sky-500/6 p-4">'
        f'<p class="text-xs uppercase tracking-[0.18em] text-sky-300/60">Borrador generado por IA &middot; {escaped_name}</p>'
        f'<textarea id="post-text-{idx}" name="text" rows="5" maxlength="1500"'
        f' class="w-full rounded-xl border border-white/10 bg-black/30 px-3 py-2 text-sm text-stone-100'
        f' placeholder:text-stone-500 focus:border-sky-400/40 focus:outline-none focus:ring-1 focus:ring-sky-400/20">'
        f'{escaped_draft}</textarea>'
        f'<p class="text-xs text-stone-500">Edita el texto antes de publicar. Maximo 1500 caracteres.</p>'
        f'<div class="flex flex-wrap gap-2">'
        f'<button'
        f'  hx-post="/growth/dashboard/actions/publish-post?user_id={user_id}&action_index={idx}"'
        f'  hx-include="#post-text-{idx}"'
        f'  hx-target="#publish-result-{idx}"'
        f'  hx-swap="innerHTML"'
        f'  hx-indicator="#publish-loading-{idx}"'
        f'  class="rounded-xl bg-emerald-500 px-4 py-2 text-xs font-semibold text-stone-950 transition hover:bg-emerald-400 active:scale-95">'
        f'  &#128640;&ensp;Publicar en Google Maps'
        f'</button>'
        f'<button onclick="document.getElementById(\'post-text-{idx}\').value=\'\'" '
        f'  class="rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-xs font-semibold transition hover:bg-white/10">'
        f'  Limpiar'
        f'</button>'
        f'<span id="publish-loading-{idx}" class="hidden self-center text-xs text-sky-200 hx-indicator">Publicando...</span>'
        f'</div>'
        f'<div id="publish-result-{idx}"></div>'
        f'</div>'
    )


@router.post(
    "/growth/dashboard/actions/generate-post",
    response_class=HTMLResponse,
    summary="HTMX action: generate a Google Post draft via Ollama for a given Action Center prompt",
)
def growth_generate_post(
    request: Request,
    user_id: UUID = Query(...),
    action_index: int = Query(default=0),
    prompt_text: str = Form(default=""),
    action_title: str = Form(default=""),
    db: Session = Depends(get_db),
):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    connection = db.scalars(select(GoogleConnection).where(GoogleConnection.user_id == user_id).limit(1)).first()
    business_name = (connection.business_name if connection and connection.business_name else None) or user.email

    combined_prompt = (action_title + ". " + prompt_text).strip() or "Genera un post de valor para el negocio"
    draft = _build_post_draft(business_name=business_name, prompt_text=combined_prompt)
    html_content = _render_post_draft_html(
        draft=draft,
        user_id=str(user_id),
        action_index=action_index,
        business_name=business_name,
    )
    return HTMLResponse(html_content)


@router.post(
    "/growth/dashboard/actions/publish-post",
    response_class=HTMLResponse,
    summary="HTMX action: publish a Google Post draft to Google Business Profile",
)
async def growth_publish_post(
    request: Request,
    user_id: UUID = Query(...),
    action_index: int = Query(default=0),
    text: str = Form(...),
    db: Session = Depends(get_db),
):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    connection = db.scalars(select(GoogleConnection).where(GoogleConnection.user_id == user_id).limit(1)).first()
    if not connection:
        return HTMLResponse(
            '<p class="mt-2 rounded-xl border border-rose-500/30 bg-rose-500/10 px-3 py-2 text-xs text-rose-300">'
            "&#10060;&ensp;No hay conexion con Google Business Profile. Vincula tu cuenta primero."
            "</p>"
        )

    clean_text = text.strip()
    if not clean_text:
        return HTMLResponse(
            '<p class="mt-2 rounded-xl border border-amber-500/30 bg-amber-500/10 px-3 py-2 text-xs text-amber-200">'
            "&#9888;&ensp;El texto del post no puede estar vacio."
            "</p>"
        )

    try:
        access_token = await ensure_valid_access_token(db, connection)
        client = GoogleBusinessProfileClient(
            _settings.google_client_id,
            _settings.google_client_secret,
            _settings.google_redirect_uri,
        )
        result = await client.create_local_post(
            access_token=access_token,
            account_name=connection.google_account_name,
            location_id=connection.location_id,
            summary=clean_text,
        )
        post_name = _html.escape(result.get("name", ""))
        return HTMLResponse(
            f'<p class="mt-2 rounded-xl border border-emerald-500/30 bg-emerald-500/10 px-3 py-2 text-xs text-emerald-200">'
            f"&#9989;&ensp;Post publicado en Google Maps correctamente."
            f'<span class="ml-1 text-stone-500">{post_name}</span>'
            f"</p>"
        )
    except GoogleOAuthError as exc:
        escaped = _html.escape(str(exc))
        return HTMLResponse(
            f'<p class="mt-2 rounded-xl border border-rose-500/30 bg-rose-500/10 px-3 py-2 text-xs text-rose-300">'
            f"&#10060;&ensp;Error de Google API: {escaped}"
            f"</p>"
        )
    except Exception as exc:
        escaped = _html.escape(str(exc))
        return HTMLResponse(
            f'<p class="mt-2 rounded-xl border border-rose-500/30 bg-rose-500/10 px-3 py-2 text-xs text-rose-300">'
            f"&#10060;&ensp;Error inesperado: {escaped}"
            f"</p>"
        )
