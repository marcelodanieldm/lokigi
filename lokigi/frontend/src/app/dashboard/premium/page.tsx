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
      <PremiumControlTower points={points} alerts={alerts} roi={roi} />
    </>
  );
}
