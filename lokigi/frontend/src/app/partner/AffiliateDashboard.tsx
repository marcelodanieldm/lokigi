// AffiliateDashboard.tsx
// Dashboard de Socios/Afiliados para Lokigi
// UX/UI: Verde neón, dark mode, estilo técnico y profesional

import React, { useState } from 'react';
import AffiliateOnboardingTour from './AffiliateOnboardingTour';

const metrics = [
  { label: 'Clics', value: 0 },
  { label: 'Leads Generados', value: 0 },
  { label: 'Comisiones Totales', value: '$0.00' },
];

export default function AffiliateDashboard({
  clicks = 0,
  leads = 0,
  commissions = 0,
  affiliateLink = '',
  qrCodeUrl = '',
  mediaKitLinks = [],
}: {
  clicks?: number;
  leads?: number;
  commissions?: number;
  affiliateLink?: string;
  qrCodeUrl?: string;
  mediaKitLinks?: { label: string; url: string }[];
}) {
  const [copied, setCopied] = useState(false);
  const handleCopy = () => {
    navigator.clipboard.writeText(affiliateLink);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  };
  return (
    <div className="min-h-screen bg-gray-950 text-white px-4 py-8 relative">
      <AffiliateOnboardingTour />
      <h1 className="text-3xl font-bold text-green-400 mb-6">Partner Portal</h1>
      <div className="mb-6" id="onboarding-guide">
        <a
          href="/frontend/src/app/partner/ONBOARDING_AFILIADOS_VISUAL.md"
          target="_blank"
          rel="noopener noreferrer"
          className="inline-block bg-green-900 text-green-300 border border-green-400 rounded px-4 py-2 text-sm font-semibold hover:bg-green-800 hover:text-green-200 transition"
        >
          📖 Ver Guía Visual de Onboarding de Afiliados
        </a>
      </div>
      {/* Métricas */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-6 mb-8" id="metrics">
        <MetricCard label="Clics" value={clicks} />
        <MetricCard label="Leads Generados" value={leads} />
        <MetricCard label="Comisiones Totales" value={`$${commissions.toFixed(2)}`} />
      </div>
      {/* Link Generator */}
      <div className="bg-gray-900 rounded-xl p-6 mb-8 border border-green-400 shadow-lg" id="link-generator">
        <h2 className="text-xl font-semibold text-green-300 mb-2">Tu link de afiliado</h2>
        <div className="flex flex-col sm:flex-row items-center gap-4">
          <input
            className="w-full bg-gray-800 text-green-400 font-mono px-3 py-2 rounded border border-green-700"
            value={affiliateLink}
            readOnly
          />
          <button
            className="bg-green-400 text-gray-900 font-bold px-4 py-2 rounded hover:bg-green-300 transition"
            onClick={handleCopy}
          >
            {copied ? '¡Copiado!' : 'Copiar link'}
          </button>
          {qrCodeUrl && (
            <img src={qrCodeUrl} alt="QR" className="w-20 h-20 border-2 border-green-400 rounded bg-white" />
          )}
        </div>
        <p className="text-xs text-gray-400 mt-2">Comparte tu link o imprime el QR para volantes físicos.</p>
      </div>
      {/* Media Kit */}
      <div className="bg-gray-900 rounded-xl p-6 border border-green-400 shadow-lg" id="media-kit">
        <h2 className="text-xl font-semibold text-green-300 mb-2">Media Kit</h2>
        <ul className="space-y-2">
          {mediaKitLinks.map((item, i) => (
            <li key={i}>
              <a
                href={item.url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-green-400 hover:underline"
              >
                {item.label}
              </a>
            </li>
          ))}
        </ul>
        <p className="text-xs text-gray-400 mt-2">Descarga banners y capturas de pantalla para tus redes.</p>
      </div>
    </div>
  );
}

function MetricCard({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="bg-gray-900 rounded-xl p-6 flex flex-col items-center border border-green-400 shadow-lg">
      <span className="text-lg text-gray-300 mb-1">{label}</span>
      <span className="text-3xl font-bold text-green-400">{value}</span>
    </div>
  );
}

// Documentación:
// - Usa <AffiliateDashboard /> en la ruta /partner o /affiliate.
// - Pasa las props con los datos del afiliado y links del media kit.
// - El QR puede generarse con una API como qrserver.com.
// - El Media Kit puede alojarse en Supabase Storage o CDN.
// - Mantiene la estética dark, técnica y profesional de Lokigi.
