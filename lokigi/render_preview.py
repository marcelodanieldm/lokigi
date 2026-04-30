"""
Renderiza los dashboards Growth y Starter con datos mock y los guarda
como HTML estáticos en frontend/static/ para previsualización.
"""
from __future__ import annotations

import math
import sys
import uuid
import webbrowser
from datetime import datetime, timezone, timedelta
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, StrictUndefined

ROOT = Path(__file__).parent
TEMPLATES_DIR = ROOT / "backend" / "app" / "templates"
OUT_DIR = ROOT / "frontend" / "static"
DEMO_USER_ID = "00000000-0000-0000-0000-000000000001"

env = Environment(
    loader=FileSystemLoader(str(TEMPLATES_DIR)),
    undefined=StrictUndefined,
    autoescape=False,
)

# ─── helpers ────────────────────────────────────────────────────────────────

def _build_radar_axes(labels, cx=170, cy=170, r=120):
    axes = []
    n = len(labels)
    for i, label in enumerate(labels):
        angle = (-math.pi / 2) + (2 * math.pi * i / n)
        axes.append({
            "label": label,
            "line": f"{cx + math.cos(angle)*10:.2f},{cy + math.sin(angle)*10:.2f} {cx + math.cos(angle)*r:.2f},{cy + math.sin(angle)*r:.2f}",
            "label_x": f"{cx + math.cos(angle)*(r+26):.2f}",
            "label_y": f"{cy + math.sin(angle)*(r+26):.2f}",
            "anchor": "start" if cx + math.cos(angle)*(r+26) > cx+8 else ("end" if cx + math.cos(angle)*(r+26) < cx-8 else "middle"),
        })
    return axes


def _build_radar_polygon(values, cx=170, cy=170, r=120):
    n = len(values)
    pts = []
    for i, v in enumerate(values):
        angle = (-math.pi / 2) + (2 * math.pi * i / n)
        pts.append(f"{cx + math.cos(angle)*r*max(0, min(v,1)):.2f},{cy + math.sin(angle)*r*max(0, min(v,1)):.2f}")
    return " ".join(pts)


# ─── GROWTH MOCK DATA ────────────────────────────────────────────────────────

def build_growth_context():
    business_name = "La Terraza Demo"
    now = datetime.now(tz=timezone.utc)

    war_radar_dimensions = [
        {"key": "reputation", "label": "Reputación", "unit": "★", "client_value": 4.3, "competitor_value": 3.9, "client_ratio": 0.86, "competitor_ratio": 0.78, "note": "Score promedio de estrellas."},
        {"key": "activity",   "label": "Actividad",  "unit": "posts/30d", "client_value": 6, "competitor_value": 9, "client_ratio": 0.60, "competitor_ratio": 0.90, "note": "Google Posts últimos 30d."},
        {"key": "response",   "label": "Respuesta",  "unit": "%", "client_value": 72, "competitor_value": 55, "client_ratio": 0.72, "competitor_ratio": 0.55, "note": "% respuesta a reseñas."},
        {"key": "freshness",  "label": "Frescura",   "unit": "fotos", "client_value": 48, "competitor_value": 61, "client_ratio": 0.79, "competitor_ratio": 1.00, "note": "Inventario de fotos."},
        {"key": "engagement", "label": "Engagement", "unit": "reseñas/30d", "client_value": 14, "competitor_value": 11, "client_ratio": 1.00, "competitor_ratio": 0.79, "note": "Reseñas último mes."},
    ]
    war_labels = [r["label"] for r in war_radar_dimensions]
    radar_rings = [_build_radar_polygon([s]*5) for s in (0.25, 0.5, 0.75, 1.0)]

    competitors = [
        {"id": str(uuid.uuid4()), "name": "El Rincón Gourmet", "city": "Madrid", "country_code": "ES",
         "snapshot_at": "2026-04-28 08:00 UTC", "rating_avg": 4.1, "review_count_total": 320,
         "posts_count_30d": 9, "photos_count_total": 61, "services_count": 12, "engagement_score": 28.4,
         "rating_gap": -0.2, "review_gap": 80, "review_growth_30d_gap": -3, "keyword_gap": 0.08},
        {"id": str(uuid.uuid4()), "name": "Sabores del Norte", "city": "Madrid", "country_code": "ES",
         "snapshot_at": "2026-04-28 08:00 UTC", "rating_avg": 3.8, "review_count_total": 210,
         "posts_count_30d": 5, "photos_count_total": 39, "services_count": 8, "engagement_score": 18.0,
         "rating_gap": 0.5, "review_gap": -30, "review_growth_30d_gap": 2, "keyword_gap": -0.04},
        {"id": str(uuid.uuid4()), "name": "Bistró Central", "city": "Madrid", "country_code": "ES",
         "snapshot_at": "2026-04-28 08:00 UTC", "rating_avg": 4.4, "review_count_total": 450,
         "posts_count_30d": 11, "photos_count_total": 74, "services_count": 15, "engagement_score": 41.6,
         "rating_gap": -0.1, "review_gap": 210, "review_growth_30d_gap": -5, "keyword_gap": 0.12},
    ]

    def _pts(ranks):
        if not ranks: return ""
        n = len(ranks)
        pts = []
        for i, rk in enumerate(ranks):
            x = 2 + 92 * (i / max(n-1, 1))
            y = 2 + 24 * ((max(1, min(rk, 20)) - 1) / 19)
            pts.append(f"{x:.2f},{y:.2f}")
        return " ".join(pts)

    ranking_rows = [
        {"keyword": "pizza artesanal", "client_rank": 4, "competitor_rank": 2, "delta": -2, "location": "centro",
         "observed_at": "2026-04-28 09:00 UTC", "trend_arrow": "up",
         "client_trend_points": _pts([8,7,6,5,5,4,4]), "competitor_trend_points": _pts([3,3,2,2,2,2,2])},
        {"keyword": "delivery nocturno", "client_rank": 2, "competitor_rank": 5, "delta": 3, "location": "norte",
         "observed_at": "2026-04-28 09:00 UTC", "trend_arrow": "up",
         "client_trend_points": _pts([6,5,4,3,3,2,2]), "competitor_trend_points": _pts([7,7,6,6,5,5,5])},
        {"keyword": "brunch premium", "client_rank": 9, "competitor_rank": 3, "delta": -6, "location": "sur",
         "observed_at": "2026-04-28 09:00 UTC", "trend_arrow": "down",
         "client_trend_points": _pts([7,7,8,8,9,9,9]), "competitor_trend_points": _pts([5,5,4,4,3,3,3])},
        {"keyword": "cafetería wifi", "client_rank": 5, "competitor_rank": 7, "delta": 2, "location": "oeste",
         "observed_at": "2026-04-28 09:00 UTC", "trend_arrow": "up",
         "client_trend_points": _pts([9,8,7,6,6,5,5]), "competitor_trend_points": _pts([8,8,8,7,7,7,7])},
        {"keyword": "desayunos saludables", "client_rank": 12, "competitor_rank": 8, "delta": -4, "location": "este",
         "observed_at": "2026-04-28 09:00 UTC", "trend_arrow": "up",
         "client_trend_points": _pts([15,14,13,13,12,12,12]), "competitor_trend_points": _pts([11,10,10,9,9,8,8])},
    ]

    alerts = [
        {"title": "El Rincón Gourmet actualizó su menú hoy",
         "message": "Agregó nuevas categorías de servicio en Google Maps.",
         "severity": "medium", "badge": "amber", "source": "ScraperWorker",
         "feed_type": "menu_update", "timestamp": now - timedelta(hours=2),
         "timestamp_label": "hace 2 horas", "context_payload": {}},
        {"title": "Bistró Central: caída de sentimiento en Atención",
         "message": "Caída en reseñas sobre atención al cliente. ¡Oportunidad!",
         "severity": "high", "badge": "rose", "source": "ScraperWorker",
         "feed_type": "sentiment_drop", "timestamp": now - timedelta(hours=5),
         "timestamp_label": "hace 5 horas", "context_payload": {}},
        {"title": "Keyword conquistada: pizza artesanal",
         "message": "Pasaste del puesto #8 al #4 en zona centro.",
         "severity": "high", "badge": "emerald", "source": "Radar SERP",
         "feed_type": "keyword_conquest", "timestamp": now - timedelta(hours=8),
         "timestamp_label": "hace 8 horas", "context_payload": {"keyword": "pizza artesanal"}},
    ]

    spy_posts = [
        {"title": "El Rincón Gourmet lanzó oferta de menú ejecutivo",
         "summary": "Post de precio gancho para mediodía. Activa contra-oferta en horario pico.",
         "classification": "oferta", "competitor_name": "El Rincón Gourmet",
         "created_at": "hace 4 horas"},
    ]

    gap_rows = [
        {"competitor": "Bistró Central", "missing_services": ["mesas al aire libre", "pet friendly", "menú brunch"]},
    ]

    ai_actions = [
        {"title": "Contra-ataque: actualización menú El Rincón Gourmet",
         "prompt": "Genera un post destacando tu menú de temporada para responder a la actualización del competidor.",
         "severity": "medium"},
        {"title": "Aprovechar caída Bistró Central",
         "prompt": "Post enfocado en atención al cliente para captar usuarios insatisfechos.",
         "severity": "high"},
    ]

    visibility_cells = []
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
            level = "client" if owner == "Cliente" else "competitor"
            if owner == "Cliente" and score < 0.52:
                level = "contested"
            visibility_cells.append({"x": x, "y": y, "owner": owner, "score": round(score, 2), "level": level})

    workers = [{"name": "scraper@demo", "status": "online", "badge": "emerald",
                "summary": "Worker demo activo", "queues": ["scraping"], "active_tasks": 0, "processed_tasks": 142}]

    return {
        "user_id": DEMO_USER_ID,
        "business_name": business_name,
        "snapshot_timestamp": "2026-04-28 09:00 UTC",
        "client_metrics": {
            "rating_avg": 4.3, "review_count_total": 240, "posts_count_30d": 6,
            "photos_count_total": 48, "services_count": 11, "engagement_score": 67.2,
        },
        "competitors": competitors,
        "alerts": alerts,
        "workers": workers,
        "report_history": [],
        "war_radar_dimensions": war_radar_dimensions,
        "radar_axes": _build_radar_axes(war_labels),
        "radar_rings": radar_rings,
        "radar_series": [
            {"name": business_name, "stroke": "#14b8a6", "fill": "rgba(20,184,166,0.22)",
             "points": _build_radar_polygon([r["client_ratio"] for r in war_radar_dimensions])},
            {"name": "Promedio competidores", "stroke": "#f97316", "fill": "rgba(249,115,22,0.18)",
             "points": _build_radar_polygon([r["competitor_ratio"] for r in war_radar_dimensions])},
        ],
        "headline_kpis": {
            "competitor_count": len(competitors),
            "unseen_alerts": 2,
            "worker_count": 1,
            "market_share_pct": 58.3,
        },
        "ranking_rows": ranking_rows,
        "visibility_cells": visibility_cells,
        "spy_posts": spy_posts,
        "gap_rows": gap_rows,
        "ai_actions": ai_actions,
    }


