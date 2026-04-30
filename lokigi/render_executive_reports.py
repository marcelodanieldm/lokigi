"""
Renderiza el flujo "Reportes Ejecutivos Consolidados" del Plan Enterprise
como páginas HTML estáticas en frontend/static/enterprise/reports/

Páginas del flujo:
  1. reports_hub.html         — Hub: informes programados, estado de generación, últimas entregas
  2. reports_step1_agg.html   — Agregación Multi-Ubicación: pipeline Python/Pandas, métricas consolidadas de 100+ locales
  3. reports_step2_roi.html   — ROI de Marca: Brand Authority Index, crecimiento regional vs. competencia
  4. reports_step3_compose.html — Composición del Informe: secciones, branding agencia, portada personalizada
  5. reports_step4_preview.html — Preview PDF: miniatura del documento antes de enviar
  6. reports_step5_send.html  — Automatización de Envío: remitente agencia, lista de distribución, historial
"""
from __future__ import annotations
import webbrowser
from pathlib import Path

ROOT = Path(__file__).parent
OUT_DIR = ROOT / "frontend" / "static" / "enterprise" / "reports"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# ─── NAV ─────────────────────────────────────────────────────────────────────

PAGES = [
    ("reports_hub.html",          "📊 Hub"),
    ("reports_step1_agg.html",    "1 · Agregación"),
    ("reports_step2_roi.html",    "2 · ROI Marca"),
    ("reports_step3_compose.html","3 · Composición"),
    ("reports_step4_preview.html","4 · Preview"),
    ("reports_step5_send.html",   "5 · Envío"),
]


def nav_bar(active: str) -> str:
    links = ""
    for href, label in PAGES:
        is_active = href == active
        if is_active:
            cls = ("px-3 py-2 rounded-lg text-sm font-semibold text-violet-200 "
                   "bg-violet-500/20 border border-violet-400/20 no-underline")
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
    <span class="text-stone-400 text-xs font-semibold">Reportes Ejecutivos</span>
  </div>
  {links}
