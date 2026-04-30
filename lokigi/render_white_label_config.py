"""
Genera el flujo completo de configuración White-Label (Marca Blanca) Enterprise.

Páginas generadas en frontend/static/enterprise/white_label/:
  wl_hub.html         — Hub: 3 pilares con estado actual
  wl_step1_identity.html  — Identidad Visual (logo, colores, tipografía)
  wl_step2_domain.html    — Mapeo de Dominio (CNAME, SSL, detección FastAPI)
  wl_step3_reports.html   — Personalización de Reportes (WeasyPrint PDF)
  wl_step4_preview.html   — Preview live de la experiencia branded
  wl_step5_activate.html  — Activar y publicar la marca
"""
from __future__ import annotations
import webbrowser
from pathlib import Path

ROOT    = Path(__file__).parent
OUT_DIR = ROOT / "frontend" / "static" / "enterprise" / "white_label"
OUT_DIR.mkdir(parents=True, exist_ok=True)

PAGES = [
    ("wl_hub.html",            "🏷️ White Label"),
    ("wl_step1_identity.html", "1 · Identidad"),
    ("wl_step2_domain.html",   "2 · Dominio"),
    ("wl_step3_reports.html",  "3 · Reportes PDF"),
    ("wl_step4_preview.html",  "4 · Preview"),
    ("wl_step5_activate.html", "5 · Activar"),
]


def nav_bar(active: str) -> str:
    links = ""
    for href, label in PAGES:
        if href == active:
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
    <span class="text-stone-400 text-xs font-semibold">White Label</span>
  </div>
  {links}