# ─── STARTER MOCK DATA ───────────────────────────────────────────────────────

def build_starter_html():
    """Returns rendered HTML for the starter dashboard (inline Python HTML)."""
    # Minimal self-contained mock — we reproduce the helper directly.
    import html as _html

    def esc(s):
        return _html.escape(str(s or ""), quote=True)

    business_name = "Panadería Demo"
    status_text = "Conectado"
    status_color = "#0f766e"
    subtitle = "Cuenta: Panadería Demo"
    current_tone = "Cercano"
    tone_class = "tone-cercano"
    trend_color = "#047857"
    trend_symbol = "↗"
    trend_copy = "al alza"
    avg_rating_text = "4.5★"
    trend_delta_text = "0.2"
    hero_time_text = "2.4 h"
    replies_sent_month = 36
    minutes_saved_month = 144
    report_days_copy = "Faltan 2 días para el cierre del reporte mensual."
    days_to_report_close = 2

    pending_html = """
      <li class="pending-item">
        <div class="pending-top"><strong>María G.</strong><span class="stars">5★</span></div>
        <p class="pending-review">El pan de masa madre es increíble, volvería cada semana.</p>
        <p class="pending-reply">IA: ¡Muchas gracias, María! Nos alegra mucho que disfrutes nuestro pan. Te esperamos pronto 🥖</p>
      </li>
      <li class="pending-item">
        <div class="pending-top"><strong>Carlos M.</strong><span class="stars">4★</span></div>
        <p class="pending-review">Buen servicio aunque la espera fue un poco larga el sábado.</p>
        <p class="pending-reply">IA: Gracias por tu comentario, Carlos. Los sábados son nuestros días más concurridos; estamos trabajando para mejorar los tiempos.</p>
      </li>
    """

    recent_reviews_html = """
      <li class="review-item">
        <div class="review-top"><strong>Ana P.</strong><span>5★</span></div>
        <p>Siempre fresco, siempre delicioso. El mejor desayuno del barrio sin duda.</p>
      </li>
      <li class="review-item">
        <div class="review-top"><strong>Luis T.</strong><span>4★</span></div>
        <p>Muy buena calidad y amable atención. Los croissants son espectaculares.</p>
      </li>
      <li class="review-item">
        <div class="review-top"><strong>Sara V.</strong><span>5★</span></div>
        <p>Me encanta la variedad y el trato. Totalmente recomendado.</p>
      </li>
    """

    sentiment_html = """
      <div class="sentiment-row">
        <div class="sentiment-label">Positivas<span>28</span></div>
        <div class="sentiment-bar"><span style="width:78%; background:#60a5fa;"></span></div>
      </div>
      <div class="sentiment-row">
        <div class="sentiment-label">Neutrales<span>6</span></div>
        <div class="sentiment-bar"><span style="width:17%; background:#cbd5e1;"></span></div>
      </div>
      <div class="sentiment-row">
        <div class="sentiment-label">Negativas<span>2</span></div>
        <div class="sentiment-bar"><span style="width:5%; background:#f87171;"></span></div>
      </div>
    """

    keyword_html = """
      <span class="keyword-chip">masa madre · 14</span>
      <span class="keyword-chip">croissant · 9</span>
      <span class="keyword-chip">servicio · 7</span>
      <span class="keyword-chip">fresco · 6</span>
      <span class="keyword-chip">desayuno · 5</span>
    """

    tip_text = "Sube una foto nueva de tu producto estrella esta semana para aumentar la visibilidad en búsquedas locales."
    tip_focus = "seo local"
    tip_confidence_copy = "84%"
    tip_evidence = 12
    tip_fallback = False
    tip_badge = "Tip context-aware"
    tip_badge_class = "tip-badge"
    tip_signals_html = """
      <li>14 menciones de "masa madre" en reseñas recientes</li>
      <li>Competidor cercano subió 3 fotos esta semana</li>
      <li>Consultas por "panadería artesanal" en auge local</li>
    """

    history_items_html = """
      <li class="history-item">
        <div><div class="history-period">Marzo 2026</div><div class="history-meta">Estado PDF: ready</div></div>
        <div class="history-actions">
          <a href="#" class="btn" target="_blank">Ver Online</a>
          <a href="#" class="btn btn-download">Descargar PDF</a>
        </div>
      </li>
      <li class="history-item">
        <div><div class="history-period">Febrero 2026</div><div class="history-meta">Estado PDF: ready</div></div>
        <div class="history-actions">
          <a href="#" class="btn" target="_blank">Ver Online</a>
          <a href="#" class="btn btn-download">Descargar PDF</a>
        </div>
      </li>
    """

    velocity_current = "18 min"
    velocity_baseline = "3.2 h"
    velocity_improvement = "89.1%"
    velocity_note = "Comparado contra referencia de 24 h (sin historial previo)."
    has_optimization_alert = True
    optimization_center_html = """
      <div class="card optimization-card">
        <div class="optimization-head">
          <div>
            <div class="optimization-kicker">Centro de Optimización</div>
            <h2 style="margin:6px 0 0;font-size:20px;">Mejora tu perfil de Google Business</h2>
          </div>
          <span class="optimization-priority">🔥 Alta prioridad</span>
        </div>
        <div class="optimization-explainer">
          <p><strong>¿Por qué importa?</strong> Los perfiles completos obtienen hasta 7× más clics que los incompletos.</p>
        </div>
        <div class="optimization-metrics">
          <div class="optimization-metric"><span>Impacto estimado</span><strong>+22% visibilidad</strong></div>
          <div class="optimization-metric"><span>Dificultad</span><strong>Baja</strong></div>
          <div class="optimization-metric"><span>Tiempo</span><strong>~10 min</strong></div>
        </div>
      </div>
    """

    return f"""<!doctype html>
<html lang="es">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Dashboard Starter | Lokigi</title>
    <style>
      :root {{
        --bg: #eff3f8; --card: #ffffff; --text: #0f172a; --muted: #64748b;
        --border: #dbe3ee; --primary: #0f62fe; --primary-dark: #0b4fd4;
      }}
      * {{ box-sizing: border-box; }}
      body {{
        margin: 0;
        font-family: Arial, "Helvetica Neue", sans-serif;
        color: var(--text);
        background: radial-gradient(circle at 10% 0%, rgba(15,98,254,0.15), transparent 32%),
                    linear-gradient(180deg, #ffffff, var(--bg));
      }}
      .wrap {{ max-width: 1100px; margin: 0 auto; padding: 18px; }}
      .topbar {{ background: var(--card); border: 1px solid var(--border); border-radius: 16px; padding: 14px 18px; display: flex; justify-content: space-between; align-items: center; gap: 10px; }}
      .status {{ display: inline-flex; align-items: center; gap: 8px; padding: 6px 12px; border-radius: 999px; font-size: 12px; font-weight: 700; color: #fff; background: {status_color}; }}
      .subtitle {{ color: var(--muted); font-size: 14px; margin-top: 5px; }}
      .hero {{ margin-top: 14px; background: linear-gradient(135deg, #0f62fe, #0b4fd4); color: #fff; border-radius: 18px; padding: 24px; box-shadow: 0 14px 30px rgba(15,98,254,0.28); }}
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
      .sentiment-label {{ display:flex; justify-content:space-between; font-size:13px; margin-bottom:5px; color:#334155; }}
      .sentiment-bar {{ height:10px; background:#e5e7eb; border-radius:999px; overflow:hidden; }}
      .sentiment-bar span {{ display:block; height:100%; border-radius:999px; }}
      .keyword-cloud {{ display:flex; flex-wrap:wrap; gap:8px; }}
      .keyword-chip {{ display:inline-flex; align-items:center; padding:7px 12px; border-radius:999px; background:#eef5ff; color:#1d4ed8; font-size:13px; font-weight:700; }}
      .tip-card {{ margin-top:14px; border:1px solid #bfdbfe; background:linear-gradient(180deg,#f8fbff,#eef5ff); }}
      .tip-header {{ display:flex; justify-content:space-between; gap:10px; align-items:center; flex-wrap:wrap; margin-bottom:10px; }}
      .tip-badge {{ display:inline-flex; border-radius:999px; padding:6px 10px; font-size:12px; font-weight:700; color:#0f62fe; background:rgba(15,98,254,0.12); }}
      .tip-badge.fallback {{ color:#b45309; background:rgba(245,158,11,0.22); }}
      .tip-main {{ font-size:16px; line-height:1.45; color:#0f172a; margin:0 0 10px; }}
      .tip-meta {{ display:flex; gap:8px; flex-wrap:wrap; margin-bottom:10px; }}
      .tip-chip {{ display:inline-flex; border-radius:999px; padding:6px 10px; border:1px solid #dbe3ee; background:#fff; font-size:12px; color:#334155; }}
      .tip-signals {{ margin:0; padding-left:18px; color:#475569; font-size:13px; line-height:1.45; }}
      .pending-list, .reviews {{ list-style:none; margin:0; padding:0; display:grid; gap:10px; }}
      .pending-item, .review-item {{ border:1px solid var(--border); border-radius:12px; padding:10px 12px; background:#fbfcff; }}
      .pending-top, .review-top {{ display:flex; align-items:center; justify-content:space-between; margin-bottom:5px; }}
      .pending-review, .pending-reply, .review-item p {{ margin:0; font-size:13px; color:#334155; line-height:1.45; }}
      .pending-reply {{ color:#475569; margin-top:4px; }}
      .stars {{ color:#a16207; font-weight:700; }}
      .empty {{ border:1px dashed #cbd5e1; border-radius:12px; padding:12px; color:var(--muted); }}
      .history-list {{ list-style:none; margin:0; padding:0; display:grid; gap:10px; }}
      .history-item {{ border:1px solid var(--border); border-radius:12px; padding:11px 12px; display:flex; justify-content:space-between; align-items:center; gap:10px; background:#fbfcff; }}
      .history-period {{ font-size:14px; font-weight:700; color:#0f172a; }}
      .history-meta {{ font-size:12px; color:var(--muted); margin-top:4px; }}
      .history-actions {{ display:flex; gap:8px; flex-wrap:wrap; }}
      .btn-download {{ background:var(--primary); border-color:var(--primary); color:#fff; }}
      .btn {{ display:inline-flex; align-items:center; justify-content:center; text-decoration:none; padding:10px 14px; border-radius:10px; border:1px solid var(--border); background:#fff; color:var(--text); font-weight:700; font-size:14px; }}
      .btn.primary {{ background:var(--primary); border-color:var(--primary); color:#fff; }}
      .tone-pill {{ display:inline-flex; align-items:center; border-radius:999px; padding:6px 10px; font-size:12px; font-weight:700; }}
      .tone-cercano {{ background:rgba(25,135,84,0.12); color:#146c43; }}
      .optimization-card {{ margin-top:14px; border:1px solid #bfdbfe; background:linear-gradient(180deg,#ffffff,#f8fbff); }}
      .optimization-head {{ display:flex; justify-content:space-between; gap:12px; align-items:flex-start; flex-wrap:wrap; }}
      .optimization-kicker {{ font-size:12px; text-transform:uppercase; letter-spacing:.05em; color:#0f62fe; font-weight:700; margin-bottom:6px; }}
      .optimization-priority {{ display:inline-flex; align-items:center; border-radius:999px; padding:8px 12px; background:#e0ecff; color:#0f62fe; font-size:12px; font-weight:700; }}
      .optimization-explainer {{ margin-top:12px; border:1px solid #dbeafe; border-radius:12px; padding:12px; background:#eff6ff; }}
      .optimization-explainer p {{ margin:6px 0 0; color:#334155; line-height:1.5; }}
      .optimization-metrics {{ display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:10px; margin-top:12px; }}
      .optimization-metric {{ border:1px solid var(--border); border-radius:12px; padding:10px 12px; background:#fff; }}
      .optimization-metric span {{ display:block; color:var(--muted); font-size:12px; text-transform:uppercase; letter-spacing:.04em; margin-bottom:6px; }}
      .optimization-metric strong {{ font-size:16px; }}
      .banner {{ margin-top:14px; background:linear-gradient(135deg,#fff7db,#fff1c4); border:1px solid #f8d36d; border-radius:14px; padding:12px 14px; display:flex; justify-content:space-between; align-items:center; gap:12px; }}
      .banner strong {{ color:#92400e; }}
      @media (max-width: 900px) {{ .hero-grid, .grid, .value-grid, .optimization-metrics {{ grid-template-columns:1fr; }} .velocity-grid {{ grid-template-columns:1fr; }} }}
      /* ── Navbar ── */
      .lokigi-nav {{ position:sticky;top:0;z-index:100;background:#fff;border-bottom:1px solid #dbe3ee;padding:0 20px;display:flex;align-items:center;gap:2px;height:58px;box-shadow:0 1px 4px rgba(15,23,42,.06); }}
      .lokigi-nav-brand {{ display:flex;align-items:center;gap:10px;margin-right:auto; }}
      .lokigi-nav-logo {{ display:inline-flex;align-items:center;justify-content:center;width:32px;height:32px;border-radius:8px;background:#0f62fe;color:#fff;font-weight:900;font-size:14px;text-decoration:none; }}
      .lokigi-nav-name {{ font-weight:800;font-size:16px;color:#0f172a;text-decoration:none; }}
      .lokigi-nav-plan {{ display:inline-flex;padding:4px 10px;border-radius:999px;background:#eef5ff;color:#0f62fe;font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:.05em; }}
      .lokigi-nav-link {{ display:inline-flex;align-items:center;gap:6px;padding:8px 12px;border-radius:8px;text-decoration:none;font-weight:600;font-size:14px;color:#475569;transition:background .15s,color .15s; }}
      .lokigi-nav-link:hover,.lokigi-nav-link:focus {{ background:#f1f5f9;color:#0f172a; }}
      .lokigi-nav-link.active {{ color:#0f62fe;background:#eff6ff; }}
      .lokigi-nav-tone {{ display:inline-flex;align-items:center;border-radius:999px;padding:5px 11px;font-size:12px;font-weight:700;margin:0 6px; }}
      .lokigi-nav-account {{ margin-left:4px;display:inline-flex;align-items:center;gap:7px;padding:8px 14px;border-radius:8px;text-decoration:none;font-weight:700;font-size:14px;color:#0f62fe;background:#eef5ff;border:1px solid #bfdbfe; }}
      .lokigi-nav-account:hover {{ background:#dbeafe;border-color:#93c5fd; }}
      @media (max-width:640px) {{ .lokigi-nav {{ padding:0 12px; }} .lokigi-nav-link {{ padding:8px 8px;font-size:13px; }} .lokigi-nav-tone {{ display:none; }} }}
    </style>
  </head>
  <body>
    <nav class="lokigi-nav" role="navigation" aria-label="Navegación principal">
      <div class="lokigi-nav-brand">
        <a class="lokigi-nav-logo" href="starter_dashboard_preview.html">L</a>
        <a class="lokigi-nav-name" href="starter_dashboard_preview.html">Lokigi</a>
        <span class="lokigi-nav-plan">Starter</span>
      </div>
      <a class="lokigi-nav-link active" href="starter_dashboard_preview.html">🏠 Dashboard</a>
      <a class="lokigi-nav-link" href="#reviews-section">💬 Reseñas</a>
      <a class="lokigi-nav-link" href="#historial">📊 Reportes</a>
      <span class="lokigi-nav-tone {tone_class}">🎤 {current_tone}</span>
      <a class="lokigi-nav-account" href="mi_cuenta_starter.html">👤 Mi Cuenta</a>
    </nav>
    <div class="wrap">

      <section class="hero">
        <div class="hero-kicker">Valor generado por IA este mes</div>
        <div class="hero-grid">
          <div>
            <h1>{hero_time_text} ahorradas</h1>
            <p>{replies_sent_month} respuestas enviadas · {minutes_saved_month} minutos recuperados</p>
          </div>
          <div class="hero-mini">
            <span style="font-size:12px;opacity:.85;text-transform:uppercase;letter-spacing:.05em;">Puntuación</span>
            <strong>{avg_rating_text}</strong>
            <span class="rep-trend">{trend_symbol} {trend_delta_text} pts {trend_copy}</span>
          </div>
        </div>
      </section>

      <div class="grid">
        <div class="card">
          <h2>Reputación</h2>
          <div class="rep-score">{avg_rating_text}</div>
          <div class="rep-trend">{trend_symbol} {trend_delta_text} pts · <span class="muted">vs mes anterior</span></div>
        </div>
        <div class="card">
          <h2>Aprobación pendiente</h2>
          <ul class="pending-list">{pending_html}</ul>
        </div>
      </div>

      <div class="value-grid">
        <div class="value-card">
          <div class="value-title">Velocidad de respuesta</div>
          <div class="velocity-grid">
            <div class="velocity-stat"><strong>{velocity_current}</strong><span>Actual</span></div>
            <div class="velocity-stat"><strong>{velocity_baseline}</strong><span>Referencia</span></div>
            <div class="velocity-stat"><strong style="color:#16a34a;">{velocity_improvement}</strong><span>Mejora</span></div>
          </div>
          <p class="value-footnote">{velocity_note}</p>
        </div>
        <div class="value-card">
          <div class="value-title">Sentimiento del mes</div>
          {sentiment_html}
        </div>
        <div class="value-card">
          <div class="value-title">Conceptos clave</div>
          <div class="keyword-cloud">{keyword_html}</div>
        </div>
      </div>

      <div class="card tip-card">
        <div class="tip-header">
          <h2 style="margin:0;font-size:18px;">Tip del día</h2>
          <span class="{tip_badge_class}">{tip_badge}</span>
        </div>
        <p class="tip-main">{tip_text}</p>
        <div class="tip-meta">
          <span class="tip-chip">Foco: {tip_focus}</span>
          <span class="tip-chip">Confianza: {tip_confidence_copy}</span>
          <span class="tip-chip">Evidencias: {tip_evidence}</span>
        </div>
        <ul class="tip-signals">{tip_signals_html}</ul>
      </div>

      {optimization_center_html}

      <div class="card" style="margin-top:14px;" id="reviews-section">
        <h2>Reseñas recientes</h2>
        <ul class="reviews">{recent_reviews_html}</ul>
        <div style="display:flex;gap:10px;flex-wrap:wrap;margin-top:14px;">
          <a href="mi_cuenta_starter.html#voz-marca" class="btn">🎤 Voz de marca</a>
          <a href="mi_cuenta_starter.html#perfil" class="btn">⚙️ Mi perfil</a>
          <a href="mi_cuenta_starter.html#suscripcion" class="btn">💳 Suscripción</a>
        </div>
      </div>

      <div class="card" style="margin-top:14px;" id="historial">
        <h2>Historial de reportes</h2>
        <ul class="history-list">{history_items_html}</ul>
      </div>

      <div class="banner">
        <div>
          <strong>⏳ Cierre de reporte</strong>
          <p style="margin:4px 0 0;color:#92400e;">{report_days_copy}</p>
        </div>
      </div>

    </div>
  </body>
</html>"""


