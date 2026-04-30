"""
Renderiza el Enterprise Dashboard Hub con los 3 features únicos:
  1. enterprise_hub.html       — Hub principal del dashboard Enterprise
  2. hub_heatmap.html          — Mapa de Calor Global (Green/Yellow/Red)
  3. hub_ranking.html          — Ranking de Sucursales (mejor/peor)
  4. hub_audit_log.html        — Log de Auditoría de Agencia
"""
from __future__ import annotations
import webbrowser
from pathlib import Path

ROOT = Path(__file__).parent
OUT_DIR = ROOT / "frontend" / "static" / "enterprise" / "hub"
OUT_DIR.mkdir(parents=True, exist_ok=True)

PAGES = [
    ("enterprise_hub.html", "🏢 Hub"),
    ("hub_heatmap.html",    "🗺️ Heat Map"),
    ("hub_ranking.html",    "🏆 Ranking"),
    ("hub_audit_log.html",  "📋 Auditoría"),
]


def nav_bar(active: str) -> str:
    links = ""
    for href, label in PAGES:
        # hub links back to enterprise landing
        real_href = f"../{href}" if href == "enterprise_hub.html" else href
        if href == active:
            cls = ("px-3 py-2 rounded-lg text-sm font-semibold text-violet-200 "
                   "bg-violet-500/20 border border-violet-400/20 no-underline")
        else:
            cls = ("px-3 py-2 rounded-lg text-sm font-medium text-stone-400 "
                   "hover:text-white hover:bg-white/5 no-underline")
        href_out = href if href != "enterprise_hub.html" else "../enterprise_hub.html"
        links += f'<a href="{href_out}" class="{cls}">{label}</a>\n'

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
    <span class="text-stone-400 text-xs font-semibold">Dashboard Hub</span>
  </div>
  {links}
