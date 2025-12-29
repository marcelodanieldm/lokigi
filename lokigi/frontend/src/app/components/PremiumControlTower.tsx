// frontend/src/app/components/PremiumControlTower.tsx
"""
Premium Customer Dashboard: Control Tower
- Mapa interactivo (Heatmap) con Leaflet
- Feed de alertas
- ROI Tracker
- Estética dark mode con neón verde
- Mobile-first
"""

import dynamic from "next/dynamic";
import { useEffect, useState } from "react";
import "leaflet/dist/leaflet.css";

const Map = dynamic(() => import("react-leaflet").then(mod => mod.MapContainer), { ssr: false });
const TileLayer = dynamic(() => import("react-leaflet").then(mod => mod.TileLayer), { ssr: false });
const Circle = dynamic(() => import("react-leaflet").then(mod => mod.Circle), { ssr: false });

export default function PremiumControlTower({ points, alerts, roi }) {
  // points: [{lat, lon, dominance: 'client'|'competitor'}]
  // alerts: [{text, type, date}]
  // roi: {amount: number, currency: string}
  const [center, setCenter] = useState([points?.[0]?.lat || 0, points?.[0]?.lon || 0]);

  return (
    <div className="card bg-white text-corporate-dark border border-corporate-gray p-6 mb-6">
      <h2 className="text-2xl font-bold text-corporate-blue mb-4">Premium Control Tower</h2>
      <div className="mb-2 text-gray-700">{summary}</div>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div>
          <span className="font-semibold">Alertas:</span> <span className="text-corporate-blue">{alerts}</span>
        </div>
        <div>
          <span className="font-semibold">ROI:</span> <span className="text-corporate-blue">{roi}</span>
        </div>
      </div>
      <div className="mt-4">
        <CTAButton onClick={onAction} label="Ver detalles" />
      </div>
    </div>
  );
}
