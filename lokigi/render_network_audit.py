"""
Renderiza el flujo "Auditoría de Red" (Network Health) del Plan Enterprise
como páginas HTML estáticas en frontend/static/enterprise/network/

Páginas del flujo:
  1. network_hub.html          — Hub de Salud de Red: KPIs globales, alertas activas
  2. network_step1_scan.html   — Escaneo de Reputación: nota media, anomalías mes a mes
  3. network_step2_crisis.html — Alerta de Crisis: IA detecta palabras críticas → alerta roja SuperAdmin
  4. network_step3_benchmark.html — Benchmarking Interno: ranking de locales, #1 vs necesitan mejora
  5. network_step4_training.html  — Plan de Entrenamiento: recomendaciones por feedback
  6. network_step5_report.html    — Informe Ejecutivo: exportar, historial, acciones
"""
from __future__ import annotations
import webbrowser
from pathlib import Path

ROOT = Path(__file__).parent
OUT_DIR = ROOT / "frontend" / "static" / "enterprise" / "network"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# ─── NAV ─────────────────────────────────────────────────────────────────────

PAGES = [
    ("network_hub.html",              "🌐 Hub"),
    ("network_step1_scan.html",       "1 · Escaneo"),
    ("network_step2_crisis.html",     "2 · Crisis"),
    ("network_step3_benchmark.html",  "3 · Benchmark"),
    ("network_step4_training.html",   "4 · Training"),
    ("network_step5_report.html",     "5 · Informe"),
]


def nav_bar(active: str) -> str:
    links = ""
    for href, label in PAGES:
        is_active = href == active
        is_crisis = "crisis" in href
        if is_active:
            cls = ("px-3 py-2 rounded-lg text-sm font-semibold text-violet-200 "
                   "bg-violet-500/20 border border-violet-400/20 no-underline")
        elif is_crisis:
            cls = ("px-3 py-2 rounded-lg text-sm font-medium text-rose-300/80 "
                   "hover:text-rose-200 hover:bg-rose-500/10 no-underline")
        else:
            cls = ("px-3 py-2 rounded-lg text-sm font-medium text-stone-400 "
                   "hover:text-white hover:bg-white/5 no-underline")
        links += f'<a href="{href}" class="{cls}">{label}</a>\n'

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
    <span class="text-stone-400 text-xs font-semibold">Auditoría de Red</span>
  </div>
  {links}
