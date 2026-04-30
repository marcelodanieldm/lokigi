"""
Renderiza el flujo de onboarding Growth (5 pasos) con datos mock
y los guarda como HTML estáticos en frontend/static/onboarding/.
Luego abre el paso 1 en el navegador.
"""
from __future__ import annotations

import webbrowser
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

ROOT = Path(__file__).parent
TEMPLATES_DIR = ROOT / "backend" / "app" / "templates"
OUT_DIR = ROOT / "frontend" / "static" / "onboarding"
OUT_DIR.mkdir(parents=True, exist_ok=True)

DEMO_USER_ID = "00000000-0000-0000-0000-000000000001"
DEMO_PLACE_ID = "ChIJdemo123456789"
DEMO_BUSINESS = "La Terraza Demo"
DEMO_KEYWORDS = ["Pizza artesanal", "Delivery nocturno", "Brunch premium"]
DEMO_KEYWORDS_CSV = ", ".join(DEMO_KEYWORDS)

env = Environment(
    loader=FileSystemLoader(str(TEMPLATES_DIR)),
    autoescape=False,
)

# ── helpers ──────────────────────────────────────────────────────────────────

def nav_bar(steps, current):
    """Renders a simple top nav with links between the static preview pages."""
    items = []
    for i, (label, href) in enumerate(steps, 1):
        active = i == current
        style = (
            "background:#10b981;color:#fff;font-weight:700;"
            if active
            else "background:rgba(255,255,255,0.07);color:rgba(255,255,255,0.55);"
        )
        items.append(
            f'<a href="{href}" style="padding:8px 18px;border-radius:999px;'
            f'text-decoration:none;font-size:13px;{style}">Paso {i}: {label}</a>'
        )
    return (
        '<div style="position:fixed;top:0;left:0;right:0;z-index:999;'
        'background:rgba(8,17,31,0.92);backdrop-filter:blur(12px);'
        'border-bottom:1px solid rgba(255,255,255,0.08);'
        'padding:10px 20px;display:flex;gap:8px;flex-wrap:wrap;align-items:center;">'
        '<span style="color:#34d399;font-weight:800;margin-right:8px;font-size:14px;">Onboarding Growth</span>'
        + "".join(items)
        + "</div>"
        '<div style="height:54px;"></div>'
    )


def inject_nav(html: str, nav: str) -> str:
    """Inject nav bar right after <body> tag."""
    tag = "<body"
    idx = html.find(tag)
    if idx == -1:
        return nav + html
    end = html.find(">", idx) + 1
    return html[:end] + "\n" + nav + html[end:]


# ── step definitions ──────────────────────────────────────────────────────────

STEPS = [
    ("Buscar negocio",  "step1_search.html"),
    ("Keywords Radar",  "step2_keywords.html"),
    ("Rivales",         "step3_competitors.html"),
    ("Voz de Marca",    "step4_brand_voice.html"),
    ("Sincronización",  "step5_sync.html"),
]
STEP_LINKS = [(label, href) for label, href in STEPS]


# ── Step 1: Business Search ───────────────────────────────────────────────────

def render_step1():
    tmpl = env.get_template("onboarding_search.html")
    # Patch: replace HTMX search with static demo results
    html = tmpl.render(maps_configured=False)

    # Replace the search card content with a static demo result showing a
    # "confirmed" business so the user can click Next
    demo_card = """
    <div style="margin-top:12px;">
      <div style="border:1px solid rgba(16,185,129,0.4);border-radius:16px;padding:16px;background:rgba(16,185,129,0.07);">
        <div style="display:flex;align-items:center;gap:12px;">
          <div style="width:44px;height:44px;border-radius:12px;background:#059669;display:flex;align-items:center;justify-content:center;font-weight:900;font-size:18px;">L</div>
          <div>
            <div style="font-weight:700;font-size:15px;">La Terraza Demo</div>
            <div style="color:rgba(255,255,255,0.5);font-size:12px;">Calle Gran Vía 42, Madrid · 4.5★ · 240 reseñas</div>
          </div>
          <div style="margin-left:auto;">
            <a href="step2_keywords.html"
               style="background:#10b981;color:#0a0f1e;padding:10px 20px;border-radius:12px;font-weight:700;font-size:13px;text-decoration:none;display:inline-block;">
              Confirmar →
            </a>
          </div>
        </div>
      </div>
      <p style="color:rgba(255,255,255,0.25);font-size:11px;margin-top:8px;text-align:center;">
        (Demo: en producción esto busca en Google Maps en tiempo real)
      </p>
    </div>
    """
    # Insert demo card before closing </div> of the card
    html = html.replace('<div id="place-preview"></div>', demo_card)
    return html


