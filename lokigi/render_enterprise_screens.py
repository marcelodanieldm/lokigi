"""
Genera 4 nuevas pantallas Enterprise:

  bulk/bulk_celery_monitor.html          — Monitor de Celery en tiempo real (Bulk Actions)
  network/network_crisis_escalation.html — Escalamiento de Crisis con SMS/Email
  vista_red.html                         — Pantalla 1: Vista de Red unificada (Mapa + Ranking)
  consola_white_label.html               — Pantalla 2: Consola de Marca Blanca (Branding + Tenants)
"""
from __future__ import annotations
from pathlib import Path

ROOT       = Path(__file__).parent
ENT_DIR    = ROOT / "frontend" / "static" / "enterprise"
BULK_DIR   = ENT_DIR / "bulk"
NET_DIR    = ENT_DIR / "network"

# ─── Shared helpers ────────────────────────────────────────────────────────────

def _css() -> str:
    return """
    body { font-family: Arial, "Helvetica Neue", sans-serif; }
    .no-underline { text-decoration: none; }
    @keyframes fadeUp {
      from { opacity:0; transform:translateY(14px); }
      to   { opacity:1; transform:translateY(0); }
    }
    .fade-up { animation: fadeUp .35s ease both; }
    @keyframes spin { to { transform:rotate(360deg); } }
    .spin { animation: spin .8s linear infinite; }
    @keyframes pulse-dot {
      0%,100% { opacity:1; transform:scale(1); }
      50%  { opacity:.4; transform:scale(1.5); }
    }
    .pulse { animation: pulse-dot 1.4s ease-in-out infinite; }
    @keyframes crisis-ring {
      0%,100% { box-shadow:0 0 0 0 rgba(239,68,68,.5); }
      50% { box-shadow:0 0 0 14px rgba(239,68,68,0); }
    }
    .crisis-ring { animation: crisis-ring 1.6s ease-in-out infinite; }
    @keyframes worker-flash {
      0%,100% { background:rgba(139,92,246,.1); }
      50% { background:rgba(139,92,246,.25); }
    }
    .worker-active { animation: worker-flash 1s ease-in-out infinite; }
    @keyframes bar-grow {
      from { width:0; }
    }
    .bar-grow { animation: bar-grow 1.6s cubic-bezier(.4,0,.2,1) both; }
    input,select {
      background:rgba(255,255,255,.05);
      border:1px solid rgba(255,255,255,.12);
      border-radius:10px;
      color:#f1f5f9;
      padding:9px 13px;
      font-size:13px;
      outline:none;
      width:100%;
    }
    select option { background:#1c1917; }
    pre {
      background:rgba(0,0,0,.4);
      border:1px solid rgba(255,255,255,.08);
      border-radius:12px;
      padding:16px;
      font-size:12px;
      color:#a3e635;
      overflow-x:auto;
      white-space:pre;
    }
"""


def _nav(section: str, active_href: str, links: list[tuple[str, str]]) -> str:
    items = ""
    for href, label in links:
        if href == active_href:
            cls = ("px-3 py-2 rounded-lg text-sm font-semibold text-violet-200 "
                   "bg-violet-500/20 border border-violet-400/20 no-underline")
        else:
            cls = ("px-3 py-2 rounded-lg text-sm font-medium text-stone-400 "
                   "hover:text-white hover:bg-white/5 no-underline")
        items += f'<a href="{href}" class="{cls}">{label}</a>\n'
    return f"""
<nav class="sticky top-0 z-50 flex items-center gap-1 px-5 h-14
     bg-stone-950/95 backdrop-blur-sm border-b border-white/10 shadow-md flex-wrap">
  <div class="flex items-center gap-2.5 mr-4">
    <a href="../enterprise_landing.html"
       class="flex items-center justify-center w-8 h-8 rounded-lg
              bg-gradient-to-br from-violet-500 to-indigo-600
              text-white font-black text-sm no-underline">L</a>
    <a href="../enterprise_landing.html"
       class="font-bold text-white text-base no-underline">Lokigi</a>
    <span class="px-2.5 py-0.5 rounded-full bg-violet-500/20 text-violet-300
                 text-xs font-bold uppercase tracking-wider">Enterprise</span>
    <span class="text-stone-600">·</span>
    <span class="text-stone-400 text-xs font-semibold">{section}</span>
  </div>
  {items}
</nav>"""


def _nav_ent(active_href: str) -> str:
    """Nav for top-level enterprise screens (not inside a flow)."""
    links = [
        ("enterprise_hub.html",      "🏠 Hub"),
        ("vista_red.html",           "🗺 Vista de Red"),
        ("consola_white_label.html", "🏷 Consola WL"),
        ("enterprise_landing.html",  "← Planes"),
    ]
    items = ""
    for href, label in links:
        active = href == active_href
        cls = ("px-3 py-2 rounded-lg text-sm font-semibold text-violet-200 "
               "bg-violet-500/20 border border-violet-400/20 no-underline") if active else \
              ("px-3 py-2 rounded-lg text-sm font-medium text-stone-400 "
               "hover:text-white hover:bg-white/5 no-underline")
        items += f'<a href="{href}" class="{cls}">{label}</a>\n'
    return f"""
<nav class="sticky top-0 z-50 flex items-center gap-1 px-5 h-14
     bg-stone-950/95 backdrop-blur-sm border-b border-white/10 shadow-md flex-wrap">
  <div class="flex items-center gap-2.5 mr-4">
    <a href="enterprise_landing.html"
       class="flex items-center justify-center w-8 h-8 rounded-lg
              bg-gradient-to-br from-violet-500 to-indigo-600
              text-white font-black text-sm no-underline">L</a>
    <a href="enterprise_landing.html"
       class="font-bold text-white text-base no-underline">Lokigi</a>
    <span class="px-2.5 py-0.5 rounded-full bg-violet-500/20 text-violet-300
                 text-xs font-bold uppercase tracking-wider">Enterprise</span>
  </div>
  {items}
</nav>"""


def _page(title: str, nav: str, body: str, extra_css: str = "") -> str:
    return f"""<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width,initial-scale=1"/>
  <title>{title} | Lokigi Enterprise</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <style>{_css()}{extra_css}</style>
</head>
<body class="min-h-screen bg-stone-950 text-stone-100">
{nav}
{body}
</body>
</html>"""


# ══════════════════════════════════════════════════════════════════════════════
# 1. BULK CELERY MONITOR
# ══════════════════════════════════════════════════════════════════════════════

BULK_NAV_LINKS = [
    ("bulk_hub.html",            "🗂 Hub"),
    ("bulk_step1_compose.html",  "1 · Redactar"),
    ("bulk_step2_segment.html",  "2 · Segmentar"),
    ("bulk_step3_preview.html",  "3 · Preview"),
    ("bulk_step4_publish.html",  "4 · Publicar"),
    ("bulk_celery_monitor.html", "⚡ Monitor"),
    ("bulk_step5_report.html",   "5 · Resultados"),
]