# ─── NAVBAR & MI CUENTA BUILDERS ─────────────────────────────────────────────

def build_growth_navbar() -> str:
    """Returns sticky dark navbar HTML for the Growth dashboard (Tailwind)."""
    return (
        '<nav class="sticky top-0 z-50 flex items-center gap-1 px-5 h-14 '
        'bg-stone-950/95 backdrop-blur-sm border-b border-white/10 shadow-md">\n'
        '  <div class="flex items-center gap-2.5 mr-auto">\n'
        '    <a href="growth_dashboard_preview.html" class="flex items-center justify-center '
        'w-8 h-8 rounded-lg bg-emerald-500 text-stone-950 font-black text-sm no-underline">L</a>\n'
        '    <a href="growth_dashboard_preview.html" '
        'class="font-bold text-white text-base no-underline">Lokigi</a>\n'
        '    <span class="px-2.5 py-0.5 rounded-full bg-emerald-500/15 text-emerald-300 '
        'text-xs font-bold uppercase tracking-wider">Growth</span>\n'
        '  </div>\n'
        '  <a href="growth_dashboard_preview.html" class="px-3 py-2 rounded-lg text-sm '
        'text-stone-200 font-semibold hover:bg-white/5 no-underline">🏠 Dashboard</a>\n'
        '  <a href="#reviews" class="px-3 py-2 rounded-lg text-sm text-stone-400 '
        'font-medium hover:text-white hover:bg-white/5 no-underline">💬 Reseñas</a>\n'
        '  <a href="#radar" class="px-3 py-2 rounded-lg text-sm text-stone-400 '
        'font-medium hover:text-white hover:bg-white/5 no-underline">📡 Competencia</a>\n'
        '  <a href="#reportes" class="px-3 py-2 rounded-lg text-sm text-stone-400 '
        'font-medium hover:text-white hover:bg-white/5 no-underline">📊 Reportes</a>\n'
        '  <a href="mi_cuenta_growth.html" class="ml-2 px-4 py-2 rounded-lg text-sm '
        'text-stone-300 bg-white/5 border border-white/10 hover:bg-white/10 '
        'font-semibold no-underline">👤 Mi Cuenta</a>\n'
        '</nav>\n'
    )


