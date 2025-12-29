import { useRef, useEffect as useEffectReact } from "react";
// frontend/src/app/dashboard/premium/page.tsx
import PremiumControlTower from "@/app/components/PremiumControlTower";
import { useEffect, useState } from "react";
import { createClient } from "@supabase/supabase-js";

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
const supabaseKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;
const supabase = createClient(supabaseUrl, supabaseKey);

function SkeletonAudit() {
  return (
    <div className="bg-gray-900/80 rounded-xl p-4 border border-[#39FF14] flex flex-col items-center mb-4 animate-pulse">
      <span className="text-xs text-gray-400 mb-1">Dominance Index</span>
      <span className="text-2xl font-bold bg-gray-800 text-gray-700 rounded w-20 h-8 mb-2"></span>
      <span className="text-xs text-gray-400 mt-1">Amenaza: <span className="bg-gray-800 text-gray-700 rounded w-24 h-4 inline-block"></span></span>
    </div>
  );
}


export default function PremiumDashboardPage() {
  const [points, setPoints] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [roi, setRoi] = useState({ amount: 0, currency: 'USD' });
  const [dominance, setDominance] = useState(null);
  const [threat, setThreat] = useState(null);
  const [auditId, setAuditId] = useState(null);
  const [auditResult, setAuditResult] = useState(null);
  const [loadingAudit, setLoadingAudit] = useState(false);
  const [growth, setGrowth] = useState(null);

  useEffect(() => {
    // Fetch puntos de visibilidad y ROI desde Supabase
    async function fetchPointsAndROI() {
      // Puntos: tabla 'visibility_points' {lat, lon, dominance}
      const { data: pointsData } = await supabase.from('visibility_points').select('*');
      setPoints(pointsData || []);
      // ROI: tabla 'roi_tracker' {amount, currency}
      const { data: roiData } = await supabase.from('roi_tracker').select('*').single();
      if (roiData) setRoi(roiData);
    }
    // Fetch alertas desde backend
    async function fetchAlerts() {
      // Simulación: snapshots de 3 competidores
      const snapshots = [
        {
          name: "Pizzeria Napoli",
          history: [
            { date: "2025-11", rating: 4.2, reviews: 120, photos: 30 },
            { date: "2025-12", rating: 4.5, reviews: 145, photos: 42, tags: "Navidad" }
          ]
        },
        {
          name: "Pizza Roma",
          history: [
            { date: "2025-11", rating: 4.0, reviews: 80, photos: 20 },
            { date: "2025-12", rating: 4.1, reviews: 100, photos: 22 }
          ]
        },
        {
          name: "Pizza Brasil",
          history: [
            { date: "2025-11", rating: 4.3, reviews: 90, photos: 25 },
            { date: "2025-12", rating: 4.6, reviews: 130, photos: 35 }
          ]
        }
      ];
      const res = await fetch("/api/alert-radar", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ snapshots, country: "AR", lang: "es" })
      });
      const json = await res.json();
      // Mapear a formato del feed
      setAlerts((json.alerts || []).map((text, i) => ({ text, type: 'danger', date: new Date().toISOString().slice(0, 10) })));
    }
    // Streaming de auditoría
    async function startAudit() {
      setLoadingAudit(true);
      // Ejemplo: cliente y competidores
      const client = { lat: -34.6, lon: -58.4, rating: 4.7, review_count: 120, name: "Mi Negocio" };
      const competitors = [
        { name: "Rival 1", lat: -34.601, lon: -58.401, rating: 4.8, review_count: 200 },
        { name: "Rival 2", lat: -34.602, lon: -58.402, rating: 4.6, review_count: 150 },
        { name: "Rival 3", lat: -34.603, lon: -58.403, rating: 4.5, review_count: 180 },
        { name: "Rival 4", lat: -34.604, lon: -58.404, rating: 4.7, review_count: 90 },
        { name: "Rival 5", lat: -34.605, lon: -58.405, rating: 4.4, review_count: 110 }
      ];
      // Lanzar auditoría asíncrona
      const res = await fetch("/api/audit", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          score: 85,
          rubro: "Peluquería",
          competencia: "3 locales en 1km con 4.5 estrellas",
          fallo: "No tiene fotos de los trabajos realizados",
          pais: "AR",
          lang: "es",
          client,
          competitors,
          locale: "es"
        })
      });
      const { audit_id } = await res.json();
      setAuditId(audit_id);
      // Polling para resultados parciales
      let tries = 0;
      let done = false;
      while (!done && tries < 20) {
        await new Promise(r => setTimeout(r, 500));
        const r = await fetch(`/api/audit/result/${audit_id}`);
        const data = await r.json();
        if (!data.status) {
          setAuditResult(data);
          setDominance(data.dominance?.dominance_index ?? null);
          setThreat(data.dominance?.competitor_threat ?? null);
          done = true;
        }
        tries++;
      }
      setLoadingAudit(false);
    }
    fetchPointsAndROI();
    fetchAlerts();
    startAudit();
    // Proyección de crecimiento (ejemplo)
    async function fetchGrowthProjection() {
      const res = await fetch("/api/growth/projection", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          initial_score: 58,
          final_score: 82,
          initial_metrics: { reputation: 60, seo: 55, visual: 50, nap: 70 },
          final_metrics: { reputation: 80, seo: 75, visual: 85, nap: 90 },
          daily_revenue: 120,
          currency: "ARS"
        })
      });
      setGrowth(await res.json());
    }
    fetchGrowthProjection();
  }, []);

  return (
    <>
      {loadingAudit || dominance === null ? <SkeletonAudit /> : (
        <div className="bg-gray-900/80 rounded-xl p-4 border border-[#39FF14] flex flex-col items-center mb-4">
          <span className="text-xs text-gray-400 mb-1">Dominance Index</span>
          <span className="text-2xl font-bold text-[#39FF14]">{(dominance * 100).toFixed(1)}%</span>
          <span className="text-xs text-gray-400 mt-1">Amenaza: <b className="text-[#FF1744]">{threat}</b></span>
        </div>
      )}
      {growth && (
        <div className="bg-gray-900/80 rounded-xl p-4 border border-green-400 flex flex-col items-center mb-4 w-full max-w-xl">
          <span className="text-xs text-gray-400 mb-1">Crecimiento Proyectado</span>
          <span className="text-2xl font-bold text-green-400">{growth.currency_symbol}{growth.projected_gain.toLocaleString()} {growth.currency}</span>
          <span className="text-xs text-gray-400 mt-1">Visibilidad: <b className="text-green-400">{growth.visibility_gain_pct}%</b></span>
          {/* Radar Chart */}
          <RadarChart data={growth.radar} />
        </div>
      )}

// --- RadarChart Component ---
function RadarChart({ data }) {
  const canvasRef = useRef(null);
  useEffectReact(() => {
    if (!data || !canvasRef.current) return;
    const ctx = canvasRef.current.getContext("2d");
    ctx.clearRect(0, 0, 320, 200);
    const { labels, datasets } = data;
    const N = labels.length;
    const center = { x: 160, y: 100 };
    const radius = 70;
    // Dibuja ejes
    ctx.strokeStyle = "#39FF14";
    ctx.globalAlpha = 0.3;
    for (let i = 0; i < N; i++) {
      const angle = (2 * Math.PI * i) / N - Math.PI / 2;
      ctx.beginPath();
      ctx.moveTo(center.x, center.y);
      ctx.lineTo(center.x + radius * Math.cos(angle), center.y + radius * Math.sin(angle));
      ctx.stroke();
    }
    // Dibuja polígonos
    datasets.forEach((ds, idx) => {
      ctx.beginPath();
      ds.data.forEach((val, i) => {
        const angle = (2 * Math.PI * i) / N - Math.PI / 2;
        const r = (val / 100) * radius;
        const x = center.x + r * Math.cos(angle);
        const y = center.y + r * Math.sin(angle);
        if (i === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
      });
      ctx.closePath();
      ctx.globalAlpha = idx === 0 ? 0.15 : 0.3;
      ctx.fillStyle = idx === 0 ? "#39FF14" : "#00BFFF";
      ctx.fill();
      ctx.globalAlpha = 1;
      ctx.strokeStyle = idx === 0 ? "#39FF14" : "#00BFFF";
      ctx.stroke();
    });
    // Dibuja labels
    ctx.font = "12px monospace";
    ctx.fillStyle = "#39FF14";
    ctx.globalAlpha = 0.7;
    labels.forEach((label, i) => {
      const angle = (2 * Math.PI * i) / N - Math.PI / 2;
      const x = center.x + (radius + 18) * Math.cos(angle);
      const y = center.y + (radius + 18) * Math.sin(angle) + 4;
      ctx.fillText(label, x - ctx.measureText(label).width / 2, y);
    });
    ctx.globalAlpha = 1;
  }, [data]);
  return <canvas ref={canvasRef} width={320} height={200} className="mt-2" />;
}
      <PremiumControlTower points={points} alerts={alerts} roi={roi} />
    </>
  );
}