# Location data: (name, worker_id, status, retry)
# status: ok | fail | running | queue
LOCATIONS = [
    ("Restaurante La Pepita - Madrid Centro",   1, "ok",      False),
    ("Restaurante La Pepita - Vallecas",        1, "ok",      False),
    ("Restaurante La Pepita - Getafe",          2, "ok",      False),
    ("Restaurante La Pepita - Alcorcón",        2, "running", False),
    ("Restaurante La Pepita - Móstoles",        3, "ok",      False),
    ("Restaurante La Pepita - Leganés",         3, "ok",      False),
    ("Restaurante La Pepita - Fuenlabrada",     4, "ok",      False),
    ("Restaurante La Pepita - Parla",           4, "running", False),
    ("Restaurante La Pepita - Torrejón",        1, "ok",      False),
    ("Restaurante La Pepita - Alcalá",          2, "ok",      False),
    ("Restaurante La Pepita - Coslada",         3, "fail",    True),
    ("Restaurante La Pepita - San Fernando",    1, "ok",      False),
    ("Restaurante La Pepita - Aranjuez",        2, "ok",      False),
    ("Restaurante La Pepita - Arganda",         4, "ok",      False),
    ("Restaurante La Pepita - Rivas",           3, "ok",      False),
    ("Restaurante La Pepita - Pozuelo",         1, "ok",      False),
    ("Restaurante La Pepita - Majadahonda",     2, "ok",      False),
    ("Restaurante La Pepita - Las Rozas",       3, "ok",      False),
    ("Restaurante La Pepita - Boadilla",        4, "fail",    True),
    ("Restaurante La Pepita - Villaviciosa",    1, "running", False),
    ("Restaurante La Pepita - Collado Villalba",2, "ok",      False),
    ("Restaurante La Pepita - El Escorial",     3, "ok",      False),
    ("Restaurante La Pepita - Colmenar Viejo",  4, "ok",      False),
    ("Restaurante La Pepita - Tres Cantos",     1, "ok",      False),
    ("Restaurante La Pepita - Alcobendas",      2, "queue",   False),
    ("Restaurante La Pepita - San Sebastián",   3, "queue",   False),
    ("Restaurante La Pepita - Paracuellos",     4, "queue",   False),
    ("Restaurante La Pepita - Daganzo",         1, "fail",    True),
    ("Restaurante La Pepita - Mejorada",        2, "queue",   False),
    ("Restaurante La Pepita - Loeches",         3, "queue",   False),
    ("Restaurante La Pepita - Velilla",         4, "queue",   False),
    ("Restaurante La Pepita - Pinto",           1, "queue",   False),
    ("Restaurante La Pepita - Valdemoro",       2, "queue",   False),
    ("Restaurante La Pepita - Ciempozuelos",    3, "queue",   False),
    ("Restaurante La Pepita - Titulcia",        4, "queue",   False),
    ("Restaurante La Pepita - San Martín",      1, "queue",   False),
    ("Restaurante La Pepita - Navalagamella",   2, "queue",   False),
    ("Restaurante La Pepita - Galapagar",       3, "queue",   False),
    ("Restaurante La Pepita - Torrelodones",    4, "queue",   False),
    ("Restaurante La Pepita - Brunete",         1, "queue",   False),
    ("Restaurante La Pepita - Quijorna",        2, "queue",   False),
    ("Restaurante La Pepita - Sevilla la Nueva",3, "queue",   False),
    ("Restaurante La Pepita - El Álamo",        4, "queue",   False),
    ("Restaurante La Pepita - Griñón",          1, "queue",   False),
    ("Restaurante La Pepita - Serranillos",     2, "queue",   False),
    ("Restaurante La Pepita - Batres",          3, "queue",   False),
    ("Restaurante La Pepita - Moraleja",        4, "queue",   False),
    ("Restaurante La Pepita - Navalcarnero",    1, "queue",   False),
    ("Restaurante La Pepita - Villamanta",      2, "queue",   False),
    ("Restaurante La Pepita - Aldea del Fresno",3, "queue",   False),
]


def _loc_badge(status: str, retry: bool) -> str:
    if status == "ok":
        return '<span class="flex-shrink-0 w-4 h-4 rounded-full bg-emerald-500 flex items-center justify-center text-white text-xs font-black">✓</span>'
    if status == "fail" and retry:
        return '<span class="flex-shrink-0 w-4 h-4 rounded-full bg-amber-500 flex items-center justify-center text-white text-xs">↺</span>'
    if status == "fail":
        return '<span class="flex-shrink-0 w-4 h-4 rounded-full bg-rose-500 flex items-center justify-center text-white text-xs font-black">✗</span>'
    if status == "running":
        return '<span class="flex-shrink-0 w-4 h-4 rounded-full bg-violet-500 pulse flex items-center justify-center text-white text-xs">▶</span>'
    # queue
    return '<span class="flex-shrink-0 w-4 h-4 rounded-full bg-stone-700 flex items-center justify-center text-stone-400 text-xs">○</span>'


def _loc_row(name: str, worker: int, status: str, retry: bool) -> str:
    badge = _loc_badge(status, retry)
    worker_color = ["violet", "indigo", "sky", "teal"][worker - 1]
    bg = {
        "ok":      "bg-emerald-500/5 border-emerald-500/15",
        "fail":    "bg-rose-500/5 border-rose-500/20",
        "running": "bg-violet-500/5 border-violet-500/20 worker-active",
        "queue":   "bg-white/2 border-white/6",
    }[status]
    label = {
        "ok": "text-emerald-400", "fail": "text-rose-400",
        "running": "text-violet-300", "queue": "text-stone-600",
    }[status]
    status_text = {
        "ok": "Publicado", "fail": "Error (reintentando)" if retry else "Error",
        "running": "Publicando...", "queue": "En cola",
    }[status]
    return f"""
    <div class="flex items-center gap-2 p-2 rounded-lg border {bg}">
      {badge}
      <span class="text-xs text-stone-300 flex-1 truncate">{name}</span>
      <span class="text-xs px-2 py-0.5 rounded-full bg-{worker_color}-500/15 text-{worker_color}-400 flex-shrink-0 font-mono">W{worker}</span>
      <span class="text-xs {label} flex-shrink-0 font-semibold">{status_text}</span>
    </div>"""