def build_mi_cuenta_starter_html() -> str:
    """Returns static Mi Cuenta page for the Starter plan."""
    return """\
<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Mi Cuenta | Lokigi Starter</title>
  <style>
    :root { --bg:#eff3f8; --card:#fff; --text:#0f172a; --muted:#64748b; --border:#dbe3ee; --primary:#0f62fe; --primary-dark:#0b4fd4; }
    * { box-sizing:border-box; }
    body { margin:0; font-family:Arial,"Helvetica Neue",sans-serif; color:var(--text);
      background: radial-gradient(circle at 10% 0%, rgba(15,98,254,.12), transparent 30%),
                  linear-gradient(180deg,#fff,var(--bg)); }
    /* Nav */
    .lokigi-nav { position:sticky;top:0;z-index:100;background:#fff;border-bottom:1px solid var(--border);
      padding:0 20px;display:flex;align-items:center;gap:2px;height:58px;box-shadow:0 1px 4px rgba(15,23,42,.06); }
    .lokigi-nav-brand { display:flex;align-items:center;gap:10px;margin-right:auto; }
    .lokigi-nav-logo { display:inline-flex;align-items:center;justify-content:center;width:32px;height:32px;
      border-radius:8px;background:#0f62fe;color:#fff;font-weight:900;font-size:14px;text-decoration:none; }
    .lokigi-nav-name { font-weight:800;font-size:16px;color:#0f172a;text-decoration:none; }
    .lokigi-nav-plan { display:inline-flex;padding:4px 10px;border-radius:999px;background:#eef5ff;
      color:#0f62fe;font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:.05em; }
    .lokigi-nav-link { display:inline-flex;align-items:center;gap:6px;padding:8px 12px;border-radius:8px;
      text-decoration:none;font-weight:600;font-size:14px;color:#475569; }
    .lokigi-nav-link:hover { background:#f1f5f9;color:#0f172a; }
    .lokigi-nav-link.active { color:#0f62fe;background:#eff6ff; }
    .lokigi-nav-account { margin-left:4px;display:inline-flex;align-items:center;gap:7px;padding:8px 14px;
      border-radius:8px;text-decoration:none;font-weight:700;font-size:14px;color:#0f62fe;
      background:#eef5ff;border:1px solid #bfdbfe; }
    /* Content */
    .wrap { max-width:760px; margin:0 auto; padding:32px 18px 56px; }
    .page-head { margin-bottom:32px; }
    .page-head h1 { margin:0 0 6px; font-size:30px; }
    .page-head p { margin:0; color:var(--muted); font-size:15px; }
    .section-card { background:var(--card); border:1px solid var(--border); border-radius:18px;
      padding:22px 24px; margin-bottom:18px; scroll-margin-top:72px; }
    .section-head { display:flex; align-items:center; gap:14px; margin-bottom:18px; }
    .s-icon { display:inline-flex;align-items:center;justify-content:center;width:42px;height:42px;
      border-radius:14px;font-size:20px;flex-shrink:0; }
    .s-blue { background:#eef5ff; } .s-green { background:#ecfdf5; }
    .s-yellow { background:#fffbeb; } .s-red { background:#fff1f2; }
    .section-head h2 { margin:0; font-size:17px; }
    .section-head p { margin:3px 0 0; color:var(--muted); font-size:13px; }
    .row { display:flex;justify-content:space-between;align-items:center;padding:11px 0;
      border-bottom:1px solid #f1f5f9;gap:10px; }
    .row:last-child { border-bottom:none;padding-bottom:0; }
    .row-label { font-size:13px; color:var(--muted); }
    .row-value { font-size:14px; font-weight:700; color:var(--text); }
    .badge-ok { display:inline-flex;padding:4px 10px;border-radius:999px;background:#ecfdf5;color:#166534;font-size:12px;font-weight:700; }
    .badge-plan { display:inline-flex;padding:4px 10px;border-radius:999px;background:#eef5ff;color:#0f62fe;font-size:12px;font-weight:700; }
    .tone-pill { display:inline-flex;padding:5px 12px;border-radius:999px;font-size:13px;font-weight:700;background:rgba(25,135,84,.12);color:#146c43; }
    .btn-row { display:flex;gap:10px;flex-wrap:wrap;margin-top:18px; }
    .btn { display:inline-flex;align-items:center;justify-content:center;text-decoration:none;
      padding:10px 16px;border-radius:10px;border:1px solid var(--border);background:#fff;
      color:var(--text);font-weight:700;font-size:14px; }
    .btn:hover { background:#f8fafc; }
    .btn-primary { background:var(--primary);border-color:var(--primary);color:#fff; }
    .btn-primary:hover { background:var(--primary-dark); }
    .btn-danger { background:#fff1f2;border-color:#fecdd3;color:#be123c; }
    .btn-danger:hover { background:#fff5f5; }
    /* Upgrade card */
    .upgrade-card { background:linear-gradient(135deg,#0f172a,#0c4a6e); border:1px solid #0369a1;
      border-radius:18px; padding:24px; margin-bottom:18px; color:#fff; }
    .upgrade-card h2 { margin:0 0 8px; font-size:20px; }
    .upgrade-card p { margin:0 0 16px; color:rgba(255,255,255,.75); font-size:14px; }
    .feat-list { list-style:none;margin:0 0 20px;padding:0;display:grid;gap:8px; }
    .feat-list li { display:flex;align-items:center;gap:8px;font-size:13px;color:rgba(255,255,255,.9); }
    .feat-list li::before { content:"✓";display:inline-flex;align-items:center;justify-content:center;
      width:18px;height:18px;border-radius:999px;background:rgba(52,211,153,.2);color:#34d399;
      font-size:11px;font-weight:900;flex-shrink:0; }
    .btn-upgrade { display:inline-flex;align-items:center;justify-content:center;text-decoration:none;
      padding:12px 20px;border-radius:12px;background:linear-gradient(135deg,#0f62fe,#7c3aed);
      color:#fff;font-weight:700;font-size:15px; }
    /* Danger */
    .danger-zone { border:1px solid #fecdd3;background:#fff5f7;border-radius:18px;padding:22px 24px; }
    .danger-zone h2 { margin:0 0 6px;font-size:17px;color:#be123c; }
    .danger-zone p { margin:0 0 16px;font-size:14px;color:#9f1239; }
  </style>
</head>
<body>
  <nav class="lokigi-nav" role="navigation" aria-label="Navegación principal">
    <div class="lokigi-nav-brand">
      <a class="lokigi-nav-logo" href="starter_dashboard_preview.html">L</a>
      <a class="lokigi-nav-name" href="starter_dashboard_preview.html">Lokigi</a>
      <span class="lokigi-nav-plan">Starter</span>
    </div>
    <a class="lokigi-nav-link" href="starter_dashboard_preview.html">🏠 Dashboard</a>
    <a class="lokigi-nav-link" href="starter_dashboard_preview.html#reviews-section">💬 Reseñas</a>
    <a class="lokigi-nav-link" href="starter_dashboard_preview.html#historial">📊 Reportes</a>
    <a class="lokigi-nav-account active" href="mi_cuenta_starter.html">👤 Mi Cuenta</a>
  </nav>
  <div class="wrap">
    <div class="page-head">
      <h1>Mi Cuenta</h1>
      <p>Gestiona tu perfil, voz de marca y suscripción desde un solo lugar.</p>
    </div>

    <!-- Perfil del Negocio -->
    <div class="section-card" id="perfil">
      <div class="section-head">
        <div class="s-icon s-blue">🏪</div>
        <div><h2>Perfil del Negocio</h2><p>Datos de tu negocio conectado a Google Maps</p></div>
      </div>
      <div class="row"><span class="row-label">Nombre del negocio</span><span class="row-value">Panadería Demo</span></div>
      <div class="row"><span class="row-label">Estado de conexión</span><span class="badge-ok">✓ Conectado — Google Maps</span></div>
      <div class="row"><span class="row-label">Cuenta Google</span><span class="row-value">panaderia.demo@gmail.com</span></div>
      <div class="row"><span class="row-label">Plan activo</span><span class="badge-plan">Plan Starter</span></div>
      <div class="btn-row">
        <a href="#" class="btn">✏️ Editar nombre</a>
        <a href="#" class="btn">🔗 Reconectar Google</a>
      </div>
    </div>

    <!-- Voz de Marca -->
    <div class="section-card" id="voz-marca">
      <div class="section-head">
        <div class="s-icon s-green">🎤</div>
        <div><h2>Voz de Marca</h2><p>Tono que usa la IA para redactar respuestas a reseñas</p></div>
      </div>
      <div class="row"><span class="row-label">Tono activo</span><span class="tone-pill">Cercano</span></div>
      <div class="row"><span class="row-label">Descripción</span><span class="row-value" style="font-weight:400;color:#475569;">Cálido, empático y en primera persona.</span></div>
      <div class="row"><span class="row-label">Palabras destacadas en reseñas</span><span class="row-value">masa madre · croissant · fresco</span></div>
      <div class="btn-row">
        <a href="#" class="btn btn-primary">Cambiar tono de voz</a>
      </div>
    </div>

    <!-- Suscripción -->
    <div class="section-card" id="suscripcion">
      <div class="section-head">
        <div class="s-icon s-yellow">💳</div>
        <div><h2>Suscripción y Facturación</h2><p>Detalle de tu plan y próximo cobro</p></div>
      </div>
      <div class="row"><span class="row-label">Plan</span><span class="badge-plan">Starter — €29/mes</span></div>
      <div class="row"><span class="row-label">Estado</span><span class="row-value" style="color:#16a34a;">✓ Activo</span></div>
      <div class="row"><span class="row-label">Próxima renovación</span><span class="row-value">1 Junio 2026</span></div>
      <div class="row"><span class="row-label">Método de pago</span><span class="row-value">•••• •••• •••• 4242</span></div>
      <div class="btn-row">
        <a href="cancellation/step1_subscription.html" class="btn">📄 Ver facturas</a>
        <a href="#" class="btn">💳 Cambiar tarjeta</a>
      </div>
    </div>

    <!-- Upgrade -->
    <div class="upgrade-card">
      <h2>✨ Pasa a Growth Edition</h2>
      <p>Desbloquea inteligencia competitiva, scraping en tiempo real y radar estratégico.</p>
      <ul class="feat-list">
        <li>Radar de Guerra con 5 competidores monitorizados</li>
        <li>Keyword Tracker — posicionamiento en tiempo real</li>
        <li>Live Feed de movimientos de la competencia</li>
        <li>AI Action Center con sugerencias de contenido</li>
        <li>Informes PDF mensuales avanzados</li>
      </ul>
      <a href="onboarding/step1_search.html" class="btn-upgrade">🚀 Ver plan Growth — €79/mes</a>
    </div>

    <!-- Zona de peligro -->
    <div class="danger-zone">
      <h2>⚠️ Zona de peligro</h2>
      <p>Acciones que modifican o cancelan tu suscripción activa.</p>
      <div class="btn-row">
        <a href="cancellation/step1_subscription.html" class="btn btn-danger">⏸ Pausar suscripción</a>
        <a href="cancellation/step1_subscription.html" class="btn btn-danger">✕ Cancelar suscripción</a>
      </div>
    </div>
  </div>
</body>
</html>"""


