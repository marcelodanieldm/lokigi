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

function trimText(value: string | null | undefined, max = 220): string {
  const text = String(value || "").trim();
  if (!text) return "Sin comentario";
  if (text.length <= max) return text;
  return `${text.slice(0, max - 1)}…`;
}

export function buildReportHtml(
  report: MonthlyReportRow,
  summary: ExecutiveSummary,
  topReviews: TopReviewRow[],
): string {
  const payload = report.payload || {};
  const kpis = payload.kpis || {};
  const valueMetrics = payload.value_metrics || {};
  const sentiment = payload.sentiment || {};
  const businessName = payload.business_name || "Negocio";

  const positive = Number(sentiment.positive_reviews || 0);
  const neutral = Number(sentiment.neutral_reviews || 0);
  const negative = Number(sentiment.negative_reviews || 0);
  const totalSent = positive + neutral + negative;

  const positiveConcepts = Array.isArray(sentiment.positive_concepts) ? sentiment.positive_concepts : [];
  const negativeConcepts = Array.isArray(sentiment.negative_concepts) ? sentiment.negative_concepts : [];
  const topConcepts = Array.isArray(sentiment.top_concepts) ? sentiment.top_concepts : [];

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
        .map(
          (item: any) =>
            `<li><strong>${esc(item.concept || "Concepto")}</strong> · ${esc(item.count || 0)} menciones</li>`,
        )
        .join("")
    : "<li>Sin patrones positivos destacados este periodo.</li>";

  const painListHtml = negativeConcepts.length
    ? negativeConcepts
        .slice(0, 5)
        .map(
          (item: any) =>
            `<li><strong>${esc(item.concept || "Concepto")}</strong> · ${esc(item.count || 0)} menciones</li>`,
        )
        .join("")
    : "<li>Sin fricciones negativas relevantes este periodo.</li>";

  const strategicTips: string[] = [];
  if (negativeConcepts[0]?.concept) {
    strategicTips.push(
      `Reduce la friccion en "${String(negativeConcepts[0].concept)}" con una accion operativa semanal y seguimiento quincenal.`,
    );
  }
  if (responseRate < 85) {
    strategicTips.push(
      `Sube la tasa de respuesta al 90% como objetivo del proximo mes para reforzar reputacion y conversacion activa.`,
    );
  }
  if (positiveConcepts[0]?.concept) {
    strategicTips.push(
      `Convierte "${String(positiveConcepts[0].concept)}" en promesa visible dentro de tus mensajes y respuestas publicas.`,
    );
  }
  if (avgRating !== null && avgRating < 4.5) {
    strategicTips.push(
      "Implementa una rutina de cierre de servicio con solicitud de resena para empujar la nota media por encima de 4.5.",
    );
  }
  if (!strategicTips.length) {
    strategicTips.push("Mantener consistencia de respuesta y escalar las mejores practicas detectadas en clientes satisfechos.");
    strategicTips.push("Refuerza la captacion de nuevas resenas para mejorar precision de insights mensuales.");
  }
  while (strategicTips.length < 3) {
    strategicTips.push("Define una accion concreta por semana y revisa avance contra KPI al cierre del mes.");
  }

  const strategicTipsHtml = strategicTips
    .slice(0, 4)
    .map((tip, idx) => `<li><span class="tip-index">${idx + 1}</span><span>${esc(tip)}</span></li>`)
    .join("");

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
            <p class="voice-review">“${esc(trimText(item.comment, 240))}”</p>
            <div class="voice-reply-box">
              <div class="voice-reply-label">Respuesta generada por Lokigi</div>
              <p class="voice-reply">${esc(trimText(item.reply_public_text || "Gracias por tu reseña. Seguimos trabajando para ofrecerte una experiencia excelente.", 260))}</p>
            </div>
          </article>
        `,
        )
        .join("")
    : `
      <article class="voice-card">
        <div class="voice-head">
          <div class="voice-rank">Top 1-3</div>
          <div class="voice-author">Sin reseñas suficientes</div>
          <div class="voice-stars">☆☆☆☆☆</div>
        </div>
        <p class="voice-review">Aún no hay reseñas destacadas para este período.</p>
        <div class="voice-reply-box">
          <div class="voice-reply-label">Respuesta generada por Lokigi</div>
          <p class="voice-reply">Cuando llegue más volumen de reseñas, esta sección mostrará tus mejores casos con respuesta sugerida.</p>
        </div>
      </article>
    `;

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
    @page {
      size: A4;
      margin: 16mm;
    }
    body {
      font-family: "Inter", "Segoe UI", Arial, sans-serif;
      color: var(--ink);
      margin: 0;
      background: var(--bg);
    }
    .report {
      padding: 14px;
    }
    .page {
      background: var(--paper);
      border: 1px solid var(--line);
      border-radius: 18px;
      padding: 22px;
      box-shadow: 0 8px 30px rgba(15, 23, 42, 0.05);
      margin-bottom: 14px;
      page-break-after: always;
      break-after: page;
      min-height: calc(297mm - 32mm);
    }
    .page:last-child {
      page-break-after: auto;
      break-after: auto;
    }
    .header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 18px;
      padding-bottom: 12px;
      border-bottom: 1px solid var(--line);
    }
    .title { font-size: 23px; font-weight: 800; letter-spacing: -0.02em; }
    .sub { color: var(--muted); font-size: 12px; margin-top: 2px; }
    .page-number {
      font-size: 11px;
      color: var(--muted);
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.08em;
    }
    .section-kicker {
      font-size: 11px;
      text-transform: uppercase;
      letter-spacing: 0.09em;
      color: var(--muted);
      margin: 0 0 10px;
      font-weight: 700;
    }
    .card {
      border: 1px solid var(--line);
      border-radius: 14px;
      padding: 14px;
      margin-bottom: 14px;
      background: var(--paper);
    }
    .kpi-grid { display:grid; grid-template-columns: repeat(3, 1fr); gap:10px; }
    .kpi {
      background: var(--brand-soft);
      border: 1px solid #cfe0ff;
      border-radius: 12px;
      padding: 11px;
    }
    .kpi .label { color: var(--muted); font-size: 11px; text-transform: uppercase; font-weight: 700; }
    .kpi .value { color: var(--brand); font-weight: 800; font-size: 24px; line-height: 1.1; margin-top: 4px; }
    .bar-wrap { margin-top: 10px; display: grid; gap: 9px; }
    .bar-row { display:grid; grid-template-columns:120px 1fr 56px; gap:8px; align-items:center; font-size:12px; }
    .bar-bg { background:#edf2f8; border-radius:999px; overflow:hidden; height:12px; }
    .bar-fill { height:100%; }
    .p { margin:0 0 10px; line-height:1.55; font-size:13px; color:#1f2937; }
    .story-grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 10px;
    }
    .story-list {
      margin: 0;
      padding-left: 18px;
      color: #334155;
      line-height: 1.5;
      font-size: 13px;
      display: grid;
      gap: 6px;
    }
    .tips-list {
      list-style: none;
      margin: 0;
      padding: 0;
      display: grid;
      gap: 10px;
    }
    .tips-list li {
      border: 1px solid var(--line);
      background: #f8fbff;
      border-radius: 10px;
      padding: 10px;
      display: grid;
      grid-template-columns: 28px 1fr;
      gap: 8px;
      align-items: start;
      font-size: 13px;
      color: #1f2937;
      line-height: 1.45;
    }
    .tip-index {
      width: 24px;
      height: 24px;
      border-radius: 999px;
      background: var(--brand);
      color: #fff;
      font-size: 12px;
      font-weight: 700;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      margin-top: 1px;
    }
    .voice-grid { display: grid; gap: 10px; }
    .voice-card {
      border: 1px solid var(--line);
      border-radius: 12px;
      padding: 12px;
      background: linear-gradient(180deg, #ffffff, #f8fbff);
    }
    .voice-head {
      display: grid;
      grid-template-columns: 64px 1fr auto;
      gap: 10px;
      align-items: center;
      margin-bottom: 8px;
    }
    .voice-rank {
      background: var(--brand);
      color: #fff;
      border-radius: 999px;
      font-size: 11px;
      font-weight: 700;
      text-align: center;
      padding: 4px 8px;
    }
    .voice-author { font-size: 12px; font-weight: 700; color: #1f2937; }
    .voice-stars { font-size: 12px; color: #b45309; font-weight: 700; }
    .voice-review { margin: 0 0 8px; font-size: 12px; color: #334155; line-height: 1.45; }
    .voice-reply-box {
      border-radius: 10px;
      border: 1px solid #d9e6ff;
      background: #f3f7ff;
      padding: 8px;
    }
    .voice-reply-label {
      font-size: 10px;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      color: #4b6fc2;
      font-weight: 700;
      margin-bottom: 5px;
    }
    .voice-reply { margin: 0; font-size: 12px; color: #1e3a8a; line-height: 1.45; }
    .footer { margin-top: 20px; color: #94a3b8; font-size: 11px; text-align: center; }
  </style>
      .hero-metrics {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 12px;
        margin-bottom: 14px;
      }
      .hero-card {
        border: 1px solid #cfe0ff;
        background: linear-gradient(180deg, #eff5ff, #f9fbff);
        border-radius: 12px;
        padding: 14px;
      }
      .hero-label {
        font-size: 11px;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: #4f6fb6;
        font-weight: 700;
        margin-bottom: 5px;
      }
      .hero-value {
        color: var(--brand);
        font-size: 32px;
        font-weight: 800;
        line-height: 1;
      }
      .hero-sub {
        font-size: 12px;
        color: #4b5563;
        margin-top: 6px;
      }
</head>
<body>
  <main class="sheet">
    <div class="header">
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

        <div class="hero-metrics">
          <article class="hero-card">
            <div class="hero-label">Nota media</div>
            <div class="hero-value">${esc(avgRating !== null ? avgRating.toFixed(1) : "-")}</div>
            <div class="hero-sub">Percepcion global de clientes en este periodo.</div>
          </article>
          <article class="hero-card">
            <div class="hero-label">Tiempo ahorrado</div>
            <div class="hero-value">${esc(estimatedTimeSavedLabel)}</div>
            <div class="hero-sub">Estimacion: ${esc(aiRepliesEstimate)} respuestas IA x 4 min.</div>
          </article>
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
            <div class="kpi"><div class="label">Tasa de respuesta IA</div><div class="value">${esc(responseRate.toFixed(0))}%</div></div>
            <div class="kpi"><div class="label">Tiempo medio respuesta</div><div class="value">${esc(kpis.avg_response_time_minutes ?? "-")}</div></div>
          </div>
        </div>

        <div class="footer">Generado por Lokigi · ${esc(config.appDomain)}</div>
      </section>

      <section class="page">
        <div class="header">
          <div>${logo}</div>
          <div style="text-align:right">
            <div class="page-number">Pagina 2 · Analisis de Sentimiento</div>
            <div class="title">Que aman y que molesta</div>
            <div class="sub">Pulso emocional del mes</div>
          </div>
        </div>

        <div class="card">
          <p class="section-kicker">Distribucion de sentimiento</p>
          <div class="bar-wrap">
            ${sentimentRowsHtml}
          </div>
        </div>

        <div class="story-grid">
          <div class="card" style="margin-bottom:0">
            <p class="section-kicker">Que aman tus clientes</p>
            <ul class="story-list">${loveListHtml}</ul>
          </div>
          <div class="card" style="margin-bottom:0">
            <p class="section-kicker">Que les molesta</p>
            <ul class="story-list">${painListHtml}</ul>
          </div>
        </div>

        <div class="card">
          <p class="section-kicker">Lectura Lokigi</p>
          <p class="p">${esc(valueMetrics?.response_velocity?.baseline_source === "google_history"
            ? "La comparativa usa historial real previo y permite medir mejora operativa con mayor precision."
            : "La comparativa usa una linea base estandar por falta de historial completo en Google.")}</p>
          <p class="p">${esc(topConcepts[0]?.concept
            ? `El concepto dominante del periodo fue "${String(topConcepts[0].concept)}", util para orientar comunicacion y servicio.`
            : "No hubo un concepto dominante lo suficientemente fuerte este mes.")}</p>
        </div>

        <div class="footer">Generado por Lokigi · ${esc(config.appDomain)}</div>
      </section>

      <section class="page">
        <div class="header">
          <div>${logo}</div>
          <div style="text-align:right">
            <div class="page-number">Pagina 3 · Mejores Interacciones</div>
            <div class="title">Seleccion de reviews destacadas</div>
            <div class="sub">Interacciones con mayor valor reputacional</div>
          </div>
        </div>

        <div class="card">
          <p class="section-kicker">Tu voz en el mundo</p>
          <div class="voice-grid">
            ${voiceCardsHtml}
          </div>
        </div>

        <div class="footer">Generado por Lokigi · ${esc(config.appDomain)}</div>
      </section>

      <section class="page">
        <div class="header">
          <div>${logo}</div>
          <div style="text-align:right">
            <div class="page-number">Pagina 4 · Estrategia Lokigi</div>
            <div class="title">Consejos para el proximo mes</div>
            <div class="sub">Plan de accion recomendado</div>
          </div>
        </div>

        <div class="card">
          <p class="section-kicker">Consejos estrategicos de Lokigi</p>
          <ul class="tips-list">
            ${strategicTipsHtml}
          </ul>
        </div>

        <div class="card">
          <p class="section-kicker">Objetivo operativo del siguiente ciclo</p>
          <p class="p">Eleva consistencia: responde mas rapido, protege los conceptos positivos dominantes y corrige la friccion principal detectada.</p>
          <p class="p">Meta recomendada: mantener tasa de respuesta IA por encima de 90% con tono de marca estable y seguimiento semanal.</p>
        </div>

        <div class="footer">Generado por Lokigi · ${esc(config.appDomain)}</div>
      </section>
      <div style="text-align:right">
}
