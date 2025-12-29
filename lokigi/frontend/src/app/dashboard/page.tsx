import React, { useEffect, useState } from "react";
import { GaugeChart } from "../components/GaugeChart";
import { ProfitLeaking } from "../components/ProfitLeaking";
import { BusinessComparison } from "../components/BusinessComparison";
import { CTAButton } from "../components/CTAButton";
import CompetitorWarRoom from "../components/CompetitorWarRoom";
import ReviewSEOAnalyzer from "../components/ReviewSEOAnalyzer";
import WorkerDashboard from "../components/WorkerDashboard";
import SuperuserGrowthProjection from "../components/SuperuserGrowthProjection";
import Link from "next/link";
import SupabaseAuthPanel from "../components/SupabaseAuthPanel";
import { useSuperuser } from "../components/useSuperuser";

export default function DashboardPage() {
  const isSuperuser = useSuperuser();
  // Demo data
  const score = 78;
  const lucroCesante = 12450;

  const [client, setClient] = useState(null);
  const [competitors, setCompetitors] = useState([]);
  const [strengths, setStrengths] = useState([1, 0.8, 0.6, 0.9]); // Normalizado 0-1
  const [weaknesses, setWeaknesses] = useState([0.5, 0.7, 0.3, 0.4]); // Normalizado 0-1
  const [locale, setLocale] = useState("es");

  useEffect(() => {
    // Ejemplo: fetch datos reales desde backend
    async function fetchData() {
      const res = await fetch("/api/audit/result/demo-id"); // demo-id: reemplaza por audit_id real
      const data = await res.json();
      if (data.result) {
        setClient({
          ...data.result.client,
          locale: data.result.client?.locale || "es",
        });
        setCompetitors(
          data.result.heatmap.map((c) => ({
            name: c.name,
            lat: c.lat,
            lon: c.lon,
          }))
        );
        // Simula fortalezas/debilidades desde backend
        setStrengths([0.9, 0.7, 0.8, 0.6]);
        setWeaknesses([0.4, 0.5, 0.3, 0.2]);
      }
    }
    fetchData();
  }, []);

  // Datos reales simulados para ImpactReport
  const impactReportData = {
    score,
    improvements: [
      "Optimización de perfil Google My Business",
      "Actualización de NAP y fotos geolocalizadas",
      "Mejora de reputación y respuesta a reseñas"
    ],
    photos: [
      { url: "/demo/photo1.jpg", lat: client?.lat || 0, lon: client?.lon || 0 },
      { url: "/demo/photo2.jpg", lat: client?.lat || 0, lon: client?.lon || 0 }
    ],
    ranking: [
      { name: client?.name || "Tu Negocio", score },
      ...competitors.slice(0, 2).map((c, i) => ({ name: c.name || `Competidor ${i+1}`, score: Math.round(score - 7 - i*6) }))
    ],
    radarData: {
      labels: ["Reputación", "SEO Local", "Visual", "NAP"],
      datasets: [
        { label: "Antes", data: [60, 55, 50, 70] },
        { label: "Después", data: [score, 80, 90, 95] }
      ]
    }
  };

  return (
    <main className="min-h-screen bg-black text-white flex flex-col items-center py-12">
      <SupabaseAuthPanel />
      <div className="w-full flex justify-end max-w-6xl mb-4">
        <Link href={{ pathname: "/impact-report", query: impactReportData }}
          className="bg-[#39FF14] text-black font-bold px-6 py-2 rounded-lg hover:scale-105 transition">
          Ver Impact Report
        </Link>
      </div>
      <h1 className="text-4xl font-extrabold mb-8 text-center tracking-tight">
        The Mirror Effect
      </h1>
      <section className="w-full max-w-2xl bg-gray-900 rounded-2xl p-8 shadow-xl mb-8">
        <GaugeChart score={score} />
      </section>
      <section className="w-full max-w-2xl bg-gray-900 rounded-2xl p-8 shadow-xl mb-8">
        <ProfitLeaking amount={lucroCesante} />
      </section>
      <section className="w-full max-w-4xl bg-gray-900 rounded-2xl p-8 shadow-xl mb-8">
        <BusinessComparison />
      </section>
      <section className="w-full max-w-2xl bg-gray-900 rounded-2xl p-8 shadow-xl mb-8 flex flex-col items-center">
        <div className="mb-4 text-lg text-center text-gray-200">
          Consejos de la IA para mejorar tu visibilidad local y superar a tu
          competencia.
        </div>
        <CTAButton onClick={() => alert("¡Acción de conversión!")} />
      </section>
      <div className="w-full max-w-6xl bg-gray-900 rounded-2xl p-8 shadow-xl mb-8">
        <CompetitorWarRoom
          client={client || { lat: 40.4168, lon: -3.7038 }}
          competitors={
            competitors.length
              ? competitors
              : [
                  { name: "Comp1", lat: 40.417, lon: -3.704 },
                  { name: "Comp2", lat: 40.415, lon: -3.702 },
                  { name: "Comp3", lat: 40.418, lon: -3.705 },
                  { name: "Comp4", lat: 40.42, lon: -3.7 },
                  { name: "Comp5", lat: 40.41, lon: -3.71 },
                ]
          }
          locale={locale}
          strengths={strengths}
          weaknesses={weaknesses}
        />
      </div>
      <ReviewSEOAnalyzer />
      <div className="w-full max-w-4xl mx-auto mt-8">
        <WorkerDashboard />
      </div>
      {isSuperuser && (
        <div className="w-full max-w-3xl mx-auto mt-8">
          <SuperuserGrowthProjection />
        </div>
      )}
    </main>
  );
}
