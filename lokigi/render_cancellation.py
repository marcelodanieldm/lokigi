"""
Renderiza el flujo de cancelación / cambio de plan de Lokigi Starter
como páginas HTML estáticas navegables y las sirve en localhost:3000.

Pasos:
  1. Página de suscripción (con botón "Gestionar Suscripción")
  2. Modal de elección: Pausar vs Cancelar
  3. Encuesta de salida (3 motivos)
  4. Encuesta confirmada (motivo seleccionado → CSV habilitado)
  5. Plan Pausa activado (éxito de pausa)
  6. Despedida / Goodbye
"""
from __future__ import annotations
import webbrowser
from pathlib import Path
from html import escape as esc

ROOT = Path(__file__).parent
OUT_DIR = ROOT / "frontend" / "static" / "cancellation"
OUT_DIR.mkdir(parents=True, exist_ok=True)

DEMO_USER_ID = "00000000-0000-0000-0000-000000000001"
DEMO_BUSINESS = "La Terraza Demo"

# ── CSS compartido ────────────────────────────────────────────────────────────

BASE_CSS = """
:root { --bg:#f2f6fb; --card:#fff; --text:#0f172a; --muted:#64748b; --border:#dbe3ee; --primary:#0f62fe; }
* { box-sizing:border-box; }
body { margin:0; font-family:Arial, 'Helvetica Neue', sans-serif; color:var(--text); background:linear-gradient(180deg,#ffffff,#f2f6fb); }
.wrap { max-width:1100px; margin:0 auto; padding:20px; }
.hero { background:linear-gradient(135deg,#082f49,#0f62fe); color:#fff; border-radius:20px; padding:24px; }
.hero-top { display:flex; justify-content:space-between; gap:12px; align-items:flex-start; flex-wrap:wrap; }
.status-badge { display:inline-flex; padding:7px 12px; border-radius:999px; font-weight:700; font-size:12px; background:#0f766e; color:#fff; }
.hero p { margin:8px 0 0; color:#dbeafe; max-width:620px; }
.grid { display:grid; grid-template-columns:0.8fr 1.2fr; gap:16px; margin-top:16px; }
.card { background:var(--card); border:1px solid var(--border); border-radius:18px; padding:18px; }
.metric { font-size:32px; font-weight:800; margin:4px 0; }
.muted { color:var(--muted); }
.btn { display:inline-flex; align-items:center; justify-content:center; text-decoration:none; padding:10px 14px; border-radius:10px; border:1px solid var(--border); background:#fff; color:var(--text); font-weight:700; cursor:pointer; }
.btn.primary { background:var(--primary); border-color:var(--primary); color:#fff; }
.btn.small { padding:8px 10px; font-size:13px; }
.cta-row, .subscription-actions { display:flex; gap:10px; flex-wrap:wrap; margin-top:14px; }
table { width:100%; border-collapse:collapse; }
th, td { text-align:left; padding:12px 10px; border-bottom:1px solid var(--border); font-size:14px; }
th { color:#475569; font-size:12px; text-transform:uppercase; letter-spacing:.04em; }
.empty-row { color:var(--muted); text-align:center; padding:18px 10px; }
.notice { margin-top:16px; border-radius:12px; padding:12px 14px; border:1px solid #cbd5e1; background:#fff; }
.notice.ok { background:#ecfdf5; border-color:#86efac; color:#166534; }
/* cancel flow */
.cancel-flow-backdrop { position:fixed; inset:0; background:rgba(15,23,42,.55); display:flex; align-items:center; justify-content:center; padding:18px; z-index:70; animation:fadeIn .18s ease-out; }
.cancel-flow-card { width:min(760px,100%); background:#fff; border-radius:24px; padding:24px; box-shadow:0 28px 60px rgba(15,23,42,.28); animation:slideUp .24s cubic-bezier(.2,.8,.2,1); }
.cancel-flow-kicker { display:inline-flex; padding:6px 10px; border-radius:999px; background:#eef5ff; color:#0f62fe; font-size:12px; font-weight:700; text-transform:uppercase; letter-spacing:.05em; }
.cancel-flow-card h2 { margin:12px 0 8px; font-size:30px; }
.cancel-flow-copy { color:#475569; line-height:1.6; margin:0; }
.pause-offer { margin-top:18px; border:1px solid #bfdbfe; background:linear-gradient(180deg,#f8fbff,#eef5ff); border-radius:18px; padding:18px; }
.pause-offer-badge { display:inline-flex; padding:5px 9px; border-radius:999px; background:#0f62fe; color:#fff; font-size:11px; font-weight:700; text-transform:uppercase; letter-spacing:.05em; }
.pause-offer h3 { margin:12px 0 8px; }
.pause-offer p { margin:0 0 14px; color:#334155; line-height:1.55; }
.cancel-flow-actions { display:flex; justify-content:space-between; gap:12px; flex-wrap:wrap; margin-top:18px; }
.link-btn { border:none; background:transparent; color:#475569; font-weight:700; text-decoration:underline; cursor:pointer; padding:0; }
.reason-grid { display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:12px; margin-top:18px; }
.reason-btn { display:flex; flex-direction:column; gap:10px; align-items:flex-start; justify-content:flex-start; min-height:118px; border:1px solid var(--border); border-radius:18px; background:#fff; padding:16px; font:inherit; font-weight:700; color:#0f172a; cursor:pointer; text-align:left; text-decoration:none; }
.reason-btn.selected { border-color:#0f62fe; background:#eef5ff; box-shadow:0 0 0 3px rgba(15,98,254,.12); }
.reason-icon { font-size:26px; line-height:1; }
.data-gift { margin-top:18px; border:1px dashed #94a3b8; border-radius:18px; padding:18px; background:#f8fafc; }
.data-gift h3 { margin:0 0 8px; }
.data-gift p { margin:0 0 14px; color:#475569; line-height:1.55; }
.cancel-confirm-form { margin-top:12px; }
/* farewell */
.farewell { max-width:760px; margin:0 auto; padding:42px 20px; }
.farewell-card { background:#fff; border:1px solid #dbe3ee; border-radius:24px; padding:30px; box-shadow:0 24px 60px rgba(15,23,42,.12); text-align:center; }
.farewell-kicker { display:inline-flex; padding:7px 12px; border-radius:999px; background:#ecfdf5; color:#166534; font-size:12px; font-weight:700; letter-spacing:.04em; text-transform:uppercase; }
.download-note { margin-top:18px; padding:14px 16px; border-radius:16px; background:#eff6ff; border:1px solid #bfdbfe; color:#1e3a8a; }
@keyframes fadeIn { from { opacity:0; } to { opacity:1; } }
@keyframes slideUp { from { opacity:0; transform:translateY(18px) scale(.98); } to { opacity:1; transform:translateY(0) scale(1); } }
@media (max-width:900px) { .grid { grid-template-columns:1fr; } .reason-grid { grid-template-columns:1fr; } }
"""

