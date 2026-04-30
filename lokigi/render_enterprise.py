"""
Renderiza el flujo White Label & Multi-Tenant del Plan Enterprise / Agency
como páginas HTML estáticas navegables en frontend/static/enterprise/.

Pasos del flujo:
  1. enterprise_landing.html       — Página de presentación del plan (pricing, features)
  2. step1_brand.html              — Configuración de marca (logo, colores, dominio)
  3. step2_tenants.html            — Panel de tenants / clientes de la agencia
  4. step3_locations.html          — Vista consolidada de ubicaciones multi-tenant
  5. step4_roles.html              — Gestión de accesos y roles (SuperAdmin / Manager / Viewer)
  6. step5_dashboard_agency.html   — Dashboard consolidado de la agencia (vista SuperAdmin)
"""
from __future__ import annotations
import webbrowser
from pathlib import Path

ROOT = Path(__file__).parent
OUT_DIR = ROOT / "frontend" / "static" / "enterprise"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# ─── NAV helper ──────────────────────────────────────────────────────────────

PAGES = [
    ("enterprise_landing.html",     "🏢 Plan Enterprise"),
    ("step1_brand.html",            "1 · Marca"),
    ("step2_tenants.html",          "2 · Tenants"),
    ("step3_locations.html",        "3 · Ubicaciones"),
    ("step4_roles.html",            "4 · Roles"),
    ("step5_dashboard_agency.html", "5 · Dashboard Agency"),
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
  <div class="flex items-center gap-2.5 mr-auto">
    <a href="enterprise_landing.html"
       class="flex items-center justify-center w-8 h-8 rounded-lg
              bg-gradient-to-br from-violet-500 to-indigo-600
              text-white font-black text-sm no-underline">L</a>
    <a href="enterprise_landing.html"
       class="font-bold text-white text-base no-underline">Lokigi</a>
    <span class="px-2.5 py-0.5 rounded-full bg-violet-500/20 text-violet-300
                 text-xs font-bold uppercase tracking-wider">Enterprise</span>
  </div>
  {links}
</nav>"""


def page(title: str, active: str, body: str) -> str:
    return f"""<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{title} | Lokigi Enterprise</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <style>
    body {{ font-family: Arial, "Helvetica Neue", sans-serif; }}
    .no-underline {{ text-decoration: none; }}
    @keyframes fadeUp {{
      from {{ opacity: 0; transform: translateY(14px); }}
      to   {{ opacity: 1; transform: translateY(0); }}
    }}
    .fade-up {{ animation: fadeUp .35s ease both; }}
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
    input[type="color"] {{
      padding: 4px 6px;
      height: 42px;
      cursor: pointer;
    }}
    select option {{ background: #1c1917; }}
    .badge-role-sa   {{ background: rgba(167,139,250,.18); color: #c4b5fd; }}
    .badge-role-mgr  {{ background: rgba(251,191,36,.15);  color: #fcd34d; }}
    .badge-role-view {{ background: rgba(148,163,184,.12); color: #94a3b8; }}
  </style>
</head>
<body class="min-h-screen bg-stone-950 text-stone-100">
{nav_bar(active)}
{body}
</body>
</html>"""


# ─── STEP 0 — Landing / Pricing ──────────────────────────────────────────────

def enterprise_landing() -> str:
    body = """
<div class="mx-auto max-w-4xl px-4 py-12 sm:px-6 pb-20 fade-up">

  <!-- Hero -->
  <div class="text-center mb-14">
    <span class="inline-flex px-3 py-1 rounded-full bg-violet-500/15 text-violet-300
                 text-xs font-bold uppercase tracking-widest mb-4">Plan Enterprise / Agency</span>
    <h1 class="text-5xl font-black text-white leading-tight mb-4">
      White Label &amp;<br>Multi-Tenant
    </h1>
    <p class="text-stone-400 text-lg max-w-2xl mx-auto leading-relaxed">
      Vende Lokigi como tu propio producto. Tu logo, tus colores, tu dominio.
      Gestiona todos tus clientes desde un panel unificado con aislamiento total de datos.
    </p>
    <div class="flex items-center justify-center gap-4 mt-8 flex-wrap">
      <a href="step1_brand.html"
         class="px-8 py-4 rounded-2xl bg-gradient-to-r from-violet-600 to-indigo-600
                text-white font-bold text-lg hover:from-violet-500 hover:to-indigo-500
                no-underline transition">
        Configurar mi agencia →
      </a>
      <span class="text-stone-400 text-sm">desde <strong class="text-white">$199 / mes</strong> · 14 días gratis</span>
    </div>
  </div>

  <!-- Pricing cards -->
  <div class="grid grid-cols-1 md:grid-cols-3 gap-5 mb-14">

    <div class="rounded-3xl border border-white/10 bg-white/5 p-6">
      <p class="text-xs uppercase tracking-widest text-stone-400 mb-2">Starter</p>
      <p class="text-3xl font-black text-white mb-1">€29<span class="text-base font-normal text-stone-400">/mes</span></p>
      <p class="text-stone-400 text-sm mb-5">1 negocio · respuestas IA · reportes</p>
      <ul class="space-y-2 text-sm text-stone-300">
        <li class="flex gap-2"><span class="text-emerald-400">✓</span> Auto-reply con IA</li>
        <li class="flex gap-2"><span class="text-emerald-400">✓</span> Reporte mensual PDF</li>
        <li class="flex gap-2"><span class="text-emerald-400">✓</span> Sentiment snapshot</li>
        <li class="flex gap-2 opacity-40"><span>✗</span> Radar competitivo</li>
        <li class="flex gap-2 opacity-40"><span>✗</span> White label</li>
      </ul>
    </div>

    <div class="rounded-3xl border border-emerald-500/25 bg-emerald-500/5 p-6">
      <p class="text-xs uppercase tracking-widest text-emerald-400 mb-2">Growth</p>
      <p class="text-3xl font-black text-white mb-1">€79<span class="text-base font-normal text-stone-400">/mes</span></p>
      <p class="text-stone-400 text-sm mb-5">1 negocio · scraping + IA · radar</p>
      <ul class="space-y-2 text-sm text-stone-300">
        <li class="flex gap-2"><span class="text-emerald-400">✓</span> Todo lo de Starter</li>
        <li class="flex gap-2"><span class="text-emerald-400">✓</span> Radar de Guerra competitivo</li>
        <li class="flex gap-2"><span class="text-emerald-400">✓</span> Keyword Tracker SERP</li>
        <li class="flex gap-2"><span class="text-emerald-400">✓</span> Live Feed inteligencia</li>
        <li class="flex gap-2 opacity-40"><span>✗</span> White label / multi-tenant</li>
      </ul>
    </div>

    <div class="rounded-3xl border border-violet-500/35 bg-violet-500/8 p-6 relative overflow-hidden">
      <div class="absolute top-4 right-4 px-2.5 py-1 rounded-full bg-violet-500/30
                  text-violet-200 text-xs font-bold uppercase tracking-wider">Nuevo</div>
      <p class="text-xs uppercase tracking-widest text-violet-400 mb-2">Enterprise / Agency</p>
      <p class="text-3xl font-black text-white mb-1">$199+<span class="text-base font-normal text-stone-400">/mes</span></p>
      <p class="text-stone-400 text-sm mb-5">∞ negocios · white label · multi-tenant</p>
      <ul class="space-y-2 text-sm text-stone-300">
        <li class="flex gap-2"><span class="text-violet-400">✓</span> Todo lo de Growth</li>
        <li class="flex gap-2"><span class="text-violet-400">✓</span> Tu logo, colores y dominio</li>
        <li class="flex gap-2"><span class="text-violet-400">✓</span> Gestión multi-tenant</li>
        <li class="flex gap-2"><span class="text-violet-400">✓</span> Roles: SuperAdmin / Manager / Viewer</li>
        <li class="flex gap-2"><span class="text-violet-400">✓</span> Vista consolidada de agencia</li>
        <li class="flex gap-2"><span class="text-violet-400">✓</span> API white-label dedicada</li>
      </ul>
    </div>

  </div>

  <!-- Feature pillars -->
  <h2 class="text-2xl font-bold text-white mb-6 text-center">El flujo de despliegue en 4 pasos</h2>
  <div class="grid grid-cols-1 sm:grid-cols-2 gap-5 mb-14">

    <a href="step1_brand.html" class="block rounded-3xl border border-white/10 bg-white/5 p-6 hover:bg-white/8 no-underline group">
      <div class="w-11 h-11 rounded-2xl bg-violet-500/15 flex items-center justify-center text-2xl mb-4">🎨</div>
      <h3 class="text-white font-bold text-lg mb-2 group-hover:text-violet-300 transition">1 · Configuración de Marca</h3>
      <p class="text-stone-400 text-sm leading-relaxed">
        Sube tu logo, define tu paleta de colores primaria y configura tu propio dominio
        (<code class="text-violet-300">qa.tuagencia.com</code>). Lokigi desaparece del frontend.
      </p>
    </a>

    <a href="step2_tenants.html" class="block rounded-3xl border border-white/10 bg-white/5 p-6 hover:bg-white/8 no-underline group">
      <div class="w-11 h-11 rounded-2xl bg-indigo-500/15 flex items-center justify-center text-2xl mb-4">🏗️</div>
      <h3 class="text-white font-bold text-lg mb-2 group-hover:text-indigo-300 transition">2 · Aislamiento de Datos</h3>
      <p class="text-stone-400 text-sm leading-relaxed">
        FastAPI gestiona múltiples Tenants con Row-Level Security en PostgreSQL.
        Cada cliente solo ve sus ubicaciones. La agencia ve el consolidado total.
      </p>
    </a>

    <a href="step3_locations.html" class="block rounded-3xl border border-white/10 bg-white/5 p-6 hover:bg-white/8 no-underline group">
      <div class="w-11 h-11 rounded-2xl bg-sky-500/15 flex items-center justify-center text-2xl mb-4">📍</div>
      <h3 class="text-white font-bold text-lg mb-2 group-hover:text-sky-300 transition">3 · Vista Consolidada</h3>
      <p class="text-stone-400 text-sm leading-relaxed">
        El SuperAdmin ve todas las ubicaciones de todos los clientes en un solo mapa.
        Filtros por tenant, ciudad, rating y estado de alerta.
      </p>
    </a>

    <a href="step4_roles.html" class="block rounded-3xl border border-white/10 bg-white/5 p-6 hover:bg-white/8 no-underline group">
      <div class="w-11 h-11 rounded-2xl bg-amber-500/15 flex items-center justify-center text-2xl mb-4">🔐</div>
      <h3 class="text-white font-bold text-lg mb-2 group-hover:text-amber-300 transition">4 · Gestión de Accesos</h3>
      <p class="text-stone-400 text-sm leading-relaxed">
        Tres roles jerárquicos: <strong class="text-violet-300">SuperAdmin</strong> (agencia),
        <strong class="text-amber-300">Manager</strong> (dueño de franquicia) y
        <strong class="text-stone-300">Viewer</strong> (encargado de local).
      </p>
    </a>

  </div>

  <!-- CTA bottom -->
  <div class="rounded-3xl border border-violet-500/25
              bg-gradient-to-br from-violet-950/60 to-indigo-950/60 p-8 text-center">
    <h2 class="text-2xl font-bold text-white mb-3">¿Lista tu agencia?</h2>
    <p class="text-stone-400 mb-6 max-w-lg mx-auto">
      Configura el white label en menos de 10 minutos. Sin código, sin servers propios.
    </p>
    <a href="step1_brand.html"
       class="inline-flex px-8 py-4 rounded-2xl bg-gradient-to-r from-violet-600 to-indigo-600
              text-white font-bold text-base hover:from-violet-500 hover:to-indigo-500
              no-underline transition">
      Empezar configuración →
    </a>
  </div>

</div>"""
    return page("Plan Enterprise — White Label & Multi-Tenant", "enterprise_landing.html", body)


# ─── STEP 1 — Configuración de Marca ─────────────────────────────────────────

def step1_brand() -> str:
    body = """
<div class="mx-auto max-w-3xl px-4 py-10 sm:px-6 pb-20 fade-up">

  <div class="mb-8">
    <p class="text-xs uppercase tracking-[.2em] text-violet-300/70 mb-1">Paso 1 de 4</p>
    <h1 class="text-3xl font-bold text-white">Configuración de Marca</h1>
    <p class="mt-1 text-stone-400 text-sm">
      Personaliza Lokigi con la identidad visual de tu agencia. Tu logo, tu paleta y tu dominio.
    </p>
  </div>

  <!-- Progress bar -->
  <div class="flex gap-2 mb-10">
    <div class="h-1.5 flex-1 rounded-full bg-violet-500"></div>
    <div class="h-1.5 flex-1 rounded-full bg-white/10"></div>
    <div class="h-1.5 flex-1 rounded-full bg-white/10"></div>
    <div class="h-1.5 flex-1 rounded-full bg-white/10"></div>
  </div>

  <div class="space-y-5">

    <!-- Logo -->
    <section class="rounded-3xl border border-white/10 bg-white/5 p-6">
      <div class="flex items-center gap-3 mb-5">
        <div class="w-10 h-10 rounded-2xl bg-violet-500/15 flex items-center justify-center text-xl">🎨</div>
        <div>
          <h2 class="text-base font-semibold text-white m-0">Logo de la Agencia</h2>
          <p class="text-xs text-stone-400 mt-0.5">PNG o SVG · recomendado 200×60 px</p>
        </div>
      </div>

      <div class="border-2 border-dashed border-white/15 rounded-2xl p-8 text-center mb-4 cursor-pointer hover:border-violet-400/40 transition">
        <div class="w-16 h-16 rounded-2xl bg-white/8 flex items-center justify-center text-3xl mx-auto mb-3">📁</div>
        <p class="text-stone-300 font-semibold mb-1">Arrastra tu logo aquí</p>
        <p class="text-stone-500 text-sm">o haz click para explorar archivos</p>
        <p class="text-stone-600 text-xs mt-2">PNG, SVG, WebP · máx. 2 MB</p>
      </div>

      <!-- Preview con logo demo -->
      <div class="rounded-2xl border border-white/10 bg-stone-950 p-4">
        <p class="text-xs text-stone-500 uppercase tracking-wider mb-3">Vista previa del navbar</p>
        <div class="flex items-center gap-3 h-10">
          <div class="w-8 h-8 rounded-lg bg-gradient-to-br from-violet-500 to-indigo-600
                      flex items-center justify-center text-white font-black text-sm">A</div>
          <span class="text-white font-bold text-base">Mi Agencia</span>
          <span class="px-2 py-0.5 rounded-full bg-violet-500/20 text-violet-300 text-xs font-bold">Agency</span>
          <span class="ml-auto text-stone-500 text-xs">powered by Lokigi (oculto)</span>
        </div>
      </div>
    </section>

    <!-- Colores -->
    <section class="rounded-3xl border border-white/10 bg-white/5 p-6">
      <div class="flex items-center gap-3 mb-5">
        <div class="w-10 h-10 rounded-2xl bg-indigo-500/15 flex items-center justify-center text-xl">🖌️</div>
        <div>
          <h2 class="text-base font-semibold text-white m-0">Paleta de Colores</h2>
          <p class="text-xs text-stone-400 mt-0.5">Define el color primario y secundario de tu marca</p>
        </div>
      </div>

      <div class="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-5">
        <div>
          <label class="block text-xs text-stone-400 font-semibold uppercase tracking-wider mb-2">Color primario</label>
          <div class="flex gap-3 items-center">
            <input type="color" value="#7c3aed" class="w-14 flex-shrink-0" />
            <input type="text" value="#7c3aed" placeholder="#7c3aed" class="flex-1" />
          </div>
        </div>
        <div>
          <label class="block text-xs text-stone-400 font-semibold uppercase tracking-wider mb-2">Color secundario / acento</label>
          <div class="flex gap-3 items-center">
            <input type="color" value="#4f46e5" class="w-14 flex-shrink-0" />
            <input type="text" value="#4f46e5" placeholder="#4f46e5" class="flex-1" />
          </div>
        </div>
      </div>

      <!-- Palette preview -->
      <div class="rounded-2xl border border-white/10 bg-stone-950 p-4">
        <p class="text-xs text-stone-500 uppercase tracking-wider mb-3">Vista previa de componentes</p>
        <div class="flex gap-3 flex-wrap items-center">
          <button class="px-5 py-2.5 rounded-xl font-bold text-white text-sm"
                  style="background:linear-gradient(135deg,#7c3aed,#4f46e5)">
            Acción principal
          </button>
          <span class="px-3 py-1 rounded-full text-xs font-bold text-white"
                style="background:#7c3aed">Badge activo</span>
          <div class="w-24 h-2 rounded-full" style="background:linear-gradient(90deg,#7c3aed,#4f46e5)"></div>
        </div>
      </div>
    </section>

    <!-- Dominio -->
    <section class="rounded-3xl border border-white/10 bg-white/5 p-6">
      <div class="flex items-center gap-3 mb-5">
        <div class="w-10 h-10 rounded-2xl bg-sky-500/15 flex items-center justify-center text-xl">🌐</div>
        <div>
          <h2 class="text-base font-semibold text-white m-0">Dominio Personalizado</h2>
          <p class="text-xs text-stone-400 mt-0.5">Apunta un CNAME a nuestro CDN para activar tu subdominio</p>
        </div>
      </div>

      <div class="space-y-4 mb-5">
        <div>
          <label class="block text-xs text-stone-400 font-semibold uppercase tracking-wider mb-2">Tu dominio</label>
          <input type="text" value="qa.miagencia.com" placeholder="app.tuagencia.com" />
        </div>
        <div>
          <label class="block text-xs text-stone-400 font-semibold uppercase tracking-wider mb-2">Nombre de la agencia (público)</label>
          <input type="text" value="Mi Agencia Digital" placeholder="Nombre que verán tus clientes" />
        </div>
      </div>

      <!-- DNS instructions -->
      <div class="rounded-2xl border border-amber-500/20 bg-amber-500/5 p-4">
        <p class="text-xs font-bold text-amber-300 uppercase tracking-wider mb-3">⚙️ Instrucciones DNS</p>
        <p class="text-stone-300 text-sm mb-3">Añade este registro CNAME en tu proveedor de DNS:</p>
        <div class="rounded-xl bg-stone-950 border border-white/10 p-3 font-mono text-xs text-stone-300 space-y-1">
          <div><span class="text-stone-500">Tipo:</span> CNAME</div>
          <div><span class="text-stone-500">Host:</span> <span class="text-violet-300">qa</span></div>
          <div><span class="text-stone-500">Valor:</span> <span class="text-emerald-300">agency.lokigi.io</span></div>
          <div><span class="text-stone-500">TTL:</span> Auto</div>
        </div>
        <div class="flex items-center gap-2 mt-3">
          <div class="w-2 h-2 rounded-full bg-amber-400 animate-pulse"></div>
          <span class="text-amber-300 text-xs font-semibold">Verificación pendiente</span>
        </div>
      </div>
    </section>

    <!-- SSL / SEO -->
    <section class="rounded-3xl border border-white/10 bg-white/5 p-6">
      <div class="flex items-center gap-3 mb-5">
        <div class="w-10 h-10 rounded-2xl bg-emerald-500/15 flex items-center justify-center text-xl">🔒</div>
        <div>
          <h2 class="text-base font-semibold text-white m-0">SSL y Configuración Avanzada</h2>
          <p class="text-xs text-stone-400 mt-0.5">Certificado TLS automático · sin coste adicional</p>
        </div>
      </div>
      <div class="divide-y divide-white/5">
        <div class="flex justify-between items-center py-3">
          <span class="text-sm text-stone-400">Certificado TLS (Let's Encrypt)</span>
          <span class="px-2.5 py-1 rounded-full bg-emerald-500/15 text-emerald-300 text-xs font-bold">Auto-renovado</span>
        </div>
        <div class="flex justify-between items-center py-3">
          <span class="text-sm text-stone-400">Footer "Powered by Lokigi"</span>
          <div class="flex items-center gap-2">
            <div class="w-10 h-5 rounded-full bg-stone-700 relative cursor-pointer">
              <div class="absolute left-0.5 top-0.5 w-4 h-4 rounded-full bg-stone-400 transition-transform"></div>
            </div>
            <span class="text-stone-400 text-xs">Oculto</span>
          </div>
        </div>
        <div class="flex justify-between items-center py-3">
          <span class="text-sm text-stone-400">Emails transaccionales con tu dominio</span>
          <span class="px-2.5 py-1 rounded-full bg-emerald-500/15 text-emerald-300 text-xs font-bold">Habilitado</span>
        </div>
      </div>
    </section>

  </div>

  <!-- Navigation -->
  <div class="flex justify-between items-center mt-8">
    <a href="enterprise_landing.html"
       class="px-5 py-3 rounded-2xl border border-white/10 bg-white/5
              text-stone-300 font-semibold text-sm hover:bg-white/10 no-underline">
      ← Atrás
    </a>
    <a href="step2_tenants.html"
       class="px-8 py-3 rounded-2xl bg-gradient-to-r from-violet-600 to-indigo-600
              text-white font-bold text-sm hover:from-violet-500 hover:to-indigo-500 no-underline">
      Siguiente: Tenants →
    </a>
  </div>
</div>"""
    return page("Paso 1 — Configuración de Marca", "step1_brand.html", body)


# ─── STEP 2 — Panel de Tenants ────────────────────────────────────────────────

def step2_tenants() -> str:
    tenants = [
        {"id": "T-001", "name": "Cadena Pizzas Norte", "locations": 8, "plan": "Growth",
         "rating": 4.3, "alerts": 2, "status": "active", "manager": "Pedro Álvarez"},
        {"id": "T-002", "name": "Franquicia Café Rápido", "locations": 14, "plan": "Growth",
         "rating": 4.0, "alerts": 0, "status": "active", "manager": "Laura Méndez"},
        {"id": "T-003", "name": "Restaurantes El Mar", "locations": 5, "plan": "Starter",
         "rating": 4.6, "alerts": 1, "status": "active", "manager": "Javier Ruiz"},
        {"id": "T-004", "name": "Hoteles Solimar", "locations": 3, "plan": "Growth",
         "rating": 3.9, "alerts": 4, "status": "trial", "manager": "Ana Costa"},
        {"id": "T-005", "name": "Demo Inactivo", "locations": 1, "plan": "Starter",
         "rating": None, "alerts": 0, "status": "paused", "manager": "—"},
    ]

    STATUS_BADGE = {
        "active": '<span class="px-2.5 py-1 rounded-full bg-emerald-500/15 text-emerald-300 text-xs font-bold">Activo</span>',
        "trial":  '<span class="px-2.5 py-1 rounded-full bg-amber-500/15  text-amber-300  text-xs font-bold">Trial</span>',
        "paused": '<span class="px-2.5 py-1 rounded-full bg-stone-500/20  text-stone-400  text-xs font-bold">Pausado</span>',
    }
    PLAN_BADGE = {
        "Growth":  '<span class="px-2.5 py-1 rounded-full bg-emerald-500/15 text-emerald-300 text-xs font-bold">Growth</span>',
        "Starter": '<span class="px-2.5 py-1 rounded-full bg-sky-500/15     text-sky-300    text-xs font-bold">Starter</span>',
    }

    rows = ""
    for t in tenants:
        rating_str = f"{t['rating']}★" if t["rating"] else "—"
        alerts_str = (
            f'<span class="font-bold text-rose-300">{t["alerts"]}</span>'
            if t["alerts"] > 0 else
            '<span class="text-stone-500">0</span>'
        )
        rows += f"""
        <tr class="border-b border-white/5 hover:bg-white/3">
          <td class="py-3 pr-4 font-mono text-xs text-stone-500">{t["id"]}</td>
          <td class="py-3 pr-4 font-semibold text-stone-100">{t["name"]}</td>
          <td class="py-3 pr-4 text-center text-stone-200">{t["locations"]}</td>
          <td class="py-3 pr-4">{PLAN_BADGE[t["plan"]]}</td>
          <td class="py-3 pr-4 font-semibold text-stone-200">{rating_str}</td>
          <td class="py-3 pr-4 text-center">{alerts_str}</td>
          <td class="py-3 pr-4 text-sm text-stone-400">{t["manager"]}</td>
          <td class="py-3">{STATUS_BADGE[t["status"]]}</td>
        </tr>"""

    total_locs = sum(t["locations"] for t in tenants)
    active_ct  = sum(1 for t in tenants if t["status"] == "active")
    alert_ct   = sum(t["alerts"] for t in tenants)

    body = f"""
<div class="mx-auto max-w-5xl px-4 py-10 sm:px-6 pb-20 fade-up">

  <div class="mb-8">
    <p class="text-xs uppercase tracking-[.2em] text-violet-300/70 mb-1">Paso 2 de 4</p>
    <h1 class="text-3xl font-bold text-white">Gestión de Tenants</h1>
    <p class="mt-1 text-stone-400 text-sm">
      Cada tenant es un cliente de tu agencia. Datos 100 % aislados entre sí.
    </p>
  </div>

  <!-- Progress bar -->
  <div class="flex gap-2 mb-10">
    <div class="h-1.5 flex-1 rounded-full bg-violet-500"></div>
    <div class="h-1.5 flex-1 rounded-full bg-violet-500"></div>
    <div class="h-1.5 flex-1 rounded-full bg-white/10"></div>
    <div class="h-1.5 flex-1 rounded-full bg-white/10"></div>
  </div>

  <!-- KPI strip -->
  <div class="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-8">
    <div class="rounded-2xl border border-white/10 bg-white/5 p-4 text-center">
      <p class="text-3xl font-black text-white">{len(tenants)}</p>
      <p class="text-xs uppercase tracking-wider text-stone-400 mt-1">Tenants totales</p>
    </div>
    <div class="rounded-2xl border border-emerald-500/20 bg-emerald-500/5 p-4 text-center">
      <p class="text-3xl font-black text-emerald-300">{active_ct}</p>
      <p class="text-xs uppercase tracking-wider text-stone-400 mt-1">Activos</p>
    </div>
    <div class="rounded-2xl border border-white/10 bg-white/5 p-4 text-center">
      <p class="text-3xl font-black text-white">{total_locs}</p>
      <p class="text-xs uppercase tracking-wider text-stone-400 mt-1">Ubicaciones</p>
    </div>
    <div class="rounded-2xl border border-rose-500/20 bg-rose-500/5 p-4 text-center">
      <p class="text-3xl font-black text-rose-300">{alert_ct}</p>
      <p class="text-xs uppercase tracking-wider text-stone-400 mt-1">Alertas abiertas</p>
    </div>
  </div>

  <!-- Tenants table -->
  <div class="rounded-3xl border border-white/10 bg-white/5 p-0 overflow-hidden mb-6">
    <div class="flex items-center justify-between px-6 py-4 border-b border-white/10">
      <h2 class="text-base font-semibold text-white m-0">Lista de clientes</h2>
      <a href="step4_roles.html"
         class="px-4 py-2 rounded-xl bg-violet-600 text-white text-sm font-bold
                hover:bg-violet-500 no-underline">
        + Nuevo tenant
      </a>
    </div>
    <div class="overflow-x-auto">
      <table class="min-w-full text-sm">
        <thead>
          <tr class="border-b border-white/10 text-stone-400 text-xs uppercase tracking-wider">
            <th class="py-3 pr-4 pl-6 text-left font-semibold">ID</th>
            <th class="py-3 pr-4 text-left font-semibold">Cliente</th>
            <th class="py-3 pr-4 text-center font-semibold">Locs.</th>
            <th class="py-3 pr-4 text-left font-semibold">Plan</th>
            <th class="py-3 pr-4 text-left font-semibold">Rating</th>
            <th class="py-3 pr-4 text-center font-semibold">Alertas</th>
            <th class="py-3 pr-4 text-left font-semibold">Manager</th>
            <th class="py-3 pr-6 text-left font-semibold">Estado</th>
          </tr>
        </thead>
        <tbody class="text-stone-200">
          {rows}
        </tbody>
      </table>
    </div>
  </div>

  <!-- Data isolation callout -->
  <div class="rounded-3xl border border-indigo-500/20 bg-indigo-500/5 p-6 mb-8">
    <div class="flex items-start gap-4">
      <div class="w-10 h-10 rounded-2xl bg-indigo-500/20 flex items-center justify-center text-xl flex-shrink-0">🔒</div>
      <div>
        <h3 class="text-white font-bold text-base mb-2">Aislamiento de datos — Row-Level Security (RLS)</h3>
        <p class="text-stone-400 text-sm leading-relaxed mb-3">
          FastAPI inyecta el <code class="text-indigo-300">tenant_id</code> en cada query a PostgreSQL.
          Las políticas RLS garantizan que un tenant nunca pueda acceder a datos de otro,
          incluso si se produce un error de lógica de aplicación.
        </p>
        <div class="rounded-xl bg-stone-950 border border-white/10 p-4 font-mono text-xs text-stone-300 space-y-1">
          <div class="text-stone-500">-- Política RLS en tabla reviews</div>
          <div><span class="text-violet-300">CREATE POLICY</span> tenant_isolation <span class="text-violet-300">ON</span> reviews</div>
          <div class="pl-4"><span class="text-violet-300">USING</span> (tenant_id = current_setting(<span class="text-amber-300">'app.tenant_id'</span>)::<span class="text-sky-300">uuid</span>);</div>
        </div>
      </div>
    </div>
  </div>

  <!-- Navigation -->
  <div class="flex justify-between items-center mt-8">
    <a href="step1_brand.html"
       class="px-5 py-3 rounded-2xl border border-white/10 bg-white/5
              text-stone-300 font-semibold text-sm hover:bg-white/10 no-underline">
      ← Atrás
    </a>
    <a href="step3_locations.html"
       class="px-8 py-3 rounded-2xl bg-gradient-to-r from-violet-600 to-indigo-600
              text-white font-bold text-sm hover:from-violet-500 hover:to-indigo-500 no-underline">
      Siguiente: Vista consolidada →
    </a>
  </div>
</div>"""
    return page("Paso 2 — Gestión de Tenants", "step2_tenants.html", body)


# ─── STEP 3 — Vista consolidada de ubicaciones ───────────────────────────────

def step3_locations() -> str:
    locations = [
        {"tenant": "Cadena Pizzas Norte", "name": "Pizza Norte — Malasaña", "city": "Madrid",
         "rating": 4.5, "reviews_30d": 22, "alerts": 1, "reply_pct": 91, "status": "ok"},
        {"tenant": "Cadena Pizzas Norte", "name": "Pizza Norte — Chamberí",  "city": "Madrid",
         "rating": 4.2, "reviews_30d": 18, "alerts": 1, "reply_pct": 78, "status": "warn"},
        {"tenant": "Cadena Pizzas Norte", "name": "Pizza Norte — Vallecas",  "city": "Madrid",
         "rating": 3.9, "reviews_30d": 9,  "alerts": 0, "reply_pct": 55, "status": "warn"},
        {"tenant": "Franquicia Café Rápido", "name": "Café Rápido — Gran Vía",   "city": "Madrid",
         "rating": 4.4, "reviews_30d": 34, "alerts": 0, "reply_pct": 94, "status": "ok"},
        {"tenant": "Franquicia Café Rápido", "name": "Café Rápido — Retiro",     "city": "Madrid",
         "rating": 4.1, "reviews_30d": 27, "alerts": 0, "reply_pct": 88, "status": "ok"},
        {"tenant": "Franquicia Café Rápido", "name": "Café Rápido — Atocha",     "city": "Madrid",
         "rating": 3.7, "reviews_30d": 11, "alerts": 0, "reply_pct": 62, "status": "alert"},
        {"tenant": "Restaurantes El Mar",    "name": "El Mar — Barceloneta",      "city": "Barcelona",
         "rating": 4.8, "reviews_30d": 41, "alerts": 1, "reply_pct": 97, "status": "ok"},
        {"tenant": "Hoteles Solimar",        "name": "Hotel Solimar Marbella",    "city": "Marbella",
         "rating": 4.0, "reviews_30d": 15, "alerts": 4, "reply_pct": 44, "status": "alert"},
    ]

    STATUS_ICON = {
        "ok":    '<span class="w-2.5 h-2.5 rounded-full bg-emerald-400 inline-block"></span>',
        "warn":  '<span class="w-2.5 h-2.5 rounded-full bg-amber-400  inline-block"></span>',
        "alert": '<span class="w-2.5 h-2.5 rounded-full bg-rose-400   inline-block animate-pulse"></span>',
    }

    rows = ""
    for loc in locations:
        reply_color = "text-emerald-300" if loc["reply_pct"] >= 80 else ("text-amber-300" if loc["reply_pct"] >= 60 else "text-rose-300")
        rows += f"""
        <tr class="border-b border-white/5 hover:bg-white/3">
          <td class="py-3 pr-4 pl-6 text-sm text-stone-400">{loc["tenant"]}</td>
          <td class="py-3 pr-4 font-semibold text-stone-100 text-sm">{loc["name"]}</td>
          <td class="py-3 pr-4 text-sm text-stone-300">{loc["city"]}</td>
          <td class="py-3 pr-4 font-bold text-stone-200">{loc["rating"]}★</td>
          <td class="py-3 pr-4 text-center text-stone-300">{loc["reviews_30d"]}</td>
          <td class="py-3 pr-4 font-bold {reply_color}">{loc["reply_pct"]}%</td>
          <td class="py-3 pr-4 text-center">
            {"<span class='text-rose-300 font-bold'>" + str(loc["alerts"]) + "</span>" if loc["alerts"] else "<span class='text-stone-500'>0</span>"}
          </td>
          <td class="py-3 pr-6 flex items-center gap-2 pt-4">{STATUS_ICON[loc["status"]]}</td>
        </tr>"""

    avg_rating = round(sum(l["rating"] for l in locations) / len(locations), 2)
    total_reviews = sum(l["reviews_30d"] for l in locations)
    alert_locs = sum(1 for l in locations if l["status"] == "alert")

    body = f"""
<div class="mx-auto max-w-6xl px-4 py-10 sm:px-6 pb-20 fade-up">

  <div class="mb-8">
    <p class="text-xs uppercase tracking-[.2em] text-violet-300/70 mb-1">Paso 3 de 4</p>
    <h1 class="text-3xl font-bold text-white">Vista Consolidada de Ubicaciones</h1>
    <p class="mt-1 text-stone-400 text-sm">
      SuperAdmin · Todas las ubicaciones de todos los tenants en un solo panel.
    </p>
  </div>

  <!-- Progress bar -->
  <div class="flex gap-2 mb-10">
    <div class="h-1.5 flex-1 rounded-full bg-violet-500"></div>
    <div class="h-1.5 flex-1 rounded-full bg-violet-500"></div>
    <div class="h-1.5 flex-1 rounded-full bg-violet-500"></div>
    <div class="h-1.5 flex-1 rounded-full bg-white/10"></div>
  </div>

  <!-- KPI strip -->
  <div class="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-8">
    <div class="rounded-2xl border border-white/10 bg-white/5 p-4 text-center">
      <p class="text-3xl font-black text-white">{len(locations)}</p>
      <p class="text-xs uppercase tracking-wider text-stone-400 mt-1">Ubicaciones totales</p>
    </div>
    <div class="rounded-2xl border border-emerald-500/20 bg-emerald-500/5 p-4 text-center">
      <p class="text-3xl font-black text-emerald-300">{avg_rating}★</p>
      <p class="text-xs uppercase tracking-wider text-stone-400 mt-1">Rating promedio</p>
    </div>
    <div class="rounded-2xl border border-white/10 bg-white/5 p-4 text-center">
      <p class="text-3xl font-black text-white">{total_reviews}</p>
      <p class="text-xs uppercase tracking-wider text-stone-400 mt-1">Reseñas / 30 d</p>
    </div>
    <div class="rounded-2xl border border-rose-500/20 bg-rose-500/5 p-4 text-center">
      <p class="text-3xl font-black text-rose-300">{alert_locs}</p>
      <p class="text-xs uppercase tracking-wider text-stone-400 mt-1">Locs. en alerta</p>
    </div>
  </div>

  <!-- Filters -->
  <div class="rounded-3xl border border-white/10 bg-white/5 px-6 py-4 flex flex-wrap gap-3 items-center mb-5">
    <span class="text-xs text-stone-400 font-semibold uppercase tracking-wider">Filtros:</span>
    <select class="w-44">
      <option>Todos los tenants</option>
      <option>Cadena Pizzas Norte</option>
      <option>Franquicia Café Rápido</option>
      <option>Restaurantes El Mar</option>
      <option>Hoteles Solimar</option>
    </select>
    <select class="w-36">
      <option>Todas las ciudades</option>
      <option>Madrid</option>
      <option>Barcelona</option>
      <option>Marbella</option>
    </select>
    <select class="w-36">
      <option>Todos los estados</option>
      <option>✅ OK</option>
      <option>⚠️ Aviso</option>
      <option>🔴 Alerta</option>
    </select>
    <button class="px-4 py-2 rounded-xl bg-violet-600/30 border border-violet-500/20
                   text-violet-300 text-sm font-semibold hover:bg-violet-600/50">
      Aplicar
    </button>
  </div>

  <!-- Locations table -->
  <div class="rounded-3xl border border-white/10 bg-white/5 overflow-hidden mb-6">
    <div class="overflow-x-auto">
      <table class="min-w-full text-sm">
        <thead>
          <tr class="border-b border-white/10 text-stone-400 text-xs uppercase tracking-wider">
            <th class="py-3 pr-4 pl-6 text-left font-semibold">Tenant</th>
            <th class="py-3 pr-4 text-left font-semibold">Ubicación</th>
            <th class="py-3 pr-4 text-left font-semibold">Ciudad</th>
            <th class="py-3 pr-4 text-left font-semibold">Rating</th>
            <th class="py-3 pr-4 text-center font-semibold">Reseñas/30d</th>
            <th class="py-3 pr-4 text-center font-semibold">Reply %</th>
            <th class="py-3 pr-4 text-center font-semibold">Alertas</th>
            <th class="py-3 pr-6 text-left font-semibold">Estado</th>
          </tr>
        </thead>
        <tbody class="text-stone-200">
          {rows}
        </tbody>
      </table>
    </div>
  </div>

  <!-- Leyenda -->
  <div class="flex gap-5 flex-wrap text-xs text-stone-400">
    <span class="flex items-center gap-2"><span class="w-2.5 h-2.5 rounded-full bg-emerald-400 inline-block"></span> OK — todas las métricas en rango</span>
    <span class="flex items-center gap-2"><span class="w-2.5 h-2.5 rounded-full bg-amber-400 inline-block"></span> Aviso — rating o reply_% por debajo del objetivo</span>
    <span class="flex items-center gap-2"><span class="w-2.5 h-2.5 rounded-full bg-rose-400 inline-block animate-pulse"></span> Alerta — requiere atención inmediata</span>
  </div>

  <!-- Navigation -->
  <div class="flex justify-between items-center mt-10">
    <a href="step2_tenants.html"
       class="px-5 py-3 rounded-2xl border border-white/10 bg-white/5
              text-stone-300 font-semibold text-sm hover:bg-white/10 no-underline">
      ← Atrás
    </a>
    <a href="step4_roles.html"
       class="px-8 py-3 rounded-2xl bg-gradient-to-r from-violet-600 to-indigo-600
              text-white font-bold text-sm hover:from-violet-500 hover:to-indigo-500 no-underline">
      Siguiente: Roles y accesos →
    </a>
  </div>
</div>"""
    return page("Paso 3 — Vista Consolidada", "step3_locations.html", body)


# ─── STEP 4 — Gestión de Roles ────────────────────────────────────────────────

def step4_roles() -> str:
    users = [
        {"name": "Elena García",   "email": "elena@miagencia.com",       "role": "superadmin", "tenant": "— (todos)",           "since": "Ene 2026", "status": "active"},
        {"name": "Pedro Álvarez",  "email": "pedro@pizzasnorte.com",      "role": "manager",    "tenant": "Cadena Pizzas Norte", "since": "Feb 2026", "status": "active"},
        {"name": "Laura Méndez",   "email": "laura@caférapido.com",       "role": "manager",    "tenant": "Franquicia Café Rápido","since": "Mar 2026","status": "active"},
        {"name": "Javier Ruiz",    "email": "j.ruiz@restauranteselmar.es","role": "manager",    "tenant": "Restaurantes El Mar", "since": "Mar 2026", "status": "active"},
        {"name": "Sara Vidal",     "email": "sara@pizzasnorte.com",       "role": "viewer",     "tenant": "Cadena Pizzas Norte", "since": "Abr 2026", "status": "active"},
        {"name": "Marc Torres",    "email": "marc@pizzasnorte.com",       "role": "viewer",     "tenant": "Cadena Pizzas Norte", "since": "Abr 2026", "status": "active"},
        {"name": "Invitado Demo",  "email": "demo@hoteles.com",           "role": "viewer",     "tenant": "Hoteles Solimar",     "since": "Abr 2026", "status": "pending"},
    ]

    ROLE_BADGE = {
        "superadmin": '<span class="px-2.5 py-1 rounded-full badge-role-sa  text-xs font-bold">SuperAdmin</span>',
        "manager":    '<span class="px-2.5 py-1 rounded-full badge-role-mgr text-xs font-bold">Manager</span>',
        "viewer":     '<span class="px-2.5 py-1 rounded-full badge-role-view text-xs font-bold">Viewer</span>',
    }
    STATUS_BADGE = {
        "active":  '<span class="px-2.5 py-1 rounded-full bg-emerald-500/15 text-emerald-300 text-xs font-bold">Activo</span>',
        "pending": '<span class="px-2.5 py-1 rounded-full bg-amber-500/15  text-amber-300  text-xs font-bold">Pendiente</span>',
    }

    rows = ""
    for u in users:
        rows += f"""
        <tr class="border-b border-white/5 hover:bg-white/3">
          <td class="py-3 pr-4 pl-6">
            <div class="font-semibold text-stone-100 text-sm">{u["name"]}</div>
            <div class="text-xs text-stone-500">{u["email"]}</div>
          </td>
          <td class="py-3 pr-4">{ROLE_BADGE[u["role"]]}</td>
          <td class="py-3 pr-4 text-sm text-stone-400">{u["tenant"]}</td>
          <td class="py-3 pr-4 text-xs text-stone-500">{u["since"]}</td>
          <td class="py-3 pr-4">{STATUS_BADGE[u["status"]]}</td>
          <td class="py-3 pr-6">
            <button class="px-3 py-1.5 rounded-lg border border-white/10 bg-white/5
                           text-xs text-stone-400 hover:text-stone-200 hover:bg-white/10">
              Editar
            </button>
          </td>
        </tr>"""

    body = f"""
<div class="mx-auto max-w-5xl px-4 py-10 sm:px-6 pb-20 fade-up">

  <div class="mb-8">
    <p class="text-xs uppercase tracking-[.2em] text-violet-300/70 mb-1">Paso 4 de 4</p>
    <h1 class="text-3xl font-bold text-white">Gestión de Accesos y Roles</h1>
    <p class="mt-1 text-stone-400 text-sm">
      Define quién puede ver qué. Tres niveles jerárquicos con permisos aislados por tenant.
    </p>
  </div>

  <!-- Progress bar -->
  <div class="flex gap-2 mb-10">
    <div class="h-1.5 flex-1 rounded-full bg-violet-500"></div>
    <div class="h-1.5 flex-1 rounded-full bg-violet-500"></div>
    <div class="h-1.5 flex-1 rounded-full bg-violet-500"></div>
    <div class="h-1.5 flex-1 rounded-full bg-violet-500"></div>
  </div>

  <!-- Role cards -->
  <div class="grid grid-cols-1 sm:grid-cols-3 gap-5 mb-10">

    <div class="rounded-3xl border border-violet-500/25 bg-violet-500/8 p-6">
      <div class="w-10 h-10 rounded-2xl bg-violet-500/20 flex items-center justify-center text-xl mb-4">👑</div>
      <h3 class="text-white font-bold text-lg mb-1">SuperAdmin</h3>
      <p class="text-violet-300 text-xs font-bold uppercase tracking-wider mb-3">Agencia</p>
      <ul class="space-y-2 text-sm text-stone-300">
        <li class="flex gap-2"><span class="text-violet-400">✓</span> Vista de todos los tenants</li>
        <li class="flex gap-2"><span class="text-violet-400">✓</span> Crear / eliminar tenants</li>
        <li class="flex gap-2"><span class="text-violet-400">✓</span> Configurar white label</li>
        <li class="flex gap-2"><span class="text-violet-400">✓</span> Asignar roles a usuarios</li>
        <li class="flex gap-2"><span class="text-violet-400">✓</span> Ver datos consolidados</li>
        <li class="flex gap-2"><span class="text-violet-400">✓</span> Facturación de agencia</li>
      </ul>
    </div>

    <div class="rounded-3xl border border-amber-500/20 bg-amber-500/5 p-6">
      <div class="w-10 h-10 rounded-2xl bg-amber-500/15 flex items-center justify-center text-xl mb-4">🏢</div>
      <h3 class="text-white font-bold text-lg mb-1">Manager</h3>
      <p class="text-amber-300 text-xs font-bold uppercase tracking-wider mb-3">Dueño de franquicia</p>
      <ul class="space-y-2 text-sm text-stone-300">
        <li class="flex gap-2"><span class="text-amber-400">✓</span> Vista de su tenant</li>
        <li class="flex gap-2"><span class="text-amber-400">✓</span> Todas sus ubicaciones</li>
        <li class="flex gap-2"><span class="text-amber-400">✓</span> Aprobar respuestas IA</li>
        <li class="flex gap-2"><span class="text-amber-400">✓</span> Configurar voz de marca</li>
        <li class="flex gap-2"><span class="text-amber-400">✓</span> Descargar reportes PDF</li>
        <li class="flex gap-2 opacity-40"><span>✗</span> Otros tenants</li>
      </ul>
    </div>

    <div class="rounded-3xl border border-white/10 bg-white/5 p-6">
      <div class="w-10 h-10 rounded-2xl bg-stone-500/20 flex items-center justify-center text-xl mb-4">👁️</div>
      <h3 class="text-white font-bold text-lg mb-1">Viewer</h3>
      <p class="text-stone-400 text-xs font-bold uppercase tracking-wider mb-3">Encargado de local</p>
      <ul class="space-y-2 text-sm text-stone-300">
        <li class="flex gap-2"><span class="text-stone-400">✓</span> Solo su ubicación asignada</li>
        <li class="flex gap-2"><span class="text-stone-400">✓</span> Ver reseñas y respuestas</li>
        <li class="flex gap-2"><span class="text-stone-400">✓</span> Ver alertas de su local</li>
        <li class="flex gap-2 opacity-40"><span>✗</span> Aprobar ni editar respuestas</li>
        <li class="flex gap-2 opacity-40"><span>✗</span> Configurar nada</li>
        <li class="flex gap-2 opacity-40"><span>✗</span> Ver otros locales</li>
      </ul>
    </div>

  </div>

  <!-- Users table -->
  <div class="rounded-3xl border border-white/10 bg-white/5 overflow-hidden mb-8">
    <div class="flex items-center justify-between px-6 py-4 border-b border-white/10">
      <h2 class="text-base font-semibold text-white m-0">Usuarios activos</h2>
      <button class="px-4 py-2 rounded-xl bg-violet-600 text-white text-sm font-bold hover:bg-violet-500">
        + Invitar usuario
      </button>
    </div>
    <div class="overflow-x-auto">
      <table class="min-w-full text-sm">
        <thead>
          <tr class="border-b border-white/10 text-stone-400 text-xs uppercase tracking-wider">
            <th class="py-3 pr-4 pl-6 text-left font-semibold">Usuario</th>
            <th class="py-3 pr-4 text-left font-semibold">Rol</th>
            <th class="py-3 pr-4 text-left font-semibold">Tenant</th>
            <th class="py-3 pr-4 text-left font-semibold">Desde</th>
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

  <!-- Invite form -->
  <div class="rounded-3xl border border-white/10 bg-white/5 p-6 mb-8">
    <h2 class="text-base font-semibold text-white mb-5">Invitar nuevo usuario</h2>
    <div class="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-4">
      <div>
        <label class="block text-xs text-stone-400 font-semibold uppercase tracking-wider mb-2">Email</label>
        <input type="email" placeholder="usuario@ejemplo.com" />
      </div>
      <div>
        <label class="block text-xs text-stone-400 font-semibold uppercase tracking-wider mb-2">Rol</label>
        <select>
          <option>SuperAdmin</option>
          <option selected>Manager</option>
          <option>Viewer</option>
        </select>
      </div>
      <div>
        <label class="block text-xs text-stone-400 font-semibold uppercase tracking-wider mb-2">Tenant asignado</label>
        <select>
          <option>— Todos (solo SuperAdmin)</option>
          <option>Cadena Pizzas Norte</option>
          <option>Franquicia Café Rápido</option>
          <option>Restaurantes El Mar</option>
          <option>Hoteles Solimar</option>
        </select>
      </div>
      <div>
        <label class="block text-xs text-stone-400 font-semibold uppercase tracking-wider mb-2">Mensaje de bienvenida (opcional)</label>
        <input type="text" placeholder="Bienvenido a nuestra plataforma..." />
      </div>
    </div>
    <button class="px-6 py-3 rounded-xl bg-gradient-to-r from-violet-600 to-indigo-600
                   text-white font-bold text-sm hover:from-violet-500 hover:to-indigo-500">
      Enviar invitación
    </button>
  </div>

  <!-- Navigation -->
  <div class="flex justify-between items-center mt-8">
    <a href="step3_locations.html"
       class="px-5 py-3 rounded-2xl border border-white/10 bg-white/5
              text-stone-300 font-semibold text-sm hover:bg-white/10 no-underline">
      ← Atrás
    </a>
    <a href="step5_dashboard_agency.html"
       class="px-8 py-3 rounded-2xl bg-gradient-to-r from-violet-600 to-indigo-600
              text-white font-bold text-sm hover:from-violet-500 hover:to-indigo-500 no-underline">
      Ver Dashboard Agency →
    </a>
  </div>
</div>"""
    return page("Paso 4 — Gestión de Roles", "step4_roles.html", body)


# ─── STEP 5 — Dashboard Agency (SuperAdmin) ──────────────────────────────────

def step5_dashboard_agency() -> str:
    body = """
<div class="mx-auto max-w-6xl px-4 py-8 sm:px-6 pb-20 fade-up">

  <!-- Header -->
  <div class="rounded-3xl border border-violet-500/20
              bg-gradient-to-br from-stone-900 via-violet-950/40 to-indigo-950/40
              p-6 mb-6 shadow-2xl">
    <div class="flex flex-col gap-6 lg:flex-row lg:items-center lg:justify-between">
      <div>
        <p class="text-xs uppercase tracking-[.28em] text-violet-300/70 mb-1">SuperAdmin · Agencia</p>
        <h1 class="text-4xl font-black text-white leading-none mb-2">Mi Agencia Digital</h1>
        <p class="text-stone-400 text-sm">Vista consolidada · 4 tenants · 8 ubicaciones monitorizadas</p>
      </div>
      <div class="flex flex-wrap gap-3">
        <div class="min-w-[88px] rounded-2xl border border-violet-500/20 bg-violet-500/10 px-5 py-3 text-center">
          <p class="text-3xl font-bold text-violet-200">4</p>
          <p class="text-xs uppercase tracking-wider text-stone-400 mt-0.5">Tenants</p>
        </div>
        <div class="min-w-[88px] rounded-2xl border border-white/10 bg-white/5 px-5 py-3 text-center">
          <p class="text-3xl font-bold text-white">31</p>
          <p class="text-xs uppercase tracking-wider text-stone-400 mt-0.5">Ubicaciones</p>
        </div>
        <div class="min-w-[88px] rounded-2xl border border-emerald-500/20 bg-emerald-500/10 px-5 py-3 text-center">
          <p class="text-3xl font-bold text-emerald-200">4.2★</p>
          <p class="text-xs uppercase tracking-wider text-stone-400 mt-0.5">Rating avg</p>
        </div>
        <div class="min-w-[88px] rounded-2xl border border-rose-500/20 bg-rose-500/10 px-5 py-3 text-center">
          <p class="text-3xl font-bold text-rose-200">6</p>
          <p class="text-xs uppercase tracking-wider text-stone-400 mt-0.5">Alertas</p>
        </div>
      </div>
    </div>
  </div>

  <!-- Main grid -->
  <div class="grid grid-cols-1 xl:grid-cols-[3fr_2fr] gap-5 mb-5">

    <!-- LEFT: Tenant performance -->
    <div class="space-y-5">

      <div class="rounded-3xl border border-white/10 bg-white/5 p-5">
        <p class="text-xs uppercase tracking-[.2em] text-stone-400">Rendimiento por Tenant</p>
        <h2 class="text-xl font-bold text-white mt-1 mb-5">Todos los clientes — resumen</h2>

        <div class="space-y-4">

          <!-- Tenant card 1 -->
          <div class="rounded-2xl border border-white/10 bg-black/20 p-4">
            <div class="flex items-start justify-between gap-2 mb-3">
              <div>
                <h3 class="text-sm font-bold text-white">Cadena Pizzas Norte</h3>
                <p class="text-xs text-stone-400">8 ubicaciones · Madrid</p>
              </div>
              <span class="px-2.5 py-1 rounded-full bg-emerald-500/15 text-emerald-300 text-xs font-bold">Activo</span>
            </div>
            <div class="grid grid-cols-3 gap-3">
              <div class="text-center"><p class="text-xl font-bold text-white">4.3★</p><p class="text-xs text-stone-400">Rating</p></div>
              <div class="text-center"><p class="text-xl font-bold text-emerald-300">91%</p><p class="text-xs text-stone-400">Reply %</p></div>
              <div class="text-center"><p class="text-xl font-bold text-rose-300">2</p><p class="text-xs text-stone-400">Alertas</p></div>
            </div>
            <div class="mt-3 bg-black/20 rounded-xl h-2 overflow-hidden">
              <div class="h-full rounded-xl" style="width:86%;background:linear-gradient(90deg,#7c3aed,#4f46e5)"></div>
            </div>
            <p class="text-xs text-stone-500 mt-1">Score de salud: 86/100</p>
          </div>

          <!-- Tenant card 2 -->
          <div class="rounded-2xl border border-white/10 bg-black/20 p-4">
            <div class="flex items-start justify-between gap-2 mb-3">
              <div>
                <h3 class="text-sm font-bold text-white">Franquicia Café Rápido</h3>
                <p class="text-xs text-stone-400">14 ubicaciones · Madrid + provincias</p>
              </div>
              <span class="px-2.5 py-1 rounded-full bg-emerald-500/15 text-emerald-300 text-xs font-bold">Activo</span>
            </div>
            <div class="grid grid-cols-3 gap-3">
              <div class="text-center"><p class="text-xl font-bold text-white">4.0★</p><p class="text-xs text-stone-400">Rating</p></div>
              <div class="text-center"><p class="text-xl font-bold text-emerald-300">82%</p><p class="text-xs text-stone-400">Reply %</p></div>
              <div class="text-center"><p class="text-xl font-bold text-stone-400">0</p><p class="text-xs text-stone-400">Alertas</p></div>
            </div>
            <div class="mt-3 bg-black/20 rounded-xl h-2 overflow-hidden">
              <div class="h-full rounded-xl" style="width:79%;background:linear-gradient(90deg,#7c3aed,#4f46e5)"></div>
            </div>
            <p class="text-xs text-stone-500 mt-1">Score de salud: 79/100</p>
          </div>

          <!-- Tenant card 3 -->
          <div class="rounded-2xl border border-white/10 bg-black/20 p-4">
            <div class="flex items-start justify-between gap-2 mb-3">
              <div>
                <h3 class="text-sm font-bold text-white">Restaurantes El Mar</h3>
                <p class="text-xs text-stone-400">5 ubicaciones · Barcelona + costa</p>
              </div>
              <span class="px-2.5 py-1 rounded-full bg-emerald-500/15 text-emerald-300 text-xs font-bold">Activo</span>
            </div>
            <div class="grid grid-cols-3 gap-3">
              <div class="text-center"><p class="text-xl font-bold text-white">4.6★</p><p class="text-xs text-stone-400">Rating</p></div>
              <div class="text-center"><p class="text-xl font-bold text-emerald-300">97%</p><p class="text-xs text-stone-400">Reply %</p></div>
              <div class="text-center"><p class="text-xl font-bold text-rose-300">1</p><p class="text-xs text-stone-400">Alertas</p></div>
            </div>
            <div class="mt-3 bg-black/20 rounded-xl h-2 overflow-hidden">
              <div class="h-full rounded-xl" style="width:93%;background:linear-gradient(90deg,#10b981,#059669)"></div>
            </div>
            <p class="text-xs text-stone-500 mt-1">Score de salud: 93/100</p>
          </div>

          <!-- Tenant card 4 -->
          <div class="rounded-2xl border border-rose-500/15 bg-rose-500/5 p-4">
            <div class="flex items-start justify-between gap-2 mb-3">
              <div>
                <h3 class="text-sm font-bold text-white">Hoteles Solimar</h3>
                <p class="text-xs text-stone-400">3 ubicaciones · Marbella</p>
              </div>
              <span class="px-2.5 py-1 rounded-full bg-amber-500/15 text-amber-300 text-xs font-bold">Trial</span>
            </div>
            <div class="grid grid-cols-3 gap-3">
              <div class="text-center"><p class="text-xl font-bold text-amber-300">4.0★</p><p class="text-xs text-stone-400">Rating</p></div>
              <div class="text-center"><p class="text-xl font-bold text-rose-300">44%</p><p class="text-xs text-stone-400">Reply %</p></div>
              <div class="text-center"><p class="text-xl font-bold text-rose-300">4</p><p class="text-xs text-stone-400">Alertas</p></div>
            </div>
            <div class="mt-3 bg-black/20 rounded-xl h-2 overflow-hidden">
              <div class="h-full rounded-xl" style="width:42%;background:linear-gradient(90deg,#f43f5e,#e11d48)"></div>
            </div>
            <p class="text-xs text-rose-400 mt-1">Score de salud: 42/100 · Requiere atención</p>
          </div>

        </div>
      </div>

    </div>
    <!-- END LEFT -->

    <!-- RIGHT: Alerts + Quick actions -->
    <div class="space-y-5">

      <!-- Alert panel -->
      <div class="rounded-3xl border border-white/10 bg-white/5 p-5">
        <p class="text-xs uppercase tracking-[.2em] text-stone-400">Centro de Alertas</p>
        <h2 class="text-xl font-bold text-white mt-1 mb-4">6 alertas abiertas</h2>
        <div class="space-y-3 max-h-72 overflow-y-auto pr-1">
          <div class="rounded-2xl border border-rose-500/20 bg-rose-500/8 p-3">
            <div class="flex justify-between items-start gap-2 mb-1">
              <p class="text-sm font-semibold text-white">Reply % crítico — Hotel Solimar</p>
              <span class="px-2 py-0.5 rounded-full bg-rose-500/20 text-rose-300 text-xs font-bold flex-shrink-0">Alta</span>
            </div>
            <p class="text-xs text-stone-400">Solo el 44 % de reseñas con respuesta. Objetivo: 80 %.</p>
            <p class="text-xs text-stone-600 mt-1">hace 2 horas</p>
          </div>
          <div class="rounded-2xl border border-rose-500/20 bg-rose-500/8 p-3">
            <div class="flex justify-between items-start gap-2 mb-1">
              <p class="text-sm font-semibold text-white">3 reseñas negativas sin contestar — Hoteles Solimar</p>
              <span class="px-2 py-0.5 rounded-full bg-rose-500/20 text-rose-300 text-xs font-bold flex-shrink-0">Alta</span>
            </div>
            <p class="text-xs text-stone-400">Reseñas de 1 y 2 estrellas sin respuesta IA aprobada.</p>
            <p class="text-xs text-stone-600 mt-1">hace 5 horas</p>
          </div>
          <div class="rounded-2xl border border-amber-500/15 bg-amber-500/5 p-3">
            <div class="flex justify-between items-start gap-2 mb-1">
              <p class="text-sm font-semibold text-white">Caída de rating — Pizza Norte Chamberí</p>
              <span class="px-2 py-0.5 rounded-full bg-amber-500/20 text-amber-300 text-xs font-bold flex-shrink-0">Media</span>
            </div>
            <p class="text-xs text-stone-400">Rating pasó de 4.4 a 4.2 en los últimos 14 días.</p>
            <p class="text-xs text-stone-600 mt-1">hace 12 horas</p>
          </div>
          <div class="rounded-2xl border border-amber-500/15 bg-amber-500/5 p-3">
            <div class="flex justify-between items-start gap-2 mb-1">
              <p class="text-sm font-semibold text-white">Reply % bajo — Café Rápido Atocha</p>
              <span class="px-2 py-0.5 rounded-full bg-amber-500/20 text-amber-300 text-xs font-bold flex-shrink-0">Media</span>
            </div>
            <p class="text-xs text-stone-400">62 % de respuesta. Esperada una mejora antes del cierre mensual.</p>
            <p class="text-xs text-stone-600 mt-1">hace 1 día</p>
          </div>
        </div>
      </div>

      <!-- Quick actions -->
      <div class="rounded-3xl border border-white/10 bg-white/5 p-5">
        <p class="text-xs uppercase tracking-[.2em] text-stone-400 mb-4">Acciones rápidas</p>
        <div class="space-y-2">
          <a href="step2_tenants.html"
             class="flex items-center gap-3 p-3 rounded-2xl border border-white/10
                    bg-white/3 hover:bg-white/8 no-underline group">
            <span class="text-xl">🏗️</span>
            <div>
              <p class="text-sm font-semibold text-white group-hover:text-violet-300 transition">Gestionar tenants</p>
              <p class="text-xs text-stone-500">Ver, crear o pausar clientes</p>
            </div>
          </a>
          <a href="step4_roles.html"
             class="flex items-center gap-3 p-3 rounded-2xl border border-white/10
                    bg-white/3 hover:bg-white/8 no-underline group">
            <span class="text-xl">🔐</span>
            <div>
              <p class="text-sm font-semibold text-white group-hover:text-violet-300 transition">Roles y permisos</p>
              <p class="text-xs text-stone-500">Invitar usuarios o cambiar roles</p>
            </div>
          </a>
          <a href="step1_brand.html"
             class="flex items-center gap-3 p-3 rounded-2xl border border-white/10
                    bg-white/3 hover:bg-white/8 no-underline group">
            <span class="text-xl">🎨</span>
            <div>
              <p class="text-sm font-semibold text-white group-hover:text-violet-300 transition">Ajustar white label</p>
              <p class="text-xs text-stone-500">Logo, colores, dominio</p>
            </div>
          </a>
          <a href="step3_locations.html"
             class="flex items-center gap-3 p-3 rounded-2xl border border-white/10
                    bg-white/3 hover:bg-white/8 no-underline group">
            <span class="text-xl">📍</span>
            <div>
              <p class="text-sm font-semibold text-white group-hover:text-violet-300 transition">Vista de ubicaciones</p>
              <p class="text-xs text-stone-500">Mapa consolidado multi-tenant</p>
            </div>
          </a>
        </div>
      </div>

      <!-- Billing summary -->
      <div class="rounded-3xl border border-violet-500/20 bg-violet-500/5 p-5">
        <p class="text-xs uppercase tracking-[.2em] text-violet-300/70 mb-4">Facturación agencia</p>
        <div class="divide-y divide-white/5 text-sm">
          <div class="flex justify-between py-2.5">
            <span class="text-stone-400">Plan Enterprise base</span>
            <span class="text-white font-bold">$199/mes</span>
          </div>
          <div class="flex justify-between py-2.5">
            <span class="text-stone-400">Tenants adicionales (3 × $29)</span>
            <span class="text-white font-bold">$87/mes</span>
          </div>
          <div class="flex justify-between py-2.5 text-base">
            <span class="text-stone-200 font-bold">Total mensual</span>
            <span class="text-violet-300 font-black">$286/mes</span>
          </div>
        </div>
        <p class="text-xs text-stone-500 mt-3">Próxima factura: 1 Mayo 2026</p>
      </div>

    </div>
    <!-- END RIGHT -->

  </div>

  <!-- Back link -->
  <div class="flex justify-start mt-2">
    <a href="step4_roles.html"
       class="px-5 py-3 rounded-2xl border border-white/10 bg-white/5
              text-stone-300 font-semibold text-sm hover:bg-white/10 no-underline">
      ← Volver a Roles
    </a>
  </div>

</div>"""
    return page("Dashboard Agency — SuperAdmin", "step5_dashboard_agency.html", body)


# ─── RENDER ──────────────────────────────────────────────────────────────────

def main() -> None:
    files = [
        ("enterprise_landing.html",     enterprise_landing()),
        ("step1_brand.html",            step1_brand()),
        ("step2_tenants.html",          step2_tenants()),
        ("step3_locations.html",        step3_locations()),
        ("step4_roles.html",            step4_roles()),
        ("step5_dashboard_agency.html", step5_dashboard_agency()),
    ]

    for fname, html in files:
        path = OUT_DIR / fname
        path.write_text(html, encoding="utf-8")
        print(f"✓ {path}")

    print("\n📌 Abriendo en el navegador:")
    for fname, _ in files:
        url = f"http://localhost:3000/enterprise/{fname}"
        webbrowser.open(url)
        print(f"   {url}")


if __name__ == "__main__":
    main()