def bulk_celery_monitor() -> str:
    ok_count      = sum(1 for _, _, s, _ in LOCATIONS if s == "ok")
    fail_count    = sum(1 for _, _, s, r in LOCATIONS if s == "fail" and not r)
    retry_count   = sum(1 for _, _, s, r in LOCATIONS if s == "fail" and r)
    running_count = sum(1 for _, _, s, _ in LOCATIONS if s == "running")
    total         = len(LOCATIONS)
    done          = ok_count + fail_count + retry_count + running_count
    pct           = round(done / total * 100)

    rows = "\n".join(_loc_row(*loc) for loc in LOCATIONS)

    body = f"""
<div class="mx-auto max-w-6xl px-4 py-10 sm:px-6 pb-20 fade-up">

  <div class="flex items-start justify-between gap-4 mb-6 flex-wrap">
    <div>
      <p class="text-xs uppercase tracking-[.2em] text-violet-300/70 mb-1">Publicación Masiva · Celery Broadcast</p>
      <h1 class="text-3xl font-bold text-white">Monitor de Publicación</h1>
      <p class="mt-1 text-stone-400 text-sm max-w-2xl">
        Celery distribuye la tarea en paralelo entre 4 workers.
        Cada worker procesa varias ubicaciones a la vez.
        Los fallos se reintentan automáticamente hasta 3 veces.
      </p>
    </div>
    <div class="flex gap-2">
      <button class="px-4 py-2 rounded-xl border border-white/10 bg-white/5 text-stone-300 text-xs font-semibold hover:bg-white/10">
        ⏸ Pausar
      </button>
      <button class="px-4 py-2 rounded-xl border border-rose-500/30 bg-rose-500/10 text-rose-300 text-xs font-semibold hover:bg-rose-500/15">
        ✗ Cancelar
      </button>
    </div>
  </div>

  <!-- Main progress bar -->
  <div class="rounded-3xl border border-violet-500/20 bg-violet-500/5 p-6 mb-6">
    <div class="flex items-end justify-between mb-3 flex-wrap gap-2">
      <div>
        <p class="text-4xl font-black text-white">{done}<span class="text-stone-500 text-2xl">/{total}</span></p>
        <p class="text-sm text-stone-400 mt-0.5">locales procesados</p>
      </div>
      <div class="text-right">
        <p class="text-3xl font-black text-violet-300">{pct}%</p>
        <p class="text-xs text-stone-500">completado</p>
      </div>
    </div>
    <div class="w-full h-4 rounded-full bg-white/8 overflow-hidden mb-4">
      <div class="h-full rounded-full bar-grow bg-gradient-to-r from-violet-500 to-indigo-500" style="width:{pct}%"></div>
    </div>
    <div class="grid grid-cols-2 sm:grid-cols-4 gap-3">
      <div class="text-center p-3 rounded-2xl border border-emerald-500/20 bg-emerald-500/5">
        <p class="text-xl font-black text-emerald-400">{ok_count}</p>
        <p class="text-xs text-stone-500">Publicados ✓</p>
      </div>
      <div class="text-center p-3 rounded-2xl border border-violet-500/20 bg-violet-500/5">
        <p class="text-xl font-black text-violet-300">{running_count}</p>
        <p class="text-xs text-stone-500">En ejecución ▶</p>
      </div>
      <div class="text-center p-3 rounded-2xl border border-amber-500/20 bg-amber-500/5">
        <p class="text-xl font-black text-amber-400">{retry_count}</p>
        <p class="text-xs text-stone-500">Reintentando ↺</p>
      </div>
      <div class="text-center p-3 rounded-2xl border border-rose-500/20 bg-rose-500/5">
        <p class="text-xl font-black text-rose-400">{fail_count}</p>
        <p class="text-xs text-stone-500">Fallidos ✗</p>
      </div>
    </div>
  </div>

  <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">

    <!-- Worker pool visualization -->
    <div class="space-y-4">
      <div class="rounded-3xl border border-white/10 bg-white/5 p-5">
        <h2 class="text-xs font-bold text-stone-300 uppercase tracking-wider mb-4">Pool de Workers</h2>
        <div class="space-y-3">

          <!-- Worker 1 -->
          <div class="rounded-2xl border border-violet-500/20 bg-violet-500/8 p-4 worker-active">
            <div class="flex items-center justify-between mb-2">
              <div class="flex items-center gap-2">
                <div class="w-6 h-6 rounded-lg bg-violet-500 flex items-center justify-center text-white text-xs font-black">1</div>
                <span class="text-xs font-bold text-violet-200">celery@worker-1</span>
              </div>
              <span class="text-xs text-emerald-400 font-semibold">activo</span>
            </div>
            <div class="text-xs text-stone-400 space-y-1">
              <div class="flex justify-between"><span>Procesadas:</span><span class="text-white font-semibold">12</span></div>
              <div class="flex justify-between"><span>En proceso:</span><span class="text-violet-300">2</span></div>
              <div class="flex justify-between"><span>CPU:</span><span class="text-emerald-400">34%</span></div>
              <div class="flex justify-between"><span>Tiempo/local:</span><span class="text-stone-300">~1.2s</span></div>
            </div>
          </div>

          <!-- Worker 2 -->
          <div class="rounded-2xl border border-indigo-500/20 bg-indigo-500/8 p-4 worker-active">
            <div class="flex items-center justify-between mb-2">
              <div class="flex items-center gap-2">
                <div class="w-6 h-6 rounded-lg bg-indigo-500 flex items-center justify-center text-white text-xs font-black">2</div>
                <span class="text-xs font-bold text-indigo-200">celery@worker-2</span>
              </div>
              <span class="text-xs text-emerald-400 font-semibold">activo</span>
            </div>
            <div class="text-xs text-stone-400 space-y-1">
              <div class="flex justify-between"><span>Procesadas:</span><span class="text-white font-semibold">11</span></div>
              <div class="flex justify-between"><span>En proceso:</span><span class="text-indigo-300">1</span></div>
              <div class="flex justify-between"><span>CPU:</span><span class="text-emerald-400">28%</span></div>
              <div class="flex justify-between"><span>Tiempo/local:</span><span class="text-stone-300">~1.4s</span></div>
            </div>
          </div>

          <!-- Worker 3 -->
          <div class="rounded-2xl border border-sky-500/20 bg-sky-500/8 p-4 worker-active">
            <div class="flex items-center justify-between mb-2">
              <div class="flex items-center gap-2">
                <div class="w-6 h-6 rounded-lg bg-sky-500 flex items-center justify-center text-white text-xs font-black">3</div>
                <span class="text-xs font-bold text-sky-200">celery@worker-3</span>
              </div>
              <span class="text-xs text-emerald-400 font-semibold">activo</span>
            </div>
            <div class="text-xs text-stone-400 space-y-1">
              <div class="flex justify-between"><span>Procesadas:</span><span class="text-white font-semibold">10</span></div>
              <div class="flex justify-between"><span>En proceso:</span><span class="text-sky-300">2</span></div>
              <div class="flex justify-between"><span>CPU:</span><span class="text-emerald-400">41%</span></div>
              <div class="flex justify-between"><span>Tiempo/local:</span><span class="text-stone-300">~0.9s</span></div>
            </div>
          </div>

          <!-- Worker 4 -->
          <div class="rounded-2xl border border-teal-500/20 bg-teal-500/8 p-4 worker-active">
            <div class="flex items-center justify-between mb-2">
              <div class="flex items-center gap-2">
                <div class="w-6 h-6 rounded-lg bg-teal-500 flex items-center justify-center text-white text-xs font-black">4</div>
                <span class="text-xs font-bold text-teal-200">celery@worker-4</span>
              </div>
              <span class="text-xs text-emerald-400 font-semibold">activo</span>
            </div>
            <div class="text-xs text-stone-400 space-y-1">
              <div class="flex justify-between"><span>Procesadas:</span><span class="text-white font-semibold">12</span></div>
              <div class="flex justify-between"><span>En proceso:</span><span class="text-teal-300">1</span></div>
              <div class="flex justify-between"><span>CPU:</span><span class="text-emerald-400">22%</span></div>
              <div class="flex justify-between"><span>Tiempo/local:</span><span class="text-stone-300">~1.1s</span></div>
            </div>
          </div>
        </div>
      </div>

      <!-- Task dispatch code -->
      <div class="rounded-3xl border border-white/10 bg-white/5 p-5">
        <h2 class="text-xs font-bold text-stone-300 uppercase tracking-wider mb-3">Dispatch Celery</h2>
        <pre># tasks/bulk_publish.py
from celery import group

task_group = group(
    publish_location.s(
        location_id=loc.id,
        content=content,
        post_type=post_type,
    )
    for loc in selected_locations
)

# Fire & forget — parallel burst
result = task_group.apply_async()
broadcast_id = result.id</pre>
      </div>
    </div>

    <!-- Per-location status grid -->
    <div class="lg:col-span-2">
      <div class="rounded-3xl border border-white/10 bg-white/5 p-5">
        <div class="flex items-center justify-between mb-4 flex-wrap gap-2">
          <h2 class="text-xs font-bold text-stone-300 uppercase tracking-wider">Estado por Ubicación</h2>
          <div class="flex gap-2">
            <span class="text-xs text-stone-500 flex items-center gap-1">
              <span class="w-2 h-2 rounded-full bg-emerald-500 inline-block"></span>OK
            </span>
            <span class="text-xs text-stone-500 flex items-center gap-1">
              <span class="w-2 h-2 rounded-full bg-violet-500 inline-block"></span>Running
            </span>
            <span class="text-xs text-stone-500 flex items-center gap-1">
              <span class="w-2 h-2 rounded-full bg-amber-500 inline-block"></span>Retry
            </span>
            <span class="text-xs text-stone-500 flex items-center gap-1">
              <span class="w-2 h-2 rounded-full bg-rose-500 inline-block"></span>Error
            </span>
          </div>
        </div>

        <div class="space-y-1.5 max-h-[560px] overflow-y-auto pr-1 custom-scroll">
          {rows}
        </div>

        <div class="mt-4 pt-4 border-t border-white/8 flex items-center justify-between">
          <p class="text-xs text-stone-500">
            ETA: ~<strong class="text-stone-300">38 segundos</strong> restantes
            · {total} locales · 4 workers en paralelo
          </p>
          <a href="bulk_step5_report.html"
             class="px-4 py-2 rounded-xl bg-gradient-to-r from-violet-600 to-indigo-600
                    text-white font-bold text-xs no-underline hover:from-violet-500 hover:to-indigo-500">
            Ver resultados →
          </a>
        </div>
      </div>
    </div>

  </div>
</div>"""

    nav = _nav("Publicación Masiva", "bulk_celery_monitor.html", BULK_NAV_LINKS)
    return _page("Monitor Celery · Bulk", nav, body,
                 extra_css=".custom-scroll::-webkit-scrollbar{width:4px}.custom-scroll::-webkit-scrollbar-track{background:transparent}.custom-scroll::-webkit-scrollbar-thumb{background:rgba(255,255,255,.1);border-radius:4px}")


# ══════════════════════════════════════════════════════════════════════════════
# 2. NETWORK CRISIS ESCALATION
# ══════════════════════════════════════════════════════════════════════════════

NET_NAV_LINKS = [
    ("network_hub.html",                "🌐 Hub"),
    ("network_step1_scan.html",         "1 · Escaneo"),
    ("network_step2_crisis.html",       "2 · Crisis"),
    ("network_crisis_escalation.html",  "🚨 Escalamiento"),
    ("network_step3_benchmark.html",    "3 · Benchmark"),
    ("network_step5_report.html",       "5 · Informe"),
]


KEYWORDS = [
    ("intoxicación", "rojo", "🔴"),
    ("denuncia", "rojo", "🔴"),
    ("fraude", "rojo", "🔴"),
    ("robo", "rojo", "🔴"),
    ("agresión", "rojo", "🔴"),
    ("accidente", "ámbar", "🟡"),
    ("cerrado", "ámbar", "🟡"),
    ("guardia civil", "rojo", "🔴"),
    ("sanidad", "rojo", "🔴"),
    ("veneno", "rojo", "🔴"),
    ("hospital", "ámbar", "🟡"),
    ("rata", "ámbar", "🟡"),
    ("cucaracha", "ámbar", "🟡"),
    ("multa", "ámbar", "🟡"),
]