# ── Step 2: Keywords ──────────────────────────────────────────────────────────

def render_step2():
    tmpl = env.get_template("onboarding_keywords.html")
    suggested = [
        "Pizzería artesanal", "Delivery rápido", "Brunch fin de semana",
        "Cafetería con wifi", "Desayunos saludables", "Menú ejecutivo",
        "Restaurante romántico", "Terraza con vistas",
    ]
    html = tmpl.render(
        user_id=DEMO_USER_ID,
        place_id=DEMO_PLACE_ID,
        business_name=DEMO_BUSINESS,
        existing_keywords=DEMO_KEYWORDS,
        suggested_keywords=suggested,
    )
    # Make "Continuar" button a plain link in the static preview
    html = html.replace(
        'id="continue-btn" type="submit" disabled',
        'id="continue-btn" type="button"'
    ).replace(
        'class="w-full rounded-2xl bg-white/5 py-3.5 font-bold text-sm text-white/20 cursor-not-allowed transition-all">Continuar a Voz de Marca',
        'class="w-full rounded-2xl bg-sky-500 py-3.5 font-bold text-sm text-white transition-all" onclick="window.location=\'step3_competitors.html\'">Continuar a Rivales →',
    )
    return html


# ── Step 3: Competitors ───────────────────────────────────────────────────────

def render_step3():
    tmpl = env.get_template("onboarding_competitors.html")

    class Competitor:
        def __init__(self, rank, name, address, rating, total_reviews, place_id, search_hits):
            self.rank = rank
            self.name = name
            self.address = address
            self.rating = rating
            self.total_reviews = total_reviews
            self.place_id = place_id
            self.search_hits = search_hits

    competitors = [
        Competitor(1, "El Rincón Gourmet",     "Calle Serrano 12, Madrid",       4.6, 890, "ChIJrival001", 3),
        Competitor(2, "Bistró Central",         "Paseo del Prado 8, Madrid",      4.4, 540, "ChIJrival002", 3),
        Competitor(3, "Sabores del Norte",      "Av. Castellana 200, Madrid",     4.1, 310, "ChIJrival003", 2),
        Competitor(4, "La Cantina Moderna",     "Gran Vía 55, Madrid",            4.3, 420, "ChIJrival004", 2),
        Competitor(5, "Tapas & Compañía",       "Calle Fuencarral 18, Madrid",    4.2, 275, "ChIJrival005", 2),
        Competitor(6, "Urban Kitchen MTD",      "Calle Alcalá 90, Madrid",        3.9, 190, "ChIJrival006", 1),
        Competitor(7, "Pizza Veloce",           "Av. América 34, Madrid",         4.0, 355, "ChIJrival007", 2),
        Competitor(8, "Café del Sol",           "Plaza Mayor 3, Madrid",          4.5, 680, "ChIJrival008", 1),
        Competitor(9, "El Mesón de la Abuela",  "Calle Toledo 21, Madrid",        4.1, 230, "ChIJrival009", 1),
        Competitor(10,"Fusion 360",             "Calle Hortaleza 5, Madrid",      3.8, 145, "ChIJrival010", 1),
    ]
    preselected = {"ChIJrival001", "ChIJrival002", "ChIJrival003", "ChIJrival004", "ChIJrival005"}

    html = tmpl.render(
        user_id=DEMO_USER_ID,
        place_id=DEMO_PLACE_ID,
        business_name=DEMO_BUSINESS,
        keywords_csv=DEMO_KEYWORDS_CSV,
        focus_keywords=DEMO_KEYWORDS,
        competitors=competitors,
        map_url=None,
        preselected_ids=preselected,
    )
    # Enable continue button as a link
    html = html.replace(
        'id="continue-btn" type="submit" disabled',
        'id="continue-btn" type="button"'
    ).replace(
        'class="w-full rounded-2xl bg-white/5 py-3.5 font-bold text-sm text-white/20 cursor-not-allowed transition-all">Continuar a Voz de Marca',
        'class="w-full rounded-2xl bg-sky-500 py-3.5 font-bold text-sm text-white transition-all" onclick="window.location=\'step4_brand_voice.html\'">Continuar a Voz de Marca →',
    )
    return html