STEPS = [
    ("Suscripción",        "step1_subscription.html"),
    ("¿Pausar o Cancelar?","step2_cancel_choice.html"),
    ("Encuesta de salida", "step3_survey.html"),
    ("Motivo confirmado",  "step4_survey_confirmed.html"),
    ("Plan Pausa activo",  "step5_pause_success.html"),
    ("Despedida",          "step6_goodbye.html"),
]


def nav_bar(current: int) -> str:
    items = []
    for i, (label, href) in enumerate(STEPS, 1):
        active = i == current
        s = ("background:#0f62fe;color:#fff;font-weight:700;"
             if active else
             "background:rgba(15,23,42,0.07);color:#475569;")
        items.append(
            f'<a href="{href}" style="padding:8px 18px;border-radius:999px;'
            f'text-decoration:none;font-size:13px;{s}">Paso {i}: {label}</a>'
        )
    return (
        '<div style="position:fixed;top:0;left:0;right:0;z-index:999;'
        'background:rgba(255,255,255,0.95);backdrop-filter:blur(12px);'
        'border-bottom:1px solid #dbe3ee;padding:10px 20px;'
        'display:flex;gap:8px;flex-wrap:wrap;align-items:center;">'
        '<span style="color:#0f62fe;font-weight:800;margin-right:8px;font-size:14px;">Cancelación</span>'
        + "".join(items) +
        '</div><div style="height:54px;"></div>'
    )