CRISIS_EVENTS = [
    ("Restaurante La Pepita - Coslada",   "intoxicación", "hace 12 min",  True,  "Ops. Manager notificado via SMS"),
    ("Restaurante La Pepita - Vallecas",  "denuncia",     "hace 47 min",  True,  "Ops. Manager notificado via Email"),
    ("Restaurante La Pepita - Parla",     "cerrado",      "hace 2 horas", False, "Encargado local notificado"),
    ("Restaurante La Pepita - Getafe",    "sanidad",      "hace 3 horas", True,  "Ops. Manager + CEO alertados"),
]


def network_crisis_escalation() -> str:
    kw_tags = "\n".join(
        f'<span class="px-2.5 py-1 rounded-full text-xs font-bold '
        f'{"bg-rose-500/15 text-rose-300 border border-rose-500/25" if level == "rojo" else "bg-amber-500/15 text-amber-300 border border-amber-500/25"}">'
        f'{icon} {kw}</span>'
        for kw, level, icon in KEYWORDS
    )

    events_html = ""
    for loc, kw, time, escalated, action in CRISIS_EVENTS:
        level_cls = "border-rose-500/20 bg-rose-500/5" if escalated else "border-amber-500/20 bg-amber-500/5"
        kw_cls    = "text-rose-300" if escalated else "text-amber-300"
        events_html += f"""
        <div class="rounded-2xl border {level_cls} p-5">
          <div class="flex items-start gap-3 mb-3">
            <div class="w-10 h-10 rounded-2xl {'bg-rose-500 crisis-ring' if escalated else 'bg-amber-500'} flex items-center justify-center text-white text-lg flex-shrink-0">
              {'🚨' if escalated else '⚠️'}
            </div>
            <div class="flex-1 min-w-0">
              <div class="flex items-start justify-between gap-2 flex-wrap">
                <p class="text-sm font-bold text-white">{loc}</p>
                <span class="text-xs text-stone-500 flex-shrink-0">{time}</span>
              </div>
              <p class="text-xs text-stone-400 mt-0.5">
                Keyword detectada: <strong class="{kw_cls}">"{kw}"</strong>
              </p>
            </div>
          </div>
          <div class="flex items-center gap-3 flex-wrap">
            <span class="px-2.5 py-1 rounded-full text-xs font-bold {'bg-rose-500/20 text-rose-200 border border-rose-500/30' if escalated else 'bg-amber-500/20 text-amber-200 border border-amber-500/30'}">
              {'🔴 Nivel Rojo — Escalado' if escalated else '🟡 Nivel Ámbar'}
            </span>
            <span class="text-xs text-stone-400">✓ {action}</span>
            <a href="#" class="ml-auto px-3 py-1.5 rounded-xl border border-white/10 bg-white/5 text-stone-300 text-xs font-semibold no-underline hover:bg-white/10">
              Ver reseña →
            </a>
          </div>
        </div>"""

    body = f"""
<div class="mx-auto max-w-4xl px-4 py-10 sm:px-6 pb-20 fade-up">

  <div class="flex items-start justify-between gap-4 mb-6 flex-wrap">
    <div>
      <p class="text-xs uppercase tracking-[.2em] text-rose-300/70 mb-1">Auditoría de Red · Escalamiento</p>
      <h1 class="text-3xl font-bold text-white">Escalamiento de Crisis</h1>
      <p class="mt-1 text-stone-400 text-sm max-w-2xl">
        Cuando el motor de IA detecta palabras clave críticas en cualquier reseña de la red,
        el sistema escala la alerta <strong class="text-white">por encima del encargado local</strong>
        — directo al Gerente de Operaciones o CEO vía SMS y email.
      </p>
    </div>
    <div class="flex items-center gap-2 px-4 py-2 rounded-2xl border border-rose-500/20 bg-rose-500/5">
      <div class="w-2.5 h-2.5 rounded-full bg-rose-500 pulse flex-shrink-0"></div>
      <span class="text-xs text-rose-300 font-semibold">Monitorización activa · 50 locales</span>
    </div>
  </div>

  <!-- Active crises -->
  <div class="mb-8">
    <div class="flex items-center justify-between mb-4 flex-wrap gap-2">
      <h2 class="text-sm font-bold text-white uppercase tracking-wider">Crisis activas</h2>
      <span class="px-3 py-1 rounded-full bg-rose-500/20 text-rose-200 text-xs font-bold">
        {len(CRISIS_EVENTS)} alertas en las últimas 6h
      </span>
    </div>
    <div class="space-y-4">
      {events_html}
    </div>
  </div>

  <!-- Escalation tree -->
  <div class="rounded-3xl border border-white/10 bg-white/5 p-6 mb-6">
    <h2 class="text-sm font-bold text-stone-300 uppercase tracking-wider mb-5">Árbol de Escalamiento</h2>
    <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">

      <div class="text-center">
        <div class="w-12 h-12 rounded-2xl bg-amber-500/20 border border-amber-500/30 flex items-center justify-center text-2xl mx-auto mb-3">⚠️</div>
        <p class="text-sm font-bold text-amber-300 mb-1">Nivel Ámbar</p>
        <p class="text-xs text-stone-400 mb-2">Sentimiento negativo inusual o keyword de nivel 2</p>
        <div class="space-y-1 text-xs text-stone-400">
          <div class="flex items-center gap-1.5 justify-center"><span>📧</span> Email al encargado local</div>
          <div class="flex items-center gap-1.5 justify-center"><span>🔔</span> Push notification</div>
        </div>
      </div>

      <div class="text-center">
        <div class="w-12 h-12 rounded-2xl bg-rose-500/20 border border-rose-500/30 flex items-center justify-center text-2xl mx-auto mb-3 crisis-ring">🚨</div>
        <p class="text-sm font-bold text-rose-300 mb-1">Nivel Rojo</p>
        <p class="text-xs text-stone-400 mb-2">Keyword crítica: intoxicación, denuncia, fraude, sanidad</p>
        <div class="space-y-1 text-xs text-stone-400">
          <div class="flex items-center gap-1.5 justify-center"><span>📱</span> SMS al Gerente de Ops.</div>
          <div class="flex items-center gap-1.5 justify-center"><span>📧</span> Email urgente + CC CEO</div>
          <div class="flex items-center gap-1.5 justify-center"><span>🔔</span> Notificación en panel</div>
        </div>
      </div>

      <div class="text-center">
        <div class="w-12 h-12 rounded-2xl bg-purple-500/20 border border-purple-500/30 flex items-center justify-center text-2xl mx-auto mb-3">🔇</div>
        <p class="text-sm font-bold text-purple-300 mb-1">Silenciado</p>
        <p class="text-xs text-stone-400 mb-2">El operador ha tomado control — alertas suspendidas 24h</p>
        <div class="space-y-1 text-xs text-stone-400">
          <div class="flex items-center gap-1.5 justify-center"><span>✓</span> Log de acciones guardado</div>
          <div class="flex items-center gap-1.5 justify-center"><span>📝</span> Informe post-crisis auto</div>
        </div>
      </div>
    </div>
  </div>

  <!-- Keyword config -->
  <div class="grid grid-cols-1 sm:grid-cols-2 gap-6 mb-6">
    <div class="rounded-3xl border border-white/10 bg-white/5 p-5">
      <h2 class="text-sm font-bold text-stone-300 uppercase tracking-wider mb-4">Keywords monitorizadas</h2>
      <div class="flex flex-wrap gap-2 mb-4">
        {kw_tags}
      </div>
      <button class="w-full px-4 py-2.5 rounded-xl border border-dashed border-white/15 text-stone-500 text-xs hover:border-white/25 hover:text-stone-400">
        + Agregar keyword
      </button>
    </div>

    <div class="rounded-3xl border border-white/10 bg-white/5 p-5">
      <h2 class="text-sm font-bold text-stone-300 uppercase tracking-wider mb-4">Destinatarios de alerta</h2>
      <div class="space-y-3">
        <div class="flex items-center gap-3 p-3 rounded-xl border border-white/8 bg-black/15">
          <div class="w-8 h-8 rounded-full bg-rose-500/20 flex items-center justify-center text-lg flex-shrink-0">👤</div>
          <div class="flex-1 min-w-0">
            <p class="text-xs font-bold text-white">Carlos Vega</p>
            <p class="text-xs text-stone-500">Gerente de Operaciones · 🔴 Rojo</p>
          </div>
          <div class="flex gap-1.5 flex-shrink-0">
            <span class="px-2 py-0.5 rounded-full bg-emerald-500/15 text-emerald-400 text-xs">SMS</span>
            <span class="px-2 py-0.5 rounded-full bg-blue-500/15 text-blue-400 text-xs">Email</span>
          </div>
        </div>
        <div class="flex items-center gap-3 p-3 rounded-xl border border-white/8 bg-black/15">
          <div class="w-8 h-8 rounded-full bg-amber-500/20 flex items-center justify-center text-lg flex-shrink-0">👤</div>
          <div class="flex-1 min-w-0">
            <p class="text-xs font-bold text-white">Ana Martínez</p>
            <p class="text-xs text-stone-500">Responsable de Calidad · 🟡 Ámbar + 🔴</p>
          </div>
          <div class="flex gap-1.5 flex-shrink-0">
            <span class="px-2 py-0.5 rounded-full bg-blue-500/15 text-blue-400 text-xs">Email</span>
          </div>
        </div>
        <button class="w-full px-4 py-2.5 rounded-xl border border-dashed border-white/15 text-stone-500 text-xs hover:border-white/25 hover:text-stone-400">
          + Agregar destinatario
        </button>
      </div>
    </div>
  </div>

  <!-- Backend snippet -->
  <div class="rounded-3xl border border-white/10 bg-white/5 p-5">
    <h2 class="text-sm font-bold text-stone-300 uppercase tracking-wider mb-3">Motor de escalamiento</h2>
    <pre># app/churn_alert_engine.py — crisis escalation
CRISIS_KEYWORDS_RED  = {{"intoxicación","denuncia","fraude","sanidad","guardia civil"}}
CRISIS_KEYWORDS_AMBER= {{"cerrado","accidente","hospital","multa","cucaracha"}}

def check_crisis(review_text: str, location: Location, db: Session):
    text_lower = review_text.lower()
    keywords_found = CRISIS_KEYWORDS_RED & set(text_lower.split())
    if keywords_found:
        # Escalate to Ops Manager — bypass local manager
        dispatch_sms(ops_manager_phone, location, keywords_found)
        dispatch_email(ops_manager_email, location, keywords_found, cc=[ceo_email])
        create_crisis_event(db, location.id, "red", list(keywords_found))
        return "escalated_red"
    # ... amber check ...</pre>
  </div>

</div>"""

    nav = _nav("Auditoría de Red", "network_crisis_escalation.html", NET_NAV_LINKS)
    return _page("Escalamiento de Crisis · Network Health", nav, body)


