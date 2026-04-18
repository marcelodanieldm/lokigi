import type { MonthlyReportRow, TopReviewRow } from "./db.js";
import type { ExecutiveSummary } from "./executive-summary.js";
import { config } from "./config.js";

function esc(value: unknown): string {
  return String(value ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/\"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function pct(value: number, total: number): string {
  if (!total) return "0";
  return ((value / total) * 100).toFixed(1);
}

function stars(value: number | null | undefined): string {
  const n = Math.max(0, Math.min(5, Number(value || 0)));
  return `${"★".repeat(n)}${"☆".repeat(5 - n)}`;
}

function fmt(value: number | null | undefined, decimals = 1): string {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return "-";
  return Number(value).toFixed(decimals);
}

function trimText(value: string | null | undefined, max = 220): string {
  const text = String(value || "").trim();
  if (!text) return "Sin comentario";
  if (text.length <= max) return text;
  return `${text.slice(0, max - 1)}...`;
}

export function buildReportHtml(report: MonthlyReportRow, summary: ExecutiveSummary, topReviews: TopReviewRow[]): string {
  const payload = report.payload || {};
  const kpis = payload.kpis || {};
  const valueMetrics = payload.value_metrics || {};
  const sentiment = payload.sentiment || {};
  const growthPremium = payload.growth_premium || {};
  const premiumAnalysis = growthPremium.analysis || {};
  const multiLocation = premiumAnalysis.multi_location || {};
  const localDominance = premiumAnalysis.local_dominance_state || {};

  const businessName = payload.business_name || "Negocio";

  const positive = Number(sentiment.positive_reviews || 0);
  const neutral = Number(sentiment.neutral_reviews || 0);
  const negative = Number(sentiment.negative_reviews || 0);
  const totalSent = positive + neutral + negative;

  const positiveConcepts = Array.isArray(sentiment.positive_concepts) ? sentiment.positive_concepts : [];
  const negativeConcepts = Array.isArray(sentiment.negative_concepts) ? sentiment.negative_concepts : [];

  const totalReviews = Number(kpis.total_reviews || 0);
  const responseRate = Number(kpis.response_rate_pct || 0);
  const avgRating = kpis.avg_rating != null ? Number(kpis.avg_rating) : null;

  const aiRepliesEstimate = Math.round(totalReviews * (responseRate / 100));
  const estimatedTimeSavedMinutes = aiRepliesEstimate * 4;
  const estimatedTimeSavedLabel = estimatedTimeSavedMinutes >= 60
    ? `${(estimatedTimeSavedMinutes / 60).toFixed(1)} h`
    : `${estimatedTimeSavedMinutes} min`;

  const logo = config.logoUrl
    ? `<img src="${esc(config.logoUrl)}" alt="Lokigi" style="height:30px" />`
    : `<div style="font-size:24px;font-weight:800;color:#1a56db">Lokigi</div>`;

  const sentimentRowsHtml = [
    ["Positivas", positive, pct(positive, totalSent), "var(--positive)"],
    ["Neutrales", neutral, pct(neutral, totalSent), "var(--neutral)"],
    ["Negativas", negative, pct(negative, totalSent), "var(--negative)"],
  ]
    .map(
      ([label, count, width, color]) => `
        <div class="bar-row">
          <div>${esc(label)}</div>
          <div class="bar-bg"><div class="bar-fill" style="width:${esc(width)}%;background:${esc(color)}"></div></div>
          <div>${esc(count)}</div>
        </div>
      `,
    )
    .join("");

  const loveListHtml = positiveConcepts.length
    ? positiveConcepts
        .slice(0, 5)
        .map((item: any) => `<li><strong>${esc(item.concept || "Concepto")}</strong> · ${esc(item.count || 0)} menciones</li>`)
        .join("")
    : "<li>Sin patrones positivos destacados este periodo.</li>";

  const painListHtml = negativeConcepts.length
    ? negativeConcepts
        .slice(0, 5)
        .map((item: any) => `<li><strong>${esc(item.concept || "Concepto")}</strong> · ${esc(item.count || 0)} menciones</li>`)
        .join("")
    : "<li>Sin fricciones negativas relevantes este periodo.</li>";

  const voiceCardsHtml = topReviews.length
    ? topReviews
        .map(
          (item, idx) => `
          <article class="voice-card">
            <div class="voice-head">
              <div class="voice-rank">Top ${idx + 1}</div>
              <div class="voice-author">${esc(item.author_display_name || "Cliente")}</div>
              <div class="voice-stars">${esc(stars(item.rating))}</div>
            </div>
            <p class="voice-review">"${esc(trimText(item.comment, 240))}"</p>
            <div class="voice-reply-box">
              <div class="voice-reply-label">Respuesta generada por Lokigi</div>
              <p class="voice-reply">${esc(trimText(item.reply_public_text || "Gracias por tu resena. Seguimos trabajando para ofrecerte una experiencia excelente.", 260))}</p>
            </div>
          </article>
        `,
        )
        .join("")
    : `
      <article class="voice-card">
        <div class="voice-head">
          <div class="voice-rank">Top 1-3</div>
          <div class="voice-author">Sin resenas suficientes</div>
          <div class="voice-stars">☆☆☆☆☆</div>
        </div>
        <p class="voice-review">Aun no hay resenas destacadas para este periodo.</p>
      </article>
    `;

  const locationItems = Array.isArray(multiLocation.items) ? multiLocation.items : [];
  const locationRowsHtml = locationItems.length
    ? locationItems
        .map(
          (item: any) => `
          <tr>
            <td>${esc(item.location_label || "default")}</td>
            <td>${esc(fmt(item.market_share_pack_pct, 1))}%</td>
            <td>${esc(fmt(item.keyword_conquest_rate_pct, 1))}%</td>
            <td>${esc(fmt(item.avg_client_rank, 2))}</td>
            <td>${esc(fmt(item.momentum_score, 1))}</td>
          </tr>
        `,
        )
        .join("")
    : "<tr><td colspan='5'>Sin datos multi-sede disponibles.</td></tr>";

  const heatmapRows = Array.isArray(localDominance.heatmap) ? localDominance.heatmap : [];
  const heatmapHtml = heatmapRows.length
    ? heatmapRows
        .map(
          (row: any) => `
            <div class="heat-item ${esc(String(row.band || "low"))}">
              <div class="heat-label">${esc(row.location_label || "default")}</div>
              <div class="heat-metrics">MSP ${esc(fmt(row.market_share_pack_pct, 1))}% · Rank ${esc(fmt(row.avg_client_rank, 2))}</div>
            </div>
          `,
        )
        .join("")
    : "<p class='p'>No hay heatmap disponible.</p>";

  const localState = String(localDominance.status || "insufficient_data");
  const stateLabel = localState === "dominant"
    ? "Dominio Solido"
    : localState === "contested"
      ? "Dominio en Disputa"
      : localState === "under_attack"
        ? "Dominio Bajo Ataque"
        : "Sin datos suficientes";

  const trophy = localDominance?.winner?.location_label
    ? `Trofeo de dominio: ${String(localDominance.winner.location_label)}`
    : "Trofeo de dominio no disponible";

  const tips = [
    "Mantener tasa de respuesta por encima de 90%.",
    "Escalar los conceptos positivos mas repetidos en mensajes comerciales.",
    "Corregir la principal friccion negativa detectada este mes.",
  ];
  const strategicTipsHtml = tips.map((tip) => `<li>${esc(tip)}</li>`).join("");

  return `<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8" />
  <style>
    :root {
      --bg: #edf2f9;
      --paper: #ffffff;
      --ink: #0f172a;
      --muted: #64748b;
      --line: #dbe5f1;
      --brand: #1a56db;
      --brand-soft: #e8f0ff;
      --positive: #60a5fa;
      --neutral: #cbd5e1;
      --negative: #f87171;
    }
    @page { size: A4; margin: 16mm; }
    body { font-family: "Inter", "Segoe UI", Arial, sans-serif; color: var(--ink); margin: 0; background: var(--bg); }
    .report { padding: 12px; }
    .page {
      background: var(--paper);
      border: 1px solid var(--line);
      border-radius: 16px;
      padding: 20px;
      margin-bottom: 12px;
      page-break-after: always;
      break-after: page;
      min-height: calc(297mm - 32mm);
    }
    .page:last-child { page-break-after: auto; break-after: auto; }
    .header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 14px; padding-bottom: 10px; border-bottom: 1px solid var(--line); }
    .title { font-size: 22px; font-weight: 800; }
    .sub { color: var(--muted); font-size: 12px; margin-top: 2px; }
    .page-number { font-size: 11px; color: var(--muted); font-weight: 700; text-transform: uppercase; }
    .section-kicker { font-size: 11px; text-transform: uppercase; color: var(--muted); font-weight: 700; margin: 0 0 10px; }
    .card { border: 1px solid var(--line); border-radius: 12px; padding: 12px; margin-bottom: 12px; }
    .kpi-grid { display:grid; grid-template-columns: repeat(3, 1fr); gap:10px; }
    .kpi { background: var(--brand-soft); border: 1px solid #cfe0ff; border-radius: 10px; padding: 10px; }
    .kpi .label { color: var(--muted); font-size: 11px; text-transform: uppercase; font-weight: 700; }
    .kpi .value { color: var(--brand); font-weight: 800; font-size: 22px; margin-top: 4px; }
    .bar-wrap { margin-top: 8px; display: grid; gap: 8px; }
    .bar-row { display:grid; grid-template-columns:120px 1fr 56px; gap:8px; align-items:center; font-size:12px; }
    .bar-bg { background:#edf2f8; border-radius:999px; overflow:hidden; height:12px; }
    .bar-fill { height:100%; }
    .p { margin:0 0 10px; line-height:1.5; font-size:13px; color:#1f2937; }
    .story-grid { display:grid; grid-template-columns: 1fr 1fr; gap: 10px; }
    .story-list { margin:0; padding-left: 18px; font-size: 13px; color: #334155; display:grid; gap:6px; }
    .voice-grid { display:grid; gap: 10px; }
    .voice-card { border:1px solid var(--line); border-radius:10px; padding:10px; background:#f9fbff; }
    .voice-head { display:grid; grid-template-columns: 64px 1fr auto; gap:8px; align-items:center; margin-bottom:7px; }
    .voice-rank { background: var(--brand); color:#fff; border-radius:999px; font-size:11px; text-align:center; padding:4px 8px; }
    .voice-author { font-size:12px; font-weight:700; }
    .voice-stars { font-size:12px; color:#b45309; font-weight:700; }
    .voice-review { margin:0 0 7px; font-size:12px; color:#334155; line-height:1.4; }
    .voice-reply-box { border-radius:8px; border:1px solid #d9e6ff; background:#f3f7ff; padding:8px; }
    .voice-reply-label { font-size:10px; text-transform:uppercase; color:#4b6fc2; font-weight:700; margin-bottom:4px; }
    .voice-reply { margin:0; font-size:12px; color:#1e3a8a; line-height:1.4; }
    .tips-list { margin:0; padding-left: 18px; display:grid; gap: 8px; }
    .footer { margin-top: 18px; color: #94a3b8; font-size: 11px; text-align:center; }
    table { width: 100%; border-collapse: collapse; font-size: 12px; }
    th, td { border: 1px solid var(--line); padding: 8px; text-align: left; }
    th { background: #f5f9ff; color: #334155; }
    .state-pill { display: inline-block; padding: 5px 10px; border-radius: 999px; font-size: 11px; font-weight: 700; background: #e8f0ff; color: #1e40af; margin-bottom: 8px; }
    .heat-grid { display:grid; gap: 8px; }
    .heat-item { border-radius: 10px; padding: 8px 10px; border: 1px solid var(--line); }
    .heat-item.high { background: #ebf8ff; border-color: #93c5fd; }
    .heat-item.mid { background: #fff7ed; border-color: #fdba74; }
    .heat-item.low { background: #fef2f2; border-color: #fca5a5; }
    .heat-label { font-weight: 700; font-size: 12px; }
    .heat-metrics { font-size: 12px; color: #475569; margin-top: 2px; }
  </style>
</head>
<body>
  <main class="report">
    <section class="page">
      <div class="header">
        <div>${logo}</div>
        <div style="text-align:right">
          <div class="page-number">Pagina 1 · Valor Ejecutivo</div>
          <div class="title">Reporte Mensual Lokigi</div>
          <div class="sub">${esc(businessName)} · ${esc(report.month)}/${esc(report.year)}</div>
        </div>
      </div>
      <div class="card">
        <p class="section-kicker">Resumen ejecutivo</p>
        <p class="p">${esc(summary.paragraph_1_client_voice)}</p>
        <p class="p">${esc(summary.paragraph_2_key_achievement)}</p>
        <p class="p">${esc(summary.paragraph_3_improvement_opportunity)}</p>
      </div>
      <div class="card">
        <p class="section-kicker">Metricas estrella</p>
        <div class="kpi-grid">
          <div class="kpi"><div class="label">Resenas totales</div><div class="value">${esc(totalReviews)}</div></div>
          <div class="kpi"><div class="label">Tasa de respuesta IA</div><div class="value">${esc(fmt(responseRate, 0))}%</div></div>
          <div class="kpi"><div class="label">Nota media</div><div class="value">${esc(avgRating !== null ? avgRating.toFixed(1) : "-")}</div></div>
        </div>
        <p class="p" style="margin-top:10px">Tiempo estimado ahorrado: ${esc(estimatedTimeSavedLabel)} (${esc(aiRepliesEstimate)} respuestas IA).</p>
      </div>
      <div class="footer">Generado por Lokigi · ${esc(config.appDomain)}</div>
    </section>

    <section class="page">
      <div class="header">
        <div>${logo}</div>
        <div style="text-align:right">
          <div class="page-number">Pagina 2 · Analisis de Sentimiento</div>
          <div class="title">Pulso de clientes</div>
          <div class="sub">Que aman y que molesta</div>
        </div>
      </div>
      <div class="card">
        <p class="section-kicker">Distribucion</p>
        <div class="bar-wrap">${sentimentRowsHtml}</div>
      </div>
      <div class="story-grid">
        <div class="card" style="margin-bottom:0"><p class="section-kicker">Puntos fuertes</p><ul class="story-list">${loveListHtml}</ul></div>
        <div class="card" style="margin-bottom:0"><p class="section-kicker">Puntos de friccion</p><ul class="story-list">${painListHtml}</ul></div>
      </div>
      <div class="card">
        <p class="section-kicker">Lectura operativa</p>
        <p class="p">${esc(valueMetrics?.response_velocity?.baseline_source === "google_history"
          ? "Comparativa de velocidad con historial real previo."
          : "Comparativa de velocidad con baseline de referencia por falta de historial completo.")}</p>
      </div>
      <div class="footer">Generado por Lokigi · ${esc(config.appDomain)}</div>
    </section>

    <section class="page">
      <div class="header">
        <div>${logo}</div>
        <div style="text-align:right">
          <div class="page-number">Pagina 3 · Mejores Interacciones</div>
          <div class="title">Reviews destacadas</div>
          <div class="sub">Casos con mayor valor reputacional</div>
        </div>
      </div>
      <div class="card"><div class="voice-grid">${voiceCardsHtml}</div></div>
      <div class="footer">Generado por Lokigi · ${esc(config.appDomain)}</div>
    </section>

    <section class="page">
      <div class="header">
        <div>${logo}</div>
        <div style="text-align:right">
          <div class="page-number">Pagina 4 · Estrategia Lokigi</div>
          <div class="title">Acciones recomendadas</div>
          <div class="sub">Plan del proximo mes</div>
        </div>
      </div>
      <div class="card">
        <p class="section-kicker">Siguiente ciclo</p>
        <ul class="tips-list">${strategicTipsHtml}</ul>
      </div>
      <div class="footer">Generado por Lokigi · ${esc(config.appDomain)}</div>
    </section>

    <section class="page">
      <div class="header">
        <div>${logo}</div>
        <div style="text-align:right">
          <div class="page-number">Pagina 5 · Growth Multi-Sede</div>
          <div class="title">Estado de Dominio Local</div>
          <div class="sub">Comparativa hasta 5 sedes</div>
        </div>
      </div>
      <div class="card">
        <p class="section-kicker">Comparativa multi-ubicacion</p>
        <table>
          <thead>
            <tr>
              <th>Sede</th>
              <th>MSP</th>
              <th>Conquest</th>
              <th>Rank medio</th>
              <th>Momentum</th>
            </tr>
          </thead>
          <tbody>
            ${locationRowsHtml}
          </tbody>
        </table>
      </div>
      <div class="card">
        <p class="section-kicker">Dominio local</p>
        <div class="state-pill">${esc(stateLabel)}</div>
        <p class="p"><strong>${esc(trophy)}</strong></p>
        <p class="p">${esc(localDominance.recommended_action || "No hay accion recomendada por falta de datos.")}</p>
        <div class="heat-grid">${heatmapHtml}</div>
      </div>
      <div class="footer">Generado por Lokigi · ${esc(config.appDomain)}</div>
    </section>
  </main>
</body>
</html>`;
}