def build_mi_cuenta_growth_html() -> str:
    """Returns static Mi Cuenta page for the Growth plan (dark Tailwind theme)."""
    return """\
<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Mi Cuenta | Lokigi Growth</title>
  <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="min-h-screen bg-stone-950 text-stone-100">
  <nav class="sticky top-0 z-50 flex items-center gap-1 px-5 h-14 bg-stone-950/95 backdrop-blur-sm border-b border-white/10 shadow-md">
    <div class="flex items-center gap-2.5 mr-auto">
      <a href="growth_dashboard_preview.html" class="flex items-center justify-center w-8 h-8 rounded-lg bg-emerald-500 text-stone-950 font-black text-sm no-underline">L</a>
      <a href="growth_dashboard_preview.html" class="font-bold text-white text-base no-underline">Lokigi</a>
      <span class="px-2.5 py-0.5 rounded-full bg-emerald-500/15 text-emerald-300 text-xs font-bold uppercase tracking-wider">Growth</span>
    </div>
    <a href="growth_dashboard_preview.html" class="px-3 py-2 rounded-lg text-sm text-stone-400 font-medium hover:text-white hover:bg-white/5 no-underline">🏠 Dashboard</a>
    <a href="growth_dashboard_preview.html#reviews" class="px-3 py-2 rounded-lg text-sm text-stone-400 font-medium hover:text-white hover:bg-white/5 no-underline">💬 Reseñas</a>
    <a href="growth_dashboard_preview.html#radar" class="px-3 py-2 rounded-lg text-sm text-stone-400 font-medium hover:text-white hover:bg-white/5 no-underline">📡 Competencia</a>
    <a href="growth_dashboard_preview.html#reportes" class="px-3 py-2 rounded-lg text-sm text-stone-400 font-medium hover:text-white hover:bg-white/5 no-underline">📊 Reportes</a>
    <a href="mi_cuenta_growth.html" class="ml-2 px-4 py-2 rounded-lg text-sm text-emerald-300 bg-emerald-500/10 border border-emerald-500/20 font-semibold no-underline">👤 Mi Cuenta</a>
  </nav>
  <div class="mx-auto max-w-2xl px-4 py-8 sm:px-6 pb-16">
    <div class="mb-8">
      <p class="text-xs uppercase tracking-[.2em] text-emerald-300/70 mb-1">Configuración</p>
      <h1 class="text-3xl font-bold text-white">Mi Cuenta</h1>
      <p class="mt-1 text-stone-400 text-sm">Gestiona tu perfil, voz de marca, competidores y suscripción Growth.</p>
    </div>

    <!-- Perfil del Negocio -->
    <section id="perfil" class="rounded-3xl border border-white/10 bg-white/5 p-6 mb-5 scroll-mt-16">
      <div class="flex items-center gap-3 mb-5">
        <div class="flex items-center justify-center w-10 h-10 rounded-2xl bg-sky-500/15 text-xl">🏪</div>
        <div>
          <h2 class="text-lg font-semibold text-white m-0">Perfil del Negocio</h2>
          <p class="text-xs text-stone-400 mt-0.5">Datos de tu negocio en Google Maps</p>
        </div>
      </div>
      <div class="space-y-0 divide-y divide-white/5">
        <div class="flex justify-between items-center py-3">
          <span class="text-sm text-stone-400">Nombre del negocio</span>
          <span class="text-sm font-semibold text-white">La Terraza Demo</span>
        </div>
        <div class="flex justify-between items-center py-3">
          <span class="text-sm text-stone-400">Estado</span>
          <span class="px-2.5 py-1 rounded-full bg-emerald-500/15 text-emerald-300 text-xs font-bold">✓ Conectado — Google Maps</span>
        </div>
        <div class="flex justify-between items-center py-3">
          <span class="text-sm text-stone-400">Cuenta Google</span>
          <span class="text-sm font-semibold text-white">laterraza.demo@gmail.com</span>
        </div>
        <div class="flex justify-between items-center py-3">
          <span class="text-sm text-stone-400">Plan activo</span>
          <span class="px-2.5 py-1 rounded-full bg-emerald-500/15 text-emerald-300 text-xs font-bold">Growth Edition</span>
        </div>
      </div>
      <div class="flex gap-3 mt-5 flex-wrap">
        <a href="#" class="px-4 py-2 rounded-xl border border-white/10 bg-white/5 text-sm font-semibold text-stone-300 hover:bg-white/10 no-underline">✏️ Editar nombre</a>
        <a href="#" class="px-4 py-2 rounded-xl border border-white/10 bg-white/5 text-sm font-semibold text-stone-300 hover:bg-white/10 no-underline">🔗 Reconectar Google</a>
      </div>
    </section>

    <!-- Voz de Marca -->
    <section id="voz-marca" class="rounded-3xl border border-white/10 bg-white/5 p-6 mb-5 scroll-mt-16">
      <div class="flex items-center gap-3 mb-5">
        <div class="flex items-center justify-center w-10 h-10 rounded-2xl bg-emerald-500/15 text-xl">🎤</div>
        <div>
          <h2 class="text-lg font-semibold text-white m-0">Voz de Marca</h2>
          <p class="text-xs text-stone-400 mt-0.5">Tono que usa la IA para redactar respuestas</p>
        </div>
      </div>
      <div class="divide-y divide-white/5">
        <div class="flex justify-between items-center py-3">
          <span class="text-sm text-stone-400">Tono activo</span>
          <span class="px-3 py-1 rounded-full bg-emerald-500/15 text-emerald-300 text-sm font-bold">Cercano</span>
        </div>
        <div class="flex justify-between items-center py-3">
          <span class="text-sm text-stone-400">Descripción</span>
          <span class="text-sm text-stone-300">Cálido, empático, en primera persona</span>
        </div>
      </div>
      <div class="flex gap-3 mt-5">
        <a href="onboarding/step4_brand_voice.html" class="px-4 py-2 rounded-xl bg-emerald-500 text-stone-950 text-sm font-bold hover:bg-emerald-400 no-underline">Cambiar tono de voz</a>
      </div>
    </section>

    <!-- Competidores -->
    <section id="competidores" class="rounded-3xl border border-white/10 bg-white/5 p-6 mb-5 scroll-mt-16">
      <div class="flex items-center gap-3 mb-5">
        <div class="flex items-center justify-center w-10 h-10 rounded-2xl bg-amber-500/15 text-xl">👁️</div>
        <div>
          <h2 class="text-lg font-semibold text-white m-0">Competidores Monitorizados</h2>
          <p class="text-xs text-stone-400 mt-0.5">Gestiona el radar de scraping de tu zona</p>
        </div>
      </div>
      <div class="divide-y divide-white/5">
        <div class="flex justify-between items-center py-3">
          <span class="text-sm text-stone-400">Activos en radar</span>
          <span class="text-sm font-bold text-white">3 competidores</span>
        </div>
        <div class="flex justify-between items-center py-3">
          <span class="text-sm text-stone-400">Zona monitoreada</span>
          <span class="text-sm font-bold text-white">Madrid Centro</span>
        </div>
        <div class="flex justify-between items-center py-3">
          <span class="text-sm text-stone-400">Frecuencia de scraping</span>
          <span class="text-sm font-bold text-white">Cada 8 h</span>
        </div>
        <div class="flex justify-between items-center py-3">
          <span class="text-sm text-stone-400">Keywords rastreadas</span>
          <span class="text-sm font-bold text-white">5 keywords activas</span>
        </div>
      </div>
      <div class="flex gap-3 mt-5 flex-wrap">
        <a href="onboarding/step3_competitors.html" class="px-4 py-2 rounded-xl border border-white/10 bg-white/5 text-sm font-semibold text-stone-300 hover:bg-white/10 no-underline">⚙️ Configurar competidores</a>
        <a href="onboarding/step2_keywords.html" class="px-4 py-2 rounded-xl border border-white/10 bg-white/5 text-sm font-semibold text-stone-300 hover:bg-white/10 no-underline">🔑 Configurar keywords</a>
      </div>
    </section>

    <!-- Suscripción -->
    <section id="suscripcion" class="rounded-3xl border border-white/10 bg-white/5 p-6 mb-5 scroll-mt-16">
      <div class="flex items-center gap-3 mb-5">
        <div class="flex items-center justify-center w-10 h-10 rounded-2xl bg-violet-500/15 text-xl">💳</div>
        <div>
          <h2 class="text-lg font-semibold text-white m-0">Suscripción y Facturación</h2>
          <p class="text-xs text-stone-400 mt-0.5">Detalle de tu plan Growth</p>
        </div>
      </div>
      <div class="divide-y divide-white/5">
        <div class="flex justify-between items-center py-3">
          <span class="text-sm text-stone-400">Plan</span>
          <span class="px-2.5 py-1 rounded-full bg-emerald-500/15 text-emerald-300 text-xs font-bold">Growth — €79/mes</span>
        </div>
        <div class="flex justify-between items-center py-3">
          <span class="text-sm text-stone-400">Estado</span>
          <span class="text-sm font-semibold text-emerald-300">✓ Activo</span>
        </div>
        <div class="flex justify-between items-center py-3">
          <span class="text-sm text-stone-400">Próxima renovación</span>
          <span class="text-sm font-semibold text-white">1 Junio 2026</span>
        </div>
        <div class="flex justify-between items-center py-3">
          <span class="text-sm text-stone-400">Método de pago</span>
          <span class="text-sm font-semibold text-white">•••• •••• •••• 4242</span>
        </div>
      </div>
      <div class="flex gap-3 mt-5 flex-wrap">
        <a href="cancellation/step1_subscription.html" class="px-4 py-2 rounded-xl border border-white/10 bg-white/5 text-sm font-semibold text-stone-300 hover:bg-white/10 no-underline">📄 Ver facturas</a>
        <a href="#" class="px-4 py-2 rounded-xl border border-white/10 bg-white/5 text-sm font-semibold text-stone-300 hover:bg-white/10 no-underline">💳 Cambiar tarjeta</a>
      </div>
    </section>

    <!-- Zona de Peligro -->
    <section class="rounded-3xl border border-rose-500/20 bg-rose-500/5 p-6">
      <div class="flex items-center gap-3 mb-5">
        <div class="flex items-center justify-center w-10 h-10 rounded-2xl bg-rose-500/15 text-xl">⚠️</div>
        <div>
          <h2 class="text-lg font-semibold text-rose-300 m-0">Zona de Peligro</h2>
          <p class="text-xs text-rose-300/60 mt-0.5">Acciones que afectan o cancelan tu suscripción</p>
        </div>
      </div>
      <div class="flex gap-3 flex-wrap">
        <a href="cancellation/step1_subscription.html" class="px-4 py-2 rounded-xl border border-rose-500/20 bg-rose-500/10 text-sm font-semibold text-rose-300 hover:bg-rose-500/20 no-underline">⏸ Pausar suscripción</a>
        <a href="cancellation/step1_subscription.html" class="px-4 py-2 rounded-xl border border-rose-500/20 bg-rose-500/10 text-sm font-semibold text-rose-300 hover:bg-rose-500/20 no-underline">↘ Bajar a Plan Starter</a>
        <a href="cancellation/step1_subscription.html" class="px-4 py-2 rounded-xl border border-rose-500/20 bg-rose-500/10 text-sm font-semibold text-rose-300 hover:bg-rose-500/20 no-underline">✕ Cancelar suscripción</a>
      </div>
    </section>
  </div>
</body>
</html>"""


