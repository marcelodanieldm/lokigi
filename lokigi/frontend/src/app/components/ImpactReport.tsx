"use client";
import { GaugeChart } from "./GaugeChart";
import { Radar } from "react-chartjs-2";

export default function ImpactReport({
  score = 85,
  improvements = [
    "Optimización de perfil Google My Business",
    "Actualización de NAP y fotos geolocalizadas",
    "Mejora de reputación y respuesta a reseñas"
  ],
  photos = [
    { url: "/demo/photo1.jpg", lat: -34.6, lon: -58.4 },
    { url: "/demo/photo2.jpg", lat: -34.61, lon: -58.41 }
  ],
  ranking = [
    { name: "Tu Negocio", score: 85 },
    { name: "Competidor A", score: 78 },
    { name: "Competidor B", score: 72 }
  ],
  radarData = {
    labels: ["Reputación", "SEO Local", "Visual", "NAP"],
    datasets: [
      { label: "Antes", data: [60, 55, 50, 70] },
      { label: "Después", data: [85, 80, 90, 95] }
    ]
  }
}) {
  return (
    <div className="bg-gray-950 text-white font-mono min-h-screen p-0">
      {/* Página 1: Medidor de Score */}
      <section className="flex flex-col items-center justify-center h-screen">
        <h1 className="text-4xl font-extrabold mb-8 text-[#39FF14]">Lokigi Impact Report</h1>
        <div className="w-full flex justify-center">
          <GaugeChart score={score} />
        </div>
        <div className="mt-8 text-2xl font-bold" style={{ color: score > 80 ? "#39FF14" : score > 60 ? "#FFD600" : "#FF3B3B" }}>
          Score Actual: {score}
        </div>
      </section>
      {/* Página 2: Mejoras Realizadas */}
      <section className="py-16 px-8">
        <h2 className="text-2xl mb-4 text-[#39FF14]">Mejoras Realizadas</h2>
        <ul className="list-disc pl-8 text-lg">
          {improvements.map((item, i) => (
            <li key={i} className="mb-2">{item}</li>
          ))}
        </ul>
      </section>
      {/* Página 3: Fotos Optimizadas con Geo-tag */}
      <section className="py-16 px-8">
        <h2 className="text-2xl mb-4 text-[#39FF14]">Fotos Optimizadas con Geo-tag</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {photos.map((photo, i) => (
            <div key={i} className="bg-gray-900 rounded-lg p-2 flex flex-col items-center">
              <img src={photo.url} alt="Foto optimizada" className="rounded shadow mb-2 max-h-32 object-cover" />
              <span className="text-xs text-gray-400">Lat: {photo.lat}, Lon: {photo.lon}</span>
            </div>
          ))}
        </div>
      </section>
      {/* Página 4: Ranking de Competencia Actualizado */}
      <section className="py-16 px-8">
        <h2 className="text-2xl mb-4 text-[#39FF14]">Ranking de Competencia Actualizado</h2>
        <table className="w-full text-left bg-gray-900 rounded-lg">
          <thead>
            <tr>
              <th className="p-2">Posición</th>
              <th className="p-2">Nombre</th>
              <th className="p-2">Score</th>
            </tr>
          </thead>
          <tbody>
            {ranking.map((comp, i) => (
              <tr key={i} className={i === 0 ? "text-[#39FF14] font-bold" : ""}>
                <td className="p-2">{i + 1}</td>
                <td className="p-2">{comp.name}</td>
                <td className="p-2">{comp.score}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
      {/* Página 5: The Hook - Tu Radar de Protección */}
      <section className="py-16 px-8">
        <h2 className="text-2xl mb-4 text-[#39FF14]">Tu Radar de Protección</h2>
        <p className="mb-4 text-lg text-gray-300">
          ¿Qué pasaría si la competencia reacciona y tú no tienes monitoreo activo? <br />
          ¡Activa tu radar y mantente siempre adelante!
        </p>
        <div className="bg-gray-900 rounded-xl p-6">
          <Radar data={radarData} options={{
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
          }} />
        </div>
      </section>
    </div>
  );
}
