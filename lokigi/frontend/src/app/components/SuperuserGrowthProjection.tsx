"use client";
import { useState } from "react";
// Radar chart: npm install chart.js react-chartjs-2
import { Radar } from "react-chartjs-2";
import {
  Chart as ChartJS,
  RadialLinearScale,
  PointElement,
  LineElement,
  Filler,
  Tooltip,
  Legend,
} from "chart.js";
ChartJS.register(RadialLinearScale, PointElement, LineElement, Filler, Tooltip, Legend);

const initialMetrics = { reputation: 60, seo: 55, visual: 50, nap: 70 };
const finalMetrics = { reputation: 80, seo: 75, visual: 85, nap: 90 };

export default function SuperuserGrowthProjection() {
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  async function handleProjection() {
    setLoading(true);
    const res = await fetch("/api/growth/projection", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        initial_score: 58,
        final_score: 82,
        initial_metrics: initialMetrics,
        final_metrics: finalMetrics,
        daily_revenue: 120,
        currency: "ARS"
      })
    });
    const data = await res.json();
    setResult(data);
    setLoading(false);
  }

  return (
    <div className="card bg-white text-corporate-dark border border-corporate-gray p-6 mb-6">
      <h2 className="text-2xl font-bold text-corporate-blue mb-4">Proyección de Crecimiento (Superuser)</h2>
      <button
        className="bg-[#39FF14] text-black font-bold px-6 py-2 rounded-lg mb-6 hover:scale-105 transition"
        onClick={handleProjection}
        disabled={loading}
      >
        {loading ? "Calculando..." : "Calcular Proyección"}
      </button>
      {result && (
        <>
          <div className="mb-4">
            <span className="text-lg">Ganancia proyectada 6 meses: </span>
            <span className="text-2xl text-[#39FF14] font-bold">{result.currency_symbol}{result.projected_gain}</span>
            <span className="ml-2 text-gray-400">({result.currency})</span>
          </div>
          <div className="mb-4">
            <span className="text-lg">Incremento de visibilidad: </span>
            <span className="text-xl text-[#39FF14] font-bold">+{result.visibility_gain_pct}%</span>
          </div>
          <Radar
            data={result.radar}
            options={{
              scales: {
                r: {
                  angleLines: { display: false },
                  suggestedMin: 0,
                  suggestedMax: 100,
                  pointLabels: { color: "#39FF14", font: { size: 14 } },
                  grid: { color: "#333" },
                  ticks: { color: "#39FF14" }
                }
              },
              plugins: {
                legend: { labels: { color: "#39FF14" } }
              }
            }}
            className="bg-gray-900 rounded-xl p-4"
          />
        </>
      )}
    </div>
  );
}
