export type ExecutiveSummaryInput = {
  business_name: string;
  month_label: string;
  metrics: Record<string, unknown>;
  sentiment: Record<string, unknown>;
};

export const SYSTEM_PROMPT = [
  "Eres un Consultor de Marketing para negocios locales.",
  "Redactas resumen ejecutivo mensual para dueños no tecnicos.",
  "Reglas: espanol, tono motivador/profesional/breve, no inventar datos, exactamente 3 parrafos.",
  "Salida obligatoria en JSON valido con claves:",
  "paragraph_1_client_voice, paragraph_2_key_achievement, paragraph_3_improvement_opportunity.",
].join(" ");

export function buildUserPrompt(input: ExecutiveSummaryInput): string {
  return [
    "Genera un resumen ejecutivo mensual usando solo los datos de entrada.",
    "Objetivos:",
    "1) Resumen de lo que opinan los clientes.",
    "2) Logro destacado con cifras reales.",
    "3) Oportunidad de mejora accionable.",
    "Devuelve solo JSON.",
    JSON.stringify(input, null, 2),
  ].join("\n\n");
}

export function buildFallbackSummary(input: ExecutiveSummaryInput) {
  const positive = Number((input.sentiment as any)?.positive_reviews || 0);
  const neutral = Number((input.sentiment as any)?.neutral_reviews || 0);
  const negative = Number((input.sentiment as any)?.negative_reviews || 0);
  const total = Number((input.metrics as any)?.total_reviews || positive + neutral + negative || 0);
  const responseRate = (input.metrics as any)?.response_rate_pct;
  const avgRating = (input.metrics as any)?.avg_rating;

  return {
    paragraph_1_client_voice: `En ${input.month_label}, ${input.business_name} recibio feedback mixto con ${positive} reseñas positivas, ${neutral} neutrales y ${negative} negativas. El volumen total de interacciones del periodo fue de ${total}, lo que ofrece una señal clara para priorizar mejoras en experiencia y consistencia del servicio.`,
    paragraph_2_key_achievement: `Tu logro principal del mes fue sostener la operacion de reputacion con indicadores concretos: nota media ${avgRating ?? "sin dato"} y tasa de respuesta ${responseRate ?? "sin dato"}%. Esto muestra una base de atencion activa y capacidad para mantener presencia constante frente a tus clientes.` ,
    paragraph_3_improvement_opportunity: "La mayor oportunidad para el proximo mes es actuar sobre los temas criticados con mayor frecuencia y cerrar el ciclo de respuesta con acciones visibles para el cliente. Define una mejora puntual por semana y mide su impacto en reseñas negativas para convertir friccion en confianza.",
  };
}