def full_page(title: str, body: str, step: int) -> str:
    return f"""<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width,initial-scale=1"/>
  <title>{esc(title)} | Lokigi</title>
  <style>{BASE_CSS}</style>
</head>
<body>
{nav_bar(step)}
{body}
</body>
</html>"""


# ── Step 1: Subscription management page ─────────────────────────────────────

def step1_subscription() -> str:
    invoice_rows = "".join(f"""
        <tr>
          <td>INV-{n:04d}</td>
          <td>Pagada</td>
          <td>29.00 USD</td>
          <td>2026-0{n}-01</td>
          <td><a class="btn small" href="#">Descargar factura</a></td>
        </tr>""" for n in range(1, 4))
    body = f"""
<div class="wrap">
  <section class="hero">
    <div class="hero-top">
      <div>
        <span class="status-badge">Activa</span>
        <h1 style="margin:12px 0 0">Gestión de Suscripción</h1>
        <p>Administra el estado del Plan Starter, consulta el histórico de facturas de Stripe y decide cuándo escalar a Growth.</p>
      </div>
      <a href="../growth_dashboard_preview.html" class="btn">← Dashboard</a>
    </div>
  </section>

  <section class="grid">
    <article class="card">
      <div class="muted">Negocio conectado</div>
      <div class="metric" style="font-size:26px">{esc(DEMO_BUSINESS)}</div>
      <div class="muted">Plan actual: Starter</div>
      <div class="muted" style="margin-top:6px">Renovación: 01/06/2026</div>
      <div class="subscription-actions">
        <button class="btn primary" type="button">Actualizar a Growth</button>
        <a class="btn" href="step2_cancel_choice.html">Gestionar Suscripción →</a>
      </div>
    </article>
    <article class="card">
      <h2 style="margin-top:0">Histórico de facturas</h2>
      <div class="muted" style="margin-bottom:12px">Cada factura enlaza al PDF o al hosted invoice de Stripe.</div>
      <table>
        <thead><tr><th>Factura</th><th>Estado</th><th>Importe</th><th>Fecha</th><th>Acción</th></tr></thead>
        <tbody>{invoice_rows}</tbody>
      </table>
    </article>
  </section>
</div>"""
    return full_page("Gestión de Suscripción", body, 1)


# ── Step 2: Cancel choice modal ───────────────────────────────────────────────

def step2_cancel_choice() -> str:
    body = f"""
<div class="wrap" style="display:flex;align-items:center;justify-content:center;min-height:calc(100vh - 54px);">
  <div class="cancel-flow-card" role="dialog" aria-modal="true">
    <div class="cancel-flow-kicker">Retención inteligente</div>
    <h2>¿Necesitas un respiro?</h2>
    <p class="cancel-flow-copy">Antes de cancelar, te ofrecemos una pausa ligera para conservar el valor que ya construiste en Lokigi.</p>
    <section class="pause-offer">
      <div class="pause-offer-badge">Recomendada</div>
      <h3>Pausar mi cuenta</h3>
      <p>Mantendremos tus datos a salvo y tus reportes activos por solo $5/mes. Vuelve cuando quieras.</p>
      <a class="btn primary" href="step5_pause_success.html">Pausar mi cuenta →</a>
    </section>
    <div class="cancel-flow-actions">
      <a class="btn" href="step1_subscription.html">← Seguir con mi plan</a>
      <a class="link-btn" href="step3_survey.html">No, prefiero cancelar mi suscripción</a>
    </div>
  </div>
</div>"""
    return full_page("¿Pausar o Cancelar?", body, 2)


# ── Step 3: Exit survey (no reason selected yet) ──────────────────────────────

