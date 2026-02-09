// partnershipsMetrics.ts
// Lógica de métricas para PartnershipsDashboard

// Simulación: reemplazar por fetch real a backend
export function getActiveAffiliates(): number {
  // Devuelve el número de afiliados con al menos 1 lead esta semana
  return 17;
}

export function getEPC(): number {
  // Earnings Per Click promedio
  return 2.35;
}

export function getRevenueComparison(): { affiliateRevenue: number; directRevenue: number } {
  // Simulación de ingresos
  return { affiliateRevenue: 1200, directRevenue: 3200 };
}
