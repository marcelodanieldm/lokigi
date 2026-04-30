"""
Renderiza el flujo "Publicación Masiva" (Bulk Actions) del Plan Enterprise
como páginas HTML estáticas en frontend/static/enterprise/bulk/

Pasos del flujo:
  1. bulk_hub.html            — Dashboard Hub: lista de campañas activas / historial
  2. bulk_step1_compose.html  — Creación centralizada: redactar post / subir foto
  3. bulk_step2_segment.html  — Segmentación por etiquetas, ciudad, horario
  4. bulk_step3_preview.html  — Vista previa de cómo quedará en cada perfil GBP
  5. bulk_step4_publish.html  — Lanzamiento: worker Celery en cascada (progress live)
  6. bulk_step5_report.html   — Informe de resultados: éxito / fallo / reintento
"""
from __future__ import annotations
import webbrowser
from pathlib import Path

ROOT = Path(__file__).parent
OUT_DIR = ROOT / "frontend" / "static" / "enterprise" / "bulk"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# ─── NAV ─────────────────────────────────────────────────────────────────────

PAGES = [
    ("bulk_hub.html",           "🗂 Hub"),
    ("bulk_step1_compose.html", "1 · Redactar"),
    ("bulk_step2_segment.html", "2 · Segmentar"),
    ("bulk_step3_preview.html", "3 · Preview"),
    ("bulk_step4_publish.html", "4 · Publicar"),
    ("bulk_step5_report.html",  "5 · Resultados"),
]


def nav_bar(active: str) -> str:
    links = ""
    for href, label in PAGES:
        is_active = href == active
        cls = (
            "px-3 py-2 rounded-lg text-sm font-semibold text-violet-200 bg-violet-500/20 border border-violet-400/20 no-underline"
            if is_active else
            "px-3 py-2 rounded-lg text-sm font-medium text-stone-400 hover:text-white hover:bg-white/5 no-underline"
        )
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
    <span class="text-stone-400 text-xs font-semibold">Publicación Masiva</span>
  </div>
  {links}
