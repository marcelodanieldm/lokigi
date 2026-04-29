(function () {
  const STORAGE_KEY = "lokigi-funnel-demo";

  const demoState = {
    lead: {
      id: "demo-4821",
      email: "dueno@cafeaurora.com",
      telefono: "+34 600 123 456",
      negocio: "Cafe Aurora",
      ciudad: "Madrid",
    },
    audit: {
      id: "demo-4821",
      businessName: "Cafe Aurora",
      score: 42,
      marketGap: 18,
      lucroMensual: 850,
      annualRisk: 10200,
      offerPlanExpress: true,
      competitor: {
        name: "Tostado Central",
        score: 67,
        reviews: 438,
      },
      metrics: {
        reviews: 119,
        responseRate: 21,
        profileCompleteness: 54,
      },
      criticalPoints: [
        {
          title: "Resenas sin responder",
          impact: "$340/mes en perdida de conversion",
          severity: "high",
          description: "Hay 37 resenas recientes sin respuesta visible y eso deprime confianza local.",
        },
        {
          title: "Ficha visual desactualizada",
          impact: "$210/mes en trafico no capturado",
          severity: "medium",
          description: "Las ultimas fotos relevantes son antiguas y el perfil pierde clics frente a competidores mas activos.",
        },
        {
          title: "Categoria secundaria ausente",
          impact: "$300/mes en consultas no ganadas",
          severity: "high",
          description: "La ficha no captura busquedas de brunch y desayunos, donde la competencia ya aparece.",
        },
      ],
      comparison: [
        { label: "Score local", you: 42, competitor: 67 },
        { label: "Resenas activas", you: 119, competitor: 438 },
        { label: "Respuesta a reseñas", you: "21%", competitor: "86%" },
        { label: "Fotos recientes", you: 6, competitor: 34 },
      ],
    },
    order: {
      sessionId: "sess_demo_001",
      amount: 9,
      status: "paid",
      deliverable: "Plan de accion SEO local PDF",
      etaHours: 24,
    },
  };

  function saveState(state) {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
  }

  function loadState() {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      if (!raw) {
        saveState(demoState);
        return structuredClone(demoState);
      }
      return { ...structuredClone(demoState), ...JSON.parse(raw) };
    } catch (error) {
      saveState(demoState);
      return structuredClone(demoState);
    }
  }

  function qs(name) {
    return new URLSearchParams(window.location.search).get(name);
  }

  function currency(amount) {
    return new Intl.NumberFormat("es-ES", {
      style: "currency",
      currency: "USD",
      maximumFractionDigits: 0,
    }).format(amount);
  }

  function goTo(path) {
    window.location.href = path;
  }

  function wireLeadForm() {
    const form = document.getElementById("lead-form");
    if (!form) {
      return;
    }

    form.addEventListener("submit", function (event) {
      event.preventDefault();
      const state = loadState();
      const formData = new FormData(form);
      const negocio = String(formData.get("negocio") || "").trim() || state.lead.negocio;
      const email = String(formData.get("email") || "").trim() || state.lead.email;
      const telefono = String(formData.get("telefono") || "").trim() || state.lead.telefono;
      const ciudad = String(formData.get("ciudad") || "").trim() || state.lead.ciudad;
      const id = `lead-${Date.now().toString(36)}`;
      const score = Math.max(27, Math.min(78, 30 + negocio.length + ciudad.length));

      state.lead = { id, negocio, email, telefono, ciudad };
      state.audit = {
        ...state.audit,
        id,
        businessName: negocio,
        score,
        offerPlanExpress: score < 50,
        marketGap: Math.max(8, 60 - score),
        lucroMensual: 420 + (50 - Math.min(score, 50)) * 22,
        annualRisk: (420 + (50 - Math.min(score, 50)) * 22) * 12,
      };
      saveState(state);
      goTo(`audit.html?id=${encodeURIComponent(id)}`);
    });

    const previewButton = document.getElementById("seed-demo");
    if (previewButton) {
      previewButton.addEventListener("click", function () {
        saveState(demoState);
        goTo(`audit.html?id=${encodeURIComponent(demoState.audit.id)}`);
      });
    }
  }

  function renderAudit() {
    const root = document.getElementById("audit-root");
    if (!root) {
      return;
    }

    const state = loadState();
    const audit = state.audit;
    const lead = state.lead;
    const offerHtml = audit.offerPlanExpress
      ? `<div class="cta-card">
          <div class="section-kicker">CTA comercial</div>
          <h3>Hay una solucion rapida para cerrar la brecha.</h3>
          <p>Tu score sigue por debajo del umbral donde normalmente empieza la conversion estable. Puedes comprar un plan express de correccion con entrega estimada en 24 horas.</p>
          <div class="cta-row">
            <button class="button button-primary" id="buy-plan">Comprar por ${currency(9)}</button>
            <a class="button button-secondary" href="index.html">Volver a la captura</a>
          </div>
        </div>`
      : `<div class="cta-card">
          <div class="section-kicker">Sin oferta directa</div>
          <h3>Tu ficha ya esta en una zona media saludable.</h3>
          <p>No activamos compra inmediata. El siguiente paso razonable es seguimiento, mejoras graduales y nurturing comercial.</p>
          <div class="cta-row">
            <a class="button button-secondary" href="index.html">Crear otro lead</a>
          </div>
        </div>`;

    root.innerHTML = `
      <section class="audit-hero">
        <div class="score-card">
          <div class="micro-label">Score local detectado</div>
          <div class="score-ring" style="--score:${audit.score};">
            <div>
              <strong>${audit.score}</strong>
              <div class="small-copy">sobre 100</div>
            </div>
          </div>
          <p>Negocio evaluado: <strong>${audit.businessName}</strong><br>Lead: ${lead.email}</p>
        </div>
        <div class="panel">
          <div class="section-kicker">Lectura ejecutiva</div>
          <h2>Estas perdiendo visibilidad donde la competencia ya capitaliza la demanda local.</h2>
          <p>Detectamos una brecha de <strong>${audit.marketGap} puntos</strong> frente al competidor principal y un riesgo estimado de <strong>${currency(audit.lucroMensual)}/mes</strong> en ventas no capturadas.</p>
          <div class="grid-3">
            <div class="stat"><div class="stat-title">Lucro cesante mensual</div><div class="stat-value">${currency(audit.lucroMensual)}</div></div>
            <div class="stat"><div class="stat-title">Riesgo anual</div><div class="stat-value">${currency(audit.annualRisk)}</div></div>
            <div class="stat"><div class="stat-title">Respuesta a resenas</div><div class="stat-value">${audit.metrics.responseRate}%</div></div>
          </div>
        </div>
      </section>
      <section class="audit-grid">
        <div class="critical-card">
          <div class="section-kicker">3 fallos criticos</div>
          <h3>Lo que esta frenando tu conversion local</h3>
          <ul class="list-reset">
            ${audit.criticalPoints.map(function (point) {
              const severityClass = point.severity === "high" ? "severity-high" : "severity-medium";
              return `<li class="list-item"><strong>${point.title}</strong><div class="${severityClass}">${point.impact}</div><p>${point.description}</p></li>`;
            }).join("")}
          </ul>
        </div>
        <div class="compare-card">
          <div class="section-kicker">Comparativa local</div>
          <h3>Tu ficha vs ${audit.competitor.name}</h3>
          <table class="compare-table">
            <thead>
              <tr><th>Metricas</th><th>Tu negocio</th><th>Competidor</th></tr>
            </thead>
            <tbody>
              ${audit.comparison.map(function (row) {
                return `<tr><td>${row.label}</td><td>${row.you}</td><td>${row.competitor}</td></tr>`;
              }).join("")}
            </tbody>
          </table>
          <div style="margin-top:16px">
            <span class="pill">Competidor principal score ${audit.competitor.score}</span>
            <span class="pill">${audit.competitor.reviews} resenas activas</span>
          </div>
        </div>
      </section>
      <section style="margin-top:18px">${offerHtml}</section>
    `;

    const buyButton = document.getElementById("buy-plan");
    if (buyButton) {
      buyButton.addEventListener("click", function () {
        const nextState = loadState();
        nextState.order = {
          ...nextState.order,
          status: "paid",
          amount: 9,
        };
        saveState(nextState);
        goTo(`success.html?id=${encodeURIComponent(audit.id)}&session_id=${encodeURIComponent(nextState.order.sessionId)}`);
      });
    }
  }

  function renderSuccess() {
    const root = document.getElementById("success-root");
    if (!root) {
      return;
    }

    const state = loadState();
    const audit = state.audit;
    const lead = state.lead;
    const order = state.order;
    const auditId = qs("id") || audit.id;

    root.innerHTML = `
      <section class="success-grid">
        <div class="success-card">
          <div class="section-kicker">Pago confirmado</div>
          <h2>Tu compra ya entro en produccion.</h2>
          <p>Registramos el pago del <strong>${order.deliverable}</strong> para <strong>${audit.businessName}</strong>. En un flujo real, aqui vendria la confirmacion desde Stripe y luego la recuperacion de la orden.</p>
          <div class="grid-2">
            <div class="stat"><div class="stat-title">Monto</div><div class="stat-value">${currency(order.amount)}</div></div>
            <div class="stat"><div class="stat-title">Entrega estimada</div><div class="stat-value">${order.etaHours}h</div></div>
          </div>
        </div>
        <div class="success-card">
          <div class="section-kicker">Proximos pasos</div>
          <h3>Que ve el cliente despues de pagar</h3>
          <ul class="list-reset">
            <li class="list-item"><strong>1.</strong> Confirmacion visual del pago y session id <span class="small-copy">${order.sessionId}</span></li>
            <li class="list-item"><strong>2.</strong> Mensaje de entrega y expectativa temporal</li>
            <li class="list-item"><strong>3.</strong> Regreso a la auditoria para revisar contexto y CTA completado</li>
          </ul>
          <p class="small-copy">Contacto confirmado para seguimiento: ${lead.email}</p>
        </div>
      </section>
      <section class="success-card" style="margin-top:18px; text-align:center;">
        <div class="section-kicker">Navegacion</div>
        <h3>Desde aqui el funnel ya convierto.</h3>
        <p>Puedes volver a la auditoria, crear un nuevo lead o reiniciar la demo completa.</p>
        <div class="success-actions">
          <a class="button button-primary" href="audit.html?id=${encodeURIComponent(auditId)}">Volver a la auditoria</a>
          <a class="button button-secondary" href="index.html">Crear otro lead</a>
          <button class="button button-ghost" id="reset-demo">Reiniciar demo</button>
        </div>
      </section>
    `;

    const resetButton = document.getElementById("reset-demo");
    if (resetButton) {
      resetButton.addEventListener("click", function () {
        saveState(demoState);
        goTo("index.html");
      });
    }
  }

  document.addEventListener("DOMContentLoaded", function () {
    wireLeadForm();
    renderAudit();
    renderSuccess();
  });
})();