def step3_survey() -> str:
    reasons = [
        ("price",           "💲", "Precio",         "El costo no encaja con el valor percibido."),
        ("difficulty",      "⚙️", "Difícil de usar", "La configuración o el uso diario fue confuso."),
        ("business_closed", "🔒", "Cerré mi local",  "El negocio pausó su operación temporalmente."),
    ]
    cards = "".join(
        f'<a class="reason-btn" href="step4_survey_confirmed.html?reason={key}">'
        f'<span class="reason-icon">{icon}</span>'
        f'<span style="font-size:15px">{esc(label)}</span>'
        f'<span style="font-weight:400;font-size:12px;color:#64748b">{esc(desc)}</span>'
        f'</a>'
        for key, icon, label, desc in reasons
    )
    body = f"""
<div class="wrap" style="display:flex;align-items:center;justify-content:center;min-height:calc(100vh - 54px);">
  <div class="cancel-flow-card" role="dialog" aria-modal="true">
    <div class="cancel-flow-kicker">Encuesta de salida</div>
    <h2>Cuéntanos por qué te vas</h2>
    <p class="cancel-flow-copy">Selecciona el motivo principal. Después habilitamos la descarga de tu historial y el cierre definitivo.</p>
    <div class="reason-grid">{cards}</div>
    <section class="data-gift">
      <h3>Antes de irte, llévate tu historial</h3>
      <p>Hemos preparado un archivo con tus reseñas y las respuestas que Lokigi generó. Primero registra el motivo y luego habilitamos la descarga.</p>
      <div class="cancel-confirm-form">
        <button class="btn primary" type="button" disabled style="opacity:.4;cursor:not-allowed;">Generar y Descargar historial (.CSV)</button>
      </div>
    </section>
    <div class="cancel-flow-actions">
      <a class="btn" href="step2_cancel_choice.html">← Volver</a>
      <button class="btn" type="button" disabled style="opacity:.4;cursor:not-allowed;">Cerrar Sesión definitiva</button>
    </div>
  </div>
</div>"""
    return full_page("Encuesta de salida", body, 3)


# ── Step 4: Survey confirmed (reason selected, CSV enabled) ───────────────────

def step4_survey_confirmed() -> str:
    reasons = [
        ("price",           "💲", "Precio",         "El costo no encaja con el valor percibido."),
        ("difficulty",      "⚙️", "Difícil de usar", "La configuración o el uso diario fue confuso."),
        ("business_closed", "🔒", "Cerré mi local",  "El negocio pausó su operación temporalmente."),
    ]
    selected_key = "price"
    selected_label = "Precio"
    cards = "".join(
        f'<div class="reason-btn{" selected" if key == selected_key else ""}">'
        f'<span class="reason-icon">{icon}</span>'
        f'<span style="font-size:15px">{esc(label)}</span>'
        f'<span style="font-weight:400;font-size:12px;color:#64748b">{esc(desc)}</span>'
        f'</div>'
        for key, icon, label, desc in reasons
    )
    body = f"""
<div class="wrap" style="display:flex;align-items:center;justify-content:center;min-height:calc(100vh - 54px);">
  <div class="cancel-flow-card" role="dialog" aria-modal="true">
    <div class="cancel-flow-kicker">Encuesta de salida</div>
    <h2>Cuéntanos por qué te vas</h2>
    <p class="cancel-flow-copy">Motivo registrado. Ya puedes descargar tu CSV y cerrar la sesión definitiva.</p>
    <div class="reason-grid">{cards}</div>
    <div class="notice ok" style="margin-top:14px">
      Motivo registrado: <strong>{esc(selected_label)}</strong>. Ya puedes descargar tu CSV y cerrar la sesión definitiva cuando quieras.
    </div>
    <section class="data-gift">
      <h3>Antes de irte, llévate tu historial</h3>
      <p>Tu archivo con reseñas y respuestas IA está listo para descargar.</p>
      <div class="cancel-confirm-form">
        <a class="btn primary" href="step6_goodbye.html">Generar y Descargar historial (.CSV) →</a>
      </div>
    </section>
    <div class="cancel-flow-actions">
      <a class="btn" href="step3_survey.html">← Volver</a>
      <a class="btn" href="step6_goodbye.html">Cerrar Sesión definitiva</a>
    </div>
  </div>
</div>"""
    return full_page("Motivo confirmado", body, 4)