</nav>"""


def page(title: str, active: str, body: str) -> str:
    return f"""<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{title} | Bulk Publish · Lokigi Enterprise</title>
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
      50%  {{ opacity: .5; transform: scale(1.4); }}
    }}
    .pulse-dot {{ animation: pulse-dot 1.2s ease-in-out infinite; }}
    input, select, textarea {{
      background: rgba(255,255,255,.05);
      border: 1px solid rgba(255,255,255,.12);
      border-radius: 10px;
      color: #f1f5f9;
      padding: 10px 14px;
      font-size: 14px;
      width: 100%;
      outline: none;
      transition: border-color .15s;
    }}
    input:focus, select:focus, textarea:focus {{
      border-color: rgba(167,139,250,.6);
      box-shadow: 0 0 0 3px rgba(139,92,246,.15);
    }}
    textarea {{ resize: vertical; min-height: 110px; }}
    select option {{ background: #1c1917; }}
    .tag {{
      display: inline-flex; align-items: center; gap: 6px;
      padding: 5px 12px; border-radius: 20px; font-size: 12px; font-weight: 700;
      border: 1px solid rgba(255,255,255,.12); cursor: pointer;
      transition: all .15s;
    }}
    .tag.selected {{
      background: rgba(139,92,246,.25);
      border-color: rgba(139,92,246,.5);
      color: #c4b5fd;
    }}
    .tag:not(.selected) {{
      background: rgba(255,255,255,.04);
      color: #94a3b8;
    }}
  </style>
</head>
<body class="min-h-screen bg-stone-950 text-stone-100">
{nav_bar(active)}
{body}
</body>
</html>"""


# ─── HUB ─────────────────────────────────────────────────────────────────────

def bulk_hub() -> str:
    campaigns = [
        {"name": "Black Friday 2026", "status": "draft",    "locations": 50, "scheduled": "28 Nov 09:00", "type": "post",  "color": "amber"},
        {"name": "Apertura Sevilla",  "status": "success",  "locations": 3,  "scheduled": "15 Abr 10:00", "type": "photo", "color": "emerald"},
        {"name": "Promo Verano",      "status": "partial",  "locations": 22, "scheduled": "1 Jun 08:00",  "type": "post",  "color": "amber"},
        {"name": "Actualiz. Horario", "status": "success",  "locations": 50, "scheduled": "1 Ene 00:01",  "type": "info",  "color": "emerald"},
        {"name": "Cierre Agosto",     "status": "failed",   "locations": 7,  "scheduled": "31 Jul 18:00", "type": "info",  "color": "rose"},
    ]

    STATUS_BADGE = {
        "draft":   '<span class="px-2.5 py-1 rounded-full bg-stone-500/20 text-stone-300 text-xs font-bold">Borrador</span>',
        "success": '<span class="px-2.5 py-1 rounded-full bg-emerald-500/15 text-emerald-300 text-xs font-bold">Completado</span>',
        "partial": '<span class="px-2.5 py-1 rounded-full bg-amber-500/15 text-amber-300 text-xs font-bold">Parcial</span>',
        "failed":  '<span class="px-2.5 py-1 rounded-full bg-rose-500/15 text-rose-300 text-xs font-bold">Fallido</span>',
    }
    TYPE_ICON = {"post": "📝", "photo": "🖼️", "info": "ℹ️"}

    rows = ""
    for c in campaigns:
        rows += f"""
        <tr class="border-b border-white/5 hover:bg-white/3">
          <td class="py-3 pl-6 pr-4">
            <span class="text-lg mr-1">{TYPE_ICON[c['type']]}</span>
            <span class="font-semibold text-stone-100 text-sm">{c['name']}</span>
          </td>
          <td class="py-3 pr-4 text-center font-bold text-stone-200">{c['locations']}</td>
          <td class="py-3 pr-4 text-sm text-stone-400">{c['scheduled']}</td>
          <td class="py-3 pr-4">{STATUS_BADGE[c['status']]}</td>
          <td class="py-3 pr-6">
            <a href="bulk_step1_compose.html"
               class="px-3 py-1.5 rounded-lg border border-white/10 bg-white/5
                      text-xs text-stone-400 hover:text-stone-200 hover:bg-white/10 no-underline">
              {'Editar' if c['status'] == 'draft' else 'Ver detalle'}
            </a>
          </td>
        </tr>"""

    body = f"""
<div class="mx-auto max-w-5xl px-4 py-10 sm:px-6 pb-20 fade-up">

  <div class="flex items-start justify-between gap-4 mb-8 flex-wrap">
    <div>
      <p class="text-xs uppercase tracking-[.2em] text-violet-300/70 mb-1">Enterprise · Publicación Masiva</p>
      <h1 class="text-3xl font-bold text-white">Dashboard Hub</h1>
      <p class="mt-1 text-stone-400 text-sm max-w-xl">
        Centraliza todas las publicaciones masivas de tu agencia. Un mensaje, 50 perfiles de Google Business Profile actualizados en simultáneo.
      </p>
    </div>
    <a href="bulk_step1_compose.html"
       class="px-6 py-3 rounded-2xl bg-gradient-to-r from-violet-600 to-indigo-600
              text-white font-bold text-sm hover:from-violet-500 hover:to-indigo-500 no-underline self-start">
      + Nueva campaña
    </a>
  </div>

  <!-- KPIs -->
  <div class="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-8">
    <div class="rounded-2xl border border-white/10 bg-white/5 p-4 text-center">
      <p class="text-3xl font-black text-white">132</p>
      <p class="text-xs uppercase tracking-wider text-stone-400 mt-1">Publicaciones totales</p>
    </div>
    <div class="rounded-2xl border border-emerald-500/20 bg-emerald-500/5 p-4 text-center">
      <p class="text-3xl font-black text-emerald-300">98.2%</p>
      <p class="text-xs uppercase tracking-wider text-stone-400 mt-1">Tasa de éxito</p>
    </div>
    <div class="rounded-2xl border border-white/10 bg-white/5 p-4 text-center">
      <p class="text-3xl font-black text-white">3.1 s</p>
      <p class="text-xs uppercase tracking-wider text-stone-400 mt-1">Tiempo medio / loc.</p>
    </div>
    <div class="rounded-2xl border border-violet-500/20 bg-violet-500/5 p-4 text-center">
      <p class="text-3xl font-black text-violet-300">50</p>
      <p class="text-xs uppercase tracking-wider text-stone-400 mt-1">Máx. locales / campaña</p>
    </div>
  </div>

  <!-- Campaigns table -->
  <div class="rounded-3xl border border-white/10 bg-white/5 overflow-hidden mb-6">
    <div class="flex items-center justify-between px-6 py-4 border-b border-white/10">
      <h2 class="text-base font-semibold text-white m-0">Campañas recientes</h2>
      <div class="flex gap-2">
        <select class="w-36 text-xs py-2 px-3">
          <option>Todos los estados</option>
          <option>Borrador</option>
          <option>Completado</option>
          <option>Fallido</option>
        </select>
      </div>
    </div>
    <div class="overflow-x-auto">
      <table class="min-w-full text-sm">
        <thead>
          <tr class="border-b border-white/10 text-stone-400 text-xs uppercase tracking-wider">
            <th class="py-3 pr-4 pl-6 text-left font-semibold">Campaña</th>
            <th class="py-3 pr-4 text-center font-semibold">Locales</th>
            <th class="py-3 pr-4 text-left font-semibold">Programado</th>
            <th class="py-3 pr-4 text-left font-semibold">Estado</th>
            <th class="py-3 pr-6 text-left font-semibold">Acción</th>
          </tr>
        </thead>
        <tbody class="text-stone-200">
          {rows}
        </tbody>
      </table>
    </div>
  </div>

  <!-- How it works -->
  <div class="rounded-3xl border border-violet-500/15 bg-violet-500/5 p-6">
    <h3 class="text-base font-bold text-white mb-5">¿Cómo funciona?</h3>
    <div class="grid grid-cols-1 sm:grid-cols-4 gap-4">
      <div class="text-center">
        <div class="w-12 h-12 rounded-2xl bg-violet-500/20 flex items-center justify-center text-2xl mx-auto mb-3">✍️</div>
        <p class="text-sm font-semibold text-white mb-1">1. Redactas</p>
        <p class="text-xs text-stone-400">Un post, foto o actualización de info desde el Hub</p>
      </div>
      <div class="text-center">
        <div class="w-12 h-12 rounded-2xl bg-indigo-500/20 flex items-center justify-center text-2xl mx-auto mb-3">🏷️</div>
        <p class="text-sm font-semibold text-white mb-1">2. Segmentas</p>
        <p class="text-xs text-stone-400">Elige etiquetas: ciudad, tipo de local, tenant</p>
      </div>
      <div class="text-center">
        <div class="w-12 h-12 rounded-2xl bg-sky-500/20 flex items-center justify-center text-2xl mx-auto mb-3">⚡</div>
        <p class="text-sm font-semibold text-white mb-1">3. Celery dispara</p>
        <p class="text-xs text-stone-400">Worker en cascada: 50 tareas en paralelo vía GBP API</p>
      </div>
      <div class="text-center">
        <div class="w-12 h-12 rounded-2xl bg-emerald-500/20 flex items-center justify-center text-2xl mx-auto mb-3">📊</div>
        <p class="text-sm font-semibold text-white mb-1">4. Validas</p>
        <p class="text-xs text-stone-400">Reporte en tiempo real: éxito / fallo / reintento</p>
      </div>
    </div>
  </div>

</div>"""
    return page("Hub de Campañas", "bulk_hub.html", body)


# ─── STEP 1 — Redactar ───────────────────────────────────────────────────────

def step1_compose() -> str:
    body = """
<div class="mx-auto max-w-3xl px-4 py-10 sm:px-6 pb-20 fade-up">

  <div class="mb-8">
    <p class="text-xs uppercase tracking-[.2em] text-violet-300/70 mb-1">Publicación Masiva · Paso 1 de 4</p>
    <h1 class="text-3xl font-bold text-white">Creación Centralizada</h1>
    <p class="mt-1 text-stone-400 text-sm">
      Redacta el contenido una sola vez. Se desplegará en todos los perfiles GBP seleccionados.
    </p>
  </div>

  <!-- Progress -->
  <div class="flex gap-2 mb-10">
    <div class="h-1.5 flex-1 rounded-full bg-violet-500"></div>
    <div class="h-1.5 flex-1 rounded-full bg-white/10"></div>
    <div class="h-1.5 flex-1 rounded-full bg-white/10"></div>
    <div class="h-1.5 flex-1 rounded-full bg-white/10"></div>
  </div>

  <!-- Type selector -->
  <div class="rounded-3xl border border-white/10 bg-white/5 p-6 mb-5">
    <h2 class="text-base font-semibold text-white mb-4">Tipo de publicación</h2>
    <div class="grid grid-cols-1 sm:grid-cols-3 gap-3">

      <label class="flex flex-col items-center gap-3 p-5 rounded-2xl border-2 border-violet-500/50
                    bg-violet-500/10 cursor-pointer">
        <input type="radio" name="type" class="hidden" />
        <span class="text-3xl">📝</span>
        <div class="text-center">
          <p class="text-sm font-bold text-violet-200">Post / Novedad</p>
          <p class="text-xs text-stone-400 mt-1">Texto + imagen opcional. Aparece en la ficha GBP.</p>
        </div>
        <span class="px-3 py-1 rounded-full bg-violet-500/30 text-violet-200 text-xs font-bold">Seleccionado</span>
      </label>

      <label class="flex flex-col items-center gap-3 p-5 rounded-2xl border border-white/10
                    bg-white/3 cursor-pointer hover:bg-white/6">
        <input type="radio" name="type" class="hidden" />
        <span class="text-3xl">🖼️</span>
        <div class="text-center">
          <p class="text-sm font-bold text-stone-200">Foto / Galería</p>
          <p class="text-xs text-stone-400 mt-1">Actualiza la foto de portada o añade a galería.</p>
        </div>
        <span class="px-3 py-1 rounded-full bg-stone-500/20 text-stone-400 text-xs font-bold">Seleccionar</span>
      </label>

      <label class="flex flex-col items-center gap-3 p-5 rounded-2xl border border-white/10
                    bg-white/3 cursor-pointer hover:bg-white/6">
        <input type="radio" name="type" class="hidden" />
        <span class="text-3xl">ℹ️</span>
        <div class="text-center">
          <p class="text-sm font-bold text-stone-200">Info del negocio</p>
          <p class="text-xs text-stone-400 mt-1">Horario, teléfono, URL o atributos especiales.</p>
        </div>
        <span class="px-3 py-1 rounded-full bg-stone-500/20 text-stone-400 text-xs font-bold">Seleccionar</span>
      </label>

    </div>
  </div>

  <!-- Content form -->
  <div class="rounded-3xl border border-white/10 bg-white/5 p-6 mb-5">
    <h2 class="text-base font-semibold text-white mb-4">Contenido del post</h2>
    <div class="space-y-4">
      <div>
        <label class="block text-xs text-stone-400 font-semibold uppercase tracking-wider mb-2">Título (opcional)</label>
        <input type="text" value="🖤 Black Friday — 30% en todos los menús" />
      </div>
      <div>
        <label class="block text-xs text-stone-400 font-semibold uppercase tracking-wider mb-2">Cuerpo del mensaje <span class="text-stone-600">(máx. 1.500 caracteres)</span></label>
        <textarea>¡Llega nuestro Black Friday más especial! 🎉

Del 28 al 30 de noviembre, disfruta de un 30 % de descuento en toda la carta en cualquiera de nuestros locales. Muestra este post en caja y el descuento se aplica automáticamente.

📍 Válido en todos nuestros restaurantes.
⏰ Solo durante el periodo indicado.

¡Te esperamos!</textarea>
        <div class="flex justify-between mt-1">
          <span class="text-xs text-stone-600">0 variables disponibles: {nombre_local}, {ciudad}, {rating}</span>
          <span class="text-xs text-stone-500">247 / 1.500</span>
        </div>
      </div>

      <!-- Variables hint -->
      <div class="rounded-2xl border border-indigo-500/20 bg-indigo-500/5 p-4">
        <p class="text-xs font-bold text-indigo-300 uppercase tracking-wider mb-2">💡 Variables dinámicas</p>
        <p class="text-stone-400 text-sm mb-3">
          Personaliza el mensaje por local usando variables. Se sustituyen automáticamente al publicar.
        </p>
        <div class="flex flex-wrap gap-2">
          <span class="px-3 py-1.5 rounded-lg bg-indigo-500/15 border border-indigo-500/20 text-indigo-300 text-xs font-mono cursor-pointer hover:bg-indigo-500/25">{nombre_local}</span>
          <span class="px-3 py-1.5 rounded-lg bg-indigo-500/15 border border-indigo-500/20 text-indigo-300 text-xs font-mono cursor-pointer hover:bg-indigo-500/25">{ciudad}</span>
          <span class="px-3 py-1.5 rounded-lg bg-indigo-500/15 border border-indigo-500/20 text-indigo-300 text-xs font-mono cursor-pointer hover:bg-indigo-500/25">{rating_actual}</span>
          <span class="px-3 py-1.5 rounded-lg bg-indigo-500/15 border border-indigo-500/20 text-indigo-300 text-xs font-mono cursor-pointer hover:bg-indigo-500/25">{direccion}</span>
          <span class="px-3 py-1.5 rounded-lg bg-indigo-500/15 border border-indigo-500/20 text-indigo-300 text-xs font-mono cursor-pointer hover:bg-indigo-500/25">{telefono}</span>
        </div>
      </div>

      <!-- Image upload -->
      <div>
        <label class="block text-xs text-stone-400 font-semibold uppercase tracking-wider mb-2">Imagen adjunta (opcional)</label>
        <div class="border-2 border-dashed border-white/15 rounded-2xl p-6 flex items-center gap-5 cursor-pointer hover:border-violet-400/40 transition">
          <div class="w-14 h-14 rounded-2xl bg-white/8 flex items-center justify-center text-2xl flex-shrink-0">🖼️</div>
          <div>
            <p class="text-stone-300 font-semibold text-sm mb-1">Arrastra la imagen aquí o haz click</p>
            <p class="text-stone-500 text-xs">JPG, PNG, WebP · máx. 5 MB · recomendado 1200×628 px</p>
          </div>
        </div>
      </div>

      <!-- CTA -->
      <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div>
          <label class="block text-xs text-stone-400 font-semibold uppercase tracking-wider mb-2">Botón de llamada a la acción</label>
          <select>
            <option>Sin botón</option>
            <option selected>Más información</option>
            <option>Reservar</option>
            <option>Pedir online</option>
            <option>Llamar ahora</option>
          </select>
        </div>
        <div>
          <label class="block text-xs text-stone-400 font-semibold uppercase tracking-wider mb-2">URL del botón</label>
          <input type="url" value="https://miagencia.com/black-friday" />
        </div>
      </div>
    </div>
  </div>

  <!-- Schedule -->
  <div class="rounded-3xl border border-white/10 bg-white/5 p-6 mb-5">
    <h2 class="text-base font-semibold text-white mb-4">Programación</h2>
    <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
      <div>
        <label class="block text-xs text-stone-400 font-semibold uppercase tracking-wider mb-2">Fecha de publicación</label>
        <input type="date" value="2026-11-28" />
      </div>
      <div>
        <label class="block text-xs text-stone-400 font-semibold uppercase tracking-wider mb-2">Hora (zona horaria de cada local)</label>
        <input type="time" value="09:00" />
      </div>
      <div>
        <label class="block text-xs text-stone-400 font-semibold uppercase tracking-wider mb-2">Fecha de expiración (opcional)</label>
        <input type="date" value="2026-11-30" />
      </div>
      <div class="flex items-end pb-0.5">
        <label class="flex items-center gap-3 cursor-pointer">
          <div class="w-10 h-5 rounded-full bg-violet-600 relative">
            <div class="absolute right-0.5 top-0.5 w-4 h-4 rounded-full bg-white shadow"></div>
          </div>
          <span class="text-sm text-stone-300 font-semibold">Respetar horas de apertura de cada local</span>
        </label>
      </div>
    </div>
  </div>

  <!-- Navigation -->
  <div class="flex justify-between items-center mt-8">
    <a href="bulk_hub.html"
       class="px-5 py-3 rounded-2xl border border-white/10 bg-white/5
              text-stone-300 font-semibold text-sm hover:bg-white/10 no-underline">
      ← Hub
    </a>
    <a href="bulk_step2_segment.html"
       class="px-8 py-3 rounded-2xl bg-gradient-to-r from-violet-600 to-indigo-600
              text-white font-bold text-sm hover:from-violet-500 hover:to-indigo-500 no-underline">
      Siguiente: Segmentar locales →
    </a>
  </div>
</div>"""
    return page("Paso 1 — Crear contenido", "bulk_step1_compose.html", body)


# ─── STEP 2 — Segmentación ───────────────────────────────────────────────────

def step2_segment() -> str:
    body = """
<div class="mx-auto max-w-4xl px-4 py-10 sm:px-6 pb-20 fade-up">

  <div class="mb-8">
    <p class="text-xs uppercase tracking-[.2em] text-violet-300/70 mb-1">Publicación Masiva · Paso 2 de 4</p>
    <h1 class="text-3xl font-bold text-white">Segmentación de Locales</h1>
    <p class="mt-1 text-stone-400 text-sm">
      Elige exactamente qué locales recibirán la publicación usando etiquetas, ciudad o tenant.
    </p>
  </div>

  <!-- Progress -->
  <div class="flex gap-2 mb-10">
    <div class="h-1.5 flex-1 rounded-full bg-violet-500"></div>
    <div class="h-1.5 flex-1 rounded-full bg-violet-500"></div>
    <div class="h-1.5 flex-1 rounded-full bg-white/10"></div>
    <div class="h-1.5 flex-1 rounded-full bg-white/10"></div>
  </div>

  <div class="grid grid-cols-1 lg:grid-cols-[3fr_2fr] gap-5">

    <!-- LEFT -->
    <div class="space-y-5">

      <!-- Tenant filter -->
      <div class="rounded-3xl border border-white/10 bg-white/5 p-6">
        <h2 class="text-base font-semibold text-white mb-4">Filtrar por Tenant</h2>
        <div class="flex flex-wrap gap-2">
          <span class="tag selected">✓ Todos los tenants</span>
          <span class="tag">Cadena Pizzas Norte</span>
          <span class="tag">Franquicia Café Rápido</span>
          <span class="tag">Restaurantes El Mar</span>
          <span class="tag">Hoteles Solimar</span>
        </div>
      </div>

      <!-- Location tags -->
      <div class="rounded-3xl border border-white/10 bg-white/5 p-6">
        <div class="flex items-center justify-between mb-4">
          <h2 class="text-base font-semibold text-white m-0">Etiquetas de locales</h2>
          <button class="px-3 py-1.5 rounded-lg bg-violet-600/30 border border-violet-500/20
                         text-violet-300 text-xs font-semibold hover:bg-violet-600/50">
            + Nueva etiqueta
          </button>
        </div>
        <div class="flex flex-wrap gap-2 mb-4">
          <span class="tag selected">✓ Todos los locales (50)</span>
          <span class="tag">Con terraza (18)</span>
          <span class="tag">Drive-thru (7)</span>
          <span class="tag">Apertura reciente (4)</span>
          <span class="tag">Alta demanda (12)</span>
          <span class="tag">Rating &lt; 4.0 (9)</span>
          <span class="tag">Franquicia Gold (6)</span>
        </div>
        <p class="text-xs text-stone-500">
          💡 Las etiquetas se asignan desde el panel de ubicaciones (Paso 3 del flujo Enterprise).
        </p>
      </div>

      <!-- City filter -->
      <div class="rounded-3xl border border-white/10 bg-white/5 p-6">
        <h2 class="text-base font-semibold text-white mb-4">Filtrar por Ciudad</h2>
        <div class="flex flex-wrap gap-2">
          <span class="tag selected">✓ Todas las ciudades</span>
          <span class="tag">Madrid (28)</span>
          <span class="tag">Barcelona (9)</span>
          <span class="tag">Sevilla (6)</span>
          <span class="tag">Marbella (3)</span>
          <span class="tag">Valencia (4)</span>
        </div>
      </div>

      <!-- Advanced -->
      <div class="rounded-3xl border border-white/10 bg-white/5 p-6">
        <h2 class="text-base font-semibold text-white mb-4">Filtros avanzados</h2>
        <div class="space-y-3">
          <div class="flex items-center justify-between py-2.5 border-b border-white/5">
            <div>
              <p class="text-sm font-semibold text-stone-200">Solo locales con GBP verificado</p>
              <p class="text-xs text-stone-500">Excluye fichas pendientes de verificación</p>
            </div>
            <label class="flex items-center cursor-pointer">
              <div class="w-10 h-5 rounded-full bg-violet-600 relative">
                <div class="absolute right-0.5 top-0.5 w-4 h-4 rounded-full bg-white shadow"></div>
              </div>
            </label>
          </div>
          <div class="flex items-center justify-between py-2.5 border-b border-white/5">
            <div>
              <p class="text-sm font-semibold text-stone-200">Excluir locales con alerta activa</p>
              <p class="text-xs text-stone-500">Evita publicar en locales con problemas pendientes</p>
            </div>
            <label class="flex items-center cursor-pointer">
              <div class="w-10 h-5 rounded-full bg-stone-700 relative">
                <div class="absolute left-0.5 top-0.5 w-4 h-4 rounded-full bg-stone-400 shadow"></div>
              </div>
            </label>
          </div>
          <div class="flex items-center justify-between py-2.5">
            <div>
              <p class="text-sm font-semibold text-stone-200">Excluir locales temporalmente cerrados</p>
              <p class="text-xs text-stone-500">No publica en fichas con estado "cerrado temporalmente"</p>
            </div>
            <label class="flex items-center cursor-pointer">
              <div class="w-10 h-5 rounded-full bg-violet-600 relative">
                <div class="absolute right-0.5 top-0.5 w-4 h-4 rounded-full bg-white shadow"></div>
              </div>
            </label>
          </div>
        </div>
      </div>

    </div>
    <!-- END LEFT -->

    <!-- RIGHT: Live selection summary -->
    <div class="space-y-5">
      <div class="rounded-3xl border border-violet-500/25 bg-violet-500/8 p-6 sticky top-20">
        <p class="text-xs uppercase tracking-[.2em] text-violet-300/70 mb-4">Resumen de selección</p>

        <div class="text-center mb-6">
          <p class="text-6xl font-black text-white">50</p>
          <p class="text-stone-400 text-sm mt-1">locales seleccionados</p>
        </div>

        <div class="space-y-3 mb-6">
          <div class="flex justify-between text-sm">
            <span class="text-stone-400">Tenants cubiertos</span>
            <span class="text-white font-bold">4 / 4</span>
          </div>
          <div class="flex justify-between text-sm">
            <span class="text-stone-400">Ciudades</span>
            <span class="text-white font-bold">5</span>
          </div>
          <div class="flex justify-between text-sm">
            <span class="text-stone-400">Con GBP verificado</span>
            <span class="text-emerald-300 font-bold">50 / 50</span>
          </div>
          <div class="flex justify-between text-sm">
            <span class="text-stone-400">Con alerta activa</span>
            <span class="text-amber-300 font-bold">6 (excluidos)</span>
          </div>
          <div class="flex justify-between text-sm border-t border-white/10 pt-3">
            <span class="text-stone-300 font-semibold">Total a publicar</span>
            <span class="text-white font-black">44 locales</span>
          </div>
        </div>

        <!-- Mini location list preview -->
        <div class="rounded-2xl border border-white/10 bg-black/20 p-4 max-h-48 overflow-y-auto mb-5">
          <p class="text-xs text-stone-500 uppercase tracking-wider mb-3">Vista previa</p>
          <div class="space-y-2 text-xs">
            <div class="flex gap-2 items-center"><span class="w-2 h-2 rounded-full bg-emerald-400"></span><span class="text-stone-300">Pizza Norte — Malasaña · Madrid</span></div>
            <div class="flex gap-2 items-center"><span class="w-2 h-2 rounded-full bg-emerald-400"></span><span class="text-stone-300">Pizza Norte — Chamberí · Madrid</span></div>
            <div class="flex gap-2 items-center"><span class="w-2 h-2 rounded-full bg-emerald-400"></span><span class="text-stone-300">Café Rápido — Gran Vía · Madrid</span></div>
            <div class="flex gap-2 items-center"><span class="w-2 h-2 rounded-full bg-emerald-400"></span><span class="text-stone-300">Café Rápido — Retiro · Madrid</span></div>
            <div class="flex gap-2 items-center"><span class="w-2 h-2 rounded-full bg-emerald-400"></span><span class="text-stone-300">El Mar — Barceloneta · Barcelona</span></div>
            <div class="flex gap-2 items-center"><span class="w-2 h-2 rounded-full bg-amber-400"></span><span class="text-stone-400 line-through">Hotel Solimar Marbella · (alerta)</span></div>
            <div class="flex items-center justify-center py-2">
              <span class="text-stone-600 text-xs">+ 38 más...</span>
            </div>
          </div>
        </div>

        <div class="rounded-2xl border border-amber-500/20 bg-amber-500/5 p-3 mb-5">
          <p class="text-xs text-amber-300 font-semibold">⚠️ 6 locales excluidos por alerta activa</p>
          <p class="text-xs text-stone-500 mt-1">Puedes revisarlos en la vista de ubicaciones antes de continuar.</p>
        </div>

        <a href="bulk_step3_preview.html"
           class="flex items-center justify-center w-full px-6 py-3 rounded-2xl
                  bg-gradient-to-r from-violet-600 to-indigo-600
                  text-white font-bold text-sm hover:from-violet-500 hover:to-indigo-500 no-underline">
          Confirmar y previsualizar →
        </a>
      </div>
    </div>

  </div>

  <!-- Navigation -->
  <div class="flex justify-between items-center mt-8">
    <a href="bulk_step1_compose.html"
       class="px-5 py-3 rounded-2xl border border-white/10 bg-white/5
              text-stone-300 font-semibold text-sm hover:bg-white/10 no-underline">
      ← Atrás
    </a>
    <a href="bulk_step3_preview.html"
       class="px-8 py-3 rounded-2xl bg-gradient-to-r from-violet-600 to-indigo-600
              text-white font-bold text-sm hover:from-violet-500 hover:to-indigo-500 no-underline">
      Vista previa →
    </a>
  </div>
</div>"""
    return page("Paso 2 — Segmentación", "bulk_step2_segment.html", body)


# ─── STEP 3 — Preview ────────────────────────────────────────────────────────

def step3_preview() -> str:
    body = """
<div class="mx-auto max-w-4xl px-4 py-10 sm:px-6 pb-20 fade-up">

  <div class="mb-8">
    <p class="text-xs uppercase tracking-[.2em] text-violet-300/70 mb-1">Publicación Masiva · Paso 3 de 4</p>
    <h1 class="text-3xl font-bold text-white">Vista Previa</h1>
    <p class="mt-1 text-stone-400 text-sm">
      Así quedará el post en Google Business Profile. Verifica que el contenido y las variables dinámicas son correctas antes de publicar.
    </p>
  </div>

  <!-- Progress -->
  <div class="flex gap-2 mb-10">
    <div class="h-1.5 flex-1 rounded-full bg-violet-500"></div>
    <div class="h-1.5 flex-1 rounded-full bg-violet-500"></div>
    <div class="h-1.5 flex-1 rounded-full bg-violet-500"></div>
    <div class="h-1.5 flex-1 rounded-full bg-white/10"></div>
  </div>

  <!-- Preview tabs -->
  <div class="flex gap-2 mb-5">
    <button class="px-4 py-2 rounded-xl bg-violet-600/30 border border-violet-500/30
                   text-violet-200 text-sm font-semibold">Vista de ficha GBP</button>
    <button class="px-4 py-2 rounded-xl border border-white/10 bg-white/5
                   text-stone-400 text-sm font-semibold hover:bg-white/10">Vista móvil</button>
    <button class="px-4 py-2 rounded-xl border border-white/10 bg-white/5
                   text-stone-400 text-sm font-semibold hover:bg-white/10">Vista desktop</button>
  </div>

  <div class="grid grid-cols-1 lg:grid-cols-[2fr_3fr] gap-5 mb-8">

    <!-- Local selector -->
    <div class="rounded-3xl border border-white/10 bg-white/5 p-5">
      <h2 class="text-base font-semibold text-white mb-1">Seleccionar local</h2>
      <p class="text-xs text-stone-500 mb-4">Previsualiza cómo quedaría en cada ficha individual</p>
      <div class="space-y-2">
        <div class="flex items-center gap-3 p-3 rounded-2xl bg-violet-500/15 border border-violet-500/25 cursor-pointer">
          <span class="w-2.5 h-2.5 rounded-full bg-violet-400 flex-shrink-0"></span>
          <div>
            <p class="text-sm font-semibold text-white">Pizza Norte — Malasaña</p>
            <p class="text-xs text-stone-400">Madrid · rating: 4.5★</p>
          </div>
        </div>
        <div class="flex items-center gap-3 p-3 rounded-2xl border border-white/10 bg-white/3 cursor-pointer hover:bg-white/6">
          <span class="w-2.5 h-2.5 rounded-full bg-stone-500 flex-shrink-0"></span>
          <div>
            <p class="text-sm font-semibold text-stone-200">Café Rápido — Gran Vía</p>
            <p class="text-xs text-stone-400">Madrid · rating: 4.4★</p>
          </div>
        </div>
        <div class="flex items-center gap-3 p-3 rounded-2xl border border-white/10 bg-white/3 cursor-pointer hover:bg-white/6">
          <span class="w-2.5 h-2.5 rounded-full bg-stone-500 flex-shrink-0"></span>
          <div>
            <p class="text-sm font-semibold text-stone-200">El Mar — Barceloneta</p>
            <p class="text-xs text-stone-400">Barcelona · rating: 4.8★</p>
          </div>
        </div>
        <div class="text-center py-2">
          <span class="text-stone-600 text-xs">+ 41 más</span>
        </div>
      </div>
    </div>

    <!-- GBP preview mockup -->
    <div class="rounded-3xl border border-white/10 bg-white/5 p-5">
      <div class="flex items-center gap-2 mb-4">
        <div class="w-3 h-3 rounded-full bg-rose-500"></div>
        <div class="w-3 h-3 rounded-full bg-amber-500"></div>
        <div class="w-3 h-3 rounded-full bg-emerald-500"></div>
        <div class="flex-1 mx-3 bg-white/10 rounded-md px-3 py-1 text-xs text-stone-500 font-mono">
          google.com/maps/place/pizza-norte-malasana
        </div>
      </div>

      <!-- Simulated GBP post card -->
      <div class="rounded-2xl bg-white p-4 shadow-xl">
        <!-- Business header -->
        <div class="flex items-center gap-3 mb-4">
          <div class="w-12 h-12 rounded-full bg-gradient-to-br from-violet-500 to-indigo-600
                      flex items-center justify-center text-white font-bold text-lg">🍕</div>
          <div>
            <p class="font-bold text-stone-900 text-sm">Pizza Norte — Malasaña</p>
            <p class="text-stone-500 text-xs">Publicado por el propietario · hace unos momentos</p>
          </div>
        </div>
        <!-- Image mockup -->
        <div class="w-full h-36 rounded-xl bg-gradient-to-br from-amber-400 via-orange-500 to-red-600
                    flex items-center justify-center mb-3">
          <span class="text-white font-black text-2xl text-center px-4">🖤 BLACK FRIDAY</span>
        </div>
        <!-- Post text -->
        <p class="text-stone-800 text-sm leading-relaxed mb-3">
          ¡Llega nuestro Black Friday más especial! 🎉<br><br>
          Del 28 al 30 de noviembre, disfruta de un 30 % de descuento en toda la carta en
          <strong>Pizza Norte — Malasaña</strong>, en el corazón de Madrid.
          Muestra este post en caja y el descuento se aplica automáticamente.<br><br>
          📍 Válido en nuestro local de Malasaña.<br>
          ⏰ Solo durante el periodo indicado.
        </p>
        <!-- CTA button -->
        <div class="flex justify-center">
          <div class="px-6 py-2.5 rounded-full border-2 border-blue-600 text-blue-600 text-sm font-bold">
            Más información
          </div>
        </div>
      </div>

      <div class="mt-4 flex items-center gap-2">
        <span class="w-2 h-2 rounded-full bg-emerald-400"></span>
        <p class="text-xs text-emerald-300 font-semibold">Variables sustituidas correctamente</p>
      </div>
    </div>

  </div>

  <!-- Summary before publish -->
  <div class="rounded-3xl border border-white/10 bg-white/5 p-6 mb-6">
    <h2 class="text-base font-semibold text-white mb-4">Resumen antes de publicar</h2>
    <div class="grid grid-cols-2 sm:grid-cols-4 gap-4 text-center">
      <div><p class="text-2xl font-black text-white">44</p><p class="text-xs text-stone-400 mt-1">Locales destino</p></div>
      <div><p class="text-2xl font-black text-emerald-300">50</p><p class="text-xs text-stone-400 mt-1">Verificados GBP</p></div>
      <div><p class="text-2xl font-black text-white">28 Nov</p><p class="text-xs text-stone-400 mt-1">Fecha publicación</p></div>
      <div><p class="text-2xl font-black text-violet-300">09:00</p><p class="text-xs text-stone-400 mt-1">Hora programada</p></div>
    </div>
  </div>

  <!-- Navigation -->
  <div class="flex justify-between items-center">
    <a href="bulk_step2_segment.html"
       class="px-5 py-3 rounded-2xl border border-white/10 bg-white/5
              text-stone-300 font-semibold text-sm hover:bg-white/10 no-underline">
      ← Ajustar segmentación
    </a>
    <a href="bulk_step4_publish.html"
       class="px-8 py-3 rounded-2xl bg-gradient-to-r from-violet-600 to-indigo-600
              text-white font-bold text-sm hover:from-violet-500 hover:to-indigo-500 no-underline">
      Confirmar y publicar →
    </a>
  </div>
</div>"""
    return page("Paso 3 — Vista Previa", "bulk_step3_preview.html", body)


# ─── STEP 4 — Publicación / Worker Celery ────────────────────────────────────

def step4_publish() -> str:
    # Mock locations with simulated task results
    locs = [
        ("Pizza Norte — Malasaña",         "ok"),
        ("Pizza Norte — Chamberí",          "ok"),
        ("Pizza Norte — Vallecas",          "ok"),
        ("Pizza Norte — Getafe",            "ok"),
        ("Café Rápido — Gran Vía",          "ok"),
        ("Café Rápido — Retiro",            "ok"),
        ("Café Rápido — Atocha",            "ok"),
        ("Café Rápido — Leganés",           "ok"),
        ("Café Rápido — Alcorcón",          "ok"),
        ("El Mar — Barceloneta",            "ok"),
        ("El Mar — Diagonal",               "ok"),
        ("El Mar — Sarrià",                 "error"),
        ("El Mar — Gràcia",                 "ok"),
        ("Café Rápido — Getafe Centro",     "ok"),
        ("Pizza Norte — Arganzuela",        "error"),
        ("Café Rápido — Majadahonda",       "ok"),
        ("Café Rápido — Pozuelo",           "ok"),
        ("Pizza Norte — Hortaleza",         "ok"),
        ("Café Rápido — Moratalaz",         "ok"),
        ("Café Rápido — Vicálvaro",         "ok"),
    ]
    success_ct = sum(1 for _, s in locs if s == "ok")
    error_ct   = sum(1 for _, s in locs if s == "error")
    pct        = round(success_ct / len(locs) * 100)

    rows = ""
    for name, status in locs:
        if status == "ok":
            icon = '<span class="w-6 h-6 rounded-full bg-emerald-500/20 flex items-center justify-center text-emerald-400 text-xs flex-shrink-0">✓</span>'
            badge = '<span class="px-2 py-0.5 rounded-full bg-emerald-500/15 text-emerald-300 text-xs font-bold">Publicado</span>'
        else:
            icon = '<span class="w-6 h-6 rounded-full bg-rose-500/20 flex items-center justify-center text-rose-400 text-xs flex-shrink-0">✗</span>'
            badge = '<span class="px-2 py-0.5 rounded-full bg-rose-500/15 text-rose-300 text-xs font-bold">Error · retry</span>'
        rows += f"""
        <div class="flex items-center gap-3 py-2 border-b border-white/5 last:border-0">
          {icon}
          <span class="text-sm text-stone-200 flex-1">{name}</span>
          {badge}
        </div>"""

    body = f"""
<div class="mx-auto max-w-3xl px-4 py-10 sm:px-6 pb-20 fade-up">

  <div class="mb-8">
    <p class="text-xs uppercase tracking-[.2em] text-violet-300/70 mb-1">Publicación Masiva · Paso 4 de 4</p>
    <h1 class="text-3xl font-bold text-white">Worker en Cascada</h1>
    <p class="mt-1 text-stone-400 text-sm">
      Celery dispara <strong class="text-white">44 tareas en paralelo</strong>
      hacia la Google Business Profile API. Progreso en tiempo real.
    </p>
  </div>

  <!-- Progress -->
  <div class="flex gap-2 mb-10">
    <div class="h-1.5 flex-1 rounded-full bg-violet-500"></div>
    <div class="h-1.5 flex-1 rounded-full bg-violet-500"></div>
    <div class="h-1.5 flex-1 rounded-full bg-violet-500"></div>
    <div class="h-1.5 flex-1 rounded-full bg-violet-500"></div>
  </div>

  <!-- Live progress card -->
  <div class="rounded-3xl border border-violet-500/25 bg-violet-500/8 p-6 mb-6">
    <div class="flex items-center justify-between mb-2">
      <div class="flex items-center gap-2">
        <span class="w-2.5 h-2.5 rounded-full bg-violet-400 pulse-dot"></span>
        <p class="text-sm font-bold text-violet-200">Publicando… Black Friday 2026</p>
      </div>
      <span class="text-xs text-stone-400 font-mono">Celery worker · 12 hilos activos</span>
    </div>

    <!-- Big progress bar -->
    <div class="relative h-5 rounded-full bg-black/30 overflow-hidden my-5 border border-white/10">
      <div class="h-full rounded-full bar-anim"
           style="width:{pct}%;background:linear-gradient(90deg,#7c3aed,#4f46e5,#6366f1)"></div>
      <span class="absolute inset-0 flex items-center justify-center text-xs font-bold text-white">
        {pct} %
      </span>
    </div>

    <div class="grid grid-cols-3 gap-3 text-center mb-5">
      <div class="rounded-2xl bg-black/20 border border-emerald-500/15 p-3">
        <p class="text-2xl font-black text-emerald-300">{success_ct}</p>
        <p class="text-xs text-stone-400 mt-1">Publicados</p>
      </div>
      <div class="rounded-2xl bg-black/20 border border-rose-500/15 p-3">
        <p class="text-2xl font-black text-rose-300">{error_ct}</p>
        <p class="text-xs text-stone-400 mt-1">Fallaron</p>
      </div>
      <div class="rounded-2xl bg-black/20 border border-stone-500/15 p-3">
        <p class="text-2xl font-black text-stone-400">{len(locs) - success_ct - error_ct}</p>
        <p class="text-xs text-stone-400 mt-1">En cola</p>
      </div>
    </div>

    <!-- Architecture note -->
    <div class="rounded-2xl bg-black/20 border border-white/10 p-4 font-mono text-xs text-stone-400 space-y-1">
      <div><span class="text-violet-400">bulk_publish_campaign</span>.apply_async(campaign_id=<span class="text-amber-300">"bf2026"</span>)</div>
      <div class="pl-4">→ <span class="text-sky-400">chord</span>([publish_location.s(loc_id) for loc_id in locations])</div>
      <div class="pl-8">→ <span class="text-emerald-400">aggregate_results</span>.s()  <span class="text-stone-600"># callback al terminar</span></div>
      <div class="pl-4 text-stone-600"># Concurrency: 12 · Rate limit: 10/s · Retry: 3x exp backoff</div>
    </div>
  </div>

  <!-- Task log -->
  <div class="rounded-3xl border border-white/10 bg-white/5 p-5 mb-6">
    <div class="flex items-center justify-between mb-4">
      <h2 class="text-base font-semibold text-white m-0">Log de tareas (últimas 20)</h2>
      <span class="text-xs text-stone-500 font-mono">actualización cada 2 s</span>
    </div>
    <div class="max-h-80 overflow-y-auto space-y-0">
      {rows}
    </div>
  </div>

  <!-- Error detail -->
  <div class="rounded-3xl border border-rose-500/20 bg-rose-500/5 p-5 mb-8">
    <h2 class="text-base font-semibold text-white mb-4">Errores detectados — {error_ct} locales</h2>
    <div class="space-y-3">
      <div class="rounded-2xl border border-white/10 bg-black/15 p-4">
        <div class="flex justify-between items-start gap-2 mb-2">
          <div>
            <p class="text-sm font-semibold text-white">El Mar — Sarrià</p>
            <p class="text-xs text-stone-500 font-mono mt-1">GBP_API_ERROR · 403 Forbidden · token_expired</p>
          </div>
          <span class="px-2.5 py-1 rounded-full bg-amber-500/15 text-amber-300 text-xs font-bold flex-shrink-0">Reintentando</span>
        </div>
        <p class="text-xs text-stone-400">El token OAuth de este local ha expirado. El sistema reintentará en 60 s tras refrescar credenciales.</p>
      </div>
      <div class="rounded-2xl border border-white/10 bg-black/15 p-4">
        <div class="flex justify-between items-start gap-2 mb-2">
          <div>
            <p class="text-sm font-semibold text-white">Pizza Norte — Arganzuela</p>
            <p class="text-xs text-stone-500 font-mono mt-1">GBP_API_ERROR · 429 Too Many Requests</p>
          </div>
          <span class="px-2.5 py-1 rounded-full bg-amber-500/15 text-amber-300 text-xs font-bold flex-shrink-0">Reintentando</span>
        </div>
        <p class="text-xs text-stone-400">Rate limit alcanzado. Backoff exponencial: próximo intento en 90 s.</p>
      </div>
    </div>
    <button class="mt-4 px-5 py-2.5 rounded-xl border border-rose-500/25 bg-rose-500/10
                   text-rose-300 text-sm font-semibold hover:bg-rose-500/20">
      Reintentar fallidos manualmente
    </button>
  </div>

  <!-- Navigation -->
  <div class="flex justify-between items-center">
    <span class="text-stone-600 text-sm">Publicación en curso · no cierres esta pestaña</span>
    <a href="bulk_step5_report.html"
       class="px-8 py-3 rounded-2xl bg-gradient-to-r from-violet-600 to-indigo-600
              text-white font-bold text-sm hover:from-violet-500 hover:to-indigo-500 no-underline">
      Ver informe final →
    </a>
  </div>
</div>"""
    return page("Paso 4 — Publicando", "bulk_step4_publish.html", body)


# ─── STEP 5 — Informe de resultados ──────────────────────────────────────────

def step5_report() -> str:
    body = """
<div class="mx-auto max-w-4xl px-4 py-10 sm:px-6 pb-20 fade-up">

  <div class="mb-8">
    <p class="text-xs uppercase tracking-[.2em] text-violet-300/70 mb-1">Publicación Masiva · Informe Final</p>
    <h1 class="text-3xl font-bold text-white">Resultados — Black Friday 2026</h1>
    <p class="mt-1 text-stone-400 text-sm">
      Campaña completada el <strong class="text-stone-200">28 Nov 2026 · 09:04:37</strong>
    </p>
  </div>

  <!-- Big result banner -->
  <div class="rounded-3xl border border-emerald-500/25
              bg-gradient-to-br from-emerald-950/60 to-stone-900 p-8 mb-8 text-center">
    <div class="text-6xl mb-3">✅</div>
    <h2 class="text-4xl font-black text-white mb-2">42 de 44 locales</h2>
    <p class="text-emerald-300 text-lg font-bold mb-1">95.5 % de éxito</p>
    <p class="text-stone-400 text-sm">2 locales reintentando · 0 fallos definitivos</p>
  </div>

  <!-- KPI grid -->
  <div class="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-8">
    <div class="rounded-2xl border border-emerald-500/20 bg-emerald-500/5 p-4 text-center">
      <p class="text-3xl font-black text-emerald-300">42</p>
      <p class="text-xs uppercase tracking-wider text-stone-400 mt-1">Publicados ✓</p>
    </div>
    <div class="rounded-2xl border border-amber-500/15 bg-amber-500/5 p-4 text-center">
      <p class="text-3xl font-black text-amber-300">2</p>
      <p class="text-xs uppercase tracking-wider text-stone-400 mt-1">En reintento</p>
    </div>
    <div class="rounded-2xl border border-white/10 bg-white/5 p-4 text-center">
      <p class="text-3xl font-black text-white">4 m 37 s</p>
      <p class="text-xs uppercase tracking-wider text-stone-400 mt-1">Duración total</p>
    </div>
    <div class="rounded-2xl border border-white/10 bg-white/5 p-4 text-center">
      <p class="text-3xl font-black text-white">6.3 s</p>
      <p class="text-xs uppercase tracking-wider text-stone-400 mt-1">Máx. por local</p>
    </div>
  </div>

  <!-- Tenant breakdown -->
  <div class="rounded-3xl border border-white/10 bg-white/5 p-6 mb-6">
    <h2 class="text-base font-semibold text-white mb-5">Desglose por Tenant</h2>
    <div class="space-y-4">

      <div>
        <div class="flex justify-between text-sm mb-1.5">
          <span class="text-stone-200 font-semibold">Cadena Pizzas Norte</span>
          <span class="text-emerald-300 font-bold">8 / 8 ✓</span>
        </div>
        <div class="h-2.5 rounded-full bg-black/30 overflow-hidden">
          <div class="h-full rounded-full bg-emerald-500 bar-anim" style="width:100%"></div>
        </div>
      </div>

      <div>
        <div class="flex justify-between text-sm mb-1.5">
          <span class="text-stone-200 font-semibold">Franquicia Café Rápido</span>
          <span class="text-emerald-300 font-bold">14 / 14 ✓</span>
        </div>
        <div class="h-2.5 rounded-full bg-black/30 overflow-hidden">
          <div class="h-full rounded-full bg-emerald-500 bar-anim" style="width:100%"></div>
        </div>
      </div>

      <div>
        <div class="flex justify-between text-sm mb-1.5">
          <span class="text-stone-200 font-semibold">Restaurantes El Mar</span>
          <span class="text-amber-300 font-bold">4 / 5 · 1 reintentando</span>
        </div>
        <div class="h-2.5 rounded-full bg-black/30 overflow-hidden">
          <div class="h-full rounded-full" style="width:80%;background:linear-gradient(90deg,#10b981,#f59e0b)"></div>
        </div>
      </div>

      <div>
        <div class="flex justify-between text-sm mb-1.5">
          <span class="text-stone-200 font-semibold">Hoteles Solimar</span>
          <span class="text-amber-300 font-bold">16 / 17 · 1 reintentando</span>
        </div>
        <div class="h-2.5 rounded-full bg-black/30 overflow-hidden">
          <div class="h-full rounded-full" style="width:94%;background:linear-gradient(90deg,#10b981,#f59e0b)"></div>
        </div>
      </div>

    </div>
  </div>

  <!-- Technical report -->
  <div class="rounded-3xl border border-white/10 bg-white/5 p-6 mb-6">
    <h2 class="text-base font-semibold text-white mb-5">Informe técnico de Celery</h2>
    <div class="rounded-2xl bg-stone-950 border border-white/10 p-5 font-mono text-xs text-stone-300 space-y-1.5">
      <div><span class="text-stone-500">[2026-11-28 09:00:01]</span> <span class="text-violet-400">TASK_GROUP_START</span>  campaign=bf2026 · tasks=44 · concurrency=12</div>
      <div><span class="text-stone-500">[2026-11-28 09:00:04]</span> <span class="text-emerald-400">SUCCESS</span>          loc=pizza-norte-malasana · elapsed=3.1s</div>
      <div><span class="text-stone-500">[2026-11-28 09:00:04]</span> <span class="text-emerald-400">SUCCESS</span>          loc=cafe-rapido-gran-via · elapsed=2.8s</div>
      <div><span class="text-stone-500">[2026-11-28 09:00:05]</span> <span class="text-rose-400">ERROR</span>            loc=el-mar-sarria · code=403 · msg=token_expired</div>
      <div><span class="text-stone-500">[2026-11-28 09:00:05]</span> <span class="text-amber-400">RETRY</span>           loc=el-mar-sarria · attempt=1/3 · eta=+60s</div>
      <div><span class="text-stone-500">[2026-11-28 09:00:07]</span> <span class="text-rose-400">ERROR</span>            loc=pizza-norte-arganzuela · code=429 · msg=rate_limit</div>
      <div><span class="text-stone-500">[2026-11-28 09:00:07]</span> <span class="text-amber-400">RETRY</span>           loc=pizza-norte-arganzuela · attempt=1/3 · eta=+90s</div>
      <div><span class="text-stone-500">[2026-11-28 09:02:14]</span> <span class="text-emerald-400">SUCCESS (retry)</span>  loc=el-mar-sarria · elapsed=1.4s</div>
      <div><span class="text-stone-500">[2026-11-28 09:04:37]</span> <span class="text-emerald-400">TASK_GROUP_DONE</span>  success=42 · failed=0 · retried=2 · total_elapsed=4m37s</div>
    </div>
  </div>

  <!-- Actions -->
  <div class="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-8">
    <button class="px-5 py-3.5 rounded-2xl border border-white/10 bg-white/5
                   text-stone-300 font-semibold text-sm hover:bg-white/10 flex items-center justify-center gap-2">
      📥 Descargar CSV
    </button>
    <button class="px-5 py-3.5 rounded-2xl border border-white/10 bg-white/5
                   text-stone-300 font-semibold text-sm hover:bg-white/10 flex items-center justify-center gap-2">
      📧 Enviar por email
    </button>
    <a href="bulk_step1_compose.html"
       class="px-5 py-3.5 rounded-2xl bg-gradient-to-r from-violet-600 to-indigo-600
              text-white font-bold text-sm hover:from-violet-500 hover:to-indigo-500
              no-underline flex items-center justify-center gap-2">
      + Nueva campaña
    </a>
  </div>

  <!-- Back to hub -->
  <div class="flex justify-start">
    <a href="bulk_hub.html"
       class="px-5 py-3 rounded-2xl border border-white/10 bg-white/5
              text-stone-300 font-semibold text-sm hover:bg-white/10 no-underline">
      ← Volver al Hub
    </a>
  </div>
</div>"""
    return page("Informe de resultados", "bulk_step5_report.html", body)


# ─── RENDER ──────────────────────────────────────────────────────────────────

def main() -> None:
    files = [
        ("bulk_hub.html",           bulk_hub()),
        ("bulk_step1_compose.html", step1_compose()),
        ("bulk_step2_segment.html", step2_segment()),
        ("bulk_step3_preview.html", step3_preview()),
        ("bulk_step4_publish.html", step4_publish()),
        ("bulk_step5_report.html",  step5_report()),
    ]

    for fname, html in files:
        path = OUT_DIR / fname
        path.write_text(html, encoding="utf-8")
        print(f"✓ {path}")

    print("\n📌 Abriendo en el navegador:")
    for fname, _ in files:
        url = f"http://localhost:3000/enterprise/bulk/{fname}"
        webbrowser.open(url)
        print(f"   {url}")


if __name__ == "__main__":
    main()
