"""Growth SEO suggestions and alerts routes."""

from __future__ import annotations

import json
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.growth_seo_service import GrowthSeoService
from app.models import User

router = APIRouter(tags=["growth-seo"])


class SeoSuggestionActionRequest(BaseModel):
    user_id: UUID
    reason: str | None = Field(default=None, max_length=280)


@router.get(
    "/api/growth/seo-suggestions",
    summary="List or generate Growth SEO suggestions",
)
def list_growth_seo_suggestions(
    user_id: UUID,
    force_refresh: bool = Query(default=False),
    db: Session = Depends(get_db),
):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    service = GrowthSeoService(db)
    suggestions = service.list_or_generate_suggestions(user_id=user_id, force_refresh=force_refresh)

    return {
        "items": [
            {
                "id": str(s.id),
                "suggestion_type": s.suggestion_type,
                "keyword": s.keyword,
                "current_text": s.current_text,
                "suggested_text": s.suggested_text,
                "keywords_payload": s.keywords_payload,
                "justification_payload": s.justification_payload,
                "risk_level": s.risk_level,
                "priority_score": s.priority_score,
                "status": s.status,
                "created_at": s.created_at,
            }
            for s in suggestions
        ]
    }


@router.post(
    "/api/growth/seo-suggestions/{suggestion_id}/apply",
    summary="Apply SEO suggestion through Google Business API",
)
async def apply_growth_seo_suggestion(
    suggestion_id: UUID,
    request: SeoSuggestionActionRequest,
    db: Session = Depends(get_db),
):
    user = db.get(User, request.user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    service = GrowthSeoService(db)
    try:
        result = await service.apply_suggestion(user_id=request.user_id, suggestion_id=suggestion_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"Apply failed: {exc}") from exc

    return {"ok": True, "result": result}


@router.post(
    "/api/growth/seo-suggestions/{suggestion_id}/dismiss",
    summary="Dismiss SEO suggestion",
)
def dismiss_growth_seo_suggestion(
    suggestion_id: UUID,
    request: SeoSuggestionActionRequest,
    db: Session = Depends(get_db),
):
    user = db.get(User, request.user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    service = GrowthSeoService(db)
    try:
        result = service.dismiss_suggestion(
            user_id=request.user_id,
            suggestion_id=suggestion_id,
            reason=request.reason,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    return {"ok": True, "result": result}


@router.get(
    "/api/growth/seo-alerts",
    summary="Read SEO alerts",
)
def list_growth_seo_alerts(
    user_id: UUID,
    mark_seen: bool = Query(default=False),
    db: Session = Depends(get_db),
):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    service = GrowthSeoService(db)
    alerts = service.list_alerts(user_id=user_id, mark_seen=mark_seen)
    return {
        "items": [
            {
                "id": str(a.id),
                "suggestion_id": str(a.suggestion_id) if a.suggestion_id else None,
                "title": a.title,
                "message": a.message,
                "severity": a.severity,
                "is_seen": a.is_seen,
                "created_at": a.created_at,
                "seen_at": a.seen_at,
            }
            for a in alerts
        ]
    }


@router.get(
    "/growth/seo-dashboard",
    response_class=HTMLResponse,
    summary="Growth SEO suggestions dashboard",
)
def growth_seo_dashboard(user_id: UUID):
    return HTMLResponse(_render_growth_seo_dashboard_html(user_id))


def _render_growth_seo_dashboard_html(user_id: UUID) -> str:
    return f"""
<!doctype html>
<html lang=\"es\">
  <head>
    <meta charset=\"utf-8\" />
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
    <title>Growth SEO Sugerencias | Lokigi</title>
    <style>
      :root {{
        --bg: #f3f7fb;
        --panel: #ffffff;
        --ink: #0f172a;
        --muted: #64748b;
        --line: #dbe5f0;
        --client: #0b6bcb;
        --warn: #b45309;
        --danger: #b42318;
        --ok: #0f766e;
      }}
      * {{ box-sizing: border-box; }}
      body {{ margin: 0; font-family: "Segoe UI", Tahoma, sans-serif; color: var(--ink); background: radial-gradient(circle at 0% 0%, #e6f0ff, transparent 30%), var(--bg); }}
      .wrap {{ max-width: 1200px; margin: 0 auto; padding: 20px; }}
      .hero {{ background: linear-gradient(135deg, #0b6bcb, #084b9a); color: #fff; border-radius: 16px; padding: 20px; box-shadow: 0 14px 30px rgba(8, 75, 154, 0.24); }}
      .hero h1 {{ margin: 0; font-size: 30px; }}
      .hero p {{ margin: 8px 0 0; opacity: .92; }}
      .row {{ display: grid; grid-template-columns: 1.5fr 1fr; gap: 14px; margin-top: 14px; }}
      .card {{ background: var(--panel); border: 1px solid var(--line); border-radius: 14px; padding: 14px; }}
      .card h2 {{ margin: 0 0 10px; font-size: 18px; }}
      .toolbar {{ display:flex; gap:10px; align-items:center; flex-wrap:wrap; margin-bottom: 10px; }}
      button {{ border: 0; border-radius: 10px; padding: 10px 14px; font-weight: 700; cursor: pointer; }}
      .btn-primary {{ background: var(--client); color: #fff; }}
      .btn-secondary {{ background: #e9f1ff; color: var(--client); }}
      .btn-danger {{ background: #fde8e8; color: var(--danger); }}
      .muted {{ color: var(--muted); }}
      .grid {{ display: grid; gap: 10px; }}
      .item {{ border: 1px solid var(--line); border-radius: 12px; padding: 12px; background: linear-gradient(180deg, #fff, #fbfdff); }}
      .item-head {{ display:flex; align-items:center; justify-content:space-between; gap:8px; }}
      .pill {{ font-size: 12px; font-weight: 700; border-radius: 999px; padding: 5px 10px; background: #e6efff; color: var(--client); }}
      .pill.high {{ background:#fff4e5; color: var(--warn); }}
      .pill.danger {{ background:#fee2e2; color: var(--danger); }}
      .twocol {{ display:grid; grid-template-columns:1fr 1fr; gap:10px; margin-top:8px; }}
      .box {{ border:1px dashed var(--line); border-radius:10px; padding:10px; background:#fff; }}
      .actions {{ display:flex; gap:8px; flex-wrap:wrap; margin-top:10px; }}
      .skeleton {{ height: 80px; border-radius: 12px; background: linear-gradient(90deg, #f1f5f9, #e2e8f0, #f1f5f9); background-size: 300% 100%; animation: shimmer 1.2s infinite; }}
      .empty {{ border: 1px dashed var(--line); border-radius: 12px; padding: 22px; color: var(--muted); text-align:center; }}
      @keyframes shimmer {{ 0% {{background-position: 100% 0;}} 100% {{background-position: -100% 0;}} }}
      @media (max-width: 960px) {{ .row {{ grid-template-columns: 1fr; }} .twocol {{ grid-template-columns: 1fr; }} }}
    </style>
  </head>
  <body>
    <div class=\"wrap\">
      <section class=\"hero\">
        <h1>Sugerencias SEO Growth</h1>
        <p>Oportunidades basadas en keywords que atraen tracción en competencia. Aplica cambios al perfil de Google al instante.</p>
      </section>

      <section class=\"row\">
        <article class=\"card\">
          <h2>Sugerencias activas</h2>
          <div class=\"toolbar\">
            <button class=\"btn-primary\" id=\"btnRefresh\">Refrescar sugerencias</button>
            <span class=\"muted\" id=\"summary\">Cargando...</span>
          </div>
          <div class=\"grid\" id=\"suggestions\">
            <div class=\"skeleton\"></div>
            <div class=\"skeleton\"></div>
          </div>
        </article>

        <aside class=\"card\">
          <h2>Alertas SEO</h2>
          <p class=\"muted\">Nuevas oportunidades de alta prioridad detectadas por inteligencia competitiva.</p>
          <div class=\"grid\" id=\"alerts\">
            <div class=\"skeleton\"></div>
          </div>
        </aside>
      </section>
    </div>

    <script>
      const USER_ID = {json.dumps(str(user_id))};
      const suggestionsEl = document.getElementById('suggestions');
      const alertsEl = document.getElementById('alerts');
      const summaryEl = document.getElementById('summary');
      const btnRefresh = document.getElementById('btnRefresh');

      function esc(v) {{
        return String(v ?? '').replace(/[&<>\"']/g, (ch) => ({{'&':'&amp;','<':'&lt;','>':'&gt;','\"':'&quot;',"'":'&#39;'}}[ch]));
      }}

      function riskClass(risk) {{
        if (risk === 'alto') return 'danger';
        if (risk === 'medio') return 'high';
        return '';
      }}

      async function loadSuggestions(forceRefresh = false) {{
        suggestionsEl.innerHTML = '<div class="skeleton"></div><div class="skeleton"></div>';
        const url = `/api/growth/seo-suggestions?user_id=${{encodeURIComponent(USER_ID)}}&force_refresh=${{forceRefresh ? 'true' : 'false'}}`;
        const res = await fetch(url);
        const payload = await res.json();
        if (!res.ok) {{
          suggestionsEl.innerHTML = `<div class=\"empty\">No se pudieron cargar sugerencias: ${{esc(payload.detail || 'error')}}</div>`;
          summaryEl.textContent = 'Error';
          return;
        }}

        const items = payload.items || [];
        summaryEl.textContent = `${{items.length}} sugerencias activas`;
        if (!items.length) {{
          suggestionsEl.innerHTML = '<div class="empty">No hay oportunidades SEO activas por ahora.</div>';
          return;
        }}

        suggestionsEl.innerHTML = items.map((item) => `
          <div class=\"item\" data-id=\"${{item.id}}\">
            <div class=\"item-head\">
              <strong>${{esc(item.keyword)}}</strong>
              <span class=\"pill ${{riskClass(item.risk_level)}}\">Prioridad ${{esc(item.priority_score)}}</span>
            </div>
            <p class=\"muted\">Tipo: <strong>${{esc(item.suggestion_type)}}</strong> · Riesgo: <strong>${{esc(item.risk_level)}}</strong></p>
            <div class=\"twocol\">
              <div class=\"box\"><strong>Antes</strong><p class=\"muted\">${{esc(item.current_text || 'Sin descripcion actual disponible')}}</p></div>
              <div class=\"box\"><strong>Despues</strong><p>${{esc(item.suggested_text)}}</p></div>
            </div>
            <p class=\"muted\">Gap: ${{esc(item.justification_payload?.gap_share)}} · Soporte competencia: ${{esc(item.justification_payload?.support)}}</p>
            <div class=\"actions\">
              <button class=\"btn-primary\" onclick=\"applySuggestion('${{item.id}}')\">Aplicar Cambio</button>
              <button class=\"btn-danger\" onclick=\"dismissSuggestion('${{item.id}}')\">Descartar</button>
            </div>
          </div>
        `).join('');
      }}

      async function loadAlerts() {{
        alertsEl.innerHTML = '<div class="skeleton"></div>';
        const res = await fetch(`/api/growth/seo-alerts?user_id=${{encodeURIComponent(USER_ID)}}&mark_seen=true`);
        const payload = await res.json();
        if (!res.ok) {{
          alertsEl.innerHTML = `<div class=\"empty\">No se pudieron cargar alertas.</div>`;
          return;
        }}

        const items = payload.items || [];
        if (!items.length) {{
          alertsEl.innerHTML = '<div class="empty">No hay alertas SEO pendientes.</div>';
          return;
        }}

        alertsEl.innerHTML = items.slice(0, 8).map((a) => `
          <div class=\"item\">
            <div class=\"item-head\">
              <strong>${{esc(a.title)}}</strong>
              <span class=\"pill ${{a.severity === 'high' ? 'danger' : 'high'}}\">${{esc(a.severity)}}</span>
            </div>
            <p class=\"muted\">${{esc(a.message)}}</p>
          </div>
        `).join('');
      }}

      async function applySuggestion(id) {{
        if (!window.confirm('Aplicar este cambio al perfil de Google Business ahora?')) return;
        const res = await fetch(`/api/growth/seo-suggestions/${{id}}/apply`, {{
          method: 'POST',
          headers: {{ 'Content-Type': 'application/json' }},
          body: JSON.stringify({{ user_id: USER_ID }}),
        }});
        const payload = await res.json();
        if (!res.ok) {{
          window.alert(`No se pudo aplicar: ${{payload.detail || 'error'}}`);
          return;
        }}
        window.alert('Cambio aplicado correctamente.');
        await loadSuggestions(false);
        await loadAlerts();
      }}

      async function dismissSuggestion(id) {{
        const res = await fetch(`/api/growth/seo-suggestions/${{id}}/dismiss`, {{
          method: 'POST',
          headers: {{ 'Content-Type': 'application/json' }},
          body: JSON.stringify({{ user_id: USER_ID, reason: 'manual' }}),
        }});
        const payload = await res.json();
        if (!res.ok) {{
          window.alert(`No se pudo descartar: ${{payload.detail || 'error'}}`);
          return;
        }}
        await loadSuggestions(false);
        await loadAlerts();
      }}

      btnRefresh.addEventListener('click', async () => {{
        await loadSuggestions(true);
        await loadAlerts();
      }});

      loadSuggestions(false);
      loadAlerts();
    </script>
  </body>
</html>
"""