# ══════════════════════════════════════════════════════════════════════════════
# 3. VISTA DE RED (Dashboard Screen 1)
# ══════════════════════════════════════════════════════════════════════════════

# (name, bai, rating, replies, zone, trend)
LOCS_MAP = [
    ("Madrid Centro",     91, 4.8, 98, "norte", "up"),
    ("Vallecas",          85, 4.6, 95, "sur",   "up"),
    ("Getafe",            82, 4.5, 92, "sur",   "flat"),
    ("Alcorcón",          79, 4.4, 89, "sur",   "up"),
    ("Móstoles",          76, 4.3, 87, "sur",   "flat"),
    ("Leganés",           74, 4.3, 85, "sur",   "down"),
    ("Fuenlabrada",       71, 4.2, 83, "sur",   "flat"),
    ("Parla",             68, 4.1, 80, "sur",   "up"),
    ("Torrejón",          88, 4.7, 94, "este",  "up"),
    ("Alcalá",            83, 4.5, 91, "este",  "up"),
    ("Coslada",           44, 3.7, 62, "este",  "down"),   # outlier
    ("San Fernando",      78, 4.4, 86, "este",  "flat"),
    ("Aranjuez",          81, 4.5, 90, "sur",   "up"),
    ("Arganda",           75, 4.3, 84, "este",  "flat"),
    ("Rivas",             80, 4.4, 88, "este",  "up"),
    ("Pozuelo",           90, 4.7, 97, "norte", "up"),
    ("Majadahonda",       87, 4.6, 94, "norte", "flat"),
    ("Las Rozas",         86, 4.6, 93, "norte", "up"),
    ("Boadilla",          39, 3.5, 58, "norte", "down"),   # outlier
    ("Villaviciosa",      72, 4.2, 82, "norte", "up"),
    ("Collado Villalba",  77, 4.4, 86, "norte", "flat"),
    ("El Escorial",       83, 4.5, 91, "norte", "up"),
    ("Colmenar Viejo",    79, 4.4, 88, "norte", "flat"),
    ("Tres Cantos",       89, 4.7, 96, "norte", "up"),
    ("Alcobendas",        84, 4.6, 92, "norte", "up"),
    ("San Sebastián",     88, 4.7, 95, "norte", "up"),
    ("Paracuellos",       73, 4.2, 83, "este",  "flat"),
    ("Daganzo",           32, 3.2, 45, "este",  "down"),   # outlier red
    ("Mejorada",          70, 4.2, 81, "este",  "up"),
    ("Loeches",           75, 4.3, 84, "este",  "flat"),
]


def _map_dot(name: str, bai: int, rating: float, zone: str, trend: str, rank: int) -> str:
    if bai >= 65:
        dot = "bg-emerald-500"
        ring = "ring-2 ring-emerald-400/30"
    elif bai >= 45:
        dot = "bg-amber-500"
        ring = "ring-2 ring-amber-400/30"
    else:
        dot = "bg-rose-500"
        ring = "ring-2 ring-rose-400/40 crisis-ring"
    trend_icon = {"up": "▲", "flat": "—", "down": "▼"}[trend]
    trend_cls  = {"up": "text-emerald-400", "flat": "text-stone-400", "down": "text-rose-400"}[trend]
    return f"""
    <div class="relative group flex flex-col items-center gap-1 cursor-pointer" title="{name} · BAI {bai}">
      <div class="w-6 h-6 rounded-full {dot} {ring} flex items-center justify-center
                  text-white text-xs font-black hover:scale-125 transition-transform">
        {rank if rank <= 3 else ""}
      </div>
      <span class="text-xs text-stone-500 hidden sm:block text-center leading-tight max-w-[64px] truncate">{name.split()[-1]}</span>
      <span class="text-xs {trend_cls} hidden sm:block">{trend_icon}</span>
      <!-- Tooltip -->
      <div class="absolute bottom-full mb-2 left-1/2 -translate-x-1/2 z-20 hidden group-hover:block
                  w-40 rounded-xl border border-white/10 bg-stone-900 shadow-xl p-2.5 text-xs">
        <p class="font-bold text-white mb-1">{name}</p>
        <div class="flex justify-between text-stone-400"><span>BAI</span><span class="font-bold {'text-emerald-400' if bai>=65 else 'text-amber-400' if bai>=45 else 'text-rose-400'}">{bai}</span></div>
        <div class="flex justify-between text-stone-400"><span>Rating</span><span class="text-white">{rating}★</span></div>
        <div class="flex justify-between text-stone-400"><span>Zona</span><span class="text-stone-300">{zone.title()}</span></div>
      </div>
    </div>"""


