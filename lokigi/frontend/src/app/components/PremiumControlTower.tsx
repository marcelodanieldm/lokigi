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
    <div className="min-h-screen bg-gray-950 text-white p-0 md:p-6 flex flex-col gap-4">
      <h1 className="text-2xl md:text-3xl font-bold text-[#39FF14] mb-2 md:mb-4">Control Tower</h1>
      {/* Heatmap */}
      <div className="w-full h-72 md:h-96 rounded-xl overflow-hidden border-2 border-[#39FF14] shadow-lg">
        <Map center={center} zoom={13} style={{ height: "100%", width: "100%" }} scrollWheelZoom={true}>
          <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
          {points.map((p, i) => (
            <Circle
              key={i}
              center={[p.lat, p.lon]}
              radius={120}
              pathOptions={{ color: p.dominance === 'client' ? '#39FF14' : '#FF1744', fillOpacity: 0.5 }}
            />
          ))}
        </Map>
      </div>
      {/* Alert Feed */}
      <div className="bg-gray-900/80 rounded-xl p-4 border border-[#39FF14] max-h-56 overflow-y-auto">
        <h2 className="text-lg font-semibold text-[#39FF14] mb-2">Alertas</h2>
        <ul className="space-y-2">
          {alerts.length === 0 && <li className="text-gray-400">Sin alertas recientes.</li>}
          {alerts.map((a, i) => (
            <li key={i} className="text-sm flex items-center gap-2">
              <span className={
                a.type === 'danger' ? 'text-[#FF1744]' :
                a.type === 'info' ? 'text-[#39FF14]' : 'text-white'
              }>●</span>
              <span>{a.text}</span>
              <span className="ml-auto text-xs text-gray-500">{a.date}</span>
            </li>
          ))}
        </ul>
      </div>
      {/* ROI Tracker */}
      <div className="bg-gray-900/80 rounded-xl p-4 border border-[#39FF14] flex flex-col items-center">
        <span className="text-xs text-gray-400 mb-1">Dinero Protegido este mes</span>
        <span className="text-2xl font-bold text-[#39FF14]">{roi.amount.toLocaleString()} {roi.currency}</span>
      </div>
    </div>
  );
}