# ─── RENDER & OPEN ───────────────────────────────────────────────────────────

def main():
    # 1. Growth dashboard
    try:
        tmpl = env.get_template("growth_dashboard.html")
        ctx = build_growth_context()
        growth_html = tmpl.render(**ctx)
    except Exception as exc:
        print(f"[WARN] No se pudo renderizar el template Jinja2 de Growth ({exc}). Usando versión simplificada.")
        growth_html = None

    # Fallback: simple standalone growth preview if Jinja2 rendering fails
    if growth_html is None:
        ctx = build_growth_context()
        growth_html = f"""<!doctype html><html lang="es"><head><meta charset="utf-8">
<title>Growth Dashboard (preview) | {ctx['business_name']}</title>
<script src="https://cdn.tailwindcss.com"></script></head>
<body class="bg-stone-950 text-stone-100 p-8">
<h1 class="text-3xl font-bold mb-4">Growth Dashboard — {ctx['business_name']}</h1>
<p class="text-stone-400">(Preview con datos mock — el template Jinja2 requiere el servidor completo)</p>
<div class="grid grid-cols-3 gap-4 mt-6">
  <div class="bg-stone-900 rounded-2xl p-5 border border-white/10">
    <p class="text-xs uppercase tracking-widest text-emerald-300 mb-1">Market Share</p>
    <p class="text-4xl font-bold">{ctx['headline_kpis']['market_share_pct']}%</p>
  </div>
  <div class="bg-stone-900 rounded-2xl p-5 border border-white/10">
    <p class="text-xs uppercase tracking-widest text-stone-400 mb-1">Rivales</p>
    <p class="text-4xl font-bold">{ctx['headline_kpis']['competitor_count']}</p>
  </div>
  <div class="bg-rose-900/40 rounded-2xl p-5 border border-rose-500/20">
    <p class="text-xs uppercase tracking-widest text-stone-400 mb-1">Alertas</p>
    <p class="text-4xl font-bold text-rose-300">{ctx['headline_kpis']['unseen_alerts']}</p>
  </div>
</div>
<h2 class="text-xl font-semibold mt-8 mb-3">Alertas</h2>
<ul class="space-y-3">
{"".join(f"<li class='bg-stone-900 rounded-xl p-4 border border-white/10'><strong>{a['title']}</strong><p class='text-stone-400 text-sm mt-1'>{a['message']}</p></li>" for a in ctx['alerts'])}
</ul>
<h2 class="text-xl font-semibold mt-8 mb-3">Competidores</h2>
<table class="w-full text-sm border-collapse">
<thead><tr class="text-left text-stone-400 border-b border-white/10">
<th class="pb-2">Nombre</th><th class="pb-2">Rating</th><th class="pb-2">Reseñas</th><th class="pb-2">Posts/30d</th></tr></thead>
<tbody>
{"".join(f"<tr class='border-b border-white/5'><td class='py-2'>{c['name']}</td><td>{c['rating_avg']}★</td><td>{c['review_count_total']}</td><td>{c['posts_count_30d']}</td></tr>" for c in ctx['competitors'])}
</tbody></table>
</body></html>"""

    growth_path = OUT_DIR / "growth_dashboard_preview.html"

    # Inject Growth navbar after <body> opening tag
    body_pos = growth_html.find('<body')
    if body_pos != -1:
        tag_end = growth_html.find('>', body_pos)
        growth_html = (
            growth_html[:tag_end + 1]
            + '\n' + build_growth_navbar()
            + growth_html[tag_end + 1:]
        )

    growth_path.write_text(growth_html, encoding="utf-8")
    print(f"✓ Growth dashboard → {growth_path}")

    # 2. Starter dashboard
    starter_html = build_starter_html()
    starter_path = OUT_DIR / "starter_dashboard_preview.html"
    starter_path.write_text(starter_html, encoding="utf-8")
    print(f"✓ Starter dashboard → {starter_path}")

    # 3. Mi Cuenta pages
    mi_starter_path = OUT_DIR / "mi_cuenta_starter.html"
    mi_starter_path.write_text(build_mi_cuenta_starter_html(), encoding="utf-8")
    print(f"✓ Mi Cuenta Starter → {mi_starter_path}")

    mi_growth_path = OUT_DIR / "mi_cuenta_growth.html"
    mi_growth_path.write_text(build_mi_cuenta_growth_html(), encoding="utf-8")
    print(f"✓ Mi Cuenta Growth  → {mi_growth_path}")

    # 4. Open in browser (server should already be running on :3000)
    webbrowser.open("http://localhost:3000/growth_dashboard_preview.html")
    webbrowser.open("http://localhost:3000/starter_dashboard_preview.html")
    webbrowser.open("http://localhost:3000/mi_cuenta_starter.html")
    webbrowser.open("http://localhost:3000/mi_cuenta_growth.html")
    print("\n📌 Abriendo en el navegador:")
    print("   Growth Dashboard  → http://localhost:3000/growth_dashboard_preview.html")
    print("   Starter Dashboard → http://localhost:3000/starter_dashboard_preview.html")
    print("   Mi Cuenta Starter → http://localhost:3000/mi_cuenta_starter.html")
    print("   Mi Cuenta Growth  → http://localhost:3000/mi_cuenta_growth.html")


if __name__ == "__main__":
    main()