def vista_red() -> str:
    sorted_locs = sorted(LOCS_MAP, key=lambda x: -x[1])
    dots = "\n".join(
        _map_dot(name, bai, rating, zone, trend, rank + 1)
        for rank, (name, bai, rating, replies, zone, trend) in enumerate(sorted_locs[:30])
    )

    ranking_rows = ""
    for i, (name, bai, rating, replies, zone, trend) in enumerate(sorted_locs[:10]):
        trend_icon = {"up": "▲", "flat": "—", "down": "▼"}[trend]
        trend_cls  = {"up": "text-emerald-400", "flat": "text-stone-500", "down": "text-rose-400"}[trend]
        bai_color = "bg-emerald-500" if bai >= 65 else "bg-amber-500" if bai >= 45 else "bg-rose-500"
        medal = ["🥇", "🥈", "🥉", ""][min(i, 3)]
        ranking_rows += f"""
        <div class="flex items-center gap-3 p-3 rounded-xl {'border border-violet-500/20 bg-violet-500/5' if i < 3 else 'border border-white/6 bg-black/10'}">
          <span class="text-lg flex-shrink-0 w-7 text-center">{medal or f'<span class="text-sm text-stone-500 font-mono">{i+1}</span>'}</span>
          <span class="flex-1 text-sm text-stone-300 truncate">{name}</span>
          <div class="w-16 h-2 rounded-full bg-white/10 overflow-hidden">
            <div class="h-full rounded-full {bai_color}" style="width:{bai}%"></div>
          </div>
          <span class="text-xs font-bold {'text-emerald-400' if bai>=65 else 'text-amber-400'} w-8 text-right">{bai}</span>
          <span class="text-xs text-stone-400 w-10 text-right">{rating}★</span>
          <span class="text-xs {trend_cls} w-4 text-center">{trend_icon}</span>
        </div>"""

    outliers = [(n, bai, r) for n, bai, r, *_ in LOCS_MAP if bai < 45]
    outlier_html = ""
    for name, bai, rating in outliers:
        outlier_html += f"""
        <div class="flex items-center gap-3 p-3 rounded-xl border border-rose-500/20 bg-rose-500/5">
          <div class="w-8 h-8 rounded-xl bg-rose-500 crisis-ring flex items-center justify-center text-white text-xs font-black flex-shrink-0">!</div>
          <div class="flex-1 min-w-0">
            <p class="text-xs font-bold text-white truncate">{name}</p>
            <p class="text-xs text-stone-500">BAI {bai} · Rating {rating}★</p>
          </div>
          <a href="network/network_crisis_escalation.html"
             class="px-3 py-1.5 rounded-xl bg-rose-500/20 text-rose-300 text-xs font-semibold no-underline hover:bg-rose-500/30 flex-shrink-0">
            Revisar →
          </a>
        </div>"""

    body = f"""
<div class="mx-auto max-w-7xl px-4 py-8 sm:px-6 pb-20 fade-up">

  <div class="flex items-start justify-between gap-4 mb-6 flex-wrap">
    <div>
      <p class="text-xs uppercase tracking-[.2em] text-violet-300/70 mb-1">Dashboard Enterprise · Pantalla 1</p>
      <h1 class="text-3xl font-bold text-white">Vista de Red</h1>
      <p class="text-stone-400 text-sm mt-1">Estado de reputación de toda la cadena en tiempo real.</p>
    </div>
    <div class="flex gap-2 flex-wrap">
      <select class="!w-auto text-xs">
        <option>Todas las zonas</option>
        <option>Zona Norte</option>
        <option>Zona Sur</option>
        <option>Zona Este</option>
      </select>
      <select class="!w-auto text-xs">
        <option>Últimos 30 días</option>
        <option>Últimos 7 días</option>
        <option>Este mes</option>
      </select>
    </div>
  </div>

  <!-- KPI strip -->
  <div class="grid grid-cols-2 sm:grid-cols-5 gap-3 mb-6">
    <div class="rounded-2xl border border-white/10 bg-white/5 p-4 text-center">
      <p class="text-2xl font-black text-white">50</p>
      <p class="text-xs text-stone-500 mt-0.5">Locales</p>
    </div>
    <div class="rounded-2xl border border-emerald-500/20 bg-emerald-500/5 p-4 text-center">
      <p class="text-2xl font-black text-emerald-400">87</p>
      <p class="text-xs text-stone-500 mt-0.5">BAI Red Media</p>
    </div>
    <div class="rounded-2xl border border-yellow-500/20 bg-yellow-500/5 p-4 text-center">
      <p class="text-2xl font-black text-yellow-400">4.5★</p>
      <p class="text-xs text-stone-500 mt-0.5">Rating medio</p>
    </div>
    <div class="rounded-2xl border border-rose-500/20 bg-rose-500/5 p-4 text-center">
      <p class="text-2xl font-black text-rose-400">3</p>
      <p class="text-xs text-stone-500 mt-0.5">Outliers críticos</p>
    </div>
    <div class="rounded-2xl border border-amber-500/20 bg-amber-500/5 p-4 text-center">
      <p class="text-2xl font-black text-amber-400">4</p>
      <p class="text-xs text-stone-500 mt-0.5">Crisis activas</p>
    </div>
  </div>

  <div class="grid grid-cols-1 xl:grid-cols-3 gap-6">

    <!-- Heatmap grid -->
    <div class="xl:col-span-2 space-y-4">
      <div class="rounded-3xl border border-white/10 bg-white/5 p-6">
        <div class="flex items-center justify-between mb-5 flex-wrap gap-2">
          <h2 class="text-sm font-bold text-stone-300 uppercase tracking-wider">Mapa de Calor de la Red</h2>
          <div class="flex gap-3 text-xs">
            <span class="flex items-center gap-1.5"><span class="w-3 h-3 rounded-full bg-emerald-500 inline-block"></span>BAI ≥ 65</span>
            <span class="flex items-center gap-1.5"><span class="w-3 h-3 rounded-full bg-amber-500 inline-block"></span>45–64</span>
            <span class="flex items-center gap-1.5"><span class="w-3 h-3 rounded-full bg-rose-500 inline-block"></span>&lt; 45</span>
          </div>
        </div>

        <!-- Map zones -->
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-4">
          <div>
            <p class="text-xs text-stone-500 uppercase tracking-wider mb-3 font-semibold">Zona Norte</p>
            <div class="flex flex-wrap gap-3">
              {chr(10).join(
                  _map_dot(name, bai, rating, zone, trend, i+1)
                  for i, (name, bai, rating, replies, zone, trend) in enumerate(sorted_locs[:30])
                  if zone == "norte"
              )}
            </div>
          </div>
          <div>
            <p class="text-xs text-stone-500 uppercase tracking-wider mb-3 font-semibold">Zona Sur</p>
            <div class="flex flex-wrap gap-3">
              {chr(10).join(
                  _map_dot(name, bai, rating, zone, trend, i+1)
                  for i, (name, bai, rating, replies, zone, trend) in enumerate(sorted_locs[:30])
                  if zone == "sur"
              )}
            </div>
          </div>
        </div>
        <div>
          <p class="text-xs text-stone-500 uppercase tracking-wider mb-3 font-semibold">Zona Este</p>
          <div class="flex flex-wrap gap-3">
            {chr(10).join(
                _map_dot(name, bai, rating, zone, trend, i+1)
                for i, (name, bai, rating, replies, zone, trend) in enumerate(sorted_locs[:30])
                if zone == "este"
            )}
          </div>
        </div>
      </div>

      <!-- Outliers alert -->
      <div class="rounded-3xl border border-rose-500/15 bg-rose-500/5 p-5">
        <div class="flex items-center justify-between mb-4 flex-wrap gap-2">
          <h2 class="text-sm font-bold text-rose-200 uppercase tracking-wider">Locales críticos (BAI &lt; 45)</h2>
          <a href="network/network_crisis_escalation.html"
             class="text-xs text-rose-400 no-underline hover:text-rose-300">Ver escalamiento →</a>
        </div>
        <div class="space-y-2">
          {outlier_html}
        </div>
      </div>
    </div>

    <!-- Ranking panel -->
    <div class="space-y-4">
      <div class="rounded-3xl border border-white/10 bg-white/5 p-5">
        <div class="flex items-center justify-between mb-4 flex-wrap gap-2">
          <h2 class="text-sm font-bold text-stone-300 uppercase tracking-wider">Top 10 Sucursales</h2>
          <span class="text-xs text-stone-500">por BAI</span>
        </div>
        <div class="space-y-1.5">
          {ranking_rows}
        </div>
        <div class="mt-4 pt-4 border-t border-white/8">
          <a href="hub/hub_ranking.html"
             class="block text-center text-xs text-violet-400 no-underline hover:text-violet-300">
            Ver ranking completo (50 locales) →
          </a>
        </div>
      </div>

      <!-- Quick actions -->
      <div class="rounded-3xl border border-white/10 bg-white/5 p-5">
        <h2 class="text-sm font-bold text-stone-300 uppercase tracking-wider mb-4">Acciones rápidas</h2>
        <div class="space-y-2">
          <a href="bulk/bulk_step1_compose.html"
             class="flex items-center gap-3 p-3 rounded-xl border border-violet-500/20 bg-violet-500/5
                    text-stone-300 text-xs font-semibold no-underline hover:bg-violet-500/10">
            <span class="text-violet-400">📣</span>
            Publicar promo en zona crítica
          </a>
          <a href="network/network_crisis_escalation.html"
             class="flex items-center gap-3 p-3 rounded-xl border border-rose-500/20 bg-rose-500/5
                    text-stone-300 text-xs font-semibold no-underline hover:bg-rose-500/10">
            <span class="text-rose-400">🚨</span>
            Ver alertas de crisis
          </a>
          <a href="reports/reports_hub.html"
             class="flex items-center gap-3 p-3 rounded-xl border border-indigo-500/20 bg-indigo-500/5
                    text-stone-300 text-xs font-semibold no-underline hover:bg-indigo-500/10">
            <span class="text-indigo-400">📄</span>
            Generar informe de red
          </a>
          <a href="hub/hub_audit_log.html"
             class="flex items-center gap-3 p-3 rounded-xl border border-white/8 bg-white/3
                    text-stone-300 text-xs font-semibold no-underline hover:bg-white/8">
            <span class="text-stone-400">📋</span>
            Log de actividad de agentes
          </a>
        </div>
      </div>
    </div>
  </div>
</div>"""

    nav = _nav_ent("vista_red.html")
    return _page("Vista de Red · Dashboard Enterprise", nav, body)