</nav>"""


def page(title: str, active: str, body: str) -> str:
    return f"""<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{title} | Enterprise Hub · Lokigi</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <style>
    body {{ font-family: Arial, "Helvetica Neue", sans-serif; }}
    .no-underline {{ text-decoration: none; }}
    @keyframes fadeUp {{
      from {{ opacity: 0; transform: translateY(14px); }}
      to   {{ opacity: 1; transform: translateY(0); }}
    }}
    .fade-up {{ animation: fadeUp .35s ease both; }}
    @keyframes barIn {{
      from {{ width: 0; }}
    }}
    .bar-in {{ animation: barIn 1.2s cubic-bezier(.4,0,.2,1) both; }}
    @keyframes pulse-glow {{
      0%,100% {{ opacity: 1; box-shadow: 0 0 0 0 currentColor; }}
      50% {{ opacity: .7; }}
    }}
    .pulse {{ animation: pulse-glow 2s ease-in-out infinite; }}
    input, select, textarea {{
      background: rgba(255,255,255,.05);
      border: 1px solid rgba(255,255,255,.12);
      border-radius: 10px;
      color: #f1f5f9;
      padding: 9px 13px;
      font-size: 13px;
      outline: none;
    }}
    select option {{ background: #1c1917; }}
    /* heat dot */
    .dot-green  {{ background: #22c55e; box-shadow: 0 0 8px #22c55e88; }}
    .dot-yellow {{ background: #f59e0b; box-shadow: 0 0 8px #f59e0b88; }}
    .dot-red    {{ background: #ef4444; box-shadow: 0 0 8px #ef444488; }}
    /* table */
    table {{ border-collapse: collapse; width: 100%; }}
    thead th {{ font-size: 11px; text-transform: uppercase; letter-spacing: .06em;
                color: #78716c; padding: 8px 12px; text-align: left; font-weight: 600;
                border-bottom: 1px solid rgba(255,255,255,.08); }}
    tbody tr {{ border-bottom: 1px solid rgba(255,255,255,.04); }}
    tbody tr:hover {{ background: rgba(255,255,255,.025); }}
    tbody td {{ padding: 11px 12px; font-size: 13px; color: #d6d3d1; }}
  </style>
</head>
<body class="min-h-screen bg-stone-950 text-stone-100">
{nav_bar(active)}
{body}
</body>
</html>"""


# ─── ENTERPRISE HUB (landing) ─────────────────────────────────────────────────
# Note: this page lives at /enterprise/enterprise_hub.html, so nav links
# to ../enterprise_hub.html from sub-pages inside /hub/

def enterprise_hub() -> str:
    """Saved to frontend/static/enterprise/enterprise_hub.html (one level up)"""
    body = """
<div class="mx-auto max-w-6xl px-4 py-10 sm:px-6 pb-20 fade-up">

  <div class="flex items-start justify-between gap-4 mb-8 flex-wrap">
    <div>
      <p class="text-xs uppercase tracking-[.2em] text-violet-300/70 mb-1">Enterprise · Dashboard</p>
      <h1 class="text-3xl font-bold text-white">Dashboard Hub Enterprise</h1>
      <p class="mt-1 text-stone-400 text-sm max-w-2xl">
        Vista unificada de toda la red. Monitoriza decenas de locales en tiempo real,
        detecta outliers automáticamente y audita cada acción de la agencia.
      </p>
    </div>
    <div class="flex gap-3 flex-wrap">
      <a href="hub/hub_heatmap.html"
         class="px-5 py-2.5 rounded-2xl border border-white/10 bg-white/5
                text-stone-300 font-semibold text-sm hover:bg-white/10 no-underline">
        🗺️ Mapa de Calor
      </a>
      <a href="hub/hub_ranking.html"
         class="px-5 py-2.5 rounded-2xl border border-white/10 bg-white/5
                text-stone-300 font-semibold text-sm hover:bg-white/10 no-underline">
        🏆 Ranking
      </a>
      <a href="hub/hub_audit_log.html"
         class="px-5 py-2.5 rounded-2xl bg-gradient-to-r from-violet-600 to-indigo-600
                text-white font-bold text-sm hover:from-violet-500 hover:to-indigo-500 no-underline">
        📋 Auditoría →
      </a>
    </div>
  </div>

  <!-- Network KPIs -->
  <div class="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-8">
    <div class="rounded-2xl border border-violet-500/20 bg-violet-500/5 p-5 text-center">
      <p class="text-4xl font-black text-violet-300">50</p>
      <p class="text-xs uppercase tracking-wider text-stone-400 mt-1">Locales activos</p>
      <p class="text-xs text-stone-500 mt-1">4 tenants · 3 ciudades</p>
    </div>
    <div class="rounded-2xl border border-emerald-500/20 bg-emerald-500/5 p-5 text-center">
      <p class="text-4xl font-black text-emerald-300">87</p>
      <p class="text-xs uppercase tracking-wider text-stone-400 mt-1">Brand Authority</p>
      <p class="text-xs text-emerald-400 mt-1">▲ +6 pp vs. Q1</p>
    </div>
    <div class="rounded-2xl border border-rose-500/20 bg-rose-500/5 p-5 text-center">
      <p class="text-4xl font-black text-rose-300">3</p>
      <p class="text-xs uppercase tracking-wider text-stone-400 mt-1">Outliers activos</p>
      <p class="text-xs text-rose-400 mt-1">Requieren atención</p>
    </div>
    <div class="rounded-2xl border border-white/10 bg-white/5 p-5 text-center">
      <p class="text-4xl font-black text-white">4.3★</p>
      <p class="text-xs uppercase tracking-wider text-stone-400 mt-1">Nota media red</p>
      <p class="text-xs text-stone-500 mt-1">14.820 reseñas</p>
    </div>
  </div>

  <!-- Three feature cards -->
  <div class="grid grid-cols-1 sm:grid-cols-3 gap-5 mb-8">

    <!-- Heatmap card -->
    <a href="hub/hub_heatmap.html" class="no-underline group">
      <div class="rounded-3xl border border-white/10 bg-white/5 p-6
                  hover:border-violet-500/30 hover:bg-white/8 transition-all h-full">
        <div class="w-12 h-12 rounded-2xl bg-gradient-to-br from-emerald-500/30 to-violet-500/30
                    flex items-center justify-center text-2xl mb-4">🗺️</div>
        <h2 class="text-base font-bold text-white mb-2">Mapa de Calor Global</h2>
        <p class="text-stone-400 text-sm mb-4">
          Visualización de toda la red con semáforo de salud (🟢 🟡 🔴).
          Detecta problemas por ciudad, zona o franquicia en un solo vistazo.
        </p>
        <!-- Mini heatmap preview -->
        <div class="grid grid-cols-10 gap-1 mb-4">
          <!-- 50 dots: 38 green, 9 yellow, 3 red -->
          <div class="w-4 h-4 rounded-full dot-green"></div><div class="w-4 h-4 rounded-full dot-green"></div><div class="w-4 h-4 rounded-full dot-green"></div><div class="w-4 h-4 rounded-full dot-green"></div><div class="w-4 h-4 rounded-full dot-green"></div><div class="w-4 h-4 rounded-full dot-green"></div><div class="w-4 h-4 rounded-full dot-yellow"></div><div class="w-4 h-4 rounded-full dot-green"></div><div class="w-4 h-4 rounded-full dot-green"></div><div class="w-4 h-4 rounded-full dot-green"></div>
          <div class="w-4 h-4 rounded-full dot-green"></div><div class="w-4 h-4 rounded-full dot-green"></div><div class="w-4 h-4 rounded-full dot-red"></div><div class="w-4 h-4 rounded-full dot-green"></div><div class="w-4 h-4 rounded-full dot-green"></div><div class="w-4 h-4 rounded-full dot-green"></div><div class="w-4 h-4 rounded-full dot-yellow"></div><div class="w-4 h-4 rounded-full dot-green"></div><div class="w-4 h-4 rounded-full dot-green"></div><div class="w-4 h-4 rounded-full dot-green"></div>
          <div class="w-4 h-4 rounded-full dot-green"></div><div class="w-4 h-4 rounded-full dot-yellow"></div><div class="w-4 h-4 rounded-full dot-green"></div><div class="w-4 h-4 rounded-full dot-green"></div><div class="w-4 h-4 rounded-full dot-green"></div><div class="w-4 h-4 rounded-full dot-red"></div><div class="w-4 h-4 rounded-full dot-green"></div><div class="w-4 h-4 rounded-full dot-green"></div><div class="w-4 h-4 rounded-full dot-yellow"></div><div class="w-4 h-4 rounded-full dot-green"></div>
          <div class="w-4 h-4 rounded-full dot-green"></div><div class="w-4 h-4 rounded-full dot-green"></div><div class="w-4 h-4 rounded-full dot-green"></div><div class="w-4 h-4 rounded-full dot-yellow"></div><div class="w-4 h-4 rounded-full dot-green"></div><div class="w-4 h-4 rounded-full dot-green"></div><div class="w-4 h-4 rounded-full dot-green"></div><div class="w-4 h-4 rounded-full dot-red"></div><div class="w-4 h-4 rounded-full dot-green"></div><div class="w-4 h-4 rounded-full dot-green"></div>
          <div class="w-4 h-4 rounded-full dot-green"></div><div class="w-4 h-4 rounded-full dot-green"></div><div class="w-4 h-4 rounded-full dot-yellow"></div><div class="w-4 h-4 rounded-full dot-green"></div><div class="w-4 h-4 rounded-full dot-green"></div><div class="w-4 h-4 rounded-full dot-yellow"></div><div class="w-4 h-4 rounded-full dot-green"></div><div class="w-4 h-4 rounded-full dot-green"></div><div class="w-4 h-4 rounded-full dot-green"></div><div class="w-4 h-4 rounded-full dot-yellow"></div>
        </div>
        <div class="flex gap-4 text-xs text-stone-400">
          <span><span class="inline-block w-2 h-2 rounded-full bg-emerald-500 mr-1"></span>38 sanos</span>
          <span><span class="inline-block w-2 h-2 rounded-full bg-amber-500 mr-1"></span>9 alerta</span>
          <span><span class="inline-block w-2 h-2 rounded-full bg-rose-500 mr-1"></span>3 críticos</span>
        </div>
        <p class="text-xs text-violet-400 mt-4 group-hover:text-violet-300">Ver mapa completo →</p>
      </div>
    </a>

    <!-- Ranking card -->
    <a href="hub/hub_ranking.html" class="no-underline group">
      <div class="rounded-3xl border border-white/10 bg-white/5 p-6
                  hover:border-violet-500/30 hover:bg-white/8 transition-all h-full">
        <div class="w-12 h-12 rounded-2xl bg-gradient-to-br from-amber-500/30 to-indigo-500/30
                    flex items-center justify-center text-2xl mb-4">🏆</div>
        <h2 class="text-base font-bold text-white mb-2">Ranking de Sucursales</h2>
        <p class="text-stone-400 text-sm mb-4">
          Comparativa interna completa ordenada por Brand Authority Index.
          Identifica el top 5 y los 5 que necesitan plan de recuperación.
        </p>
        <div class="space-y-1.5 mb-4">
          <div class="flex items-center gap-2 text-xs">
            <span class="text-amber-400 font-black w-5 text-center">#1</span>
            <div class="flex-1 h-2.5 rounded-full bg-black/20 overflow-hidden">
              <div class="h-full rounded-full bg-gradient-to-r from-amber-400 to-amber-500 bar-in" style="width:92%"></div>
            </div>
            <span class="text-stone-300 font-semibold">92</span>
          </div>
          <div class="flex items-center gap-2 text-xs">
            <span class="text-stone-400 font-bold w-5 text-center">#2</span>
            <div class="flex-1 h-2.5 rounded-full bg-black/20 overflow-hidden">
              <div class="h-full rounded-full bg-emerald-500 bar-in" style="width:89%"></div>
            </div>
            <span class="text-stone-300 font-semibold">89</span>
          </div>
          <div class="flex items-center gap-2 text-xs">
            <span class="text-stone-400 font-bold w-5 text-center">#3</span>
            <div class="flex-1 h-2.5 rounded-full bg-black/20 overflow-hidden">
              <div class="h-full rounded-full bg-violet-500 bar-in" style="width:87%"></div>
            </div>
            <span class="text-stone-300 font-semibold">87</span>
          </div>
          <div class="text-xs text-stone-600 text-center">··· 44 locales más</div>
          <div class="flex items-center gap-2 text-xs">
            <span class="text-rose-400 font-bold w-5 text-center">#48</span>
            <div class="flex-1 h-2.5 rounded-full bg-black/20 overflow-hidden">
              <div class="h-full rounded-full bg-rose-500/60 bar-in" style="width:38%"></div>
            </div>
            <span class="text-rose-400 font-semibold">38</span>
          </div>
        </div>
        <p class="text-xs text-violet-400 mt-4 group-hover:text-violet-300">Ver ranking completo →</p>
      </div>
    </a>

    <!-- Audit log card -->
    <a href="hub/hub_audit_log.html" class="no-underline group">
      <div class="rounded-3xl border border-white/10 bg-white/5 p-6
                  hover:border-violet-500/30 hover:bg-white/8 transition-all h-full">
        <div class="w-12 h-12 rounded-2xl bg-gradient-to-br from-indigo-500/30 to-rose-500/20
                    flex items-center justify-center text-2xl mb-4">📋</div>
        <h2 class="text-base font-bold text-white mb-2">Control de Logs de Agencia</h2>
        <p class="text-stone-400 text-sm mb-4">
          Auditoría completa: quién respondió a qué reseña, en qué local,
          con qué tono, cuándo y si fue aprobada o rechazada.
        </p>
        <div class="space-y-2 font-mono text-xs mb-4">
          <div class="flex gap-2">
            <span class="text-stone-600 flex-shrink-0">09:14:22</span>
            <span class="text-emerald-400 flex-shrink-0">SENT</span>
            <span class="text-stone-400 truncate">Laura M. → Pizza Norte #3</span>
          </div>
          <div class="flex gap-2">
            <span class="text-stone-600 flex-shrink-0">09:12:05</span>
            <span class="text-amber-400 flex-shrink-0">EDIT</span>
            <span class="text-stone-400 truncate">Carlos R. → Café Rápido #7</span>
          </div>
          <div class="flex gap-2">
            <span class="text-stone-600 flex-shrink-0">09:08:47</span>
            <span class="text-violet-400 flex-shrink-0">AUTO</span>
            <span class="text-stone-400 truncate">IA → Hotel Solimar BCN</span>
          </div>
          <div class="flex gap-2">
            <span class="text-stone-600 flex-shrink-0">09:03:11</span>
            <span class="text-rose-400 flex-shrink-0">RJCT</span>
            <span class="text-stone-400 truncate">Ana G. rechazó → El Mar Sarrià</span>
          </div>
        </div>
        <p class="text-xs text-violet-400 mt-4 group-hover:text-violet-300">Ver log completo →</p>
      </div>
    </a>
  </div>

  <!-- Quick links to other Enterprise flows -->
  <div class="rounded-3xl border border-white/10 bg-white/5 p-6">
    <h2 class="text-sm font-bold text-stone-400 uppercase tracking-wider mb-4">Flujos Enterprise</h2>
    <div class="grid grid-cols-2 sm:grid-cols-4 gap-3">
      <a href="enterprise/enterprise_landing.html"
         class="rounded-2xl border border-white/8 bg-black/10 p-4 hover:bg-white/5 no-underline flex items-center gap-2">
        <span>🏷️</span><span class="text-sm text-stone-300 font-semibold">White Label</span>
      </a>
      <a href="enterprise/bulk/bulk_hub.html"
         class="rounded-2xl border border-white/8 bg-black/10 p-4 hover:bg-white/5 no-underline flex items-center gap-2">
        <span>📦</span><span class="text-sm text-stone-300 font-semibold">Bulk Publish</span>
      </a>
      <a href="enterprise/network/network_hub.html"
         class="rounded-2xl border border-white/8 bg-black/10 p-4 hover:bg-white/5 no-underline flex items-center gap-2">
        <span>🔍</span><span class="text-sm text-stone-300 font-semibold">Network Audit</span>
      </a>
      <a href="enterprise/reports/reports_hub.html"
         class="rounded-2xl border border-violet-500/20 bg-violet-500/5 p-4 hover:bg-violet-500/10 no-underline flex items-center gap-2">
        <span>📊</span><span class="text-sm text-violet-300 font-semibold">Exec Reports</span>
      </a>
    </div>
  </div>

</div>"""
    return page("Enterprise Dashboard Hub", "enterprise_hub.html", body)


# ─── HEAT MAP ─────────────────────────────────────────────────────────────────

# Location data for the grid (50 items)
LOCATIONS = [
    ("Pizza Norte — Alicante #1",     92, "green"),
    ("Hotel Solimar — BCN",           91, "green"),
    ("El Mar — Barceloneta",          90, "green"),
    ("Café Rápido — Málaga #1",       89, "green"),
    ("Pizza Norte — Valencia #1",     88, "green"),
    ("El Mar — Palma",                87, "green"),
    ("Hotel Solimar — Valencia",      87, "green"),
    ("Café Rápido — Madrid #1",       86, "green"),
    ("Pizza Norte — Murcia #1",       85, "green"),
    ("El Mar — Sitges",               85, "green"),
    ("Café Rápido — Sevilla #1",      84, "green"),
    ("Pizza Norte — Alicante #2",     84, "green"),
    ("Hotel Solimar — Tarragona",     83, "green"),
    ("El Mar — Alicante",             83, "green"),
    ("Pizza Norte — Valencia #2",     82, "green"),
    ("Café Rápido — Madrid #2",       82, "green"),
    ("Pizza Norte — Benidorm",        81, "green"),
    ("El Mar — Marbella",             81, "green"),
    ("Café Rápido — Málaga #2",       80, "green"),
    ("Hotel Solimar — Ibiza",         80, "green"),
    ("Pizza Norte — Murcia #2",       79, "green"),
    ("Café Rápido — Granada",         78, "green"),
    ("Pizza Norte — Elche",           78, "green"),
    ("El Mar — Torrevieja",           77, "green"),
    ("Café Rápido — Sevilla #2",      77, "green"),
    ("Pizza Norte — Almería",         76, "green"),
    ("Hotel Solimar — Costa Brava",   76, "green"),
    ("Pizza Norte — Cartagena",       75, "green"),
    ("Café Rápido — Zaragoza",        75, "green"),
    ("El Mar — Dénia",                74, "green"),
    ("Pizza Norte — Gandía",          73, "green"),
    ("Café Rápido — Bilbao",          72, "green"),
    ("Pizza Norte — Torrevieja",      71, "green"),
    ("El Mar — Fuengirola",           70, "green"),
    ("Pizza Norte — La Manga",        69, "yellow"),
    ("Café Rápido — Córdoba",         67, "yellow"),
    ("Pizza Norte — Elda",            65, "yellow"),
    ("El Mar — Cádiz",                64, "yellow"),
    ("Pizza Norte — Orihuela",        62, "yellow"),
    ("Café Rápido — Huelva",          61, "yellow"),
    ("Pizza Norte — Villena",         60, "yellow"),
    ("El Mar — Almería",              58, "yellow"),
    ("Café Rápido — Jaén",            57, "yellow"),
    ("Pizza Norte — Yecla",           54, "yellow"),
    ("El Mar — Motril",               52, "yellow"),
    ("Pizza Norte — Hellín",          49, "yellow"),
    ("Café Rápido — Linares",         45, "yellow"),
    ("El Mar — Sarrià",               40, "red"),
    ("Pizza Norte — Getafe Sur",      35, "red"),
    ("Café Rápido — Badajoz",         30, "red"),
]


def hub_heatmap() -> str:
    # Build grid cells
    cells = ""
    for name, bai, color in LOCATIONS:
        if color == "green":
            dot_cls = "dot-green"
            ring = "border-emerald-500/25 bg-emerald-500/5 hover:bg-emerald-500/10"
            text_cls = "text-emerald-300"
            badge = f'<span class="px-1.5 py-0.5 rounded-full bg-emerald-500/15 text-emerald-300 text-xs font-bold">{bai}</span>'
        elif color == "yellow":
            dot_cls = "dot-yellow"
            ring = "border-amber-500/25 bg-amber-500/5 hover:bg-amber-500/10"
            text_cls = "text-amber-300"
            badge = f'<span class="px-1.5 py-0.5 rounded-full bg-amber-500/15 text-amber-300 text-xs font-bold">{bai}</span>'
        else:
            dot_cls = "dot-red pulse"
            ring = "border-rose-500/35 bg-rose-500/8 hover:bg-rose-500/12"
            text_cls = "text-rose-300"
            badge = f'<span class="px-1.5 py-0.5 rounded-full bg-rose-500/15 text-rose-300 text-xs font-bold">{bai}</span>'

        cells += f"""
        <div class="rounded-2xl border {ring} p-3 flex items-center gap-2.5 cursor-pointer">
          <div class="w-3 h-3 rounded-full flex-shrink-0 {dot_cls}"></div>
          <div class="flex-1 min-w-0">
            <p class="text-xs font-semibold {text_cls} truncate">{name}</p>
          </div>
          {badge}
        </div>"""

    body = f"""
<div class="mx-auto max-w-6xl px-4 py-10 sm:px-6 pb-20 fade-up">

  <div class="mb-8">
    <p class="text-xs uppercase tracking-[.2em] text-violet-300/70 mb-1">Enterprise Hub · Mapa de Calor</p>
    <h1 class="text-3xl font-bold text-white">Mapa de Calor Global</h1>
    <p class="mt-1 text-stone-400 text-sm">
      Estado en tiempo real de los 50 locales de la red.
      Color determinado por el Brand Authority Index (IQR + umbrales dinámicos).
    </p>
  </div>

  <!-- Legend + filters -->
  <div class="flex items-center gap-6 mb-6 flex-wrap">
    <div class="flex items-center gap-2 text-sm font-semibold">
      <div class="w-3 h-3 rounded-full dot-green"></div>
      <span class="text-emerald-300">Sano (BAI ≥ 65)</span>
    </div>
    <div class="flex items-center gap-2 text-sm font-semibold">
      <div class="w-3 h-3 rounded-full dot-yellow"></div>
      <span class="text-amber-300">Alerta (BAI 45–64)</span>
    </div>
    <div class="flex items-center gap-2 text-sm font-semibold">
      <div class="w-3 h-3 rounded-full dot-red pulse"></div>
      <span class="text-rose-300">Crítico — Outlier (BAI &lt; 45)</span>
    </div>
    <div class="ml-auto flex gap-3">
      <select class="text-xs">
        <option selected>Todas las cadenas</option>
        <option>Pizza Norte (22 locales)</option>
        <option>Café Rápido (15 locales)</option>
        <option>El Mar (8 locales)</option>
        <option>Hotel Solimar (5 locales)</option>
      </select>
      <select class="text-xs">
        <option selected>Últimos 30 días</option>
        <option>Última semana</option>
        <option>Última hora</option>
      </select>
    </div>
  </div>

  <!-- KPI bar -->
  <div class="grid grid-cols-3 gap-4 mb-6">
    <div class="rounded-2xl border border-emerald-500/20 bg-emerald-500/5 p-4 text-center">
      <p class="text-3xl font-black text-emerald-300">34</p>
      <p class="text-xs uppercase tracking-wider text-stone-400 mt-1">🟢 Sanos</p>
    </div>
    <div class="rounded-2xl border border-amber-500/20 bg-amber-500/5 p-4 text-center">
      <p class="text-3xl font-black text-amber-300">13</p>
      <p class="text-xs uppercase tracking-wider text-stone-400 mt-1">🟡 En alerta</p>
    </div>
    <div class="rounded-2xl border border-rose-500/25 bg-rose-500/5 p-4 text-center">
      <p class="text-3xl font-black text-rose-300">3</p>
      <p class="text-xs uppercase tracking-wider text-stone-400 mt-1">🔴 Críticos</p>
    </div>
  </div>

  <!-- Heat grid -->
  <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-2 mb-8">
    {cells}
  </div>

  <!-- Outlier detail -->
  <div class="rounded-3xl border border-rose-500/25 bg-rose-950/20 p-6">
    <h2 class="text-base font-semibold text-rose-300 mb-4">🔴 Locales críticos — plan de acción</h2>
    <div class="space-y-3">
      <div class="flex items-center gap-4 p-4 rounded-2xl border border-rose-500/20 bg-black/15 flex-wrap">
        <div class="w-10 h-10 rounded-xl bg-rose-500/20 flex items-center justify-center font-black text-rose-300 flex-shrink-0">#48</div>
        <div class="flex-1 min-w-0">
          <p class="text-sm font-bold text-rose-200">El Mar — Sarrià</p>
          <p class="text-xs text-stone-500 mt-0.5">BAI 40 · Nota 2.8★ · Sentimiento 0.21 · Outlier: low_sentiment + low_rating</p>
        </div>
        <div class="flex gap-2">
          <span class="px-2 py-1 rounded-lg bg-rose-500/20 text-rose-300 text-xs font-bold">Respuesta urgente</span>
          <a href="../network/network_step3_action.html" class="px-3 py-1 rounded-lg bg-rose-600 text-white text-xs font-bold no-underline hover:bg-rose-500">Actuar →</a>
        </div>
      </div>
      <div class="flex items-center gap-4 p-4 rounded-2xl border border-rose-500/20 bg-black/15 flex-wrap">
        <div class="w-10 h-10 rounded-xl bg-rose-500/20 flex items-center justify-center font-black text-rose-300 flex-shrink-0">#49</div>
        <div class="flex-1 min-w-0">
          <p class="text-sm font-bold text-rose-200">Pizza Norte — Getafe Sur</p>
          <p class="text-xs text-stone-500 mt-0.5">BAI 35 · Nota 2.5★ · Sentimiento 0.18 · Outlier: low_rating</p>
        </div>
        <div class="flex gap-2">
          <span class="px-2 py-1 rounded-lg bg-rose-500/20 text-rose-300 text-xs font-bold">Plan de recuperación</span>
          <a href="../network/network_step3_action.html" class="px-3 py-1 rounded-lg bg-rose-600 text-white text-xs font-bold no-underline hover:bg-rose-500">Actuar →</a>
        </div>
      </div>
      <div class="flex items-center gap-4 p-4 rounded-2xl border border-rose-500/20 bg-black/15 flex-wrap">
        <div class="w-10 h-10 rounded-xl bg-rose-500/20 flex items-center justify-center font-black text-rose-300 flex-shrink-0">#50</div>
        <div class="flex-1 min-w-0">
          <p class="text-sm font-bold text-rose-200">Café Rápido — Badajoz</p>
          <p class="text-xs text-stone-500 mt-0.5">BAI 30 · Nota 2.2★ · Sentimiento 0.12 · Outlier: low_rating + low_sentiment</p>
        </div>
        <div class="flex gap-2">
          <span class="px-2 py-1 rounded-lg bg-rose-500/20 text-rose-300 text-xs font-bold">Auditoría urgente</span>
          <a href="../network/network_step3_action.html" class="px-3 py-1 rounded-lg bg-rose-600 text-white text-xs font-bold no-underline hover:bg-rose-500">Actuar →</a>
        </div>
      </div>
    </div>
  </div>

</div>"""
    return page("Mapa de Calor Global", "hub_heatmap.html", body)


# ─── RANKING ──────────────────────────────────────────────────────────────────

def hub_ranking() -> str:
    rows_html = ""
    for rank, (name, bai, color) in enumerate(LOCATIONS, 1):
        if color == "green":
            rank_cls = "text-emerald-300"
            bai_cls  = "text-emerald-300"
            trend    = "▲" if bai > 80 else "—"
            trend_cls = "text-emerald-400" if bai > 80 else "text-stone-500"
        elif color == "yellow":
            rank_cls = "text-amber-300"
            bai_cls  = "text-amber-300"
            trend    = "▼"
            trend_cls = "text-amber-400"
        else:
            rank_cls = "text-rose-300"
            bai_cls  = "text-rose-300"
            trend    = "▼▼"
            trend_cls = "text-rose-400"

        # derive fake values
        avg_rating = round(2.0 + (bai / 100) * 3.0, 1)
        reviews    = int(50 + (bai / 100) * 450)
        sentiment  = round(0.1 + (bai / 100) * 0.85, 2)

        bar_pct = bai
        bar_color = "bg-emerald-500" if color == "green" else ("bg-amber-500" if color == "yellow" else "bg-rose-500")

        rows_html += f"""
        <tr>
          <td class="font-black {rank_cls} text-center w-10">{rank}</td>
          <td class="font-semibold text-stone-200">{name}</td>
          <td class="text-center">{avg_rating}★</td>
          <td class="text-center">{reviews}</td>
          <td class="text-center">{sentiment}</td>
          <td>
            <div class="flex items-center gap-2">
              <div class="flex-1 h-2 rounded-full bg-black/30 overflow-hidden min-w-16">
                <div class="h-full rounded-full {bar_color} bar-in" style="width:{bar_pct}%"></div>
              </div>
              <span class="{bai_cls} font-black text-xs w-8">{bai}</span>
            </div>
          </td>
          <td class="text-center {trend_cls} font-bold text-sm">{trend}</td>
        </tr>"""

    body = f"""
<div class="mx-auto max-w-6xl px-4 py-10 sm:px-6 pb-20 fade-up">

  <div class="mb-8">
    <p class="text-xs uppercase tracking-[.2em] text-violet-300/70 mb-1">Enterprise Hub · Ranking</p>
    <h1 class="text-3xl font-bold text-white">Ranking de Sucursales</h1>
    <p class="mt-1 text-stone-400 text-sm">
      Comparativa interna completa ordenada por Brand Authority Index (BAI).
      Actualizada cada 5 min vía cache Redis + Celery beat.
    </p>
  </div>

  <!-- Controls -->
  <div class="flex flex-wrap gap-3 mb-6">
    <select class="text-xs"><option selected>Todas las cadenas</option><option>Pizza Norte</option><option>Café Rápido</option><option>El Mar</option><option>Hotel Solimar</option></select>
    <select class="text-xs"><option selected>Ordenar: Brand Authority ↓</option><option>Nota media ↓</option><option>Reseñas ↓</option><option>Sentimiento ↓</option></select>
    <select class="text-xs"><option selected>Últimos 30 días</option><option>Últimos 7 días</option><option>Este trimestre</option></select>
    <button class="px-4 py-2 rounded-xl border border-white/10 bg-white/5 text-stone-300 text-xs font-semibold hover:bg-white/10 ml-auto">
      📥 Exportar CSV
    </button>
  </div>

  <!-- Podium -->
  <div class="grid grid-cols-3 gap-4 mb-8">
    <div class="col-start-1 rounded-3xl border border-stone-500/30 bg-stone-500/5 p-5 text-center">
      <p class="text-xs text-stone-400 uppercase tracking-wider mb-1">#2</p>
      <p class="text-base font-bold text-stone-300">Hotel Solimar BCN</p>
      <p class="text-3xl font-black text-stone-300 mt-2">91</p>
      <p class="text-xs text-stone-500 mt-1">BAI · 4.5★</p>
    </div>
    <div class="rounded-3xl border border-amber-500/40 bg-amber-500/10 p-5 text-center relative">
      <div class="absolute -top-3 left-1/2 -translate-x-1/2 text-2xl">🏆</div>
      <p class="text-xs text-amber-300 uppercase tracking-wider font-bold mb-1">#1 — Campeón</p>
      <p class="text-base font-bold text-amber-200">Pizza Norte — Alicante #1</p>
      <p class="text-4xl font-black text-amber-300 mt-2">92</p>
      <p class="text-xs text-amber-400 mt-1">BAI · 4.6★ · ▲ +3 pp</p>
    </div>
    <div class="rounded-3xl border border-amber-900/30 bg-amber-900/5 p-5 text-center">
      <p class="text-xs text-stone-400 uppercase tracking-wider mb-1">#3</p>
      <p class="text-base font-bold text-stone-300">El Mar — Barceloneta</p>
      <p class="text-3xl font-black text-stone-300 mt-2">90</p>
      <p class="text-xs text-stone-500 mt-1">BAI · 4.8★ — Récord histórico</p>
    </div>
  </div>

  <!-- Full table -->
  <div class="rounded-3xl border border-white/10 bg-white/5 overflow-hidden">
    <div class="p-4 border-b border-white/10">
      <p class="text-sm font-semibold text-white">Tabla completa — 50 locales</p>
    </div>
    <div class="overflow-x-auto">
      <table>
        <thead>
          <tr>
            <th class="text-center">#</th>
            <th>Local</th>
            <th class="text-center">Nota</th>
            <th class="text-center">Reseñas</th>
            <th class="text-center">Sentim.</th>
            <th>Brand Authority</th>
            <th class="text-center">Tendencia</th>
          </tr>
        </thead>
        <tbody>
          {rows_html}
        </tbody>
      </table>
    </div>
  </div>

  <!-- Bottom action -->
  <div class="mt-6 flex justify-end">
    <a href="../reports/reports_hub.html"
       class="px-6 py-3 rounded-2xl bg-gradient-to-r from-violet-600 to-indigo-600
              text-white font-bold text-sm hover:from-violet-500 hover:to-indigo-500 no-underline">
      📊 Generar informe ejecutivo →
    </a>
  </div>

</div>"""
    return page("Ranking de Sucursales", "hub_ranking.html", body)


# ─── AUDIT LOG ────────────────────────────────────────────────────────────────

AUDIT_ENTRIES = [
    ("30 Abr 09:14:22", "SENT",  "Laura Martínez",  "Pizza Norte — Alicante #1", "3★ — 'Servicio mejorable'",    "Positivo", "Auto-aprobado", "reseña atendida en 48h"),
    ("30 Abr 09:12:05", "EDIT",  "Carlos Rodríguez","Café Rápido — Madrid #1",   "1★ — 'Nunca más'",             "Empático",  "Edición manual",  "tono revisado por manager"),
    ("30 Abr 09:10:41", "AUTO",  "IA Lokigi",        "Hotel Solimar — BCN",       "5★ — 'Excelente estancia'",   "Cálido",   "Auto-enviado",    "respuesta positiva automática"),
    ("30 Abr 09:08:47", "AUTO",  "IA Lokigi",        "El Mar — Barceloneta",      "4★ — 'Muy buena comida'",     "Agradecido","Auto-enviado",    "respuesta estándar"),
    ("30 Abr 09:03:11", "RJCT",  "Ana García",       "El Mar — Sarrià",           "1★ — 'Pésima atención'",      "—",         "Rechazada",       "escala a manager de zona"),
    ("30 Abr 08:55:33", "SENT",  "Pedro Sánchez",    "Pizza Norte — Valencia #1", "2★ — 'Demasiado lento'",      "Empático",  "Aprobado manual", "cliente contactado offline"),
    ("30 Abr 08:44:17", "AUTO",  "IA Lokigi",        "Café Rápido — Sevilla #1",  "5★ — 'Increíble'",            "Cálido",   "Auto-enviado",    "respuesta en < 1 min"),
    ("30 Abr 08:39:02", "EDIT",  "Laura Martínez",   "Hotel Solimar — Valencia",  "3★ — 'Habitación pequeña'",   "Profesional","Edición manual", "ajustado a reclamación"),
    ("30 Abr 08:22:55", "SENT",  "Carlos Rodríguez", "El Mar — Palma",            "4★ — 'Buena terraza'",        "Agradecido","Auto-aprobado",   ""),
    ("30 Abr 08:11:09", "RJCT",  "Ana García",       "Pizza Norte — Getafe Sur",  "1★ — 'Suciedad'",             "—",         "Rechazada",       "abierta incidencia interna"),
    ("30 Abr 07:58:44", "SENT",  "IA Lokigi",        "Café Rápido — Granada",     "5★ — 'Rápido y rico'",        "Cálido",   "Auto-enviado",    ""),
    ("30 Abr 07:43:21", "EDIT",  "Pedro Sánchez",    "Pizza Norte — Murcia #1",   "2★ — 'Pedido incorrecto'",    "Disculpa",  "Aprobado manual", "reposición ofrecida"),
]


def hub_audit_log() -> str:
    def badge(action: str) -> str:
        configs = {
            "SENT": ("bg-emerald-500/15 text-emerald-300", "✓ Enviado"),
            "EDIT": ("bg-amber-500/15 text-amber-300",     "✏️ Editado"),
            "AUTO": ("bg-violet-500/15 text-violet-300",   "🤖 Auto"),
            "RJCT": ("bg-rose-500/15 text-rose-300",       "✗ Rechazado"),
        }
        cls, label = configs.get(action, ("bg-stone-500/15 text-stone-400", action))
        return f'<span class="px-2 py-0.5 rounded-full {cls} text-xs font-bold whitespace-nowrap">{label}</span>'

    rows = ""
    for ts, action, agent, location, review, tone, approval, note in AUDIT_ENTRIES:
        rows += f"""
        <tr>
          <td class="font-mono text-xs text-stone-500 whitespace-nowrap">{ts}</td>
          <td>{badge(action)}</td>
          <td class="font-semibold text-stone-200 text-xs">{agent}</td>
          <td class="text-stone-400 text-xs">{location}</td>
          <td class="text-stone-500 text-xs max-w-xs truncate" title="{review}">{review}</td>
          <td class="text-xs">
            <span class="px-2 py-0.5 rounded-full bg-white/8 text-stone-300 text-xs">{tone}</span>
          </td>
          <td class="text-xs text-stone-400">{approval}</td>
          <td class="text-xs text-stone-600 italic">{note}</td>
        </tr>"""

    body = f"""
<div class="mx-auto max-w-7xl px-4 py-10 sm:px-6 pb-20 fade-up">

  <div class="mb-8">
    <p class="text-xs uppercase tracking-[.2em] text-violet-300/70 mb-1">Enterprise Hub · Auditoría</p>
    <h1 class="text-3xl font-bold text-white">Control de Logs de Agencia</h1>
    <p class="mt-1 text-stone-400 text-sm max-w-2xl">
      Registro inmutable de cada acción realizada sobre las reseñas: quién respondió,
      en qué local, con qué tono, si fue aprobada, rechazada o automática.
      Base para compliance y control de calidad de la agencia.
    </p>
  </div>

  <!-- Audit KPIs -->
  <div class="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-6">
    <div class="rounded-2xl border border-emerald-500/20 bg-emerald-500/5 p-4 text-center">
      <p class="text-3xl font-black text-emerald-300">1.247</p>
      <p class="text-xs uppercase tracking-wider text-stone-400 mt-1">Acciones este mes</p>
    </div>
    <div class="rounded-2xl border border-violet-500/20 bg-violet-500/5 p-4 text-center">
      <p class="text-3xl font-black text-violet-300">68%</p>
      <p class="text-xs uppercase tracking-wider text-stone-400 mt-1">Auto-enviadas (IA)</p>
    </div>
    <div class="rounded-2xl border border-amber-500/20 bg-amber-500/5 p-4 text-center">
      <p class="text-3xl font-black text-amber-300">29%</p>
      <p class="text-xs uppercase tracking-wider text-stone-400 mt-1">Editadas manualmente</p>
    </div>
    <div class="rounded-2xl border border-rose-500/20 bg-rose-500/5 p-4 text-center">
      <p class="text-3xl font-black text-rose-300">3%</p>
      <p class="text-xs uppercase tracking-wider text-stone-400 mt-1">Rechazadas</p>
    </div>
  </div>

  <!-- Filters -->
  <div class="flex flex-wrap gap-3 mb-4">
    <select class="text-xs"><option selected>Todos los agentes</option><option>Laura Martínez</option><option>Carlos Rodríguez</option><option>Ana García</option><option>Pedro Sánchez</option><option>IA Lokigi</option></select>
    <select class="text-xs"><option selected>Todas las acciones</option><option>Solo SENT</option><option>Solo AUTO</option><option>Solo EDIT</option><option>Solo RJCT</option></select>
    <select class="text-xs"><option selected>Todos los locales</option><option>Pizza Norte</option><option>Café Rápido</option><option>El Mar</option><option>Hotel Solimar</option></select>
    <select class="text-xs"><option selected>Hoy</option><option>Últimas 7 días</option><option>Este mes</option></select>
    <button class="px-4 py-2 rounded-xl border border-white/10 bg-white/5 text-stone-300 text-xs font-semibold hover:bg-white/10 ml-auto">
      📥 Exportar CSV
    </button>
  </div>

  <!-- Agent activity summary -->
  <div class="rounded-3xl border border-white/10 bg-white/5 p-5 mb-6">
    <h2 class="text-sm font-bold text-stone-300 uppercase tracking-wider mb-4">Actividad por agente — hoy</h2>
    <div class="grid grid-cols-2 sm:grid-cols-5 gap-3">
      <div class="rounded-2xl bg-black/15 border border-white/8 p-3 text-center">
        <div class="w-8 h-8 rounded-full bg-violet-500/30 flex items-center justify-center text-xs font-bold text-violet-300 mx-auto mb-2">IA</div>
        <p class="text-xl font-black text-violet-300">847</p>
        <p class="text-xs text-stone-500 mt-0.5">IA Lokigi</p>
      </div>
      <div class="rounded-2xl bg-black/15 border border-white/8 p-3 text-center">
        <div class="w-8 h-8 rounded-full bg-emerald-500/30 flex items-center justify-center text-xs font-bold text-emerald-300 mx-auto mb-2">LM</div>
        <p class="text-xl font-black text-emerald-300">184</p>
        <p class="text-xs text-stone-500 mt-0.5">Laura M.</p>
      </div>
      <div class="rounded-2xl bg-black/15 border border-white/8 p-3 text-center">
        <div class="w-8 h-8 rounded-full bg-indigo-500/30 flex items-center justify-center text-xs font-bold text-indigo-300 mx-auto mb-2">CR</div>
        <p class="text-xl font-black text-indigo-300">112</p>
        <p class="text-xs text-stone-500 mt-0.5">Carlos R.</p>
      </div>
      <div class="rounded-2xl bg-black/15 border border-white/8 p-3 text-center">
        <div class="w-8 h-8 rounded-full bg-amber-500/30 flex items-center justify-center text-xs font-bold text-amber-300 mx-auto mb-2">PS</div>
        <p class="text-xl font-black text-amber-300">68</p>
        <p class="text-xs text-stone-500 mt-0.5">Pedro S.</p>
      </div>
      <div class="rounded-2xl bg-black/15 border border-white/8 p-3 text-center">
        <div class="w-8 h-8 rounded-full bg-rose-500/30 flex items-center justify-center text-xs font-bold text-rose-300 mx-auto mb-2">AG</div>
        <p class="text-xl font-black text-rose-300">36</p>
        <p class="text-xs text-stone-500 mt-0.5">Ana G.</p>
      </div>
    </div>
  </div>

  <!-- Log table -->
  <div class="rounded-3xl border border-white/10 bg-white/5 overflow-hidden">
    <div class="flex items-center justify-between p-4 border-b border-white/10">
      <p class="text-sm font-semibold text-white">Log de auditoría — 30 Abr 2026</p>
      <span class="text-xs text-stone-500">Mostrando 12 de 1.247 entradas</span>
    </div>
    <div class="overflow-x-auto">
      <table>
        <thead>
          <tr>
            <th>Timestamp</th>
            <th>Acción</th>
            <th>Agente</th>
            <th>Local</th>
            <th>Reseña</th>
            <th>Tono</th>
            <th>Aprobación</th>
            <th>Nota</th>
          </tr>
        </thead>
        <tbody>
          {rows}
        </tbody>
      </table>
    </div>
    <div class="p-4 border-t border-white/10 text-center">
      <button class="px-5 py-2 rounded-xl border border-white/10 bg-white/5 text-stone-400 text-xs font-semibold hover:bg-white/8">
        Cargar más entradas ↓
      </button>
    </div>
  </div>

</div>"""
    return page("Control de Logs de Agencia", "hub_audit_log.html", body)


# ─── RENDER ───────────────────────────────────────────────────────────────────

def main() -> None:
    # Enterprise Hub lives one level up from /hub/
    hub_dir = ROOT / "frontend" / "static" / "enterprise"
    hub_path = hub_dir / "enterprise_hub.html"
    hub_html = enterprise_hub()
    hub_path.write_text(hub_html, encoding="utf-8")
    print(f"✓ {hub_path}")

    sub_files = [
        ("hub_heatmap.html",  hub_heatmap()),
        ("hub_ranking.html",  hub_ranking()),
        ("hub_audit_log.html", hub_audit_log()),
    ]

    for fname, html in sub_files:
        path = OUT_DIR / fname
        path.write_text(html, encoding="utf-8")
        print(f"✓ {path}")

    print("\n📌 Abriendo en el navegador:")
    urls = [
        "http://localhost:3000/enterprise/enterprise_hub.html",
        "http://localhost:3000/enterprise/hub/hub_heatmap.html",
        "http://localhost:3000/enterprise/hub/hub_ranking.html",
        "http://localhost:3000/enterprise/hub/hub_audit_log.html",
    ]
    for url in urls:
        webbrowser.open(url)
        print(f"   {url}")


if __name__ == "__main__":
    main()