</nav>"""


def page(title: str, active: str, body: str) -> str:
    return f"""<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{title} | Network Health · Lokigi Enterprise</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <style>
    body {{ font-family: Arial, "Helvetica Neue", sans-serif; }}
    .no-underline {{ text-decoration: none; }}
    @keyframes fadeUp {{
      from {{ opacity: 0; transform: translateY(14px); }}
      to   {{ opacity: 1; transform: translateY(0); }}
    }}
    .fade-up {{ animation: fadeUp .35s ease both; }}
    @keyframes progress {{
      from {{ width: 0; }}
    }}
    .bar-anim {{ animation: progress 1.4s cubic-bezier(.4,0,.2,1) both; }}
    @keyframes pulse-dot {{
      0%,100% {{ opacity: 1; transform: scale(1); }}
      50%  {{ opacity: .5; transform: scale(1.6); }}
    }}
    .pulse-dot {{ animation: pulse-dot 1s ease-in-out infinite; }}
    @keyframes crisis-pulse {{
      0%,100% {{ box-shadow: 0 0 0 0 rgba(239,68,68,.4); }}
      50%  {{ box-shadow: 0 0 0 12px rgba(239,68,68,0); }}
    }}
    .crisis-pulse {{ animation: crisis-pulse 1.8s ease-in-out infinite; }}
    input, select, textarea {{
      background: rgba(255,255,255,.05);
      border: 1px solid rgba(255,255,255,.12);
      border-radius: 10px;
      color: #f1f5f9;
      padding: 10px 14px;
      font-size: 14px;
      width: 100%;
      outline: none;
    }}
    select option {{ background: #1c1917; }}
  </style>
</head>
<body class="min-h-screen bg-stone-950 text-stone-100">
{nav_bar(active)}
{body}
</body>
</html>"""


# ─── HUB ─────────────────────────────────────────────────────────────────────

def network_hub() -> str:
    body = """
<div class="mx-auto max-w-5xl px-4 py-10 sm:px-6 pb-20 fade-up">

  <!-- Header -->
  <div class="flex items-start justify-between gap-4 mb-8 flex-wrap">
    <div>
      <p class="text-xs uppercase tracking-[.2em] text-violet-300/70 mb-1">Enterprise · Auditoría de Red</p>
      <h1 class="text-3xl font-bold text-white">Hub de Salud de Red</h1>
      <p class="mt-1 text-stone-400 text-sm max-w-xl">
        Monitoreo centralizado de la reputación y calidad de toda la red de puntos de venta.
        La IA detecta anomalías, crisis y oportunidades de mejora en tiempo real.
      </p>
    </div>
    <div class="flex gap-3">
      <a href="network_step1_scan.html"
         class="px-5 py-2.5 rounded-2xl border border-white/10 bg-white/5
                text-stone-300 font-semibold text-sm hover:bg-white/10 no-underline">
        Iniciar escaneo
      </a>
      <a href="network_step5_report.html"
         class="px-5 py-2.5 rounded-2xl bg-gradient-to-r from-violet-600 to-indigo-600
                text-white font-bold text-sm hover:from-violet-500 hover:to-indigo-500 no-underline">
        Ver informe
      </a>
    </div>
  </div>

  <!-- Crisis banner -->
  <div class="rounded-3xl border border-rose-500/40 bg-rose-950/40 p-5 mb-6 flex items-start gap-4 crisis-pulse">
    <div class="w-10 h-10 rounded-full bg-rose-500 flex items-center justify-center flex-shrink-0 mt-0.5">
      <span class="text-white text-lg font-black">!</span>
    </div>
    <div class="flex-1">
      <p class="text-rose-300 font-bold text-base mb-1">🚨 2 alertas de crisis activas</p>
      <p class="text-rose-200/70 text-sm">
        La IA detectó menciones críticas de <strong class="text-rose-300">"suciedad"</strong> y
        <strong class="text-rose-300">"estafa"</strong> en 2 locales. Se notificó al SuperAdmin hace 4 min.
      </p>
    </div>
    <a href="network_step2_crisis.html"
       class="px-4 py-2 rounded-xl bg-rose-600 text-white text-xs font-bold hover:bg-rose-500 no-underline flex-shrink-0 self-center">
      Ver alertas →
    </a>
  </div>

  <!-- KPI grid -->
  <div class="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-8">
    <div class="rounded-2xl border border-emerald-500/20 bg-emerald-500/5 p-5 text-center">
      <p class="text-4xl font-black text-emerald-300">4.3</p>
      <p class="text-xs uppercase tracking-wider text-stone-400 mt-1">Nota media red</p>
      <p class="text-xs text-emerald-400 mt-1">▲ +0.1 vs mes anterior</p>
    </div>
    <div class="rounded-2xl border border-rose-500/20 bg-rose-500/5 p-5 text-center">
      <p class="text-4xl font-black text-rose-300">2</p>
      <p class="text-xs uppercase tracking-wider text-stone-400 mt-1">Crisis activas</p>
      <p class="text-xs text-rose-400 mt-1">Requieren acción inmediata</p>
    </div>
    <div class="rounded-2xl border border-amber-500/20 bg-amber-500/5 p-5 text-center">
      <p class="text-4xl font-black text-amber-300">5</p>
      <p class="text-xs uppercase tracking-wider text-stone-400 mt-1">Anomalías</p>
      <p class="text-xs text-amber-400 mt-1">Bajada &gt; 0.5★ este mes</p>
    </div>
    <div class="rounded-2xl border border-white/10 bg-white/5 p-5 text-center">
      <p class="text-4xl font-black text-white">50</p>
      <p class="text-xs uppercase tracking-wider text-stone-400 mt-1">Locales activos</p>
      <p class="text-xs text-stone-500 mt-1">Último scan: hace 2 h</p>
    </div>
  </div>

  <!-- Network health map (visual) -->
  <div class="rounded-3xl border border-white/10 bg-white/5 p-6 mb-6">
    <div class="flex items-center justify-between mb-5">
      <h2 class="text-base font-semibold text-white m-0">Distribución de salud por local</h2>
      <span class="text-xs text-stone-500">50 locales · actualizado hace 2 h</span>
    </div>
    <div class="flex flex-wrap gap-2 mb-4">
      <!-- Health dots grid — visual representation -->
      <!-- Green: ok, Amber: warning, Red: crisis -->
      <div class="flex flex-wrap gap-2 w-full">
        <!-- 38 green -->
        <div class="flex flex-wrap gap-1.5">
          <!-- Row simulation: 38 emerald, 5 amber, 2 rose, 5 stone -->
          <span title="Pizza Norte — Malasaña · 4.7★" class="w-8 h-8 rounded-lg bg-emerald-500/30 border border-emerald-500/40 flex items-center justify-center text-xs text-emerald-300 cursor-default font-bold">4.7</span>
          <span title="Pizza Norte — Chamberí · 4.5★" class="w-8 h-8 rounded-lg bg-emerald-500/30 border border-emerald-500/40 flex items-center justify-center text-xs text-emerald-300 cursor-default font-bold">4.5</span>
          <span title="Café Rápido — Gran Vía · 4.4★" class="w-8 h-8 rounded-lg bg-emerald-500/30 border border-emerald-500/40 flex items-center justify-center text-xs text-emerald-300 cursor-default font-bold">4.4</span>
          <span title="El Mar — Barceloneta · 4.8★" class="w-8 h-8 rounded-lg bg-emerald-500/30 border border-emerald-500/40 flex items-center justify-center text-xs text-emerald-300 cursor-default font-bold">4.8</span>
          <span title="Hotel Solimar Marbella · 4.6★" class="w-8 h-8 rounded-lg bg-emerald-500/30 border border-emerald-500/40 flex items-center justify-center text-xs text-emerald-300 cursor-default font-bold">4.6</span>
          <span title="Café Rápido — Retiro · 4.3★" class="w-8 h-8 rounded-lg bg-emerald-500/30 border border-emerald-500/40 flex items-center justify-center text-xs text-emerald-300 cursor-default font-bold">4.3</span>
          <span title="Pizza Norte — Vallecas · 4.2★" class="w-8 h-8 rounded-lg bg-emerald-500/30 border border-emerald-500/40 flex items-center justify-center text-xs text-emerald-300 cursor-default font-bold">4.2</span>
          <span title="El Mar — Diagonal · 4.5★" class="w-8 h-8 rounded-lg bg-emerald-500/30 border border-emerald-500/40 flex items-center justify-center text-xs text-emerald-300 cursor-default font-bold">4.5</span>
          <span title="Anomalía: Pizza Norte — Avellaneda ·  bajó 1★" class="w-8 h-8 rounded-lg bg-amber-500/30 border border-amber-500/40 flex items-center justify-center text-xs text-amber-300 cursor-default font-bold">3.4</span>
          <span title="Anomalía: Café Rápido — Leganés · bajó 0.7★" class="w-8 h-8 rounded-lg bg-amber-500/30 border border-amber-500/40 flex items-center justify-center text-xs text-amber-300 cursor-default font-bold">3.5</span>
          <span title="Crisis: El Mar — Sarrià · menciones 'suciedad'" class="w-8 h-8 rounded-lg bg-rose-500/30 border border-rose-500/50 flex items-center justify-center text-xs text-rose-300 cursor-default font-bold crisis-pulse">2.9</span>
          <span title="Crisis: Pizza Norte — Getafe · menciones 'estafa'" class="w-8 h-8 rounded-lg bg-rose-500/30 border border-rose-500/50 flex items-center justify-center text-xs text-rose-300 cursor-default font-bold">3.1</span>
          <!-- more green -->
          <span class="w-8 h-8 rounded-lg bg-emerald-500/30 border border-emerald-500/40 flex items-center justify-center text-xs text-emerald-300 cursor-default font-bold">4.1</span>
          <span class="w-8 h-8 rounded-lg bg-emerald-500/30 border border-emerald-500/40 flex items-center justify-center text-xs text-emerald-300 cursor-default font-bold">4.4</span>
          <span class="w-8 h-8 rounded-lg bg-emerald-500/30 border border-emerald-500/40 flex items-center justify-center text-xs text-emerald-300 cursor-default font-bold">4.6</span>
          <span class="w-8 h-8 rounded-lg bg-emerald-500/30 border border-emerald-500/40 flex items-center justify-center text-xs text-emerald-300 cursor-default font-bold">4.3</span>
          <span class="w-8 h-8 rounded-lg bg-amber-500/30 border border-amber-500/40 flex items-center justify-center text-xs text-amber-300 cursor-default font-bold">3.7</span>
          <span class="w-8 h-8 rounded-lg bg-emerald-500/30 border border-emerald-500/40 flex items-center justify-center text-xs text-emerald-300 cursor-default font-bold">4.5</span>
          <span class="w-8 h-8 rounded-lg bg-emerald-500/30 border border-emerald-500/40 flex items-center justify-center text-xs text-emerald-300 cursor-default font-bold">4.2</span>
          <span class="w-8 h-8 rounded-lg bg-emerald-500/30 border border-emerald-500/40 flex items-center justify-center text-xs text-emerald-300 cursor-default font-bold">4.7</span>
          <span class="w-8 h-8 rounded-lg bg-emerald-500/30 border border-emerald-500/40 flex items-center justify-center text-xs text-emerald-300 cursor-default font-bold">4.4</span>
          <span class="w-8 h-8 rounded-lg bg-emerald-500/30 border border-emerald-500/40 flex items-center justify-center text-xs text-emerald-300 cursor-default font-bold">4.6</span>
          <span class="w-8 h-8 rounded-lg bg-amber-500/30 border border-amber-500/40 flex items-center justify-center text-xs text-amber-300 cursor-default font-bold">3.6</span>
          <span class="w-8 h-8 rounded-lg bg-emerald-500/30 border border-emerald-500/40 flex items-center justify-center text-xs text-emerald-300 cursor-default font-bold">4.3</span>
          <span class="w-8 h-8 rounded-lg bg-emerald-500/30 border border-emerald-500/40 flex items-center justify-center text-xs text-emerald-300 cursor-default font-bold">4.5</span>
          <span class="w-8 h-8 rounded-lg bg-emerald-500/30 border border-emerald-500/40 flex items-center justify-center text-xs text-emerald-300 cursor-default font-bold">4.1</span>
          <span class="w-8 h-8 rounded-lg bg-emerald-500/30 border border-emerald-500/40 flex items-center justify-center text-xs text-emerald-300 cursor-default font-bold">4.4</span>
          <span class="w-8 h-8 rounded-lg bg-emerald-500/30 border border-emerald-500/40 flex items-center justify-center text-xs text-emerald-300 cursor-default font-bold">4.8</span>
          <span class="w-8 h-8 rounded-lg bg-emerald-500/30 border border-emerald-500/40 flex items-center justify-center text-xs text-emerald-300 cursor-default font-bold">4.2</span>
          <span class="w-8 h-8 rounded-lg bg-emerald-500/30 border border-emerald-500/40 flex items-center justify-center text-xs text-emerald-300 cursor-default font-bold">4.6</span>
          <span class="w-8 h-8 rounded-lg bg-emerald-500/30 border border-emerald-500/40 flex items-center justify-center text-xs text-emerald-300 cursor-default font-bold">4.3</span>
          <span class="w-8 h-8 rounded-lg bg-emerald-500/30 border border-emerald-500/40 flex items-center justify-center text-xs text-emerald-300 cursor-default font-bold">4.5</span>
          <span class="w-8 h-8 rounded-lg bg-emerald-500/30 border border-emerald-500/40 flex items-center justify-center text-xs text-emerald-300 cursor-default font-bold">4.4</span>
          <span class="w-8 h-8 rounded-lg bg-emerald-500/30 border border-emerald-500/40 flex items-center justify-center text-xs text-emerald-300 cursor-default font-bold">4.7</span>
          <span class="w-8 h-8 rounded-lg bg-emerald-500/30 border border-emerald-500/40 flex items-center justify-center text-xs text-emerald-300 cursor-default font-bold">4.3</span>
          <span class="w-8 h-8 rounded-lg bg-emerald-500/30 border border-emerald-500/40 flex items-center justify-center text-xs text-emerald-300 cursor-default font-bold">4.4</span>
          <span class="w-8 h-8 rounded-lg bg-emerald-500/30 border border-emerald-500/40 flex items-center justify-center text-xs text-emerald-300 cursor-default font-bold">4.1</span>
          <span class="w-8 h-8 rounded-lg bg-emerald-500/30 border border-emerald-500/40 flex items-center justify-center text-xs text-emerald-300 cursor-default font-bold">4.6</span>
          <span class="w-8 h-8 rounded-lg bg-emerald-500/30 border border-emerald-500/40 flex items-center justify-center text-xs text-emerald-300 cursor-default font-bold">4.5</span>
          <span class="w-8 h-8 rounded-lg bg-emerald-500/30 border border-emerald-500/40 flex items-center justify-center text-xs text-emerald-300 cursor-default font-bold">4.2</span>
          <span class="w-8 h-8 rounded-lg bg-emerald-500/30 border border-emerald-500/40 flex items-center justify-center text-xs text-emerald-300 cursor-default font-bold">4.3</span>
          <span class="w-8 h-8 rounded-lg bg-emerald-500/30 border border-emerald-500/40 flex items-center justify-center text-xs text-emerald-300 cursor-default font-bold">4.6</span>
          <span class="w-8 h-8 rounded-lg bg-emerald-500/30 border border-emerald-500/40 flex items-center justify-center text-xs text-emerald-300 cursor-default font-bold">4.4</span>
        </div>
      </div>
    </div>
    <div class="flex gap-4 text-xs mt-2">
      <div class="flex items-center gap-1.5"><span class="w-3 h-3 rounded bg-emerald-500/60"></span><span class="text-stone-400">Saludable (≥ 4.0)</span></div>
      <div class="flex items-center gap-1.5"><span class="w-3 h-3 rounded bg-amber-500/60"></span><span class="text-stone-400">Anomalía (bajó &gt; 0.5★)</span></div>
      <div class="flex items-center gap-1.5"><span class="w-3 h-3 rounded bg-rose-500/60"></span><span class="text-stone-400">Crisis (sentimiento crítico)</span></div>
    </div>
  </div>

  <!-- Quick actions -->
  <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
    <a href="network_step1_scan.html"
       class="rounded-2xl border border-white/10 bg-white/5 p-5 hover:bg-white/8 no-underline flex items-center gap-4">
      <span class="text-3xl">🔍</span>
      <div>
        <p class="text-sm font-bold text-white">Escaneo de Reputación</p>
        <p class="text-xs text-stone-500 mt-0.5">Nota media, anomalías, tendencias</p>
      </div>
    </a>
    <a href="network_step2_crisis.html"
       class="rounded-2xl border border-rose-500/30 bg-rose-500/5 p-5 hover:bg-rose-500/10 no-underline flex items-center gap-4">
      <span class="text-3xl">🚨</span>
      <div>
        <p class="text-sm font-bold text-rose-300">2 Alertas de Crisis</p>
        <p class="text-xs text-stone-500 mt-0.5">Sentimientos críticos detectados</p>
      </div>
    </a>
    <a href="network_step3_benchmark.html"
       class="rounded-2xl border border-white/10 bg-white/5 p-5 hover:bg-white/8 no-underline flex items-center gap-4">
      <span class="text-3xl">🏆</span>
      <div>
        <p class="text-sm font-bold text-white">Benchmarking Interno</p>
        <p class="text-xs text-stone-500 mt-0.5">#1 de la red y locales a mejorar</p>
      </div>
    </a>
  </div>

</div>"""
    return page("Hub de Salud de Red", "network_hub.html", body)


# ─── STEP 1 — Escaneo ────────────────────────────────────────────────────────

def step1_scan() -> str:
    locs = [
        ("El Mar — Barceloneta",       "Barcelona",  "4.8", "+0.3",  "emerald", True),
        ("Pizza Norte — Malasaña",     "Madrid",     "4.7", "+0.2",  "emerald", False),
        ("Hotel Solimar Marbella",     "Marbella",   "4.6", "+0.1",  "emerald", False),
        ("Café Rápido — Retiro",       "Madrid",     "4.4", "0.0",   "stone",   False),
        ("El Mar — Diagonal",          "Barcelona",  "4.3", "-0.1",  "stone",   False),
        ("Café Rápido — Gran Vía",     "Madrid",     "4.2", "-0.2",  "stone",   False),
        ("Pizza Norte — Getafe",       "Madrid",     "3.8", "-0.5",  "amber",   True),
        ("Café Rápido — Alcorcón",     "Madrid",     "3.6", "-0.7",  "amber",   True),
        ("Pizza Norte — Avellaneda",   "Madrid",     "3.4", "-1.0",  "amber",   True),
        ("El Mar — Sarrià",            "Barcelona",  "2.9", "-1.3",  "rose",    True),
        ("Pizza Norte — Getafe Sur",   "Madrid",     "3.1", "-0.9",  "rose",    True),
    ]

    COLOR_MAP = {
        "emerald": ("bg-emerald-500/15 text-emerald-300", "text-emerald-400"),
        "stone":   ("bg-stone-500/15 text-stone-400",     "text-stone-500"),
        "amber":   ("bg-amber-500/15 text-amber-300",     "text-amber-400"),
        "rose":    ("bg-rose-500/15 text-rose-300",       "text-rose-400"),
    }

    rows = ""
    for name, city, rating, delta, color, anomaly in locs:
        badge_cls, delta_cls = COLOR_MAP[color]
        anomaly_badge = ('<span class="px-2 py-0.5 rounded-full bg-amber-500/15 text-amber-300 text-xs font-bold ml-2">anomalía</span>'
                         if color == "amber" else
                         '<span class="px-2 py-0.5 rounded-full bg-rose-500/15 text-rose-300 text-xs font-bold ml-2">crisis</span>'
                         if color == "rose" else "")
        delta_icon = "▲" if delta.startswith("+") else ("▼" if delta.startswith("-") else "–")
        rows += f"""
        <tr class="border-b border-white/5 hover:bg-white/3">
          <td class="py-3 pl-6 pr-4">
            <span class="text-sm font-semibold text-stone-100">{name}</span>
            {anomaly_badge}
          </td>
          <td class="py-3 pr-4 text-sm text-stone-400">{city}</td>
          <td class="py-3 pr-4 text-center">
            <span class="px-2.5 py-1 rounded-full {badge_cls} text-sm font-black">{rating}★</span>
          </td>
          <td class="py-3 pr-4 text-center">
            <span class="text-sm font-bold {delta_cls}">{delta_icon} {delta}</span>
          </td>
          <td class="py-3 pr-6">
            <a href="network_step2_crisis.html" class="text-xs text-stone-500 hover:text-stone-300 no-underline">Ver detalle →</a>
          </td>
        </tr>"""

    body = f"""
<div class="mx-auto max-w-5xl px-4 py-10 sm:px-6 pb-20 fade-up">

  <div class="mb-8">
    <p class="text-xs uppercase tracking-[.2em] text-violet-300/70 mb-1">Auditoría de Red · Paso 1</p>
    <h1 class="text-3xl font-bold text-white">Escaneo de Reputación</h1>
    <p class="mt-1 text-stone-400 text-sm">
      Análisis de la nota media de toda la red y detección automática de anomalías mes a mes.
    </p>
  </div>

  <!-- Summary metrics -->
  <div class="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-8">
    <div class="rounded-2xl border border-emerald-500/20 bg-emerald-500/5 p-5 text-center">
      <p class="text-4xl font-black text-emerald-300">4.3★</p>
      <p class="text-xs uppercase tracking-wider text-stone-400 mt-1">Media de red</p>
      <p class="text-xs text-emerald-400 mt-1">▲ +0.1 vs. abril</p>
    </div>
    <div class="rounded-2xl border border-amber-500/20 bg-amber-500/5 p-5 text-center">
      <p class="text-4xl font-black text-amber-300">5</p>
      <p class="text-xs uppercase tracking-wider text-stone-400 mt-1">Anomalías</p>
      <p class="text-xs text-amber-400 mt-1">Bajada &gt; 0.5★ este mes</p>
    </div>
    <div class="rounded-2xl border border-rose-500/20 bg-rose-500/5 p-5 text-center">
      <p class="text-4xl font-black text-rose-300">2</p>
      <p class="text-xs uppercase tracking-wider text-stone-400 mt-1">Crisis activas</p>
      <p class="text-xs text-rose-400 mt-1">Debajo de 3.2★</p>
    </div>
    <div class="rounded-2xl border border-white/10 bg-white/5 p-5 text-center">
      <p class="text-4xl font-black text-white">43</p>
      <p class="text-xs uppercase tracking-wider text-stone-400 mt-1">Saludables</p>
      <p class="text-xs text-stone-500 mt-1">≥ 4.0★</p>
    </div>
  </div>

  <!-- Trend chart (visual bar) -->
  <div class="rounded-3xl border border-white/10 bg-white/5 p-6 mb-6">
    <h2 class="text-base font-semibold text-white mb-5">Tendencia de nota media — últimos 6 meses</h2>
    <div class="flex items-end gap-3 h-32">
      <div class="flex flex-col items-center gap-1 flex-1">
        <span class="text-xs text-stone-500 font-bold">4.1</span>
        <div class="w-full rounded-t-lg bg-violet-500/30 bar-anim" style="height:70%"></div>
        <span class="text-xs text-stone-600">Nov</span>
      </div>
      <div class="flex flex-col items-center gap-1 flex-1">
        <span class="text-xs text-stone-500 font-bold">4.0</span>
        <div class="w-full rounded-t-lg bg-violet-500/30 bar-anim" style="height:65%"></div>
        <span class="text-xs text-stone-600">Dic</span>
      </div>
      <div class="flex flex-col items-center gap-1 flex-1">
        <span class="text-xs text-stone-500 font-bold">4.0</span>
        <div class="w-full rounded-t-lg bg-violet-500/30 bar-anim" style="height:65%"></div>
        <span class="text-xs text-stone-600">Ene</span>
      </div>
      <div class="flex flex-col items-center gap-1 flex-1">
        <span class="text-xs text-stone-500 font-bold">4.1</span>
        <div class="w-full rounded-t-lg bg-violet-500/30 bar-anim" style="height:70%"></div>
        <span class="text-xs text-stone-600">Feb</span>
      </div>
      <div class="flex flex-col items-center gap-1 flex-1">
        <span class="text-xs text-stone-500 font-bold">4.2</span>
        <div class="w-full rounded-t-lg bg-violet-500/40 bar-anim" style="height:76%"></div>
        <span class="text-xs text-stone-600">Mar</span>
      </div>
      <div class="flex flex-col items-center gap-1 flex-1">
        <span class="text-xs text-stone-300 font-black">4.3</span>
        <div class="w-full rounded-t-lg bg-violet-500 bar-anim" style="height:82%"></div>
        <span class="text-xs text-violet-400 font-bold">Abr ↑</span>
      </div>
    </div>
  </div>

  <!-- Table -->
  <div class="rounded-3xl border border-white/10 bg-white/5 overflow-hidden mb-8">
    <div class="flex items-center justify-between px-6 py-4 border-b border-white/10">
      <h2 class="text-base font-semibold text-white m-0">Todos los locales</h2>
      <select class="w-40 text-xs py-2 px-3">
        <option>Todos</option>
        <option>Solo anomalías</option>
        <option>Solo crisis</option>
        <option>Solo saludables</option>
      </select>
    </div>
    <div class="overflow-x-auto">
      <table class="min-w-full text-sm">
        <thead>
          <tr class="border-b border-white/10 text-stone-400 text-xs uppercase tracking-wider">
            <th class="py-3 pr-4 pl-6 text-left font-semibold">Local</th>
            <th class="py-3 pr-4 text-left font-semibold">Ciudad</th>
            <th class="py-3 pr-4 text-center font-semibold">Nota</th>
            <th class="py-3 pr-4 text-center font-semibold">Δ mensual</th>
            <th class="py-3 pr-6 text-left font-semibold"></th>
          </tr>
        </thead>
        <tbody class="text-stone-200">
          {rows}
        </tbody>
      </table>
    </div>
  </div>

  <!-- Anomaly explanation -->
  <div class="rounded-3xl border border-amber-500/20 bg-amber-500/5 p-6 mb-8">
    <h3 class="text-sm font-bold text-amber-300 uppercase tracking-wider mb-3">¿Cómo detecta Lokigi las anomalías?</h3>
    <p class="text-stone-300 text-sm leading-relaxed mb-4">
      El sistema calcula la media móvil de 4 semanas por local y compara con la semana actual.
      Si la variación supera el umbral configurado (por defecto <strong class="text-white">−0.5★</strong>),
      el local se marca como anomalía y se genera una alerta en el Hub.
    </p>
    <div class="rounded-2xl bg-black/20 border border-white/10 p-4 font-mono text-xs text-stone-300 space-y-1">
      <div><span class="text-violet-400">anomaly_score</span> = current_rating − moving_avg_4w</div>
      <div><span class="text-violet-400">if</span> anomaly_score &lt; <span class="text-amber-300">-0.5</span>: trigger_anomaly_alert(location_id)</div>
      <div><span class="text-violet-400">if</span> anomaly_score &lt; <span class="text-rose-300">-1.0</span>: trigger_crisis_alert(location_id, notify_superadmin=True)</div>
    </div>
  </div>

  <!-- Nav -->
  <div class="flex justify-between items-center">
    <a href="network_hub.html"
       class="px-5 py-3 rounded-2xl border border-white/10 bg-white/5
              text-stone-300 font-semibold text-sm hover:bg-white/10 no-underline">
      ← Hub
    </a>
    <a href="network_step2_crisis.html"
       class="px-8 py-3 rounded-2xl bg-gradient-to-r from-violet-600 to-indigo-600
              text-white font-bold text-sm hover:from-violet-500 hover:to-indigo-500 no-underline">
      Ver alertas de crisis →
    </a>
  </div>
</div>"""
    return page("Paso 1 — Escaneo de Reputación", "network_step1_scan.html", body)


# ─── STEP 2 — Crisis ─────────────────────────────────────────────────────────

def step2_crisis() -> str:
    body = """
<div class="mx-auto max-w-4xl px-4 py-10 sm:px-6 pb-20 fade-up">

  <div class="mb-8">
    <p class="text-xs uppercase tracking-[.2em] text-rose-300/70 mb-1">Auditoría de Red · Paso 2</p>
    <h1 class="text-3xl font-bold text-white">Alerta de Crisis</h1>
    <p class="mt-1 text-stone-400 text-sm">
      La IA monitoriza el sentimiento de cada reseña. Cuando detecta palabras o patrones críticos,
      dispara una alerta inmediata al SuperAdmin de la agencia.
    </p>
  </div>

  <!-- How AI works -->
  <div class="rounded-3xl border border-violet-500/20 bg-violet-500/5 p-6 mb-6">
    <h2 class="text-base font-semibold text-white mb-4">¿Cómo funciona la detección de crisis?</h2>
    <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
      <div class="text-center">
        <div class="w-12 h-12 rounded-2xl bg-violet-500/20 flex items-center justify-center text-2xl mx-auto mb-3">📥</div>
        <p class="text-sm font-semibold text-white mb-1">Ingesta continua</p>
        <p class="text-xs text-stone-400">GBP API envía nuevas reseñas al webhook de Lokigi cada 15 min</p>
      </div>
      <div class="text-center">
        <div class="w-12 h-12 rounded-2xl bg-indigo-500/20 flex items-center justify-center text-2xl mx-auto mb-3">🤖</div>
        <p class="text-sm font-semibold text-white mb-1">Análisis NLP</p>
        <p class="text-xs text-stone-400">Modelo de sentimiento detecta categorías críticas: higiene, fraude, seguridad, servicio</p>
      </div>
      <div class="text-center">
        <div class="w-12 h-12 rounded-2xl bg-rose-500/20 flex items-center justify-center text-2xl mx-auto mb-3">🚨</div>
        <p class="text-sm font-semibold text-white mb-1">Alerta inmediata</p>
        <p class="text-xs text-stone-400">Email + push al SuperAdmin + ticket automático de gestión</p>
      </div>
    </div>
  </div>

  <!-- Crisis cards -->
  <h2 class="text-base font-semibold text-white mb-4">Alertas activas — 2 crisis detectadas</h2>

  <!-- Crisis 1 -->
  <div class="rounded-3xl border border-rose-500/40 bg-rose-950/30 p-6 mb-5 crisis-pulse">
    <div class="flex items-start justify-between gap-4 mb-5 flex-wrap">
      <div class="flex items-center gap-3">
        <div class="w-10 h-10 rounded-2xl bg-rose-500 flex items-center justify-center text-white font-black text-lg flex-shrink-0">!</div>
        <div>
          <p class="text-rose-300 font-black text-lg">El Mar — Sarrià · Barcelona</p>
          <p class="text-stone-400 text-sm">Detectado: hace 4 min · 1 reseña crítica</p>
        </div>
      </div>
      <span class="px-3 py-1.5 rounded-full bg-rose-500/20 border border-rose-500/30 text-rose-300 text-xs font-black uppercase tracking-wider">
        🔴 Crisis activa
      </span>
    </div>

    <!-- The offending review -->
    <div class="rounded-2xl border border-rose-500/25 bg-black/20 p-5 mb-5">
      <div class="flex items-center gap-3 mb-3">
        <div class="w-9 h-9 rounded-full bg-stone-700 flex items-center justify-center text-sm font-bold text-stone-300">MG</div>
        <div>
          <p class="text-sm font-semibold text-stone-200">Marta García</p>
          <div class="flex gap-0.5 text-amber-400 text-xs">★★☆☆☆</div>
        </div>
        <span class="ml-auto text-xs text-stone-600">hace 5 min · Google</span>
      </div>
      <p class="text-stone-300 text-sm leading-relaxed">
        "Completamente decepcionante. El local estaba <strong class="text-rose-300 bg-rose-500/15 px-1 rounded">sucio</strong>, los baños en estado lamentable
        y el pescado olía mal. No volveré nunca. Esperaba más de un sitio de este nivel de precios."
      </p>
      <div class="flex flex-wrap gap-2 mt-4">
        <span class="px-2.5 py-1 rounded-full bg-rose-500/20 border border-rose-500/20 text-rose-300 text-xs font-bold">🔴 suciedad</span>
        <span class="px-2.5 py-1 rounded-full bg-rose-500/20 border border-rose-500/20 text-rose-300 text-xs font-bold">🔴 higiene alimentaria</span>
        <span class="px-2.5 py-1 rounded-full bg-amber-500/15 border border-amber-500/15 text-amber-300 text-xs font-bold">⚠️ precio/valor</span>
        <span class="text-xs text-stone-500 self-center ml-1">Confianza del modelo: 97.3%</span>
      </div>
    </div>

    <div class="grid grid-cols-1 sm:grid-cols-3 gap-3">
      <div class="rounded-2xl bg-black/15 border border-white/8 p-4 text-center">
        <p class="text-2xl font-black text-rose-300">2.9★</p>
        <p class="text-xs text-stone-500 mt-1">Nota actual</p>
      </div>
      <div class="rounded-2xl bg-black/15 border border-white/8 p-4 text-center">
        <p class="text-2xl font-black text-amber-300">-1.3</p>
        <p class="text-xs text-stone-500 mt-1">Caída este mes</p>
      </div>
      <div class="rounded-2xl bg-black/15 border border-white/8 p-4 text-center">
        <p class="text-2xl font-black text-white">1</p>
        <p class="text-xs text-stone-500 mt-1">Reseñas críticas nuevas</p>
      </div>
    </div>

    <div class="flex flex-wrap gap-3 mt-5">
      <button class="px-5 py-2.5 rounded-xl bg-rose-600 text-white text-sm font-bold hover:bg-rose-500">
        📧 Responder ahora
      </button>
      <button class="px-5 py-2.5 rounded-xl border border-white/10 bg-white/5 text-stone-300 text-sm font-semibold hover:bg-white/10">
        📋 Crear ticket de gestión
      </button>
      <button class="px-5 py-2.5 rounded-xl border border-white/10 bg-white/5 text-stone-300 text-sm font-semibold hover:bg-white/10">
        🔕 Descartar alerta
      </button>
    </div>
  </div>

  <!-- Crisis 2 -->
  <div class="rounded-3xl border border-rose-500/30 bg-rose-950/20 p-6 mb-8">
    <div class="flex items-start justify-between gap-4 mb-5 flex-wrap">
      <div class="flex items-center gap-3">
        <div class="w-10 h-10 rounded-2xl bg-rose-600 flex items-center justify-center text-white font-black text-lg flex-shrink-0">!</div>
        <div>
          <p class="text-rose-300 font-black text-lg">Pizza Norte — Getafe Sur · Madrid</p>
          <p class="text-stone-400 text-sm">Detectado: hace 47 min · 3 reseñas críticas</p>
        </div>
      </div>
      <span class="px-3 py-1.5 rounded-full bg-rose-500/20 border border-rose-500/30 text-rose-300 text-xs font-black uppercase tracking-wider">
        🔴 Crisis activa
      </span>
    </div>

    <div class="rounded-2xl border border-rose-500/20 bg-black/20 p-5 mb-5">
      <div class="flex items-center gap-3 mb-3">
        <div class="w-9 h-9 rounded-full bg-stone-700 flex items-center justify-center text-sm font-bold text-stone-300">JR</div>
        <div>
          <p class="text-sm font-semibold text-stone-200">Javier Ruiz</p>
          <div class="flex gap-0.5 text-amber-400 text-xs">★☆☆☆☆</div>
        </div>
        <span class="ml-auto text-xs text-stone-600">hace 47 min · Google</span>
      </div>
      <p class="text-stone-300 text-sm leading-relaxed">
        "Me cobraron de más y cuando reclamé me dijeron que era normal. Eso es una
        <strong class="text-rose-300 bg-rose-500/15 px-1 rounded">estafa</strong> descarada.
        Voy a poner una denuncia. 3 personas de mi mesa con el mismo problema."
      </p>
      <div class="flex flex-wrap gap-2 mt-4">
        <span class="px-2.5 py-1 rounded-full bg-rose-500/20 border border-rose-500/20 text-rose-300 text-xs font-bold">🔴 fraude / estafa</span>
        <span class="px-2.5 py-1 rounded-full bg-rose-500/20 border border-rose-500/20 text-rose-300 text-xs font-bold">🔴 denuncia legal</span>
        <span class="px-2.5 py-1 rounded-full bg-amber-500/15 border border-amber-500/15 text-amber-300 text-xs font-bold">⚠️ gestión deficiente</span>
        <span class="text-xs text-stone-500 self-center ml-1">Confianza del modelo: 99.1%</span>
      </div>
    </div>

    <div class="flex flex-wrap gap-3">
      <button class="px-5 py-2.5 rounded-xl bg-rose-600 text-white text-sm font-bold hover:bg-rose-500">
        📧 Responder ahora
      </button>
      <button class="px-5 py-2.5 rounded-xl border border-white/10 bg-white/5 text-stone-300 text-sm font-semibold hover:bg-white/10">
        📋 Crear ticket urgente
      </button>
    </div>
  </div>

  <!-- SuperAdmin notification log -->
  <div class="rounded-3xl border border-white/10 bg-white/5 p-6 mb-8">
    <h2 class="text-base font-semibold text-white mb-4">Registro de notificaciones a SuperAdmin</h2>
    <div class="space-y-3 font-mono text-xs">
      <div class="flex gap-3 text-stone-300">
        <span class="text-stone-500 flex-shrink-0">09:58:12</span>
        <span class="text-rose-400 font-bold">CRISIS_ALERT</span>
        <span>loc=el-mar-sarria · keywords=["suciedad","higiene"] · confidence=97.3% · notified=superadmin@agencia.es</span>
      </div>
      <div class="flex gap-3 text-stone-300">
        <span class="text-stone-500 flex-shrink-0">09:58:13</span>
        <span class="text-indigo-400">PUSH_SENT</span>
        <span>channel=email · to=superadmin@agencia.es · subject="🚨 Crisis en El Mar — Sarrià"</span>
      </div>
      <div class="flex gap-3 text-stone-300">
        <span class="text-stone-500 flex-shrink-0">09:11:04</span>
        <span class="text-rose-400 font-bold">CRISIS_ALERT</span>
        <span>loc=pizza-norte-getafe-sur · keywords=["estafa","denuncia"] · confidence=99.1% · notified=superadmin@agencia.es</span>
      </div>
      <div class="flex gap-3 text-stone-300">
        <span class="text-stone-500 flex-shrink-0">09:11:04</span>
        <span class="text-indigo-400">PUSH_SENT</span>
        <span>channel=email+push · to=superadmin@agencia.es · subject="🚨 Crisis en Pizza Norte — Getafe Sur"</span>
      </div>
    </div>
  </div>

  <!-- Nav -->
  <div class="flex justify-between items-center">
    <a href="network_step1_scan.html"
       class="px-5 py-3 rounded-2xl border border-white/10 bg-white/5
              text-stone-300 font-semibold text-sm hover:bg-white/10 no-underline">
      ← Escaneo
    </a>
    <a href="network_step3_benchmark.html"
       class="px-8 py-3 rounded-2xl bg-gradient-to-r from-violet-600 to-indigo-600
              text-white font-bold text-sm hover:from-violet-500 hover:to-indigo-500 no-underline">
      Benchmarking →
    </a>
  </div>
</div>"""
    return page("Paso 2 — Alertas de Crisis", "network_step2_crisis.html", body)


# ─── STEP 3 — Benchmark ──────────────────────────────────────────────────────

def step3_benchmark() -> str:
    locations = [
        (1,  "🥇", "El Mar — Barceloneta",      "Barcelona",  "4.8", 312, "emerald", True),
        (2,  "🥈", "Pizza Norte — Malasaña",     "Madrid",     "4.7", 278, "emerald", False),
        (3,  "🥉", "Hotel Solimar Marbella",     "Marbella",   "4.6", 195, "violet",  False),
        (4,  "",   "El Mar — Diagonal",          "Barcelona",  "4.5", 241, "emerald", False),
        (5,  "",   "Café Rápido — Retiro",       "Madrid",     "4.4", 310, "emerald", False),
        (6,  "",   "Café Rápido — Gran Vía",     "Madrid",     "4.2", 425, "stone",   False),
        (40, "",   "Café Rápido — Alcorcón",     "Madrid",     "3.6",  87, "amber",   True),
        (41, "",   "Pizza Norte — Avellaneda",   "Madrid",     "3.4",  62, "amber",   True),
        (42, "",   "Pizza Norte — Getafe Sur",   "Madrid",     "3.1",  54, "rose",    True),
        (43, "",   "El Mar — Sarrià",            "Barcelona",  "2.9",  39, "rose",    True),
    ]

    COLOR_MAP = {
        "emerald": "text-emerald-300",
        "violet":  "text-violet-300",
        "stone":   "text-stone-400",
        "amber":   "text-amber-300",
        "rose":    "text-rose-300",
    }
    BAR_COLOR = {
        "emerald": "bg-emerald-500",
        "violet":  "bg-violet-500",
        "stone":   "bg-stone-500",
        "amber":   "bg-amber-500",
        "rose":    "bg-rose-500",
    }
    BADGE = {
        "emerald": "",
        "violet":  "",
        "stone":   "",
        "amber":   '<span class="px-2 py-0.5 rounded-full bg-amber-500/15 text-amber-300 text-xs font-bold ml-2">entrenamiento</span>',
        "rose":    '<span class="px-2 py-0.5 rounded-full bg-rose-500/15 text-rose-300 text-xs font-bold ml-2">crisis</span>',
    }

    rows = ""
    for rank, medal, name, city, rating, reviews, color, needs_training in locations:
        bar_pct = int((float(rating) / 5.0) * 100)
        if rank in (40, 41, 42, 43):
            rank_display = f"···"
        else:
            rank_display = str(rank)
        rows += f"""
        <tr class="border-b border-white/5 hover:bg-white/3">
          <td class="py-3 pl-6 pr-3 text-center">
            <span class="text-lg">{medal or rank_display}</span>
          </td>
          <td class="py-3 pr-4">
            <span class="text-sm font-semibold text-stone-100">{name}</span>
            {BADGE[color]}
          </td>
          <td class="py-3 pr-4 text-sm text-stone-400">{city}</td>
          <td class="py-3 pr-4 text-center">
            <span class="text-sm font-black {COLOR_MAP[color]}">{rating}★</span>
          </td>
          <td class="py-3 pr-4 text-sm text-stone-500 text-center">{reviews}</td>
          <td class="py-3 pr-6 w-32">
            <div class="h-2 rounded-full bg-black/30 overflow-hidden">
              <div class="h-full rounded-full bar-anim {BAR_COLOR[color]}" style="width:{bar_pct}%"></div>
            </div>
          </td>
        </tr>"""

    body = f"""
<div class="mx-auto max-w-5xl px-4 py-10 sm:px-6 pb-20 fade-up">

  <div class="mb-8">
    <p class="text-xs uppercase tracking-[.2em] text-violet-300/70 mb-1">Auditoría de Red · Paso 3</p>
    <h1 class="text-3xl font-bold text-white">Benchmarking Interno</h1>
    <p class="mt-1 text-stone-400 text-sm">
      Ranking completo de todos los locales de la red. Identifica tu #1 y los que necesitan formación basada en el feedback real de clientes.
    </p>
  </div>

  <!-- Podium -->
  <div class="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-8">
    <!-- #2 -->
    <div class="rounded-3xl border border-stone-500/25 bg-stone-500/5 p-6 text-center sm:mt-6">
      <p class="text-4xl mb-2">🥈</p>
      <p class="text-sm font-bold text-stone-200 mb-1">Pizza Norte — Malasaña</p>
      <p class="text-xs text-stone-500 mb-3">Madrid</p>
      <p class="text-3xl font-black text-stone-200">4.7★</p>
      <p class="text-xs text-stone-500 mt-1">278 reseñas</p>
    </div>
    <!-- #1 -->
    <div class="rounded-3xl border border-emerald-500/30 bg-emerald-950/30 p-6 text-center ring-2 ring-emerald-500/20">
      <p class="text-4xl mb-2">🥇</p>
      <p class="text-sm font-black text-emerald-200 mb-1">#1 de la red</p>
      <p class="text-base font-bold text-white mb-1">El Mar — Barceloneta</p>
      <p class="text-xs text-stone-400 mb-3">Barcelona</p>
      <p class="text-4xl font-black text-emerald-300">4.8★</p>
      <p class="text-xs text-stone-500 mt-1">312 reseñas · mejor nota de la red</p>
      <div class="mt-4 rounded-xl bg-emerald-500/10 border border-emerald-500/20 p-3">
        <p class="text-xs text-emerald-300 font-semibold">Fortalezas clave</p>
        <p class="text-xs text-stone-400 mt-1">"Fresco", "trato excelente", "vistas únicas"</p>
      </div>
    </div>
    <!-- #3 -->
    <div class="rounded-3xl border border-violet-500/20 bg-violet-500/5 p-6 text-center sm:mt-6">
      <p class="text-4xl mb-2">🥉</p>
      <p class="text-sm font-bold text-violet-200 mb-1">Hotel Solimar Marbella</p>
      <p class="text-xs text-stone-500 mb-3">Marbella</p>
      <p class="text-3xl font-black text-violet-300">4.6★</p>
      <p class="text-xs text-stone-500 mt-1">195 reseñas</p>
    </div>
  </div>

  <!-- Full ranking table -->
  <div class="rounded-3xl border border-white/10 bg-white/5 overflow-hidden mb-6">
    <div class="px-6 py-4 border-b border-white/10">
      <h2 class="text-base font-semibold text-white m-0">Ranking completo (muestra representativa)</h2>
    </div>
    <div class="overflow-x-auto">
      <table class="min-w-full text-sm">
        <thead>
          <tr class="border-b border-white/10 text-stone-400 text-xs uppercase tracking-wider">
            <th class="py-3 pl-6 pr-3 text-center font-semibold">#</th>
            <th class="py-3 pr-4 text-left font-semibold">Local</th>
            <th class="py-3 pr-4 text-left font-semibold">Ciudad</th>
            <th class="py-3 pr-4 text-center font-semibold">Nota</th>
            <th class="py-3 pr-4 text-center font-semibold">Reseñas</th>
            <th class="py-3 pr-6 text-left font-semibold">Score</th>
          </tr>
        </thead>
        <tbody class="text-stone-200">
          {rows}
        </tbody>
      </table>
    </div>
  </div>

  <!-- Training needs summary -->
  <div class="rounded-3xl border border-amber-500/20 bg-amber-500/5 p-6 mb-8">
    <h2 class="text-base font-semibold text-white mb-2">Locales que necesitan entrenamiento</h2>
    <p class="text-stone-400 text-sm mb-4">
      Basado en análisis de feedback: 7 locales tienen patrones recurrentes de queja que pueden resolverse con formación de equipo.
    </p>
    <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
      <div class="rounded-2xl border border-white/8 bg-black/15 p-4">
        <p class="text-sm font-bold text-amber-300 mb-1">⚠️ Café Rápido — Alcorcón</p>
        <p class="text-xs text-stone-400">Problema recurrente: <strong class="text-stone-300">"lentitud en el servicio"</strong> (21 menciones este mes)</p>
      </div>
      <div class="rounded-2xl border border-white/8 bg-black/15 p-4">
        <p class="text-sm font-bold text-amber-300 mb-1">⚠️ Pizza Norte — Avellaneda</p>
        <p class="text-xs text-stone-400">Problema recurrente: <strong class="text-stone-300">"masa fría"</strong> y <strong class="text-stone-300">"pedidos incorrectos"</strong> (17 menciones)</p>
      </div>
      <div class="rounded-2xl border border-white/8 bg-black/15 p-4">
        <p class="text-sm font-bold text-rose-300 mb-1">🔴 Pizza Norte — Getafe Sur</p>
        <p class="text-xs text-stone-400">Crisis: <strong class="text-stone-300">"cobros incorrectos"</strong> — requiere acción urgente de management</p>
      </div>
      <div class="rounded-2xl border border-white/8 bg-black/15 p-4">
        <p class="text-sm font-bold text-rose-300 mb-1">🔴 El Mar — Sarrià</p>
        <p class="text-xs text-stone-400">Crisis: <strong class="text-stone-300">"limpieza"</strong> — requiere inspección de local y protocolo de higiene</p>
      </div>
    </div>
  </div>

  <!-- Nav -->
  <div class="flex justify-between items-center">
    <a href="network_step2_crisis.html"
       class="px-5 py-3 rounded-2xl border border-white/10 bg-white/5
              text-stone-300 font-semibold text-sm hover:bg-white/10 no-underline">
      ← Crisis
    </a>
    <a href="network_step4_training.html"
       class="px-8 py-3 rounded-2xl bg-gradient-to-r from-violet-600 to-indigo-600
              text-white font-bold text-sm hover:from-violet-500 hover:to-indigo-500 no-underline">
      Plan de entrenamiento →
    </a>
  </div>
</div>"""
    return page("Paso 3 — Benchmarking Interno", "network_step3_benchmark.html", body)


# ─── STEP 4 — Training ───────────────────────────────────────────────────────

def step4_training() -> str:
    body = """
<div class="mx-auto max-w-4xl px-4 py-10 sm:px-6 pb-20 fade-up">

  <div class="mb-8">
    <p class="text-xs uppercase tracking-[.2em] text-violet-300/70 mb-1">Auditoría de Red · Paso 4</p>
    <h1 class="text-3xl font-bold text-white">Plan de Entrenamiento</h1>
    <p class="mt-1 text-stone-400 text-sm">
      Lokigi analiza el feedback de los clientes y genera automáticamente recomendaciones de mejora
      personalizadas por local. Basado en NLP sobre 4.200 reseñas del último trimestre.
    </p>
  </div>

  <!-- Summary -->
  <div class="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-8">
    <div class="rounded-2xl border border-white/10 bg-white/5 p-4 text-center">
      <p class="text-3xl font-black text-white">7</p>
      <p class="text-xs uppercase tracking-wider text-stone-400 mt-1">Locales con plan</p>
    </div>
    <div class="rounded-2xl border border-amber-500/15 bg-amber-500/5 p-4 text-center">
      <p class="text-3xl font-black text-amber-300">23</p>
      <p class="text-xs uppercase tracking-wider text-stone-400 mt-1">Acciones generadas</p>
    </div>
    <div class="rounded-2xl border border-violet-500/15 bg-violet-500/5 p-4 text-center">
      <p class="text-3xl font-black text-violet-300">4.200</p>
      <p class="text-xs uppercase tracking-wider text-stone-400 mt-1">Reseñas analizadas</p>
    </div>
    <div class="rounded-2xl border border-emerald-500/15 bg-emerald-500/5 p-4 text-center">
      <p class="text-3xl font-black text-emerald-300">+0.6★</p>
      <p class="text-xs uppercase tracking-wider text-stone-400 mt-1">Mejora estimada</p>
    </div>
  </div>

  <!-- Training cards -->

  <!-- Card 1: Café Rápido Alcorcón -->
  <div class="rounded-3xl border border-amber-500/20 bg-white/4 p-6 mb-5">
    <div class="flex items-start justify-between gap-3 mb-5 flex-wrap">
      <div>
        <p class="text-base font-bold text-white">Café Rápido — Alcorcón</p>
        <p class="text-xs text-stone-500">Madrid · Nota actual: <span class="text-amber-300 font-bold">3.6★</span> · Objetivo: 4.2★</p>
      </div>
      <span class="px-3 py-1.5 rounded-full bg-amber-500/15 border border-amber-500/20 text-amber-300 text-xs font-bold">
        Prioridad alta
      </span>
    </div>

    <div class="rounded-2xl bg-black/15 border border-white/8 p-4 mb-4">
      <p class="text-xs text-stone-500 uppercase tracking-wider font-semibold mb-3">Diagnóstico IA — Top quejas</p>
      <div class="space-y-2">
        <div class="flex items-center gap-3">
          <span class="w-2 h-2 rounded-full bg-rose-400 flex-shrink-0"></span>
          <span class="text-sm text-stone-200 flex-1">"lentitud en el servicio"</span>
          <span class="text-xs text-stone-500 font-mono">21 menciones</span>
          <div class="w-20 h-1.5 rounded-full bg-black/30 overflow-hidden">
            <div class="h-full rounded-full bg-rose-500 bar-anim" style="width:78%"></div>
          </div>
        </div>
        <div class="flex items-center gap-3">
          <span class="w-2 h-2 rounded-full bg-amber-400 flex-shrink-0"></span>
          <span class="text-sm text-stone-200 flex-1">"esperas largas en caja"</span>
          <span class="text-xs text-stone-500 font-mono">14 menciones</span>
          <div class="w-20 h-1.5 rounded-full bg-black/30 overflow-hidden">
            <div class="h-full rounded-full bg-amber-500 bar-anim" style="width:52%"></div>
          </div>
        </div>
        <div class="flex items-center gap-3">
          <span class="w-2 h-2 rounded-full bg-amber-400 flex-shrink-0"></span>
          <span class="text-sm text-stone-200 flex-1">"personal poco atento"</span>
          <span class="text-xs text-stone-500 font-mono">9 menciones</span>
          <div class="w-20 h-1.5 rounded-full bg-black/30 overflow-hidden">
            <div class="h-full rounded-full bg-amber-500 bar-anim" style="width:33%"></div>
          </div>
        </div>
      </div>
    </div>

    <div class="space-y-2">
      <p class="text-xs text-stone-500 uppercase tracking-wider font-semibold mb-3">Acciones recomendadas por la IA</p>
      <div class="flex items-start gap-3 p-3 rounded-xl bg-emerald-500/5 border border-emerald-500/15">
        <span class="text-emerald-400 mt-0.5">✓</span>
        <div>
          <p class="text-sm font-semibold text-stone-200">Sesión de formación: "Flujo de atención rápida"</p>
          <p class="text-xs text-stone-500 mt-0.5">Protocolo estándar de toma de pedido — objetivo: &lt; 2 min por cliente</p>
        </div>
      </div>
      <div class="flex items-start gap-3 p-3 rounded-xl bg-emerald-500/5 border border-emerald-500/15">
        <span class="text-emerald-400 mt-0.5">✓</span>
        <div>
          <p class="text-sm font-semibold text-stone-200">Revisión de turnos y refuerzo en hora punta (13–15 h)</p>
          <p class="text-xs text-stone-500 mt-0.5">Los picos de queja coinciden con el tramo de mediodía (análisis de timestamps)</p>
        </div>
      </div>
      <div class="flex items-start gap-3 p-3 rounded-xl bg-violet-500/5 border border-violet-500/15">
        <span class="text-violet-400 mt-0.5">→</span>
        <div>
          <p class="text-sm font-semibold text-stone-200">Instalar segunda caja exprés (recomendación estructural)</p>
          <p class="text-xs text-stone-500 mt-0.5">Requiere aprobación del tenant manager antes de ejecutar</p>
        </div>
      </div>
    </div>
  </div>

  <!-- Card 2: Pizza Norte Avellaneda -->
  <div class="rounded-3xl border border-amber-500/20 bg-white/4 p-6 mb-5">
    <div class="flex items-start justify-between gap-3 mb-5 flex-wrap">
      <div>
        <p class="text-base font-bold text-white">Pizza Norte — Avellaneda</p>
        <p class="text-xs text-stone-500">Madrid · Nota actual: <span class="text-amber-300 font-bold">3.4★</span> · Objetivo: 4.0★</p>
      </div>
      <span class="px-3 py-1.5 rounded-full bg-rose-500/15 border border-rose-500/20 text-rose-300 text-xs font-bold">
        Prioridad urgente
      </span>
    </div>

    <div class="rounded-2xl bg-black/15 border border-white/8 p-4 mb-4">
      <p class="text-xs text-stone-500 uppercase tracking-wider font-semibold mb-3">Top quejas</p>
      <div class="space-y-2">
        <div class="flex items-center gap-3">
          <span class="w-2 h-2 rounded-full bg-rose-400 flex-shrink-0"></span>
          <span class="text-sm text-stone-200 flex-1">"masa fría al llegar"</span>
          <span class="text-xs text-stone-500 font-mono">17 menciones</span>
          <div class="w-20 h-1.5 rounded-full bg-black/30 overflow-hidden">
            <div class="h-full rounded-full bg-rose-500 bar-anim" style="width:63%"></div>
          </div>
        </div>
        <div class="flex items-center gap-3">
          <span class="w-2 h-2 rounded-full bg-rose-400 flex-shrink-0"></span>
          <span class="text-sm text-stone-200 flex-1">"pedidos incorrectos"</span>
          <span class="text-xs text-stone-500 font-mono">12 menciones</span>
          <div class="w-20 h-1.5 rounded-full bg-black/30 overflow-hidden">
            <div class="h-full rounded-full bg-rose-500 bar-anim" style="width:44%"></div>
          </div>
        </div>
      </div>
    </div>

    <div class="space-y-2">
      <p class="text-xs text-stone-500 uppercase tracking-wider font-semibold mb-3">Acciones</p>
      <div class="flex items-start gap-3 p-3 rounded-xl bg-emerald-500/5 border border-emerald-500/15">
        <span class="text-emerald-400 mt-0.5">✓</span>
        <div>
          <p class="text-sm font-semibold text-stone-200">Calibrar temperatura de hornos y tiempo de empaquetado</p>
          <p class="text-xs text-stone-500 mt-0.5">Protocolo: máx. 3 min desde horno hasta entrega</p>
        </div>
      </div>
      <div class="flex items-start gap-3 p-3 rounded-xl bg-emerald-500/5 border border-emerald-500/15">
        <span class="text-emerald-400 mt-0.5">✓</span>
        <div>
          <p class="text-sm font-semibold text-stone-200">Implementar checklist de verificación de pedido antes de entrega</p>
          <p class="text-xs text-stone-500 mt-0.5">Reducción estimada de errores: 80% (benchmark red interna)</p>
        </div>
      </div>
    </div>
  </div>

  <!-- Positive reinforcement -->
  <div class="rounded-3xl border border-emerald-500/20 bg-emerald-950/20 p-6 mb-8">
    <h2 class="text-base font-semibold text-white mb-4">Aprender del #1: El Mar — Barceloneta</h2>
    <p class="text-stone-400 text-sm mb-4">
      El local con mejor nota de la red destaca consistentemente en 3 categorías.
      Exportar su protocolo a otros locales podría elevar la media de red hasta <strong class="text-white">4.5★</strong>.
    </p>
    <div class="grid grid-cols-1 sm:grid-cols-3 gap-3">
      <div class="rounded-2xl bg-black/15 border border-emerald-500/15 p-4 text-center">
        <p class="text-2xl mb-2">🐟</p>
        <p class="text-sm font-bold text-emerald-200">Frescura de producto</p>
        <p class="text-xs text-stone-400 mt-1">Mencionada en 89% de reseñas 5★</p>
      </div>
      <div class="rounded-2xl bg-black/15 border border-emerald-500/15 p-4 text-center">
        <p class="text-2xl mb-2">😊</p>
        <p class="text-sm font-bold text-emerald-200">Trato personalizado</p>
        <p class="text-xs text-stone-400 mt-1">73% menciona al personal por su nombre</p>
      </div>
      <div class="rounded-2xl bg-black/15 border border-emerald-500/15 p-4 text-center">
        <p class="text-2xl mb-2">⚡</p>
        <p class="text-sm font-bold text-emerald-200">Rapidez de servicio</p>
        <p class="text-xs text-stone-400 mt-1">Media de espera 4 min (red: 11 min)</p>
      </div>
    </div>
    <button class="mt-4 px-5 py-2.5 rounded-xl bg-emerald-600/30 border border-emerald-500/20
                   text-emerald-300 text-sm font-semibold hover:bg-emerald-600/50">
      📤 Exportar protocolo de Barceloneta a todos los locales
    </button>
  </div>

  <!-- Nav -->
  <div class="flex justify-between items-center">
    <a href="network_step3_benchmark.html"
       class="px-5 py-3 rounded-2xl border border-white/10 bg-white/5
              text-stone-300 font-semibold text-sm hover:bg-white/10 no-underline">
      ← Benchmarking
    </a>
    <a href="network_step5_report.html"
       class="px-8 py-3 rounded-2xl bg-gradient-to-r from-violet-600 to-indigo-600
              text-white font-bold text-sm hover:from-violet-500 hover:to-indigo-500 no-underline">
      Ver informe ejecutivo →
    </a>
  </div>
</div>"""
    return page("Paso 4 — Plan de Entrenamiento", "network_step4_training.html", body)


# ─── STEP 5 — Informe ejecutivo ──────────────────────────────────────────────

def step5_report() -> str:
    body = """
<div class="mx-auto max-w-4xl px-4 py-10 sm:px-6 pb-20 fade-up">

  <div class="mb-8">
    <p class="text-xs uppercase tracking-[.2em] text-violet-300/70 mb-1">Auditoría de Red · Informe Ejecutivo</p>
    <h1 class="text-3xl font-bold text-white">Informe de Auditoría — Abril 2026</h1>
    <p class="mt-1 text-stone-400 text-sm">
      Generado el <strong class="text-stone-200">30 Abr 2026 · 10:02</strong> · 50 locales · 4 tenants
    </p>
  </div>

  <!-- Executive banner -->
  <div class="rounded-3xl border border-violet-500/25
              bg-gradient-to-br from-violet-950/60 to-stone-900 p-8 mb-8">
    <div class="grid grid-cols-2 sm:grid-cols-4 gap-6 text-center">
      <div>
        <p class="text-4xl font-black text-emerald-300 mb-1">4.3★</p>
        <p class="text-xs uppercase tracking-wider text-stone-400">Nota media red</p>
        <p class="text-xs text-emerald-400 mt-1">▲ +0.1 vs. marzo</p>
      </div>
      <div>
        <p class="text-4xl font-black text-white mb-1">86%</p>
        <p class="text-xs uppercase tracking-wider text-stone-400">Locales saludables</p>
        <p class="text-xs text-stone-500 mt-1">≥ 4.0★</p>
      </div>
      <div>
        <p class="text-4xl font-black text-amber-300 mb-1">10%</p>
        <p class="text-xs uppercase tracking-wider text-stone-400">Con anomalía</p>
        <p class="text-xs text-amber-400 mt-1">5 locales</p>
      </div>
      <div>
        <p class="text-4xl font-black text-rose-300 mb-1">4%</p>
        <p class="text-xs uppercase tracking-wider text-stone-400">En crisis</p>
        <p class="text-xs text-rose-400 mt-1">2 locales</p>
      </div>
    </div>
  </div>

  <!-- Section: Highlights -->
  <div class="rounded-3xl border border-white/10 bg-white/5 p-6 mb-5">
    <h2 class="text-base font-semibold text-white mb-5">Highlights del mes</h2>
    <div class="space-y-4">

      <div class="flex items-start gap-4 p-4 rounded-2xl bg-emerald-500/5 border border-emerald-500/15">
        <span class="text-2xl flex-shrink-0">🏆</span>
        <div>
          <p class="text-sm font-bold text-emerald-200">El Mar — Barceloneta alcanza 4.8★ — mejor nota histórica de la red</p>
          <p class="text-xs text-stone-400 mt-1">Incremento de 0.3 puntos. Referente de buenas prácticas para toda la cadena.</p>
        </div>
      </div>

      <div class="flex items-start gap-4 p-4 rounded-2xl bg-amber-500/5 border border-amber-500/15">
        <span class="text-2xl flex-shrink-0">⚠️</span>
        <div>
          <p class="text-sm font-bold text-amber-200">Pizza Norte — Avellaneda cae 1.0★ en 30 días</p>
          <p class="text-xs text-stone-400 mt-1">Mayor anomalía de la red. Causa principal: temperatura de producto y errores en pedidos.</p>
        </div>
      </div>

      <div class="flex items-start gap-4 p-4 rounded-2xl bg-rose-500/5 border border-rose-500/15">
        <span class="text-2xl flex-shrink-0">🚨</span>
        <div>
          <p class="text-sm font-bold text-rose-200">2 crisis activas detectadas por IA — alertas enviadas en &lt; 1 min</p>
          <p class="text-xs text-stone-400 mt-1">El Mar — Sarrià (higiene) y Pizza Norte — Getafe Sur (fraude). SuperAdmin notificado.</p>
        </div>
      </div>

      <div class="flex items-start gap-4 p-4 rounded-2xl bg-violet-500/5 border border-violet-500/15">
        <span class="text-2xl flex-shrink-0">🤖</span>
        <div>
          <p class="text-sm font-bold text-violet-200">23 acciones de entrenamiento generadas para 7 locales</p>
          <p class="text-xs text-stone-400 mt-1">Mejora proyectada de +0.6★ en media de red si se implementan en 60 días.</p>
        </div>
      </div>

    </div>
  </div>

  <!-- Tenant breakdown -->
  <div class="rounded-3xl border border-white/10 bg-white/5 p-6 mb-5">
    <h2 class="text-base font-semibold text-white mb-5">Desglose por Tenant</h2>
    <div class="space-y-4">
      <div>
        <div class="flex justify-between text-sm mb-1.5">
          <span class="text-stone-200 font-semibold">Cadena Pizzas Norte</span>
          <span class="text-amber-300 font-bold">4.1★ · 1 crisis · 2 anomalías</span>
        </div>
        <div class="h-2.5 rounded-full bg-black/30 overflow-hidden">
          <div class="h-full rounded-full bar-anim" style="width:82%;background:linear-gradient(90deg,#10b981,#f59e0b)"></div>
        </div>
      </div>
      <div>
        <div class="flex justify-between text-sm mb-1.5">
          <span class="text-stone-200 font-semibold">Franquicia Café Rápido</span>
          <span class="text-emerald-300 font-bold">4.3★ · sin crisis · 2 anomalías</span>
        </div>
        <div class="h-2.5 rounded-full bg-black/30 overflow-hidden">
          <div class="h-full rounded-full bg-emerald-500 bar-anim" style="width:86%"></div>
        </div>
      </div>
      <div>
        <div class="flex justify-between text-sm mb-1.5">
          <span class="text-stone-200 font-semibold">Restaurantes El Mar</span>
          <span class="text-amber-300 font-bold">4.4★ · 1 crisis · 1 anomalía</span>
        </div>
        <div class="h-2.5 rounded-full bg-black/30 overflow-hidden">
          <div class="h-full rounded-full bar-anim" style="width:88%;background:linear-gradient(90deg,#10b981,#f59e0b)"></div>
        </div>
      </div>
      <div>
        <div class="flex justify-between text-sm mb-1.5">
          <span class="text-stone-200 font-semibold">Hoteles Solimar</span>
          <span class="text-emerald-300 font-bold">4.5★ · sin crisis · sin anomalías</span>
        </div>
        <div class="h-2.5 rounded-full bg-black/30 overflow-hidden">
          <div class="h-full rounded-full bg-emerald-500 bar-anim" style="width:90%"></div>
        </div>
      </div>
    </div>
  </div>

  <!-- Next steps -->
  <div class="rounded-3xl border border-indigo-500/20 bg-indigo-500/5 p-6 mb-8">
    <h2 class="text-base font-semibold text-white mb-4">Próximas acciones recomendadas</h2>
    <ol class="space-y-3">
      <li class="flex items-start gap-3">
        <span class="w-6 h-6 rounded-full bg-rose-500/30 text-rose-300 text-xs font-black flex items-center justify-center flex-shrink-0 mt-0.5">1</span>
        <p class="text-sm text-stone-300"><strong class="text-white">Resolver crisis activas</strong> en El Mar — Sarrià y Pizza Norte — Getafe Sur esta semana</p>
      </li>
      <li class="flex items-start gap-3">
        <span class="w-6 h-6 rounded-full bg-amber-500/30 text-amber-300 text-xs font-black flex items-center justify-center flex-shrink-0 mt-0.5">2</span>
        <p class="text-sm text-stone-300"><strong class="text-white">Iniciar plan de entrenamiento</strong> en los 7 locales identificados (mayo 2026)</p>
      </li>
      <li class="flex items-start gap-3">
        <span class="w-6 h-6 rounded-full bg-violet-500/30 text-violet-300 text-xs font-black flex items-center justify-center flex-shrink-0 mt-0.5">3</span>
        <p class="text-sm text-stone-300"><strong class="text-white">Exportar protocolo</strong> de El Mar — Barceloneta a los 5 locales con nota &lt; 4.0★</p>
      </li>
      <li class="flex items-start gap-3">
        <span class="w-6 h-6 rounded-full bg-indigo-500/30 text-indigo-300 text-xs font-black flex items-center justify-center flex-shrink-0 mt-0.5">4</span>
        <p class="text-sm text-stone-300"><strong class="text-white">Programar auditoría de seguimiento</strong> en 30 días para verificar mejoras</p>
      </li>
    </ol>
  </div>

  <!-- Actions -->
  <div class="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-8">
    <button class="px-5 py-3.5 rounded-2xl border border-white/10 bg-white/5
                   text-stone-300 font-semibold text-sm hover:bg-white/10 flex items-center justify-center gap-2">
      📥 Descargar PDF
    </button>
    <button class="px-5 py-3.5 rounded-2xl border border-white/10 bg-white/5
                   text-stone-300 font-semibold text-sm hover:bg-white/10 flex items-center justify-center gap-2">
      📧 Enviar a clientes
    </button>
    <a href="network_hub.html"
       class="px-5 py-3.5 rounded-2xl bg-gradient-to-r from-violet-600 to-indigo-600
              text-white font-bold text-sm hover:from-violet-500 hover:to-indigo-500
              no-underline flex items-center justify-center gap-2">
      ← Volver al Hub
    </a>
  </div>

</div>"""
    return page("Informe Ejecutivo — Red", "network_step5_report.html", body)


# ─── RENDER ──────────────────────────────────────────────────────────────────

def main() -> None:
    files = [
        ("network_hub.html",             network_hub()),
        ("network_step1_scan.html",      step1_scan()),
        ("network_step2_crisis.html",    step2_crisis()),
        ("network_step3_benchmark.html", step3_benchmark()),
        ("network_step4_training.html",  step4_training()),
        ("network_step5_report.html",    step5_report()),
    ]

    for fname, html in files:
        path = OUT_DIR / fname
        path.write_text(html, encoding="utf-8")
        print(f"✓ {path}")

    print("\n📌 Abriendo en el navegador:")
    for fname, _ in files:
        url = f"http://localhost:3000/enterprise/network/{fname}"
        webbrowser.open(url)
        print(f"   {url}")


if __name__ == "__main__":
    main()