# ══════════════════════════════════════════════════════════════════════════════
# 4. CONSOLA DE MARCA BLANCA (Dashboard Screen 2)
# ══════════════════════════════════════════════════════════════════════════════

TENANTS = [
    ("Marketing Pro SL",         "org_7f3a2b", 12, 4.6, "#2563EB", "✓ Activo",    "wl",  True),
    ("Agencia Reputación XYZ",   "org_a1b2c3", 8,  4.4, "#16a34a", "✓ Activo",    "wl",  True),
    ("Gestión Digital Norte",    "org_c4d5e6", 25, 4.7, "#7c3aed", "✓ Activo",    "wl",  True),
    ("Reputación Online Sur",    "org_f7g8h9", 5,  4.2, "#dc2626", "⏳ Pendiente","no-wl",False),
    ("Consultoría Marca 360",    "org_i0j1k2", 18, 4.5, "#ea580c", "✓ Activo",    "wl",  True),
    ("Social Media Partners",    "org_l3m4n5", 3,  4.1, "#0891b2", "✗ Inactivo",  "no-wl",False),
    ("Franquicias Mediterráneas","org_o6p7q8", 47, 4.8, "#059669", "✓ Activo",    "wl",  True),
    ("Grupo Hostelería Premium", "org_r9s0t1", 32, 4.6, "#7c3aed", "✓ Activo",    "wl",  True),
]


def _tenant_row(name: str, org_id: str, locs: int, rating: float,
                color: str, status: str, wl: str, active: bool) -> str:
    status_cls = ("text-emerald-400" if "Activo" in status
                  else "text-amber-400" if "Pendiente" in status
                  else "text-rose-400")
    return f"""
    <tr class="border-b border-white/5 hover:bg-white/3">
      <td class="py-3 px-4">
        <div class="flex items-center gap-3">
          <div class="w-8 h-8 rounded-xl flex items-center justify-center text-white font-black text-sm flex-shrink-0"
               style="background:{color}">{name[0]}</div>
          <div>
            <p class="text-sm font-semibold text-white">{name}</p>
            <p class="text-xs text-stone-500 font-mono">{org_id}</p>
          </div>
        </div>
      </td>
      <td class="py-3 px-4 text-center">
        <span class="text-sm text-stone-300">{locs}</span>
      </td>
      <td class="py-3 px-4 text-center">
        <span class="text-sm text-stone-300">{rating}★</span>
      </td>
      <td class="py-3 px-4 text-center">
        <div class="flex items-center justify-center gap-2">
          <div class="w-4 h-4 rounded-full flex-shrink-0" style="background:{color}"></div>
          <span class="text-xs font-mono text-stone-400">{color}</span>
        </div>
      </td>
      <td class="py-3 px-4 text-center">
        {'<span class="px-2.5 py-1 rounded-full bg-violet-500/15 text-violet-300 border border-violet-500/25 text-xs font-bold">WL Activo</span>' if wl == "wl" else '<span class="px-2.5 py-1 rounded-full bg-stone-500/15 text-stone-400 text-xs">Estándar</span>'}
      </td>
      <td class="py-3 px-4 text-center">
        <span class="text-xs font-semibold {status_cls}">{status}</span>
      </td>
      <td class="py-3 px-4 text-right">
        <div class="flex gap-1.5 justify-end">
          <a href="white_label/wl_hub.html" class="px-2.5 py-1.5 rounded-lg border border-white/10 bg-white/5 text-stone-300 text-xs no-underline hover:bg-white/10">Editar WL</a>
          <a href="#" class="px-2.5 py-1.5 rounded-lg border border-white/8 bg-white/3 text-stone-400 text-xs no-underline hover:bg-white/8">Ajustes</a>
        </div>
      </td>
    </tr>"""


