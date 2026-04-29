"""SSR dashboard and local PDF reporting for the Growth plan."""

from __future__ import annotations

import base64
import io
import json
from datetime import datetime, timedelta, timezone
from math import cos, pi, sin
from pathlib import Path
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.growth_scraper_service import GrowthScraperService
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


router = APIRouter(tags=["growth-dashboard"])

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


def _safe_float(value: Any) -> float:
    if value is None:
        return 0.0
    return float(value)


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
        else:
            current_comp = slot.get("competitor_best_rank")
            if current_comp is None or row.rank_position < current_comp:
                slot["competitor_best_rank"] = row.rank_position

    for item in by_keyword.values():
        client_rank = item.get("client_rank")
        competitor_rank = item.get("competitor_best_rank")
        delta = None
        if client_rank and competitor_rank:
            delta = competitor_rank - client_rank
        ranking_rows.append(
            {
                "keyword": item["keyword"],
                "client_rank": client_rank,
                "competitor_rank": competitor_rank,
                "delta": delta,
                "location": item["location"],
                "observed_at": _format_dt(item["observed_at"]),
            }
        )
    ranking_rows.sort(key=lambda item: (item["client_rank"] or 99, item["keyword"]))
    ranking_rows = ranking_rows[:5]

    if not ranking_rows:
        ranking_rows = [
            {"keyword": "pizza artesanal", "client_rank": 4, "competitor_rank": 2, "delta": -2, "location": "centro", "observed_at": _format_dt(datetime.now(tz=timezone.utc))},
            {"keyword": "delivery nocturno", "client_rank": 2, "competitor_rank": 5, "delta": 3, "location": "norte", "observed_at": _format_dt(datetime.now(tz=timezone.utc))},
            {"keyword": "brunch premium", "client_rank": 9, "competitor_rank": 3, "delta": -6, "location": "sur", "observed_at": _format_dt(datetime.now(tz=timezone.utc))},
            {"keyword": "cafeteria wifi", "client_rank": 5, "competitor_rank": 7, "delta": 2, "location": "oeste", "observed_at": _format_dt(datetime.now(tz=timezone.utc))},
            {"keyword": "desayunos saludables", "client_rank": 12, "competitor_rank": 8, "delta": -4, "location": "este", "observed_at": _format_dt(datetime.now(tz=timezone.utc))},
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
    radar_axes = _build_radar_axes([label for _key, label in RADAR_METRICS])
    radar_rings = [_build_radar_polygon([step] * len(RADAR_METRICS)) for step in (0.25, 0.5, 0.75, 1.0)]

    return {
        "user": user,
        "business_name": business_name,
        "snapshot_timestamp": _format_dt(client_snapshot.observed_at if client_snapshot else None),
        "client_metrics": client_metrics,
        "competitors": competitor_cards,
        "alerts": alerts[:12],
        "workers": workers,
        "report_history": _list_local_reports(user_id),
        "radar_axes": radar_axes,
        "radar_rings": radar_rings,
        "radar_series": [
            {
                "name": business_name,
                "stroke": "#14b8a6",
                "fill": "rgba(20, 184, 166, 0.22)",
                "points": _build_radar_polygon(client_series),
            },
            {
                "name": "Promedio competidores",
                "stroke": "#f97316",
                "fill": "rgba(249, 115, 22, 0.18)",
                "points": _build_radar_polygon(competitor_average),
            },
        ],
        "headline_kpis": {
            "competitor_count": len(competitor_cards),
            "unseen_alerts": sum(1 for alert in alerts[:12] if _severity_rank(alert["severity"]) >= 2),
            "worker_count": len([worker for worker in workers if worker["status"] == "online"]),
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
    axis.plot(angles, competitor_values, color="#c2410c", linewidth=2.2, label="Promedio competidores")
    axis.fill(angles, competitor_values, color="#c2410c", alpha=0.14)
    axis.legend(loc="upper right", bbox_to_anchor=(1.15, 1.15))
    axis.set_title("Radar de competencia", pad=18)
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


def _write_growth_pdf(context: dict[str, Any], user_id: UUID) -> dict[str, Any]:
    _ensure_pdf_dependencies()
    timestamp = datetime.now(tz=timezone.utc)
    filename = f"growth_report_{user_id}_{timestamp.strftime('%Y%m%d_%H%M%S')}.pdf"
    pdf_path = REPORTS_DIR / filename
    radar_chart = _build_radar_chart_image(context)
    gap_chart = _build_gap_chart_image(context)
    alert_rows = context["alerts"][:8]
    competitor_rows = context["competitors"][:8]

    html = f"""
    <!doctype html>
    <html lang="es">
      <head>
        <meta charset="utf-8" />
        <style>
          body {{ font-family: DejaVu Sans, Arial, sans-serif; color: #0f172a; margin: 28px; }}
          h1, h2, h3 {{ margin: 0 0 10px; }}
          .hero {{ padding: 24px; border-radius: 18px; background: linear-gradient(135deg, #0f766e, #1d4ed8); color: white; }}
          .grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 18px; margin-top: 20px; }}
          .card {{ border: 1px solid #dbe5f0; border-radius: 16px; padding: 18px; background: #fff; }}
          .metric {{ display: inline-block; width: 31%; margin-right: 2%; vertical-align: top; }}
          .metric strong {{ display:block; font-size: 24px; margin-top: 8px; }}
          table {{ width: 100%; border-collapse: collapse; font-size: 12px; }}
          th, td {{ text-align: left; padding: 8px 0; border-bottom: 1px solid #e2e8f0; }}
          .alert {{ padding: 10px 12px; border-radius: 12px; margin-bottom: 10px; background: #f8fafc; border: 1px solid #e2e8f0; }}
          .alert strong {{ display:block; }}
          .charts img {{ width: 100%; border-radius: 16px; border: 1px solid #e2e8f0; }}
          .footer {{ margin-top: 24px; font-size: 11px; color: #475569; }}
        </style>
      </head>
      <body>
        <section class="hero">
          <h1>Reporte estrategico Growth</h1>
          <p>{context['business_name']} · generado localmente el {timestamp.strftime('%Y-%m-%d %H:%M UTC')}</p>
        </section>

        <section class="card" style="margin-top:18px;">
          <div class="metric"><span>Competidores activos</span><strong>{context['headline_kpis']['competitor_count']}</strong></div>
          <div class="metric"><span>Alertas en feed</span><strong>{len(alert_rows)}</strong></div>
          <div class="metric"><span>Workers online</span><strong>{context['headline_kpis']['worker_count']}</strong></div>
        </section>

        <section class="grid charts">
          <article class="card">
            <h2>Radar de competencia</h2>
            <img src="data:image/png;base64,{radar_chart}" alt="Radar de competencia" />
          </article>
          <article class="card">
            <h2>Gap de reseñas</h2>
            <img src="data:image/png;base64,{gap_chart}" alt="Gap de reseñas" />
          </article>
        </section>

        <section class="grid">
          <article class="card">
            <h2>Benchmark competitivo</h2>
            <table>
              <thead>
                <tr>
                  <th>Competidor</th>
                  <th>Rating</th>
                  <th>Reseñas</th>
                  <th>Gap reseñas</th>
                  <th>Gap keyword</th>
                </tr>
              </thead>
              <tbody>
                {''.join([f"<tr><td>{row['name']}</td><td>{row['rating_avg'] if row['rating_avg'] is not None else '-'}</td><td>{row['review_count_total'] if row['review_count_total'] is not None else '-'}</td><td>{row['review_gap'] if row['review_gap'] is not None else '-'}</td><td>{row['keyword_gap'] if row['keyword_gap'] is not None else '-'}</td></tr>" for row in competitor_rows]) or '<tr><td colspan="5">No hay benchmark disponible.</td></tr>'}
              </tbody>
            </table>
          </article>
          <article class="card">
            <h2>Alertas inteligentes</h2>
            {''.join([f"<div class='alert'><strong>{row['title']}</strong><div>{row['message']}</div><small>{row['source']} · {row['timestamp_label']}</small></div>" for row in alert_rows]) or '<div class="alert">No hay alertas para este usuario.</div>'}
          </article>
        </section>

        <div class="footer">Archivo generado en {pdf_path}. Descargable desde /api/growth/reports/{filename}?user_id={user_id}</div>
      </body>
    </html>
    """

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
        service = GrowthScraperService(db)
        result = service.scrape_and_persist_all_competitors(user_id=user_id)
        summary_status = "ok"
        summary_message = (
            f"Deep scan completado: {result.total_competitors} competidores, "
            f"{len(result.successes)} exitosos, {len(result.failures)} con error."
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