# ── Step 5: Plan Pausa success ────────────────────────────────────────────────

def step5_pause_success() -> str:
    body = f"""
<div class="wrap" style="display:flex;align-items:center;justify-content:center;min-height:calc(100vh - 54px);">
  <div class="cancel-flow-card" role="dialog" aria-modal="true">
    <div class="cancel-flow-kicker">Cuenta pausada</div>
    <h2>Tu Plan Pausa ya está activo</h2>
    <p class="cancel-flow-copy">Hemos pausado la automatización de respuestas. Pagarás solo $5/mes durante los próximos 90 días.</p>
    <div class="notice ok">
      Tus datos, histórico de IA y reportes siguen disponibles. Solo se suspende la automatización de respuestas.
    </div>
    <div style="margin-top:18px;border:1px solid #bfdbfe;border-radius:16px;padding:16px;background:#f8fbff;">
      <div class="muted" style="font-size:12px;text-transform:uppercase;letter-spacing:.05em;">Resumen Plan Pausa</div>
      <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px;margin-top:12px;">
        <div><div class="muted" style="font-size:12px">Precio</div><div style="font-size:22px;font-weight:800;">$5<span style="font-size:13px;font-weight:400;">/mes</span></div></div>
        <div><div class="muted" style="font-size:12px">Duración</div><div style="font-size:22px;font-weight:800;">90 días</div></div>
        <div><div class="muted" style="font-size:12px">Reactivación</div><div style="font-size:16px;font-weight:700;">01/08/2026</div></div>
      </div>
    </div>
    <div class="cancel-flow-actions">
      <a class="btn primary" href="step1_subscription.html">← Volver a Suscripción</a>
    </div>
  </div>
</div>"""
    return full_page("Plan Pausa activo", body, 5)


# ── Step 6: Goodbye farewell ─────────────────────────────────────────────────

def step6_goodbye() -> str:
    body = f"""
<main class="farewell">
  <section class="farewell-card">
    <div class="farewell-kicker">Último paso</div>
    <h1 style="margin:16px 0 10px;font-size:clamp(28px,5vw,40px);">Gracias por todo, {esc(DEMO_BUSINESS)}</h1>
    <p style="color:#475569;line-height:1.6;">Hemos registrado tu cancelación. Tu plan seguirá activo hasta el <strong>31/05/2026</strong>. Después de esa fecha se suspenderán las automatizaciones.</p>
    <div class="download-note">
      El archivo incluye las reseñas gestionadas y las respuestas de IA que Lokigi preparó por ti.
    </div>
    <div style="margin-top:18px;display:flex;flex-direction:column;gap:12px;align-items:center;">
      <a class="btn primary" href="#" style="width:100%;max-width:340px;justify-content:center;">
        📥 Descargar historial en CSV
      </a>
      <a class="btn" href="step1_subscription.html" style="width:100%;max-width:340px;justify-content:center;">
        ← Volver al inicio
      </a>
    </div>
    <div style="margin-top:24px;border-top:1px solid #e2e8f0;padding-top:16px;">
      <p style="font-size:13px;color:#94a3b8;">¿Cambias de opinión? Puedes reactivar tu cuenta en cualquier momento desde el panel de suscripción.</p>
    </div>
  </section>
</main>"""
    return full_page("Hasta pronto", body, 6)


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    renderers = [
        step1_subscription,
        step2_cancel_choice,
        step3_survey,
        step4_survey_confirmed,
        step5_pause_success,
        step6_goodbye,
    ]
    for i, (renderer, (label, filename)) in enumerate(zip(renderers, STEPS), 1):
        html = renderer()
        out_path = OUT_DIR / filename
        out_path.write_text(html, encoding="utf-8")
        print(f"✓ Paso {i} ({label}): {out_path.name}")

    webbrowser.open("http://localhost:3000/cancellation/step1_subscription.html")
    print("\n📌 URLs del flujo:")
    for i, (label, fname) in enumerate(STEPS, 1):
        print(f"   Paso {i} ({label}) → http://localhost:3000/cancellation/{fname}")


if __name__ == "__main__":
    main()
