// PartnershipsDashboard.tsx
// Admin Dashboard: Indicadores de Poder de Red y White-Label para Agencias
// Documentación al final del archivo

import React, { useState } from 'react';
import { getActiveAffiliates, getEPC, getRevenueComparison } from './partnershipsMetrics';
import BrandingEngine from './BrandingEngine';

export default function PartnershipsDashboard() {
  const [agencyBrand, setAgencyBrand] = useState({
    logo: '',
    primaryColor: '#22d3ee',
    secondaryColor: '#0f172a',
    agencyName: '',
  });

  // Simulación de datos (reemplazar por fetch real)
  const activeAffiliates = getActiveAffiliates();
  const epc = getEPC();
  const { affiliateRevenue, directRevenue } = getRevenueComparison();

  return (
    <div className="min-h-screen bg-gray-950 text-white p-8">
      <h1 className="text-3xl font-bold mb-6 text-green-400">Admin: Partnerships & White-Label</h1>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <div className="bg-gray-900 rounded-xl p-6 shadow-xl border-l-4 border-cyan-400">
          <h2 className="text-lg font-bold mb-2">Active Affiliates</h2>
          <p className="text-3xl font-mono text-cyan-300">{activeAffiliates}</p>
          <span className="text-xs text-gray-400">Con al menos 1 lead esta semana</span>
        </div>
        <div className="bg-gray-900 rounded-xl p-6 shadow-xl border-l-4 border-green-400">
          <h2 className="text-lg font-bold mb-2">EPC (Earnings Per Click)</h2>
          <p className="text-3xl font-mono text-green-300">${epc.toFixed(2)}</p>
          <span className="text-xs text-gray-400">Promedio por afiliado</span>
        </div>
        <div className="bg-gray-900 rounded-xl p-6 shadow-xl border-l-4 border-fuchsia-400">
          <h2 className="text-lg font-bold mb-2">Affiliate vs Direct Revenue</h2>
          <div className="flex items-end gap-2 mt-2">
            <div className="h-8 bg-green-400 rounded w-1/2 flex items-center justify-center text-gray-900 font-bold">
              ${affiliateRevenue}
            </div>
            <div className="h-8 bg-fuchsia-400 rounded w-1/2 flex items-center justify-center text-gray-900 font-bold">
              ${directRevenue}
            </div>
          </div>
          <span className="text-xs text-gray-400">Comparativa semanal</span>
        </div>
      </div>
      <BrandingEngine agencyBrand={agencyBrand} setAgencyBrand={setAgencyBrand} />
    </div>
  );
}

/*
Documentación:
- Este dashboard muestra indicadores clave para el equipo de partnerships y la fase white-label.
- KPIs: Active Affiliates, EPC, Affiliate vs Direct Revenue.
- BrandingEngine permite a agencias personalizar logo y colores (white-label).
- Integra con la base de datos para cargar variables de marca y reportes personalizados.
*/