# ── Step 4: Brand Voice ───────────────────────────────────────────────────────

def render_step4():
    tmpl = env.get_template("onboarding_brand_voice.html")

    tone_options = [
        {
            "key": "cercano",
            "label": "Cercano y Cálido",
            "description": "Tono amigable, personal y empático. Ideal para negocios de barrio.",
            "icon": "🤝",
            "color": "emerald",
            "reply": "¡Muchas gracias por tu visita, María! Nos alegra muchísimo que hayas disfrutado la experiencia. Te esperamos pronto con muchas novedades 🌟",
        },
        {
            "key": "formal",
            "label": "Profesional y Formal",
            "description": "Correcto, elegante y corporativo. Perfecto para restaurantes premium.",
            "icon": "🎩",
            "color": "blue",
            "reply": "Estimada María, le agradecemos sinceramente su valoración. Es un placer para nuestro equipo brindarle la mejor experiencia. Quedamos a su disposición.",
        },
        {
            "key": "moderno",
            "label": "Moderno y Directo",
            "description": "Conciso, fresco y con personalidad. Conecta con audiencias jóvenes.",
            "icon": "⚡",
            "color": "violet",
            "reply": "¡Gracias María! 🙌 Tu opinión nos impulsa a seguir mejorando. ¡Vuelve cuando quieras!",
        },
    ]

    html = tmpl.render(
        user_id=DEMO_USER_ID,
        place_id=DEMO_PLACE_ID,
        business_name=DEMO_BUSINESS,
        keywords_csv=DEMO_KEYWORDS_CSV,
        focus_keywords=DEMO_KEYWORDS,
        competitor_count=5,
        review_author="María García",
        review_stars=5,
        review_text="Increíble experiencia, la pizza artesanal es la mejor que he probado en Madrid. El servicio fue atento y el ambiente muy acogedor.",
        tone_options=tone_options,
    )
    # Patch activate button to link to sync page
    html = html.replace(
        'hx-post="/onboarding/activate"',
        'onclick="window.location=\'step5_sync.html\'"'
    ).replace(
        'id="activate-btn"\n        disabled\n        class="w-full py-3.5 rounded-xl font-bold text-sm transition-all\n               bg-white/5 text-white/20 cursor-not-allowed"',
        'id="activate-btn" class="w-full py-3.5 rounded-xl font-bold text-sm transition-all bg-emerald-500 text-slate-950 cursor-pointer"'
    )
    # Also handle the disabled state from the template via JS
    html = html.replace(
        "hx-target=\"body\"\n        hx-swap=\"outerHTML\"",
        ""
    )
    return html


# ── Step 5: Sync ──────────────────────────────────────────────────────────────

def render_step5():
    tmpl = env.get_template("onboarding_sync.html")

    class Sync:
        progress_pct = 68
        message = "Extrayendo perfiles de competidores y sembrando el Radar Competitivo inicial…"
        active_count = 5
        snapshot_count = 3
        benchmark_count = 2

    html = tmpl.render(
        user_id=DEMO_USER_ID,
        business_name=DEMO_BUSINESS,
        sync=Sync(),
        task_id="celery-task-demo-abc123",
    )
    # Remove the auto-reload script in preview mode and fix dashboard link
    html = html.replace(
        "setTimeout(() => window.location.reload(), 4500);",
        "// auto-reload disabled in preview"
    ).replace(
        f'/growth/dashboard?user_id={DEMO_USER_ID}',
        "../growth_dashboard_preview.html"
    )
    return html


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    renderers = [render_step1, render_step2, render_step3, render_step4, render_step5]
    filenames = [fname for _, fname in STEPS]

    for i, (renderer, filename) in enumerate(zip(renderers, filenames), 1):
        try:
            html = renderer()
        except Exception as exc:
            print(f"[ERROR] Paso {i} ({filename}): {exc}")
            raise

        nav = nav_bar(STEP_LINKS, i)
        html = inject_nav(html, nav)

        out_path = OUT_DIR / filename
        out_path.write_text(html, encoding="utf-8")
        print(f"✓ Paso {i}: {out_path}")

    # Open step 1 in browser
    webbrowser.open("http://localhost:3000/onboarding/step1_search.html")
    print("\n📌 Abriendo en el navegador:")
    for i, (label, fname) in enumerate(STEPS, 1):
        print(f"   Paso {i} ({label}) → http://localhost:3000/onboarding/{fname}")


if __name__ == "__main__":
    main()
