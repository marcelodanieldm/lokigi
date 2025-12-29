// CompetitorWarRoom.tsx
/**
 * Componente visual "Competitor War Room" para Lokigi
 * - Mapa minimalista dark mode: punto rojo parpadeante (cliente), puntos verdes (competidores)
 * - Copy dinámico multilingüe
 * - Radar chart SVG ultra liviano (fortalezas vs debilidades)
 * - Sin librerías pesadas
 */
import React from "react";

const labels = {
  es: "Esta es tu zona de pérdida de clientes",
  pt: "Esta é a sua zona de perda de clientes",
  en: "This is your customer loss zone"
};

export default function CompetitorWarRoom({
  client = { x: 120, y: 120 },
  competitors = [
    { x: 60, y: 80 },
    { x: 180, y: 100 },
    { x: 100, y: 180 }
  ],
  radar = {
    labels: ["Reputación", "SEO", "Visual", "NAP"],
    client: [80, 60, 70, 90],
    competitor: [90, 80, 85, 95]
  },
  lang = "es"
}) {
  // Radar chart SVG generator
  function RadarChart({ labels, client, competitor, size = 180 }) {
    const N = labels.length;
    const angle = (i) => (Math.PI * 2 * i) / N;
    const center = size / 2;
    const radius = size / 2 - 20;
    // Helper to get point
    const point = (val, i, max = 100) => [
      center + Math.sin(angle(i)) * (radius * val / max),
      center - Math.cos(angle(i)) * (radius * val / max)
    ];
    // Polygon points
    const poly = (arr) => arr.map(point).map(([x, y]) => `${x},${y}`).join(" ");
    return (
      <svg width={size} height={size} className="mx-auto block">
        {/* Grid */}
        {[0.5, 1].map((f, j) => (
          <polygon
            key={j}
            points={Array(N).fill(0).map((_, i) => point(100 * f, i)).map(([x, y]) => `${x},${y}`).join(" ")}
            fill="none"
            stroke="#333"
            strokeDasharray="4 2"
          />
        ))}
        {/* Competitor */}
        <polygon points={poly(competitor)} fill="#39FF1460" stroke="#39FF14" strokeWidth={2} />
        {/* Client */}
        <polygon points={poly(client)} fill="#FF174460" stroke="#FF1744" strokeWidth={2} />
        {/* Axes and labels */}
        {labels.map((lbl, i) => {
          const [x, y] = point(110, i);
          return <text key={i} x={x} y={y} fill="#aaa" fontSize={12} textAnchor="middle">{lbl}</text>;
        })}
      </svg>
    );
  }

  return (
    <div className="bg-gray-950 rounded-2xl p-6 shadow-xl border border-[#39FF14] max-w-xl mx-auto mt-8">
      <h2 className="text-2xl font-bold text-[#39FF14] mb-2 text-center">Competitor War Room</h2>
      <div className="relative w-64 h-64 mx-auto mb-4 bg-gradient-to-br from-gray-900 to-gray-800 rounded-full border-2 border-[#222]">
        {/* Cliente: punto rojo parpadeante */}
        <span className="absolute animate-pulse block w-6 h-6 rounded-full bg-[#FF1744] border-2 border-white shadow-lg" style={{ left: client.x - 12, top: client.y - 12 }} />
        {/* Competidores: puntos verdes sólidos */}
        {competitors.map((c, i) => (
          <span key={i} className="absolute block w-5 h-5 rounded-full bg-[#39FF14] border-2 border-white shadow" style={{ left: c.x - 10, top: c.y - 10 }} />
        ))}
        {/* Área de influencia (simulada) */}
        <div className="absolute left-0 top-0 w-full h-full pointer-events-none">
          <svg width="100%" height="100%">
            <circle cx={client.x} cy={client.y} r="60" fill="#FF174420" />
            {competitors.map((c, i) => (
              <circle key={i} cx={c.x} cy={c.y} r="50" fill="#39FF1420" />
            ))}
          </svg>
        </div>
      </div>
      <div className="text-center text-lg text-[#FF1744] font-semibold mb-4">
        {labels[lang]}
      </div>
      <div className="bg-gray-900 rounded-xl p-4">
        <div className="text-center text-sm text-gray-400 mb-2">Fortalezas vs Debilidades</div>
        <RadarChart labels={radar.labels} client={radar.client} competitor={radar.competitor} />
        <div className="flex justify-between mt-2 text-xs text-gray-400">
          <span className="text-[#FF1744]">Tú</span>
          <span className="text-[#39FF14]">Competidor</span>
        </div>
      </div>
    </div>
  );
}
