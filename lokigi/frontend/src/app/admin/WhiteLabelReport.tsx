// WhiteLabelReport.tsx
// Reporte PDF/Web con branding de agencia (White-Label)
// Documentación al final del archivo

import React from 'react';

interface WhiteLabelReportProps {
  agencyLogo: string;
  agencyColor: string;
  agencyName: string;
  children?: React.ReactNode;
}

export default function WhiteLabelReport({ agencyLogo, agencyColor, agencyName, children }: WhiteLabelReportProps) {
  return (
    <div className="p-8 rounded-xl shadow-xl" style={{ background: agencyColor }}>
      <div className="flex items-center gap-4 mb-6">
        {agencyLogo ? (
          <img src={agencyLogo} alt="Agency Logo" className="h-12 rounded shadow" />
        ) : (
          <div className="h-12 w-32 bg-gray-200 rounded flex items-center justify-center text-gray-500 font-bold">Agency Logo</div>
        )}
        <span className="text-2xl font-bold text-white">{agencyName || 'Agency Name'}</span>
      </div>
      <div className="bg-white rounded p-6 text-gray-900">
        {children || <p>Contenido del reporte aquí...</p>}
      </div>
    </div>
  );
}

/*
Documentación:
- Este componente genera un reporte web/pdf con branding personalizado.
- Si no hay logo, muestra un placeholder neutro.
- El color y nombre de la agencia se aplican dinámicamente.
- Útil para la fase B2B y white-label.
*/