</nav>"""


def page(title: str, active: str, body: str) -> str:
    return f"""<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{title} | Reportes Ejecutivos · Lokigi Enterprise</title>
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
    @keyframes spin {{
      to {{ transform: rotate(360deg); }}
    }}
    .spin {{ animation: spin 1s linear infinite; }}
    @keyframes pulse-glow {{
      0%,100% {{ opacity: 1; }}
      50% {{ opacity: .45; }}
    }}
    .pulse-glow {{ animation: pulse-glow 2s ease-in-out infinite; }}
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
    /* PDF preview simulation */
    .pdf-page {{
      background: #fff;
      color: #111;
      border-radius: 12px;
      padding: 32px 36px;
      box-shadow: 0 20px 60px rgba(0,0,0,.6);
      max-width: 520px;
      margin: 0 auto;
    }}
    .pdf-page h1 {{ font-size: 20px; font-weight: 900; color: #111; margin: 0 0 4px; }}
    .pdf-page h2 {{ font-size: 13px; font-weight: 700; color: #444; margin: 16px 0 6px; border-bottom: 1px solid #e5e7eb; padding-bottom: 4px; }}
    .pdf-page p, .pdf-page li {{ font-size: 11px; color: #374151; line-height: 1.6; margin: 0; }}
    .pdf-page .kpi-row {{ display: flex; gap: 12px; margin: 10px 0; }}
    .pdf-page .kpi-box {{ flex: 1; background: #f3f4f6; border-radius: 8px; padding: 8px; text-align: center; }}
    .pdf-page .kpi-box strong {{ font-size: 18px; font-weight: 900; display: block; color: #111; }}
    .pdf-page .kpi-box span {{ font-size: 9px; color: #6b7280; text-transform: uppercase; letter-spacing: .05em; }}
    .pdf-page .bar-row {{ display: flex; align-items: center; gap: 8px; margin-bottom: 6px; }}
    .pdf-page .bar-label {{ width: 130px; font-size: 10px; color: #374151; flex-shrink: 0; text-align: right; }}
    .pdf-page .bar-track {{ flex: 1; height: 8px; background: #e5e7eb; border-radius: 4px; overflow: hidden; }}
    .pdf-page .bar-fill {{ height: 100%; background: #7c3aed; border-radius: 4px; }}
    .pdf-page .bar-val {{ font-size: 10px; font-weight: 700; color: #111; width: 32px; }}
    .pdf-page footer {{ margin-top: 20px; padding-top: 10px; border-top: 1px solid #e5e7eb; font-size: 9px; color: #9ca3af; text-align: center; }}
  </style>
</head>
<body class="min-h-screen bg-stone-950 text-stone-100">
{nav_bar(active)}
{body}
</body>
</html>"""


# ─── HUB ─────────────────────────────────────────────────────────────────────

def reports_hub() -> str:
    body = """
<div class="mx-auto max-w-5xl px-4 py-10 sm:px-6 pb-20 fade-up">

  <!-- Header -->
  <div class="flex items-start justify-between gap-4 mb-8 flex-wrap">
    <div>
      <p class="text-xs uppercase tracking-[.2em] text-violet-300/70 mb-1">Enterprise · Reportes Ejecutivos</p>
      <h1 class="text-3xl font-bold text-white">Hub de Reportes Consolidados</h1>
      <p class="mt-1 text-stone-400 text-sm max-w-xl">
        Genera informes de alta dirección que consolidan métricas de cientos de locales.
        Mide la Autoridad de Marca en toda la región y entrégalos automáticamente con el branding de tu agencia.
      </p>
    </div>
    <div class="flex gap-3">
      <a href="reports_step1_agg.html"
         class="px-5 py-2.5 rounded-2xl border border-white/10 bg-white/5
                text-stone-300 font-semibold text-sm hover:bg-white/10 no-underline">
        Nuevo informe
      </a>
      <a href="reports_step5_send.html"
         class="px-5 py-2.5 rounded-2xl bg-gradient-to-r from-violet-600 to-indigo-600
                text-white font-bold text-sm hover:from-violet-500 hover:to-indigo-500 no-underline">
        Configurar envíos →
      </a>
    </div>
  </div>

  <!-- KPIs -->
  <div class="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-8">
    <div class="rounded-2xl border border-violet-500/20 bg-violet-500/5 p-5 text-center">
      <p class="text-4xl font-black text-violet-300">12</p>
      <p class="text-xs uppercase tracking-wider text-stone-400 mt-1">Informes este mes</p>
      <p class="text-xs text-violet-400 mt-1">▲ +4 vs. marzo</p>
    </div>
    <div class="rounded-2xl border border-emerald-500/20 bg-emerald-500/5 p-5 text-center">
      <p class="text-4xl font-black text-emerald-300">4</p>
      <p class="text-xs uppercase tracking-wider text-stone-400 mt-1">Tenants cubiertos</p>
      <p class="text-xs text-stone-500 mt-1">50 locales consolidados</p>
    </div>
    <div class="rounded-2xl border border-indigo-500/20 bg-indigo-500/5 p-5 text-center">
      <p class="text-4xl font-black text-indigo-300">87%</p>
      <p class="text-xs uppercase tracking-wider text-stone-400 mt-1">Brand Authority</p>
      <p class="text-xs text-emerald-400 mt-1">▲ +6 pp vs. Q1</p>
    </div>
    <div class="rounded-2xl border border-white/10 bg-white/5 p-5 text-center">
      <p class="text-4xl font-black text-white">98%</p>
      <p class="text-xs uppercase tracking-wider text-stone-400 mt-1">Tasa de apertura</p>
      <p class="text-xs text-stone-500 mt-1">Emails de informe</p>
    </div>
  </div>

  <!-- Scheduled reports -->
  <div class="rounded-3xl border border-white/10 bg-white/5 p-6 mb-6">
    <div class="flex items-center justify-between mb-5">
      <h2 class="text-base font-semibold text-white m-0">Informes programados</h2>
      <button class="px-4 py-2 rounded-xl bg-violet-500/20 text-violet-300 text-xs font-bold hover:bg-violet-500/30">
        + Añadir programa
      </button>
    </div>
    <div class="space-y-3">
      <!-- Scheduled 1 -->
      <div class="flex items-center gap-4 p-4 rounded-2xl border border-white/8 bg-black/10 flex-wrap">
        <div class="w-10 h-10 rounded-xl bg-emerald-500/20 flex items-center justify-center text-xl flex-shrink-0">📅</div>
        <div class="flex-1 min-w-0">
          <p class="text-sm font-bold text-white">Informe Mensual — Cadena Completa</p>
          <p class="text-xs text-stone-500 mt-0.5">Cada 1° del mes · 09:00 h · Destinatarios: 8 directivos</p>
        </div>
        <div class="flex items-center gap-2">
          <span class="w-2 h-2 rounded-full bg-emerald-400 pulse-glow"></span>
          <span class="text-xs font-semibold text-emerald-300">Activo</span>
        </div>
        <span class="text-xs text-stone-500">Próximo: 1 May 09:00</span>
      </div>
      <!-- Scheduled 2 -->
      <div class="flex items-center gap-4 p-4 rounded-2xl border border-white/8 bg-black/10 flex-wrap">
        <div class="w-10 h-10 rounded-xl bg-indigo-500/20 flex items-center justify-center text-xl flex-shrink-0">📅</div>
        <div class="flex-1 min-w-0">
          <p class="text-sm font-bold text-white">Informe Semanal — Alertas y KPIs</p>
          <p class="text-xs text-stone-500 mt-0.5">Cada lunes · 08:00 h · Destinatarios: 4 managers</p>
        </div>
        <div class="flex items-center gap-2">
          <span class="w-2 h-2 rounded-full bg-emerald-400 pulse-glow"></span>
          <span class="text-xs font-semibold text-emerald-300">Activo</span>
        </div>
        <span class="text-xs text-stone-500">Próximo: Lun 4 May</span>
      </div>
      <!-- Scheduled 3 -->
      <div class="flex items-center gap-4 p-4 rounded-2xl border border-white/8 bg-black/10 flex-wrap">
        <div class="w-10 h-10 rounded-xl bg-amber-500/20 flex items-center justify-center text-xl flex-shrink-0">📅</div>
        <div class="flex-1 min-w-0">
          <p class="text-sm font-bold text-white">Informe Trimestral — ROI de Marca</p>
          <p class="text-xs text-stone-500 mt-0.5">Cada 3 meses · Destinatarios: Comité directivo (12 personas)</p>
        </div>
        <div class="flex items-center gap-2">
          <span class="w-2 h-2 rounded-full bg-amber-400"></span>
          <span class="text-xs font-semibold text-amber-300">Pausado</span>
        </div>
        <span class="text-xs text-stone-500">Último: 31 Mar</span>
      </div>
    </div>
  </div>

  <!-- Recent deliveries -->
  <div class="rounded-3xl border border-white/10 bg-white/5 p-6 mb-6">
    <h2 class="text-base font-semibold text-white mb-5">Últimas entregas</h2>
    <div class="overflow-x-auto">
      <table class="min-w-full text-sm">
        <thead>
          <tr class="text-stone-400 text-xs uppercase tracking-wider border-b border-white/10">
            <th class="py-2 pr-4 text-left font-semibold">Informe</th>
            <th class="py-2 pr-4 text-left font-semibold">Fecha envío</th>
            <th class="py-2 pr-4 text-left font-semibold">Destinatarios</th>
            <th class="py-2 pr-4 text-center font-semibold">Aperturas</th>
            <th class="py-2 pr-4 text-center font-semibold">Estado</th>
            <th class="py-2 text-left font-semibold"></th>
          </tr>
        </thead>
        <tbody>
          <tr class="border-b border-white/5 hover:bg-white/3">
            <td class="py-3 pr-4 text-stone-200 font-semibold">Mensual Abril 2026</td>
            <td class="py-3 pr-4 text-stone-400">30 Abr · 09:01</td>
            <td class="py-3 pr-4 text-stone-400">8 destinatarios</td>
            <td class="py-3 pr-4 text-center text-emerald-300 font-bold">8/8</td>
            <td class="py-3 pr-4 text-center"><span class="px-2 py-0.5 rounded-full bg-emerald-500/15 text-emerald-300 text-xs font-bold">✓ Entregado</span></td>
            <td class="py-3"><a href="reports_step4_preview.html" class="text-xs text-stone-500 hover:text-stone-300 no-underline">Ver PDF →</a></td>
          </tr>
          <tr class="border-b border-white/5 hover:bg-white/3">
            <td class="py-3 pr-4 text-stone-200 font-semibold">Semanal 28 Abr</td>
            <td class="py-3 pr-4 text-stone-400">28 Abr · 08:00</td>
            <td class="py-3 pr-4 text-stone-400">4 managers</td>
            <td class="py-3 pr-4 text-center text-emerald-300 font-bold">4/4</td>
            <td class="py-3 pr-4 text-center"><span class="px-2 py-0.5 rounded-full bg-emerald-500/15 text-emerald-300 text-xs font-bold">✓ Entregado</span></td>
            <td class="py-3"><a href="reports_step4_preview.html" class="text-xs text-stone-500 hover:text-stone-300 no-underline">Ver PDF →</a></td>
          </tr>
          <tr class="border-b border-white/5 hover:bg-white/3">
            <td class="py-3 pr-4 text-stone-200 font-semibold">Mensual Marzo 2026</td>
            <td class="py-3 pr-4 text-stone-400">1 Abr · 09:00</td>
            <td class="py-3 pr-4 text-stone-400">8 destinatarios</td>
            <td class="py-3 pr-4 text-center text-emerald-300 font-bold">7/8</td>
            <td class="py-3 pr-4 text-center"><span class="px-2 py-0.5 rounded-full bg-emerald-500/15 text-emerald-300 text-xs font-bold">✓ Entregado</span></td>
            <td class="py-3"><a href="reports_step4_preview.html" class="text-xs text-stone-500 hover:text-stone-300 no-underline">Ver PDF →</a></td>
          </tr>
          <tr class="hover:bg-white/3">
            <td class="py-3 pr-4 text-stone-200 font-semibold">Trimestral Q1 2026</td>
            <td class="py-3 pr-4 text-stone-400">31 Mar · 10:15</td>
            <td class="py-3 pr-4 text-stone-400">12 directivos</td>
            <td class="py-3 pr-4 text-center text-emerald-300 font-bold">11/12</td>
            <td class="py-3 pr-4 text-center"><span class="px-2 py-0.5 rounded-full bg-emerald-500/15 text-emerald-300 text-xs font-bold">✓ Entregado</span></td>
            <td class="py-3"><a href="reports_step4_preview.html" class="text-xs text-stone-500 hover:text-stone-300 no-underline">Ver PDF →</a></td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>

  <!-- Quick actions -->
  <div class="grid grid-cols-1 sm:grid-cols-4 gap-4">
    <a href="reports_step1_agg.html"
       class="rounded-2xl border border-white/10 bg-white/5 p-5 hover:bg-white/8 no-underline flex items-center gap-3">
      <span class="text-2xl">📦</span>
      <div>
        <p class="text-sm font-bold text-white">Agregar datos</p>
        <p class="text-xs text-stone-500 mt-0.5">Pandas pipeline</p>
      </div>
    </a>
    <a href="reports_step2_roi.html"
       class="rounded-2xl border border-white/10 bg-white/5 p-5 hover:bg-white/8 no-underline flex items-center gap-3">
      <span class="text-2xl">📈</span>
      <div>
        <p class="text-sm font-bold text-white">ROI de Marca</p>
        <p class="text-xs text-stone-500 mt-0.5">Brand Authority</p>
      </div>
    </a>
    <a href="reports_step3_compose.html"
       class="rounded-2xl border border-white/10 bg-white/5 p-5 hover:bg-white/8 no-underline flex items-center gap-3">
      <span class="text-2xl">🎨</span>
      <div>
        <p class="text-sm font-bold text-white">Composición</p>
        <p class="text-xs text-stone-500 mt-0.5">Branding agencia</p>
      </div>
    </a>
    <a href="reports_step5_send.html"
       class="rounded-2xl border border-violet-500/20 bg-violet-500/5 p-5 hover:bg-violet-500/10 no-underline flex items-center gap-3">
      <span class="text-2xl">📧</span>
      <div>
        <p class="text-sm font-bold text-violet-300">Automatizar envío</p>
        <p class="text-xs text-stone-500 mt-0.5">informes@agencia.com</p>
      </div>
    </a>
  </div>

</div>"""
    return page("Hub de Reportes Ejecutivos", "reports_hub.html", body)


# ─── STEP 1 — Agregación ─────────────────────────────────────────────────────

def step1_agg() -> str:
    body = """
<div class="mx-auto max-w-5xl px-4 py-10 sm:px-6 pb-20 fade-up">

  <div class="mb-8">
    <p class="text-xs uppercase tracking-[.2em] text-violet-300/70 mb-1">Reportes Ejecutivos · Paso 1</p>
    <h1 class="text-3xl font-bold text-white">Agregación Multi-Ubicación</h1>
    <p class="mt-1 text-stone-400 text-sm">
      Un pipeline Python (Pandas + NumPy) consolida métricas de cientos de locales en minutos.
      El proceso normaliza escalas, detecta outliers y calcula índices compuestos listos para el informe.
    </p>
  </div>

  <!-- Config panel -->
  <div class="rounded-3xl border border-white/10 bg-white/5 p-6 mb-6">
    <h2 class="text-base font-semibold text-white mb-5">Configurar fuente de datos</h2>
    <div class="grid grid-cols-1 sm:grid-cols-2 gap-5 mb-5">
      <div>
        <label class="block text-xs text-stone-400 uppercase tracking-wider font-semibold mb-2">Rango de fechas</label>
        <select>
          <option selected>Abril 2026 (mes completo)</option>
          <option>Q1 2026 (enero–marzo)</option>
          <option>Últimos 6 meses</option>
          <option>Año 2025 completo</option>
          <option>Rango personalizado...</option>
        </select>
      </div>
      <div>
        <label class="block text-xs text-stone-400 uppercase tracking-wider font-semibold mb-2">Scope</label>
        <select>
          <option selected>Toda la red (50 locales · 4 tenants)</option>
          <option>Solo Cadena Pizzas Norte (22 locales)</option>
          <option>Solo Café Rápido (15 locales)</option>
          <option>Solo Restaurantes El Mar (8 locales)</option>
          <option>Solo Hoteles Solimar (5 locales)</option>
        </select>
      </div>
      <div>
        <label class="block text-xs text-stone-400 uppercase tracking-wider font-semibold mb-2">Métricas a incluir</label>
        <select>
          <option selected>Todas las métricas disponibles</option>
          <option>Solo reputación (nota, reseñas)</option>
          <option>Solo visibilidad (GBP, clics)</option>
          <option>Solo rendimiento (conversiones, llamadas)</option>
        </select>
      </div>
      <div>
        <label class="block text-xs text-stone-400 uppercase tracking-wider font-semibold mb-2">Agrupación</label>
        <select>
          <option selected>Por tenant y por local</option>
          <option>Por ciudad / región</option>
          <option>Por tipo de negocio</option>
          <option>Plano (sin agrupación)</option>
        </select>
      </div>
    </div>
    <button class="px-6 py-3 rounded-2xl bg-gradient-to-r from-violet-600 to-indigo-600
                   text-white font-bold text-sm hover:from-violet-500 hover:to-indigo-500">
      ▶ Ejecutar pipeline de agregación
    </button>
  </div>

  <!-- Pipeline visualization -->
  <div class="rounded-3xl border border-violet-500/20 bg-violet-500/5 p-6 mb-6">
    <h2 class="text-base font-semibold text-white mb-4">Pipeline de procesamiento</h2>
    <div class="grid grid-cols-1 sm:grid-cols-5 gap-3 text-center text-xs">
      <div class="rounded-2xl bg-black/20 border border-white/8 p-4">
        <div class="w-9 h-9 rounded-xl bg-violet-500/30 flex items-center justify-center text-lg mx-auto mb-2">🗄️</div>
        <p class="font-bold text-stone-200 mb-1">Extracción</p>
        <p class="text-stone-500">GBP API · Postgres · Celery</p>
      </div>
      <div class="flex items-center justify-center text-stone-600 text-xl hidden sm:flex">→</div>
      <div class="rounded-2xl bg-black/20 border border-white/8 p-4">
        <div class="w-9 h-9 rounded-xl bg-indigo-500/30 flex items-center justify-center text-lg mx-auto mb-2">🧹</div>
        <p class="font-bold text-stone-200 mb-1">Limpieza</p>
        <p class="text-stone-500">Pandas · Normalización · Outliers</p>
      </div>
      <div class="flex items-center justify-center text-stone-600 text-xl hidden sm:flex">→</div>
      <div class="rounded-2xl bg-black/20 border border-white/8 p-4">
        <div class="w-9 h-9 rounded-xl bg-emerald-500/30 flex items-center justify-center text-lg mx-auto mb-2">📊</div>
        <p class="font-bold text-stone-200 mb-1">Agregación</p>
        <p class="text-stone-500">groupby · agg · pivot</p>
      </div>
    </div>
    <div class="grid grid-cols-1 sm:grid-cols-5 gap-3 text-center text-xs mt-3">
      <div class="rounded-2xl bg-black/20 border border-emerald-500/15 p-4">
        <div class="w-9 h-9 rounded-xl bg-emerald-500/20 flex items-center justify-center text-lg mx-auto mb-2">🤖</div>
        <p class="font-bold text-stone-200 mb-1">KPIs IA</p>
        <p class="text-stone-500">NLP · Sentimiento · Brand Authority</p>
      </div>
      <div class="flex items-center justify-center text-stone-600 text-xl hidden sm:flex">→</div>
      <div class="rounded-2xl bg-black/20 border border-violet-500/15 p-4">
        <div class="w-9 h-9 rounded-xl bg-violet-500/20 flex items-center justify-center text-lg mx-auto mb-2">📄</div>
        <p class="font-bold text-stone-200 mb-1">Exportación</p>
        <p class="text-stone-500">JSON · CSV · PDF (WeasyPrint)</p>
      </div>
      <div></div>
      <div></div>
    </div>
  </div>

  <!-- Code snippet -->
  <div class="rounded-3xl border border-white/10 bg-white/5 p-6 mb-6">
    <h2 class="text-base font-semibold text-white mb-4">Extracto del pipeline (Python · Pandas)</h2>
    <div class="rounded-2xl bg-black/30 border border-white/8 p-5 font-mono text-xs leading-relaxed overflow-x-auto">
      <div class="text-stone-500 mb-2"># lokigi/app/report_aggregation.py</div>
      <div><span class="text-violet-400">import</span> <span class="text-stone-200">pandas as pd</span></div>
      <div><span class="text-violet-400">from</span> <span class="text-stone-200">app.models</span> <span class="text-violet-400">import</span> <span class="text-stone-200">Location, Review</span></div>
      <div class="mt-3"><span class="text-violet-400">def</span> <span class="text-emerald-300">aggregate_network</span><span class="text-stone-200">(tenant_ids, date_from, date_to):</span></div>
      <div class="ml-4 text-stone-400">    # 1. Extraer reseñas del período</div>
      <div class="ml-4"><span class="text-stone-200">    df = pd.read_sql(</span></div>
      <div class="ml-8"><span class="text-amber-300">        "SELECT l.id, l.name, l.tenant_id, r.rating, r.date, r.sentiment"</span></div>
      <div class="ml-8"><span class="text-amber-300">        " FROM reviews r JOIN locations l ON r.location_id = l.id"</span></div>
      <div class="ml-8"><span class="text-amber-300">        " WHERE l.tenant_id = ANY(%s) AND r.date BETWEEN %s AND %s"</span><span class="text-stone-200">,</span></div>
      <div class="ml-8"><span class="text-stone-200">        params=[tenant_ids, date_from, date_to], con=db.engine)</span></div>
      <div class="mt-2 ml-4 text-stone-400">    # 2. Agregar por local</div>
      <div class="ml-4"><span class="text-stone-200">    agg = df.groupby([</span><span class="text-amber-300">"tenant_id"</span><span class="text-stone-200">,</span><span class="text-amber-300">"id"</span><span class="text-stone-200">,</span><span class="text-amber-300">"name"</span><span class="text-stone-200">]).agg(</span></div>
      <div class="ml-8"><span class="text-stone-200">        avg_rating=(</span><span class="text-amber-300">"rating"</span><span class="text-stone-200">,</span><span class="text-amber-300">"mean"</span><span class="text-stone-200">),</span></div>
      <div class="ml-8"><span class="text-stone-200">        review_count=(</span><span class="text-amber-300">"rating"</span><span class="text-stone-200">,</span><span class="text-amber-300">"count"</span><span class="text-stone-200">),</span></div>
      <div class="ml-8"><span class="text-stone-200">        avg_sentiment=(</span><span class="text-amber-300">"sentiment"</span><span class="text-stone-200">,</span><span class="text-amber-300">"mean"</span><span class="text-stone-200">),</span></div>
      <div class="ml-4"><span class="text-stone-200">    ).reset_index().round(</span><span class="text-indigo-300">2</span><span class="text-stone-200">)</span></div>
      <div class="mt-2 ml-4 text-stone-400">    # 3. Calcular Brand Authority Index (0–100)</div>
      <div class="ml-4"><span class="text-stone-200">    agg[</span><span class="text-amber-300">"brand_authority"</span><span class="text-stone-200">] = (</span></div>
      <div class="ml-8"><span class="text-stone-200">        agg[</span><span class="text-amber-300">"avg_rating"</span><span class="text-stone-200">] / </span><span class="text-indigo-300">5</span><span class="text-stone-200"> * </span><span class="text-indigo-300">0.4</span></div>
      <div class="ml-8"><span class="text-stone-200">        + agg[</span><span class="text-amber-300">"avg_sentiment"</span><span class="text-stone-200">] * </span><span class="text-indigo-300">0.4</span></div>
      <div class="ml-8"><span class="text-stone-200">        + (agg[</span><span class="text-amber-300">"review_count"</span><span class="text-stone-200">].clip(</span><span class="text-indigo-300">0</span><span class="text-stone-200">,</span><span class="text-indigo-300">500</span><span class="text-stone-200">) / </span><span class="text-indigo-300">500</span><span class="text-stone-200">) * </span><span class="text-indigo-300">0.2</span></div>
      <div class="ml-4"><span class="text-stone-200">    ) * </span><span class="text-indigo-300">100</span></div>
      <div class="mt-2 ml-4"><span class="text-violet-400">    return</span> <span class="text-stone-200">agg.sort_values(</span><span class="text-amber-300">"brand_authority"</span><span class="text-stone-200">, ascending=</span><span class="text-rose-300">False</span><span class="text-stone-200">)</span></div>
    </div>
  </div>

  <!-- Results preview -->
  <div class="rounded-3xl border border-white/10 bg-white/5 p-6 mb-8">
    <div class="flex items-center gap-3 mb-5">
      <div class="w-2 h-2 rounded-full bg-emerald-400 pulse-glow"></div>
      <h2 class="text-base font-semibold text-white m-0">Resultados de la última agregación — Abril 2026</h2>
      <span class="text-xs text-stone-500 ml-auto">Ejecutado hace 2 min · 50 locales · 14.820 reseñas</span>
    </div>
    <div class="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-5">
      <div class="rounded-2xl bg-black/15 border border-white/8 p-4 text-center">
        <p class="text-2xl font-black text-emerald-300">14.820</p>
        <p class="text-xs text-stone-500 mt-1">Reseñas procesadas</p>
      </div>
      <div class="rounded-2xl bg-black/15 border border-white/8 p-4 text-center">
        <p class="text-2xl font-black text-violet-300">87.4</p>
        <p class="text-xs text-stone-500 mt-1">Brand Authority medio</p>
      </div>
      <div class="rounded-2xl bg-black/15 border border-white/8 p-4 text-center">
        <p class="text-2xl font-black text-white">4.3★</p>
        <p class="text-xs text-stone-500 mt-1">Nota media ponderada</p>
      </div>
      <div class="rounded-2xl bg-black/15 border border-white/8 p-4 text-center">
        <p class="text-2xl font-black text-indigo-300">0.78</p>
        <p class="text-xs text-stone-500 mt-1">Sentimiento medio (0–1)</p>
      </div>
    </div>
    <div class="space-y-2">
      <p class="text-xs text-stone-500 uppercase tracking-wider font-semibold mb-3">Brand Authority por tenant</p>
      <div class="flex items-center gap-3">
        <span class="text-xs text-stone-300 w-44 text-right flex-shrink-0">Hoteles Solimar</span>
        <div class="flex-1 h-3 rounded-full bg-black/30 overflow-hidden"><div class="h-full rounded-full bg-violet-500 bar-anim" style="width:92%"></div></div>
        <span class="text-xs font-bold text-violet-300 w-10 flex-shrink-0">92.1</span>
      </div>
      <div class="flex items-center gap-3">
        <span class="text-xs text-stone-300 w-44 text-right flex-shrink-0">Restaurantes El Mar</span>
        <div class="flex-1 h-3 rounded-full bg-black/30 overflow-hidden"><div class="h-full rounded-full bg-emerald-500 bar-anim" style="width:89%"></div></div>
        <span class="text-xs font-bold text-emerald-300 w-10 flex-shrink-0">89.3</span>
      </div>
      <div class="flex items-center gap-3">
        <span class="text-xs text-stone-300 w-44 text-right flex-shrink-0">Franquicia Café Rápido</span>
        <div class="flex-1 h-3 rounded-full bg-black/30 overflow-hidden"><div class="h-full rounded-full bg-indigo-500 bar-anim" style="width:86%"></div></div>
        <span class="text-xs font-bold text-indigo-300 w-10 flex-shrink-0">86.2</span>
      </div>
      <div class="flex items-center gap-3">
        <span class="text-xs text-stone-300 w-44 text-right flex-shrink-0">Cadena Pizzas Norte</span>
        <div class="flex-1 h-3 rounded-full bg-black/30 overflow-hidden"><div class="h-full rounded-full bg-amber-500 bar-anim" style="width:82%"></div></div>
        <span class="text-xs font-bold text-amber-300 w-10 flex-shrink-0">82.0</span>
      </div>
    </div>
  </div>

  <!-- Nav -->
  <div class="flex justify-between items-center">
    <a href="reports_hub.html"
       class="px-5 py-3 rounded-2xl border border-white/10 bg-white/5
              text-stone-300 font-semibold text-sm hover:bg-white/10 no-underline">
      ← Hub
    </a>
    <a href="reports_step2_roi.html"
       class="px-8 py-3 rounded-2xl bg-gradient-to-r from-violet-600 to-indigo-600
              text-white font-bold text-sm hover:from-violet-500 hover:to-indigo-500 no-underline">
      Ver ROI de Marca →
    </a>
  </div>
</div>"""
    return page("Paso 1 — Agregación Multi-Ubicación", "reports_step1_agg.html", body)


# ─── STEP 2 — ROI de Marca ───────────────────────────────────────────────────

def step2_roi() -> str:
    body = """
<div class="mx-auto max-w-5xl px-4 py-10 sm:px-6 pb-20 fade-up">

  <div class="mb-8">
    <p class="text-xs uppercase tracking-[.2em] text-violet-300/70 mb-1">Reportes Ejecutivos · Paso 2</p>
    <h1 class="text-3xl font-bold text-white">ROI de Marca</h1>
    <p class="mt-1 text-stone-400 text-sm max-w-xl">
      Más allá de los clics: Lokigi mide la <strong class="text-white">Autoridad de Marca</strong> en toda la región.
      Un índice compuesto que combina reputación, visibilidad, sentimiento y crecimiento de reseñas,
      traducido a impacto económico real.
    </p>
  </div>

  <!-- Brand Authority Index -->
  <div class="rounded-3xl border border-violet-500/30
              bg-gradient-to-br from-violet-950/60 to-stone-900 p-8 mb-8">
    <div class="flex flex-col sm:flex-row items-center gap-8">
      <div class="text-center flex-shrink-0">
        <p class="text-xs uppercase tracking-[.2em] text-violet-300/70 mb-2">Brand Authority Index™</p>
        <div class="relative w-36 h-36 mx-auto">
          <!-- Circle gauge visualization -->
          <div class="w-36 h-36 rounded-full border-8 border-violet-500/30 flex items-center justify-center">
            <div>
              <p class="text-5xl font-black text-violet-300 leading-none">87</p>
              <p class="text-xs text-stone-400 text-center">/100</p>
            </div>
          </div>
        </div>
        <p class="text-xs text-violet-300/70 mt-3 font-semibold">▲ +6 pp vs. Q1 2026</p>
      </div>
      <div class="flex-1 w-full">
        <h3 class="text-sm font-bold text-stone-300 uppercase tracking-wider mb-4">Composición del índice</h3>
        <div class="space-y-3">
          <div>
            <div class="flex justify-between text-xs mb-1">
              <span class="text-stone-300">Reputación (nota media 4.3★)</span>
              <span class="text-stone-400 font-semibold">peso 40%</span>
            </div>
            <div class="h-2.5 rounded-full bg-black/30 overflow-hidden">
              <div class="h-full rounded-full bg-emerald-500 bar-anim" style="width:86%"></div>
            </div>
          </div>
          <div>
            <div class="flex justify-between text-xs mb-1">
              <span class="text-stone-300">Sentimiento NLP (media 0.78)</span>
              <span class="text-stone-400 font-semibold">peso 40%</span>
            </div>
            <div class="h-2.5 rounded-full bg-black/30 overflow-hidden">
              <div class="h-full rounded-full bg-indigo-500 bar-anim" style="width:78%"></div>
            </div>
          </div>
          <div>
            <div class="flex justify-between text-xs mb-1">
              <span class="text-stone-300">Volumen de reseñas (297/mes)</span>
              <span class="text-stone-400 font-semibold">peso 20%</span>
            </div>
            <div class="h-2.5 rounded-full bg-black/30 overflow-hidden">
              <div class="h-full rounded-full bg-violet-400 bar-anim" style="width:59%"></div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>

  <!-- Regional growth -->
  <div class="grid grid-cols-1 sm:grid-cols-2 gap-5 mb-6">

    <!-- Authority over time -->
    <div class="rounded-3xl border border-white/10 bg-white/5 p-6">
      <h2 class="text-sm font-bold text-white mb-4">Evolución Brand Authority — 12 meses</h2>
      <div class="flex items-end gap-2 h-28">
        <div class="flex flex-col items-center gap-1 flex-1">
          <span class="text-xs text-stone-500">74</span>
          <div class="w-full rounded-t-lg bg-violet-500/20 bar-anim" style="height:55%"></div>
          <span class="text-xs text-stone-600">May</span>
        </div>
        <div class="flex flex-col items-center gap-1 flex-1">
          <span class="text-xs text-stone-500">75</span>
          <div class="w-full rounded-t-lg bg-violet-500/20 bar-anim" style="height:57%"></div>
          <span class="text-xs text-stone-600">Jun</span>
        </div>
        <div class="flex flex-col items-center gap-1 flex-1">
          <span class="text-xs text-stone-500">77</span>
          <div class="w-full rounded-t-lg bg-violet-500/25 bar-anim" style="height:61%"></div>
          <span class="text-xs text-stone-600">Jul</span>
        </div>
        <div class="flex flex-col items-center gap-1 flex-1">
          <span class="text-xs text-stone-500">76</span>
          <div class="w-full rounded-t-lg bg-violet-500/25 bar-anim" style="height:59%"></div>
          <span class="text-xs text-stone-600">Ago</span>
        </div>
        <div class="flex flex-col items-center gap-1 flex-1">
          <span class="text-xs text-stone-500">79</span>
          <div class="w-full rounded-t-lg bg-violet-500/30 bar-anim" style="height:64%"></div>
          <span class="text-xs text-stone-600">Sep</span>
        </div>
        <div class="flex flex-col items-center gap-1 flex-1">
          <span class="text-xs text-stone-500">80</span>
          <div class="w-full rounded-t-lg bg-violet-500/35 bar-anim" style="height:66%"></div>
          <span class="text-xs text-stone-600">Oct</span>
        </div>
        <div class="flex flex-col items-center gap-1 flex-1">
          <span class="text-xs text-stone-500">81</span>
          <div class="w-full rounded-t-lg bg-violet-500/40 bar-anim" style="height:68%"></div>
          <span class="text-xs text-stone-600">Nov</span>
        </div>
        <div class="flex flex-col items-center gap-1 flex-1">
          <span class="text-xs text-stone-500">82</span>
          <div class="w-full rounded-t-lg bg-violet-500/45 bar-anim" style="height:70%"></div>
          <span class="text-xs text-stone-600">Dic</span>
        </div>
        <div class="flex flex-col items-center gap-1 flex-1">
          <span class="text-xs text-stone-500">83</span>
          <div class="w-full rounded-t-lg bg-violet-500/55 bar-anim" style="height:73%"></div>
          <span class="text-xs text-stone-600">Ene</span>
        </div>
        <div class="flex flex-col items-center gap-1 flex-1">
          <span class="text-xs text-stone-500">84</span>
          <div class="w-full rounded-t-lg bg-violet-500/65 bar-anim" style="height:77%"></div>
          <span class="text-xs text-stone-600">Feb</span>
        </div>
        <div class="flex flex-col items-center gap-1 flex-1">
          <span class="text-xs text-stone-500">85</span>
          <div class="w-full rounded-t-lg bg-violet-500/75 bar-anim" style="height:81%"></div>
          <span class="text-xs text-stone-600">Mar</span>
        </div>
        <div class="flex flex-col items-center gap-1 flex-1">
          <span class="text-xs text-stone-300 font-black">87</span>
          <div class="w-full rounded-t-lg bg-violet-500 bar-anim" style="height:88%"></div>
          <span class="text-xs text-violet-400 font-bold">Abr↑</span>
        </div>
      </div>
    </div>

    <!-- vs Competition -->
    <div class="rounded-3xl border border-white/10 bg-white/5 p-6">
      <h2 class="text-sm font-bold text-white mb-4">Comparativa regional — Brand Authority</h2>
      <div class="space-y-3">
        <div>
          <div class="flex justify-between text-xs mb-1">
            <span class="text-violet-300 font-bold">Tu red (Lokigi) ★</span>
            <span class="text-violet-300 font-black">87</span>
          </div>
          <div class="h-3 rounded-full bg-black/30 overflow-hidden">
            <div class="h-full rounded-full bg-violet-500 bar-anim" style="width:87%"></div>
          </div>
        </div>
        <div>
          <div class="flex justify-between text-xs mb-1">
            <span class="text-stone-400">Competidor A (est.)</span>
            <span class="text-stone-400 font-bold">71</span>
          </div>
          <div class="h-3 rounded-full bg-black/30 overflow-hidden">
            <div class="h-full rounded-full bg-stone-600 bar-anim" style="width:71%"></div>
          </div>
        </div>
        <div>
          <div class="flex justify-between text-xs mb-1">
            <span class="text-stone-400">Competidor B (est.)</span>
            <span class="text-stone-400 font-bold">64</span>
          </div>
          <div class="h-3 rounded-full bg-black/30 overflow-hidden">
            <div class="h-full rounded-full bg-stone-700 bar-anim" style="width:64%"></div>
          </div>
        </div>
        <div>
          <div class="flex justify-between text-xs mb-1">
            <span class="text-stone-400">Media de sector (hostelería)</span>
            <span class="text-stone-400 font-bold">59</span>
          </div>
          <div class="h-3 rounded-full bg-black/30 overflow-hidden">
            <div class="h-full rounded-full bg-stone-700 bar-anim" style="width:59%"></div>
          </div>
        </div>
        <p class="text-xs text-emerald-400 mt-3 font-semibold">▲ +28 pp sobre la media del sector</p>
      </div>
    </div>
  </div>

  <!-- ROI translation -->
  <div class="rounded-3xl border border-emerald-500/20 bg-emerald-950/20 p-6 mb-8">
    <h2 class="text-base font-semibold text-white mb-5">Impacto económico estimado</h2>
    <p class="text-stone-400 text-sm mb-5">
      Cada punto de Brand Authority se correlaciona con un aumento de ~1.2% en conversiones
      (llamadas + clics → visitas). Estimación basada en el modelo de reputación de Lokigi (N=50 locales, 12 meses).
    </p>
    <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
      <div class="rounded-2xl border border-emerald-500/20 bg-black/15 p-5 text-center">
        <p class="text-3xl font-black text-emerald-300">+18.4%</p>
        <p class="text-xs text-stone-400 mt-1 uppercase tracking-wider">Conversiones GBP</p>
        <p class="text-xs text-stone-500 mt-1">vs. hace 12 meses</p>
      </div>
      <div class="rounded-2xl border border-emerald-500/20 bg-black/15 p-5 text-center">
        <p class="text-3xl font-black text-emerald-300">+31%</p>
        <p class="text-xs text-stone-400 mt-1 uppercase tracking-wider">Llamadas directas</p>
        <p class="text-xs text-stone-500 mt-1">desde perfil GBP</p>
      </div>
      <div class="rounded-2xl border border-violet-500/20 bg-black/15 p-5 text-center">
        <p class="text-3xl font-black text-violet-300">€124K</p>
        <p class="text-xs text-stone-400 mt-1 uppercase tracking-wider">Valor est. reseñas</p>
        <p class="text-xs text-stone-500 mt-1">Coste equivalente en publicidad pagada</p>
      </div>
    </div>
  </div>

  <!-- Nav -->
  <div class="flex justify-between items-center">
    <a href="reports_step1_agg.html"
       class="px-5 py-3 rounded-2xl border border-white/10 bg-white/5
              text-stone-300 font-semibold text-sm hover:bg-white/10 no-underline">
      ← Agregación
    </a>
    <a href="reports_step3_compose.html"
       class="px-8 py-3 rounded-2xl bg-gradient-to-r from-violet-600 to-indigo-600
              text-white font-bold text-sm hover:from-violet-500 hover:to-indigo-500 no-underline">
      Componer informe →
    </a>
  </div>
</div>"""
    return page("Paso 2 — ROI de Marca", "reports_step2_roi.html", body)


# ─── STEP 3 — Composición ────────────────────────────────────────────────────

def step3_compose() -> str:
    body = """
<div class="mx-auto max-w-4xl px-4 py-10 sm:px-6 pb-20 fade-up">

  <div class="mb-8">
    <p class="text-xs uppercase tracking-[.2em] text-violet-300/70 mb-1">Reportes Ejecutivos · Paso 3</p>
    <h1 class="text-3xl font-bold text-white">Composición del Informe</h1>
    <p class="mt-1 text-stone-400 text-sm">
      Configura la portada, las secciones incluidas y el branding de la agencia.
      El informe final se presenta como un documento de alta dirección con la identidad visual de tu empresa.
    </p>
  </div>

  <!-- Branding -->
  <div class="rounded-3xl border border-white/10 bg-white/5 p-6 mb-6">
    <h2 class="text-base font-semibold text-white mb-5">Identidad visual de la agencia</h2>
    <div class="grid grid-cols-1 sm:grid-cols-2 gap-5">
      <div>
        <label class="block text-xs text-stone-400 uppercase tracking-wider font-semibold mb-2">Nombre de la agencia</label>
        <input type="text" value="Marketing Digital Pro SL" />
      </div>
      <div>
        <label class="block text-xs text-stone-400 uppercase tracking-wider font-semibold mb-2">Remitente de informes</label>
        <input type="email" value="informes@tuagencia.com" />
      </div>
      <div>
        <label class="block text-xs text-stone-400 uppercase tracking-wider font-semibold mb-2">Color primario de marca</label>
        <div class="flex gap-3 items-center">
          <div class="w-10 h-10 rounded-xl bg-violet-600 border-2 border-violet-400 cursor-pointer flex-shrink-0"></div>
          <div class="w-10 h-10 rounded-xl bg-indigo-600 border border-white/10 cursor-pointer flex-shrink-0"></div>
          <div class="w-10 h-10 rounded-xl bg-emerald-600 border border-white/10 cursor-pointer flex-shrink-0"></div>
          <div class="w-10 h-10 rounded-xl bg-rose-600 border border-white/10 cursor-pointer flex-shrink-0"></div>
          <div class="w-10 h-10 rounded-xl bg-amber-600 border border-white/10 cursor-pointer flex-shrink-0"></div>
          <input type="text" value="#7c3aed" class="w-28 text-xs" />
        </div>
      </div>
      <div>
        <label class="block text-xs text-stone-400 uppercase tracking-wider font-semibold mb-2">Logo de agencia (PNG/SVG)</label>
        <div class="flex items-center gap-3 border border-dashed border-white/20 rounded-xl p-3 cursor-pointer hover:border-violet-500/40">
          <span class="text-2xl">📎</span>
          <div>
            <p class="text-sm text-stone-300 font-semibold">logo_agencia.png</p>
            <p class="text-xs text-stone-500">192×64 px · Cargado · Cambiar</p>
          </div>
        </div>
      </div>
    </div>
  </div>

  <!-- Cover page -->
  <div class="rounded-3xl border border-white/10 bg-white/5 p-6 mb-6">
    <h2 class="text-base font-semibold text-white mb-5">Portada del documento</h2>
    <div class="grid grid-cols-1 sm:grid-cols-2 gap-5 mb-5">
      <div>
        <label class="block text-xs text-stone-400 uppercase tracking-wider font-semibold mb-2">Título del informe</label>
        <input type="text" value="Informe Ejecutivo de Reputación — Abril 2026" />
      </div>
      <div>
        <label class="block text-xs text-stone-400 uppercase tracking-wider font-semibold mb-2">Subtítulo</label>
        <input type="text" value="Análisis consolidado · 50 locales · 4 cadenas" />
      </div>
      <div>
        <label class="block text-xs text-stone-400 uppercase tracking-wider font-semibold mb-2">Preparado para</label>
        <input type="text" value="Comité Directivo — Grupo Gastronómico Sur" />
      </div>
      <div>
        <label class="block text-xs text-stone-400 uppercase tracking-wider font-semibold mb-2">Fecha del documento</label>
        <input type="text" value="30 de abril de 2026" />
      </div>
    </div>
  </div>

  <!-- Sections -->
  <div class="rounded-3xl border border-white/10 bg-white/5 p-6 mb-6">
    <h2 class="text-base font-semibold text-white mb-5">Secciones del informe</h2>
    <div class="space-y-3">
      <div class="flex items-center gap-4 p-4 rounded-2xl border border-white/8 bg-black/10">
        <input type="checkbox" class="w-4 h-4 accent-violet-500 w-auto flex-shrink-0" checked />
        <div class="flex-1">
          <p class="text-sm font-semibold text-white">1. Resumen Ejecutivo</p>
          <p class="text-xs text-stone-500 mt-0.5">KPIs globales, Brand Authority Index, 3 conclusiones clave</p>
        </div>
        <span class="text-xs text-stone-600">~1 pág.</span>
      </div>
      <div class="flex items-center gap-4 p-4 rounded-2xl border border-white/8 bg-black/10">
        <input type="checkbox" class="w-4 h-4 accent-violet-500 w-auto flex-shrink-0" checked />
        <div class="flex-1">
          <p class="text-sm font-semibold text-white">2. Análisis de Reputación por Red</p>
          <p class="text-xs text-stone-500 mt-0.5">Nota media, distribución de ratings, tendencia mensual</p>
        </div>
        <span class="text-xs text-stone-600">~2 pág.</span>
      </div>
      <div class="flex items-center gap-4 p-4 rounded-2xl border border-white/8 bg-black/10">
        <input type="checkbox" class="w-4 h-4 accent-violet-500 w-auto flex-shrink-0" checked />
        <div class="flex-1">
          <p class="text-sm font-semibold text-white">3. ROI de Marca y Brand Authority</p>
          <p class="text-xs text-stone-500 mt-0.5">BAI por tenant, comparativa sectorial, impacto económico</p>
        </div>
        <span class="text-xs text-stone-600">~2 pág.</span>
      </div>
      <div class="flex items-center gap-4 p-4 rounded-2xl border border-white/8 bg-black/10">
        <input type="checkbox" class="w-4 h-4 accent-violet-500 w-auto flex-shrink-0" checked />
        <div class="flex-1">
          <p class="text-sm font-semibold text-white">4. Alertas y Crisis del Período</p>
          <p class="text-xs text-stone-500 mt-0.5">Incidencias detectadas, tiempo de respuesta, resolución</p>
        </div>
        <span class="text-xs text-stone-600">~1 pág.</span>
      </div>
      <div class="flex items-center gap-4 p-4 rounded-2xl border border-white/8 bg-black/10">
        <input type="checkbox" class="w-4 h-4 accent-violet-500 w-auto flex-shrink-0" checked />
        <div class="flex-1">
          <p class="text-sm font-semibold text-white">5. Benchmarking Interno y Ranking</p>
          <p class="text-xs text-stone-500 mt-0.5">#1 de la red, top 5, locales que requieren atención</p>
        </div>
        <span class="text-xs text-stone-600">~2 pág.</span>
      </div>
      <div class="flex items-center gap-4 p-4 rounded-2xl border border-white/8 bg-black/10">
        <input type="checkbox" class="w-4 h-4 accent-violet-500 w-auto flex-shrink-0" />
        <div class="flex-1">
          <p class="text-sm font-semibold text-stone-400">6. Detalle por Local (anexo)</p>
          <p class="text-xs text-stone-500 mt-0.5">Ficha individual de cada local — solo bajo demanda</p>
        </div>
        <span class="text-xs text-stone-600">~12 pág.</span>
      </div>
      <div class="flex items-center gap-4 p-4 rounded-2xl border border-white/8 bg-black/10">
        <input type="checkbox" class="w-4 h-4 accent-violet-500 w-auto flex-shrink-0" checked />
        <div class="flex-1">
          <p class="text-sm font-semibold text-white">7. Plan de Acción Recomendado</p>
          <p class="text-xs text-stone-500 mt-0.5">4–6 acciones priorizadas con responsable y fecha</p>
        </div>
        <span class="text-xs text-stone-600">~1 pág.</span>
      </div>
    </div>
    <p class="text-xs text-stone-500 mt-4">Documento estimado: <strong class="text-stone-300">9 páginas</strong> · Idioma: Español</p>
  </div>

  <!-- Nav -->
  <div class="flex justify-between items-center">
    <a href="reports_step2_roi.html"
       class="px-5 py-3 rounded-2xl border border-white/10 bg-white/5
              text-stone-300 font-semibold text-sm hover:bg-white/10 no-underline">
      ← ROI de Marca
    </a>
    <a href="reports_step4_preview.html"
       class="px-8 py-3 rounded-2xl bg-gradient-to-r from-violet-600 to-indigo-600
              text-white font-bold text-sm hover:from-violet-500 hover:to-indigo-500 no-underline">
      Vista previa PDF →
    </a>
  </div>
</div>"""
    return page("Paso 3 — Composición del Informe", "reports_step3_compose.html", body)


# ─── STEP 4 — Preview PDF ────────────────────────────────────────────────────

def step4_preview() -> str:
    body = """
<div class="mx-auto max-w-4xl px-4 py-10 sm:px-6 pb-20 fade-up">

  <div class="mb-8">
    <p class="text-xs uppercase tracking-[.2em] text-violet-300/70 mb-1">Reportes Ejecutivos · Paso 4</p>
    <h1 class="text-3xl font-bold text-white">Vista Previa del Informe</h1>
    <p class="mt-1 text-stone-400 text-sm">
      Revisa el documento generado antes de enviarlo. El PDF incluye tu branding, las secciones seleccionadas
      y los datos agregados de toda la red.
    </p>
  </div>

  <!-- Actions bar -->
  <div class="flex flex-wrap gap-3 mb-8">
    <button class="px-5 py-2.5 rounded-xl border border-white/10 bg-white/5 text-stone-300 text-sm font-semibold hover:bg-white/10 flex items-center gap-2">
      🔄 Regenerar
    </button>
    <button class="px-5 py-2.5 rounded-xl border border-white/10 bg-white/5 text-stone-300 text-sm font-semibold hover:bg-white/10 flex items-center gap-2">
      ✏️ Editar secciones
    </button>
    <button class="px-5 py-2.5 rounded-xl border border-white/10 bg-white/5 text-stone-300 text-sm font-semibold hover:bg-white/10 flex items-center gap-2">
      📥 Descargar PDF
    </button>
    <a href="reports_step5_send.html"
       class="px-5 py-2.5 rounded-xl bg-gradient-to-r from-violet-600 to-indigo-600
              text-white font-bold text-sm hover:from-violet-500 hover:to-indigo-500 no-underline flex items-center gap-2">
      📧 Enviar →
    </a>
  </div>

  <!-- PDF simulation -->
  <div class="pdf-page">

    <!-- Cover -->
    <div style="text-align:center;padding:16px 0 24px;border-bottom:2px solid #7c3aed;margin-bottom:20px">
      <div style="background:linear-gradient(135deg,#7c3aed,#4f46e5);width:40px;height:40px;border-radius:10px;display:inline-flex;align-items:center;justify-content:center;color:#fff;font-size:18px;font-weight:900;margin-bottom:10px">L</div>
      <div style="font-size:9px;color:#6b7280;text-transform:uppercase;letter-spacing:.1em;margin-bottom:8px">Marketing Digital Pro SL</div>
      <h1 style="font-size:18px;font-weight:900;color:#111;margin:0 0 4px">Informe Ejecutivo de Reputación</h1>
      <p style="font-size:13px;font-weight:700;color:#7c3aed;margin:0 0 8px">Abril 2026</p>
      <p style="font-size:10px;color:#6b7280;margin:0">Análisis consolidado · 50 locales · 4 cadenas</p>
      <p style="font-size:10px;color:#6b7280;margin:4px 0 0">Preparado para: <strong style="color:#374151">Comité Directivo — Grupo Gastronómico Sur</strong></p>
      <p style="font-size:9px;color:#9ca3af;margin:8px 0 0">Confidencial · 30 de abril de 2026</p>
    </div>

    <!-- Executive summary -->
    <h2>1. Resumen Ejecutivo</h2>
    <div class="kpi-row">
      <div class="kpi-box">
        <strong style="color:#7c3aed">87</strong>
        <span>Brand Authority</span>
      </div>
      <div class="kpi-box">
        <strong>4.3★</strong>
        <span>Nota media red</span>
      </div>
      <div class="kpi-box">
        <strong style="color:#10b981">+18%</strong>
        <span>Conversiones GBP</span>
      </div>
      <div class="kpi-box">
        <strong style="color:#10b981">50</strong>
        <span>Locales activos</span>
      </div>
    </div>
    <p style="margin:8px 0 4px"><strong>Conclusiones clave del período:</strong></p>
    <ul style="padding-left:16px;margin:4px 0 8px">
      <li>La red alcanza un BAI de 87/100, +6 pp respecto al Q1, situándola 28 pp por encima de la media sectorial.</li>
      <li>2 alertas de crisis resueltas con tiempo de respuesta &lt; 5 min gracias a la detección NLP automática.</li>
      <li>El Mar — Barceloneta (#1) establece un nuevo récord histórico de 4.8★ y sirve de referente de protocolo.</li>
    </ul>

    <!-- Reputation section -->
    <h2>2. Análisis de Reputación</h2>
    <p>La nota media ponderada de la red es <strong>4.3★</strong>, con tendencia ascendente (+0.3★ en 12 meses). El 86% de los 50 locales operan con nota ≥ 4.0★.</p>
    <div style="margin:10px 0">
      <div class="bar-row">
        <span class="bar-label">Hoteles Solimar</span>
        <div class="bar-track"><div class="bar-fill" style="width:92%;background:#7c3aed"></div></div>
        <span class="bar-val">4.5★</span>
      </div>
      <div class="bar-row">
        <span class="bar-label">Rest. El Mar</span>
        <div class="bar-track"><div class="bar-fill" style="width:88%;background:#10b981"></div></div>
        <span class="bar-val">4.4★</span>
      </div>
      <div class="bar-row">
        <span class="bar-label">Café Rápido</span>
        <div class="bar-track"><div class="bar-fill" style="width:86%;background:#6366f1"></div></div>
        <span class="bar-val">4.3★</span>
      </div>
      <div class="bar-row">
        <span class="bar-label">Pizzas Norte</span>
        <div class="bar-track"><div class="bar-fill" style="width:82%;background:#f59e0b"></div></div>
        <span class="bar-val">4.1★</span>
      </div>
    </div>

    <!-- ROI section -->
    <h2>3. ROI de Marca — Brand Authority Index</h2>
    <p>El BAI combina nota media (40%), sentimiento NLP (40%) y volumen de reseñas (20%). El índice actual de <strong>87/100</strong> equivale a €124.000 en valor publicitario equivalente (+18.4% conversiones GBP respecto al año anterior).</p>

    <!-- Actions -->
    <h2>7. Plan de Acción</h2>
    <ul style="padding-left:16px;margin:4px 0">
      <li><strong>Urgente:</strong> Cerrar crisis en El Mar — Sarrià y Pizza Norte — Getafe Sur (semana 1 mayo).</li>
      <li><strong>Corto plazo:</strong> Iniciar formación en 7 locales identificados (mayo 2026).</li>
      <li><strong>Medio plazo:</strong> Exportar protocolo de Barceloneta a los 5 locales con nota &lt; 4.0★.</li>
      <li><strong>Seguimiento:</strong> Auditoría de seguimiento programada para el 30 de mayo 2026.</li>
    </ul>

    <footer>
      Marketing Digital Pro SL · informes@tuagencia.com · Generado por Lokigi Enterprise
      <br/>Informe confidencial — uso interno y para el cliente. Prohibida su difusión externa.
    </footer>
  </div>

  <p class="text-center text-xs text-stone-600 mt-4">Simulación de portada · El documento completo tiene 9 páginas</p>

  <!-- Nav -->
  <div class="flex justify-between items-center mt-8">
    <a href="reports_step3_compose.html"
       class="px-5 py-3 rounded-2xl border border-white/10 bg-white/5
              text-stone-300 font-semibold text-sm hover:bg-white/10 no-underline">
      ← Composición
    </a>
    <a href="reports_step5_send.html"
       class="px-8 py-3 rounded-2xl bg-gradient-to-r from-violet-600 to-indigo-600
              text-white font-bold text-sm hover:from-violet-500 hover:to-indigo-500 no-underline">
      Configurar envío →
    </a>
  </div>
</div>"""
    return page("Paso 4 — Vista Previa PDF", "reports_step4_preview.html", body)


# ─── STEP 5 — Envío ──────────────────────────────────────────────────────────

def step5_send() -> str:
    body = """
<div class="mx-auto max-w-4xl px-4 py-10 sm:px-6 pb-20 fade-up">

  <div class="mb-8">
    <p class="text-xs uppercase tracking-[.2em] text-violet-300/70 mb-1">Reportes Ejecutivos · Paso 5</p>
    <h1 class="text-3xl font-bold text-white">Automatización de Envío</h1>
    <p class="mt-1 text-stone-400 text-sm">
      Los informes se envían desde el dominio de tu agencia (<strong class="text-white">informes@tuagencia.com</strong>),
      con tu logo y firma corporativa. Tus clientes ven el informe como tuyo — Lokigi trabaja entre bastidores.
    </p>
  </div>

  <!-- Sender config -->
  <div class="rounded-3xl border border-white/10 bg-white/5 p-6 mb-6">
    <h2 class="text-base font-semibold text-white mb-5">Configuración del remitente</h2>
    <div class="grid grid-cols-1 sm:grid-cols-2 gap-5 mb-5">
      <div>
        <label class="block text-xs text-stone-400 uppercase tracking-wider font-semibold mb-2">Email remitente</label>
        <input type="email" value="informes@tuagencia.com" />
        <p class="text-xs text-stone-500 mt-1.5 ml-1">✓ Dominio verificado · SPF y DKIM configurados</p>
      </div>
      <div>
        <label class="block text-xs text-stone-400 uppercase tracking-wider font-semibold mb-2">Nombre visible del remitente</label>
        <input type="text" value="Marketing Digital Pro SL" />
      </div>
      <div>
        <label class="block text-xs text-stone-400 uppercase tracking-wider font-semibold mb-2">Reply-to</label>
        <input type="email" value="tu@tuagencia.com" />
      </div>
      <div>
        <label class="block text-xs text-stone-400 uppercase tracking-wider font-semibold mb-2">Proveedor de envío</label>
        <select>
          <option selected>SendGrid (configurado · 10.000 emails/mes)</option>
          <option>Amazon SES</option>
          <option>Postmark</option>
          <option>SMTP personalizado</option>
        </select>
      </div>
    </div>
    <!-- Email preview -->
    <div class="rounded-2xl border border-white/10 bg-black/20 overflow-hidden">
      <div class="px-4 py-3 border-b border-white/10 flex items-center gap-3">
        <div class="w-3 h-3 rounded-full bg-rose-500/60"></div>
        <div class="w-3 h-3 rounded-full bg-amber-500/60"></div>
        <div class="w-3 h-3 rounded-full bg-emerald-500/60"></div>
        <span class="text-xs text-stone-500 ml-2">Vista previa del email de entrega</span>
      </div>
      <div class="p-5 bg-white/[.03]">
        <div class="text-xs space-y-1 mb-4 font-mono">
          <div><span class="text-stone-500">De:</span> <span class="text-stone-200">Marketing Digital Pro SL &lt;informes@tuagencia.com&gt;</span></div>
          <div><span class="text-stone-500">Asunto:</span> <span class="text-stone-200">📊 Informe Ejecutivo de Reputación — Abril 2026</span></div>
          <div><span class="text-stone-500">Para:</span> <span class="text-stone-200">CEO Grupo Gastronómico Sur, Director Marketing +6 más</span></div>
        </div>
        <div class="rounded-xl bg-white/5 border border-white/8 p-5 text-sm space-y-3">
          <div class="flex items-center gap-2.5 pb-3 border-b border-white/10">
            <div class="w-8 h-8 rounded-lg bg-gradient-to-br from-violet-500 to-indigo-600 flex items-center justify-center text-white font-black text-sm flex-shrink-0">MD</div>
            <div>
              <p class="text-xs font-bold text-white">Marketing Digital Pro SL</p>
              <p class="text-xs text-stone-500">informes@tuagencia.com</p>
            </div>
          </div>
          <p class="text-stone-300 text-xs leading-relaxed">
            Estimado/a equipo directivo,<br/><br/>
            Adjunto encontrarán el <strong class="text-white">Informe Ejecutivo de Reputación de abril de 2026</strong>
            correspondiente a su red de 50 establecimientos.<br/><br/>
            Este mes su red alcanza un <strong class="text-white">Brand Authority Index de 87/100</strong>,
            posicionándola <strong class="text-white">28 puntos por encima de la media del sector</strong>.<br/><br/>
            El informe completo (9 páginas) está adjunto en formato PDF.<br/><br/>
            Quedamos a su disposición para cualquier consulta.<br/><br/>
            Un saludo,<br/>
            <strong class="text-stone-200">El equipo de Marketing Digital Pro SL</strong>
          </p>
          <div class="flex items-center gap-3 pt-2 border-t border-white/10">
            <div class="w-10 h-10 rounded-xl border border-stone-700 bg-stone-800 flex items-center justify-center text-2xl">📄</div>
            <div>
              <p class="text-xs font-semibold text-stone-200">Informe_Ejecutivo_Abril2026.pdf</p>
              <p class="text-xs text-stone-500">9 páginas · 842 KB</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>

  <!-- Distribution list -->
  <div class="rounded-3xl border border-white/10 bg-white/5 p-6 mb-6">
    <div class="flex items-center justify-between mb-5">
      <h2 class="text-base font-semibold text-white m-0">Lista de distribución</h2>
      <button class="px-4 py-2 rounded-xl bg-violet-500/20 text-violet-300 text-xs font-bold hover:bg-violet-500/30">
        + Añadir destinatario
      </button>
    </div>
    <div class="space-y-2">
      <div class="flex items-center gap-4 p-3 rounded-2xl border border-white/8 bg-black/10 flex-wrap">
        <div class="w-8 h-8 rounded-full bg-violet-500/30 flex items-center justify-center text-xs font-bold text-violet-300 flex-shrink-0">CR</div>
        <div class="flex-1 min-w-0">
          <p class="text-sm font-semibold text-stone-200">Carlos Rodríguez</p>
          <p class="text-xs text-stone-500">CEO · carlos@grupogastronomicosur.es</p>
        </div>
        <span class="px-2 py-0.5 rounded-full bg-emerald-500/15 text-emerald-300 text-xs font-bold">✓ Informe completo</span>
      </div>
      <div class="flex items-center gap-4 p-3 rounded-2xl border border-white/8 bg-black/10 flex-wrap">
        <div class="w-8 h-8 rounded-full bg-indigo-500/30 flex items-center justify-center text-xs font-bold text-indigo-300 flex-shrink-0">LM</div>
        <div class="flex-1 min-w-0">
          <p class="text-sm font-semibold text-stone-200">Laura Martínez</p>
          <p class="text-xs text-stone-500">Dir. Marketing · laura@grupogastronomicosur.es</p>
        </div>
        <span class="px-2 py-0.5 rounded-full bg-emerald-500/15 text-emerald-300 text-xs font-bold">✓ Informe completo</span>
      </div>
      <div class="flex items-center gap-4 p-3 rounded-2xl border border-white/8 bg-black/10 flex-wrap">
        <div class="w-8 h-8 rounded-full bg-amber-500/30 flex items-center justify-center text-xs font-bold text-amber-300 flex-shrink-0">PG</div>
        <div class="flex-1 min-w-0">
          <p class="text-sm font-semibold text-stone-200">Pedro García</p>
          <p class="text-xs text-stone-500">Dir. Operaciones · pedro@grupogastronomicosur.es</p>
        </div>
        <span class="px-2 py-0.5 rounded-full bg-indigo-500/15 text-indigo-300 text-xs font-bold">Solo resumen (1 pág.)</span>
      </div>
      <div class="flex items-center gap-4 p-3 rounded-2xl border border-white/8 bg-black/10 flex-wrap">
        <div class="w-8 h-8 rounded-full bg-stone-500/30 flex items-center justify-center text-xs font-bold text-stone-400 flex-shrink-0">+5</div>
        <div class="flex-1">
          <p class="text-sm text-stone-400">5 destinatarios más (managers de cadena)</p>
        </div>
        <button class="text-xs text-stone-500 hover:text-stone-300">Ver todos →</button>
      </div>
    </div>
  </div>

  <!-- Schedule -->
  <div class="rounded-3xl border border-white/10 bg-white/5 p-6 mb-6">
    <h2 class="text-base font-semibold text-white mb-5">Programación de envíos</h2>
    <div class="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-5">
      <div>
        <label class="block text-xs text-stone-400 uppercase tracking-wider font-semibold mb-2">Frecuencia</label>
        <select>
          <option selected>Mensual (1° de cada mes)</option>
          <option>Semanal (todos los lunes)</option>
          <option>Quincenal</option>
          <option>Trimestral</option>
          <option>Solo manual</option>
        </select>
      </div>
      <div>
        <label class="block text-xs text-stone-400 uppercase tracking-wider font-semibold mb-2">Hora de envío</label>
        <input type="text" value="09:00 h (hora local)" />
      </div>
      <div>
        <label class="block text-xs text-stone-400 uppercase tracking-wider font-semibold mb-2">Zona horaria</label>
        <select>
          <option selected>Europe/Madrid (CET/CEST)</option>
          <option>UTC</option>
          <option>America/Mexico_City</option>
        </select>
      </div>
    </div>

    <!-- Delivery log -->
    <h3 class="text-sm font-semibold text-stone-300 mb-3">Registro de entregas recientes</h3>
    <div class="space-y-2 font-mono text-xs">
      <div class="flex gap-3 text-stone-300">
        <span class="text-stone-500 flex-shrink-0">30 Abr 09:01</span>
        <span class="text-emerald-400">SENT</span>
        <span>report=mensual-abr2026 · recipients=8 · opens=8 · status=delivered</span>
      </div>
      <div class="flex gap-3 text-stone-300">
        <span class="text-stone-500 flex-shrink-0">28 Abr 08:00</span>
        <span class="text-emerald-400">SENT</span>
        <span>report=semanal-28abr · recipients=4 · opens=4 · status=delivered</span>
      </div>
      <div class="flex gap-3 text-stone-300">
        <span class="text-stone-500 flex-shrink-0">1 Abr 09:00</span>
        <span class="text-emerald-400">SENT</span>
        <span>report=mensual-mar2026 · recipients=8 · opens=7 · status=delivered</span>
      </div>
      <div class="flex gap-3 text-stone-300">
        <span class="text-stone-500 flex-shrink-0">31 Mar 10:15</span>
        <span class="text-emerald-400">SENT</span>
        <span>report=trimestral-q1-2026 · recipients=12 · opens=11 · status=delivered</span>
      </div>
    </div>
  </div>

  <!-- Send now CTA -->
  <div class="rounded-3xl border border-violet-500/25 bg-violet-950/30 p-6 mb-8 flex flex-col sm:flex-row items-center gap-5">
    <div class="flex-1">
      <h3 class="text-base font-bold text-white mb-1">¿Enviar el informe ahora?</h3>
      <p class="text-stone-400 text-sm">
        Se enviará el informe de abril a los 8 destinatarios desde
        <span class="text-white font-semibold">informes@tuagencia.com</span>.
        La siguiente entrega programada es el <strong class="text-white">1 mayo a las 09:00</strong>.
      </p>
    </div>
    <button class="px-7 py-3.5 rounded-2xl bg-gradient-to-r from-violet-600 to-indigo-600
                   text-white font-bold text-sm hover:from-violet-500 hover:to-indigo-500 flex-shrink-0 w-full sm:w-auto">
      📧 Enviar ahora
    </button>
  </div>

  <!-- Nav -->
  <div class="flex justify-between items-center">
    <a href="reports_step4_preview.html"
       class="px-5 py-3 rounded-2xl border border-white/10 bg-white/5
              text-stone-300 font-semibold text-sm hover:bg-white/10 no-underline">
      ← Vista previa
    </a>
    <a href="reports_hub.html"
       class="px-8 py-3 rounded-2xl bg-gradient-to-r from-violet-600 to-indigo-600
              text-white font-bold text-sm hover:from-violet-500 hover:to-indigo-500 no-underline">
      ← Volver al Hub
    </a>
  </div>
</div>"""
    return page("Paso 5 — Automatización de Envío", "reports_step5_send.html", body)


# ─── RENDER ──────────────────────────────────────────────────────────────────

def main() -> None:
    files = [
        ("reports_hub.html",           reports_hub()),
        ("reports_step1_agg.html",     step1_agg()),
        ("reports_step2_roi.html",     step2_roi()),
        ("reports_step3_compose.html", step3_compose()),
        ("reports_step4_preview.html", step4_preview()),
        ("reports_step5_send.html",    step5_send()),
    ]

    for fname, html in files:
        path = OUT_DIR / fname
        path.write_text(html, encoding="utf-8")
        print(f"✓ {path}")

    print("\n📌 Abriendo en el navegador:")
    for fname, _ in files:
        url = f"http://localhost:3000/enterprise/reports/{fname}"
        webbrowser.open(url)
        print(f"   {url}")


if __name__ == "__main__":
    main()