</nav>"""


def page(title: str, active: str, body: str) -> str:
    return f"""<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{title} | White Label · Lokigi Enterprise</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <style>
    body {{ font-family: Arial, "Helvetica Neue", sans-serif; }}
    .no-underline {{ text-decoration: none; }}
    @keyframes fadeUp {{
      from {{ opacity:0; transform:translateY(14px); }}
      to   {{ opacity:1; transform:translateY(0); }}
    }}
    .fade-up {{ animation: fadeUp .35s ease both; }}
    @keyframes pulse-dot {{
      0%,100% {{ opacity:1; }} 50% {{ opacity:.4; }}
    }}
    .pulse {{ animation: pulse-dot 1.8s ease-in-out infinite; }}
    /* Inputs */
    input[type=text], input[type=url], input[type=email], select, textarea {{
      background: rgba(255,255,255,.05);
      border: 1px solid rgba(255,255,255,.12);
      border-radius: 10px;
      color: #f1f5f9;
      padding: 9px 13px;
      font-size: 13px;
      outline: none;
      width: 100%;
    }}
    input[type=color] {{
      background: transparent;
      border: 1px solid rgba(255,255,255,.15);
      border-radius: 8px;
      padding: 2px;
      height: 40px;
      width: 48px;
      cursor: pointer;
    }}
    select option {{ background: #1c1917; }}
    /* Step indicator */
    .step-done  {{ background: #22c55e; color: #052e16; }}
    .step-active{{ background: #7c3aed; color: #fff; }}
    .step-todo  {{ background: rgba(255,255,255,.08); color: #78716c; }}
    /* Code block */
    pre {{
      background: rgba(0,0,0,.4);
      border: 1px solid rgba(255,255,255,.08);
      border-radius: 12px;
      padding: 16px;
      font-size: 12px;
      color: #a3e635;
      overflow-x: auto;
      white-space: pre;
    }}
    /* PDF mockup */
    .pdf-page {{
      background: #fff;
      border-radius: 12px;
      padding: 32px;
      color: #1c1917;
      font-family: 'Georgia', serif;
      max-width: 540px;
    }}
    /* Tag badge */
    .badge-ok  {{ background:#16a34a22; color:#86efac; border:1px solid #16a34a40; }}
    .badge-warn{{ background:#d9770622; color:#fcd34d; border:1px solid #d9770640; }}
    .badge-err {{ background:#dc262622; color:#fca5a5; border:1px solid #dc262640; }}
  </style>
</head>
<body class="min-h-screen bg-stone-950 text-stone-100">
{nav_bar(active)}
{body}
</body>
</html>"""


# ─── STEP PROGRESS BAR ───────────────────────────────────────────────────────

def step_bar(current: int) -> str:
    steps = [
        (1, "Identidad Visual"),
        (2, "Mapeo de Dominio"),
        (3, "Reportes PDF"),
        (4, "Preview"),
        (5, "Activar"),
    ]
    items = ""
    for n, label in steps:
        if n < current:
            cls = "step-done"
            icon = "✓"
        elif n == current:
            cls = "step-active"
            icon = str(n)
        else:
            cls = "step-todo"
            icon = str(n)
        items += f"""
        <div class="flex items-center gap-2 {'opacity-40' if n > current else ''}">
          <div class="w-7 h-7 rounded-full {cls} flex items-center justify-center
                      text-xs font-black flex-shrink-0">{icon}</div>
          <span class="text-xs font-semibold {'text-white' if n == current else 'text-stone-400'} hidden sm:block">{label}</span>
        </div>
        {'<div class="flex-1 h-px bg-white/10 hidden sm:block"></div>' if n < 5 else ''}"""
    return f"""
    <div class="flex items-center gap-1 mb-8 px-1">
      {items}
    </div>"""


# ─── HUB ─────────────────────────────────────────────────────────────────────

def wl_hub() -> str:
    body = """
<div class="mx-auto max-w-5xl px-4 py-10 sm:px-6 pb-20 fade-up">

  <div class="flex items-start justify-between gap-4 mb-8 flex-wrap">
    <div>
      <p class="text-xs uppercase tracking-[.2em] text-violet-300/70 mb-1">Enterprise · Plan Agencia</p>
      <h1 class="text-3xl font-bold text-white">Configuración White-Label</h1>
      <p class="mt-1 text-stone-400 text-sm max-w-2xl">
        Convierte Lokigi en tu propia plataforma de reputación.
        Tu logo, tus colores, tu dominio — sin rastro de Lokigi en la experiencia cliente.
      </p>
    </div>
    <a href="wl_step1_identity.html"
       class="px-6 py-3 rounded-2xl bg-gradient-to-r from-violet-600 to-indigo-600
              text-white font-bold text-sm hover:from-violet-500 hover:to-indigo-500 no-underline flex-shrink-0">
      Comenzar configuración →
    </a>
  </div>

  <!-- 3 Pilares -->
  <div class="grid grid-cols-1 sm:grid-cols-3 gap-5 mb-10">

    <!-- Pilar 1: Identidad Visual -->
    <a href="wl_step1_identity.html" class="no-underline group">
      <div class="rounded-3xl border border-violet-500/20 bg-violet-500/5 p-6
                  hover:border-violet-400/30 hover:bg-violet-500/8 transition-all">
        <div class="flex items-center justify-between mb-4">
          <div class="w-11 h-11 rounded-2xl bg-violet-500/20 flex items-center justify-center text-xl">🎨</div>
          <span class="px-2.5 py-1 rounded-full badge-ok text-xs font-bold">Configurado</span>
        </div>
        <h2 class="text-base font-bold text-white mb-2">Identidad Visual</h2>
        <p class="text-stone-400 text-sm mb-4">
          Logo de la agencia, colores institucionales y tipografía aplicados
          en todo el panel de cliente y las notificaciones.
        </p>
        <div class="space-y-2 text-xs">
          <div class="flex items-center gap-2">
            <span class="text-emerald-400">✓</span>
            <span class="text-stone-400">Logo subido (marketing_pro_logo.svg)</span>
          </div>
          <div class="flex items-center gap-2">
            <span class="text-emerald-400">✓</span>
            <span class="text-stone-400">Color primario: #2563EB</span>
          </div>
          <div class="flex items-center gap-2">
            <span class="text-emerald-400">✓</span>
            <span class="text-stone-400">Tipografía: Inter (sans-serif)</span>
          </div>
        </div>
        <p class="text-xs text-violet-400 mt-4 group-hover:text-violet-300">Editar →</p>
      </div>
    </a>

    <!-- Pilar 2: Mapeo de Dominio -->
    <a href="wl_step2_domain.html" class="no-underline group">
      <div class="rounded-3xl border border-amber-500/15 bg-amber-500/5 p-6
                  hover:border-amber-400/25 hover:bg-amber-500/8 transition-all">
        <div class="flex items-center justify-between mb-4">
          <div class="w-11 h-11 rounded-2xl bg-amber-500/20 flex items-center justify-center text-xl">🌐</div>
          <span class="px-2.5 py-1 rounded-full badge-warn text-xs font-bold">SSL pendiente</span>
        </div>
        <h2 class="text-base font-bold text-white mb-2">Mapeo de Dominio</h2>
        <p class="text-stone-400 text-sm mb-4">
          El servidor FastAPI detecta el <code class="text-violet-300">Host</code> header
          y carga automáticamente el tema de la agencia correcta.
        </p>
        <div class="space-y-2 text-xs">
          <div class="flex items-center gap-2">
            <span class="text-emerald-400">✓</span>
            <span class="text-stone-400">CNAME creado: clientes.marketingpro.com</span>
          </div>
          <div class="flex items-center gap-2">
            <span class="text-amber-400">⏳</span>
            <span class="text-stone-400">SSL en propagación (≈ 15 min)</span>
          </div>
          <div class="flex items-center gap-2">
            <span class="text-emerald-400">✓</span>
            <span class="text-stone-400">ThemeMiddleware detectando host</span>
          </div>
        </div>
        <p class="text-xs text-amber-400 mt-4 group-hover:text-amber-300">Ver estado →</p>
      </div>
    </a>

    <!-- Pilar 3: Reportes PDF -->
    <a href="wl_step3_reports.html" class="no-underline group">
      <div class="rounded-3xl border border-rose-500/15 bg-rose-500/5 p-6
                  hover:border-rose-400/25 hover:bg-rose-500/8 transition-all">
        <div class="flex items-center justify-between mb-4">
          <div class="w-11 h-11 rounded-2xl bg-rose-500/20 flex items-center justify-center text-xl">📄</div>
          <span class="px-2.5 py-1 rounded-full badge-err text-xs font-bold">Sin configurar</span>
        </div>
        <h2 class="text-base font-bold text-white mb-2">Personalización de Reportes</h2>
        <p class="text-stone-400 text-sm mb-4">
          PDFs generados con WeasyPrint sin rastro de Lokigi:
          logo de la agencia en cabecera, colores institucionales y pie de página propio.
        </p>
        <div class="space-y-2 text-xs">
          <div class="flex items-center gap-2">
            <span class="text-rose-400">✗</span>
            <span class="text-stone-400">Plantilla PDF no personalizada</span>
          </div>
          <div class="flex items-center gap-2">
            <span class="text-rose-400">✗</span>
            <span class="text-stone-400">Pie de página de agencia pendiente</span>
          </div>
          <div class="flex items-center gap-2">
            <span class="text-rose-400">✗</span>
            <span class="text-stone-400">Email de contacto no configurado</span>
          </div>
        </div>
        <p class="text-xs text-rose-400 mt-4 group-hover:text-rose-300">Configurar →</p>
      </div>
    </a>
  </div>

  <!-- Status overview -->
  <div class="rounded-3xl border border-white/10 bg-white/5 p-6">
    <div class="flex items-center justify-between mb-5 flex-wrap gap-2">
      <h2 class="text-sm font-bold text-stone-300 uppercase tracking-wider">Estado general del tenant</h2>
      <span class="text-xs text-stone-500">Tenant: Marketing Pro SL · ID: org_7f3a2b</span>
    </div>
    <div class="grid grid-cols-2 sm:grid-cols-4 gap-4">
      <div class="text-center">
        <p class="text-2xl font-black text-violet-300">12</p>
        <p class="text-xs text-stone-500 mt-1">Clientes bajo marca blanca</p>
      </div>
      <div class="text-center">
        <p class="text-2xl font-black text-emerald-300">2/3</p>
        <p class="text-xs text-stone-500 mt-1">Pilares configurados</p>
      </div>
      <div class="text-center">
        <p class="text-2xl font-black text-amber-300">15 min</p>
        <p class="text-xs text-stone-500 mt-1">Tiempo estimado SSL</p>
      </div>
      <div class="text-center">
        <p class="text-2xl font-black text-stone-400">Inactivo</p>
        <p class="text-xs text-stone-500 mt-1">Estado de activación</p>
      </div>
    </div>
    <div class="mt-5 p-4 rounded-2xl border border-amber-500/20 bg-amber-500/5">
      <p class="text-sm text-amber-300 font-semibold mb-1">⚠️ Acción requerida antes de activar</p>
      <p class="text-xs text-stone-400">Completa la configuración de Reportes PDF (Pilar 3) para poder publicar la marca blanca a tus clientes.</p>
    </div>
  </div>

</div>"""
    return page("White Label Hub", "wl_hub.html", body)


# ─── STEP 1: IDENTIDAD VISUAL ────────────────────────────────────────────────

def wl_step1_identity() -> str:
    body = f"""
<div class="mx-auto max-w-4xl px-4 py-10 sm:px-6 pb-20 fade-up">

  <p class="text-xs uppercase tracking-[.2em] text-violet-300/70 mb-1">White Label · Paso 1</p>
  <h1 class="text-3xl font-bold text-white mb-2">Identidad Visual</h1>
  <p class="text-stone-400 text-sm mb-6">
    Define la identidad completa de tu agencia. Esta configuración se aplica
    al panel de clientes, emails, notificaciones y PDFs generados por Lokigi.
  </p>

  {step_bar(1)}

  <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">

    <!-- Form -->
    <div class="space-y-5">

      <!-- Logo upload -->
      <div class="rounded-3xl border border-white/10 bg-white/5 p-6">
        <h2 class="text-sm font-bold text-white uppercase tracking-wider mb-4">Logo de la Agencia</h2>
        <div class="border-2 border-dashed border-violet-500/30 rounded-2xl p-8 text-center
                    hover:border-violet-400/50 cursor-pointer mb-4">
          <div class="w-16 h-16 rounded-2xl bg-blue-600 flex items-center justify-center
                      text-white font-black text-2xl mx-auto mb-3">MP</div>
          <p class="text-sm font-semibold text-white mb-1">marketing_pro_logo.svg</p>
          <p class="text-xs text-stone-500 mb-3">192×48 px · SVG · 4.2 KB</p>
          <button class="px-4 py-2 rounded-xl border border-white/10 bg-white/5 text-stone-300 text-xs font-semibold hover:bg-white/10">
            🔄 Cambiar logo
          </button>
        </div>
        <p class="text-xs text-stone-500">
          Formatos aceptados: SVG, PNG, WebP. Máximo 2 MB.
          Recomendado: fondo transparente, min. 200px de ancho.
        </p>
      </div>

      <!-- Color palette -->
      <div class="rounded-3xl border border-white/10 bg-white/5 p-6">
        <h2 class="text-sm font-bold text-white uppercase tracking-wider mb-4">Paleta de Colores</h2>
        <div class="space-y-3">
          <div class="flex items-center gap-3">
            <input type="color" value="#2563EB" />
            <div class="flex-1">
              <label class="text-xs text-stone-400 block mb-1">Color Primario</label>
              <input type="text" value="#2563EB" class="font-mono text-xs" style="width:100%" />
            </div>
            <div class="w-8 h-8 rounded-lg flex-shrink-0" style="background:#2563EB"></div>
          </div>
          <div class="flex items-center gap-3">
            <input type="color" value="#1E40AF" />
            <div class="flex-1">
              <label class="text-xs text-stone-400 block mb-1">Color Secundario / Hover</label>
              <input type="text" value="#1E40AF" class="font-mono text-xs" style="width:100%" />
            </div>
            <div class="w-8 h-8 rounded-lg flex-shrink-0" style="background:#1E40AF"></div>
          </div>
          <div class="flex items-center gap-3">
            <input type="color" value="#DBEAFE" />
            <div class="flex-1">
              <label class="text-xs text-stone-400 block mb-1">Color de Acento</label>
              <input type="text" value="#DBEAFE" class="font-mono text-xs" style="width:100%" />
            </div>
            <div class="w-8 h-8 rounded-lg flex-shrink-0" style="background:#DBEAFE"></div>
          </div>
        </div>
        <div class="mt-4 p-3 rounded-xl bg-black/20 border border-white/8">
          <p class="text-xs text-stone-500 mb-2 font-mono">CSS variables generadas automáticamente:</p>
          <pre class="!p-0 !border-0 !rounded-none !bg-transparent text-[11px]">:root {{
  --color-primary:   #2563EB;
  --color-secondary: #1E40AF;
  --color-accent:    #DBEAFE;
  --font-brand:      'Inter', sans-serif;
}}</pre>
        </div>
      </div>

      <!-- Typography -->
      <div class="rounded-3xl border border-white/10 bg-white/5 p-6">
        <h2 class="text-sm font-bold text-white uppercase tracking-wider mb-4">Tipografía</h2>
        <div class="space-y-3">
          <div>
            <label class="text-xs text-stone-400 block mb-1.5">Fuente principal</label>
            <select>
              <option selected>Inter (Recomendada · Sans-serif)</option>
              <option>Roboto</option>
              <option>Poppins</option>
              <option>Montserrat</option>
              <option>Source Sans Pro</option>
              <option>Open Sans</option>
            </select>
          </div>
          <div>
            <label class="text-xs text-stone-400 block mb-1.5">Fuente para títulos (opcional)</label>
            <select>
              <option selected>— Igual que la principal —</option>
              <option>Playfair Display (Serif)</option>
              <option>Merriweather (Serif)</option>
              <option>DM Serif Display</option>
            </select>
          </div>
        </div>
      </div>

      <!-- Agency info -->
      <div class="rounded-3xl border border-white/10 bg-white/5 p-6">
        <h2 class="text-sm font-bold text-white uppercase tracking-wider mb-4">Datos de la Agencia</h2>
        <div class="space-y-3">
          <div>
            <label class="text-xs text-stone-400 block mb-1.5">Nombre de la agencia</label>
            <input type="text" value="Marketing Pro SL" />
          </div>
          <div>
            <label class="text-xs text-stone-400 block mb-1.5">Email de contacto (aparece en PDFs y emails)</label>
            <input type="email" value="hola@marketingpro.es" />
          </div>
          <div>
            <label class="text-xs text-stone-400 block mb-1.5">Slogan / tagline (pie de PDFs)</label>
            <input type="text" value="Gestión de reputación online para tu negocio" />
          </div>
        </div>
      </div>

    </div>

    <!-- Live preview panel -->
    <div class="space-y-5">
      <div class="rounded-3xl border border-white/10 bg-white/5 p-6 sticky top-20">
        <h2 class="text-sm font-bold text-stone-300 uppercase tracking-wider mb-4">
          Preview en tiempo real
        </h2>

        <!-- Simulated branded navbar -->
        <div class="rounded-2xl overflow-hidden border border-white/10 mb-4">
          <div class="flex items-center gap-3 px-4 py-3" style="background:#2563EB">
            <div class="w-7 h-7 rounded bg-white/20 flex items-center justify-center
                        font-black text-white text-xs flex-shrink-0">MP</div>
            <span class="font-bold text-white text-sm">Marketing Pro SL</span>
            <span class="ml-auto px-2.5 py-0.5 rounded-full bg-white/20 text-white text-xs font-bold">Panel de reputación</span>
          </div>
          <div class="bg-stone-900 p-5">
            <div class="flex items-center justify-between mb-4 flex-wrap gap-2">
              <div>
                <p class="text-xs text-stone-500">Buenos días,</p>
                <p class="font-bold text-white">Restaurante La Pepita</p>
              </div>
              <div class="px-4 py-2 rounded-xl text-white text-xs font-bold"
                   style="background:#2563EB">Nueva reseña</div>
            </div>
            <div class="grid grid-cols-3 gap-2">
              <div class="rounded-xl bg-white/5 p-3 text-center">
                <p class="text-lg font-black text-white">4.7★</p>
                <p class="text-xs text-stone-500">Nota media</p>
              </div>
              <div class="rounded-xl bg-white/5 p-3 text-center">
                <p class="text-lg font-black" style="color:#2563EB">142</p>
                <p class="text-xs text-stone-500">Reseñas</p>
              </div>
              <div class="rounded-xl bg-white/5 p-3 text-center">
                <p class="text-lg font-black text-emerald-400">+12</p>
                <p class="text-xs text-stone-500">Este mes</p>
              </div>
            </div>
          </div>
          <div class="flex items-center justify-center py-2 bg-stone-900 border-t border-white/5">
            <p class="text-xs text-stone-600">© 2026 Marketing Pro SL · Todos los derechos reservados</p>
          </div>
        </div>

        <!-- CSS vars preview -->
        <div class="rounded-2xl border border-white/8 bg-black/20 p-4">
          <p class="text-xs font-bold text-stone-400 uppercase tracking-wider mb-3">
            ThemeService → BrandTheme
          </p>
          <div class="space-y-2 font-mono text-xs">
            <div class="flex items-center gap-2">
              <div class="w-3 h-3 rounded-full flex-shrink-0" style="background:#2563EB"></div>
              <span class="text-stone-400">primary_color:</span>
              <span class="text-lime-400">"#2563EB"</span>
            </div>
            <div class="flex items-center gap-2">
              <div class="w-3 h-3 rounded-full flex-shrink-0" style="background:#1E40AF"></div>
              <span class="text-stone-400">secondary_color:</span>
              <span class="text-lime-400">"#1E40AF"</span>
            </div>
            <div class="flex items-center gap-2">
              <span class="text-stone-600">·</span>
              <span class="text-stone-400">agency_name:</span>
              <span class="text-lime-400">"Marketing Pro SL"</span>
            </div>
            <div class="flex items-center gap-2">
              <span class="text-stone-600">·</span>
              <span class="text-stone-400">font_family:</span>
              <span class="text-lime-400">"Inter, sans-serif"</span>
            </div>
            <div class="flex items-center gap-2">
              <span class="text-stone-600">·</span>
              <span class="text-stone-400">cache:</span>
              <span class="text-violet-400">Redis L2 · TTL 300s</span>
            </div>
          </div>
        </div>

        <!-- Navigation -->
        <div class="flex gap-3 mt-5">
          <a href="wl_hub.html"
             class="flex-1 px-4 py-2.5 rounded-2xl border border-white/10 bg-white/5
                    text-stone-300 font-semibold text-sm text-center hover:bg-white/10 no-underline">
            ← Volver
          </a>
          <a href="wl_step2_domain.html"
             class="flex-1 px-4 py-2.5 rounded-2xl bg-gradient-to-r from-violet-600 to-indigo-600
                    text-white font-bold text-sm text-center hover:from-violet-500 hover:to-indigo-500 no-underline">
            Guardar y continuar →
          </a>
        </div>
      </div>
    </div>
  </div>

</div>"""
    return page("Identidad Visual", "wl_step1_identity.html", body)


# ─── STEP 2: MAPEO DE DOMINIO ─────────────────────────────────────────────────

def wl_step2_domain() -> str:
    body = f"""
<div class="mx-auto max-w-4xl px-4 py-10 sm:px-6 pb-20 fade-up">

  <p class="text-xs uppercase tracking-[.2em] text-violet-300/70 mb-1">White Label · Paso 2</p>
  <h1 class="text-3xl font-bold text-white mb-2">Mapeo de Dominio</h1>
  <p class="text-stone-400 text-sm mb-6 max-w-2xl">
    Cuando un cliente visita <strong class="text-white">clientes.marketingpro.com</strong>, el servidor
    FastAPI detecta el header <code class="text-violet-300">Host</code> y aplica automáticamente
    el tema de tu agencia. Sin redirecciones visibles, sin rastro de Lokigi.
  </p>

  {step_bar(2)}

  <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">

    <!-- Config form -->
    <div class="space-y-5">

      <div class="rounded-3xl border border-white/10 bg-white/5 p-6">
        <h2 class="text-sm font-bold text-white uppercase tracking-wider mb-4">Dominio personalizado</h2>
        <div class="space-y-4">
          <div>
            <label class="text-xs text-stone-400 block mb-1.5">Subdominio de tu agencia</label>
            <div class="flex gap-2">
              <input type="text" value="clientes.marketingpro.com" class="flex-1" />
              <button class="px-4 py-2 rounded-xl border border-white/10 bg-white/5 text-stone-300 text-xs font-semibold hover:bg-white/10 flex-shrink-0">
                Verificar
              </button>
            </div>
            <p class="text-xs text-stone-500 mt-1.5">Puede ser un subdominio tuyo o un dominio propio completo.</p>
          </div>

          <!-- CNAME instructions -->
          <div class="p-4 rounded-2xl border border-indigo-500/20 bg-indigo-500/5">
            <p class="text-xs font-bold text-indigo-300 uppercase tracking-wider mb-3">Instrucciones DNS — Registro CNAME</p>
            <div class="space-y-2 font-mono text-xs">
              <div class="grid grid-cols-3 gap-2 text-stone-500">
                <span>Tipo</span><span>Host</span><span>Valor</span>
              </div>
              <div class="grid grid-cols-3 gap-2 bg-black/25 rounded-lg p-2 text-stone-300">
                <span class="text-emerald-400">CNAME</span>
                <span>clientes</span>
                <span class="text-violet-300 break-all">enterprise.lokigi.io</span>
              </div>
            </div>
            <p class="text-xs text-stone-500 mt-3">TTL recomendado: 300 s. La propagación puede tardar entre 5 y 60 minutos.</p>
          </div>
        </div>
      </div>

      <!-- SSL Status -->
      <div class="rounded-3xl border border-amber-500/20 bg-amber-500/5 p-6">
        <div class="flex items-center justify-between mb-4 flex-wrap gap-2">
          <h2 class="text-sm font-bold text-amber-200 uppercase tracking-wider">Certificado SSL / TLS</h2>
          <span class="px-2.5 py-1 rounded-full badge-warn text-xs font-bold">⏳ Aprovisionando</span>
        </div>
        <div class="space-y-3">
          <div class="flex items-center gap-3">
            <div class="w-5 h-5 rounded-full border-2 border-amber-400 flex items-center justify-center flex-shrink-0">
              <div class="w-2 h-2 rounded-full bg-amber-400 pulse"></div>
            </div>
            <div>
              <p class="text-sm font-semibold text-amber-200">Let's Encrypt · Wildcard</p>
              <p class="text-xs text-stone-500">Emitido por Lokigi · Renovación automática cada 90 días</p>
            </div>
          </div>
          <div class="mt-2 pl-8">
            <div class="flex items-center gap-2 text-xs text-stone-400 mb-1">
              <span class="text-emerald-400">✓</span> CNAME propagado (verificado)
            </div>
            <div class="flex items-center gap-2 text-xs text-stone-400 mb-1">
              <span class="text-amber-400">⏳</span> Desafío ACME HTTP-01 en curso
            </div>
            <div class="flex items-center gap-2 text-xs text-stone-400">
              <span class="text-stone-600">○</span> Certificado activo (pendiente)
            </div>
          </div>
        </div>
      </div>

      <!-- Multiple domains -->
      <div class="rounded-3xl border border-white/10 bg-white/5 p-6">
        <h2 class="text-sm font-bold text-white uppercase tracking-wider mb-4">Múltiples dominios</h2>
        <p class="text-xs text-stone-500 mb-3">Cada dominio puede apuntar a un tenant diferente.</p>
        <div class="space-y-2">
          <div class="flex items-center gap-3 p-3 rounded-xl bg-black/15 border border-white/8">
            <span class="text-emerald-400 text-xs">🟢</span>
            <span class="text-sm text-stone-300 flex-1 font-mono">clientes.marketingpro.com</span>
            <span class="text-xs text-stone-500">→ org_7f3a2b</span>
          </div>
          <div class="flex items-center gap-3 p-3 rounded-xl bg-black/15 border border-white/8">
            <span class="text-emerald-400 text-xs">🟢</span>
            <span class="text-sm text-stone-300 flex-1 font-mono">reputacion.agenciaxyz.com</span>
            <span class="text-xs text-stone-500">→ org_a1b2c3</span>
          </div>
          <button class="w-full p-3 rounded-xl border border-dashed border-white/15 text-stone-500 text-xs hover:border-white/25 hover:text-stone-400">
            + Agregar dominio
          </button>
        </div>
      </div>

    </div>

    <!-- Technical diagram -->
    <div class="space-y-5">

      <div class="rounded-3xl border border-white/10 bg-white/5 p-6">
        <h2 class="text-sm font-bold text-stone-300 uppercase tracking-wider mb-4">
          Arquitectura de detección
        </h2>

        <!-- Request flow diagram -->
        <div class="space-y-2 text-xs font-mono mb-5">
          <div class="flex items-center gap-2 p-2.5 rounded-lg bg-black/25">
            <span class="text-blue-400 flex-shrink-0">①</span>
            <span class="text-stone-400">Browser:</span>
            <span class="text-stone-200">GET / HTTP/1.1</span>
          </div>
          <div class="flex items-center gap-2 p-2.5 rounded-lg bg-black/15 ml-4">
            <span class="text-stone-600 flex-shrink-0">↓</span>
            <span class="text-violet-400">Host: clientes.marketingpro.com</span>
          </div>
          <div class="flex items-center gap-2 p-2.5 rounded-lg bg-black/25">
            <span class="text-blue-400 flex-shrink-0">②</span>
            <span class="text-stone-400">ThemeMiddleware</span>
            <span class="text-stone-500 ml-auto">FastAPI</span>
          </div>
          <div class="ml-4 p-2.5 rounded-lg bg-black/15 space-y-1">
            <div><span class="text-stone-600">L1:</span> <span class="text-emerald-400">_LOCAL_CACHE</span> <span class="text-stone-500">(miss)</span></div>
            <div><span class="text-stone-600">L2:</span> <span class="text-amber-400">Redis</span> <span class="text-stone-500">theme:clientes.marketingpro.com</span></div>
            <div><span class="text-stone-600">L3:</span> <span class="text-rose-400">Postgres</span> <span class="text-stone-500">WHERE domain = host</span></div>
          </div>
          <div class="flex items-center gap-2 p-2.5 rounded-lg bg-black/25">
            <span class="text-blue-400 flex-shrink-0">③</span>
            <span class="text-stone-400">request.state.theme</span>
            <span class="text-emerald-400 ml-auto">BrandTheme ✓</span>
          </div>
          <div class="flex items-center gap-2 p-2.5 rounded-lg bg-black/25">
            <span class="text-blue-400 flex-shrink-0">④</span>
            <span class="text-stone-400">Respuesta con CSS vars</span>
            <span class="text-violet-400 ml-auto">--color-primary: #2563EB</span>
          </div>
        </div>

        <!-- Code snippet -->
        <pre># backend/app/enterprise/white_label.py
class ThemeMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        host = request.headers.get("host", "").split(":")[0]
        with SessionLocal() as db:
            request.state.theme = theme_service.get_theme(
                domain=host, db=db
            )
        return await call_next(request)</pre>
      </div>

      <!-- Navegación -->
      <div class="flex gap-3">
        <a href="wl_step1_identity.html"
           class="flex-1 px-4 py-3 rounded-2xl border border-white/10 bg-white/5
                  text-stone-300 font-semibold text-sm text-center hover:bg-white/10 no-underline">
          ← Identidad
        </a>
        <a href="wl_step3_reports.html"
           class="flex-1 px-4 py-3 rounded-2xl bg-gradient-to-r from-violet-600 to-indigo-600
                  text-white font-bold text-sm text-center hover:from-violet-500 hover:to-indigo-500 no-underline">
          Siguiente: Reportes →
        </a>
      </div>

    </div>
  </div>

</div>"""
    return page("Mapeo de Dominio", "wl_step2_domain.html", body)


# ─── STEP 3: REPORTES PDF ─────────────────────────────────────────────────────

def wl_step3_reports() -> str:
    body = f"""
<div class="mx-auto max-w-5xl px-4 py-10 sm:px-6 pb-20 fade-up">

  <p class="text-xs uppercase tracking-[.2em] text-violet-300/70 mb-1">White Label · Paso 3</p>
  <h1 class="text-3xl font-bold text-white mb-2">Personalización de Reportes PDF</h1>
  <p class="text-stone-400 text-sm mb-6 max-w-2xl">
    Configura cómo WeasyPrint genera los PDFs para tus clientes.
    El logo de Lokigi desaparece — solo aparece el de tu agencia.
  </p>

  {step_bar(3)}

  <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">

    <!-- PDF config -->
    <div class="space-y-5">

      <div class="rounded-3xl border border-white/10 bg-white/5 p-6">
        <h2 class="text-sm font-bold text-white uppercase tracking-wider mb-4">Cabecera del PDF</h2>
        <div class="space-y-4">
          <div>
            <label class="text-xs text-stone-400 block mb-1.5">Logo en la cabecera</label>
            <div class="flex gap-2 items-center">
              <div class="w-12 h-12 rounded-xl bg-blue-600 flex items-center justify-center
                          text-white font-black text-sm flex-shrink-0">MP</div>
              <div class="flex-1">
                <input type="text" value="marketing_pro_logo.svg" class="text-xs" />
              </div>
            </div>
          </div>
          <div>
            <label class="text-xs text-stone-400 block mb-1.5">Posición del logo</label>
            <select>
              <option selected>Izquierda (recomendado)</option>
              <option>Centro</option>
              <option>Derecha</option>
            </select>
          </div>
          <div>
            <label class="text-xs text-stone-400 block mb-1.5">Ancho máximo del logo (px)</label>
            <input type="text" value="160" />
          </div>
        </div>
      </div>

      <div class="rounded-3xl border border-white/10 bg-white/5 p-6">
        <h2 class="text-sm font-bold text-white uppercase tracking-wider mb-4">Pie de Página</h2>
        <div class="space-y-3">
          <div>
            <label class="text-xs text-stone-400 block mb-1.5">Texto del pie (izquierda)</label>
            <input type="text" value="Marketing Pro SL · hola@marketingpro.es" />
          </div>
          <div>
            <label class="text-xs text-stone-400 block mb-1.5">Texto del pie (derecha)</label>
            <input type="text" value="Informe generado el {{fecha}} · Confidencial" />
          </div>
          <div class="flex items-center gap-3 p-3 rounded-xl border border-white/8 bg-black/15">
            <input type="checkbox" checked class="w-4 h-4" />
            <label class="text-xs text-stone-300">Mostrar numeración de página (Página X de Y)</label>
          </div>
          <div class="flex items-center gap-3 p-3 rounded-xl border border-white/8 bg-black/15">
            <input type="checkbox" class="w-4 h-4" />
            <label class="text-xs text-stone-300">Incluir referencia "Powered by Lokigi" (desactivado por defecto en Enterprise)</label>
          </div>
        </div>
      </div>

      <div class="rounded-3xl border border-white/10 bg-white/5 p-6">
        <h2 class="text-sm font-bold text-white uppercase tracking-wider mb-4">Colores y Estilo</h2>
        <div class="space-y-3">
          <div class="flex items-center gap-3">
            <input type="color" value="#2563EB" />
            <div class="flex-1">
              <label class="text-xs text-stone-400 block mb-1">Color de cabecera del PDF</label>
              <input type="text" value="#2563EB" class="text-xs" />
            </div>
          </div>
          <div class="flex items-center gap-3">
            <input type="color" value="#1E3A8A" />
            <div class="flex-1">
              <label class="text-xs text-stone-400 block mb-1">Color de acento en tablas</label>
              <input type="text" value="#1E3A8A" class="text-xs" />
            </div>
          </div>
          <div>
            <label class="text-xs text-stone-400 block mb-1.5">Tipo de informe por defecto</label>
            <select>
              <option selected>Informe mensual completo</option>
              <option>Resumen ejecutivo (2 páginas)</option>
              <option>Informe de red (multi-local)</option>
            </select>
          </div>
        </div>
      </div>

      <!-- Backend code -->
      <div class="rounded-3xl border border-white/10 bg-white/5 p-6">
        <h2 class="text-sm font-bold text-stone-300 uppercase tracking-wider mb-3">Servicio backend</h2>
        <pre>from app.enterprise.pdf_branding import BrandedPDFRenderer

renderer = BrandedPDFRenderer(theme=request.state.theme)
pdf_bytes = renderer.render_monthly_report(
    location=connection,
    reviews=reviews,
    period="Abril 2026",
)
# → PDF sin rastro de Lokigi ✓</pre>
      </div>

    </div>

    <!-- PDF preview -->
    <div class="sticky top-20 space-y-5">
      <div class="rounded-3xl border border-white/10 bg-white/5 p-6">
        <h2 class="text-sm font-bold text-stone-300 uppercase tracking-wider mb-4">Preview del PDF</h2>

        <!-- PDF mockup -->
        <div class="pdf-page shadow-2xl mx-auto text-sm">
          <!-- PDF Header -->
          <div class="flex items-start justify-between pb-4 mb-4" style="border-bottom: 3px solid #2563EB">
            <div>
              <div class="w-28 h-7 rounded flex items-center justify-center font-black text-white text-xs"
                   style="background:#2563EB">Marketing Pro SL</div>
              <p class="text-xs mt-1" style="color:#6b7280">Gestión de reputación online</p>
            </div>
            <div class="text-right">
              <p class="text-xs font-bold" style="color:#1f2937">INFORME DE REPUTACIÓN</p>
              <p class="text-xs" style="color:#6b7280">Abril 2026</p>
              <p class="text-xs" style="color:#6b7280">Restaurante La Pepita</p>
            </div>
          </div>
          <!-- PDF Content -->
          <p class="text-xs font-bold mb-2" style="color:#1f2937">Resumen del período</p>
          <div class="grid grid-cols-3 gap-2 mb-4">
            <div class="text-center p-2 rounded" style="background:#EFF6FF">
              <p class="text-lg font-black" style="color:#2563EB">4.7★</p>
              <p class="text-xs" style="color:#6b7280">Nota media</p>
            </div>
            <div class="text-center p-2 rounded" style="background:#EFF6FF">
              <p class="text-lg font-black" style="color:#2563EB">142</p>
              <p class="text-xs" style="color:#6b7280">Reseñas</p>
            </div>
            <div class="text-center p-2 rounded" style="background:#EFF6FF">
              <p class="text-lg font-black" style="color:#16a34a">96%</p>
              <p class="text-xs" style="color:#6b7280">Respondidas</p>
            </div>
          </div>
          <p class="text-xs font-bold mb-1" style="color:#1f2937">Distribución de valoraciones</p>
          <div class="space-y-1 mb-4">
            <div class="flex items-center gap-2 text-xs">
              <span style="color:#6b7280; width:30px">5★</span>
              <div class="flex-1 h-2 rounded-full" style="background:#e5e7eb">
                <div class="h-full rounded-full" style="background:#2563EB; width:72%"></div>
              </div>
              <span style="color:#6b7280">72%</span>
            </div>
            <div class="flex items-center gap-2 text-xs">
              <span style="color:#6b7280; width:30px">4★</span>
              <div class="flex-1 h-2 rounded-full" style="background:#e5e7eb">
                <div class="h-full rounded-full" style="background:#60a5fa; width:18%"></div>
              </div>
              <span style="color:#6b7280">18%</span>
            </div>
          </div>
          <!-- PDF Footer -->
          <div class="flex justify-between items-center pt-3 text-xs"
               style="border-top:1px solid #e5e7eb; color:#9ca3af">
            <span>Marketing Pro SL · hola@marketingpro.es</span>
            <span>Página 1 de 4</span>
          </div>
        </div>

        <p class="text-xs text-stone-500 text-center mt-3">
          Sin logo de Lokigi · Colores de Marketing Pro SL ✓
        </p>
      </div>

      <!-- Navigation -->
      <div class="flex gap-3">
        <a href="wl_step2_domain.html"
           class="flex-1 px-4 py-3 rounded-2xl border border-white/10 bg-white/5
                  text-stone-300 font-semibold text-sm text-center hover:bg-white/10 no-underline">
          ← Dominio
        </a>
        <a href="wl_step4_preview.html"
           class="flex-1 px-4 py-3 rounded-2xl bg-gradient-to-r from-violet-600 to-indigo-600
                  text-white font-bold text-sm text-center hover:from-violet-500 hover:to-indigo-500 no-underline">
          Ver preview completo →
        </a>
      </div>
    </div>
  </div>

</div>"""
    return page("Reportes PDF", "wl_step3_reports.html", body)


# ─── STEP 4: PREVIEW ─────────────────────────────────────────────────────────

def wl_step4_preview() -> str:
    body = f"""
<div class="mx-auto max-w-4xl px-4 py-10 sm:px-6 pb-20 fade-up">

  <p class="text-xs uppercase tracking-[.2em] text-violet-300/70 mb-1">White Label · Paso 4</p>
  <h1 class="text-3xl font-bold text-white mb-2">Preview de la Experiencia Branded</h1>
  <p class="text-stone-400 text-sm mb-6">
    Así verá tu cliente el panel cuando acceda a
    <strong class="text-violet-300">clientes.marketingpro.com</strong>.
    Zero rastros de Lokigi.
  </p>

  {step_bar(4)}

  <!-- Approval checklist -->
  <div class="rounded-3xl border border-white/10 bg-white/5 p-5 mb-6">
    <h2 class="text-sm font-bold text-stone-300 uppercase tracking-wider mb-4">Checklist pre-activación</h2>
    <div class="grid grid-cols-1 sm:grid-cols-3 gap-3">
      <div class="flex items-center gap-3 p-3 rounded-2xl border border-emerald-500/20 bg-emerald-500/5">
        <span class="text-emerald-400 text-lg">✓</span>
        <div><p class="text-xs font-bold text-emerald-300">Identidad Visual</p><p class="text-xs text-stone-500">Logo + colores configurados</p></div>
      </div>
      <div class="flex items-center gap-3 p-3 rounded-2xl border border-amber-500/20 bg-amber-500/5">
        <span class="text-amber-400 text-lg">⏳</span>
        <div><p class="text-xs font-bold text-amber-300">Dominio</p><p class="text-xs text-stone-500">SSL en propagación</p></div>
      </div>
      <div class="flex items-center gap-3 p-3 rounded-2xl border border-emerald-500/20 bg-emerald-500/5">
        <span class="text-emerald-400 text-lg">✓</span>
        <div><p class="text-xs font-bold text-emerald-300">Reportes PDF</p><p class="text-xs text-stone-500">Plantilla configurada</p></div>
      </div>
    </div>
  </div>

  <!-- Full branded preview mockup -->
  <div class="rounded-3xl border border-white/10 overflow-hidden">

    <!-- Branded top bar -->
    <div class="flex items-center gap-4 px-5 py-3" style="background:#2563EB">
      <div class="w-8 h-8 rounded-lg bg-white/20 flex items-center justify-center font-black text-white text-sm">MP</div>
      <span class="font-bold text-white">Marketing Pro SL</span>
      <span class="ml-auto text-xs text-white/70">Panel de Reputación</span>
      <div class="w-7 h-7 rounded-full bg-white/20 flex items-center justify-center text-white text-xs">👤</div>
    </div>

    <!-- Sidebar + content -->
    <div class="flex" style="background:#0f172a; min-height:480px">
      <!-- Sidebar -->
      <div class="w-44 flex-shrink-0 border-r border-white/8 p-4 space-y-1">
        <div class="px-3 py-2 rounded-lg text-xs font-semibold text-white" style="background:#2563EB22; border:1px solid #2563EB44">📊 Dashboard</div>
        <div class="px-3 py-2 rounded-lg text-xs text-stone-400 hover:bg-white/5">⭐ Reseñas</div>
        <div class="px-3 py-2 rounded-lg text-xs text-stone-400 hover:bg-white/5">💬 Respuestas</div>
        <div class="px-3 py-2 rounded-lg text-xs text-stone-400 hover:bg-white/5">📄 Informes</div>
        <div class="px-3 py-2 rounded-lg text-xs text-stone-400 hover:bg-white/5">⚙️ Ajustes</div>
        <div class="pt-6 mt-6 border-t border-white/10">
          <p class="text-xs text-stone-600 px-2">Restaurante La Pepita</p>
          <p class="text-xs text-stone-700 px-2 mt-0.5">ID: usr_abc123</p>
        </div>
      </div>

      <!-- Main content -->
      <div class="flex-1 p-6">
        <div class="flex items-center justify-between mb-5 flex-wrap gap-3">
          <div>
            <p class="text-xs text-stone-500">Buenos días,</p>
            <p class="text-lg font-bold text-white">Restaurante La Pepita 🍽️</p>
          </div>
          <button class="px-4 py-2 rounded-xl text-white text-xs font-bold" style="background:#2563EB">
            + Nueva respuesta
          </button>
        </div>

        <!-- KPI grid -->
        <div class="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-5">
          <div class="rounded-xl p-3 text-center" style="background:#1e293b">
            <p class="text-xl font-black text-white">4.7★</p>
            <p class="text-xs text-stone-400 mt-0.5">Nota media</p>
          </div>
          <div class="rounded-xl p-3 text-center" style="background:#1e293b">
            <p class="text-xl font-black" style="color:#2563EB">142</p>
            <p class="text-xs text-stone-400 mt-0.5">Total reseñas</p>
          </div>
          <div class="rounded-xl p-3 text-center" style="background:#1e293b">
            <p class="text-xl font-black text-emerald-400">+12</p>
            <p class="text-xs text-stone-400 mt-0.5">Este mes</p>
          </div>
          <div class="rounded-xl p-3 text-center" style="background:#1e293b">
            <p class="text-xl font-black text-white">96%</p>
            <p class="text-xs text-stone-400 mt-0.5">Respondidas</p>
          </div>
        </div>

        <!-- Recent reviews -->
        <p class="text-xs font-bold text-stone-400 uppercase tracking-wider mb-3">Últimas reseñas</p>
        <div class="space-y-2">
          <div class="flex items-start gap-3 p-3 rounded-xl" style="background:#1e293b">
            <div class="w-7 h-7 rounded-full bg-emerald-500/20 flex items-center justify-center text-xs flex-shrink-0">👤</div>
            <div class="flex-1 min-w-0">
              <div class="flex justify-between gap-2">
                <p class="text-xs font-semibold text-white">María García</p>
                <p class="text-xs text-yellow-400">⭐⭐⭐⭐⭐</p>
              </div>
              <p class="text-xs text-stone-400 mt-0.5 truncate">Increíble experiencia, volveré sin duda...</p>
            </div>
          </div>
          <div class="flex items-start gap-3 p-3 rounded-xl" style="background:#1e293b">
            <div class="w-7 h-7 rounded-full bg-rose-500/20 flex items-center justify-center text-xs flex-shrink-0">👤</div>
            <div class="flex-1 min-w-0">
              <div class="flex justify-between gap-2">
                <p class="text-xs font-semibold text-white">Carlos M.</p>
                <p class="text-xs text-yellow-400">⭐⭐</p>
              </div>
              <p class="text-xs text-stone-400 mt-0.5 truncate">Tardaron demasiado, no recomiendo...</p>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Branded footer -->
    <div class="flex items-center justify-center py-3 border-t border-white/8" style="background:#0a0f1a">
      <p class="text-xs text-stone-700">© 2026 Marketing Pro SL · hola@marketingpro.es</p>
    </div>
  </div>

  <div class="mt-4 flex items-center gap-2 p-4 rounded-2xl border border-emerald-500/20 bg-emerald-500/5">
    <span class="text-emerald-400 text-xl">✓</span>
    <p class="text-sm text-emerald-300 font-semibold">
      Lokigi completamente oculto — el cliente solo ve la marca de <strong>Marketing Pro SL</strong>.
    </p>
  </div>

  <div class="flex gap-3 mt-6">
    <a href="wl_step3_reports.html"
       class="flex-1 px-4 py-3 rounded-2xl border border-white/10 bg-white/5
              text-stone-300 font-semibold text-sm text-center hover:bg-white/10 no-underline">
      ← Reportes
    </a>
    <a href="wl_step5_activate.html"
       class="flex-1 px-4 py-3 rounded-2xl bg-gradient-to-r from-violet-600 to-indigo-600
              text-white font-bold text-sm text-center hover:from-violet-500 hover:to-indigo-500 no-underline">
      Activar marca blanca →
    </a>
  </div>

</div>"""
    return page("Preview Branded", "wl_step4_preview.html", body)


# ─── STEP 5: ACTIVATE ─────────────────────────────────────────────────────────

def wl_step5_activate() -> str:
    body = f"""
<div class="mx-auto max-w-3xl px-4 py-10 sm:px-6 pb-20 fade-up">

  <p class="text-xs uppercase tracking-[.2em] text-violet-300/70 mb-1">White Label · Paso 5</p>
  <h1 class="text-3xl font-bold text-white mb-2">Activar Marca Blanca</h1>
  <p class="text-stone-400 text-sm mb-6">
    Revisa la configuración final y activa la marca blanca para todos tus clientes.
    El cambio es instantáneo gracias al caché Redis.
  </p>

  {step_bar(5)}

  <!-- Final summary -->
  <div class="rounded-3xl border border-white/10 bg-white/5 p-6 mb-6">
    <h2 class="text-sm font-bold text-stone-300 uppercase tracking-wider mb-5">Resumen final de configuración</h2>
    <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">

      <div class="space-y-3">
        <div class="flex items-start gap-3 p-4 rounded-2xl border border-emerald-500/20 bg-emerald-500/5">
          <span class="text-emerald-400 text-lg flex-shrink-0">🎨</span>
          <div>
            <p class="text-xs font-bold text-emerald-300 uppercase tracking-wide mb-2">Identidad Visual</p>
            <p class="text-xs text-stone-400">Logo: marketing_pro_logo.svg</p>
            <p class="text-xs text-stone-400">Color: <span class="text-blue-400 font-mono">#2563EB</span></p>
            <p class="text-xs text-stone-400">Fuente: Inter, sans-serif</p>
            <p class="text-xs text-stone-400">Agencia: Marketing Pro SL</p>
          </div>
        </div>

        <div class="flex items-start gap-3 p-4 rounded-2xl border border-amber-500/20 bg-amber-500/5">
          <span class="text-amber-400 text-lg flex-shrink-0">🌐</span>
          <div>
            <p class="text-xs font-bold text-amber-300 uppercase tracking-wide mb-2">Dominio</p>
            <p class="text-xs text-stone-400 font-mono">clientes.marketingpro.com</p>
            <p class="text-xs text-stone-400">CNAME: ✓ Propagado</p>
            <p class="text-xs text-amber-400">SSL: ⏳ En propagación</p>
          </div>
        </div>
      </div>

      <div class="space-y-3">
        <div class="flex items-start gap-3 p-4 rounded-2xl border border-emerald-500/20 bg-emerald-500/5">
          <span class="text-emerald-400 text-lg flex-shrink-0">📄</span>
          <div>
            <p class="text-xs font-bold text-emerald-300 uppercase tracking-wide mb-2">Reportes PDF</p>
            <p class="text-xs text-stone-400">Cabecera: logo izquierda</p>
            <p class="text-xs text-stone-400">Pie: Marketing Pro SL</p>
            <p class="text-xs text-stone-400">Lokigi: oculto ✓</p>
          </div>
        </div>

        <div class="flex items-start gap-3 p-4 rounded-2xl border border-violet-500/20 bg-violet-500/5">
          <span class="text-violet-400 text-lg flex-shrink-0">⚡</span>
          <div>
            <p class="text-xs font-bold text-violet-300 uppercase tracking-wide mb-2">Rendimiento</p>
            <p class="text-xs text-stone-400">Cache: Redis L1+L2+L3</p>
            <p class="text-xs text-stone-400">TTL: 300 s</p>
            <p class="text-xs text-stone-400">Latencia tema: &lt; 2 ms</p>
          </div>
        </div>
      </div>
    </div>
  </div>

  <!-- What happens on activation -->
  <div class="rounded-3xl border border-white/10 bg-white/5 p-6 mb-6">
    <h2 class="text-sm font-bold text-stone-300 uppercase tracking-wider mb-4">¿Qué ocurre al activar?</h2>
    <div class="space-y-3">
      <div class="flex items-start gap-3">
        <div class="w-6 h-6 rounded-full bg-violet-500/20 flex items-center justify-center
                    text-violet-300 text-xs font-black flex-shrink-0 mt-0.5">1</div>
        <div>
          <p class="text-sm font-semibold text-white">BrandTheme escrito en Postgres</p>
          <p class="text-xs text-stone-500">Se actualiza la fila de Organization con primary_color, logo_url, agency_name, domain.</p>
        </div>
      </div>
      <div class="flex items-start gap-3">
        <div class="w-6 h-6 rounded-full bg-violet-500/20 flex items-center justify-center
                    text-violet-300 text-xs font-black flex-shrink-0 mt-0.5">2</div>
        <div>
          <p class="text-sm font-semibold text-white">Cache Redis invalidado</p>
          <p class="text-xs text-stone-500">ThemeService.invalidate(domain) borra L1+L2 para forzar relecture inmediata.</p>
        </div>
      </div>
      <div class="flex items-start gap-3">
        <div class="w-6 h-6 rounded-full bg-violet-500/20 flex items-center justify-center
                    text-violet-300 text-xs font-black flex-shrink-0 mt-0.5">3</div>
        <div>
          <p class="text-sm font-semibold text-white">ThemeMiddleware activo en todos los requests</p>
          <p class="text-xs text-stone-500">Cada request al dominio personalizado recibe el BrandTheme correcto en &lt; 2 ms (Redis hit).</p>
        </div>
      </div>
      <div class="flex items-start gap-3">
        <div class="w-6 h-6 rounded-full bg-violet-500/20 flex items-center justify-center
                    text-violet-300 text-xs font-black flex-shrink-0 mt-0.5">4</div>
        <div>
          <p class="text-sm font-semibold text-white">PDFs generados con tu marca</p>
          <p class="text-xs text-stone-500">BrandedPDFRenderer inyecta logo_url + colores en la plantilla Jinja2 antes de pasarla a WeasyPrint.</p>
        </div>
      </div>
    </div>
  </div>

  <!-- Warning about SSL -->
  <div class="rounded-3xl border border-amber-500/20 bg-amber-500/5 p-5 mb-6 flex items-start gap-4">
    <span class="text-2xl flex-shrink-0">⚠️</span>
    <div>
      <p class="text-sm font-bold text-amber-300 mb-1">SSL pendiente — activación parcial</p>
      <p class="text-xs text-stone-400">
        Puedes activar la configuración ahora. El dominio personalizado funcionará
        en cuanto el certificado SSL termine de propagarse (estimado: 15 min).
        Mientras tanto, la configuración estará activa en el dominio de staging.
      </p>
    </div>
  </div>

  <!-- CTA -->
  <div class="flex gap-3">
    <a href="wl_step4_preview.html"
       class="flex-1 px-5 py-3.5 rounded-2xl border border-white/10 bg-white/5
              text-stone-300 font-semibold text-sm text-center hover:bg-white/10 no-underline">
      ← Preview
    </a>
    <button
       class="flex-1 px-5 py-3.5 rounded-2xl bg-gradient-to-r from-emerald-600 to-teal-600
              text-white font-bold text-sm text-center hover:from-emerald-500 hover:to-teal-500 cursor-pointer border-0">
      🚀 Activar Marca Blanca
    </button>
  </div>

  <!-- Post-activation state (would show after click) -->
  <div class="mt-5 p-5 rounded-3xl border border-emerald-500/30 bg-emerald-950/30">
    <div class="flex items-center gap-3 mb-3">
      <span class="text-2xl">🎉</span>
      <p class="text-sm font-bold text-emerald-300">¡Marca blanca activada con éxito!</p>
    </div>
    <p class="text-xs text-stone-400 mb-3">
      La configuración se ha guardado y el cache Redis ha sido invalidado.
      Tus 12 clientes ahora ven el panel con la identidad de Marketing Pro SL.
    </p>
    <div class="flex gap-3 flex-wrap">
      <a href="wl_hub.html"
         class="px-4 py-2 rounded-xl border border-emerald-500/30 text-emerald-300 text-xs font-semibold no-underline hover:bg-emerald-500/10">
        Ver estado del tenant →
      </a>
      <a href="../enterprise_hub.html"
         class="px-4 py-2 rounded-xl border border-white/10 bg-white/5 text-stone-300 text-xs font-semibold no-underline hover:bg-white/10">
        Ir al Dashboard Hub →
      </a>
    </div>
  </div>

</div>"""
    return page("Activar Marca Blanca", "wl_step5_activate.html", body)


# ─── RENDER ───────────────────────────────────────────────────────────────────

def main() -> None:
    files = [
        ("wl_hub.html",            wl_hub()),
        ("wl_step1_identity.html", wl_step1_identity()),
        ("wl_step2_domain.html",   wl_step2_domain()),
        ("wl_step3_reports.html",  wl_step3_reports()),
        ("wl_step4_preview.html",  wl_step4_preview()),
        ("wl_step5_activate.html", wl_step5_activate()),
    ]

    for fname, html in files:
        path = OUT_DIR / fname
        path.write_text(html, encoding="utf-8")
        print(f"✓ {path}")

    print("\n📌 Abriendo en el navegador:")
    for fname, _ in files:
        url = f"http://localhost:3000/enterprise/white_label/{fname}"
        webbrowser.open(url)
        print(f"   {url}")


if __name__ == "__main__":
    main()