def consola_white_label() -> str:
    rows = "\n".join(_tenant_row(*t) for t in TENANTS)
    total_locs = sum(t[2] for t in TENANTS)
    active_wl  = sum(1 for t in TENANTS if t[7])

    body = f"""
<div class="mx-auto max-w-7xl px-4 py-8 sm:px-6 pb-20 fade-up">

  <div class="flex items-start justify-between gap-4 mb-6 flex-wrap">
    <div>
      <p class="text-xs uppercase tracking-[.2em] text-violet-300/70 mb-1">Dashboard Enterprise · Pantalla 2</p>
      <h1 class="text-3xl font-bold text-white">Consola de Marca Blanca</h1>
      <p class="text-stone-400 text-sm mt-1">
        Gestiona la identidad visual de cada agencia cliente y controla los límites de su plan.
      </p>
    </div>
    <div class="flex gap-2">
      <a href="white_label/wl_hub.html"
         class="px-5 py-2.5 rounded-2xl bg-gradient-to-r from-violet-600 to-indigo-600
                text-white font-bold text-sm no-underline hover:from-violet-500 hover:to-indigo-500">
        + Nuevo tenant
      </a>
    </div>
  </div>

  <!-- Stats -->
  <div class="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-6">
    <div class="rounded-2xl border border-white/10 bg-white/5 p-4 text-center">
      <p class="text-2xl font-black text-white">{len(TENANTS)}</p>
      <p class="text-xs text-stone-500 mt-0.5">Tenants totales</p>
    </div>
    <div class="rounded-2xl border border-violet-500/20 bg-violet-500/5 p-4 text-center">
      <p class="text-2xl font-black text-violet-300">{active_wl}</p>
      <p class="text-xs text-stone-500 mt-0.5">Con WL activo</p>
    </div>
    <div class="rounded-2xl border border-emerald-500/20 bg-emerald-500/5 p-4 text-center">
      <p class="text-2xl font-black text-emerald-400">{total_locs}</p>
      <p class="text-xs text-stone-500 mt-0.5">Locales gestionados</p>
    </div>
    <div class="rounded-2xl border border-indigo-500/20 bg-indigo-500/5 p-4 text-center">
      <p class="text-2xl font-black text-indigo-400">8</p>
      <p class="text-xs text-stone-500 mt-0.5">Dominios activos</p>
    </div>
  </div>

  <div class="grid grid-cols-1 xl:grid-cols-3 gap-6">

    <!-- Branding Editor -->
    <div class="space-y-4">

      <div class="rounded-3xl border border-violet-500/20 bg-violet-500/5 p-6">
        <h2 class="text-sm font-bold text-violet-200 uppercase tracking-wider mb-5">Editor de Branding Rápido</h2>

        <!-- Tenant selector -->
        <div class="mb-4">
          <label class="text-xs text-stone-400 block mb-1.5">Tenant activo</label>
          <select>
            {"".join(f"<option>{'★ ' if t[7] else ''}{t[0]}</option>" for t in TENANTS)}
          </select>
        </div>

        <!-- Color swatches -->
        <div class="mb-4">
          <label class="text-xs text-stone-400 block mb-2">Paleta de colores</label>
          <div class="grid grid-cols-3 gap-2">
            {"".join(f'<div class="h-10 rounded-xl cursor-pointer ring-2 ring-white/10 hover:ring-violet-400/40 transition-all" style="background:{t[4]}" title="{t[0]}"></div>' for t in TENANTS[:6])}
          </div>
        </div>

        <!-- Color inputs -->
        <div class="space-y-3">
          <div>
            <label class="text-xs text-stone-400 block mb-1.5">Color primario</label>
            <div class="flex gap-2 items-center">
              <input type="color" value="#2563EB" class="!w-12 !h-10 !p-1" />
              <input type="text" value="#2563EB" class="flex-1 font-mono text-xs" />
            </div>
          </div>
          <div>
            <label class="text-xs text-stone-400 block mb-1.5">Color secundario</label>
            <div class="flex gap-2 items-center">
              <input type="color" value="#1E40AF" class="!w-12 !h-10 !p-1" />
              <input type="text" value="#1E40AF" class="flex-1 font-mono text-xs" />
            </div>
          </div>
        </div>

        <!-- Logo upload -->
        <div class="mt-4">
          <label class="text-xs text-stone-400 block mb-1.5">Logo del tenant</label>
          <div class="border-2 border-dashed border-violet-500/30 rounded-2xl p-4 text-center hover:border-violet-400/50 cursor-pointer">
            <p class="text-xs text-stone-400">Arrastra el logo aquí o</p>
            <p class="text-xs text-violet-400 font-semibold mt-0.5">haz click para subir</p>
          </div>
        </div>

        <button class="w-full mt-4 px-4 py-3 rounded-2xl bg-gradient-to-r from-violet-600 to-indigo-600 text-white font-bold text-sm hover:from-violet-500 hover:to-indigo-500">
          Guardar y sincronizar →
        </button>

        <p class="text-xs text-stone-500 text-center mt-2">
          Cambios en vivo · Redis TTL 300s
        </p>
      </div>

      <!-- Domain mapping -->
      <div class="rounded-3xl border border-white/10 bg-white/5 p-5">
        <h2 class="text-sm font-bold text-stone-300 uppercase tracking-wider mb-4">Dominios activos</h2>
        <div class="space-y-2">
          <div class="flex items-center gap-2 p-2.5 rounded-xl bg-black/20 border border-white/8">
            <div class="w-2 h-2 rounded-full bg-emerald-400 flex-shrink-0"></div>
            <span class="text-xs font-mono text-stone-300 flex-1 truncate">clientes.marketingpro.com</span>
            <span class="text-xs text-stone-600">7f3a2b</span>
          </div>
          <div class="flex items-center gap-2 p-2.5 rounded-xl bg-black/20 border border-white/8">
            <div class="w-2 h-2 rounded-full bg-emerald-400 flex-shrink-0"></div>
            <span class="text-xs font-mono text-stone-300 flex-1 truncate">panel.agenciaxyz.com</span>
            <span class="text-xs text-stone-600">a1b2c3</span>
          </div>
          <div class="flex items-center gap-2 p-2.5 rounded-xl bg-black/20 border border-white/8">
            <div class="w-2 h-2 rounded-full bg-emerald-400 flex-shrink-0"></div>
            <span class="text-xs font-mono text-stone-300 flex-1 truncate">reputacion.digital-norte.es</span>
            <span class="text-xs text-stone-600">c4d5e6</span>
          </div>
          <div class="flex items-center gap-2 p-2.5 rounded-xl bg-black/20 border border-amber-500/15">
            <div class="w-2 h-2 rounded-full bg-amber-400 pulse flex-shrink-0"></div>
            <span class="text-xs font-mono text-stone-400 flex-1 truncate">reputacion-sur.com · SSL ⏳</span>
            <span class="text-xs text-stone-600">f7g8h9</span>
          </div>
          <a href="white_label/wl_step2_domain.html"
             class="block text-center text-xs text-violet-400 no-underline hover:text-violet-300 mt-2">
            Gestionar dominios →
          </a>
        </div>
      </div>
    </div>

    <!-- Tenant table -->
    <div class="xl:col-span-2">
      <div class="rounded-3xl border border-white/10 bg-white/5 overflow-hidden">
        <div class="flex items-center justify-between px-5 py-4 border-b border-white/8 flex-wrap gap-2">
          <h2 class="text-sm font-bold text-stone-300 uppercase tracking-wider">Gestión de Tenants</h2>
          <div class="flex gap-2">
            <input type="text" placeholder="Buscar tenant..." class="!w-48 text-xs !py-2" />
            <select class="!w-auto text-xs !py-2">
              <option>Todos</option>
              <option>WL Activo</option>
              <option>Sin WL</option>
            </select>
          </div>
        </div>
        <div class="overflow-x-auto">
          <table class="w-full">
            <thead>
              <tr class="text-xs text-stone-500 uppercase tracking-wider border-b border-white/8">
                <th class="text-left py-3 px-4 font-semibold">Tenant</th>
                <th class="text-center py-3 px-4 font-semibold">Locales</th>
                <th class="text-center py-3 px-4 font-semibold">Rating</th>
                <th class="text-center py-3 px-4 font-semibold">Color</th>
                <th class="text-center py-3 px-4 font-semibold">White Label</th>
                <th class="text-center py-3 px-4 font-semibold">Estado</th>
                <th class="text-right py-3 px-4 font-semibold">Acciones</th>
              </tr>
            </thead>
            <tbody>
              {rows}
            </tbody>
          </table>
        </div>
        <div class="px-5 py-3 border-t border-white/8 flex items-center justify-between">
          <p class="text-xs text-stone-500">{len(TENANTS)} tenants · {total_locs} locales totales</p>
          <div class="flex gap-2">
            <button class="px-3 py-1.5 rounded-lg border border-white/10 text-stone-400 text-xs hover:bg-white/5">← Anterior</button>
            <button class="px-3 py-1.5 rounded-lg border border-white/10 text-stone-400 text-xs hover:bg-white/5">Siguiente →</button>
          </div>
        </div>
      </div>

      <!-- Plan limits -->
      <div class="rounded-3xl border border-white/10 bg-white/5 p-5 mt-4">
        <h2 class="text-sm font-bold text-stone-300 uppercase tracking-wider mb-4">Límites del Plan Enterprise</h2>
        <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div>
            <div class="flex justify-between text-xs mb-1.5">
              <span class="text-stone-400">Tenants activos</span>
              <span class="text-stone-300 font-semibold">{len(TENANTS)} / 20</span>
            </div>
            <div class="h-2 rounded-full bg-white/10 overflow-hidden">
              <div class="h-full rounded-full bg-violet-500 bar-grow" style="width:{len(TENANTS)/20*100:.0f}%"></div>
            </div>
          </div>
          <div>
            <div class="flex justify-between text-xs mb-1.5">
              <span class="text-stone-400">Locales totales</span>
              <span class="text-stone-300 font-semibold">{total_locs} / 500</span>
            </div>
            <div class="h-2 rounded-full bg-white/10 overflow-hidden">
              <div class="h-full rounded-full bg-indigo-500 bar-grow" style="width:{total_locs/500*100:.0f}%"></div>
            </div>
          </div>
          <div>
            <div class="flex justify-between text-xs mb-1.5">
              <span class="text-stone-400">Dominios WL</span>
              <span class="text-stone-300 font-semibold">8 / 20</span>
            </div>
            <div class="h-2 rounded-full bg-white/10 overflow-hidden">
              <div class="h-full rounded-full bg-teal-500 bar-grow" style="width:40%"></div>
            </div>
          </div>
        </div>
      </div>
    </div>

  </div>
</div>"""

    nav = _nav_ent("consola_white_label.html")
    return _page("Consola de Marca Blanca · Dashboard Enterprise", nav, body,
                 extra_css="input[type=color]{background:transparent;border:1px solid rgba(255,255,255,.15);border-radius:8px;padding:2px;cursor:pointer;}")


# ══════════════════════════════════════════════════════════════════════════════
# RENDER
# ══════════════════════════════════════════════════════════════════════════════

def main() -> None:
    outputs = [
        (BULK_DIR  / "bulk_celery_monitor.html",             bulk_celery_monitor()),
        (NET_DIR   / "network_crisis_escalation.html",       network_crisis_escalation()),
        (ENT_DIR   / "vista_red.html",                       vista_red()),
        (ENT_DIR   / "consola_white_label.html",             consola_white_label()),
    ]

    for path, html in outputs:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(html, encoding="utf-8")
        print(f"✓  {path}")

    import webbrowser
    print("\n📌 Abriendo en el navegador:")
    base = "http://localhost:3000/enterprise"
    urls = [
        f"{base}/bulk/bulk_celery_monitor.html",
        f"{base}/network/network_crisis_escalation.html",
        f"{base}/vista_red.html",
        f"{base}/consola_white_label.html",
    ]
    for url in urls:
        webbrowser.open(url)
        print(f"   {url}")


if __name__ == "__main__":
    main()
